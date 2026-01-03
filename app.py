import streamlit as st
import cv2
import numpy as np

# Sayfa ayarları
st.set_page_config(page_title="Alan Lazer - Teklif Paneli", layout="wide")

# Sidebar'ı tamamen kilitleyen ve logo taşmasını engelleyen CSS
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
        .stAlert {
            padding: 0.8rem !important;
            margin-top: 10px !important;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# ADMIN AYARLARI
# ==========================================
DK_UCRETI = 25.0       
PIERCING_SURESI = 2.0  # Saniye
KG_UCRETI = 45.0       

VERİ = {
    "Siyah Sac": {
        "kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20], 
        "ozkutle": 7.85,
        "hizlar": {0.8: 6000, 1: 5500, 3: 2800, 5: 1800, 10: 800}
    },
    "Paslanmaz": {
        "kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8, 10], 
        "ozkutle": 8.0,
        "hizlar": {0.8: 7000, 2: 4500, 10: 500}
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
    st.info(f"**Sistem Parametreleri:**\n* Hız: {guncel_hiz} mm/dk\n* Birim Maliyet: {DK_UCRETI} TL/dk")

# --- ANA EKRAN ---
st.title("Alan Lazer Profesyonel Teklif Paneli")

uploaded_file = st.file_uploader("Çizim Fotoğrafını Yükle", type=['jpg', 'png'])

if uploaded_file:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Parazitleri temizlemek için Binary Threshold kullanıyoruz
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    
    # Hiyerarşik kontur bulma (İç ve dış ayrımı için en hassas yöntem)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        # En büyük konturu (dış çerçeve) bul
        main_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(main_contour)
        oran = referans_olcu / w
        
        # Plaka Kontrolü
        p_en, p_boy = w * oran, h * oran
        pl_en_val, pl_boy_val = map(int, secilen_plaka.split('x'))
        if not ((p_en <= pl_en_val and p_boy <= pl_boy_val) or (p_en <= pl_boy_val and p_boy <= pl_en_val)):
            st.error(f"❌ Parça ({round(p_en)}x{round(p_boy)} mm) seçilen {secilen_plaka} plakaya sığmıyor!")
            st.stop()

        # --- PIERCING VE KESİM HESABI ---
        gercek_kontur_sayisi = 0
        toplam_kesim_piksel = 0
        min_cevre_mm = 5.0 # 5mm'den küçük pürüzleri ele
        
        for i, cnt in enumerate(contours):
            cevre_piksel = cv2.arcLength(cnt, True)
            if (cevre_piksel * oran) > min_cevre_mm:
                # RETR_CCOMP hiyerarşisinde sadece ana konturları say (gereksiz iç detayları ele)
                if hierarchy[0][i][3] == -1 or hierarchy[0][i][3] == 0:
                    gercek_kontur_sayisi += 1
                    toplam_kesim_piksel += cevre_piksel
                    cv2.drawContours(img, [cnt], -1, (0, 255, 0), 2)

        piercing_sayisi = gercek_kontur_sayisi * adet
        kesim_yolu_m = (toplam_kesim_piksel * oran) / 1000
        
        # Maliyet
        sure_dk = ((kesim_yolu_m * 1000) / guncel_hiz) * adet + (piercing_sayisi * PIERCING_SURESI / 60)
        toplam_fiyat = sure_dk * DK_UCRETI + ((cv2.contourArea(main_contour) * (oran**2) * kalinlik * VERİ[metal]["ozkutle"] / 1e6) * adet * KG_UCRETI)

        st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), use_container_width=True)
        
        st.subheader("📋 Analiz Sonuçları")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Toplam Kesim", f"{round(kesim_yolu_m, 1)} m")
        c2.metric("Piercing", f"{piercing_sayisi} Adet")
        c3.metric("Tahmini Süre", f"{round(sure_dk, 1)} dk")
        c4.metric("TOPLAM FİYAT", f"{round(toplam_fiyat, 2)} TL")
