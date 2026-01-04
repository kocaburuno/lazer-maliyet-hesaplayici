import streamlit as st
import cv2
import numpy as np
import math

# 1. SAYFA YAPILANDIRMASI
st.set_page_config(page_title="Alan Lazer Teklif Paneli", layout="wide", page_icon="tarayici.png")

# 2. SABİT PARAMETRELER
DK_UCRETI = 25.0       
PIERCING_SURESI = 2.0  

# Malzeme veritabanı (Kalınlık ve Hızlar)
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

# 3. SIDEBAR (AYARLAR VE GİRİŞLER)
with st.sidebar:
    try:
        st.image("logo.png", use_column_width=True)
    except:
        st.markdown("<h1 style='text-align: center; color: #FF4B4B;'>ALAN LAZER</h1>", unsafe_allow_html=True)
        
    st.markdown("---")
    
    # Metal ve Kalınlık Seçimi
    metal = st.selectbox("Metal Türü", list(VERİ.keys()))
    kalinlik = st.selectbox("Kalınlık (mm)", VERİ[metal]["kalinliklar"])
    
    # Plaka Seçimi
    plaka_secenekleri = {"1500x6000": (1500, 6000), "1500x3000": (1500, 3000), "2500x1250": (2500, 1250)}
    secilen_plaka_adi = st.selectbox("Plaka Boyutu (mm)", list(plaka_secenekleri.keys()))
    secilen_p_en, secilen_p_boy = plaka_secenekleri[secilen_plaka_adi]
    
    adet = st.number_input("Parça Adedi", min_value=1, value=1)
    
    # Hız Belirleme
    hiz_tablosu = VERİ[metal]["hizlar"]
    tanimli_k = sorted(hiz_tablosu.keys())
    uygun_k = tanimli_k[0]
    for k in tanimli_k:
        if kalinlik >= k: uygun_k = k
    guncel_hiz = hiz_tablosu[uygun_k]

    st.markdown("---")
    
    # --- YENİ EKLENEN BÖLÜM: DEĞİŞTİRİLEBİLİR FİYAT ---
    # Varsayılan fiyatları belirle
    varsayilan_fiyat = 30.0
    if metal == "Siyah Sac":
        varsayilan_fiyat = 30.0
    elif metal == "Paslanmaz":
        varsayilan_fiyat = 150.0
    elif metal == "Alüminyum":
        varsayilan_fiyat = 220.0
        
    # Kullanıcıya değiştirebileceği bir alan sun (key=metal ile her metal değişiminde resetlenir)
    kg_fiyati = st.number_input("Malzeme KG Fiyatı (TL)", min_value=0.0, value=varsayilan_fiyat, format="%.2f", help="Birim kilogram fiyatını buradan güncelleyebilirsiniz.")
    # --------------------------------------------------

    st.markdown("---")
    st.subheader("Birim Bilgiler")
    st.info(f"Kesim Hızı: {guncel_hiz} mm/dk")
    st.success(f"Hesaplanan KG Fiyatı: {kg_fiyati} TL")

# 4. ANA PANEL
st.title("Profesyonel Kesim Analiz Paneli")

tab1, tab2 = st.tabs(["📷 FOTOĞRAFTAN ANALİZ", "🛠 HAZIR PARÇA OLUŞTUR"])

