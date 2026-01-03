import streamlit as st
import cv2
import numpy as np

# 1. SAYFA YAPILANDIRMASI
st.set_page_config(page_title="Alan Lazer Teklif Paneli", layout="wide")

# 2. ÜRETİM VE FİYAT PARAMETRELERİ
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

# 3. SIDEBAR
with st.sidebar:
    st.title("ALAN LAZER")
    metal = st.selectbox("Metal Türü", list(VERİ.keys()))
    kalinlik = st.selectbox("Kalınlık (mm)", VERİ[metal]["kalinliklar"])
    secilen_plaka = st.selectbox("Plaka Boyutu (mm)", ["1500x6000", "1500x3000", "2500x1250"])
    adet = st.number_input("Parça Adedi", min_value=1, value=1)
    referans_olcu = st.number_input("Çizimdeki Genişlik (mm)", value=3295.39)
    
    st.divider()
    hassasiyet = st.slider("Hassasiyet (Izgara Temizleme)", 50, 255, 180)
    
    hiz_listesi = VERİ[metal]["hizlar"]
    guncel_hiz = hiz_listesi.get(kalinlik, min(hiz_listesi.values()))
    
    st.divider()
    st.subheader("Birim Fiyatlar")
    st.write(f"Dakika Ücreti: **{DK_UCRETI} TL**")
    st.write(f"KG Ücreti: **{KG_UCRETI} TL**")

# 4. ANA PANEL
st.title("Profesyonel Kesim Analiz Paneli")
uploaded_file = st.file_uploader("Çizim Fotoğrafını Yükle", type=['jpg', 'png', 'jpeg'])

if uploaded_file:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    _, binary = cv2.threshold(gray, hassasiyet, 255, cv2.THRESH_BINARY_INV)
    contours, hierarchy = cv2.findContours(binary, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours and hierarchy is not None:
        main_contour = max(contours, key=cv2.contourArea)
        
        # BOYUT HESAPLAMA (Bounding Box)
        # Parçanın piksel cinsinden genişlik (w) ve yüksekliği (h)
        x, y, w_px, h_px = cv2.boundingRect(main_contour)
        
        # Oran: Kullanıcının girdiği mm / Piksel genişliği
        oran = referans_olcu / w_px
        
        # Gerçek mm boyutları
        gercek_genislik_mm = w_px * oran
        gercek_yukseklik_mm = h_px * oran
        
        gecerli_konturlar = []
        toplam_yol_piksel = 0

        for i, cnt in enumerate(contours):
            if hierarchy[0][i][3] == -1 or hierarchy[0][i][3] == 0:
                cevre = cv2.arcLength(cnt, True)
                if cevre * oran > 10.0:
                    gecerli_konturlar.append(cnt)
                    toplam_yol_piksel += cevre
        
        # HESAPLAMALAR
        piercing_basi = len(gecerli_konturlar)
        kesim_yolu_m = (toplam_yol_piksel * oran) / 1000
        sure_dk = (kesim_yolu_m * 1000 / guncel_hiz) * adet + (piercing_basi * adet * PIERCING_SURESI / 60)
        agirlik = (cv2.contourArea(main_contour) * (oran**2) * kalinlik * VERİ[metal]["ozkutle"]) / 1e6
        toplam_fiyat = (sure_dk * DK_UCRETI) + (agirlik * adet * KG_UCRETI)

        # GÖRSEL SONUÇ
        output_img = img.copy()
        cv2.drawContours(output_img, gecerli_konturlar, -1, (0, 255, 0), 2)
        
        # Parçanın üzerine veya altına ölçü bilgisi yazdırma (Görselde göstermek için)
        cv2.putText(output_img, f"{round(gercek_genislik_mm, 2)} mm", (x, y - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
        
        st.image(cv2.cvtColor(output_img, cv2.COLOR_BGR2RGB), caption="Analiz Edilen Parça", use_container_width=True)
        
        # ANALİZ TABLOSU
        st.subheader("📋 Kesim Analizi ve Teklif")
        
        # Yeni kolon yapısı (5 Kolon: Genişlik ve Yükseklik dahil)
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Parça Ölçüleri", f"{round(gercek_genislik_mm, 1)} x {round(gercek_yukseklik_mm, 1)} mm")
        m2.metric("Toplam Kesim", f"{round(kesim_yolu_m * adet, 2)} m")
        m3.metric("Piercing Adedi", f"{piercing_basi * adet}")
        m4.metric("Tahmini Süre", f"{round(sure_dk, 1)} dk")
        m5.metric("TOPLAM FİYAT", f"{round(toplam_fiyat, 2)} TL")
        
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.write("### Teknik Detaylar")
            st.write(f"- Parça Genişliği: **{round(gercek_genislik_mm, 2)} mm**")
            st.write(f"- Parça Yüksekliği: **{round(gercek_yukseklik_mm, 2)} mm**")
            st.write(f"- Kesim Hızı: **{guncel_hiz} mm/dk**")
        with col2:
            st.write("### Maliyet Dağılımı")
            st.write(f"- Toplam Ağırlık: **{round(agirlik * adet, 2)} kg**")
            st.write(f"- İşçilik: **{round(sure_dk * DK_UCRETI, 2)} TL**")
            st.write(f"- Malzeme: **{round(agirlik * adet * KG_UCRETI, 2)} TL**")
