import streamlit as st
import cv2
import numpy as np

# Sayfa ayarları
st.set_page_config(page_title="Alan Lazer - Teklif Paneli", layout="wide")

# Stabilite için CSS: Sadece boşlukları ve gereksiz scroll'u yönetir
st.markdown("""
    <style>
        /* Sidebar içeriğini yukarı çek ve logonun tam görünmesini sağla */
        [data-testid="stSidebar"] .block-container {
            padding-top: 2rem !important;
        }
        
        /* Sidebar içindeki elemanların arasını daraltarak kompakt görünüm sağla */
        .stSelectbox, .stNumberInput {
            margin-bottom: -10px !important;
        }

        /* Sistem parametreleri kutusu stili */
        .stAlert {
            padding: 0.8rem !important;
            border: 1px solid #d1d5db !important;
        }

        /* Başlık stili */
        h1 {
            color: #1e3a8a;
        }
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
        "hizlar": {0.8: 6000, 1: 5500, 2: 3500, 3: 2800, 5: 1800, 10: 800, 20: 300}
    },
    "Paslanmaz": {
        "kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8, 10], 
        "ozkutle": 8.0,
        "hizlar": {0.8: 7000, 2: 4500, 5: 1200, 10: 500}
    },
    "Alüminyum": {
        "kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8], 
        "ozkutle": 2.7,
        "hizlar": {0.8: 8000, 2: 5000, 5: 1500, 8: 600}
    }
}

# --- SOL MENÜ (SIDEBAR) ---
with st.sidebar:
    # Logonun en üstte düzgün görünmesi için padding ayarlı
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
    
    # BİLGİLENDİRME ALANI
    st.markdown("---")
    hiz_listesi = VERİ[metal]["hizlar"]
    guncel_hiz = hiz_listesi.get(kalinlik, min(hiz_listesi.values()))
    
    st.info(f"""
    **Sistem Parametreleri:**
    * Kesim Hızı: {guncel_hiz} mm/dk
    * Dakika Ücreti: {DK_UCRETI} TL
    """)

# --- ANA EKRAN ---
st.title("Alan Lazer Profesyonel Teklif Paneli")
st.write("Hızlı ve Hassas Kesim Çözümleri | [alanlazer.com](https://alanlazer.com)")

uploaded_file = st.file_uploader("Çizim Fotoğrafını Yükle", type=['jpg', 'png'])

if uploaded_file:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 30, 150)
    
    contours, _ = cv2.findContours(edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        main_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(main_contour)
        oran = referans_olcu / w
        
        total_cevre_piksel = 0
        delik_sayisi = 0
        
        for cnt in contours:
            c_length = cv2.arcLength(cnt, True)
            if c_length > 15:
                total_cevre_piksel += c_length
                delik_sayisi += 1
                cv2.drawContours(img, [cnt], -1, (0, 255, 0), 2)
        
        p_en, p_boy = w * oran, h * oran
        toplam_kesim_yolu_mm = total_cevre_piksel * oran
        piercing_sayisi = int(delik_sayisi) * adet
        
        saf_kesim_suresi_dk = (toplam_kesim_yolu_mm / guncel_hiz) * adet
        piercing_ek_suresi_dk = (piercing_sayisi * PIERCING_SURESI) / 60
        toplam_sure_dk = saf_kesim_suresi_dk + piercing_ek_suresi_dk
        
        isclik_bedeli = toplam_sure_dk * DK_UCRETI
        alan = cv2.contourArea(main_contour) * (oran**2)
        agirlik = (alan * kalinlik * VERİ[metal]["ozkutle"]) / 1000000 
        malzeme_bedeli = (agirlik * adet) * KG_UCRETI

        st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), use_container_width=True)

        st.subheader("📋 Detaylı Fiyatlandırma")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Toplam Kesim", f"{round(toplam_kesim_yolu_mm/1000, 1)} m")
        c2.metric("Piercing Sayısı", f"{piercing_sayisi} Adet")
        c3.metric("Toplam Süre", f"{round(toplam_sure_dk, 1)} dk")
        c4.metric("TOPLAM TEKLİF", f"{round(isclik_bedeli + malzeme_bedeli, 2)} TL")
