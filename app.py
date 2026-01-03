import streamlit as st
import cv2
import numpy as np

# 1. SAYFA YAPILANDIRMASI
st.set_page_config(page_title="Teklif Paneli", layout="wide")

# 2. ÜRETİM PARAMETRELERİ (Sadece sizin verdiğiniz ilk değerler)
DK_UCRETI = 25.0       
PIERCING_SURESI = 2.0  
KG_UCRETI = 45.0       

VERİ = {
    "Siyah Sac": {
        "ozkutle": 7.85, 
        "kalinliklar": [0.8, 1, 2, 3, 5, 10, 20], 
        "hizlar": {0.8: 6000, 3: 2800, 10: 800}
    },
    "Paslanmaz": {
        "ozkutle": 8.0, 
        "kalinliklar": [0.8, 1, 2, 5, 10], 
        "hizlar": {0.8: 7000, 2: 4500, 10: 500}
    },
    "Alüminyum": {
        "ozkutle": 2.7, 
        "kalinliklar": [0.8, 1, 2, 5, 8], 
        "hizlar": {0.8: 8000, 2: 5000, 8: 600}
    }
}

# 3. SIDEBAR (Seçenekler)
with st.sidebar:
    st.title("ALAN LAZER")
    metal = st.selectbox("Metal Türü", list(VERİ.keys()))
    kalinlik = st.selectbox("Kalınlık (mm)", VERİ[metal]["kalinliklar"])
    secilen_plaka = st.selectbox("Plaka Boyutu (mm)", ["1500x6000", "1500x3000", "2500x1250"])
    adet = st.number_input("Parça Adedi", min_value=1, value=1)
    referans_olcu = st.number_input("Çizimdeki Genişlik (mm)", value=3295.39)
    
    st.divider()
    # Piercing sayısını düzeltmek için hassasiyet ayarı
    hassasiyet = st.slider("Hassasiyet (Izgara Temizleme)", 50, 255, 180)
    
    hiz_listesi = VERİ[metal]["hizlar"]
    guncel_hiz = hiz_listesi.get(kalinlik, min(hiz_listesi.values()))

# 4. ANA PANEL
st.title("Profesyonel Teklif Paneli")
uploaded_file = st.file_uploader("Çizim Fotoğrafını Yükle", type=['jpg', 'png', 'jpeg'])

if uploaded_file:
    # Görüntüyü oku ve işle
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Eşikleme ve gürültü temizleme (Sizin belirlediğiniz hassasiyetle)
    _, binary = cv2.threshold(gray, hassasiyet, 255, cv2.THRESH_BINARY_INV)
    
    # Hiyerarşik kontur tespiti
    contours, hierarchy = cv2.findContours(binary, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours and hierarchy is not None:
        main_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(main_contour)
        oran = referans_olcu / w
        
        gecerli_konturlar = []
        toplam_yol_piksel = 0

        for i, cnt in enumerate(contours):
            # Sadece kapalı odaları sayan hiyerarşi filtresi
            if hierarchy[0][i][3] == -1 or hierarchy[0][i][3] == 0:
                cevre = cv2.arcLength(cnt, True)
                if cevre * oran > 10.0: # Küçük noktaları ele
                    gecerli_konturlar.append(cnt)
                    toplam_yol_piksel += cevre
        
        # Analitikler
        piercing_sayisi = len(gecerli_konturlar)
        kesim_m = (toplam_yol_piksel * oran) / 1000
        sure_dk = (kesim_m * 1000 / guncel_hiz) * adet + (piercing_sayisi * adet * PIERCING_SURESI / 60)
        agirlik = (cv2.contourArea(main_contour) * (oran**2) * kalinlik * VERİ[metal]["ozkutle"]) / 1e6
        fiyat = (sure_dk * DK_UCRETI) + (agirlik * adet * KG_UCRETI)

        # GÖRSEL ÇIKTI: Parça burada görünecek
        output_img = img.copy()
        cv2.drawContours(output_img, gecerli_konturlar, -1, (0, 255, 0), 2)
        st.image(cv2.cvtColor(output_img, cv2.COLOR_BGR2RGB), use_container_width=True)
        
        # SONUÇ TABLOSU
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Toplam Kesim", f"{round(kesim_m * adet, 2)} m")
        c2.metric("Piercing Adedi", f"{piercing_sayisi * adet}")
        c3.metric("Tahmini Süre", f"{round(sure_dk, 1)} dk")
        c4.metric("TOPLAM FİYAT", f"{round(fiyat, 2)} TL")
