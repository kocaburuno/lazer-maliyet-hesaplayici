import streamlit as st
import cv2
import numpy as np

# 1. SAYFA YAPILANDIRMASI
st.set_page_config(page_title="Teklif Paneli", layout="wide")

# 2. MALZEME VERİLERİ (Tüm Kalınlıklar Geri Geldi)
VERİ = {
    "Siyah Sac": {
        "ozkutle": 7.85, 
        "kalinliklar": [0.5, 0.8, 1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25],
        "hizlar": {1: 5500, 3: 2800, 5: 1800, 10: 800, 20: 400}
    },
    "Paslanmaz": {
        "ozkutle": 8.0, 
        "kalinliklar": [0.5, 0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8, 10, 12, 15],
        "hizlar": {1: 6000, 2: 4500, 5: 1200, 10: 500}
    },
    "Alüminyum": {
        "ozkutle": 2.7, 
        "kalinliklar": [0.5, 0.8, 1, 1.5, 2, 3, 4, 5, 6, 8, 10],
        "hizlar": {1: 8000, 3: 4000, 5: 1500, 10: 400}
    }
}

DK_UCRETI = 25.0
PIERCING_SURESI = 2.0
KG_UCRETI = 45.0

# 3. SIDEBAR
with st.sidebar:
    try: st.image("logo.png", use_container_width=True)
    except: st.title("LOGO")
    
    metal = st.selectbox("Metal Türü", list(VERİ.keys()))
    kalinlik = st.selectbox("Kalınlık (mm)", VERİ[metal]["kalinliklar"])
    secilen_plaka = st.selectbox("Plaka Boyutu (mm)", ["1500x6000", "1500x3000", "2500x1250"])
    adet = st.number_input("Parça Adedi", min_value=1, value=1)
    referans_olcu = st.number_input("Çizimdeki Genişlik (mm)", value=3295.0)
    
    hizlar = VERİ[metal]["hizlar"]
    guncel_hiz = hizlar.get(kalinlik, min(hizlar.values()))

# 4. ANA PANEL
st.title("Profesyonel Teklif Paneli")
uploaded_file = st.file_uploader("Çizim Fotoğrafını Yükle", type=['jpg', 'png', 'jpeg'])

if uploaded_file:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Eşikleme (Siyah-Beyaz Dönüşümü)
    # Fotoğraftaki her detayı yakalamak için threshold değerini 200'e çektik
    _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    
    # Hiyerarşik Kontur Tespiti (RETR_TREE: Tüm iç içe yapıları bulur)
    contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours and hierarchy is not None:
        main_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(main_contour)
        oran = referans_olcu / w
        
        gecerli_konturlar = []
        toplam_yol_piksel = 0
        
        # --- TÜM KONTURLARI BULAN MANTIK ---
        for i, cnt in enumerate(contours):
            # En dış çerçeve veya hemen bir altındaki delikler (piercing noktaları)
            # hierarchy[0][i][3] değeri üst seviyeyi belirtir.
            if hierarchy[0][i][3] == -1 or hierarchy[0][i][3] == 0:
                # Çok küçük tozları elemek için çok düşük bir eşik (min 1mm çevre)
                if cv2.arcLength(cnt, True) * oran > 1.0:
                    gecerli_konturlar.append(cnt)
                    toplam_yol_piksel += cv2.arcLength(cnt, True)
        
        # Analitik Sonuçlar
        piercing_basi = len(gecerli_konturlar)
        piercing_toplam = piercing_basi * adet
        kesim_m = (toplam_yol_piksel * oran) / 1000
        
        sure_dk = (kesim_m * 1000 / guncel_hiz) * adet + (piercing_toplam * PIERCING_SURESI / 60)
        agirlik = (cv2.contourArea(main_contour) * (oran**2) * kalinlik * VERİ[metal]["ozkutle"]) / 1e6
        fiyat = (sure_dk * DK_UCRETI) + (agirlik * adet * KG_UCRETI)

        # GÖRSELLEŞTİRME: İnce Yeşil Çizgi ile Tüm Konturlar
        output_img = img.copy()
        cv2.drawContours(output_img, gecerli_konturlar, -1, (0, 255, 0), 1)
        st.image(cv2.cvtColor(output_img, cv2.COLOR_BGR2RGB), use_container_width=True)
        
        # ÖZET TABLOSU
        st.subheader("📋 Kesim Analizi ve Teklif")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Toplam Kesim", f"{round(kesim_m, 1)} m")
        c2.metric("Piercing Adedi", f"{piercing_toplam}")
        c3.metric("Tahmini Süre", f"{round(sure_dk, 1)} dk")
        c4.metric("TOPLAM FİYAT", f"{round(fiyat, 2)} TL")
        
        with st.expander("Maliyet Detayları & Sac Bilgileri"):
            st.write(f"**Seçilen Malzeme:** {metal} {kalinlik}mm")
            st.write(f"**Birim Başına Piercing:** {piercing_basi} (48 iç + 1 dış)")
            st.write(f"**Net Ağırlık:** {round(agirlik, 2)} kg")
