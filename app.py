import streamlit as st
import cv2
import numpy as np
from PIL import Image

st.set_page_config(page_title="Lazer Kesim Maliyet Hesaplayıcı", layout="wide")

st.title("✂️ Lazer Kesim Maliyet ve Nesting Hesaplayıcı")

# Yan Menü - Parametreler
st.sidebar.header("Üretim Parametreleri")
malzeme = st.sidebar.selectbox("Malzeme Türü", ["Siyah Sac", "Paslanmaz", "Alüminyum"])
kalinlik = st.sidebar.slider("Sac Kalınlığı (mm)", 1, 20, 2)
adet = st.sidebar.number_input("Parça Adedi", min_value=1, value=1)

# Arka plandaki verilerin (Bunları sonra beraber güncelleyeceğiz)
kesim_hizi = 2000 # mm/dk (Örnek)
makine_saat_ucreti = 1500 # TL

st.info("Lütfen AutoCAD ekran görüntüsünü (en az bir ölçü görünecek şekilde) yükleyin.")

uploaded_file = st.file_uploader("Fotoğraf Yükle", type=['jpg', 'jpeg', 'png'])

if uploaded_file is not None:
    # Fotoğrafı oku
    image = Image.open(uploaded_file)
    st.image(image, caption='Yüklenen Parça', use_column_width=True)
    
    st.success("Görüntü başarıyla yüklendi. Kontur analizi ve fiyatlandırma için bir sonraki aşamaya geçiyoruz.")
    
    # Basit bir maliyet tablosu gösterimi (Taslak)
    st.subheader("📊 Tahmini Maliyet Özeti")
    col1, col2, col3 = st.columns(3)
    col1.metric("Kesim Yolu", "Hesaplanıyor... m")
    col2.metric("Tahmini Süre", "Hesaplanıyor... dk")
    col3.metric("Toplam Fiyat", "TL")
