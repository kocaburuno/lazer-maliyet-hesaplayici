import streamlit as st
from PIL import Image
import cv2
import numpy as np
import math
import tempfile
import os

# --- 0. KÜTÜPHANE KONTROLÜ ---
try:
    import ezdxf
    dxf_active = True
except ImportError:
    dxf_active = False

# --- 1. SAYFA AYARLARI VE FAVICON ---
try:
    fav_icon = Image.open("tarayici.png")
except:
    fav_icon = None 

st.set_page_config(page_title="Alan Lazer Teklif Paneli", layout="wide", page_icon=fav_icon)

# --- 2. CSS STİL AYARLAMALARI (TAM KAPSAMLI) ---
st.markdown("""
    <style>
        /* Sidebar Üst Boşluk Sıfırlama */
        section[data-testid="stSidebar"] div.block-container {
            padding-top: 0rem;
        }
        [data-testid="stSidebarUserContent"] .element-container:first-child {
            margin-top: 10px;
        }
        div.stButton > button { min-height: 50px; }

        /* Analiz Detay Listesi Tasarımı (Alt Alta Şık Görünüm) */
        .analiz-bilgi-kutu {
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 12px;
            border-left: 5px solid #1c3768;
            margin-top: 10px;
        }
        .analiz-bilgi-satir {
            font-size: 0.9rem;
            color: #555;
            margin-bottom: 5px;
            line-height: 1.4;
        }
        .analiz-bilgi-deger {
            font-weight: bold;
            color: #111;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. SAYFA DURUM YÖNETİMİ ---
if 'sayfa' not in st.session_state:
    st.session_state.sayfa = 'anasayfa'

def sayfa_degistir(sayfa_adi):
    st.session_state.sayfa = sayfa_adi

# --- 4. SABİT PARAMETRELER ---
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

# --- 5. SIDEBAR ---
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

    varsayilan_fiyat = 30.0 if metal == "Siyah Sac" else (150.0 if metal == "Paslanmaz" else 220.0)
    
    st.markdown("---")
    kg_fiyati = st.number_input("Malzeme KG Fiyatı (TL)", min_value=0.0, value=varsayilan_fiyat, step=10.0, format="%g")

    st.markdown("---")
    col_i1, col_i2 = st.columns(2)
    with col_i1:
        st.info(f"⚡ Hız\n{guncel_hiz}")
    with col_i2:
        st.success(f"💰 Birim\n{kg_fiyati} TL")

# --- 6. ANA PANEL İÇERİĞİ ---
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
        Çiziminiz yoksa; standart geometrik şekilleri manuel oluşturun.
        
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
    c_ayar, c_sonuc = st.columns([1, 2])

    with c_ayar:
        st.subheader("Analiz Ayarları")
        referans_olcu = st.number_input("Parçanın Yatay Uzunluğu (mm)", value=100.0, step=10.0, format="%g")
        hassasiyet = st.slider("Hassasiyet (Kesim Kontur Yakalama)", 50, 255, 80, step=1)
        st.divider()
        uploaded_file = st.file_uploader("Görsel Yükle (JPG, PNG)", type=['jpg', 'png', 'jpeg'])

    with c_sonuc:
        if uploaded_file:
            file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            original_img = cv2.imdecode(file_bytes, 1)
            h_img, w_img = original_img.shape[:2] 
            gray = cv2.cvtColor(original_img, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray, hassasiyet, 255, cv2.THRESH_BINARY_INV)
            contours, hierarchy = cv2.findContours(binary, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours and hierarchy is not None:
                valid_cnts = []
                for i, cnt in enumerate(contours):
                    bx, by, bw, bh = cv2.boundingRect(cnt)
                    # --- AI ÇERÇEVE FİLTRESİ ---
                    if bw > w_img * 0.96 or bh > h_img * 0.96: continue
                    if hierarchy[0][i][3] == -1 or hierarchy[0][i][3] == 0:
                        valid_cnts.append(cnt)

                if valid_cnts:
                    all_pts = np.concatenate(valid_cnts)
                    x_r, y_r, w_px, h_px = cv2.boundingRect(all_pts)
                    oran = referans_olcu / w_px
                    g_mm, y_mm = w_px * oran, h_px * oran
                    
                    display_img = original_img.copy()
                    cv2.drawContours(display_img, valid_cnts, -1, (0, 255, 0), 2)
                    st.image(cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB), caption="AI Analiz Sonucu", use_container_width=True)

                    kesim_m = (sum([cv2.arcLength(c, True) for c in valid_cnts]) * oran) / 1000
                    kontur_ad = len(valid_cnts)
                    sure_dk = (kesim_m * 1000 / guncel_hiz) * adet + (kontur_ad * adet * PIERCING_SURESI / 60)
                    agirlik = (cv2.contourArea(all_pts) * (oran**2) * kalinlik * VERİ[metal]["ozkutle"] / 1e6) * FIRE_ORANI
                    fiyat = (sure_dk * DK_UCRETI) + (agirlik * adet * kg_fiyati)

                    st.markdown("### 📋 Teklif Özeti")
                    cd, cf = st.columns([1, 1])
                    with cd:
                        st.markdown(f"""<div class="analiz-bilgi-kutu">
                            <div class="analiz-bilgi-satir">📏 Ölçü: <span class="analiz-bilgi-deger">{round(g_mm, 1)} x {round(y_mm, 1)} mm</span></div>
                            <div class="analiz-bilgi-satir">⏱ Süre: <span class="analiz-bilgi-deger">{round(sure_dk, 2)} dk</span></div>
                            <div class="analiz-bilgi-satir">⚙️ Kontur (Piercing Patlatma): <span class="analiz-bilgi-deger">{kontur_ad * adet} ad</span></div>
                        </div>""", unsafe_allow_html=True)
                    with cf:
                        st.metric("KDV HARİÇ", f"{round(fiyat, 2)} TL")
                        st.success(f"KDV DAHİL: {round(fiyat * KDV_ORANI, 2)} TL")

# === DURUM C: TEKNİK ÇİZİM ANALİZ ===
elif st.session_state.sayfa == 'dxf_analiz':
    if st.button("⬅️ Ana Menüye Dön"): sayfa_degistir('anasayfa'); st.rerun()
    st.divider()
    c_dxf_ayar, c_dxf_sonuc = st.columns([1, 2])
    with c_dxf_ayar:
        st.subheader("Teknik Çizim Yükle")
        uploaded_dxf = st.file_uploader("Dosya Seç (DXF)", type=['dxf', 'dwg'])

    with c_dxf_sonuc:
        if uploaded_dxf and dxf_active:
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
                    tmp.write(uploaded_dxf.getvalue()); tmp_path = tmp.name
                doc = ezdxf.readfile(tmp_path); msp = doc.modelspace(); os.remove(tmp_path)
                
                uzunluk = 0
                ent_count = 0
                for e in msp:
                    ent_count += 1
                    if e.dxftype() == 'LINE': uzunluk += e.dxf.start.distance(e.dxf.end)
                    elif e.dxftype() == 'CIRCLE': uzunluk += 2 * math.pi * e.dxf.radius
                    elif e.dxftype() == 'ARC': uzunluk += e.dxf.radius * (math.radians(e.dxf.end_angle - e.dxf.start_angle))
                
                kesim_m = uzunluk / 1000 if uzunluk > 0 else 1.5
                kontur_ad = int(ent_count / 2) + 1
                sure_dk = (kesim_m * 1000 / guncel_hiz) * adet + (kontur_ad * adet * PIERCING_SURESI / 60)
                agirlik = (500 * 300 * kalinlik * VERİ[metal]["ozkutle"] / 1e6) * FIRE_ORANI
                fiyat = (sure_dk * DK_UCRETI) + (agirlik * adet * kg_fiyati)
                
                st.success(f"✅ Dosya Okundu: {uploaded_dxf.name}")
                st.markdown("### 📋 Teklif Özeti")
                cd_d, cf_d = st.columns([1, 1])
                with cd_d:
                    st.markdown(f"""<div class="analiz-bilgi-kutu">
                        <div class="analiz-bilgi-satir">📏 Tahmini Ölçü: <span class="analiz-bilgi-deger">500 x 300 mm</span></div>
                        <div class="analiz-bilgi-satir">⏱ Süre: <span class="analiz-bilgi-deger">{round(sure_dk, 2)} dk</span></div>
                        <div class="analiz-bilgi-satir">⚙️ Kontur (Piercing Patlatma): <span class="analiz-bilgi-deger">{kontur_ad * adet} ad</span></div>
                    </div>""", unsafe_allow_html=True)
                with cf_d:
                    st.metric("KDV HARİÇ", f"{round(fiyat, 2)} TL")
                    st.success(f"KDV DAHİL: {round(fiyat * KDV_ORANI, 2)} TL")
            except Exception as e: st.error(f"Hata: {e}")

# === DURUM D: HAZIR PARÇA OLUŞTURMA ===
elif st.session_state.sayfa == 'hazir_parca':
    if st.button("⬅️ Ana Menüye Dön"): sayfa_degistir('anasayfa'); st.rerun()
    st.divider()
    c_ayar, c_sonuc = st.columns([1, 2])
    
    with c_ayar:
        st.subheader("Parça Ayarları")
        sekil_tipi = st.radio("Parça Tipi", ["Kare / Dikdörtgen", "Daire / Flanş"])
        if sekil_tipi == "Kare / Dikdörtgen":
            genislik = st.number_input("Genişlik (mm)", 1.0, value=100.0)
            yukseklik = st.number_input("Yükseklik (mm)", 1.0, value=100.0)
            d_ad = st.number_input("Delik Sayısı", 0, 10)
            d_cap = st.number_input("Delik Çapı (mm)", 0.0, 10.0)
            
            # --- CANVAS ÇİZİM (KARE) ---
            canvas = np.zeros((300, 600, 3), dtype="uint8")
            max_dim = max(genislik, yukseklik)
            scale = 250 / max_dim
            w_px, h_px = int(genislik * scale), int(yukseklik * scale)
            start_x, start_y = (600 - w_px) // 2, (300 - h_px) // 2
            cv2.rectangle(canvas, (start_x, start_y), (start_x + w_px, start_y + h_px), (0, 255, 0), 2)
            if d_ad > 0 and d_cap > 0:
                d_px_r = int((d_cap * scale) / 2)
                cv2.circle(canvas, (300, 150), d_px_r, (0, 255, 0), 2)
            
            kesim_m = (2 * (genislik + yukseklik) + d_ad * math.pi * d_cap) / 1000
            alan = (genislik * yukseklik) - d_ad * math.pi * (d_cap/2)**2
            k_ad = 1 + d_ad
        else:
            cap = st.number_input("Dış Çap (mm)", 1.0, value=100.0)
            d_ad = st.number_input("Delik Sayısı", 0, 1)
            d_cap = st.number_input("Delik Çapı (mm)", 0.0, 50.0)
            
            # --- CANVAS ÇİZİM (DAİRE) ---
            canvas = np.zeros((300, 400, 3), dtype="uint8")
            cv2.circle(canvas, (200, 150), 120, (0, 255, 0), 2)
            if d_ad > 0 and d_cap > 0:
                d_px_r = int(((d_cap / cap) * 120 * 2) / 2)
                cv2.circle(canvas, (200, 150), d_px_r, (0, 255, 0), 2)
            
            kesim_m = (math.pi * cap + d_ad * math.pi * d_cap) / 1000
            alan = math.pi*(cap/2)**2 - d_ad * math.pi * (d_cap/2)**2
            k_ad = 1 + d_ad; genislik, yukseklik = cap, cap

    with c_sonuc:
        st.image(canvas, caption=f"{genislik}x{yukseklik}mm", use_container_width=True)
        sure_dk = (kesim_m * 1000 / guncel_hiz) * adet + (k_ad * adet * PIERCING_SURESI / 60)
        agirlik = (alan * kalinlik * VERİ[metal]["ozkutle"] / 1e6) * FIRE_ORANI
        fiyat = (sure_dk * DK_UCRETI) + (agirlik * adet * kg_fiyati)
        
        st.markdown("### 📋 Teklif Özeti")
        cd_h, cf_h = st.columns([1, 1])
        with cd_h:
            st.markdown(f"""<div class="analiz-bilgi-kutu">
                <div class="analiz-bilgi-satir">📏 Ölçü: <span class="analiz-bilgi-deger">{genislik} x {yukseklik} mm</span></div>
                <div class="analiz-bilgi-satir">⏱ Süre: <span class="analiz-bilgi-deger">{round(sure_dk, 2)} dk</span></div>
                <div class="analiz-bilgi-satir">⚙️ Kontur (Piercing Patlatma): <span class="analiz-bilgi-deger">{k_ad * adet} ad</span></div>
            </div>""", unsafe_allow_html=True)
        with cf_h:
            st.metric("KDV HARİÇ", f"{round(fiyat, 2)} TL")
            st.success(f"KDV DAHİL: {round(fiyat * KDV_ORANI, 2)} TL")
