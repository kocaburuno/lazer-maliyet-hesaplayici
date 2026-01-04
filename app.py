import streamlit as st
from PIL import Image
import cv2
import numpy as np
import math

# --- 1. AYARLAR VE FAVICON ---
try:
    fav_icon = Image.open("tarayici.png")
except:
    fav_icon = None 

st.set_page_config(page_title="Alan Lazer Teklif Paneli", layout="wide", page_icon=fav_icon)

# 2. SABİT PARAMETRELER
DK_UCRETI = 25.0       
PIERCING_SURESI = 2.0  
FIRE_ORANI = 1.15 # %15 Fire
KDV_ORANI = 1.20  # %20 KDV

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

# 3. SIDEBAR (KOMPAKT TASARIM)
with st.sidebar:
    try:
        st.image("logo.png", use_column_width=True)
    except:
        st.markdown("<h1 style='text-align: center; color: #FF4B4B;'>ALAN LAZER</h1>", unsafe_allow_html=True)
        
    st.markdown("---")
    
    # 1. SATIR: Metal ve Kalınlık Yan Yana (REVİZE: Metal ismine daha fazla yer verildi)
    col_s1, col_s2 = st.columns([2, 1])
    with col_s1:
        metal = st.selectbox("Metal Türü", list(VERİ.keys()))
    with col_s2:
        kalinlik = st.selectbox("Kalınlık (mm)", VERİ[metal]["kalinliklar"])
    
    # 2. SATIR: Plaka ve Adet Yan Yana
    col_s3, col_s4 = st.columns([2, 1])
    with col_s3:
        plaka_secenekleri = {"1500x6000": (1500, 6000), "1500x3000": (1500, 3000), "2500x1250": (2500, 1250)}
        secilen_plaka_adi = st.selectbox("Plaka", list(plaka_secenekleri.keys()))
        secilen_p_en, secilen_p_boy = plaka_secenekleri[secilen_plaka_adi]
    with col_s4:
        adet = st.number_input("Adet", min_value=1, value=1, step=1)
    
    # Hız Belirleme
    hiz_tablosu = VERİ[metal]["hizlar"]
    tanimli_k = sorted(hiz_tablosu.keys())
    uygun_k = tanimli_k[0]
    for k in tanimli_k:
        if kalinlik >= k: uygun_k = k
    guncel_hiz = hiz_tablosu[uygun_k]

    # Fiyat Belirleme
    varsayilan_fiyat = 30.0
    if metal == "Siyah Sac": varsayilan_fiyat = 30.0
    elif metal == "Paslanmaz": varsayilan_fiyat = 150.0
    elif metal == "Alüminyum": varsayilan_fiyat = 220.0
    
    st.markdown("---")
    
    # 3. SATIR: Fiyat Girişi
    kg_fiyati = st.number_input(
        "Malzeme KG Fiyatı (TL)", 
        min_value=0.0, 
        value=varsayilan_fiyat, 
        step=10.0, 
        format="%g",
        help="Birim fiyat"
    )

    st.markdown("---")
    
    # 4. SATIR: Bilgi Kutucukları
    col_i1, col_i2 = st.columns(2)
    with col_i1:
        st.info(f"Hız:\n{guncel_hiz}")
    with col_i2:
        st.success(f"Birim:\n{kg_fiyati} TL")

# 4. ANA PANEL
st.title("Profesyonel Kesim Analiz Paneli")

tab1, tab2 = st.tabs(["📷 FOTOĞRAFTAN ANALİZ", "🛠 HAZIR PARÇA OLUŞTUR"])

