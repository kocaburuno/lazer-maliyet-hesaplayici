import streamlit as st
import cv2
import numpy as np

# Sayfa ayarları
st.set_page_config(page_title="Alan Lazer - Teklif Paneli", layout="wide")

# Sidebar'ı çivileyen ve kaydırmayı tamamen kapatan CSS
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            position: fixed !important;
            height: 100vh !important;
            overflow: hidden !important;
        }
        [data-testid="stSidebar"] .block-container {
            padding-top: 1rem !important;
        }
        .stSelectbox, .stNumberInput {
            margin-bottom: -10px !important;
        }
        h1 { color: #1e3a8a; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# ADMIN AYARLARI
# ==========================================
DK_UCRETI = 25.0       
PIERCING_SURESI = 2.0  
KG_UCRETI = 45.0       

VERİ = {
    "Siyah Sac": {
        "kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20], 
        "ozkutle": 7.85,
        "hizlar": {0.8: 6000, 1: 5500, 2: 4500, 3: 2800, 5: 1800, 10: 800}
    },
    "Paslanmaz": {
        "kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8, 10], 
        "ozkutle": 8.0,
        "hizlar": {0.8: 7000, 2: 4500, 5: 1200, 10: 500}
    }
}

# --- SIDEBAR ---
with st.sidebar:
    try:
        st.image("logo.png", use_container_width=True)
    except:
        st.markdown("## ALAN LAZER")
    
    st.markdown("### Üretim Seçenekleri")
    metal = st.selectbox("Metal Türü", list(VERİ.keys()))
    kalinlik = st.selectbox("Kalınlık (mm)", VERİ[metal]["kalinliklar"])
    
    plakalar = ["1500x6000", "1500x3000", "2500x1250", "1000x2000"]
    secilen_plaka = st.selectbox("Plaka Boyutu (mm)", plakalar)
    
    adet = st.number_input("Parça Adedi", min_value=1, value=1)
    referans_olcu = st.number_input("Çizim Genişliği (mm)", value=3295)
    
    st.markdown("---")
    guncel_hiz = VERİ[metal]["hizlar"].get(kalinlik, 2000)
    st.info(f"**Sistem Parametreleri:**\n* Kesim Hızı: {guncel_hiz} mm/dk\n* Dakika Ücreti: {DK_UCRETI} TL")

# --- ANA EKRAN ---
st.title("Alan Lazer Profesyonel Teklif Paneli")

uploaded_file = st.file_uploader("Çizim Fotoğrafını Yükle", type=['jpg', 'png'])

if uploaded_file:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 1. Aşama: Pürüzleri gidermek için yumuşatma ve eşikleme
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    _, thresh = cv2.threshold(blurred, 150, 255, cv2.THRESH_BINARY_INV)
    
    # 2. Aşama: Çizgi kalınlığından kaynaklanan çift sayımı bitirmek için "Morphological Closing"
    kernel = np.ones((5,5), np.uint8)
    closing = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    # 3. Aşama: Hiyerarşik kontur tespiti (RETR_EXTERNAL ve RETR_CCOMP kombinasyonu gibi çalışır)
    contours, hierarchy = cv2.findContours(closing, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        main_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(main_contour)
        oran = referans_olcu / w
        
        # Plaka Kontrolü
        p_en, p_boy = w * oran, h * oran
        pl_en_val, pl_boy_val = map(int, secilen_plaka.split('x'))
        if not ((p_en <= pl_en_val and p_boy <= pl_boy_val) or (p_en <= pl_boy_val and p_boy <= pl_en_val)):
            st.error(f"❌ Parça ({round(p_en)}x{round(p_boy)}mm) {secilen_plaka} plakaya sığmıyor!")
            st.stop()

        # --- HASSAS PIERCING HESABI ---
        gercek_kontur_sayisi = 0
        toplam_kesim_piksel = 0
        filtre_2mm_piksel = 2 / oran

        for i, cnt in enumerate(contours):
            # Sadece hiyerarşide en üst seviye veya 1. seviye iç delikleri say (Çizginin içini/dışını ayrı saymaz)
            if hierarchy[0][i][3] == -1 or hierarchy[0][i][3] == 0:
                cevre = cv2.arcLength(cnt, True)
                if cevre > filtre_2mm_piksel:
                    gercek_kontur_sayisi += 1
                    toplam_kesim_piksel += cevre
                    cv2.drawContours(img, [cnt], -1, (0, 255, 0), 2)

        # Çizimdeki 49 konturu burada yakalıyoruz
        piercing_toplam = gercek_kontur_sayisi * adet
        kesim_yolu_m = (toplam_kesim_piksel * oran) / 1000
        
        # Süre ve Fiyat
        sure_dk = (kesim_yolu_m * 1000 / guncel_hiz) * adet + (piercing_toplam * PIERCING_SURESI / 60)
        malzeme_kg = (cv2.contourArea(main_contour) * (oran**2) * kalinlik * VERİ[metal]["ozkutle"]) / 1e6
        toplam_teklif = (sure_dk * DK_UCRETI) + (malzeme_kg * adet * KG_UCRETI)

        st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), use_container_width=True)
        
        st.subheader("📋 Detaylı Fiyatlandırma")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Toplam Kesim", f"{round(kesim_yolu_m, 1)} m")
        c2.metric("Piercing Sayısı", f"{piercing_toplam} Adet")
        c3.metric("Toplam Süre", f"{round(sure_dk, 1)} dk")
        c4.metric("TOPLAM TEKLİF", f"{round(toplam_teklif, 2)} TL")
