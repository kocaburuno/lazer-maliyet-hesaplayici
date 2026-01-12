import streamlit as st
from PIL import Image
import cv2
import numpy as np
import math
import tempfile
import os

# --- HARİCİ VERİ DOSYASINDAN OKUMA ---
# materials.py dosyanızın yan tarafta olduğunu varsayıyoruz
import materials 

from fpdf import FPDF

# --- PDF OLUŞTURMA FONKSİYONU ---
def generate_pdf(data_dict, image_path=None):
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # 1. HEADER & LOGO
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, "ALAN LAZER TEKLIF FORMU", ln=True, align="C")
        pdf.set_font("helvetica", "", 10)
        pdf.cell(0, 10, "www.alanlazer.com", ln=True, align="C")
        pdf.line(10, 30, 200, 30)
        pdf.ln(5)
        
        # 2. PARÇA GÖRSELİ
        if image_path and os.path.exists(image_path):
            pdf.image(image_path, x=60, y=35, w=90)
            pdf.ln(95)
        else:
            pdf.ln(20)

        # 3. MALZEME BİLGİLERİ
        pdf.set_font("helvetica", "B", 12)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 8, "  MALZEME BILGILERI", ln=True, fill=True)
        pdf.ln(2)
        
        pdf.set_font("helvetica", "", 10)
        pdf.cell(40, 8, "Metal Turu:", border=0)
        pdf.cell(55, 8, f"{data_dict.get('metal', '-')}", border=1)
        pdf.cell(10, 8, "", border=0)
        pdf.cell(40, 8, "Kalinlik:", border=0)
        pdf.cell(45, 8, f"{data_dict.get('kalinlik', '-')} mm", border=1, ln=True)
        
        pdf.ln(1)
        pdf.cell(40, 8, "Plaka Boyutu:", border=0)
        pdf.cell(55, 8, f"{data_dict.get('plaka', '-')}", border=1)
        pdf.cell(10, 8, "", border=0)
        pdf.cell(40, 8, "Adet:", border=0)
        pdf.cell(45, 8, f"{data_dict.get('adet', '-')}", border=1, ln=True)
        pdf.ln(5)
        
        # 4. ANALİZ VE TEKNİK DETAYLAR
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 8, "  TEKNIK ANALIZ OZETI", ln=True, fill=True)
        pdf.ln(2)
        
        pdf.set_font("helvetica", "", 10)
        pdf.cell(40, 8, "Parca Olcusu:", border=0)
        pdf.cell(55, 8, f"{data_dict.get('olcu', '-')}", border=1)
        pdf.cell(10, 8, "", border=0)
        pdf.cell(40, 8, "Kesim Suresi:", border=0)
        pdf.cell(45, 8, f"{data_dict.get('sure', '-')} dk", border=1, ln=True)
        
        pdf.ln(1)
        pdf.cell(40, 8, "Kontur (Patlatma):", border=0)
        pdf.cell(55, 8, f"{data_dict.get('kontur', '-')} ad", border=1)
        pdf.cell(10, 8, "", border=0)
        pdf.cell(40, 8, "Kesim Hizi:", border=0)
        pdf.cell(45, 8, f"{data_dict.get('hiz', '-')} mm/dk", border=1, ln=True)
        pdf.ln(10)
        
        # 5. FİYATLANDIRMA
        pdf.set_draw_color(28, 55, 104)
        pdf.set_line_width(0.5)
        pdf.rect(10, pdf.get_y(), 190, 35)
        
        pdf.set_y(pdf.get_y() + 5)
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 10, "TEKLIF OZETI", ln=True, align="C")
        
        pdf.set_font("helvetica", "B", 11)
        pdf.set_text_color(28, 55, 104)
        pdf.cell(95, 10, f"TOPLAM (KDV HARIC):   {data_dict.get('fiyat_haric', '-')} TL", border=0, align="C")
        
        pdf.set_text_color(22, 101, 52)
        pdf.cell(95, 10, f"TOPLAM (KDV DAHIL):   {data_dict.get('fiyat_dahil', '-')} TL", border=0, ln=True, align="C")
        
        # FOOTER
        pdf.set_y(-30)
        pdf.set_text_color(100, 100, 100)
        pdf.set_font("helvetica", "I", 8)
        pdf.cell(0, 5, "Bu belge sistem tarafindan otomatik olarak olusturulmustur.", ln=True, align="C")
        pdf.cell(0, 5, "Fiyatlar malzeme piyasa kosullarina gore degisiklik gosterebilir.", ln=True, align="C")
        
        return bytes(pdf.output())
    except Exception as e:
        return str(e).encode()