# --- TAB 1: FOTO ANALİZ ---
with tab1:
    c_analiz_ayar, c_analiz_sonuc = st.columns([1, 2])

    with c_analiz_ayar:
        st.subheader("Analiz Ayarları")
        referans_olcu = st.number_input(
            "Parçanın Yatay Uzunluğu (mm)", 
            value=3295.39, 
            step=10.0, 
            format="%g",
            help="Yüklediğiniz çizimdeki parçanın soldan sağa (yatay) olan gerçek uzunluğunu giriniz."
        )
        hassasiyet = st.slider("Hassasiyet (Izgara Temizleme)", 50, 255, 84, step=1)
        st.divider()
        uploaded_file = st.file_uploader("Çizim Fotoğrafını Yükle", type=['jpg', 'png', 'jpeg'])

    with c_analiz_sonuc:
        if uploaded_file:
            file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            original_img = cv2.imdecode(file_bytes, 1)
            h_img, w_img = original_img.shape[:2] 
            
            gray = cv2.cvtColor(original_img, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray, hassasiyet, 255, cv2.THRESH_BINARY_INV)
            contours, hierarchy = cv2.findContours(binary, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours and hierarchy is not None:
                valid_contour_list = []
                for i, cnt in enumerate(contours):
                    x, y, w, h = cv2.boundingRect(cnt)
                    if w > w_img * 0.98 and h > h_img * 0.98: continue
                    if hierarchy[0][i][3] == -1 or hierarchy[0][i][3] == 0:
                        valid_contour_list.append(cnt)

                if valid_contour_list:
                    all_pts = np.concatenate(valid_contour_list)
                    x_real, y_real, w_px, h_px = cv2.boundingRect(all_pts)
                    
                    oran = referans_olcu / w_px
                    gercek_genislik = w_px * oran
                    gercek_yukseklik = h_px * oran
                    
                    p_max, p_min = max(secilen_p_en, secilen_p_boy), min(secilen_p_en, secilen_p_boy)
                    g_max, g_min = max(gercek_genislik, gercek_yukseklik), min(gercek_genislik, gercek_yukseklik)
                    
                    display_img = original_img.copy()
                    cv2.drawContours(display_img, valid_contour_list, -1, (0, 255, 0), 2)
                    rgb_img = cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB)
                    
                    st.image(rgb_img, caption="Analiz Edilen Parça", use_container_width=True)

                    if g_max > p_max or g_min > p_min:
                        st.error(f"⚠️ HATA: Parça ({round(gercek_genislik)}x{round(gercek_yukseklik)}mm), seçilen plakaya sığmıyor!")
                    else:
                        toplam_yol_piksel = sum([cv2.arcLength(c, True) for c in valid_contour_list])
                        piercing_basi = len(valid_contour_list)
                        kesim_yolu_m = (toplam_yol_piksel * oran) / 1000
                        sure_dk = (kesim_yolu_m * 1000 / guncel_hiz) * adet + (piercing_basi * adet * PIERCING_SURESI / 60)
                        
                        ham_agirlik = (cv2.contourArea(all_pts) * (oran**2) * kalinlik * VERİ[metal]["ozkutle"]) / 1e6
                        agirlik = ham_agirlik * FIRE_ORANI
                        
                        toplam_fiyat = (sure_dk * DK_UCRETI) + (agirlik * adet * kg_fiyati)
                        kdvli_fiyat = toplam_fiyat * KDV_ORANI

                        st.markdown("### 📋 Teklif Özeti")
                        m1, m2, m3, m4 = st.columns([1, 1, 1, 1.5])
                        m1.metric("Ölçü (GxY)", f"{round(gercek_genislik, 1)} x {round(gercek_yukseklik, 1)}")
                        m2.metric("Kesim", f"{round(kesim_yolu_m * adet, 2)} m")
                        m3.metric("Piercing", f"{piercing_basi * adet} ad")
                        
                        m4.metric("KDV HARİÇ", f"{round(toplam_fiyat, 2)} TL")
                        m4.markdown(f"<span style='color:green; font-weight:bold;'>KDV DAHİL: {round(kdvli_fiyat, 2)} TL</span>", unsafe_allow_html=True)
                        
                        with st.expander("🔍 Teknik Detaylar"):
                            st.write(f"- Parça Ağırlığı (+%15 Fire): {round(agirlik, 2)} kg")
                            st.write(f"- İşçilik: {round(sure_dk * DK_UCRETI, 2)} TL")
                            st.write(f"- Malzeme: {round(agirlik * adet * kg_fiyati, 2)} TL")
        else:
             st.info("Lütfen sol taraftan bir çizim görseli yükleyiniz.")

