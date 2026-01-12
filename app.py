import streamlit as st
from PIL import Image
import cv2
import numpy as np
import math
import tempfile
import os

# --- HARİCİ VERİ DOSYASINDAN OKUMA ---
import materials 

from fpdf import FPDF

# ==========================================
# 1. YARDIMCI FONKSİYONLAR (DEĞİŞTİRİLMEDİ)
# ==========================================

def generate_pdf(data_dict, image_path=None):
    try:
        pdf = FPDF()
        pdf.add_page()
        # Header
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, "ALAN LAZER TEKLIF FORMU", ln=True, align="C")
        pdf.set_font("helvetica", "", 10)
        pdf.cell(0, 10, "www.alanlazer.com", ln=True, align="C")
        pdf.line(10, 30, 200, 30)
        pdf.ln(5)
        # Görsel
        if image_path and os.path.exists(image_path):
            pdf.image(image_path, x=60, y=35, w=90)
            pdf.ln(95)
        else:
            pdf.ln(20)
        # Malzeme
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
        # Teknik
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
        # Fiyat
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
        # Footer
        pdf.set_y(-30)
        pdf.set_text_color(100, 100, 100)
        pdf.set_font("helvetica", "I", 8)
        pdf.cell(0, 5, "Bu belge sistem tarafindan otomatik olarak olusturulmustur.", ln=True, align="C")
        return bytes(pdf.output())
    except Exception as e:
        return str(e).encode()

