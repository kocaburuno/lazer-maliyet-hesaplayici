import streamlit as st
import cv2
import numpy as np
from PIL import Image

st.set_page_config(page_title="Lazer Kesim Maliyet", layout="wide")

# --- PARAMETRE TABLOSU (Burayı dilediğin gibi güncelleyebiliriz) ---
# Malzeme: [Hız (mm/dk), Birim Fiyat (TL/kg)]
PARAMETRELER = {
    "Siyah Sac (2mm)": [3500, 45],
    "Siyah Sac (5mm)": [1800, 45],
    "Paslanmaz (2mm)": [4500, 120],
}
MAKINE_SAAT_UCRETI = 1500 # TL

st.title("✂️ Lazer Kesim Akıllı Maliyet Hesaplama")

# Yan Menü
st.sidebar.header("1. Üretim Ayarları")
secim = st.sidebar.selectbox("Malzeme ve Kalınlık", list(PARAMETRELER.keys()))
adet = st.sidebar.number_input("Parça Adedi", min_value=1, value=1)
referans_olcu = st.sidebar.number_input("Referans Ölçü (mm) - (Çizimdeki bilinen uzunluk)", value=100)

st.sidebar.header("2. Fiyatlandırma")
st.sidebar.write(f"Kesim Hızı: {PARAMETRELER[secim][0]} mm/dk")

# Dosya Yükleme
uploaded_file = st.file_uploader("AutoCAD Ekran Görüntüsü Yükleyin", type=['jpg', 'jpeg', 'png'])

if uploaded_file is not None:
    # Görüntüyü işle
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Kontur tespiti (Canny Edge Detection)
    edged = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # En büyük konturu bul (Parçanın kendisi)
    if contours:
        main_contour = max(contours, key=cv2.contourArea)
        # Çizim üzerine konturu çiz
        cv2.drawContours(img, [main_contour], -1, (0, 255, 0), 3)
        
        # Basit Ölçü Mantığı: 
        # (Şimdilik en geniş kısmı referans alıyoruz, bir sonraki adımda kullanıcıya seçtireceğiz)
        x, y, w, h = cv2.boundingRect(main_contour)
        piksel_oran = referans_olcu / w # Genişliği referans alıyoruz
        
        cevre_piksel = cv2.arcLength(main_contour, True)
        gerçek_cevre_mm = cevre_piksel * piksel_oran
        
        # Maliyet Hesaplama
        kesim_suresi_dk = (gerçek_cevre_mm / PARAMETRELER[secim][0]) * adet
        maliyet_tl = (kesim_suresi_dk / 60) * MAKINE_SAAT_UCRETI

        # Görseli Göster
        st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), caption='Tespit Edilen Konturlar (Yeşil)', use_column_width=True)

        # Sonuçlar
        st.subheader("📊 Analiz Sonuçları")
        c1, c2, c3 = st.columns(3)
        c1.metric("Parça Çevresi", f"{round(gerçek_cevre_mm, 2)} mm")
        c2.metric("Toplam Kesim Süresi", f"{round(kesim_suresi_dk, 2)} dk")
        c3.metric("Tahmini İşçilik Fiyatı", f"{round(maliyet_tl, 2)} TL")
        
        st.warning("Not: Malzeme ağırlık maliyeti ve nesting firesi şu an kaba hesaplanmaktadır.")
