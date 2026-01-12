import streamlit as st
from PIL import Image
import cv2
import numpy as np
import math
import tempfile
import os
import base64

# --- HARİCİ VERİ DOSYASINDAN OKUMA ---
import materials 

from fpdf import FPDF

# ==========================================
# 0. SAYFA KONFİGÜRASYONU
# ==========================================
try:
    fav_icon = Image.open("tarayici.png")
except:
    fav_icon = None 

st.set_page_config(page_title="Alan Lazer Teklif Paneli", layout="wide", page_icon=fav_icon)

# ==========================================
# 1. CSS VE STİL AYARLARI
# ==========================================
st.markdown("""
    <style>
        /* Genel Ayarlar */
        section[data-testid="stSidebar"] div.block-container { padding-top: 1rem; }
        div.stButton > button { min-height: 50px; }
        
        /* Analiz Kutuları */
        .analiz-bilgi-kutu {
            background-color: #f8f9fa; border-radius: 8px; padding: 12px;
            border-left: 5px solid #1c3768; margin-top: 10px;
        }
        .analiz-bilgi-satir { font-size: 0.9rem; color: #555; margin-bottom: 5px; line-height: 1.4; }
        .analiz-bilgi-deger { font-weight: bold; color: #111; }
        
        /* Floating Button (PDF) */
        .floating-pdf-container {
            position: fixed; bottom: 30px; right: 30px; z-index: 9999;
            background-color: #ffffff; padding: 15px; border-radius: 12px;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.2); border-top: 4px solid #1C3768; width: 250px;
        }
        
        /* SCROLLBAR GİZLEME */
        section[data-testid="stSidebar"] ::-webkit-scrollbar { display: none; }
        section[data-testid="stSidebar"] { -ms-overflow-style: none; scrollbar-width: none; }
        
        /* LANDING PAGE KARTLARI */
        .landing-card {
            background-color: #f8f9fa;
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            height: 100%;
            transition: transform 0.3s;
        }
        .landing-card:hover {
            transform: translateY(-5px);
            border: 1px solid #1C3768;
        }
        .landing-icon {
            font-size: 50px;
            margin-bottom: 15px;
        }
        .landing-title {
            font-weight: bold;
            color: #1C3768;
            margin-bottom: 10px;
            font-size: 18px;
        }
        .landing-text {
            color: #666;
            font-size: 14px;
        }

        @media only screen and (max_width: 600px) {
            .floating-pdf-container {
                width: 90% !important; left: 5% !important; right: 5% !important;
                bottom: 10px !important; padding: 10px !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. YARDIMCI FONKSİYONLAR
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
        pdf.cell(40, 8, "Bukum Sayisi:", border=0)
        pdf.cell(55, 8, f"{data_dict.get('bukum_adedi', '0')} adet", border=1)
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
        pdf.cell(40, 8, "Toplam Agirlik:", border=0)
        pdf.cell(45, 8, f"{data_dict.get('toplam_agirlik', '-')} kg", border=1, ln=True)
        pdf.ln(1)
        pdf.cell(40, 8, "Kontur (Patlatma):", border=0)
        pdf.cell(55, 8, f"{data_dict.get('kontur', '-')} ad", border=1)
        pdf.cell(10, 8, "", border=0)
        pdf.cell(40, 8, "Kesim Hizi:", border=0)
        pdf.cell(45, 8, f"{data_dict.get('hiz', '-')} mm/dk", border=1, ln=True)
        pdf.ln(10)
        
        # Maliyet Detayları
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 8, "  MALIYET DETAYLARI", ln=True, fill=True)
        pdf.ln(2)
        pdf.set_font("helvetica", "", 10)
        pdf.cell(100, 8, "Malzeme Bedeli:", border=0)
        pdf.cell(40, 8, f"{data_dict.get('malzeme_tutar', '-')} TL", border=0, align="R", ln=True)
        pdf.cell(100, 8, "Lazer Isciligi:", border=0)
        pdf.cell(40, 8, f"{data_dict.get('lazer_tutar', '-')} TL", border=0, align="R", ln=True)
        pdf.cell(100, 8, "Bukum Isciligi:", border=0)
        pdf.cell(40, 8, f"{data_dict.get('bukum_tutar', '-')} TL", border=0, align="R", ln=True)
        pdf.ln(5)

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

def hesapla_ve_goster(kesim_m, kontur_ad, alan_mm2, w_real, h_real, result_img_bgr, metal, kalinlik, adet, guncel_hiz, plaka_adi, bukum_adedi):
    DK_UCRETI = materials.DK_UCRETI
    FIRE_ORANI = materials.FIRE_ORANI
    KDV_ORANI = materials.KDV_ORANI
    
    kg_fiyat = st.session_state.get('kg_input_field', 0.0)
    bukum_baz_fiyat_manual = st.session_state.get('bukum_baz_input', 0.0)
    p_suresi = materials.PIERCING_SURELERI.get(kalinlik, 1.0)
    
    tek_agirlik = (alan_mm2 * kalinlik * materials.VERİ[metal]["ozkutle"] / 1e6)
    toplam_agirlik_fireli = tek_agirlik * adet * FIRE_ORANI
    limit_kontrol_agirligi = toplam_agirlik_fireli 

    sure_dk = (kesim_m * 1000 / guncel_hiz) * adet + (kontur_ad * adet * p_suresi / 60)
    
    malzeme_tutar = toplam_agirlik_fireli * kg_fiyat
    lazer_tutar = sure_dk * DK_UCRETI
    
    bukum_tutar = 0.0
    aktif_bukum_baz_fiyat = bukum_baz_fiyat_manual
    
    if bukum_adedi > 0:
        if limit_kontrol_agirligi > materials.BUKUM_TOPTAN_LIMIT_KG:
            aktif_bukum_baz_fiyat = materials.BUKUM_TOPTAN_FIYAT
        
        carpan = 1.5 ** (bukum_adedi - 1)
        bukum_tutar = limit_kontrol_agirligi * aktif_bukum_baz_fiyat * carpan

    toplam_fiyat = malzeme_tutar + lazer_tutar + bukum_tutar
    kdvli_fiyat = toplam_fiyat * KDV_ORANI

    st.markdown("### 📋 Teklif Özeti")
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.markdown(f"""<div class="analiz-bilgi-kutu">
            <div class="analiz-bilgi-satir">Ölçü: <span class="analiz-bilgi-deger">{round(w_real, 1)} x {round(h_real, 1)} mm</span></div>
            <div class="analiz-bilgi-satir">Toplam Ağırlık: <span class="analiz-bilgi-deger">{round(limit_kontrol_agirligi, 2)} kg</span></div>
            <div class="analiz-bilgi-satir">Kesim Süresi: <span class="analiz-bilgi-deger">{round(sure_dk, 2)} dk</span></div>
            <div class="analiz-bilgi-satir">Büküm Sayısı: <span class="analiz-bilgi-deger">{bukum_adedi} adet</span></div>
        </div>""", unsafe_allow_html=True)
        
    with c2:
        st.markdown(f"""<div class="analiz-bilgi-kutu">
            <div style="display:flex; justify-content:space-between; margin-bottom:4px; font-size:14px; color:#555;">
                <span>Malzeme:</span> <span style="font-weight:bold;">{round(malzeme_tutar, 2)} TL</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:4px; font-size:14px; color:#555;">
                <span>Lazer İşç.:</span> <span style="font-weight:bold;">{round(lazer_tutar, 2)} TL</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:8px; font-size:14px; color:#555; border-bottom:1px solid #ddd; padding-bottom:4px;">
                <span>Büküm İşç.:</span> <span style="font-weight:bold;">{round(bukum_tutar, 2)} TL</span>
            </div>
            <div style="font-size: 24px; font-weight: bold; color: #1C3768; margin-bottom: 5px; text-align:right;">
                {round(toplam_fiyat, 2)} TL <span style="font-size:12px; font-weight:normal;">(KDV Hariç)</span>
            </div>
            <div style="background-color: #dcfce7; color: #166534; padding: 8px; border-radius: 6px; font-weight: bold; font-size: 18px; border-left: 5px solid #166534; text-align:center;">
                KDV DAHİL: {round(kdvli_fiyat, 2)} TL
            </div>
        </div>""", unsafe_allow_html=True)

    pdf_bytes = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_img:
            cv2.imwrite(tmp_img.name, result_img_bgr)
            pdf_data = {
                "metal": metal, "kalinlik": kalinlik, "adet": adet, 
                "plaka": plaka_adi, "olcu": f"{round(w_real,1)}x{round(h_real,1)}", 
                "sure": round(sure_dk,2), "kontur": kontur_ad * adet, 
                "hiz": guncel_hiz, 
                "malzeme_tutar": round(malzeme_tutar,2),
                "lazer_tutar": round(lazer_tutar,2),
                "bukum_tutar": round(bukum_tutar,2),
                "bukum_adedi": bukum_adedi,
                "toplam_agirlik": round(limit_kontrol_agirligi, 2),
                "fiyat_haric": round(toplam_fiyat,2), 
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

# ==========================================
# 3. SAYFA YÖNETİMİ VE ANA AKIŞ
# ==========================================

# Oturum Durumu Başlatma
if 'app_mode' not in st.session_state:
    st.session_state.app_mode = 'landing'

if 'sayfa' not in st.session_state: st.session_state.sayfa = 'anasayfa'
def sayfa_degistir(sayfa_adi): st.session_state.sayfa = sayfa_adi

def landing_page():
    # 1. Üst Boşluk
    st.write("")
    st.write("")

    # 2. LOGOYU TAM ORTALAMAK İÇİN ÖZEL YAPI
    col_left, col_center, col_right = st.columns([1, 1, 1]) 
    
    with col_center:
        logo_html = ""
        if os.path.exists("logo.png"):
            try:
                with open("logo.png", "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode()
                logo_html = f"""
                    <div style="display: flex; justify-content: center; margin-bottom: 5px;">
                        <img src="data:image/png;base64,{encoded_string}" width="200" style="display: block;">
                    </div>
                """
            except:
                logo_html = "<h1 style='text-align: center; color: #1C3768;'>ALAN LAZER</h1>"
        else:
            logo_html = "<h1 style='text-align: center; color: #1C3768;'>ALAN LAZER</h1>"
            
        st.markdown(logo_html, unsafe_allow_html=True)
        
        st.markdown("""
            <div style='text-align: center; margin-bottom: 25px;'>
                <a href='https://www.alanlazer.com' target='_blank' 
                   style='text-decoration: none; color: #1C3768; font-size: 22px; font-weight: 300;'>alanlazer.com</a>
            </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    st.markdown("<h1 style='text-align: center; color: #1C3768; margin-bottom: 40px;'>Profesyonel Lazer ve Büküm Maliyet Analizi</h1>", unsafe_allow_html=True)
    
    # 4. Bilgi Kartları
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="landing-card">
            <div class="landing-icon">📸</div>
            <div class="landing-title">1. Yükle & Çek</div>
            <div class="landing-text">Parçanın fotoğrafını çekin, dosyasını yükleyin veya DXF çizimini ekleyin.</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        # REVİZE: Kullanıcıyı Sol Menüye Yönlendiren Metin
        st.markdown("""
        <div class="landing-card">
            <div class="landing-icon">⚙️</div>
            <div class="landing-title">2. Ayarları Yap (Sol Menü)</div>
            <div class="landing-text">Analize başlamadan önce <b>sol taraftaki (mobilde >) açılır menüden</b> malzeme ve kalınlık seçin.</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
        <div class="landing-card">
            <div class="landing-icon">📄</div>
            <div class="landing-title">3. Sonuç Al</div>
            <div class="landing-text">Saniyeler içinde detaylı maliyet analizini ve PDF teklif formunu indirin.</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    c_btn1, c_btn2, c_btn3 = st.columns([1, 2, 1])
    with c_btn2:
        if st.button("ANALİZE BAŞLA", use_container_width=True, type="primary"):
            st.session_state.app_mode = 'app'
            st.rerun()

def main_app():
    # --- SIDEBAR (SADECE UYGULAMA MODUNDA GÖRÜNÜR) ---
    with st.sidebar:
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

        metal = st.selectbox("Metal Türü", list(materials.VERİ.keys()))

        secilen_metalin_fiyati = float(materials.VARSAYILAN_FIYATLAR.get(metal, 29.0))
        if 'last_metal' not in st.session_state or st.session_state.last_metal != metal:
            st.session_state.kg_input_field = secilen_metalin_fiyati
            st.session_state.last_metal = metal

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            kalinlik = st.selectbox("Kalınlık (mm)", materials.VERİ[metal]["kalinliklar"])
        with col_s2:
            adet = st.number_input("Adet", min_value=1, value=1, step=1)
        
        bukum_adedi = st.number_input("Büküm Sayısı (Parça Başı)", min_value=0, value=0, step=1)

        if 0.8 <= kalinlik <= 1.5:
            plaka_secenekleri = {"100x200 cm": (1000, 2000), "150x300 cm": (1500, 3000)}
        else:
            plaka_secenekleri = {"100x200 cm": (1000, 2000), "150x300 cm": (1500, 3000), "150x600 cm": (1500, 6000)}
        secilen_plaka_adi = st.selectbox("Plaka Boyutu", list(plaka_secenekleri.keys()))

        hiz_tablosu = materials.VERİ[metal]["hizlar"]
        guncel_hiz = hiz_tablosu.get(kalinlik, 1000)
        guncel_fiyat_gosterim = st.session_state.get('kg_input_field', 0)
        
        default_bukum_baz = materials.BUKUM_F_STANDART
        if 0.8 <= kalinlik < 2.0: default_bukum_baz = materials.BUKUM_F_0_2_MM
        elif 2.0 <= kalinlik < 5.0: default_bukum_baz = materials.BUKUM_F_2_5_MM
        elif 5.0 <= kalinlik < 6.0: default_bukum_baz = materials.BUKUM_F_5_6_MM
        elif 6.0 <= kalinlik <= 10.0: default_bukum_baz = materials.BUKUM_F_6_10_MM

        if 'last_kalinlik' not in st.session_state or st.session_state.last_kalinlik != kalinlik:
            st.session_state.bukum_baz_input = default_bukum_baz
            st.session_state.last_kalinlik = kalinlik
        
        guncel_bukum_baz = st.session_state.get('bukum_baz_input', default_bukum_baz)

        st.markdown("<br>", unsafe_allow_html=True)
        col_i1, col_i2 = st.columns(2)
        
        with col_i1:
            st.markdown(f"""
                <div style="background-color: #e7f3fe; padding: 10px; border-radius: 5px; border-left: 4px solid #2196F3; color: #0c5460; box-shadow: 0px 2px 4px rgba(0,0,0,0.1);">
                    <div style="font-size: 10px; font-weight: 700; text-transform: uppercase; margin-bottom: 2px;">Hız (mm/dk)</div>
                    <div style="font-size: 18px; font-weight: 800;">{guncel_hiz}</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col_i2:
            st.markdown(f"""
                <div style="background-color: #d4edda; padding: 10px; border-radius: 5px; border-left: 4px solid #28a745; color: #155724; box-shadow: 0px 2px 4px rgba(0,0,0,0.1);">
                    <div style="font-size: 10px; font-weight: 700; text-transform: uppercase; margin-bottom: 2px;">Birim (TL/kg)</div>
                    <div style="font-size: 18px; font-weight: 800;">{guncel_fiyat_gosterim} TL</div>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown(f"""
            <div style="background-color: #fff3cd; padding: 10px; border-radius: 5px; border-left: 4px solid #ffc107; color: #856404; box-shadow: 0px 2px 4px rgba(0,0,0,0.1); margin-top:10px;">
                <div style="font-size: 10px; font-weight: 700; text-transform: uppercase; margin-bottom: 2px;">Büküm Baz (TL/kg)</div>
                <div style="font-size: 18px; font-weight: 800;">{guncel_bukum_baz} TL</div>
                <div style="font-size: 9px; opacity:0.8;">({int(materials.BUKUM_TOPTAN_LIMIT_KG)}kg üstü: {int(materials.BUKUM_TOPTAN_FIYAT)} TL)</div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # REVİZE: Başlık Değiştirildi
        with st.expander("Birim Fiyatlar"):
            st.write("Malzeme Fiyatı:")
            st.number_input("Manuel Sac Fiyat (TL)", min_value=0.0, step=1.0, format="%g", key="kg_input_field")
            st.markdown("---")
            st.write("Büküm Baz Fiyatı:")
            st.number_input("Manuel Büküm Fiyat (TL)", min_value=0.0, step=1.0, format="%g", key="bukum_baz_input")

    # --- ANA EKRAN ---
    st.title("AI DESTEKLİ PROFESYONEL ANALİZ")

    if st.session_state.sayfa == 'anasayfa':
        st.markdown("### Lütfen yapmak istediğiniz işlem türünü seçiniz:")
        st.divider()
        
        tab1, tab2, tab3 = st.tabs(["📸 FOTOĞRAF", "📐 DXF ÇİZİM", "🛠 MANUEL"])
        
        with tab1:
            st.info("Parçanın fotoğrafını çekin veya yükleyin (Fotoğraf Çek / Galeri).")
            # SADECE FILE UPLOADER
            upl_val = st.file_uploader("Görsel Yükle", type=['jpg', 'png', 'jpeg'])
            
            if upl_val:
                st.session_state.gecici_gorsel = upl_val
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
                                      metal, kalinlik, adet, guncel_hiz, secilen_plaka_adi, bukum_adedi)
                else:
                    st.warning("Kesim yolu bulunamadı.")
            else:
                st.error("Görsel okunamadı.")
        else:
            st.info("Görsel yüklenmedi.")

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
                                          metal, kalinlik, adet, guncel_hiz, secilen_plaka_adi, bukum_adedi)
                else:
                    st.warning("DXF boş.")
            except Exception as e:
                st.error(f"Hata: {e}")

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
                              metal, kalinlik, adet, guncel_hiz, secilen_plaka_adi, bukum_adedi)

# ==========================================
# 4. UYGULAMA BAŞLATICI
# ==========================================
if st.session_state.app_mode == 'landing':
    landing_page()
else:
    main_app()
