import streamlit as st
import cv2
import numpy as np
from PIL import Image

st.set_page_config(page_title="Lazer Kesim Pro + İç Delik Analizi", layout="wide")

# --- VERİ YAPISI ---
VERİ = {
    "Siyah Sac": {"kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20], "ozkutle": 7.85},
    "Paslanmaz": {"kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8, 10], "ozkutle": 8.0},
    "Alüminyum": {"kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8], "ozkutle": 2.7}
}

st.title("⚙️ Lazer Kesim Profesyonel Teklif Paneli (İç Delik Analizli)")

# --- YAN MENÜ ---
st.sidebar.header("1. Üretim ve Plaka")
metal = st.sidebar.selectbox("Metal Türü", list(VERİ.keys()))
kalinlik = st.sidebar.selectbox("Kalınlık (mm)", VERİ[metal]["kalinliklar"])

plakalar = ["1500x6000", "1500x3000", "2500x1250", "1000x2000"] # Basitleştirilmiş plaka listesi
secilen_plaka = st.sidebar.selectbox("Plaka Boyutu (mm)", plakalar)
adet = st.sidebar.number_input("Parça Adedi", min_value=1, value=1)
referans_olcu = st.sidebar.number_input("Çizimdeki Genişlik (mm)", value=3295) # Son yüklediğin görsele göre varsayılan

st.sidebar.header("2. Fiyatlandırma Parametreleri")
hiz = st.sidebar.number_input("Kesim Hızı (mm/dk)", value=2000)
dk_ucreti = st.sidebar.number_input("Kesim Dakika Ücreti (TL)", value=25.0)
kg_ucreti = st.sidebar.number_input("Malzeme kg Fiyatı (TL)", value=45.0)

# --- İŞLEME ---
uploaded_file = st.file_uploader("Çizim Fotoğrafını Yükle", type=['jpg', 'png'])

if uploaded_file:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Parazit engelleme ve netleştirme
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 30, 150)
    
    # Tüm konturları bul (RETR_LIST ile iç-dış ayrımı yapmadan hepsini alırız)
    contours, hierarchy = cv2.findContours(edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        # En büyük kontur dış konturdur
        main_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(main_contour)
        oran = referans_olcu / w
        
        total_cevre_piksel = 0
        delik_sayisi = 0
        
        # Konturları filtrele (Çok küçük gürültüleri ele)
        for cnt in contours:
            c_length = cv2.arcLength(cnt, True)
            if c_length > 10: # 10 pikselden küçük noktaları yoksay
                total_cevre_piksel += c_length
                delik_sayisi += 1
                cv2.drawContours(img, [cnt], -1, (0, 255, 0), 2)
        
        # Matematiksel Hesaplar
        p_en, p_boy = w * oran, h * oran
        toplam_kesim_yolu_mm = total_cevre_piksel * oran
        delik_sayisi = delik_sayisi - 1 # Dış konturu çıkarınca kalan delikler
        
        # Sığma Kontrolü
        plaka_en, plaka_boy = map(int, secilen_plaka.split('x'))
        sigiyor_mu = (p_en <= plaka_en and p_boy <= plaka_boy) or (p_en <= plaka_boy and p_boy <= plaka_en)
        
        if not sigiyor_mu:
            st.error(f"❌ Parça Boyutu: {round(p_en)}x{round(p_boy)}mm. Plaka: {secilen_plaka}mm. SIĞMIYOR!")
        else:
            # Maliyet
            toplam_sure = (toplam_kesim_yolu_mm / hiz) * adet
            isclik = toplam_sure * dk_ucreti
            # Alan hesabı (Dış kontura göre kaba ağırlık)
            alan = cv2.contourArea(main_contour) * (oran**2)
            agirlik = (alan * kalinlik * VERİ[metal]["ozkutle"]) / 1000000 
            malzeme = (agirlik * adet) * kg_ucreti
            
            st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), use_column_width=True)

            st.subheader("📋 Gelişmiş Kesim Analizi")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Toplam Kesim Yolu", f
