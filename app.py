import streamlit as st
from PIL import Image
import cv2
import numpy as np
import math
import tempfile
import os
import io

# --- HARİCİ VERİ DOSYASINDAN OKUMA ---
import materials  # materials.py dosyasını dahil ediyoruz

from fpdf import FPDF

def generate_pdf(data_dict):
    pdf = FPDF()
    pdf.add_page()
    
    # Başlık ve Logo Alanı
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "ALAN LAZER TEKLIF FORMU", ln=True, align="C")
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 10, "www.alanlazer.com", ln=True, align="C")
    pdf.line(10, 30, 200, 30)
    pdf.ln(10)
    
    # Malzeme Bilgileri
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "Malzeme Bilgileri", ln=True)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(95, 8, f"Metal Turu: {data_dict['metal']}", border=1)
    pdf.cell(95, 8, f"Kalinlik: {data_dict['kalinlik']} mm", border=1, ln=True)
    pdf.cell(95, 8, f"Adet: {data_dict['adet']}", border=1)
    pdf.cell(95, 8, f"Plaka Boyutu: {data_dict['plaka']}", border=1, ln=True)
    pdf.ln(5)
    
    # Analiz Sonuclari
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "Analiz Detaylari", ln=True)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(95, 8, f"Olcu: {data_dict['olcu']}", border=1)
    pdf.cell(95, 8, f"Kesim Suresi: {data_dict['sure']} dk", border=1, ln=True)
    pdf.cell(95, 8, f"Kontur Sayisi: {data_dict['kontur']} ad", border=1)
    pdf.cell(95, 8, f"Kesim Hizi: {data_dict['hiz']} mm/dk", border=1, ln=True)
    pdf.ln(5)
    
    # Fiyatlandirma
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "Fiyatlandirma", ln=True)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(95, 10, f"TOPLAM (KDV HARIC):", border=1)
    pdf.set_text_color(28, 55, 104) # Lacivert
    pdf.cell(95, 10, f"{data_dict['fiyat_haric']} TL", border=1, ln=True, align="R")
    
    pdf.set_text_color(22, 101, 52) # Yesil
    pdf.cell(95, 10, f"TOPLAM (KDV DAHIL):", border=1)
    pdf.cell(95, 10, f"{data_dict['fiyat_dahil']} TL", border=1, ln=True, align="R")
    
    pdf.ln(10)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "I", 8)
    pdf.cell(0, 10, "Bu belge sistem tarafindan otomatik olarak olusturulmustur.", align="C")
    
    return pdf.output()
    
# --- KÜTÜPHANE KONTROLÜ (Hata Yönetimi) ---
try:
    import ezdxf
    from ezdxf import bbox
    import matplotlib
    matplotlib.use('Agg') # GUI olmadan çalışması için backend
    import matplotlib.pyplot as plt
    from ezdxf.addons.drawing import RenderContext, Frontend
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    dxf_active = True
except ImportError:
    dxf_active = False

# --- 1. AYARLAR VE FAVICON ---
try:
    fav_icon = Image.open("tarayici.png")
except:
    fav_icon = None 

st.set_page_config(page_title="Alan Lazer Teklif Paneli", layout="wide", page_icon=fav_icon)

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
            font-size: 30px !important;
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

# --- 4. SABİT PARAMETRELER (Artık materials.py'den geliyor) ---
DK_UCRETI = materials.DK_UCRETI
# PIERCING_SURESI satırını buradan sildik çünkü dinamik çekeceğiz.
FIRE_ORANI = materials.FIRE_ORANI
KDV_ORANI = materials.KDV_ORANI