# --- TAB 2: HAZIR PARÇA OLUŞTUR ---
with tab2:
    c_ayar, c_sonuc = st.columns([1, 2])
    
    with c_ayar:
        st.subheader("Parça Ayarları")
        sekil_tipi = st.radio("Parça Tipi", ["Kare / Dikdörtgen", "Daire / Flanş"])
        st.divider()
        
        if sekil_tipi == "Kare / Dikdörtgen":
            genislik = st.number_input("Genişlik (mm)", min_value=1.0, value=100.0, step=10.0, format="%g")
            yukseklik = st.number_input("Yükseklik (mm)", min_value=1.0, value=100.0, step=10.0, format="%g")
            delik_sayisi = st.number_input("Delik Sayısı", min_value=0, value=0, step=1)
            delik_capi = st.number_input("Delik Çapı (mm)", min_value=0.0, value=10.0, step=1.0, format="%g")
            
            canvas = np.zeros((300, 600, 3), dtype="uint8")
            max_dim = max(genislik, yukseklik)
            scale = 250 / max_dim
            w_px = int(genislik * scale)
            h_px = int(yukseklik * scale)
            start_x = (600 - w_px) // 2
            start_y = (300 - h_px) // 2
            cv2.rectangle(canvas, (start_x, start_y), (start_x + w_px, start_y + h_px), (0, 255, 0), 2)
            
            if delik_sayisi > 0 and delik_capi > 0:
                d_px_r = int((delik_capi * scale) / 2)
                padding = d_px_r + 10 
                coords = [(start_x + padding, start_y + padding), (start_x + w_px - padding, start_y + padding),
                          (start_x + w_px - padding, start_y + h_px - padding), (start_x + padding, start_y + h_px - padding)]
                if delik_sayisi == 1: cv2.circle(canvas, (300, 150), d_px_r, (0, 255, 0), 2)
                else:
                    for i in range(min(delik_sayisi, 4)): cv2.circle(canvas, coords[i], d_px_r, (0, 255, 0), 2)

            cevre_dis = 2 * (genislik + yukseklik)
            cevre_ic = delik_sayisi * (math.pi * delik_capi)
            toplam_kesim_mm = cevre_dis + cevre_ic
            alan_dis = genislik * yukseklik
            alan_ic = delik_sayisi * (math.pi * (delik_capi/2)**2)
            net_alan_mm2 = alan_dis - alan_ic
            piercing_sayisi = 1 + delik_sayisi

        elif sekil_tipi == "Daire / Flanş":
            cap = st.number_input("Dış Çap (mm)", min_value=1.0, value=100.0, step=10.0, format="%g")
            delik_sayisi = st.number_input("İç Delik Sayısı", min_value=0, value=1, step=1)
            delik_capi = st.number_input("Delik Çapı (mm)", min_value=0.0, value=50.0, step=1.0, format="%g")
            
            canvas = np.zeros((300, 400, 3), dtype="uint8")
            r_px = 120
            center = (200, 150)
            cv2.circle(canvas, center, r_px, (0, 255, 0), 2)
            if delik_sayisi > 0 and delik_capi > 0:
                d_px_r = int(((delik_capi / cap) * r_px * 2) / 2)
                if delik_sayisi == 1: cv2.circle(canvas, center, d_px_r, (0, 255, 0), 2)
                else:
                    pcd_radius = int(r_px * 0.7) 
                    for i in range(delik_sayisi):
                        angle = (2 * math.pi / delik_sayisi) * i
                        cv2.circle(canvas, (center[0] + int(pcd_radius * math.cos(angle)), center[1] + int(pcd_radius * math.sin(angle))), d_px_r, (0, 255, 0), 2)
            
            cevre_dis = math.pi * cap
            cevre_ic = delik_sayisi * (math.pi * delik_capi)
            toplam_kesim_mm = cevre_dis + cevre_ic
            alan_dis = math.pi * (cap/2)**2
            alan_ic = delik_sayisi * (math.pi * (delik_capi/2)**2)
            net_alan_mm2 = alan_dis - alan_ic
            piercing_sayisi = 1 + delik_sayisi
            genislik, yukseklik = cap, cap

    with c_sonuc:
        p_max, p_min = max(secilen_p_en, secilen_p_boy), min(secilen_p_en, secilen_p_boy)
        g_max, g_min = max(genislik, yukseklik), min(genislik, yukseklik)
        st.image(canvas, caption=f"{genislik}x{yukseklik}mm", use_container_width=True)

        if g_max > p_max or g_min > p_min:
            st.error(f"⚠️ HATA: Parça ({genislik}x{yukseklik}mm), seçilen plakaya sığmıyor!")
        else:
            kesim_yolu_m = toplam_kesim_mm / 1000
            sure_dk = (kesim_yolu_m * 1000 / guncel_hiz) * adet + (piercing_sayisi * adet * PIERCING_SURESI / 60)
            ham_agirlik = (net_alan_mm2 * kalinlik * VERİ[metal]["ozkutle"]) / 1e6
            agirlik = ham_agirlik * FIRE_ORANI
            toplam_fiyat = (sure_dk * DK_UCRETI) + (agirlik * adet * kg_fiyati)
            kdvli_fiyat = toplam_fiyat * KDV_ORANI
            
            st.markdown("### 📋 Teklif Özeti")
            m1, m2, m3, m4 = st.columns([1, 1, 1, 1.5])
            m1.metric("Ölçü", f"{genislik}x{yukseklik}")
            m2.metric("Kesim", f"{round(kesim_yolu_m * adet, 2)} m")
            m3.metric("Piercing", f"{piercing_sayisi * adet} ad")
            m4.metric("KDV HARİÇ", f"{round(toplam_fiyat, 2)} TL")
            m4.markdown(f"<span style='color:green; font-weight:bold;'>KDV DAHİL: {round(kdvli_fiyat, 2)} TL</span>", unsafe_allow_html=True)
            
            with st.expander("🔍 Teknik Detaylar"):
                st.write(f"- Parça Ağırlığı (+%15 Fire): {round(agirlik, 2)} kg")
                st.write(f"- İşçilik: {round(sure_dk * DK_UCRETI, 2)} TL")
                st.write(f"- Malzeme: {round(agirlik * adet * kg_fiyati, 2)} TL")
