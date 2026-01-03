import streamlit as st
import cv2
import numpy as np
from PIL import Image

st.set_page_config(page_title="Lazer Kesim Pro", layout="wide")

# --- VERİ YAPISI ---
VERİ = {
    "Siyah Sac": {
        "kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20],
        "hizlar": {0.8: 6000, 2: 3500, 5: 1800, 10: 800, 20: 300}, # Örnek hızlar
        "ozkutle": 7.85 # gr/cm3
    },
    "Paslanmaz": {
        "kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8, 10],
        "hizlar": {0.8: 7000, 2: 4500, 5: 1200, 10: 500},
        "ozkutle": 8.0
    },
    "Alüminyum": {
        "kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8],
        "hizlar": {0.8: 8000, 2: 5000, 5: 1500, 8: 600},
        "ozkutle": 2.7
    }
}

st.title("⚙️ Lazer Kesim Profesyonel Teklif Paneli")

# --- YAN MENÜ: AKILLI SEÇİM ---
st.sidebar.header("1. Malzeme ve Plaka")
metal = st.sidebar.selectbox("Metal Türü", list(VERİ.keys()))
kalinlik = st.sidebar.selectbox("Kalınlık (mm)", VERİ[metal]["kalinliklar"])

# Plaka Ölçüleri Mantığı
if metal == "Siyah Sac":
    if kalinlik >= 2:
        plakalar = ["1500x6000", "1500x3000", "2500x1250", "1000x2000"]
    else:
        plakalar = ["1500x3000", "1250x2500", "1000x2000"]
else: # Paslanmaz ve Alüminyum
    plakalar = ["1500x3000", "1220x2440", "1000x2000"]

secilen_plaka = st.sidebar.selectbox("Plaka Boyutu (mm)", plakalar)
adet = st.sidebar.number_input("Parça Adedi", min_value=1, value=1)
referans_olcu = st.sidebar.number_input("Çizimdeki Genişlik (mm)", value=100)

# --- ANA EKRAN ---
uploaded_file = st.file_uploader("Çizim Fotoğrafını Yükle", type=['jpg', 'png'])

if uploaded_file:
    # Görüntü İşleme
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edged = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        cnt = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(cnt)
        
        # Matematiksel Hesaplar
        oran = referans_olcu / w
        parca_boy = h * oran
        parca_en = w * oran
        cevre = cv2.arcLength(cnt, True) * oran
        alan = cv2.contourArea(cnt) * (oran**2)
        
        # Hız ve Maliyet (Tablodaki en yakın kalınlığa göre hız seçimi)
        hiz = VERİ[metal]["hizlar"].get(kalinlik, 1000) 
        sure = (cevre / hiz) * adet
        
        # Basit Nesting Tahmini
        p_en, p_boy = map(int, secilen_plaka.split('x'))
        sigan_adet = (p_en // (parca_en + 5)) * (p_boy // (parca_boy + 5))
        plaka_ihtiyac = int(np.ceil(adet / sigan_adet)) if sigan_adet > 0 else 1

        # Ağırlık Hesabı
        agirlik = (alan * kalinlik * VERİ[metal]["ozkutle"]) / 1000000 # kg
        
        # Görüntüyü Göster
        cv2.rectangle(img, (x,y), (x+w, y+h), (255,0,0), 2)
        st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), use_column_width=True)

        # SONUÇ TABLOSU
        st.subheader("📋 Teknik Detaylar ve Teklif")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Parça Boyutu", f"{round(parca_en,1)}x{round(parca_boy,1)} mm")
        col2.metric("Kesim Yolu", f"{round(cevre,1)} mm")
        col3.metric("Birim Ağırlık", f"{round(agirlik,3)} kg")
        col4.metric("Plaka Başına Adet", f"{int(sigan_adet)}")

        st.success(f"**Sonuç:** {adet} parça için **{plaka_ihtiyac} adet** {secilen_plaka} plaka kullanılacak. Tahmini toplam kesim süresi: **{round(sure, 2)} dk**")
