import streamlit as st
import cv2
import numpy as np

# 1. SAYFA AYARLARI (En başta olmalı)
st.set_page_config(page_title="Alan Lazer - Teklif Paneli", layout="wide")

# 2. SABİT PARAMETRELER
DK_UCRETI = 25.0       
PIERCING_SURESI = 2.0  
KG_UCRETI = 45.0       

VERİ = {
    "Siyah Sac": {"ozkutle": 7.85, "hizlar": {0.8: 6000, 1: 5500, 2: 4500, 3: 2800, 5: 1800, 10: 800}},
    "Paslanmaz": {"ozkutle": 8.0, "hizlar": {0.8: 7000, 2: 4500, 5: 1200, 10: 500}}
}

# 3. SIDEBAR (SOL PANEL)
with st.sidebar:
    # Logoyu standart Streamlit bileşeni olarak ekliyoruz (Kaymayı önler)
    try:
        st.image("logo.png", use_container_width=True)
    except:
        st.title("ALAN LAZER")
    
    st.subheader("Üretim Seçenekleri")
    metal = st.selectbox("Metal Türü", list(VERİ.keys()))
    kalinlik = st.selectbox("Kalınlık (mm)", [0.8, 1, 2, 3, 5, 10])
    secilen_plaka = st.selectbox("Plaka Boyutu (mm)", ["1500x6000", "1500x3000", "2500x1250"])
    adet = st.number_input("Parça Adedi", min_value=1, value=1)
    referans_olcu = st.number_input("Çizim Genişliği (mm)", value=3295)
    
    st.markdown("---")
    guncel_hiz = VERİ[metal]["hizlar"].get(kalinlik, 2000)
    st.info(f"**Sistem:** {guncel_hiz} mm/dk | {DK_UCRETI} TL/dk")

# 4. ANA EKRAN
st.title("Alan Lazer Profesyonel Teklif Paneli")

uploaded_file = st.file_uploader("Çizim Fotoğrafını Yükle", type=['jpg', 'png', 'jpeg'])

if uploaded_file:
    # Görüntü İşleme
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Gürültü engelleme ve netleştirme
    blurred = cv2.medianBlur(gray, 5)
    _, thresh = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY_INV)
    
    # Kontur bulma (Hiyerarşik: İç ve dışı ayırır)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        # En büyük kontur (Dış çerçeve)
        main_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(main_contour)
        oran = referans_olcu / w
        
        # Plaka Kontrolü
        p_en, p_boy = w * oran, h * oran
        pl_en, pl_boy = map(int, secilen_plaka.split('x'))
        if not ((p_en <= pl_en and p_boy <= pl_boy) or (p_en <= pl_boy and p_boy <= pl_en)):
            st.error(f"❌ Parça ({round(p_en)}x{round(p_boy)}mm) {secilen_plaka} plakaya sığmıyor!")
        else:
            # 49 Piercing hedefi için hassas filtreleme
            gercek_konturlar = []
            toplam_kesim_piksel = 0
            
            for i, cnt in enumerate(contours):
                # Alanı çok küçük olan pürüzleri ve iç içe geçmiş çift çizgileri ele
                area = cv2.contourArea(cnt)
                if area > (10 / (oran**2)): # Minimum 10mm² alan filtresi
                    # Sadece ana hiyerarşideki (ebeveyn ve birinci derece çocuk) konturları al
                    if hierarchy[0][i][3] == -1 or hierarchy[0][i][3] == 0:
                        gercek_konturlar.append(cnt)
                        toplam_kesim_piksel += cv2.arcLength(cnt, True)
            
            piercing_sayisi = len(gercek_konturlar) * adet
            kesim_m = (toplam_kesim_piksel * oran) / 1000
            
            # Hesaplamalar
            sure_dk = (kesim_m * 1000 / guncel_hiz) * adet + (piercing_sayisi * PIERCING_SURESI / 60)
            malzeme_kg = (cv2.contourArea(main_contour) * (oran**2) * kalinlik * VERİ[metal]["ozkutle"]) / 1e6
            toplam_fiyat = (sure_dk * DK_UCRETI) + (malzeme_kg * adet * KG_UCRETI)

            # Görselleştirme
            for cnt in gercek_konturlar:
                cv2.drawContours(img, [cnt], -1, (0, 255, 0), 2)
            st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), use_container_width=True)
            
            # Sonuç Tablosu
            st.subheader("📋 Detaylı Fiyatlandırma")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Toplam Kesim", f"{round(kesim_m, 1)} m")
            c2.metric("Piercing", f"{piercing_sayisi} Adet")
            c3.metric("Toplam Süre", f"{round(sure_dk, 1)} dk")
            c4.metric("TOPLAM FİYAT", f"{round(toplam_fiyat, 2)} TL")
