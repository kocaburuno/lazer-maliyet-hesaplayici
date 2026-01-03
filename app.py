import streamlit as st
import cv2
import numpy as np
from PIL import Image

# Sayfa ayarları
st.set_page_config(page_title="Alan Lazer - Teklif Paneli", layout="wide")

# --- LOGO VE BAŞLIK ---
# Logo dosyanızın adının 'logo.png' olduğunu varsayıyoruz. 
# Eğer GitHub'a farklı bir isimle yüklediyseniz aşağıyı güncelleyin.
try:
    col_logo, col_text = st.columns([1, 4])
    with col_logo:
        st.image("logo.png", width=150) # Logonuzu GitHub'a 'logo.png' adıyla yüklemeyi unutmayın
    with col_text:
        st.title("Alan Lazer Profesyonel Teklif Paneli")
        st.write("Hızlı ve Hassas Kesim Çözümleri | [alanlazer.com](https://alanlazer.com)")
except:
    st.title("Alan Lazer Profesyonel Teklif Paneli")

# ==========================================
# ADMIN AYARLARI (YALNIZCA BURADAN DEĞİŞTİRİLİR)
# ==========================================
DK_UCRETI = 25.0       # Dakika kesim ücreti (TL)
PIERCING_SURESI = 2.0  # Her bir patlatma için ek süre (Saniye)
KG_UCRETI = 45.0       # Malzeme kg fiyatı (TL)

VERİ = {
    "Siyah Sac": {"kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20], "ozkutle": 7.85},
    "Paslanmaz": {"kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8, 10], "ozkutle": 8.0},
    "Alüminyum": {"kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8], "ozkutle": 2.7}
}

# --- KULLANICI YAN MENÜSÜ ---
st.sidebar.header("Üretim Seçenekleri")
metal = st.sidebar.selectbox("Metal Türü", list(VERİ.keys()))
kalinlik = st.sidebar.selectbox("Kalınlık (mm)", VERİ[metal]["kalinliklar"])
secilen_plaka = st.sidebar.selectbox("Plaka Boyutu (mm)", ["1500x6000", "1500x3000", "2500x1250", "1000x2000"])
adet = st.sidebar.number_input("Parça Adedi", min_value=1, value=1)
referans_olcu = st.sidebar.number_input("Çizimdeki Genişlik (mm)", value=100)
hiz = st.sidebar.number_input("Kesim Hızı (mm/dk)", value=2000)

# --- İŞLEME ---
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
            if c_length > 15: # Küçük gürültüleri ele
                total_cevre_piksel += c_length
                delik_sayisi += 1
                cv2.drawContours(img, [cnt], -1, (0, 255, 0), 2)
        
        # Matematiksel Hesaplar
        p_en, p_boy = w * oran, h * oran
        toplam_kesim_yolu_mm = total_cevre_piksel * oran
        piercing_sayisi = int(delik_sayisi) * adet
        
        # Sığma Kontrolü
        plaka_en, plaka_boy = map(int, secilen_plaka.split('x'))
        sigiyor_mu = (p_en <= plaka_en and p_boy <= plaka_boy) or (p_en <= plaka_boy and p_boy <= plaka_en)
        
        if not sigiyor_mu:
            st.error(f"❌ Parça ({round(p_en)}x{round(p_boy)}mm) seçilen plakaya sığmıyor!")
        else:
            # SÜRE VE MALİYET ANALİZİ
            saf_kesim_suresi_dk = (toplam_kesim_yolu_mm / hiz) * adet
            piercing_ek_suresi_dk = (piercing_sayisi * PIERCING_SURESI) / 60
            toplam_sure_dk = saf_kesim_suresi_dk + piercing_ek_suresi_dk
            isclik_bedeli = toplam_sure_dk * DK_UCRETI
            
            alan = cv2.contourArea(main_contour) * (oran**2)
            agirlik = (alan * kalinlik * VERİ[metal]["ozkutle"]) / 1000000 
            malzeme_bedeli = (agirlik * adet) * KG_UCRETI
            
            toplam_fiyat = isclik_bedeli + malzeme_bedeli

            # Görüntü Gösterimi
            st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), use_column_width=True)

            # SONUÇ TABLOSU
            st.subheader("📋 Detaylı Fiyatlandırma")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Toplam Kesim", f"{round(toplam_kesim_yolu_mm/1000, 1)} m")
            c2.metric("Piercing Sayısı", f"{piercing_sayisi} Adet")
            c3.metric("Toplam Süre", f"{round(toplam_sure_dk, 1)} dk")
            c4.metric("TOPLAM TEKLİF", f"{round(toplam_fiyat, 2)} TL")
            
            # Alt Bilgi Reklamı
            st.markdown(
                """
                <hr>
                <div style='text-align: center; color: #1e3a8a;'>
                    <p>Alan Lazer Kesim Çözümleri - 2024</p>
                    <a href='https://alanlazer.com' target='_blank'>www.alanlazer.com</a>
                </div>
                """, unsafe_allow_html=True)
