import streamlit as st
from PIL import Image
import cv2
import numpy as np
import math
import tempfile
import os
import io
from fpdf import FPDF
import materials  # materials.py dosyanızın aynı klasörde olduğundan emin olun

# --- PDF OLUŞTURMA FONKSİYONU ---
def generate_pdf(data_dict):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, "ALAN LAZER TEKLIF FORMU", ln=True, align="C")
        pdf.set_font("helvetica", "", 10)
        pdf.cell(0, 10, "www.alanlazer.com", ln=True, align="C")
        pdf.line(10, 30, 200, 30)
        pdf.ln(10)
        
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 10, "Analiz Detaylari", ln=True)
        pdf.set_font("helvetica", "", 10)
        pdf.cell(95, 8, f"Metal Turu: {data_dict.get('metal', '-')}", border=1)
        pdf.cell(95, 8, f"Kalinlik: {data_dict.get('kalinlik', '-')} mm", border=1, ln=True)
        pdf.cell(95, 8, f"Adet: {data_dict.get('adet', '-')}", border=1)
        pdf.cell(95, 8, f"Plaka Boyutu: {data_dict.get('plaka', '-')}", border=1, ln=True)
        pdf.ln(5)
        
        pdf.cell(95, 8, f"Olcu: {data_dict.get('olcu', '-')}", border=1)
        pdf.cell(95, 8, f"Sure: {data_dict.get('sure', '-')} dk", border=1, ln=True)
        pdf.cell(95, 8, f"Kontur: {data_dict.get('kontur', '-')} ad", border=1)
        pdf.cell(95, 8, f"Hiz: {data_dict.get('hiz', '-')} mm/dk", border=1, ln=True)
        pdf.ln(5)
        
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 10, "Fiyatlandirma", ln=True)
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(95, 10, "TOPLAM (KDV HARIC):", border=1)
        pdf.set_text_color(28, 55, 104)
        pdf.cell(95, 10, f"{data_dict.get('fiyat_haric', '-')} TL", border=1, ln=True, align="R")
        pdf.set_text_color(22, 101, 52)
        pdf.cell(95, 10, "TOPLAM (KDV DAHIL):", border=1)
        pdf.cell(95, 10, f"{data_dict.get('fiyat_dahil', '-')} TL", border=1, ln=True, align="R")
        
        return bytes(pdf.output())
    except Exception as e:
        return str(e)

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

st.set_page_config(page_title="Alan Lazer Teklif Paneli", layout="wide")