# --- SEKME 1: FOTOĞRAF ANALİZİ ---
with tab1:
    col_ref, col_hassas = st.columns(2)
    with col_ref:
        referans_olcu = st.number_input("Parçanın En Geniş Uzunluğu (mm)", value=3295.39, help="Çizimdeki parçanın en solundan en sağına olan gerçek ölçü.")
    with col_hassas:
        hassasiyet = st.slider("Hassasiyet (Izgara Temizleme)", 50, 255, 84)

    uploaded_file = st.file_uploader("Çizim Fotoğrafını Yükle", type=['jpg', 'png', 'jpeg'])

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
                # Dış çerçeve filtresi
                if w > w_img * 0.98 and h > h_img * 0.98: continue
                # Hiyerarşi filtresi
                if hierarchy[0][i][3] == -1 or hierarchy[0][i][3] == 0:
                    valid_contour_list.append(cnt)

            if valid_contour_list:
                all_pts = np.concatenate(valid_contour_list)
                x_real, y_real, w_px, h_px = cv2.boundingRect(all_pts)
                
                oran = referans_olcu / w_px
                gercek_genislik = w_px * oran
                gercek_yukseklik = h_px * oran
                
                # Plaka Kontrolü
                p_max, p_min = max(secilen_p_en, secilen_p_boy), min(secilen_p_en, secilen_p_boy)
                g_max, g_min = max(gercek_genislik, gercek_yukseklik), min(gercek_genislik, gercek_yukseklik)
                
                if g_max > p_max or g_min > p_min:
                    st.error(f"⚠️ HATA: Parça ({round(gercek_genislik)}x{round(gercek_yukseklik)}mm), seçilen plakaya sığmıyor!")
                else:
                    toplam_yol_piksel = sum([cv2.arcLength(c, True) for c in valid_contour_list])
                    
                    display_img = original_img.copy()
                    cv2.drawContours(display_img, valid_contour_list, -1, (0, 255, 0), 2)
                    rgb_img = cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB)
                    st.image(rgb_img, caption="Analiz Edilen Parça", use_container_width=True)

                    piercing_basi = len(valid_contour_list)
                    kesim_yolu_m = (toplam_yol_piksel * oran) / 1000
                    sure_dk = (kesim_yolu_m * 1000 / guncel_hiz) * adet + (piercing_basi * adet * PIERCING_SURESI / 60)
                    agirlik = (cv2.contourArea(all_pts) * (oran**2) * kalinlik * VERİ[metal]["ozkutle"]) / 1e6
                    # Fiyat hesabı (değiştirilebilir kg_fiyati kullanılıyor)
                    toplam_fiyat = (sure_dk * DK_UCRETI) + (agirlik * adet * kg_fiyati)

                    st.subheader("📋 Teklif Özeti")
                    m1, m2, m3, m4 = st.columns([1.5, 1, 1, 1.2])
                    m1.metric("Parça Ölçüsü (GxY)", f"{round(gercek_genislik, 1)} x {round(gercek_yukseklik, 1)} mm")
                    m2.metric("Toplam Kesim", f"{round(kesim_yolu_m * adet, 2)} m")
                    m3.metric("Piercing", f"{piercing_basi * adet} ad")
                    m4.metric("TOPLAM FİYAT", f"{round(toplam_fiyat, 2)} TL")
                    
                    with st.expander("🔍 Teknik Detaylar"):
                        st.write(f"- Parça Ağırlığı: {round(agirlik, 2)} kg")
                        st.write(f"- İşçilik: {round(sure_dk * DK_UCRETI, 2)} TL")
                        st.write(f"- Malzeme: {round(agirlik * adet * kg_fiyati, 2)} TL")

