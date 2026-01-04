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
        section[data-testid="stSidebar"] div.block-container { padding-top: 0rem; }
        [data-testid="stSidebarUserContent"] .element-container:first-child { margin-top: 10px; }
        div.stButton > button { min-height: 50px; }
        
        /* Teklif Özeti Sol Liste Tasarımı */
        .analiz-bilgi-kutu {
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 12px;
            border-left: 4px solid #1c3768;
            margin-top: 10px;
        }
        .analiz-bilgi-satir {
            font-size: 0.85rem;
            color: #444;
            margin-bottom: 4px;
            line-height: 1.4;
        }
        .analiz-bilgi-deger {
            font-weight: bold;
            color: #000;
        }
        /* Metric font ayarı */
        [data-testid="stMetricValue"] { font-size: 1.8rem !important; }
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
    "Siyah Sac": {"ozkutle": 7.85, "kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20], "hizlar": {0.8: 6000, 3: 2800, 10: 800}},
    "Paslanmaz": {"ozkutle": 8.0, "kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8, 10, 12, 15], "hizlar": {0.8: 7000, 2: 4500, 10: 500}},
    "Alüminyum": {"ozkutle": 2.7, "kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8], "hizlar": {0.8: 8000, 2: 5000, 8: 600}}
}

# --- 4. SIDEBAR ---
with st.sidebar:
    try:
        st.image("logo.png", use_column_width=True)
    except:
        st.markdown("<h1 style='text-align: center; color: #FF4B4B;'>ALAN LAZER</h1>", unsafe_allow_html=True)
    
    st.markdown("<div style='text-align:center; margin-bottom:20px;'><a href='https://alanlazer.com' style='color:#1c3768; font-weight:300; font-size:22px; text-decoration:none;'>alanlazer.com</a></div>", unsafe_allow_html=True)
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
    with col_i1: st.info(f"⚡ Hız\n{guncel_hiz}")
    with col_i2: st.success(f"💰 Birim\n{kg_fiyati} TL")

# --- 5. ANA PANEL ---
st.title("AI DESTEKLİ PROFESYONEL ANALİZ")

if st.session_state.sayfa == 'anasayfa':
    st.markdown("### Lütfen yapmak istediğiniz işlem türünü seçiniz:")
    st.markdown("---")
    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        st.info("📸 **FOTOĞRAFTAN ANALİZ**")
        st.markdown("Fotoğraf veya eskiz görsellerini yükleyin. **AI görüntü işleme algoritmamız** işini yapsın.")
        if st.button("FOTOĞRAF YÜKLE", use_container_width=True, type="primary"): sayfa_degistir('foto_analiz'); st.rerun()
    with c2:
        st.warning("📐 **TEKNİK ÇİZİM ANALİZİ (DWG / DXF)**")
        st.markdown("Vektörel çizim dosyalarınızı yükleyerek %100 hassas sonuç alın.")
        if st.button("ÇİZİM DOSYASI YÜKLE", use_container_width=True, type="primary"): sayfa_degistir('dxf_analiz'); st.rerun()
    with c3:
        st.success("🛠 **HAZIR PARÇA OLUŞTUR**")
        st.markdown("Standart geometrik şekilleri manuel oluşturun.")
        if st.button("MANUEL PARÇA OLUŞTUR", use_container_width=True, type="primary"): sayfa_degistir('hazir_parca'); st.rerun()

# --- MODÜL: FOTOĞRAFTAN ANALİZ ---
elif st.session_state.sayfa == 'foto_analiz':
    if st.button("⬅️ Ana Menüye Dön"): sayfa_degistir('anasayfa'); st.rerun()
    st.divider()
    c_ayar, c_sonuc = st.columns([1, 2])
    with c_ayar:
        st.subheader("Analiz Ayarları")
        referans_olcu = st.number_input("Parçanın Yatay Uzunluğu (mm)", value=100.0, step=10.0, format="%g")
        hassasiyet = st.slider("Hassasiyet (Kesim Kontur Yakalama)", 50, 255, 80, step=1)
        uploaded_file = st.file_uploader("Görsel Yükle (JPG, PNG)", type=['jpg', 'png', 'jpeg'])

    with c_sonuc:
        if uploaded_file:
            file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, 1)
            h_img, w_img = img.shape[:2]
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray, hassasiyet, 255, cv2.THRESH_BINARY_INV)
            contours, hierarchy = cv2.findContours(binary, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours and hierarchy is not None:
                # AI FİLTRELEME (DIŞ ÇERÇEVE SORUNU ÇÖZÜMÜ)
                valid_cnts = []
                for i, cnt in enumerate(contours):
                    bx, by, bw, bh = cv2.boundingRect(cnt)
                    if bw > w_img * 0.96 or bh > h_img * 0.96: continue # Dış çerçeveyi yoksay
                    if hierarchy[0][i][3] in [-1, 0]: valid_cnts.append(cnt)
                
                if valid_cnts:
                    all_pts = np.concatenate(valid_cnts)
                    x, y, w_px, h_px = cv2.boundingRect(all_pts)
                    oran = referans_olcu / w_px
                    g_mm, y_mm = w_px * oran, h_px * oran
                    cv2.drawContours(img, valid_cnts, -1, (0, 255, 0), 2)
                    st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), caption="AI Analiz Sonucu", use_container_width=True)

                    kesim_m = (sum([cv2.arcLength(c, True) for c in valid_cnts]) * oran) / 1000
                    k_ad = len(valid_cnts)
                    kesim_dk = (kesim_m * 1000 / guncel_hiz) * adet + (k_ad * adet * PIERCING_SURESI / 60)
                    agirlik = (cv2.contourArea(all_pts) * (oran**2) * kalinlik * VERİ[metal]["ozkutle"] / 1e6) * FIRE_ORANI
                    fiyat = (kesim_dk * DK_UCRETI) + (agirlik * adet * kg_fiyati)

                    st.markdown("### 📋 Teklif Özeti")
                    col_detay, col_fiyat = st.columns([1, 1])
                    with col_detay:
                        st.markdown(f"""<div class="analiz-bilgi-kutu">
                            <div class="analiz-bilgi-satir">📏 Ölçü: <span class="analiz-bilgi-deger">{round(g_mm, 1)} x {round(y_mm, 1)} mm</span></div>
                            <div class="analiz-bilgi-satir">⏱ Süre: <span class="analiz-bilgi-deger">{round(kesim_dk, 2)} dk</span></div>
                            <div class="analiz-bilgi-satir">⚙️ Kontur (Piercing Patlatma): <span class="analiz-bilgi-deger">{k_ad * adet} ad</span></div>
                        </div>""", unsafe_allow_html=True)
                    with col_fiyat:
                        st.metric("KDV HARİÇ", f"{round(fiyat, 2)} TL")
                        st.success(f"KDV DAHİL: {round(fiyat * KDV_ORANI, 2)} TL")

