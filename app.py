import streamlit as st
import sys
import subprocess
import importlib.util

# --- 0. OTOMATİK KÜTÜPHANE YÜKLEYİCİ (Terminal Açmadan Çözüm) ---
def kutuphane_kontrol_ve_yukle():
    gerekli_paketler = ['ezdxf', 'matplotlib']
    yuklenen_var = False
    
    for paket in gerekli_paketler:
        spec = importlib.util.find_spec(paket)
        if spec is None:
            placeholder = st.empty()
            placeholder.warning(f"⚠️ '{paket}' kütüphanesi eksik. Arka planda otomatik yükleniyor... Lütfen bekleyin.")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", paket])
                placeholder.success(f"✅ '{paket}' başarıyla yüklendi!")
                yuklenen_var = True
            except Exception as e:
                st.error(f"Otomatik yükleme başarısız oldu: {e}")
    
    if yuklenen_var:
        st.success("Tüm gereksinimler sağlandı. Uygulama yeniden başlatılıyor...")
        st.rerun()

# Sayfa ayarlarından önce kontrolü çalıştır
st.set_page_config(page_title="Alan Lazer Teklif Paneli", layout="wide")
kutuphane_kontrol_ve_yukle()

# --- STANDART IMPORTLAR ---
from PIL import Image
import cv2
import numpy as np
import math
import tempfile
import os

# --- KÜTÜPHANE IMPORTLARI (Artık Yüklü Olduğundan Eminiz) ---
try:
    import ezdxf
    from ezdxf import bbox
    import matplotlib
    matplotlib.use('Agg') # GUI olmadan çalışması için
    import matplotlib.pyplot as plt
    from ezdxf.addons.drawing import RenderContext, Frontend
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    dxf_active = True
except ImportError:
    # Otomatik yükleyici çalışmazsa burası son güvenlik ağıdır
    dxf_active = False

# --- 1. AYARLAR VE FAVICON ---
try:
    fav_icon = Image.open("tarayici.png")
except:
    fav_icon = None 

# st.set_page_config yukarıda çağrıldı, burayı geçiyoruz.

# --- 2. CSS STİL AYARLAMALARI ---
st.markdown("""
    <style>
        section[data-testid="stSidebar"] div.block-container {
            padding-top: 0rem;
        }
        [data-testid="stSidebarUserContent"] .element-container:first-child {
            margin-top: 10px;
        }
        div.stButton > button { min-height: 50px; }

        /* Analiz Detay Listesi Tasarımı */
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
        }
        [data-testid="stMetricLabel"] {
            font-size: 13px !important;
            font-weight: 600 !important;
            color: #31333F !important;
            text-transform: uppercase;
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
        st.warning("📐 **TEKNİK ÇİZİM ANALİZİ (DXF)**")
        st.markdown("""
        Vektörel çizim dosyalarınızı (DXF) doğrudan yükleyerek %100 hassas sonuç alın.
        
        **Özellikler:**
        * Yalnızca DXF Desteği
        * Yaylar (ARC) ve Birleşik Çizgiler
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
        referans_olcu = st.number_input(
            "Parçanın Yatay Uzunluğu (mm)", 
            value=100.0, 
            step=10.0, 
            format="%g",
            help="Yüklediğiniz çizimdeki parçanın soldan sağa (yatay) olan gerçek uzunluğunu giriniz."
        )
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
                    x_b, y_b, w_b, h_b = cv2.boundingRect(cnt)
                    # ÇERÇEVE FİLTRESİ
                    if w_b > w_img * 0.96 or h_b > h_img * 0.96: continue
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
                    st.image(cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB), caption="AI Analiz Sonucu", use_container_width=True)

                    kesim_m = (sum([cv2.arcLength(c, True) for c in valid_contour_list]) * oran) / 1000
                    kontur_ad = len(valid_contour_list)
                    sure_dk = (kesim_m * 1000 / guncel_hiz) * adet + (kontur_ad * adet * PIERCING_SURESI / 60)
                    agirlik = (cv2.contourArea(all_pts) * (oran**2) * kalinlik * VERİ[metal]["ozkutle"] / 1e6) * FIRE_ORANI
                    fiyat = (sure_dk * DK_UCRETI) + (agirlik * adet * kg_fiyati)
                    kdvli_fiyat = fiyat * KDV_ORANI

                    st.markdown("### 📋 Teklif Özeti")
                    cd_f, cf_f = st.columns([1, 1])
                    with cd_f:
                        st.markdown(f"""<div class="analiz-bilgi-kutu">
                            <div class="analiz-bilgi-satir">📏 Ölçü (GxY): <span class="analiz-bilgi-deger">{round(gercek_genislik, 1)} x {round(gercek_yukseklik, 1)} mm</span></div>
                            <div class="analiz-bilgi-satir">⏱ Süre: <span class="analiz-bilgi-deger">{round(sure_dk, 2)} dk</span></div>
                            <div class="analiz-bilgi-satir">⚙️ Kontur (Piercing Patlatma): <span class="analiz-bilgi-deger">{kontur_ad * adet} ad</span></div>
                        </div>""", unsafe_allow_html=True)
                    with cf_f:
                        st.metric("KDV HARİÇ", f"{round(fiyat, 2)} TL")
                        st.success(f"KDV DAHİL: {round(kdvli_fiyat, 2)} TL")
        else:
             st.info("Lütfen bir görsel yükleyiniz.")

