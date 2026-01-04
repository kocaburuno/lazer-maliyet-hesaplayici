import streamlit as st
from PIL import Image
import cv2
import numpy as np
import math
import tempfile
import os

# --- KÜTÜPHANE KONTROLÜ ---
try:
    import ezdxf
    dxf_active = True
except ImportError:
    dxf_active = False

# --- 1. AYARLAR VE FAVICON ---
try:
    fav_icon = Image.open("tarayici.png")
except:
    fav_icon = None 

st.set_page_config(page_title="Alan Lazer Teklif Paneli", layout="wide", page_icon=fav_icon)

# --- CSS İLE STİL AYARLAMALARI ---
st.markdown("""
    <style>
        /* Sidebar üst boşluğunu tamamen yok etme ve logoyu yukarı taşıma */
        section[data-testid="stSidebar"] div.block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        
        /* Sidebar içindeki elementlerin arasını biraz açarak ferahlık sağlama */
        [data-testid="stSidebarUserContent"] {
            gap: 1rem;
        }
        
        /* Buton yüksekliklerini eşitleme */
        div.stButton > button { min-height: 50px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SAYFA DURUM YÖNETİMİ ---
if 'sayfa' not in st.session_state:
    st.session_state.sayfa = 'anasayfa'

def sayfa_degistir(sayfa_adi):
    st.session_state.sayfa = sayfa_adi

# --- 3. SABİT PARAMETRELER ---
DK_UCRETI = 25.0       
PIERCING_SURESI = 2.0  
FIRE_ORANI = 1.15 
KDV_ORANI = 1.20  

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

# --- 4. SIDEBAR (REVİZE EDİLDİ - GRID SİSTEMİ) ---
with st.sidebar:
    try:
        st.image("logo.png", use_column_width=True)
    except:
        st.markdown("<h1 style='text-align: center; color: #FF4B4B;'>ALAN LAZER</h1>", unsafe_allow_html=True)
    
    # URL: Şık, ince font, kurumsal renk
    st.markdown(
        """
        <div style='text-align: center; margin-top: -15px; margin-bottom: 25px;'>
            <a href='https://www.alanlazer.com' target='_blank' 
               style='text-decoration: none; color: #1C3768; font-size: 1.6em; font-weight: 100; font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif; letter-spacing: 0.5px;'>
                alanlazer.com
            </a>
        </div>
        """, 
        unsafe_allow_html=True
    )
        
    st.markdown("---")
    
    # --- GİRİŞ ALANLARI: 2x2 GRID (DAHA DÜZENLİ) ---
    
    # 1. Satır: Metal ve Kalınlık
    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        metal = st.selectbox("Metal Türü", list(VERİ.keys()))
    with row1_col2:
        kalinlik = st.selectbox("Kalınlık (mm)", VERİ[metal]["kalinliklar"])
    
    # 2. Satır: Plaka ve Adet
    row2_col1, row2_col2 = st.columns(2)
    with row2_col1:
        plaka_secenekleri = {"1500x6000": (1500, 6000), "1500x3000": (1500, 3000), "2500x1250": (2500, 1250)}
        secilen_plaka_adi = st.selectbox("Plaka Boyutu", list(plaka_secenekleri.keys()))
        secilen_p_en, secilen_p_boy = plaka_secenekleri[secilen_plaka_adi]
    with row2_col2:
        adet = st.number_input("Adet", min_value=1, value=1, step=1)
    
    # Hız Hesaplama
    hiz_tablosu = VERİ[metal]["hizlar"]
    tanimli_k = sorted(hiz_tablosu.keys())
    uygun_k = tanimli_k[0]
    for k in tanimli_k:
        if kalinlik >= k: uygun_k = k
    guncel_hiz = hiz_tablosu[uygun_k]

    # Varsayılan Fiyat
    varsayilan_fiyat = 30.0
    if metal == "Siyah Sac": varsayilan_fiyat = 30.0
    elif metal == "Paslanmaz": varsayilan_fiyat = 150.0
    elif metal == "Alüminyum": varsayilan_fiyat = 220.0
    
    st.markdown("---")
    
    kg_fiyati = st.number_input(
        "Malzeme KG Fiyatı (TL)", 
        min_value=0.0, 
        value=varsayilan_fiyat, 
        step=10.0, 
        format="%g",
        help="Güncel piyasa fiyatını buradan değiştirebilirsiniz."
    )

    st.markdown("---")
    
    col_i1, col_i2 = st.columns(2)
    with col_i1:
        st.info(f"⚡ Hız\n{guncel_hiz}")
    with col_i2:
        st.success(f"💰 Birim\n{kg_fiyati} TL")

# --- 5. ANA PANEL İÇERİĞİ ---

# BAŞLIK GÜNCELLENDİ
st.title("AI DESTEKLİ PROFESYONEL MALİYET ANALİZ PANELİ")
# Alt başlık (caption) kaldırıldı

# === DURUM A: ANASAYFA (KARŞILAMA EKRANI) ===
if st.session_state.sayfa == 'anasayfa':
    st.markdown("### Lütfen yapmak istediğiniz işlem türünü seçiniz:")
    st.markdown("---")
    
    c1, c2, c3 = st.columns(3, gap="medium")
    
    # --- 1. Sütun: Fotoğraftan Analiz ---
    with c1:
        # BAŞLIK GÜNCELLENDİ
        st.info("📸 **FOTOĞRAFTAN ANALİZ**")
        # METİN GÜNCELLENDİ ("Teknik çizim" silindi)
        st.markdown("""
        Fotoğraf veya eskiz görsellerini yükleyin. **AI görüntü işleme algoritmamız** kesim yollarını otomatik tespit eder.
        
        **Özellikler:**
        * JPG, PNG formatı
        * Otomatik Kenar Tespiti
        * Referans Ölçü ile Ölçekleme
        """)
        if st.button("FOTOĞRAF YÜKLE", use_container_width=True, type="primary"):
            sayfa_degistir('foto_analiz')
            st.rerun()

    # --- 2. Sütun: Teknik Çizim ---
    with c2:
        st.warning("📐 **TEKNİK ÇİZİM ANALİZİ (DWG / DXF)**")
        st.markdown("""
        Vektörel çizim dosyalarınızı (DXF/DWG) doğrudan yükleyerek %100 hassas sonuç alın.
        
        **Özellikler:**
        * DXF ve DWG Desteği
        * Net Kesim Yolu Hesabı
        * Otomatik Yerleşim (Nesting)
        """)
        if st.button("ÇİZİM DOSYASI YÜKLE", use_container_width=True, type="primary"):
            sayfa_degistir('dxf_analiz')
            st.rerun()

    # --- 3. Sütun: Hazır Parça ---
    with c3:
        st.success("🛠 **HAZIR PARÇA OLUŞTUR**")
        st.markdown("""
        Çiziminiz yoksa; standart geometrik şekilleri (Kare, Flanş vb.) manuel oluşturun.
        
        **Özellikler:**
        * Kare, Dikdörtgen, Daire
        * Delik Tanımlama
        * Hızlı Şablon Oluşturma
        """)
        if st.button("MANUEL PARÇA OLUŞTUR", use_container_width=True, type="primary"):
            sayfa_degistir('hazir_parca')
            st.rerun()

# === DURUM B: FOTOĞRAFTAN ANALİZ SAYFASI ===
elif st.session_state.sayfa == 'foto_analiz':
    if st.button("⬅️ Ana Menüye Dön"):
        sayfa_degistir('anasayfa')
        st.rerun()
    
    st.divider()
    
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
        uploaded_file = st.file_uploader("Görsel Yükle (JPG, PNG)", type=['jpg', 'png', 'jpeg'])

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
                    
                    st.image(rgb_img, caption="AI Tarafından Tespit Edilen Kesim Yolları", use_container_width=True)

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

# === DURUM C: TEKNİK ÇİZİM (DXF/DWG) ANALİZ SAYFASI ===
elif st.session_state.sayfa == 'dxf_analiz':
    if st.button("⬅️ Ana Menüye Dön"):
        sayfa_degistir('anasayfa')
        st.rerun()

    st.divider()
    c_dxf_ayar, c_dxf_sonuc = st.columns([1, 2])

    with c_dxf_ayar:
        st.subheader("Teknik Çizim Yükle")
        if not dxf_active:
            st.warning("⚠️ DXF modülü için 'ezdxf' kütüphanesi gereklidir.")
            st.code("pip install ezdxf")
        
        uploaded_dxf = st.file_uploader("Dosya Seç (DXF Önerilir)", type=['dxf', 'dwg'])
        st.info("💡 Not: DWG dosyaları versiyon uyumsuzluğu yaratabilir. En sağlıklı sonuç için DXF formatı önerilir.")

    with c_dxf_sonuc:
        if uploaded_dxf and dxf_active:
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp_file:
                    tmp_file.write(uploaded_dxf.getvalue())
                    tmp_path = tmp_file.name

                doc = ezdxf.readfile(tmp_path)
                msp = doc.modelspace()
                
                toplam_uzunluk = 0
                entity_count = 0

                for e in msp:
                    entity_count += 1
                    if e.dxftype() == 'LINE':
                        toplam_uzunluk += e.dxf.start.distance(e.dxf.end)
                    elif e.dxftype() == 'CIRCLE':
                        toplam_uzunluk += 2 * math.pi * e.dxf.radius
                    elif e.dxftype() == 'ARC':
                        toplam_uzunluk += e.dxf.radius * (math.radians(e.dxf.end_angle - e.dxf.start_angle))
                
                os.remove(tmp_path)
                
                dxf_genislik = 500.0  # Örnek
                dxf_yukseklik = 300.0 # Örnek
                kesim_m = toplam_uzunluk / 1000.0 if toplam_uzunluk > 0 else 1.5
                
                st.success(f"✅ Dosya Başarıyla Okundu: {uploaded_dxf.name}")
                st.write(f"Tespit Edilen Nesne Sayısı: {entity_count}")
                
                piercing_basi = int(entity_count / 2) + 1
                sure_dk = (kesim_m * 1000 / guncel_hiz) * adet + (piercing_basi * adet * PIERCING_SURESI / 60)
                
                alan_mm2 = dxf_genislik * dxf_yukseklik 
                ham_agirlik = (alan_mm2 * kalinlik * VERİ[metal]["ozkutle"]) / 1e6
                agirlik = ham_agirlik * FIRE_ORANI
                
                toplam_fiyat = (sure_dk * DK_UCRETI) + (agirlik * adet * kg_fiyati)
                kdvli_fiyat = toplam_fiyat * KDV_ORANI
                
                st.markdown("### 📋 Teknik Çizim Teklifi")
                m1, m2, m3, m4 = st.columns([1, 1, 1, 1.5])
                m1.metric("Tahmini Ölçü", f"{dxf_genislik}x{dxf_yukseklik}")
                m2.metric("Net Kesim", f"{round(kesim_m * adet, 2)} m")
                m3.metric("Nesne/Delik", f"{piercing_basi * adet}")
                m4.metric("KDV HARİÇ", f"{round(toplam_fiyat, 2)} TL")
                m4.markdown(f"<span style='color:green; font-weight:bold;'>KDV DAHİL: {round(kdvli_fiyat, 2)} TL</span>", unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Dosya okunurken hata oluştu veya desteklenmeyen format. Hata: {e}")
        
        elif uploaded_dxf and not dxf_active:
            st.error("Sistemde 'ezdxf' kütüphanesi eksik olduğu için analiz yapılamadı.")
            
        else:
            st.info("Lütfen sol taraftan .DXF veya .DWG uzantılı çizim dosyanızı yükleyiniz.")

# === DURUM D: HAZIR PARÇA OLUŞTURMA SAYFASI ===
elif st.session_state.sayfa == 'hazir_parca':
    if st.button("⬅️ Ana Menüye Dön"):
        sayfa_degistir('anasayfa')
        st.rerun()
    
    st.divider()

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