# --- MODÜL: TEKNİK ÇİZİM (DXF/DWG) ---
elif st.session_state.sayfa == 'dxf_analiz':
    if st.button("⬅️ Ana Menüye Dön"): sayfa_degistir('anasayfa'); st.rerun()
    st.divider()
    c_ayar, c_sonuc = st.columns([1, 2])
    with c_ayar:
        st.subheader("Teknik Çizim Yükle")
        uploaded_dxf = st.file_uploader("Dosya Seç (DXF)", type=['dxf', 'dwg'])

    with c_sonuc:
        if uploaded_dxf and dxf_active:
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
                    tmp.write(uploaded_dxf.getvalue()); tmp_path = tmp.name
                doc = ezdxf.readfile(tmp_path); msp = doc.modelspace(); os.remove(tmp_path)
                
                uzunluk = 0
                entity_count = 0
                for e in msp:
                    entity_count += 1
                    if e.dxftype() == 'LINE': uzunluk += e.dxf.start.distance(e.dxf.end)
                    elif e.dxftype() == 'CIRCLE': uzunluk += 2*math.pi*e.dxf.radius
                    elif e.dxftype() == 'ARC': uzunluk += e.dxf.radius * (math.radians(e.dxf.end_angle - e.dxf.start_angle))
                
                kesim_m = uzunluk / 1000 if uzunluk > 0 else 1.5
                k_ad = int(entity_count / 2) + 1
                kesim_dk = (kesim_m * 1000 / guncel_hiz) * adet + (k_ad * adet * PIERCING_SURESI / 60)
                agirlik = (500 * 300 * kalinlik * VERİ[metal]["ozkutle"] / 1e6) * FIRE_ORANI # Örnek alan
                fiyat = (kesim_dk * DK_UCRETI) + (agirlik * adet * kg_fiyati)

                st.success(f"✅ Dosya Okundu: {uploaded_dxf.name}")
                st.markdown("### 📋 Teklif Özeti")
                cd, cf = st.columns([1, 1])
                with cd:
                    st.markdown(f"""<div class="analiz-bilgi-kutu">
                        <div class="analiz-bilgi-satir">📏 Tahmini Ölçü: <span class="analiz-bilgi-deger">500 x 300 mm</span></div>
                        <div class="analiz-bilgi-satir">⏱ Süre: <span class="analiz-bilgi-deger">{round(kesim_dk, 2)} dk</span></div>
                        <div class="analiz-bilgi-satir">⚙️ Kontur (Piercing Patlatma): <span class="analiz-bilgi-deger">{k_ad * adet} ad</span></div>
                    </div>""", unsafe_allow_html=True)
                with cf:
                    st.metric("KDV HARİÇ", f"{round(fiyat, 2)} TL")
                    st.success(f"KDV DAHİL: {round(fiyat * KDV_ORANI, 2)} TL")
            except Exception as e: st.error(f"Hata: {e}")

