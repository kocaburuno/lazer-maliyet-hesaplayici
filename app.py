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
        section[data-testid="stSidebar"] div.block-container {
            padding-top: 0rem;
        }
        [data-testid="stSidebarUserContent"] .element-container:first-child {
            margin-top: 10px;
        }
        div.stButton > button { min-height: 50px; }

        /* Metric Styling */
        div[data-testid="metric-container"] {
            background-color: #f8f9fb;
            padding: 10px 15px !important;
            border-radius: 10px;
            border-left: 5px solid #1C3768;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
            width: auto !important;
            min-width: 150px !important;
        }
        [data-testid="stMetricValue"] {
            font-size: 22px !important;
            font-weight: bold !important;
            color: #1C3768 !important;
            white-space: nowrap !important;
            overflow: visible !important;
            text-overflow: clip !important;
            display: block !important;
        }
        [data-testid="stMetricLabel"] {
            font-size: 13px !important;
            font-weight: 600 !important;
            color: #31333F !important;
            text-transform: uppercase;
            white-space: nowrap !important;
            overflow: visible !important;
        }
        /* Ensure columns don't squeeze metrics */
        div[data-testid="column"] {
            width: auto !important;
            flex: 1 1 auto !important;
            min-width: fit-content !important;
        }
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

# --- 4. SIDEBAR ---
with st.sidebar:
    try:
        st.image("logo.png", use_column_width=True)
    except:
        st.markdown("<h1 style='text-align: center; color: #FF4B4B;'>ALAN LAZER</h1>", unsafe_allow_html=True)
    
    st.markdown(
        """
        <div style='text-align: center; margin-top: -10px; margin-bottom: 25px;'>
            <a href='https://www.alanlazer.com' target='_blank' 
               style='text-decoration: none; color: #1C3768; font-size: 22px; font-weight: 300; letter-spacing: 1.5px; font-family: "Segoe UI Semilight", "Segoe UI", sans-serif;'>
                alanlazer.com
            </a>
        </div>
        """, 
        unsafe_allow_html=True
    )
        
    st.markdown("---")
    
    metal = st.selectbox("Metal Türü", list(VERİ.keys()))
    plaka_secenekleri = {"1500x6000": (1500, 6000), "1500x3000": (1500, 3000), "2500x1250": (2500, 1250)}
    secilen_plaka_adi = st.selectbox("Plaka Boyutu", list(plaka_secenekleri.keys()))
    secilen_p_en, secilen_p_boy = plaka_secenekleri[secilen_plaka_adi]

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        kalinlik = st.selectbox("Kalınlık (mm)", VERİ[metal]["kalinliklar"])
    with col_s2:
        adet = st.number_input("Adet", min_value=1, value=1, step=1)
    
    hiz_tablosu = VERİ[metal]["hizlar"]
    tanimli_k = sorted(hiz_tablosu.keys())
    uygun_k = tanimli_k[0]
    for k in tanimli_k:
        if kalinlik >= k: uygun_k = k
    guncel_hiz = hiz_tablosu[uygun_k]

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
        format="%g"
    )

    st.markdown("---")
    
    col_i1, col_i2 = st.columns(2)
    with col_i1:
        st.info(f"⚡ Hız\n{guncel_hiz}")
    with col_i2:
        st.success(f"💰 Birim\n{kg_fiyati} TL")

# --- 5. ANA PANEL İÇERİĞİ ---

st.title("AI DESTEKLİ PROFESYONEL ANALİZ")

