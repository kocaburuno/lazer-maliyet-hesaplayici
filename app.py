import streamlit as st
import cv2
import numpy as np

# 1. SAYFA YAPILANDIRMASI
st.set_page_config(page_title="Alan Lazer Teklif Paneli", layout="wide")

# 2. ÜRETİM VE FİYAT PARAMETRELERİ (Orijinal Verileriniz)
DK_UCRETI = 25.0       
PIERCING_SURESI = 2.0  
KG_UCRETI = 45.0       

# Sizin ilk verdiğiniz malzeme ve hız tablosu
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

# 3. SIDEBAR (Seçenekler ve Tablolar)
with st.sidebar:
    st.title("ALAN LAZER")
    metal = st.selectbox("Metal Türü", list(VERİ.keys()))
    kalinlik = st.selectbox("Kalınlık (mm)", VERİ[metal]["kalinliklar"])
    secilen_plaka = st.selectbox("Plaka Boyutu (mm)", ["1500x6000", "1500x3000", "2500x1250"])
    adet = st.number_input("Parça Adedi", min_value=1, value=1)
    referans_olcu = st.number_input("Çizimdeki Genişlik (mm)", value=3295.39)
    
    st.divider()
    # Piercing hassasiyeti (Izgara temizleme için)
    hassasiyet = st.slider("Hassasiyet (Izgara Temizleme)", 50, 255, 180)
    
    # Kesim Hızı Belirleme
    hiz_listesi = VERİ[metal]["hizlar"]
    guncel_hiz = hiz_listesi.get(kalinlik, min(hiz_listesi.values()))
    
    st.divider()
    # Kaybolan Birim Fiyat Tablosu (Sidebar'da gösterim)
    st.subheader("Birim Fiyatlar")
    st.write(f"Dakika Ücreti: **{DK_UCRETI} TL**")
    st.write(f"KG Ücreti: **{KG_UCRETI} TL**")
    st.write(f"Piercing Süresi: **{PIERCING_SURESI} sn**")

# 4. ANA PANEL
st.title("Profesyonel Kesim Analiz Paneli")
uploaded_file = st.file_uploader("Çizim Fotoğrafını Yükle", type=['jpg', 'png', 'jpeg'])

if uploaded_file:
    # Görüntü İşleme
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Seçilen hassasiyete göre siyah-beyaz çevrim
    _, binary = cv2.threshold(gray, hassasiyet, 255, cv2.THRESH_BINARY_INV)
    
    # Kontur Tespiti
    contours, hierarchy = cv2.findContours(binary, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours and hierarchy is not None:
        main_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(main_contour)
        oran = referans_olcu / w
        
        gecerli_konturlar = []
        toplam_yol_piksel = 0

        for i, cnt in enumerate(contours):
            # Hiyerarşi Filtresi (Çizgi kalınlığını tek piercing sayar)
            if hierarchy[0][i][3] == -1 or hierarchy[0][i][3] == 0:
                cevre = cv2.arcLength(cnt, True)
                if cevre * oran > 10.0:
                    gecerli_konturlar.append(cnt)
                    toplam_yol_piksel += cevre
        
        # HESAPLAMALAR
        piercing_basi = len(gecerli_konturlar)
        kesim_yolu_m = (toplam_yol_piksel * oran) / 1000
        
        # Süre ve Maliyet Hesabı
        sure_dk = (kesim_yolu_m * 1000 / guncel_hiz) * adet + (piercing_basi * adet * PIERCING_SURESI / 60)
        agirlik = (cv2.contourArea(main_contour) * (oran**2) * kalinlik * VERİ[metal]["ozkutle"]) / 1e6
        toplam_fiyat = (sure_dk * DK_UCRETI) + (agirlik * adet * KG_UCRETI)

        # GÖRSEL SONUÇ
        output_img = img.copy()
        cv2.drawContours(output_img, gecerli_konturlar, -1, (0, 255, 0), 2)
        st.image(cv2.cvtColor(output_img, cv2.COLOR_BGR2RGB), caption="Analiz Edilen Parça", use_container_width=True)
        
        # ANALİZ TABLOSU
        st.subheader("📋 Kesim Analizi ve Teklif")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Toplam Kesim", f"{round(kesim_yolu_m * adet, 2)} m")
        c2.metric("Piercing Adedi", f"{piercing_basi * adet}")
        c3.metric("Tahmini Süre", f"{round(sure_dk, 1)} dk")
        c4.metric("TOPLAM FİYAT", f"{round(toplam_fiyat, 2)} TL")
        
        # Alt Detay Tablosu (Hız ve Kesim Detayları)
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.write("### Kesim Detayları")
            st.write(f"- Seçilen Malzeme: **{metal} {kalinlik}mm**")
            st.write(f"- Kesim Hızı: **{guncel_hiz} mm/dk**")
            st.write(f"- Toplam Ağırlık: **{round(agirlik * adet, 2)} kg**")
        with col2:
            st.write("### Maliyet Dağılımı")
            st.write(f"- İşçilik Maliyeti: **{round(sure_dk * DK_UCRETI, 2)} TL**")
            st.write(f"- Malzeme Maliyeti: **{round(agirlik * adet * KG_UCRETI, 2)} TL**")