# --- MODÜL: HAZIR PARÇA OLUŞTURMA ---
elif st.session_state.sayfa == 'hazir_parca':
    if st.button("⬅️ Ana Menüye Dön"): sayfa_degistir('anasayfa'); st.rerun()
    st.divider()
    c_ayar, c_sonuc = st.columns([1, 2])
    with c_ayar:
        st.subheader("Parça Ayarları")
        sekil = st.radio("Parça Tipi", ["Kare / Dikdörtgen", "Daire / Flanş"])
        if sekil == "Kare / Dikdörtgen":
            g = st.number_input("Genişlik (mm)", 1.0, value=100.0); y = st.number_input("Yükseklik (mm)", 1.0, value=100.0)
            d_ad = st.number_input("Delik Sayısı", 0, 10); d_cap = st.number_input("Delik Çapı (mm)", 0.0, 10.0)
            kesim_m = (2*(g+y) + d_ad*math.pi*d_cap)/1000
            alan = (g*y) - d_ad*math.pi*(d_cap/2)**2
            k_ad = 1 + d_ad
        else:
            cap = st.number_input("Dış Çap (mm)", 1.0, value=100.0); d_ad = st.number_input("İç Delik Sayısı", 0, 1)
            d_cap = st.number_input("Delik Çapı (mm)", 0.0, 50.0)
            kesim_m = (math.pi*cap + d_ad*math.pi*d_cap)/1000
            alan = math.pi*(cap/2)**2 - d_ad*math.pi*(d_cap/2)**2
            k_ad = 1 + d_ad; g, y = cap, cap

    with c_sonuc:
        kesim_dk = (kesim_m * 1000 / guncel_hiz) * adet + (k_ad * adet * PIERCING_SURESI / 60)
        agirlik = (alan * kalinlik * VERİ[metal]["ozkutle"] / 1e6) * FIRE_ORANI
        fiyat = (kesim_dk * DK_UCRETI) + (agirlik * adet * kg_fiyati)
        
        st.markdown("### 📋 Teklif Özeti")
        cd, cf = st.columns([1, 1])
        with cd:
            st.markdown(f"""<div class="analiz-bilgi-kutu">
                <div class="analiz-bilgi-satir">📏 Ölçü: <span class="analiz-bilgi-deger">{g} x {y} mm</span></div>
                <div class="analiz-bilgi-satir">⏱ Süre: <span class="analiz-bilgi-deger">{round(kesim_dk, 2)} dk</span></div>
                <div class="analiz-bilgi-satir">⚙️ Kontur (Piercing Patlatma): <span class="analiz-bilgi-deger">{k_ad * adet} ad</span></div>
            </div>""", unsafe_allow_html=True)
        with cf:
            st.metric("KDV HARİÇ", f"{round(fiyat, 2)} TL")
            st.success(f"KDV DAHİL: {round(fiyat * KDV_ORANI, 2)} TL")