# --- 5. SIDEBAR (REVİZE EDİLDİ: YERLEŞİM VE TASARIM) ---
with st.sidebar:
    try:
        st.image("logo.png", use_column_width=True)
    except:
        st.markdown("<h1 style='text-align: center; color: #1C3768;'>ALAN LAZER</h1>", unsafe_allow_html=True)
    
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
    
    # 1. Metal, Kalınlık ve Adet Seçimi
    metal = st.selectbox("Metal Türü", list(materials.VERİ.keys()))
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        kalinlik = st.selectbox("Kalınlık (mm)", materials.VERİ[metal]["kalinliklar"])
    with col_s2:
        adet = st.number_input("Adet", min_value=1, value=1, step=1)

    # 2. Plaka Seçenekleri Mantığı (Tüm Malzemeler İçin Ortak)
    if 0.8 <= kalinlik <= 1.5:
        # İnce Malzemeler: 125x250 seçeneği var, 6 metre yok
        plaka_secenekleri = {
            "100x200 cm": (1000, 2000),  
            "150x300 cm": (1500, 3000)
        }
    else:
        # Kalın Malzemeler (2mm+): 125x250 kalkar, 6 metre gelir
        plaka_secenekleri = {
            "100x200 cm": (1000, 2000), 
            "150x300 cm": (1500, 3000), 
            "150x600 cm": (1500, 6000)
        }

    secilen_plaka_adi = st.selectbox("Plaka Boyutu", list(plaka_secenekleri.keys()))

    # --- 3. BİLGİ KUTUCUKLARI (YERİ DEĞİŞTİRİLDİ VE TASARIMI GÜNCELLENDİ) ---
    # Plaka boyutu ile Fiyat girişi arasına alındı.
    # Taşmayı önlemek için başlık ve değer alt alta (dikey) hizalandı.
    
    hiz_tablosu = materials.VERİ[metal]["hizlar"]
    guncel_hiz = hiz_tablosu.get(kalinlik, 1000)
    
    # Fiyat değişkenini session_state ile yönetiyoruz ki kutucuk anlık güncellensin
    if 'temp_kg_fiyat' not in st.session_state:
        st.session_state.temp_kg_fiyat = float(materials.VARSAYILAN_FIYATLAR.get(metal, 33.0))

    st.markdown("<br>", unsafe_allow_html=True) # Küçük bir boşluk

    col_i1, col_i2 = st.columns(2)
    with col_i1:
        # Mavi Kutu: Hız
        st.markdown(f"""
            <div style="background-color: #e7f3fe; padding: 10px; border-radius: 8px; border-left: 4px solid #2196F3; color: #0c5460; min-height: 70px;">
                <div style="font-size: 11px; font-weight: 600; opacity: 0.8; margin-bottom: 2px;">Hız(mm/dk)</div>
                <div style="font-size: 17px; font-weight: bold;">{guncel_hiz}</div>
            </div>
        """, unsafe_allow_html=True)
    with col_i2:
        # Yeşil Kutu: Birim Fiyat
        st.markdown(f"""
            <div style="background-color: #d4edda; padding: 10px; border-radius: 8px; border-left: 4px solid #28a745; color: #155724; min-height: 70px;">
                <div style="font-size: 11px; font-weight: 600; opacity: 0.8; margin-bottom: 2px;">Birim(TL/kg)</div>
                <div style="font-size: 17px; font-weight: bold;">{st.session_state.temp_kg_fiyat} TL</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

    # --- 4. MALZEME KG FİYATI GİRİŞİ (KUTUCUKLARDAN SONRA) ---
    kg_fiyati = st.number_input(
        "Malzeme KG Fiyatı (TL)", 
        min_value=0.0, 
        value=st.session_state.temp_kg_fiyat, 
        step=1.0, 
        format="%g",
        key="kg_input_field"
    )
    # Değişikliği anında yukarıdaki yeşil kutuya yansıt
    st.session_state.temp_kg_fiyat = kg_fiyati

# --- 6. ANA PANEL İÇERİĞİ ---
st.title("AI DESTEKLİ PROFESYONEL ANALİZ")

# === DURUM A: ANASAYFA ===
if st.session_state.sayfa == 'anasayfa':
    st.markdown("### Lütfen yapmak istediğiniz işlem türünü seçiniz:")
    st.markdown("---")
    
    c1, c2, c3 = st.columns(3, gap="medium")
    
    # Kutucukların içeriği ne kadar kısa veya uzun olursa olsun
    # metin alanı en az 220px yer kaplayacak. Böylece butonlar hep aynı hizada başlar.
    box_style = "min-height: 220px; display: flex; flex-direction: column;"
    
    with c1:
        st.info("📸 **FOTOĞRAFTAN ANALİZ**")
        st.markdown(f"""
        <div style="{box_style}">
            <p style="margin-bottom: 10px;">Fotoğraf veya eskiz görsellerini yükleyin. <b>AI görüntü işleme algoritmamız</b> işini yapsın.</p>
            <p style="margin-bottom: 5px;"><b>Özellikler:</b></p>
            <ul style="margin-top: 0;">
                <li>JPG, PNG formatı</li>
                <li>Referans Ölçü ile Ölçekleme</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("FOTOĞRAF YÜKLE", use_container_width=True, type="primary"):
            sayfa_degistir('foto_analiz')
            st.rerun()

    with c2:
        st.warning("📐 **TEKNİK ÇİZİM ANALİZİ (DXF)**")
        st.markdown(f"""
        <div style="{box_style}">
            <p style="margin-bottom: 10px;">Vektörel çizim dosyanızı doğrudan yükleyerek %100 hassas sonuç alın.</p>
            <p style="margin-bottom: 5px;"><b>Özellikler:</b></p>
            <ul style="margin-top: 0;">
                <li>Yalnızca DXF Desteği</li>
                <li>Otomatik Yerleşim (Nesting)</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("ÇİZİM DOSYASI YÜKLE", use_container_width=True, type="primary"):
            sayfa_degistir('dxf_analiz')
            st.rerun()

    with c3:
        st.success("🛠 **HAZIR PARÇA OLUŞTUR**")
        st.markdown(f"""
        <div style="{box_style}">
            <p style="margin-bottom: 10px;">Çiziminiz yoksa; standart geometrik şekilleri (Kare, Flanş vb.) manuel oluşturun.</p>
            <p style="margin-bottom: 5px;"><b>Özellikler:</b></p>
            <ul style="margin-top: 0;">
                <li>Kare, Dikdörtgen, Daire</li>
                <li>Delik Tanımlama</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
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
                    agirlik = (cv2.contourArea(all_pts) * (oran**2) * kalinlik * materials.VERİ[metal]["ozkutle"] / 1e6) * FIRE_ORANI
                    fiyat = (sure_dk * DK_UCRETI) + (agirlik * adet * kg_fiyati)
                    kdvli_fiyat = fiyat * KDV_ORANI

                    st.markdown("### 📋 Teklif Özeti")
                    cd_f, cf_f = st.columns([1, 1])
                    with cd_f:
                        st.markdown(f"""<div class="analiz-bilgi-kutu">
                            <div class="analiz-bilgi-satir">Ölçü: <span class="analiz-bilgi-deger">{round(gercek_genislik, 1)} x {round(gercek_yukseklik, 1)} mm</span></div>
                            <div class="analiz-bilgi-satir">Süre: <span class="analiz-bilgi-deger">{round(sure_dk, 2)} dk</span></div>
                            <div class="analiz-bilgi-satir">⚙️ Kontur (Piercing Patlatma): <span class="analiz-bilgi-deger">{kontur_ad * adet} ad</span></div>
                        </div>""", unsafe_allow_html=True)
                    with cf_f:
                        st.markdown(f"""<div class="analiz-bilgi-kutu">
                            <div class="analiz-bilgi-satir" style="color: #31333F; font-weight: 600; text-transform: uppercase;">KDV HARİÇ</div>
                            <div style="font-size: 28px; font-weight: bold; color: #1C3768; margin-bottom: 8px;">{round(fiyat, 2)} TL</div>
                            <div style="background-color: #dcfce7; color: #166534; padding: 10px; border-radius: 6px; font-weight: bold; font-size: 20px; border-left: 5px solid #166534;">
                                KDV DAHİL: {round(kdvli_fiyat, 2)} TL
                            </div>
                        </div>""", unsafe_allow_html=True)
                    
        else:
             st.info("Lütfen bir görsel yükleyiniz.")

# === DURUM C: TEKNİK ÇİZİM ANALİZ (DXF GÖRSELLEŞTİRME - MATPLOTLIB BACKEND) ===
elif st.session_state.sayfa == 'dxf_analiz':
    if st.button("⬅️ Ana Menüye Dön"):
        sayfa_degistir('anasayfa')
        st.rerun()

    st.divider()
    c_dxf_ayar, c_dxf_sonuc = st.columns([1, 2])

    with c_dxf_ayar:
        st.subheader("Teknik Çizim Yükle")
        if not dxf_active:
            st.error("⚠️ 'ezdxf' veya 'matplotlib' kütüphanesi eksik!")
            st.info("Lütfen proje klasörünüze 'requirements.txt' dosyasını ekleyin.")
        
        # Hassasiyet ayarı
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

                # 2. GÖRSELLEŞTİRME (Koyu Mod + Tam Geometri)
                # Bounding Box Hesapla
                try:
                    bbox_cache = bbox.extents(msp)
                    w_real = bbox_cache.extmax.x - bbox_cache.extmin.x
                    h_real = bbox_cache.extmax.y - bbox_cache.extmin.y
                except:
                    w_real, h_real = 0, 0
                
                if w_real > 0 and h_real > 0:
                    # Matplotlib Figürü (Koyu Arkaplan)
                    fig = plt.figure(figsize=(10, 10), facecolor='#111827')
                    ax = fig.add_axes([0, 0, 1, 1])
                    ax.set_facecolor('#111827')
                    
                    # Çizim Context (Beyaz Çizgiler)
                    ctx = RenderContext(doc)
                    for layer in ctx.layers.values():
                        layer.color = '#FFFFFF' 
                    
                    # Çizimi Yap
                    out = MatplotlibBackend(ax)
                    Frontend(ctx, out).draw_layout(msp, finalize=True)
                    
                    ax.set_aspect('equal', 'datalim')
                    ax.axis('off')
                    
                    # Matplotlib Yeni Sürüm Uyumluluğu
                    fig.canvas.draw()
                    width, height = fig.canvas.get_width_height()
                    img_data = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8).reshape(height, width, 4)
                    plt.close(fig)
                    
                    # OpenCV Formatına (RGBA -> BGR) Dönüştür
                    dxf_img_bgr = cv2.cvtColor(img_data, cv2.COLOR_RGBA2BGR)
                    
                    # 3. Kontur Analizi
                    gray = cv2.cvtColor(dxf_img_bgr, cv2.COLOR_BGR2GRAY)
                    _, binary = cv2.threshold(gray, hassasiyet_dxf, 255, cv2.THRESH_BINARY)
                    contours, hierarchy = cv2.findContours(binary, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
                    
                    valid_cnts = []
                    if contours and hierarchy is not None:
                        for i, cnt in enumerate(contours):
                            if cv2.contourArea(cnt) < 5: continue 
                            valid_cnts.append(cnt)
                    
                    # Sonuç Gösterimi
                    result_img = dxf_img_bgr.copy()
                    cv2.drawContours(result_img, valid_cnts, -1, (0, 255, 0), 2)
                    st.image(result_img, caption=f"DXF Görselleştirme: {uploaded_dxf.name}", use_container_width=True)
                    
                    # 4. Hesaplamalar
                    if valid_cnts:
                        all_pts = np.concatenate(valid_cnts)
                        x_p, y_p, w_p, h_p = cv2.boundingRect(all_pts)
                        scale_ratio = w_real / w_p # mm / pixel
                        
                        toplam_piksel_yol = sum([cv2.arcLength(c, True) for c in valid_cnts])
                        kesim_m = (toplam_piksel_yol * scale_ratio) / 1000.0 # metre
                        piercing_basi = len(valid_cnts)
                        
                        sure_dk = (kesim_m * 1000 / guncel_hiz) * adet + (piercing_basi * adet * PIERCING_SURESI / 60)
                        agirlik = (w_real * h_real * kalinlik * materials.VERİ[metal]["ozkutle"] / 1e6) * FIRE_ORANI
                        
                        toplam_fiyat = (sure_dk * DK_UCRETI) + (agirlik * adet * kg_fiyati)
                        kdvli_fiyat = toplam_fiyat * KDV_ORANI
                        
                        st.success(f"✅ Analiz Başarılı: {uploaded_dxf.name}")
                        st.markdown("### 📋 Teklif Özeti")
                        
                        cd_d, cf_d = st.columns([1, 1])
                        with cd_d:
                            st.markdown(f"""<div class="analiz-bilgi-kutu">
                                <div class="analiz-bilgi-satir">Ölçü: <span class="analiz-bilgi-deger">{round(w_real, 1)} x {round(h_real, 1)} mm</span></div>
                                <div class="analiz-bilgi-satir">Süre: <span class="analiz-bilgi-deger">{round(sure_dk, 2)} dk</span></div>
                                <div class="analiz-bilgi-satir">⚙️ Kontur (Piercing Patlatma): <span class="analiz-bilgi-deger">{piercing_basi * adet} ad</span></div>
                            </div>""", unsafe_allow_html=True)
                        with cf_d:
                            st.markdown(f"""<div class="analiz-bilgi-kutu">
                                <div class="analiz-bilgi-satir" style="text-transform: uppercase; font-weight: 600;">KDV HARİÇ</div>
                                <div style="font-size: 28px; font-weight: bold; color: #1C3768; margin-bottom: 8px;">{round(toplam_fiyat, 2)} TL</div>
                                <div style="background-color: #dcfce7; color: #166534; padding: 10px; border-radius: 6px; font-weight: bold; font-size: 20px; border-left: 3px solid #166534;">
                                    KDV DAHİL: {round(kdvli_fiyat, 2)} TL
                                </div>
                            </div>""", unsafe_allow_html=True)
                    else:
                        st.warning("Görsel üzerinde kesim yolu algılanamadı.")
                else:
                    st.warning("DXF dosyasında geçerli çizim verisi bulunamadı.")

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
        
        # --- KARE / DİKDÖRTGEN MANTIĞI ---
        if sekil_tipi == "Kare / Dikdörtgen":
            genislik = st.number_input("Genişlik (mm)", min_value=1.0, value=100.0, step=10.0, format="%g")
            yukseklik = st.number_input("Yükseklik (mm)", min_value=1.0, value=100.0, step=10.0, format="%g")
            delik_sayisi = st.number_input("Delik Sayısı", min_value=0, value=0, step=1)
            delik_capi = st.number_input("Delik Çapı (mm)", min_value=0.0, value=10.0, step=1.0, format="%g")
            
            canvas = np.zeros((400, 600, 3), dtype="uint8") + 255 # Beyaz zemin
            max_dim = max(genislik, yukseklik)
            scale = 300 / max_dim 
            w_px, h_px = int(genislik * scale), int(yukseklik * scale)
            start_x, start_y = (600 - w_px) // 2, (400 - h_px) // 2
            
            cv2.rectangle(canvas, (start_x, start_y), (start_x + w_px, start_y + h_px), (0, 0, 0), 2)
            
            if delik_sayisi > 0 and delik_capi > 0:
                d_px_r = int((delik_capi * scale) / 2)
                padding = d_px_r + 15
                coords = [
                    (start_x + padding, start_y + padding), 
                    (start_x + w_px - padding, start_y + padding),
                    (start_x + w_px - padding, start_y + h_px - padding),
                    (start_x + padding, start_y + h_px - padding),
                    (start_x + w_px // 2, start_y + h_px // 2)
                ]

                if delik_sayisi <= 5:
                    count_to_draw = min(delik_sayisi, 5)
                    if delik_sayisi == 1:
                         cv2.circle(canvas, coords[4], d_px_r, (0, 0, 255), 2)
                    else:
                        for i in range(count_to_draw):
                            pos = coords[i]
                            cv2.circle(canvas, pos, d_px_r, (0, 0, 255), 2)
                else:
                    center_pos = coords[4]
                    cv2.circle(canvas, center_pos, d_px_r, (0, 0, 255), 2)
                    text = f"{delik_sayisi} adet"
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 0.7
                    thickness = 2
                    text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
                    text_x = center_pos[0] + d_px_r + 10
                    text_y = center_pos[1] + 5
                    cv2.putText(canvas, text, (text_x, text_y), font, font_scale, (0, 0, 0), thickness)

            toplam_kesim_mm = 2 * (genislik + yukseklik) + delik_sayisi * (math.pi * delik_capi)
            net_alan_mm2 = (genislik * yukseklik) - delik_sayisi * (math.pi * (delik_capi/2)**2)
            piercing_sayisi = 1 + delik_sayisi
            
            canvas_rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)

        # --- DAİRE / FLANŞ MANTIĞI ---
        elif sekil_tipi == "Daire / Flanş":
            cap = st.number_input("Dış Çap (mm)", min_value=1.0, value=100.0, step=10.0, format="%g")
            delik_sayisi = st.number_input("İç Delik Sayısı", min_value=0, value=1, step=1)
            delik_capi = st.number_input("Delik Çapı (mm)", min_value=0.0, value=50.0, step=1.0, format="%g")
            
            canvas = np.zeros((400, 400, 3), dtype="uint8") + 255 # Beyaz zemin
            r_px = 140
            center = (200, 200)
            
            cv2.circle(canvas, center, r_px, (0, 0, 0), 2)
            
            if delik_sayisi > 0 and delik_capi > 0:
                d_px_r = int(((delik_capi / cap) * r_px)) 
                
                if delik_sayisi <= 5:
                    if delik_sayisi == 1:
                        cv2.circle(canvas, center, d_px_r, (0, 0, 255), 2)
                    else:
                        orbit_radius = r_px * 0.6 
                        for i in range(delik_sayisi):
                            angle = (2 * math.pi / delik_sayisi) * i
                            dx = int(center[0] + orbit_radius * math.cos(angle))
                            dy = int(center[1] + orbit_radius * math.sin(angle))
                            cv2.circle(canvas, (dx, dy), d_px_r, (0, 0, 255), 2)
                else:
                    cv2.circle(canvas, center, d_px_r, (0, 0, 255), 2)
                    text = f"{delik_sayisi} adet"
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 0.7
                    thickness = 2
                    text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
                    text_x = center[0] - (text_size[0] // 2)
                    text_y = center[1] + d_px_r + 30
                    cv2.putText(canvas, text, (text_x, text_y), font, font_scale, (0, 0, 0), thickness)

            toplam_kesim_mm = math.pi * cap + delik_sayisi * (math.pi * delik_capi)
            net_alan_mm2 = math.pi * (cap/2)**2 - delik_sayisi * (math.pi * (delik_capi/2)**2)
            piercing_sayisi = 1 + delik_sayisi
            genislik, yukseklik = cap, cap
            
            canvas_rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)

    with c_sonuc:
        st.image(canvas_rgb, caption=f"Önizleme: {genislik}x{yukseklik}mm", use_container_width=True)
        
        kesim_m = toplam_kesim_mm / 1000
        sure_dk = (kesim_m * 1000 / guncel_hiz) * adet + (piercing_sayisi * adet * PIERCING_SURESI / 60)
        agirlik = (net_alan_mm2 * kalinlik * materials.VERİ[metal]["ozkutle"] / 1e6) * FIRE_ORANI
        toplam_fiyat = (sure_dk * DK_UCRETI) + (agirlik * adet * kg_fiyati)
        kdvli_fiyat = toplam_fiyat * KDV_ORANI
        
        st.markdown("### 📋 Teklif Özeti")
        cd_h, cf_h = st.columns([1, 1])
        with cd_h:
            st.markdown(f"""<div class="analiz-bilgi-kutu">
                <div class="analiz-bilgi-satir">Ölçü: <span class="analiz-bilgi-deger">{genislik} x {yukseklik} mm</span></div>
                <div class="analiz-bilgi-satir">Süre: <span class="analiz-bilgi-deger">{round(sure_dk, 2)} dk</span></div>
                <div class="analiz-bilgi-satir">⚙️ Kontur (Piercing Patlatma): <span class="analiz-bilgi-deger">{piercing_sayisi * adet} ad</span></div>
            </div>""", unsafe_allow_html=True)
        with cf_h:
            st.markdown(f"""<div class="analiz-bilgi-kutu">
                <div class="analiz-bilgi-satir" style="color: #31333F; font-weight: 600; text-transform: uppercase;">KDV HARİÇ</div>
                <div style="font-size: 28px; font-weight: bold; color: #1C3768; margin-bottom: 8px;">{round(toplam_fiyat, 2)} TL</div>
                <div style="background-color: #dcfce7; color: #166534; padding: 10px; border-radius: 6px; font-weight: bold; font-size: 20px; border-left: 5px solid #166534;">
                    KDV DAHİL: {round(kdvli_fiyat, 2)} TL
                </div>
            </div>""", unsafe_allow_html=True)
