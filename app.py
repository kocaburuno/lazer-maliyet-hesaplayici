import streamlit as st
import cv2
import numpy as np

# 1. SAYFA YAPILANDIRMASI
st.set_page_config(page_title="Alan Lazer - Teklif Paneli", layout="wide")

# 2. ÜRETİM PARAMETRELERİ
DK_UCRETI = 25.0       
PIERCING_SURESI = 2.0  
KG_UCRETI = 45.0       

VERİ = {
    "Siyah Sac": {
        "ozkutle": 7.85, 
        "kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20],
        "hizlar": {0.8: 6000, 1: 5500, 2: 4500, 3: 2800, 5: 1800, 10: 800}
    },
    "Paslanmaz": {
        "ozkutle": 8.0, 
        "kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8, 10],
        "hizlar": {0.8: 7000, 2: 4500, 5: 1200, 10: 500}
    },
    "Alüminyum": {
        "ozkutle": 2.7, 
        "kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8],
        "hizlar": {0.8: 8000, 1.5: 6000, 2: 5000, 5: 1500, 8: 600}
    }
}

# 3. SIDEBAR (Sol Panel)
with st.sidebar:
    try:
        st.image("logo.png", use_container_width=True)
    except:
        st.title("ALAN LAZER")
    
    st.subheader("Üretim Seçenekleri")
    metal = st.selectbox("Metal Türü", list(VERİ.keys()))
    kalinlik = st.selectbox("Kalınlık (mm)", VERİ[metal]["kalinliklar"])
    secilen_plaka = st.selectbox("Plaka Boyutu (mm)", ["1500x6000", "1500x3000", "2500x1250", "1000x2000"])
    adet = st.number_input("Parça Adedi", min_value=1, value=1)
    referans_olcu = st.number_input("Çizimdeki Genişlik (mm)", value=3295.0)
    
    st.markdown("---")
    hiz_tablosu = VERİ[metal]["hizlar"]
    guncel_hiz = hiz_tablosu.get(kalinlik, min(hiz_tablosu.values()))
    st.info(f"**Sistem Parametreleri:**\n- Hız: {guncel_hiz} mm/dk\n- İşçilik: {DK_UCRETI} TL/dk")

# 4. ANA EKRAN VE ANALİZ
st.title("Alan Lazer Profesyonel Teklif Paneli")
uploaded_file = st.file_uploader("Çizim Fotoğrafını Yükle", type=['jpg', 'png', 'jpeg'])

if uploaded_file:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Görsel netleştirme (Yeşil çizgilerin doğruluğu için)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 150, 255, cv2.THRESH_BINARY_INV)
    
    # Hiyerarşik kontur tespiti (RETR_CCOMP: Sadece iç ve dış delikleri bulur)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours and hierarchy is not None:
        main_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(main_contour)
        oran = referans_olcu / w
        
        # Plaka Sığma Kontrolü
        p_en, p_boy = w * oran, h * oran
        pl_en_v, pl_boy_v = map(int, secilen_plaka.split('x'))
        if not ((p_en <= pl_en_v and p_boy <= pl_boy_v) or (p_en <= pl_boy_v and p_boy <= pl_en_v)):
            st.error(f"❌ HATA: {round(p_en)}x{round(p_boy)}mm parça {secilen_plaka} plakaya sığmıyor!")
        else:
            # --- ANALİZ DÖNGÜSÜ ---
            gecerli_konturlar = []
            toplam_yol_piksel = 0
            
            # 5mm altındaki toz pürüzlerini piercing saymamak için filtre
            min_cevre_piksel = 5 / oran 

            for i, cnt in enumerate(contours):
                # hierarchy[0][i][3] == -1 -> En dış çerçeve
                # hierarchy[0][i][3] == 0  -> Dış çerçevenin hemen içindeki delikler
                if hierarchy[0][i][3] == -1 or hierarchy[0][i][3] == 0:
                    cevre = cv2.arcLength(cnt, True)
                    if cevre > min_cevre_piksel:
                        gecerli_konturlar.append(cnt)
                        toplam_yol_piksel += cevre
            
            # Hesaplamalar
            piercing_basi = len(gecerli_konturlar) # Hedef: 49
            piercing_toplam = piercing_basi * adet
            kesim_yolu_m = (toplam_yol_piksel * oran) / 1000
            
            sure_dk = (kesim_yolu_m * 1000 / guncel_hiz) * adet + (piercing_toplam * PIERCING_SURESI / 60)
            agirlik = (cv2.contourArea(main_contour) * (oran**2) * kalinlik * VERİ[metal]["ozkutle"]) / 1e6
            toplam_fiyat = (sure_dk * DK_UCRETI) + (agirlik * adet * KG_UCRETI)

            # YEŞİL KONTUR ÇİZİMİ (Belirginleştirilmiş)
            output_img = img.copy()
            cv2.drawContours(output_img, gecerli_konturlar, -1, (0, 255, 0), 3) # Kalınlık 3 yapıldı
            
            st.image(cv2.cvtColor(output_img, cv2.COLOR_BGR2RGB), use_container_width=True)
            
            # SONUÇLAR
            st.subheader("📋 Kesim Analizi ve Teklif")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Toplam Kesim", f"{round(kesim_yolu_m, 1)} m")
            c2.metric("Piercing Adedi", f"{piercing_toplam}")
            c3.metric("Tahmini Süre", f"{round(sure_dk, 1)} dk")
            c4.metric("TOPLAM FİYAT", f"{round(toplam_fiyat, 2)} TL")
            
            with st.expander("Maliyet Detayları"):
                st.write(f"**Parça Boyutu:** {round(p_en)} x {round(p_boy)} mm")
                st.write(f"**Birim Piercing:** {piercing_basi} adet (1 Dış + {piercing_basi-1} İç)")
                st.write(f"**Malzeme Ağırlığı:** {round(agirlik, 2)} kg")
