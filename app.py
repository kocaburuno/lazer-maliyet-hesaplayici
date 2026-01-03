import streamlit as st
import cv2
import numpy as np

# 1. SAYFA YAPILANDIRMASI
st.set_page_config(page_title="Alan Lazer Teklif Paneli", layout="wide")

# 2. ÜRETİM VE FİYAT PARAMETRELERİ (İlk verdiğiniz orijinal veriler)
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
    
    # Plaka ebatları
    plaka_secenekleri = {
        "1500x6000": (1500, 6000),
        "1500x3000": (1500, 3000),
        "2500x1250": (2500, 1250)
    }
    secilen_plaka_adi = st.selectbox("Plaka Boyutu (mm)", list(plaka_secenekleri.keys()))
    secilen_p_en, secilen_p_boy = plaka_secenekleri[secilen_plaka_adi]
    
    adet = st.number_input("Parça Adedi", min_value=1, value=1)
    referans_olcu = st.number_input("Çizimdeki Genişlik (mm)", value=3295.39)
    
    st.divider()
    hassasiyet = st.slider("Hassasiyet (Izgara Temizleme)", 50, 255, 180)
    
    hiz_listesi = VERİ[metal]["hizlar"]
    guncel_hiz = hiz_listesi.get(kalinlik, min(hiz_listesi.values()))

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
        x, y, w_px, h_px = cv2.boundingRect(main_contour)
        
        # Oran ve Boyut Hesaplama
        oran = referans_olcu / w_px
        gercek_genislik = w_px * oran
        gercek_yukseklik = h_px * oran
        
        # --- PLAKA EBAT KONTROLÜ (MADDER 3) ---
        # Parçanın herhangi bir boyutu plaka boyutundan büyükse hata ver
        p_max = max(secilen_p_en, secilen_p_boy)
        p_min = min(secilen_p_en, secilen_p_boy)
        g_max = max(gercek_genislik, gercek_yukseklik)
        g_min = min(gercek_genislik, gercek_yukseklik)
        
        if g_max > p_max or g_min > p_min:
            st.error(f"⚠️ HATA: Parça boyutları ({round(gercek_genislik)}x{round(gercek_yukseklik)} mm), seçilen plakaya ({secilen_plaka_adi} mm) sığmıyor! Lütfen daha büyük bir plaka seçin.")
        else:
            # Hesaplamalara devam et
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
            st.image(cv2.cvtColor(output_img, cv2.COLOR_BGR2RGB), caption="Analiz Edilen Kesim Yolları", use_container_width=True)
            
            # ÖZET METRİKLER
            st.subheader("📋 Teklif Özeti")
            m1, m2, m3, m4 = st.columns([1.5, 1, 1, 1.2])
            m1.metric("Parça Ölçüsü (GxY)", f"{round(gercek_genislik, 1)} x {round(gercek_yukseklik, 1)} mm")
            m2.metric("Toplam Kesim", f"{round(kesim_yolu_m * adet, 2)} m")
            m3.metric("Piercing", f"{piercing_basi * adet} ad")
            m4.metric("TOPLAM FİYAT", f"{round(toplam_fiyat, 2)} TL")
            
            with st.expander("🔍 Teknik Detaylar ve Maliyet Dökümü"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write("**Parça Bilgisi**")
                    st.write(f"- Genişlik: {round(gercek_genislik, 2)} mm")
                    st.write(f"- Yükseklik: {round(gercek_yukseklik, 2)} mm")
                with col2:
                    st.write("**Operasyon**")
                    st.write(f"- Kesim Hızı: {guncel_hiz} mm/dk")
                    st.write(f"- Birim Ağırlık: {round(agirlik, 2)} kg")
                with col3:
                    st.write("**Maliyet**")
                    st.write(f"- İşçilik: {round(sure_dk * DK_UCRETI, 2)} TL")
                    st.write(f"- Malzeme: {round(agirlik * adet * KG_UCRETI, 2)} TL")