# === DURUM C: TEKNİK ÇİZİM ANALİZ (YENİLENMİŞ DXF GÖRSELLEŞTİRME) ===
elif st.session_state.sayfa == 'dxf_analiz':
    if st.button("⬅️ Ana Menüye Dön"):
        sayfa_degistir('anasayfa')
        st.rerun()

    st.divider()
    c_dxf_ayar, c_dxf_sonuc = st.columns([1, 2])

    with c_dxf_ayar:
        st.subheader("Teknik Çizim Yükle")
        if not dxf_active:
            st.error("⚠️ Kütüphaneler hala yüklenemedi. Lütfen internet bağlantısını kontrol edip uygulamayı yeniden başlatın.")
        
        hassasiyet_dxf = st.slider("Hassasiyet (Kontur Yakalama)", 50, 255, 100, step=1)
        uploaded_dxf = st.file_uploader("Dosya Seç (Sadece DXF)", type=['dxf'])

    with c_dxf_sonuc:
        if uploaded_dxf and dxf_active:
            try:
                # 1. DXF Dosyasını Oku
                with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp_file:
                    tmp_file.write(uploaded_dxf.getvalue())
                    tmp_path = tmp_file.name

                doc = ezdxf.readfile(tmp_path)
                msp = doc.modelspace()
                os.remove(tmp_path)

                # 2. REVİZE EDİLEN KISIM: MATPLOTLIB İLE GÖRSELLEŞTİRME
                # Arkaplan: Koyu (#111827), Çizgiler: Beyaz (#FFFFFF)
                
                # Gerçek Boyutları Hesapla (Bounding Box)
                bbox_cache = bbox.extents(msp)
                w_real = bbox_cache.extmax.x - bbox_cache.extmin.x
                h_real = bbox_cache.extmax.y - bbox_cache.extmin.y
                
                if w_real > 0 and h_real > 0:
                    # Matplotlib Figürü Oluştur (Koyu Arkaplan)
                    fig = plt.figure(figsize=(10, 10), facecolor='#111827')
                    ax = fig.add_axes([0, 0, 1, 1])
                    ax.set_facecolor('#111827')
                    
                    # Çizim Context Oluştur ve Renkleri Beyaza Zorla
                    ctx = RenderContext(doc)
                    for layer in ctx.layers.values():
                        layer.color = '#FFFFFF' # Tüm katmanlar BEYAZ
                    
                    # Çizimi Yap (ARC ve POLYLINE otomatik çizilir)
                    out = MatplotlibBackend(ax)
                    Frontend(ctx, out).draw_layout(msp, finalize=True)
                    
                    ax.set_aspect('equal', 'datalim')
                    ax.axis('off')
                    
                    # Figürü Resme Çevir (OpenCV ile işlenebilecek hale getir)
                    fig.canvas.draw()
                    
                    # Buffer'dan numpy array'e dönüştür
                    img_data = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
                    img_data = img_data.reshape(fig.canvas.get_width_height()[::-1] + (3,))
                    
                    plt.close(fig) # Bellek temizliği
                    
                    # OpenCV Formatına Dönüştür (RGB -> BGR)
                    dxf_img_bgr = cv2.cvtColor(img_data, cv2.COLOR_RGB2BGR)
                    
                    # 3. Kontur Analizi ve Hesaplama (Görüntü İşleme)
                    gray = cv2.cvtColor(dxf_img_bgr, cv2.COLOR_BGR2GRAY)
                    _, binary = cv2.threshold(gray, hassasiyet_dxf, 255, cv2.THRESH_BINARY)
                    contours, hierarchy = cv2.findContours(binary, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
                    
                    valid_cnts = []
                    if contours and hierarchy is not None:
                        for i, cnt in enumerate(contours):
                            if cv2.contourArea(cnt) < 5: continue 
                            valid_cnts.append(cnt)
                    
                    # Sonuç Gösterimi (Yeşil Kontur Çizgisi Eklenmiş Halde)
                    result_img = dxf_img_bgr.copy()
                    cv2.drawContours(result_img, valid_cnts, -1, (0, 255, 0), 2)
                    st.image(result_img, caption=f"DXF Görselleştirme: {uploaded_dxf.name}", use_container_width=True)
                    
                    # 4. Hesaplamalar
                    h_px_img, w_px_img = dxf_img_bgr.shape[:2]
                    
                    all_pts = np.concatenate(valid_cnts) if valid_cnts else None
                    
                    if all_pts is not None:
                        x_p, y_p, w_p, h_p = cv2.boundingRect(all_pts)
                        scale_ratio = w_real / w_p # mm / pixel
                        
                        toplam_piksel_yol = sum([cv2.arcLength(c, True) for c in valid_cnts])
                        kesim_m = (toplam_piksel_yol * scale_ratio) / 1000.0 # metre
                        piercing_basi = len(valid_cnts)
                        
                        sure_dk = (kesim_m * 1000 / guncel_hiz) * adet + (piercing_basi * adet * PIERCING_SURESI / 60)
                        agirlik = (w_real * h_real * kalinlik * VERİ[metal]["ozkutle"] / 1e6) * FIRE_ORANI
                        
                        toplam_fiyat = (sure_dk * DK_UCRETI) + (agirlik * adet * kg_fiyati)
                        kdvli_fiyat = toplam_fiyat * KDV_ORANI
                        
                        st.success(f"✅ Analiz Başarılı: {uploaded_dxf.name}")
                        st.markdown("### 📋 Teknik Çizim Teklifi")
                        
                        cd_d, cf_d = st.columns([1, 1])
                        with cd_d:
                            st.markdown(f"""<div class="analiz-bilgi-kutu">
                                <div class="analiz-bilgi-satir">Tahmini Ölçü: <span class="analiz-bilgi-deger">{round(w_real, 1)} x {round(h_real, 1)} mm</span></div>
                                <div class="analiz-bilgi-satir">⏱ Süre: <span class="analiz-bilgi-deger">{round(sure_dk, 2)} dk</span></div>
                                <div class="analiz-bilgi-satir">⚙️ Kontur (Piercing Patlatma): <span class="analiz-bilgi-deger">{piercing_basi * adet} ad</span></div>
                            </div>""", unsafe_allow_html=True)
                        with cf_d:
                            st.metric("KDV HARİÇ", f"{round(toplam_fiyat, 2)} TL")
                            st.success(f"KDV DAHİL: {round(kdvli_fiyat, 2)} TL")
                    else:
                        st.warning("Görsel üzerinde kontur algılanamadı.")
                else:
                    st.warning("DXF dosyasında çizim verisi (Line, Arc, Circle vb.) bulunamadı.")

            except Exception as e:
                st.error(f"Hata: {e}")
        else:
            if not uploaded_dxf:
                st.info("Lütfen .DXF uzantılı çizim dosyanızı yükleyiniz.")

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
                    coords = [(start_x + padding, start_y + padding), (start_x + w_px - padding, start_y + padding),
                              (start_x + w_px - padding, start_y + h_px - padding), (start_x + padding, start_y + h_px - padding)]
                    for i in range(min(delik_sayisi, 4)): cv2.circle(canvas, coords[i], d_px_r, (0, 255, 0), 2)

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
                d_px_r = int(((delik_capi / cap) * 120 * 2) / 2)
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
        cd_h, cf_h = st.columns([1, 1])
        with cd_h:
            st.markdown(f"""<div class="analiz-bilgi-kutu">
                <div class="analiz-bilgi-satir">📏 Ölçü: <span class="analiz-bilgi-deger">{genislik} x {yukseklik} mm</span></div>
                <div class="analiz-bilgi-satir">⏱ Süre: <span class="analiz-bilgi-deger">{round(sure_dk, 2)} dk</span></div>
                <div class="analiz-bilgi-satir">⚙️ Kontur (Piercing Patlatma): <span class="analiz-bilgi-deger">{piercing_sayisi * adet} ad</span></div>
            </div>""", unsafe_allow_html=True)
        with cf_h:
            st.metric("KDV HARİÇ", f"{round(toplam_fiyat, 2)} TL")
            st.success(f"KDV DAHİL: {round(kdvli_fiyat, 2)} TL")