def hesapla_ve_goster(kesim_m, kontur_ad, alan_mm2, w_real, h_real, result_img_bgr, metal, kalinlik, adet, guncel_hiz, plaka_adi):
    # Sabitler
    DK_UCRETI = materials.DK_UCRETI
    FIRE_ORANI = materials.FIRE_ORANI
    KDV_ORANI = materials.KDV_ORANI
    
    kg_fiyat = st.session_state.get('kg_input_field', 0.0)
    p_suresi = materials.PIERCING_SURELERI.get(kalinlik, 1.0)
    
    # Hesaplama
    sure_dk = (kesim_m * 1000 / guncel_hiz) * adet + (kontur_ad * adet * p_suresi / 60)
    agirlik = (alan_mm2 * kalinlik * materials.VERİ[metal]["ozkutle"] / 1e6) * FIRE_ORANI
    fiyat = (sure_dk * DK_UCRETI) + (agirlik * adet * kg_fiyat)
    kdvli_fiyat = fiyat * KDV_ORANI

    # Gösterim
    st.markdown("### 📋 Teklif Özeti")
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown(f"""<div class="analiz-bilgi-kutu">
            <div class="analiz-bilgi-satir">Ölçü: <span class="analiz-bilgi-deger">{round(w_real, 1)} x {round(h_real, 1)} mm</span></div>
            <div class="analiz-bilgi-satir">Süre: <span class="analiz-bilgi-deger">{round(sure_dk, 2)} dk</span></div>
            <div class="analiz-bilgi-satir">⚙️ Kontur (Piercing): <span class="analiz-bilgi-deger">{kontur_ad * adet} ad</span></div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="analiz-bilgi-kutu">
            <div class="analiz-bilgi-satir" style="color: #31333F; font-weight: 600; text-transform: uppercase;">KDV HARİÇ</div>
            <div style="font-size: 28px; font-weight: bold; color: #1C3768; margin-bottom: 8px;">{round(fiyat, 2)} TL</div>
            <div style="background-color: #dcfce7; color: #166534; padding: 10px; border-radius: 6px; font-weight: bold; font-size: 20px; border-left: 5px solid #166534;">
                KDV DAHİL: {round(kdvli_fiyat, 2)} TL
            </div>
        </div>""", unsafe_allow_html=True)

    # PDF
    pdf_bytes = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_img:
            cv2.imwrite(tmp_img.name, result_img_bgr)
            pdf_data = {
                "metal": metal, "kalinlik": kalinlik, "adet": adet, 
                "plaka": plaka_adi, "olcu": f"{round(w_real,1)}x{round(h_real,1)}", 
                "sure": round(sure_dk,2), "kontur": kontur_ad * adet, 
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

# ==========================================
# 2. AYARLAR VE SAYFA YAPISI
# ==========================================
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

try:
    fav_icon = Image.open("tarayici.png")
except:
    fav_icon = None 

st.set_page_config(page_title="Alan Lazer Teklif Paneli", layout="wide", page_icon=fav_icon)

st.markdown("""
    <style>
        section[data-testid="stSidebar"] div.block-container { padding-top: 1rem; }
        div.stButton > button { min-height: 50px; }
        .analiz-bilgi-kutu {
            background-color: #f8f9fa; border-radius: 8px; padding: 12px;
            border-left: 5px solid #1c3768; margin-top: 10px;
        }
        .analiz-bilgi-satir { font-size: 0.9rem; color: #555; margin-bottom: 5px; line-height: 1.4; }
        .analiz-bilgi-deger { font-weight: bold; color: #111; }
        
        /* Floating Button */
        .floating-pdf-container {
            position: fixed; bottom: 30px; right: 30px; z-index: 9999;
            background-color: #ffffff; padding: 15px; border-radius: 12px;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.2); border-top: 4px solid #1C3768; width: 250px;
        }
        @media only screen and (max_width: 600px) {
            .floating-pdf-container {
                width: 90% !important; left: 5% !important; right: 5% !important;
                bottom: 10px !important; padding: 10px !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

if 'sayfa' not in st.session_state: st.session_state.sayfa = 'anasayfa'
def sayfa_degistir(sayfa_adi): st.session_state.sayfa = sayfa_adi

# ==========================================
# 3. SIDEBAR (TAMAMEN ESKİ HALİNE DÖNDÜ)
# ==========================================
with st.sidebar:
    # A) LOGO VE LİNK
    try:
        st.image("logo.png", use_column_width=True)
    except:
        st.markdown("<h2 style='text-align: center; color: #1C3768;'>ALAN LAZER</h2>", unsafe_allow_html=True)
    
    st.markdown("""
        <div style='text-align: center; margin-top: -10px; margin-bottom: 25px;'>
            <a href='https://www.alanlazer.com' target='_blank' 
               style='text-decoration: none; color: #1C3768; font-size: 20px; font-weight: 300;'>alanlazer.com</a>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    # B) SEÇİM ARAÇLARI (SOL TARAFA SABİTLENDİ)
    metal = st.selectbox("Metal Türü", list(materials.VERİ.keys()))

    # Fiyat Başlatma/Güncelleme Mantığı
    secilen_metalin_fiyati = float(materials.VARSAYILAN_FIYATLAR.get(metal, 29.0))
    if 'last_metal' not in st.session_state or st.session_state.last_metal != metal:
        st.session_state.kg_input_field = secilen_metalin_fiyati
        st.session_state.last_metal = metal

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        kalinlik = st.selectbox("Kalınlık (mm)", materials.VERİ[metal]["kalinliklar"])
    with col_s2:
        adet = st.number_input("Adet", min_value=1, value=1, step=1)
    
    # Plaka Seçimi
    if 0.8 <= kalinlik <= 1.5:
        plaka_secenekleri = {"100x200 cm": (1000, 2000), "150x300 cm": (1500, 3000)}
    else:
        plaka_secenekleri = {"100x200 cm": (1000, 2000), "150x300 cm": (1500, 3000), "150x600 cm": (1500, 6000)}
    secilen_plaka_adi = st.selectbox("Plaka Boyutu", list(plaka_secenekleri.keys()))

    # C) BİLGİ KUTULARI (SOL TARAFA SABİTLENDİ)
    hiz_tablosu = materials.VERİ[metal]["hizlar"]
    guncel_hiz = hiz_tablosu.get(kalinlik, 1000)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col_i1, col_i2 = st.columns(2)
    with col_i1:
        st.markdown(f"""
            <div style="background-color: #e7f3fe; padding: 10px; border-radius: 8px; border-left: 4px solid #2196F3; color: #0c5460; min-height: 80px;">
                <div style="font-size: 10px; font-weight: 600; opacity: 0.8;">Hız(mm/dk)</div>
                <div style="font-size: 16px; font-weight: bold;">{guncel_hiz}</div>
            </div>
        """, unsafe_allow_html=True)
    with col_i2:
        guncel_fiyat_gosterim = st.session_state.get('kg_input_field', 0)
        st.markdown(f"""
            <div style="background-color: #d4edda; padding: 10px; border-radius: 8px; border-left: 4px solid #28a745; color: #155724; min-height: 80px;">
                <div style="font-size: 10px; font-weight: 600; opacity: 0.8;">Birim(TL/kg)</div>
                <div style="font-size: 16px; font-weight: bold;">{guncel_fiyat_gosterim} TL</div>
            </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)

    # D) YÖNETİCİ AYARI (GECİKME DÜZELTİLDİ - DİREKT KEY BAĞLANTISI)
    with st.expander("Yönetici Ayarı (Birim Fiyat)"):
         st.number_input(
             "Manuel Fiyat (TL)", 
             min_value=0.0, 
             step=1.0, 
             format="%g", 
             key="kg_input_field" 
         )

# ==========================================
# 4. ANA PANEL (İÇERİK)
# ==========================================

# --- ÜST BAŞLIK (MOBİLDE LOGO GÖRÜNMESİ İÇİN) ---
# Sidebar masaüstünde iyidir ama mobilde gizlenir.
# Bu başlık, mobilden girenlerin markayı görmesini sağlar.
col_main_logo, col_main_text = st.columns([1, 5])
with col_main_logo:
    try:
        st.image("logo.png", width=80)
    except:
        pass
with col_main_text:
    st.markdown("<h2 style='margin-top: -10px; color:#1C3768;'>ALAN LAZER</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:grey; font-size:14px; margin-top:-15px;'>AI Destekli Profesyonel Analiz</p>", unsafe_allow_html=True)

st.divider()

# --- SAYFA İÇERİKLERİ ---

if st.session_state.sayfa == 'anasayfa':
    st.markdown("### Lütfen yapmak istediğiniz işlem türünü seçiniz:")
    
    # Sekmeler Ana Ekranda (Eski tasarım mantığı)
    tab1, tab2, tab3 = st.tabs(["📸 FOTOĞRAF", "📐 DXF ÇİZİM", "🛠 MANUEL"])
    
    with tab1:
        st.info("Parçanın fotoğrafını çekin veya yükleyin.")
        c_cam, c_upl = st.columns(2)
        with c_cam:
            cam_val = st.camera_input("Fotoğraf Çek")
        with c_upl:
            upl_val = st.file_uploader("Galeriden Seç", type=['jpg', 'png', 'jpeg'])
        
        if cam_val or upl_val:
            st.session_state.gecici_gorsel = cam_val if cam_val else upl_val
            sayfa_degistir('foto_analiz')
            st.rerun()

    with tab2:
        st.warning("Teknik çizim dosyasını yükleyin.")
        dxf_val = st.file_uploader("DXF Yükle", type=['dxf'])
        if dxf_val:
            st.session_state.gecici_dxf = dxf_val
            sayfa_degistir('dxf_analiz')
            st.rerun()

    with tab3:
        st.success("Çiziminiz yoksa standart şekiller oluşturun.")
        if st.button("PARÇA OLUŞTURUCU BAŞLAT", use_container_width=True, type="primary"):
            sayfa_degistir('hazir_parca')
            st.rerun()

# --- FOTOĞRAF ANALİZ ---
elif st.session_state.sayfa == 'foto_analiz':
    if st.button("⬅️ Geri Dön", use_container_width=True):
        sayfa_degistir('anasayfa')
        st.rerun()
    
    st.subheader("📸 Görsel Analizi")
    with st.expander("Görüntü Ayarları", expanded=True):
        col_fa1, col_fa2 = st.columns(2)
        with col_fa1:
            referans_olcu = st.number_input("Parça Yatay Uzunluğu (mm)", value=100.0, step=10.0, format="%g")
        with col_fa2:
            hassasiyet = st.slider("Hassasiyet", 50, 255, 80, step=1)

    if 'gecici_gorsel' in st.session_state and st.session_state.gecici_gorsel:
        file_bytes = np.asarray(bytearray(st.session_state.gecici_gorsel.read()), dtype=np.uint8)
        st.session_state.gecici_gorsel.seek(0)
        original_img = cv2.imdecode(file_bytes, 1)
        
        if original_img is not None:
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
                _, _, w_px, h_px = cv2.boundingRect(all_pts)
                oran = referans_olcu / w_px
                gercek_genislik = w_px * oran
                gercek_yukseklik = h_px * oran
                
                display_img = original_img.copy()
                cv2.drawContours(display_img, valid_contour_list, -1, (0, 255, 0), 2)
                st.image(cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB), caption="Analiz", use_container_width=True)
                
                kesim_m = (sum([cv2.arcLength(c, True) for c in valid_contour_list]) * oran) / 1000
                kontur_ad = len(valid_contour_list)
                alan_mm2 = cv2.contourArea(all_pts) * (oran**2)
                
                hesapla_ve_goster(kesim_m, kontur_ad, alan_mm2, gercek_genislik, gercek_yukseklik, display_img,
                                  metal, kalinlik, adet, guncel_hiz, secilen_plaka_adi)
            else:
                st.warning("Kesim yolu bulunamadı.")
        else:
            st.error("Görsel okunamadı.")
    else:
        st.info("Görsel yüklenmedi.")

# --- DXF ANALİZ ---
elif st.session_state.sayfa == 'dxf_analiz':
    if st.button("⬅️ Geri Dön", use_container_width=True):
        sayfa_degistir('anasayfa')
        st.rerun()

    st.subheader("📐 DXF Analizi")
    if 'gecici_dxf' in st.session_state and st.session_state.gecici_dxf and dxf_active:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp_file:
                tmp_file.write(st.session_state.gecici_dxf.getvalue())
                tmp_path = tmp_file.name
            st.session_state.gecici_dxf.seek(0)
            doc = ezdxf.readfile(tmp_path)
            msp = doc.modelspace()
            os.remove(tmp_path)
            
            try:
                bbox_cache = bbox.extents(msp)
                w_real = bbox_cache.extmax.x - bbox_cache.extmin.x
                h_real = bbox_cache.extmax.y - bbox_cache.extmin.y
            except:
                w_real, h_real = 0, 0
            
            if w_real > 0:
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
                _, binary = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
                contours, _ = cv2.findContours(binary, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
                valid_cnts = [c for c in contours if cv2.contourArea(c) >= 5]
                
                result_img = dxf_img_bgr.copy()
                cv2.drawContours(result_img, valid_cnts, -1, (0, 255, 0), 2)
                st.image(result_img, caption="DXF Önizleme", use_container_width=True)
                
                if valid_cnts:
                    toplam_piksel_yol = sum([cv2.arcLength(c, True) for c in valid_cnts])
                    _, _, w_p, _ = cv2.boundingRect(np.concatenate(valid_cnts))
                    scale_ratio = w_real / w_p
                    kesim_m = (toplam_piksel_yol * scale_ratio) / 1000.0
                    piercing_basi = len(valid_cnts)
                    alan_mm2 = w_real * h_real
                    
                    hesapla_ve_goster(kesim_m, piercing_basi, alan_mm2, w_real, h_real, result_img,
                                      metal, kalinlik, adet, guncel_hiz, secilen_plaka_adi)
            else:
                st.warning("DXF boş.")
        except Exception as e:
            st.error(f"Hata: {e}")

# --- HAZIR PARÇA ---
elif st.session_state.sayfa == 'hazir_parca':
    if st.button("⬅️ Geri Dön", use_container_width=True):
        sayfa_degistir('anasayfa')
        st.rerun()

    st.subheader("🛠 Parça Oluşturucu")
    col_hz1, col_hz2 = st.columns([1, 2])
    with col_hz1:
        sekil_tipi = st.radio("Tip", ["Kare / Dikdörtgen", "Daire / Flanş"])
        if sekil_tipi == "Kare / Dikdörtgen":
            genislik = st.number_input("Genişlik", value=100.0)
            yukseklik = st.number_input("Yükseklik", value=100.0)
            delik_sayisi = st.number_input("Delik Sayısı", value=0)
            delik_capi = st.number_input("Delik Çapı", value=10.0)
            canvas = np.zeros((400, 600, 3), dtype="uint8") + 255
            max_dim = max(genislik, yukseklik)
            scale = 300 / max_dim
            w_px, h_px = int(genislik * scale), int(yukseklik * scale)
            start_x, start_y = (600 - w_px) // 2, (400 - h_px) // 2
            cv2.rectangle(canvas, (start_x, start_y), (start_x + w_px, start_y + h_px), (0,0,0), 2)
            if delik_sayisi > 0:
                cv2.circle(canvas, (300, 200), int(delik_capi*scale/2), (0,0,255), 2)
            toplam_kesim_mm = 2 * (genislik + yukseklik) + delik_sayisi * (math.pi * delik_capi)
            net_alan_mm2 = (genislik * yukseklik) - delik_sayisi * (math.pi * (delik_capi/2)**2)
            piercing = 1 + delik_sayisi
            w_r, h_r = genislik, yukseklik
        else:
            cap = st.number_input("Dış Çap", value=100.0)
            delik_sayisi = st.number_input("İç Delik", value=1)
            delik_capi = st.number_input("Delik Çapı", value=50.0)
            canvas = np.zeros((400, 400, 3), dtype="uint8") + 255
            cv2.circle(canvas, (200, 200), 140, (0,0,0), 2)
            if delik_sayisi > 0:
                cv2.circle(canvas, (200, 200), int((delik_capi/cap)*140), (0,0,255), 2)
            toplam_kesim_mm = math.pi * cap + delik_sayisi * (math.pi * delik_capi)
            net_alan_mm2 = math.pi * (cap/2)**2 - delik_sayisi * (math.pi * (delik_capi/2)**2)
            piercing = 1 + delik_sayisi
            w_r, h_r = cap, cap

    with col_hz2:
        canvas_rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
        st.image(canvas_rgb, caption=f"Önizleme: {w_r}x{h_r}mm", use_container_width=True)
        canvas_bgr = cv2.cvtColor(canvas_rgb, cv2.COLOR_RGB2BGR)
        hesapla_ve_goster(toplam_kesim_mm/1000, piercing, net_alan_mm2, w_r, h_r, canvas_bgr,
                          metal, kalinlik, adet, guncel_hiz, secilen_plaka_adi)
