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
        
        /* LANDING PAGE BIO KUTUSU (GÜNCELLENDİ: DİKEY ORTALAMA) */
        .landing-bio-box {
            background-color: #f8f9fa; 
            border-left: 4px solid #1C3768; 
            padding: 20px; 
            border-radius: 0 10px 10px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            color: #444;
            line-height: 1.6;
            font-size: 14px;
            min-height: 140px; /* Kutuya hacim kazandırır */
            display: flex;
            align-items: center; /* Dikey olarak tam ortalar */
            justify-content: flex-start; /* Yatayda sola yaslar */
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
        current_y_before_box = pdf.get_y()
        pdf.set_draw_color(28, 55, 104)
        pdf.set_line_width(0.5)
        pdf.rect(10, current_y_before_box, 190, 35) # Kutu çiziliyor
        
        pdf.set_y(current_y_before_box + 5)
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 10, "TEKLIF OZETI", ln=True, align="C")
        pdf.set_font("helvetica", "B", 11)
        pdf.set_text_color(28, 55, 104)
        pdf.cell(95, 10, f"TOPLAM (KDV HARIC):   {data_dict.get('fiyat_haric', '-')} TL", border=0, align="C")
        pdf.set_text_color(22, 101, 52)
        pdf.cell(95, 10, f"TOPLAM (KDV DAHIL):   {data_dict.get('fiyat_dahil', '-')} TL", border=0, ln=True, align="C")
        
        # İmleci kutunun altından temiz bir noktaya taşıyoruz
        pdf.set_y(current_y_before_box + 40)
        
        # --- PDF YASAL UYARI (AKILLI KONUMLANDIRMA) ---
        if pdf.get_y() < 245:
            pdf.set_y(-45)
        else:
            pdf.ln(5)

        pdf.set_font("helvetica", "B", 8)
        pdf.set_text_color(128, 0, 0) # Koyu Kırmızı
        pdf.cell(0, 5, "YASAL UYARI VE BILGILENDIRME:", ln=True)
        
        pdf.set_font("helvetica", "", 7)
        pdf.set_text_color(50, 50, 50) # Koyu Gri
        disclaimer_text = (
            "Bu belgedeki veriler, yuklenen cizimlerin algoritmik analizine dayanir ve ON BILGILENDIRME "
            "amacli olup RESMI TEKLIF niteligi tasimaz. Sirketimiz acisindan yasal baglayiciligi yoktur. "
            "Kesin fiyatlandirma, teknik inceleme ve stok kontrolu sonrasinda onaylanan resmi teklif formu "
            "ile gecerlilik kazanir. Veri girisi ve teknik aksakliklardan dogabilecek hatalardan sirketimiz sorumlu degildir."
        )
        pdf.multi_cell(0, 4, disclaimer_text)
        
        # Footer
        if pdf.get_y() < 280:
             pdf.set_y(-15)
        else:
             pdf.ln(2)

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
    
    # --- MINIMUM FIYAT MANTIGI ---
    ham_lazer_tutar = sure_dk * DK_UCRETI
    lazer_min_not = ""
    
    if ham_lazer_tutar < 250.0:
        lazer_tutar = 250.0
        lazer_min_not = "(Min. 250 TL)"
    else:
        lazer_tutar = ham_lazer_tutar
    # -----------------------------
    
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
                <span>Lazer İşç.:</span> <span style="font-weight:bold;">{round(lazer_tutar, 2)} TL <span style="font-size:11px; color:#d9534f; margin-left:5px;">{lazer_min_not}</span></span>
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

    # --- EKRAN İÇİN YASAL UYARI KUTUSU (Bullet Points) ---
    st.markdown("""
        <div style="background-color: #fff4f4; padding: 15px; border-radius: 10px; border: 1px solid #f5c6cb; margin-top: 20px; margin-bottom: 20px;">
            <h5 style="color: #721c24; margin-top: 0; font-size: 16px; margin-bottom: 10px;">⚠️ YASAL UYARI VE SORUMLULUK REDDİ</h5>
            <div style="color: #721c24; font-size: 13px; line-height: 1.4;">
                <ul style="margin-bottom: 0; padding-left: 20px;">
                    <li style="margin-bottom: 5px;">Bu panelde sunulan sonuçlar, yüklenen çizimlerin <b>algoritmik analizine</b> dayanır ve yalnızca <b>ön bilgilendirme</b> amaçlıdır.</li>
                    <li style="margin-bottom: 5px;">Burada belirtilen tutarlar <b>resmi bir teklif niteliği taşımaz</b> ve şirketimiz açısından yasal bir bağlayıcılığı yoktur.</li>
                    <li>Kesin fiyatlandırma; teknik inceleme, güncel stok ve hammadde maliyetleri kontrol edildikten sonra sunulacak <b>resmi teklif</b> ile geçerlilik kazanır.</li>
                </ul>
            </div>
        </div>
    """, unsafe_allow_html=True)

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
    # 1. Üst Boşluk (Azaltıldı)
    st.write("") 
    
    # Başlık (Yukarı çekildi: margin-top: -20px)
    st.markdown("<h1 style='text-align: center; color: #1C3768; margin-top: -20px;'>Profesyonel Lazer ve Büküm Maliyet Analizi</h1>", unsafe_allow_html=True)
    
    # --- İSTEDİĞİNİZ ÖZEL YAZIYI BURADAN DEĞİŞTİREBİLİRSİNİZ ---
    st.markdown("<h3 style='text-align: center; color: red;'>BURAYA İSTEDİĞİNİZ MESAJI YAZABİLİRSİNİZ</h3>", unsafe_allow_html=True)
    # -------------------------------------------------------------
    
    st.divider()
    
    # Bilgi Kartları
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="landing-card">
            <div class="landing-icon">📸</div>
            <div class="landing-title">1. Yükle & Çek</div>
            <div class="landing-text">Parçanın fotoğrafını çekin, hazır şablon çizimi yapın veya ekran görüntüsü/DXF yükleyin.</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="landing-card">
            <div class="landing-icon">⚙️</div>
            <div class="landing-title">2. Ayarları Yap (Sol Menü)</div>
            <div class="landing-text">Analize başlamadan önce <b>Sol Taraftaki Kayar Menüden</b> malzeme ve kalınlık seçin.</div>
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
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Başla Butonu
    c_btn1, c_btn2, c_btn3 = st.columns([1, 2, 1])
    with c_btn2:
        if st.button("ANALİZE BAŞLA", use_container_width=True, type="primary"):
            st.session_state.app_mode = 'app'
            st.rerun()

    # --- ALT BÖLÜM: Logo ve Link + Kurumsal Yazı (DÜZENLENDİ) ---
    st.write("<br>", unsafe_allow_html=True)
    st.divider()
    
    # 1 Birim Logo için, 3 Birim Yazı için (Alan açıldı)
    col_footer_l, col_footer_r = st.columns([1, 3], gap="large")
    
    with col_footer_l:
        # LOGO KISMI (SOLA YASLI)
        if os.path.exists("logo.png"):
            try:
                with open("logo.png", "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode()
                st.markdown(f"""
                    <div style="display: flex; justify-content: center; margin-top: 10px;">
                        <img src="data:image/png;base64,{encoded_string}" width="140" style="display: block;">
                    </div>
                """, unsafe_allow_html=True)
            except:
                st.markdown("<h3 style='text-align: center; color: #1C3768;'>ALAN LAZER</h3>", unsafe_allow_html=True)
        else:
            st.markdown("<h3 style='text-align: center; color: #1C3768;'>ALAN LAZER</h3>", unsafe_allow_html=True)
        
        # LINK
        st.markdown("""
            <div style='text-align: center; margin-top: 10px;'>
                <a href='https://www.alanlazer.com' target='_blank' 
                   style='text-decoration: none; color: #1C3768; font-size: 18px; font-weight: 300;'>alanlazer.com</a>
            </div>
        """, unsafe_allow_html=True)

    with col_footer_r:
        # KURUMSAL YAZI KISMI (DİKEY ORTALAMA UYGULANDI)
        st.markdown("""
            <div class="landing-bio-box">
                <div>
                    <b>Alan Lazer</b>, kökleri 1963 yılına dayanan bir aile işletmesi olarak lazer kesim ve abkant büküm alanında fason üretim hizmeti sunmaktadır. 
                    Farklı sektörlere yönelik parça üretimini, planlı termin ve teknik gereklilikler doğrultusunda gerçekleştirmeyi esas alır. 
                    Üretim süreçlerinde sürdürülebilirlik ve verimlilik birlikte gözetilir.
                </div>
            </div>
        """, unsafe_allow_html=True)

# ==========================================
# 4. UYGULAMA BAŞLATICI
# ==========================================
if st.session_state.app_mode == 'landing':
    landing_page()
else:
    main_app()