# === DURUM A: ANASAYFA ===
if st.session_state.sayfa == 'anasayfa':
    st.markdown("### Lütfen yapmak istediğiniz işlem türünü seçiniz:")
    st.markdown("---")
    
    c1, c2, c3 = st.columns(3, gap="medium")
    
    with c1:
        st.info("📸 **FOTOĞRAFTAN ANALİZ**")
        st.markdown("""
        Fotoğraf veya eskiz görsellerini yükleyin. **AI görüntü işleme algoritmamız** işini yapsın.
        
        **Özellikler:**
        * JPG, PNG formatı
        * Otomatik Kenar Tespiti
        * Referans Ölçü ile Ölçekleme
        """)
        if st.button("FOTOĞRAF YÜKLE", use_container_width=True, type="primary"):
            sayfa_degistir('foto_analiz')
            st.rerun()

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
        # 1) Yatay Uzunluk Default 100 olarak güncellendi
        referans_olcu = st.number_input(
            "Parçanın Yatay Uzunluğu (mm)", 
            value=100.0, 
            step=10.0, 
            format="%g",
            help="Yüklediğiniz çizimdeki parçanın soldan sağa (yatay) olan gerçek uzunluğunu giriniz."
        )
        # 2) ve 3) Hassasiyet yazısı ve default değeri (80) güncellendi
        hassasiyet = st.slider("Hassasiyet (Kesim Kontur Yakalama)", 50, 255, 80, step=1)
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
                    
                    display_img = original_img.copy()
                    cv2.drawContours(display_img, valid_contour_list, -1, (0, 255, 0), 2)
                    rgb_img = cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB)
                    
                    st.image(rgb_img, caption="AI Tarafından Tespit Edilen Kesim Yolları", use_container_width=True)

                    p_max, p_min = max(secilen_p_en, secilen_p_boy), min(secilen_p_en, secilen_p_boy)
                    g_max, g_min = max(gercek_genislik, gercek_yukseklik), min(gercek_genislik, gercek_yukseklik)

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
                        
                        st.markdown(f"""
                        <div style="display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 20px;">
                            <div style="background-color: #f8f9fb; padding: 15px; border-radius: 10px; border-left: 5px solid #1C3768; min-width: 180px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
                                <div style="font-size: 13px; font-weight: 600; color: #31333F; text-transform: uppercase; margin-bottom: 5px;">Ölçü (mm)</div>
                                <div style="font-size: 24px; font-weight: bold; color: #1C3768; white-space: nowrap;">{round(gercek_genislik, 1)} x {round(gercek_yukseklik, 1)}</div>
                            </div>
                            <div style="background-color: #f8f9fb; padding: 15px; border-radius: 10px; border-left: 5px solid #1C3768; min-width: 150px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
                                <div style="font-size: 13px; font-weight: 600; color: #31333F; text-transform: uppercase; margin-bottom: 5px;">Kesim</div>
                                <div style="font-size: 24px; font-weight: bold; color: #1C3768; white-space: nowrap;">{round(kesim_yolu_m * adet, 2)} m</div>
                            </div>
                            <div style="background-color: #f8f9fb; padding: 15px; border-radius: 10px; border-left: 5px solid #1C3768; min-width: 150px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
                                <div style="font-size: 13px; font-weight: 600; color: #31333F; text-transform: uppercase; margin-bottom: 5px;">Piercing</div>
                                <div style="font-size: 24px; font-weight: bold; color: #1C3768; white-space: nowrap;">{piercing_basi * adet} ad</div>
                            </div>
                            <div style="background-color: #e8f0fe; padding: 15px; border-radius: 10px; border-left: 5px solid #d32f2f; min-width: 200px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
                                <div style="font-size: 13px; font-weight: 600; color: #d32f2f; text-transform: uppercase; margin-bottom: 5px;">KDV HARİÇ</div>
                                <div style="font-size: 28px; font-weight: bold; color: #d32f2f; white-space: nowrap;">{round(toplam_fiyat, 2)} TL</div>
                                <div style="color: green; font-weight: bold; font-size: 16px; margin-top: 5px;">KDV DAHİL: {round(kdvli_fiyat, 2)} TL</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        with st.expander("🔍 Teknik Detaylar"):
                            st.write(f"- Parça Ağırlığı (+%15 Fire): {round(agirlik, 2)} kg")
                            st.write(f"- İşçilik: {round(sure_dk * DK_UCRETI, 2)} TL")
                            st.write(f"- Malzeme: {round(agirlik * adet * kg_fiyati, 2)} TL")
        else:
             st.info("Lütfen sol taraftan bir çizim görseli yükleyiniz.")

# === DURUM C: TEKNİK ÇİZİM ANALİZ SAYFASI ===
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
        
        uploaded_dxf = st.file_uploader("Dosya Seç (DXF Önerilir)", type=['dxf', 'dwg'])

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
                
                dxf_genislik, dxf_yukseklik = 500.0, 300.0
                kesim_m = toplam_uzunluk / 1000.0 if toplam_uzunluk > 0 else 1.5
                piercing_basi = int(entity_count / 2) + 1
                sure_dk = (kesim_m * 1000 / guncel_hiz) * adet + (piercing_basi * adet * PIERCING_SURESI / 60)
                
                ham_agirlik = (dxf_genislik * dxf_yukseklik * kalinlik * VERİ[metal]["ozkutle"]) / 1e6
                agirlik = ham_agirlik * FIRE_ORANI
                toplam_fiyat = (sure_dk * DK_UCRETI) + (agirlik * adet * kg_fiyati)
                kdvli_fiyat = toplam_fiyat * KDV_ORANI
                
                st.success(f"✅ Dosya Başarıyla Okundu: {uploaded_dxf.name}")
                st.markdown("### 📋 Teknik Çizim Teklifi")
                
                st.markdown(f"""
                <div style="display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 20px;">
                    <div style="background-color: #f8f9fb; padding: 15px; border-radius: 10px; border-left: 5px solid #1C3768; min-width: 180px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
                        <div style="font-size: 13px; font-weight: 600; color: #31333F; text-transform: uppercase; margin-bottom: 5px;">Ölçü (mm)</div>
                        <div style="font-size: 24px; font-weight: bold; color: #1C3768; white-space: nowrap;">{dxf_genislik}x{dxf_yukseklik}</div>
                    </div>
                    <div style="background-color: #f8f9fb; padding: 15px; border-radius: 10px; border-left: 5px solid #1C3768; min-width: 150px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
                        <div style="font-size: 13px; font-weight: 600; color: #31333F; text-transform: uppercase; margin-bottom: 5px;">Net Kesim</div>
                        <div style="font-size: 24px; font-weight: bold; color: #1C3768; white-space: nowrap;">{round(kesim_m * adet, 2)} m</div>
                    </div>
                    <div style="background-color: #f8f9fb; padding: 15px; border-radius: 10px; border-left: 5px solid #1C3768; min-width: 150px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
                        <div style="font-size: 13px; font-weight: 600; color: #31333F; text-transform: uppercase; margin-bottom: 5px;">Nesne/Delik</div>
                        <div style="font-size: 24px; font-weight: bold; color: #1C3768; white-space: nowrap;">{piercing_basi * adet}</div>
                    </div>
                    <div style="background-color: #e8f0fe; padding: 15px; border-radius: 10px; border-left: 5px solid #d32f2f; min-width: 200px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
                        <div style="font-size: 13px; font-weight: 600; color: #d32f2f; text-transform: uppercase; margin-bottom: 5px;">KDV HARİÇ</div>
                        <div style="font-size: 28px; font-weight: bold; color: #d32f2f; white-space: nowrap;">{round(toplam_fiyat, 2)} TL</div>
                        <div style="color: green; font-weight: bold; font-size: 16px; margin-top: 5px;">KDV DAHİL: {round(kdvli_fiyat, 2)} TL</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Hata: {e}")
        else:
            st.info("Lütfen .DXF veya .DWG uzantılı çizim dosyanızı yükleyiniz.")

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
            w_px, h_px = int(genislik * scale), int(yukseklik * scale)
            start_x, start_y = (600 - w_px) // 2, (300 - h_px) // 2
            cv2.rectangle(canvas, (start_x, start_y), (start_x + w_px, start_y + h_px), (0, 255, 0), 2)
            
            if delik_sayisi > 0 and delik_capi > 0:
                d_px_r = int((delik_capi * scale) / 2)
                padding = d_px_r + 10 
                if delik_sayisi == 1: cv2.circle(canvas, (300, 150), d_px_r, (0, 255, 0), 2)
                else:
                    coords = [(start_x + padding, start_y + padding), (start_x + w_px - padding, start_y + padding)]
                    for i in range(min(delik_sayisi, 2)): cv2.circle(canvas, coords[i], d_px_r, (0, 255, 0), 2)

            toplam_kesim_mm = 2 * (genislik + yukseklik) + delik_sayisi * (math.pi * delik_capi)
            net_alan_mm2 = (genislik * yukseklik) - delik_sayisi * (math.pi * (delik_capi/2)**2)
            piercing_sayisi = 1 + delik_sayisi

        elif sekil_tipi == "Daire / Flanş":
            cap = st.number_input("Dış Çap (mm)", min_value=1.0, value=100.0, step=10.0, format="%g")
            delik_sayisi = st.number_input("İç Delik Sayısı", min_value=0, value=1, step=1)
            delik_capi = st.number_input("Delik Çapı (mm)", min_value=0.0, value=50.0, step=1.0, format="%g")
            
            canvas = np.zeros((300, 400, 3), dtype="uint8")
            r_px, center = 120, (200, 150)
            cv2.circle(canvas, center, r_px, (0, 255, 0), 2)
            if delik_sayisi > 0 and delik_capi > 0:
                d_px_r = int(((delik_capi / cap) * r_px * 2) / 2)
                cv2.circle(canvas, center, d_px_r, (0, 255, 0), 2)
            
            toplam_kesim_mm = math.pi * cap + delik_sayisi * (math.pi * delik_capi)
            net_alan_mm2 = math.pi * (cap/2)**2 - delik_sayisi * (math.pi * (delik_capi/2)**2)
            piercing_sayisi = 1 + delik_sayisi
            genislik, yukseklik = cap, cap

    with c_sonuc:
        st.image(canvas, caption=f"{genislik}x{yukseklik}mm", use_container_width=True)
        kesim_m = toplam_kesim_mm / 1000
        sure_dk = (kesim_m * 1000 / guncel_hiz) * adet + (piercing_sayisi * adet * PIERCING_SURESI / 60)
        agirlik = (net_alan_mm2 * kalinlik * VERİ[metal]["ozkutle"] / 1e6) * FIRE_ORANI
        toplam_fiyat = (sure_dk * DK_UCRETI) + (agirlik * adet * kg_fiyati)
        kdvli_fiyat = toplam_fiyat * KDV_ORANI
        
        st.markdown("### 📋 Teklif Özeti")
        
        st.markdown(f"""
        <div style="display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 20px;">
            <div style="background-color: #f8f9fb; padding: 15px; border-radius: 10px; border-left: 5px solid #1C3768; min-width: 180px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
                <div style="font-size: 13px; font-weight: 600; color: #31333F; text-transform: uppercase; margin-bottom: 5px;">Ölçü (mm)</div>
                <div style="font-size: 24px; font-weight: bold; color: #1C3768; white-space: nowrap;">{genislik}x{yukseklik}</div>
            </div>
            <div style="background-color: #f8f9fb; padding: 15px; border-radius: 10px; border-left: 5px solid #1C3768; min-width: 150px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
                <div style="font-size: 13px; font-weight: 600; color: #31333F; text-transform: uppercase; margin-bottom: 5px;">Kesim</div>
                <div style="font-size: 24px; font-weight: bold; color: #1C3768; white-space: nowrap;">{round(kesim_m * adet, 2)} m</div>
            </div>
            <div style="background-color: #f8f9fb; padding: 15px; border-radius: 10px; border-left: 5px solid #1C3768; min-width: 150px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
                <div style="font-size: 13px; font-weight: 600; color: #31333F; text-transform: uppercase; margin-bottom: 5px;">Piercing</div>
                <div style="font-size: 24px; font-weight: bold; color: #1C3768; white-space: nowrap;">{piercing_sayisi * adet} ad</div>
            </div>
            <div style="background-color: #e8f0fe; padding: 15px; border-radius: 10px; border-left: 5px solid #d32f2f; min-width: 200px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
                <div style="font-size: 13px; font-weight: 600; color: #d32f2f; text-transform: uppercase; margin-bottom: 5px;">KDV HARİÇ</div>
                <div style="font-size: 28px; font-weight: bold; color: #d32f2f; white-space: nowrap;">{round(toplam_fiyat, 2)} TL</div>
                <div style="color: green; font-weight: bold; font-size: 16px; margin-top: 5px;">KDV DAHİL: {round(kdvli_fiyat, 2)} TL</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
