import streamlit as st
import cv2
import numpy as np

# 1. SAYFA YAPILANDIRMASI
st.set_page_config(page_title="Alan Lazer Teklif Paneli", layout="wide")

# 2. ÜRETİM VE FİYAT PARAMETRELERİ (Sabit)
DK_UCRETI = 25.0       
PIERCING_SURESI = 2.0  
KG_UCRETI = 45.0       

VERİ = {
    "Siyah Sac": {
        "ozkutle": 7.85, 
        "kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20], 
        "hizlar": {0.8: 6000, 3: 2800, 10: 800}
    },
    "Paslanmaz": {
        "ozkutle": 8.0, 
        "kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8, 10, 12, 15], 
        "hizlar": {0.8: 7000, 2: 4500, 10: 500}
    },
    "Alüminyum": {
        "ozkutle": 2.7, 
        "kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8], 
        "hizlar": {0.8: 8000, 2: 5000, 8: 600}
    }
}

# 3. SIDEBAR (Logo Geri Getirildi)
with st.sidebar:
    # --- DÜZELTME 1: LOGO ---
    st.markdown("<h1 style='text-align: center; color: red;'>ALAN LAZER</h1>", unsafe_allow_html=True)
    st.divider()
    
    metal = st.selectbox("Metal Türü", list(VERİ.keys()))
    kalinlik = st.selectbox("Kalınlık (mm)", VERİ[metal]["kalinliklar"])
    
    plaka_secenekleri = {"1500x6000": (1500, 6000), "1500x3000": (1500, 3000), "2500x1250": (2500, 1250)}
    secilen_plaka_adi = st.selectbox("Plaka Boyutu (mm)", list(plaka_secenekleri.keys()))
    secilen_p_en, secilen_p_boy = plaka_secenekleri[secilen_plaka_adi]
    
    adet = st.number_input("Parça Adedi", min_value=1, value=1)
    referans_olcu = st.number_input("Çizimdeki Genişlik (mm)", value=3295.39)
    
    st.divider()
    hassasiyet = st.slider("Hassasiyet (Izgara Temizleme)", 50, 255, 84) # Resminizdeki 84 değerine çekildi
    
    hiz_tablosu = VERİ[metal]["hizlar"]
    tanimli_k = sorted(hiz_tablosu.keys())
    uygun_k = tanimli_k[0]
    for k in tanimli_k:
        if kalinlik >= k: uygun_k = k
    guncel_hiz = hiz_tablosu[uygun_k]

# 4. ANA PANEL
st.title("Profesyonel Kesim Analiz Paneli")
uploaded_file = st.file_uploader("Çizim Fotoğrafını Yükle", type=['jpg', 'png', 'jpeg'])

if uploaded_file:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    original_img = cv2.imdecode(file_bytes, 1)
    gray = cv2.cvtColor(original_img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, hassasiyet, 255, cv2.THRESH_BINARY_INV)
    contours, hierarchy = cv2.findContours(binary, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours and hierarchy is not None:
        # --- DÜZELTME 2: GENİŞLİK HESAPLAMA MANTIĞI ---
        # Tüm konturların oluşturduğu en dış dikdörtgeni (bounding box) baz alıyoruz
        all_pts = np.concatenate(contours)
        x, y, w_px, h_px = cv2.boundingRect(all_pts)
        
        # Referans ölçü çizimin en dış genişliğine atanır
        oran = referans_olcu / w_px
        gercek_genislik = w_px * oran
        gercek_yukseklik = h_px * oran
        
        # Plaka Kontrolü
        p_max, p_min = max(secilen_p_en, secilen_p_boy), min(secilen_p_en, secilen_p_boy)
        g_max, g_min = max(gercek_genislik, gercek_yukseklik), min(gercek_genislik, gercek_yukseklik)
        
        if g_max > p_max or g_min > p_min:
            st.error(f"⚠️ HATA: Parça ({round(gercek_genislik)}x{round(gercek_yukseklik)}mm), {secilen_plaka_adi} plakaya sığmıyor!")
        else:
            gecerli_konturlar = []
            toplam_yol_piksel = 0
            for i, cnt in enumerate(contours):
                if hierarchy[0][i][3] == -1 or hierarchy[0][i][3] == 0:
                    cevre = cv2.arcLength(cnt, True)
                    if cevre * oran > 10.0:
                        gecerli_konturlar.append(cnt)
                        toplam_yol_piksel += cevre
            
            display_img = original_img.copy()
            cv2.drawContours(display_img, gecerli_konturlar, -1, (0, 255, 0), 2)
            rgb_img = cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB)
            st.image(rgb_img, caption="Tespit Edilen Kesim Hatları (Yeşil)", use_container_width=True)

            piercing_basi = len(gecerli_konturlar)
            kesim_yolu_m = (toplam_yol_piksel * oran) / 1000
            sure_dk = (kesim_yolu_m * 1000 / guncel_hiz) * adet + (piercing_basi * adet * PIERCING_SURESI / 60)
            agirlik = (cv2.contourArea(all_pts) * (oran**2) * kalinlik * VERİ[metal]["ozkutle"]) / 1e6
            toplam_fiyat = (sure_dk * DK_UCRETI) + (agirlik * adet * KG_UCRETI)

            st.subheader("📋 Teklif Özeti")
            m1, m2, m3, m4 = st.columns([1.5, 1, 1, 1.2])
            # Genişlik şimdi tam olarak "Çizimdeki Genişlik" girdisine eşit çıkacaktır
            m1.metric("Parça Ölçüsü (GxY)", f"{round(gercek_genislik, 1)} x {round(gercek_yukseklik, 1)} mm")
            m2.metric("Toplam Kesim", f"{round(kesim_yolu_m * adet, 2)} m")
            m3.metric("Piercing", f"{piercing_basi * adet} ad")
            m4.metric("TOPLAM FİYAT", f"{round(toplam_fiyat, 2)} TL")
            
            with st.expander("🔍 Teknik Detaylar ve Maliyet Dökümü"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"- Genişlik: {round(gercek_genislik, 2)} mm")
                    st.write(f"- Yükseklik: {round(gercek_yukseklik, 2)} mm")
                with col2:
                    st.write(f"- Kesim Hızı: {guncel_hiz} mm/dk")
                    st.write(f"- Birim Ağırlık: {round(agirlik, 2)} kg")
                with col3:
                    st.write(f"- İşçilik: {round(sure_dk * DK_UCRETI, 2)} TL")
                    st.write(f"- Malzeme: {round(agirlik * adet * KG_UCRETI, 2)} TL")