# --- MERKEZİ HESAPLAMA VE GÖSTERİM FONKSİYONU (YENİ - SADELEŞTİRME İÇİN) ---
def hesapla_ve_goster(kesim_uzunlugu_m, kontur_sayisi, alan_mm2, w_mm, h_mm, result_img_bgr):
    """
    Tüm sayfalarda tekrar eden matematiksel hesaplamaları ve görselleştirmeyi yapar.
    """
    # Global değişkenleri çek
    try:
        kg_fiyat = st.session_state.kg_input_field
    except:
        kg_fiyat = 0
        
    # Hesaplamalar
    p_suresi = materials.PIERCING_SURELERI.get(kalinlik, 1.0)
    
    # 1. Süre Hesabı
    sure_dk = (kesim_uzunlugu_m * 1000 / guncel_hiz) * adet + (kontur_sayisi * adet * p_suresi / 60)
    
    # 2. Ağırlık ve Fiyat Hesabı
    # Alan mm2 cinsinden geliyor, bunu metrekareye çevirip özgül ağırlıkla çarpıyoruz
    # (mm2 / 10^6 = m2) * kalınlık(mm) * özgül ağırlık yaklaşık hesabı
    # Not: Ozkütle genellikle g/cm3 veya kg/m2/mm verilir. Kodunuzdaki formüle sadık kalındı.
    agirlik = (alan_mm2 * kalinlik * materials.VERİ[metal]["ozkutle"] / 1e6) * FIRE_ORANI
    fiyat = (sure_dk * DK_UCRETI) + (agirlik * adet * kg_fiyat)
    kdvli_fiyat = fiyat * KDV_ORANI

    # Ekrana Yazdırma (UI)
    st.markdown("### 📋 Teklif Özeti")
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.markdown(f"""<div class="analiz-bilgi-kutu">
            <div class="analiz-bilgi-satir">Ölçü: <span class="analiz-bilgi-deger">{round(w_mm, 1)} x {round(h_mm, 1)} mm</span></div>
            <div class="analiz-bilgi-satir">Süre: <span class="analiz-bilgi-deger">{round(sure_dk, 2)} dk</span></div>
            <div class="analiz-bilgi-satir">⚙️ Kontur (Piercing): <span class="analiz-bilgi-deger">{kontur_sayisi * adet} ad</span></div>
        </div>""", unsafe_allow_html=True)
        
    with c2:
        st.markdown(f"""<div class="analiz-bilgi-kutu">
            <div class="analiz-bilgi-satir" style="color: #31333F; font-weight: 600; text-transform: uppercase;">KDV HARİÇ</div>
            <div style="font-size: 28px; font-weight: bold; color: #1C3768; margin-bottom: 8px;">{round(fiyat, 2)} TL</div>
            <div style="background-color: #dcfce7; color: #166534; padding: 10px; border-radius: 6px; font-weight: bold; font-size: 20px; border-left: 5px solid #166534;">
                KDV DAHİL: {round(kdvli_fiyat, 2)} TL
            </div>
        </div>""", unsafe_allow_html=True)

    # PDF Oluşturma
    pdf_bytes = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_img:
            cv2.imwrite(tmp_img.name, result_img_bgr)
            pdf_data = {
                "metal": metal, "kalinlik": kalinlik, "adet": adet, 
                "plaka": secilen_plaka_adi, "olcu": f"{round(w_mm,1)}x{round(h_mm,1)}", 
                "sure": round(sure_dk,2), "kontur": kontur_sayisi * adet, 
                "hiz": guncel_hiz, "fiyat_haric": round(fiyat,2), 
                "fiyat_dahil": round(kdvli_fiyat,2)
            }
            pdf_bytes = generate_pdf(pdf_data, image_path=tmp_img.name)
        os.unlink(tmp_img.name)
    except:
        pass
        
    st.markdown('<div class="floating-pdf-container">📄 <b>Teklif Hazır</b>', unsafe_allow_html=True)
    if pdf_bytes:
        st.download_button("PDF İndir", data=pdf_bytes, file_name="Teklif.pdf", mime="application/pdf", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    
# --- KÜTÜPHANE KONTROLÜ ---
try:
    import ezdxf
    from ezdxf import bbox
    import matplotlib
    matplotlib.use('Agg')
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
        section[data-testid="stSidebar"] div.block-container { padding-top: 0rem; }
        [data-testid="stSidebarUserContent"] .element-container:first-child { margin-top: 10px; }
        div.stButton > button { min-height: 50px; }
        .analiz-bilgi-kutu {
            background-color: #f8f9fa; border-radius: 8px; padding: 12px;
            border-left: 5px solid #1c3768; margin-top: 10px;
        }
        .analiz-bilgi-satir { font-size: 0.9rem; color: #555; margin-bottom: 5px; line-height: 1.4; }
        .analiz-bilgi-deger { font-weight: bold; color: #111; }
        .floating-pdf-container {
            position: fixed; bottom: 30px; right: 30px; z-index: 9999;
            background-color: #ffffff; padding: 15px; border-radius: 12px;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.2); border-top: 4px solid #1C3768; width: 250px;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. SAYFA DURUM YÖNETİMİ ---
if 'sayfa' not in st.session_state:
    st.session_state.sayfa = 'anasayfa'

def sayfa_degistir(sayfa_adi):
    st.session_state.sayfa = sayfa_adi

# --- 4. SABİT PARAMETRELER ---
DK_UCRETI = materials.DK_UCRETI
FIRE_ORANI = materials.FIRE_ORANI
KDV_ORANI = materials.KDV_ORANI

# --- 5. SIDEBAR (DÜZELTİLMİŞ FİYAT MANTIĞI İLE) ---
with st.sidebar:
    try:
        st.image("logo.png", use_column_width=True)
    except:
        st.markdown("<h1 style='text-align: center; color: #1C3768;'>ALAN LAZER</h1>", unsafe_allow_html=True)
    
    st.markdown("""<div style='text-align: center; margin-top: -10px; margin-bottom: 25px;'>
            <a href='https://www.alanlazer.com' target='_blank' 
               style='text-decoration: none; color: #1C3768; font-size: 22px; font-weight: 300;'>alanlazer.com</a>
        </div>""", unsafe_allow_html=True)
    st.markdown("---")
    
    # 1. Metal, Kalınlık ve Adet Seçimi
    metal = st.selectbox("Metal Türü", list(materials.VERİ.keys()))

    # FİYAT GÜNCELLEME MANTIĞI
    secilen_metalin_fiyati = float(materials.VARSAYILAN_FIYATLAR.get(metal, 29.0))

    if 'last_metal' not in st.session_state or st.session_state.last_metal != metal:
        st.session_state.kg_input_field = secilen_metalin_fiyati
        st.session_state.temp_kg_fiyat = secilen_metalin_fiyati
        st.session_state.last_metal = metal
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        kalinlik = st.selectbox("Kalınlık (mm)", materials.VERİ[metal]["kalinliklar"])
    with col_s2:
        adet = st.number_input("Adet", min_value=1, value=1, step=1)

    # 2. Plaka Seçenekleri
    if 0.8 <= kalinlik <= 1.5:
        plaka_secenekleri = {"100x200 cm": (1000, 2000), "150x300 cm": (1500, 3000)}
    else:
        plaka_secenekleri = {"100x200 cm": (1000, 2000), "150x300 cm": (1500, 3000), "150x600 cm": (1500, 6000)}

    secilen_plaka_adi = st.selectbox("Plaka Boyutu", list(plaka_secenekleri.keys()))

    # 3. Bilgi Kutuları
    hiz_tablosu = materials.VERİ[metal]["hizlar"]
    guncel_hiz = hiz_tablosu.get(kalinlik, 1000)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col_i1, col_i2 = st.columns(2)
    with col_i1:
        st.markdown(f"""<div style="background-color: #e7f3fe; padding: 10px; border-radius: 8px; border-left: 4px solid #2196F3; color: #0c5460; min-height: 70px;">
                <div style="font-size: 11px; font-weight: 600; opacity: 0.8;">Hız(mm/dk)</div>
                <div style="font-size: 17px; font-weight: bold;">{guncel_hiz}</div>
            </div>""", unsafe_allow_html=True)
    with col_i2:
        guncel_fiyat_gosterim = st.session_state.kg_input_field
        st.markdown(f"""<div style="background-color: #d4edda; padding: 10px; border-radius: 8px; border-left: 4px solid #28a745; color: #155724; min-height: 70px;">
                <div style="font-size: 11px; font-weight: 600; opacity: 0.8;">Birim(TL/kg)</div>
                <div style="font-size: 17px; font-weight: bold;">{guncel_fiyat_gosterim} TL</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

    # 4. Malzeme Kg Fiyatı
    kg_fiyati = st.number_input("Malzeme KG Fiyatı (TL)", min_value=0.0, step=1.0, format="%g", key="kg_input_field")
    st.session_state.temp_kg_fiyat = kg_fiyati

# --- 6. ANA PANEL İÇERİĞİ ---
st.title("AI DESTEKLİ PROFESYONEL ANALİZ")

# === DURUM A: ANASAYFA ===
if st.session_state.sayfa == 'anasayfa':
    st.markdown("### Lütfen yapmak istediğiniz işlem türünü seçiniz:")
    st.markdown("---")
    c1, c2, c3 = st.columns(3, gap="medium")
    box_style = "min-height: 220px; display: flex; flex-direction: column;"
    
    with c1:
        st.info("📸 **FOTOĞRAFTAN ANALİZ**")
        st.markdown(f"""<div style="{box_style}">
            <p>Fotoğraf veya eskiz görsellerini yükleyin. <b>AI görüntü işleme</b> işini yapsın.</p>
            <ul><li>JPG, PNG</li><li>Referans Ölçü ile Ölçekleme</li></ul>
        </div>""", unsafe_allow_html=True)
        if st.button("FOTOĞRAF YÜKLE", use_container_width=True, type="primary"):
            sayfa_degistir('foto_analiz')
            st.rerun()

    with c2:
        st.warning("📐 **TEKNİK ÇİZİM ANALİZİ (DXF)**")
        st.markdown(f"""<div style="{box_style}">
            <p>Vektörel çizim dosyanızı yükleyerek %100 hassas sonuç alın.</p>
            <ul><li>DXF Desteği</li><li>Otomatik Yerleşim</li></ul>
        </div>""", unsafe_allow_html=True)
        if st.button("ÇİZİM DOSYASI YÜKLE", use_container_width=True, type="primary"):
            sayfa_degistir('dxf_analiz')
            st.rerun()

    with c3:
        st.success("🛠 **HAZIR PARÇA OLUŞTUR**")
        st.markdown(f"""<div style="{box_style}">
            <p>Standart geometrik şekilleri (Kare, Flanş) manuel oluşturun.</p>
            <ul><li>Kare, Dikdörtgen, Daire</li><li>Delik Tanımlama</li></ul>
        </div>""", unsafe_allow_html=True)
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
        referans_olcu = st.number_input("Parçanın Yatay Uzunluğu (mm)", value=100.0, step=10.0, format="%g")
        hassasiyet = st.slider("Hassasiyet", 50, 255, 80, step=1)
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
            
            valid_contour_list = []
            if contours and hierarchy is not None:
                for i, cnt in enumerate(contours):
                    x_b, y_b, w_b, h_b = cv2.boundingRect(cnt)
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

                # Hesaplama Verilerini Hazırla
                kesim_m = (sum([cv2.arcLength(c, True) for c in valid_contour_list]) * oran) / 1000
                kontur_ad = len(valid_contour_list)
                alan_mm2 = cv2.contourArea(all_pts) * (oran**2)
                
                # MERKEZİ FONKSİYONU ÇAĞIR
                hesapla_ve_goster(kesim_m, kontur_ad, alan_mm2, gercek_genislik, gercek_yukseklik, display_img)
            else:
                 st.info("Lütfen bir görsel yükleyiniz veya hassasiyeti ayarlayınız.")

# === DURUM C: TEKNİK ÇİZİM ANALİZ ===
elif st.session_state.sayfa == 'dxf_analiz':
    if st.button("⬅️ Ana Menüye Dön"):
        sayfa_degistir('anasayfa')
        st.rerun()

    st.divider()
    c_dxf_ayar, c_dxf_sonuc = st.columns([1, 2])

    with c_dxf_ayar:
        st.subheader("Teknik Çizim Yükle")
        if not dxf_active:
            st.error("⚠️ Kütüphaneler eksik (ezdxf, matplotlib).")
        hassasiyet_dxf = st.slider("Hassasiyet", 50, 255, 100, step=1)
        uploaded_dxf = st.file_uploader("Dosya Seç (Sadece DXF)", type=['dxf'])

    with c_dxf_sonuc:
        if uploaded_dxf and dxf_active:
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp_file:
                    tmp_file.write(uploaded_dxf.getvalue())
                    tmp_path = tmp_file.name

                doc = ezdxf.readfile(tmp_path)
                msp = doc.modelspace()
                os.remove(tmp_path)

                # Render İşlemi (Matplotlib ile Görüntüye Çevirme)
                try:
                    bbox_cache = bbox.extents(msp)
                    w_real = bbox_cache.extmax.x - bbox_cache.extmin.x
                    h_real = bbox_cache.extmax.y - bbox_cache.extmin.y
                except:
                    w_real, h_real = 0, 0
                
                if w_real > 0 and h_real > 0:
                    fig = plt.figure(figsize=(10, 10), facecolor='#111827')
                    ax = fig.add_axes([0, 0, 1, 1])
                    ax.set_facecolor('#111827')
                    ctx = RenderContext(doc)
                    for layer in ctx.layers.values(): layer.color = '#FFFFFF' 
                    out = MatplotlibBackend(ax)
                    Frontend(ctx, out).draw_layout(msp, finalize=True)
                    ax.set_aspect('equal', 'datalim')
                    ax.axis('off')
                    fig.canvas.draw()
                    width, height = fig.canvas.get_width_height()
                    img_data = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8).reshape(height, width, 4)
                    plt.close(fig)
                    
                    dxf_img_bgr = cv2.cvtColor(img_data, cv2.COLOR_RGBA2BGR)
                    gray = cv2.cvtColor(dxf_img_bgr, cv2.COLOR_BGR2GRAY)
                    _, binary = cv2.threshold(gray, hassasiyet_dxf, 255, cv2.THRESH_BINARY)
                    contours, hierarchy = cv2.findContours(binary, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
                    
                    valid_cnts = [c for c in contours if cv2.contourArea(c) >= 5]
                    result_img = dxf_img_bgr.copy()
                    cv2.drawContours(result_img, valid_cnts, -1, (0, 255, 0), 2)
                    st.image(result_img, caption=f"DXF: {uploaded_dxf.name}", use_container_width=True)
                    
                    if valid_cnts:
                        all_pts = np.concatenate(valid_cnts)
                        x_p, y_p, w_p, h_p = cv2.boundingRect(all_pts)
                        scale_ratio = w_real / w_p
                        
                        toplam_piksel_yol = sum([cv2.arcLength(c, True) for c in valid_cnts])
                        kesim_m = (toplam_piksel_yol * scale_ratio) / 1000.0 
                        piercing_basi = len(valid_cnts)
                        
                        # Alan hesabı (Basitleştirilmiş: Bounding Box alanı)
                        # Gerçek nestingleme olmadan fire oranı ile yaklaşık alan
                        alan_mm2 = w_real * h_real 
                        
                        # MERKEZİ FONKSİYONU ÇAĞIR
                        hesapla_ve_goster(kesim_m, piercing_basi, alan_mm2, w_real, h_real, result_img)
                    else:
                        st.warning("Çizim algılanamadı.")
                else:
                    st.warning("Boş DXF dosyası.")
            except Exception as e:
                st.error(f"Hata: {e}")

# === DURUM D: HAZIR PARÇA ===
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
        
        # Geometri Oluşturma
        if sekil_tipi == "Kare / Dikdörtgen":
            genislik = st.number_input("Genişlik", value=100.0, step=10.0, format="%g")
            yukseklik = st.number_input("Yükseklik", value=100.0, step=10.0, format="%g")
            delik_sayisi = st.number_input("Delik Sayısı", value=0, step=1)
            delik_capi = st.number_input("Delik Çapı", value=10.0, format="%g")
            
            canvas = np.zeros((400, 600, 3), dtype="uint8") + 255
            max_dim = max(genislik, yukseklik)
            scale = 300 / max_dim 
            w_px, h_px = int(genislik * scale), int(yukseklik * scale)
            start_x, start_y = (600 - w_px) // 2, (400 - h_px) // 2
            
            cv2.rectangle(canvas, (start_x, start_y), (start_x + w_px, start_y + h_px), (0, 0, 0), 2)
            # (Delik çizim mantığı sadeleştirildi, görsel amaçlıdır)
            if delik_sayisi > 0:
                 cv2.circle(canvas, (300, 200), int(delik_capi*scale/2), (0,0,255), 2)
                 cv2.putText(canvas, f"{delik_sayisi} delik", (320, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,0), 2)
            
            # Hesaplama Verileri
            toplam_kesim_mm = 2 * (genislik + yukseklik) + delik_sayisi * (math.pi * delik_capi)
            net_alan_mm2 = (genislik * yukseklik) - delik_sayisi * (math.pi * (delik_capi/2)**2)
            piercing_sayisi = 1 + delik_sayisi
            w_real, h_real = genislik, yukseklik

        elif sekil_tipi == "Daire / Flanş":
            cap = st.number_input("Dış Çap", value=100.0, step=10.0, format="%g")
            delik_sayisi = st.number_input("İç Delik", value=1, step=1)
            delik_capi = st.number_input("Delik Çapı", value=50.0, format="%g")
            
            canvas = np.zeros((400, 400, 3), dtype="uint8") + 255
            cv2.circle(canvas, (200, 200), 140, (0,0,0), 2)
            if delik_sayisi > 0:
                cv2.circle(canvas, (200, 200), int((delik_capi/cap)*140), (0,0,255), 2)
            
            toplam_kesim_mm = math.pi * cap + delik_sayisi * (math.pi * delik_capi)
            net_alan_mm2 = math.pi * (cap/2)**2 - delik_sayisi * (math.pi * (delik_capi/2)**2)
            piercing_sayisi = 1 + delik_sayisi
            w_real, h_real = cap, cap

        canvas_rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
        canvas_bgr = cv2.cvtColor(canvas_rgb, cv2.COLOR_RGB2BGR) # PDF için BGR lazım

    with c_sonuc:
        st.image(canvas_rgb, caption=f"Önizleme: {w_real}x{h_real}mm", use_container_width=True)
        # MERKEZİ FONKSİYONU ÇAĞIR
        hesapla_ve_goster(toplam_kesim_mm/1000, piercing_sayisi, net_alan_mm2, w_real, h_real, canvas_bgr)
