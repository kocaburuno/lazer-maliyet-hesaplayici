import streamlit as st
import cv2
import numpy as np

# 1. SAYFA YAPILANDIRMASI
st.set_page_config(page_title="Teklif Paneli", layout="wide")

# 2. MALZEME VERİLERİ (Genişletilmiş Standart Liste)
VERİ = {
    "Siyah Sac": {
        "ozkutle": 7.85, 
        "kalinliklar": [0.5, 0.8, 1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25],
        "hizlar": {1: 5500, 3: 2800, 5: 1800, 10: 800, 20: 400}
    },
    "Paslanmaz": {
        "ozkutle": 8.0, 
        "kalinliklar": [0.5, 0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8, 10, 12, 15],
        "hizlar": {1: 6000, 2: 4500, 5: 1200, 10: 500}
    },
    "Alüminyum": {
        "ozkutle": 2.7, 
        "kalinliklar": [0.5, 0.8, 1, 1.5, 2, 3, 4, 5, 6, 8, 10],
        "hizlar": {1: 8000, 3: 4000, 5: 1500, 10: 400}
    }
}

DK_UCRETI = 25.0
PIERCING_SURESI = 2.0
KG_UCRETI = 45.0

# 3. SIDEBAR
with st.sidebar:
    try: st.image("logo.png", use_container_width=True)
    except: st.title("LOGO")
    
    metal = st.selectbox("Metal Türü", list(VERİ.keys()))
    kalinlik = st.selectbox("Kalınlık (mm)", VERİ[metal]["kalinliklar"])
    secilen_plaka = st.selectbox("Plaka Boyutu (mm)", ["1500x6000", "1500x3000", "2500x1250"])
    adet = st.number_input("Parça Adedi", min_value=1, value=1)
    referans_olcu = st.number_input("Çizimdeki Genişlik (mm)", value=3295.0)
    
    guncel_hiz = VERİ[metal]["hizlar"].get(kalinlik, min(VERİ[metal]["hizlar"].values()))

# 4. ANA PANEL
st.title("Profesyonel Teklif Paneli")
uploaded_file = st.file_uploader("Çizim Fotoğrafını Yükle", type=['jpg', 'png', 'jpeg'])

if uploaded_file:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Adaptif eşikleme: Işık farklarını yok eder ve tüm konturları belirginleştirir
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY_INV, 11, 2)
    
    # Konturları hiyerarşik bul
    contours, hierarchy = cv2.findContours(binary, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours and hierarchy is not None:
        main_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(main_contour)
        oran = referans_olcu / w
        
        gecerli_konturlar = []
        toplam_yol_piksel = 0

        for i, cnt in enumerate(contours):
            # Hiyerarşi Kontrolü: 
            # hierarchy[0][i][3] == -1 -> En dış çerçeve
            # hierarchy[0][i][3] != -1 -> İç delikler (Sadece ilk seviye çocukları alarak çift saymayı önler)
            # hierarchy[0][i][3] == 0  -> En dış çerçevenin hemen içindeki delikler
            parent_idx = hierarchy[0][i][3]
            
            if parent_idx == -1 or parent_idx == 0:
                cevre = cv2.arcLength(cnt, True)
                if cevre * oran > 2.0: # 2mm'den küçük pikselleri ele (nokta hatası)
                    gecerli_konturlar.append(cnt)
                    toplam_yol_piksel += cevre
        
        # Sonuçlar
        piercing_basi = len(gecerli_konturlar)
        kesim_m = (toplam_yol_piksel * oran) / 1000
        sure_dk = (kesim_m * 1000 / guncel_hiz) * adet + (piercing_basi * adet * PIERCING_SURESI / 60)
        agirlik = (cv2.contourArea(main_contour) * (oran**2) * kalinlik * VERİ[metal]["ozkutle"]) / 1e6
        fiyat = (sure_dk * DK_UCRETI) + (agirlik * adet * KG_UCRETI)

        # Görselleştirme: TÜM KONTURLAR YEŞİL
        output_img = img.copy()
        cv2.drawContours(output_img, gecerli_konturlar, -1, (0, 255, 0), 2)
        st.image(cv2.cvtColor(output_img, cv2.COLOR_BGR2RGB), use_container_width=True)
        
        # Özet Tablosu
        st.subheader("📋 Kesim Analizi ve Teklif")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Toplam Kesim", f"{round(kesim_m * adet, 1)} m")
        c2.metric("Piercing Adedi", f"{piercing_basi * adet}")
        c3.metric("Tahmini Süre", f"{round(sure_dk, 1)} dk")
        c4.metric("TOPLAM FİYAT", f"{round(fiyat, 2)} TL")