# --- CSS STİLLERİ ---
st.markdown("""
    <style>
        .analiz-bilgi-kutu {
            background-color: #f8f9fa; border-radius: 8px; padding: 12px;
            border-left: 5px solid #1c3768; margin-top: 10px;
        }
        .analiz-bilgi-satir { font-size: 0.9rem; color: #555; margin-bottom: 5px; }
        .analiz-bilgi-deger { font-weight: bold; color: #111; }
        .floating-pdf-container {
            position: fixed; bottom: 30px; right: 30px; z-index: 9999;
            background-color: #ffffff; padding: 15px; border-radius: 12px;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.2); border-top: 4px solid #1C3768; width: 250px;
        }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
if 'sayfa' not in st.session_state: st.session_state.sayfa = 'anasayfa'
with st.sidebar:
    try:
        st.image("logo.png", use_column_width=True)
    except:
        st.markdown("<h1 style='text-align: center; color: #1C3768;'>ALAN LAZER</h1>", unsafe_allow_html=True)
    
    st.markdown("<div style='text-align: center; margin-bottom: 25px;'><a href='https://www.alanlazer.com' target='_blank' style='text-decoration: none; color: #1C3768;'>alanlazer.com</a></div>", unsafe_allow_html=True)
    st.markdown("---")
    
    metal = st.selectbox("Metal Türü", list(materials.VERİ.keys()))
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        kalinlik = st.selectbox("Kalınlık (mm)", materials.VERİ[metal]["kalinliklar"])
    with col_s2:
        adet = st.number_input("Adet", min_value=1, value=1, step=1)

    # Plaka Mantığı (Tüm metaller için 0.8-1.5mm kuralı)
    if 0.8 <= kalinlik <= 1.5:
        plaka_secenekleri = {"100x200cm": (1000, 2000), "125x250cm": (1250, 2500), "150x300cm": (1500, 3000)}
    else:
        plaka_secenekleri = {"100x200cm": (1000, 2000), "150x300cm": (1500, 3000), "150x600cm": (1500, 6000)}

    secilen_plaka_adi = st.selectbox("Plaka Boyutu", list(plaka_secenekleri.keys()))

    # Hız ve Birim Kutucukları (Dikey Tasarım)
    hiz_tablosu = materials.VERİ[metal]["hizlar"]
    guncel_hiz = hiz_tablosu.get(kalinlik, 1000)
    
    if 'temp_kg_fiyat' not in st.session_state:
        st.session_state.temp_kg_fiyat = float(materials.VARSAYILAN_FIYATLAR.get(metal, 33.0))
    
    st.markdown("<br>", unsafe_allow_html=True)
    col_i1, col_i2 = st.columns(2)
    with col_i1:
        st.markdown(f"""
            <div style="background-color: #e7f3fe; padding: 10px; border-radius: 8px; border-left: 4px solid #2196F3; color: #0c5460; min-height: 75px;">
                <div style="font-size: 11px; font-weight: 600; opacity: 0.8; margin-bottom: 4px;">Hız(mm/dk)</div>
                <div style="font-size: 17px; font-weight: bold;">{guncel_hiz}</div>
            </div>
        """, unsafe_allow_html=True)
    with col_i2:
        st.markdown(f"""
            <div style="background-color: #d4edda; padding: 10px; border-radius: 8px; border-left: 4px solid #28a745; color: #155724; min-height: 75px;">
                <div style="font-size: 11px; font-weight: 600; opacity: 0.8; margin-bottom: 4px;">Birim(TL/kg)</div>
                <div style="font-size: 17px; font-weight: bold;">{st.session_state.temp_kg_fiyat} TL</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

    kg_fiyati = st.number_input(
        "Malzeme KG Fiyatı (TL)", 
        min_value=0.0, 
        value=st.session_state.temp_kg_fiyat, 
        step=1.0, 
        format="%g",
        key="kg_input_field"
    )
    st.session_state.temp_kg_fiyat = kg_fiyati

# --- ANA PANEL ---
if st.session_state.sayfa == 'anasayfa':
    st.title("AI DESTEKLİ PROFESYONEL ANALİZ")
    c1, c2, c3 = st.columns(3, gap="medium")
    
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
            st.session_state.sayfa = 'foto_analiz'; st.rerun()

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
            st.session_state.sayfa = 'dxf_analiz'; st.rerun()

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
            st.session_state.sayfa = 'hazir_parca'; st.rerun()

elif st.session_state.sayfa == 'foto_analiz':
    if st.button("⬅️ Geri"):
        st.session_state.sayfa = 'anasayfa'; st.rerun()
    uploaded_file = st.file_uploader("Görsel Yükle", type=['jpg', 'png', 'jpeg'])
    if uploaded_file:
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, 1)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            cnt = max(contours, key=cv2.contourArea)
            ref_mm = st.number_input("Genişlik (mm)", value=100.0)
            x, y, w, h = cv2.boundingRect(cnt)
            oran = ref_mm / w
            g_gen, g_yuk = w * oran, h * oran
            
            # --- DİNAMİK PATLATMA SÜRESİ HESABI ---
            p_suresi = materials.PIERCING_SURELERI.get(kalinlik, 1.0)
            kontur_ad = 1 # Basitlik için 1 varsayıldı
            
            sure_dk = ((cv2.arcLength(cnt, True) * oran) / guncel_hiz) * adet + (kontur_ad * adet * p_suresi / 60)
            agirlik = (cv2.contourArea(cnt) * (oran**2) * kalinlik * materials.VERİ[metal]["ozkutle"] / 1e6) * materials.FIRE_ORANI
            f_haric = (sure_dk * materials.DK_UCRETI) + (agirlik * adet * kg_fiyati)
            f_dahil = f_haric * materials.KDV_ORANI
            
            st.image(cv2.drawContours(img.copy(), [cnt], -1, (0, 255, 0), 2))
            st.markdown("### 📋 Teklif Özeti")
            cl1, cl2 = st.columns(2)
            with cl1:
                st.markdown(f'<div class="analiz-bilgi-kutu">📏 Ölçü: {round(g_gen,1)}x{round(g_yuk,1)} mm<br>⏱ Süre: {round(sure_dk,2)} dk</div>', unsafe_allow_html=True)
            with cl2:
                st.markdown(f'<div class="analiz-bilgi-kutu"><b>KDV HARİÇ: {round(f_haric,2)} TL</b><br><span style="color:green">KDV DAHİL: {round(f_dahil,2)} TL</span></div>', unsafe_allow_html=True)
            
            pdf_data = {"metal": metal, "kalinlik": kalinlik, "adet": adet, "plaka": secilen_plaka_adi, "olcu": f"{round(g_gen,1)}x{round(g_yuk,1)}", "sure": round(sure_dk,2), "kontur": kontur_ad, "hiz": guncel_hiz, "fiyat_haric": round(f_haric,2), "fiyat_dahil": round(f_dahil,2)}
            st.markdown('<div class="floating-pdf-container">📄 <b>Teklif Hazır</b>', unsafe_allow_html=True)
            st.download_button("PDF İndir", data=generate_pdf(pdf_data), file_name="Teklif.pdf", mime="application/pdf", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.sayfa == 'dxf_analiz':
    if st.button("⬅️ Geri"):
        st.session_state.sayfa = 'anasayfa'; st.rerun()
    if not dxf_active: st.error("Kütüphane Hatası!"); st.stop()
    uploaded_dxf = st.file_uploader("DXF Seç", type=['dxf'])
    if uploaded_dxf:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
            tmp.write(uploaded_dxf.getvalue())
            doc = ezdxf.readfile(tmp.name)
            msp = doc.modelspace()
            extents = bbox.extents(msp)
            w_real = extents.extmax.x - extents.extmin.x
            h_real = extents.extmax.y - extents.extmin.y
            
            fig = plt.figure(figsize=(8,8), facecolor='#111827')
            ax = fig.add_axes([0,0,1,1]); ax.set_facecolor('#111827')
            ctx = RenderContext(doc)
            for l in ctx.layers.values(): l.color = '#FFFFFF'
            Frontend(ctx, MatplotlibBackend(ax)).draw_layout(msp, finalize=True)
            ax.axis('off'); fig.canvas.draw()
            rgba_buf = fig.canvas.buffer_rgba()
            img_array = np.frombuffer(rgba_buf, dtype=np.uint8).reshape(fig.canvas.get_width_height()[1], fig.canvas.get_width_height()[0], 4)
            plt.close(fig)
            st.image(img_array)

            # --- DİNAMİK PATLATMA SÜRESİ HESABI ---
            p_suresi = materials.PIERCING_SURELERI.get(kalinlik, 1.0)
            piercing_adedi = 1 # Gelişmiş versiyonda msp entity sayısı sayılabilir
            
            sure_dk = (w_real*2 + h_real*2) / guncel_hiz * adet + (piercing_adedi * adet * p_suresi / 60)
            f_haric = (sure_dk * materials.DK_UCRETI) + (w_real*h_real*kalinlik*materials.VERİ[metal]["ozkutle"]/1e6*adet*kg_fiyati)
            f_dahil = f_haric * materials.KDV_ORANI
            
            st.markdown("### 📋 Teknik Çizim Özeti")
            cl1, cl2 = st.columns(2)
            with cl1:
                st.markdown(f'<div class="analiz-bilgi-kutu">📏 Tahmini Ölçü: {round(w_real, 1)}x{round(h_real, 1)} mm<br>⏱ Süre: {round(sure_dk, 2)} dk</div>', unsafe_allow_html=True)
            with cl2:
                st.markdown(f'<div class="analiz-bilgi-kutu"><b>KDV HARİÇ: {round(f_haric, 2)} TL</b><br><span style="color:green">KDV DAHİL: {round(f_dahil, 2)} TL</span></div>', unsafe_allow_html=True)

            pdf_data = {"metal": metal, "kalinlik": kalinlik, "adet": adet, "plaka": secilen_plaka_adi, "olcu": f"{round(w_real,1)}x{round(h_real,1)}", "sure": round(sure_dk,2), "kontur": piercing_adedi, "hiz": guncel_hiz, "fiyat_haric": round(f_haric,2), "fiyat_dahil": round(f_dahil,2)}
            st.markdown('<div class="floating-pdf-container">📄 <b>Teklif Hazır</b>', unsafe_allow_html=True)
            st.download_button("PDF İndir", data=generate_pdf(pdf_data), file_name="Teklif.pdf", mime="application/pdf", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.sayfa == 'hazir_parca':
    if st.button("⬅️ Geri"):
        st.session_state.sayfa = 'anasayfa'; st.rerun()
    g = st.number_input("Genişlik", value=100.0)
    y = st.number_input("Yükseklik", value=100.0)
    delik = st.number_input("Delik Sayısı", value=0)
    
    # --- DİNAMİK PATLATMA SÜRESİ HESABI ---
    p_suresi = materials.PIERCING_SURELERI.get(kalinlik, 1.0)
    piercing_sayisi = 1 + delik
    
    sure_dk = (g*2 + y*2) / guncel_hiz * adet + (piercing_sayisi * adet * p_suresi / 60)
    f_haric = (sure_dk * materials.DK_UCRETI) + (g*y*kalinlik*materials.VERİ[metal]["ozkutle"]/1e6*adet*kg_fiyati)
    f_dahil = f_haric * materials.KDV_ORANI
    
    st.markdown("### 📋 Hazır Parça Özeti")
    cl1, cl2 = st.columns(2)
    with cl1:
        st.markdown(f'<div class="analiz-bilgi-kutu">📏 Ölçü: {g}x{y} mm<br>⏱ Süre: {round(sure_dk, 2)} dk</div>', unsafe_allow_html=True)
    with cl2:
        st.markdown(f'<div class="analiz-bilgi-kutu"><b>KDV HARİÇ: {round(f_haric, 2)} TL</b><br><span style="color:green">KDV DAHİL: {round(f_dahil, 2)} TL</span></div>', unsafe_allow_html=True)
    
    pdf_data = {"metal": metal, "kalinlik": kalinlik, "adet": adet, "plaka": secilen_plaka_adi, "olcu": f"{g}x{y}", "sure": round(sure_dk,2), "kontur": piercing_sayisi, "hiz": guncel_hiz, "fiyat_haric": round(f_haric,2), "fiyat_dahil": round(f_dahil,2)}
    st.markdown('<div class="floating-pdf-container">📄 <b>Teklif Hazır</b>', unsafe_allow_html=True)
    st.download_button("PDF İndir", data=generate_pdf(pdf_data), file_name="Teklif.pdf", mime="application/pdf", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