# --- SEKME 2: HAZIR PARÇA OLUŞTURMA ---
with tab2:
    st.subheader("Parça Tipini Seçiniz")
    sekil_tipi = st.radio("", ["Kare / Dikdörtgen", "Daire / Flanş"], horizontal=True)
    
    st.divider()
    
    if sekil_tipi == "Kare / Dikdörtgen":
        c1, c2, c3 = st.columns(3)
        with c1:
            genislik = st.number_input("Genişlik (mm)", min_value=1.0, value=100.0)
        with c2:
            yukseklik = st.number_input("Yükseklik (mm)", min_value=1.0, value=100.0)
        with c3:
            delik_sayisi = st.number_input("Delik Sayısı", min_value=0, value=0)
            delik_capi = st.number_input("Delik Çapı (mm)", min_value=0.0, value=10.0)
            
        canvas = np.zeros((400, 600, 3), dtype="uint8")
        max_dim = max(genislik, yukseklik)
        scale = 300 / max_dim
        w_px = int(genislik * scale)
        h_px = int(yukseklik * scale)
        start_x = (600 - w_px) // 2
        start_y = (400 - h_px) // 2
        
        cv2.rectangle(canvas, (start_x, start_y), (start_x + w_px, start_y + h_px), (0, 255, 0), 2)
        
        # Delik Görselleştirme (Köşe Mantığı)
        if delik_sayisi > 0 and delik_capi > 0:
            d_px_r = int((delik_capi * scale) / 2)
            padding = d_px_r + 10 
            
            coords = [
                (start_x + padding, start_y + padding),             # Sol Üst
                (start_x + w_px - padding, start_y + padding),      # Sağ Üst
                (start_x + w_px - padding, start_y + h_px - padding), # Sağ Alt
                (start_x + padding, start_y + h_px - padding)       # Sol Alt
            ]
            
            if delik_sayisi == 1:
                 cv2.circle(canvas, (300, 200), d_px_r, (0, 255, 0), 2)
            else:
                loop_count = min(delik_sayisi, 4)
                for i in range(loop_count):
                    cv2.circle(canvas, coords[i], d_px_r, (0, 255, 0), 2)

        st.image(canvas, caption=f"{genislik}x{yukseklik}mm - {delik_sayisi} Delik", use_container_width=True)
        
        # Matematik
        cevre_dis = 2 * (genislik + yukseklik)
        cevre_ic = delik_sayisi * (math.pi * delik_capi)
        toplam_kesim_mm = cevre_dis + cevre_ic
        
        alan_dis = genislik * yukseklik
        alan_ic = delik_sayisi * (math.pi * (delik_capi/2)**2)
        net_alan_mm2 = alan_dis - alan_ic
        
        piercing_sayisi = 1 + delik_sayisi

    elif sekil_tipi == "Daire / Flanş":
        c1, c2 = st.columns(2)
        with c1:
            cap = st.number_input("Dış Çap (mm)", min_value=1.0, value=100.0)
        with c2:
            delik_sayisi = st.number_input("İç Delik Sayısı", min_value=0, value=1)
            delik_capi = st.number_input("Delik Çapı (mm)", min_value=0.0, value=50.0)
            
        canvas = np.zeros((400, 400, 3), dtype="uint8")
        r_px = 150
        center = (200, 200)
        cv2.circle(canvas, center, r_px, (0, 255, 0), 2)
        
        # Delik Görselleştirme (PCD Mantığı)
        if delik_sayisi > 0 and delik_capi > 0:
            d_px_r = int(((delik_capi / cap) * r_px * 2) / 2)
            
            if delik_sayisi == 1:
                cv2.circle(canvas, center, d_px_r, (0, 255, 0), 2)
            else:
                pcd_radius = int(r_px * 0.7) 
                for i in range(delik_sayisi):
                    angle = (2 * math.pi / delik_sayisi) * i
                    x_offset = int(pcd_radius * math.cos(angle))
                    y_offset = int(pcd_radius * math.sin(angle))
                    cv2.circle(canvas, (center[0] + x_offset, center[1] + y_offset), d_px_r, (0, 255, 0), 2)

        st.image(canvas, caption=f"Q{cap}mm Flanş", use_container_width=True)
        
        # Matematik
        cevre_dis = math.pi * cap
        cevre_ic = delik_sayisi * (math.pi * delik_capi)
        toplam_kesim_mm = cevre_dis + cevre_ic
        
        alan_dis = math.pi * (cap/2)**2
        alan_ic = delik_sayisi * (math.pi * (delik_capi/2)**2)
        net_alan_mm2 = alan_dis - alan_ic
        
        piercing_sayisi = 1 + delik_sayisi
        genislik = cap 
        yukseklik = cap

    # ORTAK HESAPLAMA (TAB 2)
    p_max, p_min = max(secilen_p_en, secilen_p_boy), min(secilen_p_en, secilen_p_boy)
    g_max, g_min = max(genislik, yukseklik), min(genislik, yukseklik)
    
    if g_max > p_max or g_min > p_min:
        st.error(f"⚠️ HATA: Parça ({genislik}x{yukseklik}mm), seçilen plakaya sığmıyor!")
    else:
        kesim_yolu_m = toplam_kesim_mm / 1000
        sure_dk = (kesim_yolu_m * 1000 / guncel_hiz) * adet + (piercing_sayisi * adet * PIERCING_SURESI / 60)
        agirlik = (net_alan_mm2 * kalinlik * VERİ[metal]["ozkutle"]) / 1e6
        # Fiyat hesabı (değiştirilebilir kg_fiyati kullanılıyor)
        toplam_fiyat = (sure_dk * DK_UCRETI) + (agirlik * adet * kg_fiyati)
        
        st.subheader("📋 Hazır Parça Teklifi")
        m1, m2, m3, m4 = st.columns([1.5, 1, 1, 1.2])
        m1.metric("Parça Ölçüsü", f"{genislik} x {yukseklik} mm")
        m2.metric("Toplam Kesim", f"{round(kesim_yolu_m * adet, 2)} m")
        m3.metric("Piercing", f"{piercing_sayisi * adet} ad")
        m4.metric("TOPLAM FİYAT", f"{round(toplam_fiyat, 2)} TL")
        
        with st.expander("🔍 Teknik Detaylar (Hazır Parça)"):
            st.write(f"- Parça Ağırlığı: {round(agirlik, 2)} kg")
            st.write(f"- İşçilik: {round(sure_dk * DK_UCRETI, 2)} TL")
            st.write(f"- Malzeme: {round(agirlik * adet * kg_fiyati, 2)} TL")
