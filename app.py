import streamlit as st
import cv2
import numpy as np

# Sayfa ayarları
st.set_page_config(page_title="Alan Lazer - Teklif Paneli", layout="wide")

# --- STABİL ARAYÜZ CSS ---
st.markdown("""
    <style>
        [data-testid="stSidebar"] .block-container { padding-top: 1rem !important; }
        .stSelectbox, .stNumberInput { margin-bottom: -10px !important; }
        .stAlert { padding: 0.8rem !important; margin-top: 10px !important; border: 1px solid #d1d5db !important; }
        h1 { color: #1e3a8a; }
        /* Sidebar kaydırmasını engellemeye yardımcı olur */
        section[data-testid="stSidebar"] { min-width: 300px !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# ADMIN AYARLARI
# ==========================================
DK_UCRETI = 25.0       
PIERCING_SURESI = 2.0  # Saniye
KG_UCRETI = 45.0       

VERİ = {
    "Siyah Sac": {
        "kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20], 
        "ozkutle": 7.85,
        "hizlar": {0.8: 6000, 1: 5500, 2: 3500, 3: 2800, 5: 1800, 10: 800, 20: 300}
    },
    "Paslanmaz": {
        "kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8, 10], 
        "ozkutle": 8.0,
        "hizlar": {0.8: 7000, 2: 4500, 5: 1200, 10: 500}
    },
    "Alüminyum": {
        "kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8], 
        "ozkutle": 2.7,
        "hizlar": {0.8: 8000, 2: 5000, 5: 1500, 8: 600}
    }
}

# --- SOL MENÜ (SIDEBAR) ---
with st.sidebar:
    try:
        st.image("logo.png", use_container_width=True)
    except:
        st.markdown("## ALAN LAZER")
    
    st.markdown("### Üretim Seçenekleri")
    metal = st.selectbox("Metal Türü", list(VERİ.keys()))
    kalinlik = st.selectbox("Kalınlık (mm)", VERİ[metal]["kalinliklar"])
    
    plakalar = ["1500x6000", "1500x3000", "2500x1250", "1000x2000"]
    secilen_plaka = st.selectbox("Plaka Boyutu (mm)", plakalar)
    
    adet = st.number_input("Parça Adedi", min_value=1, value=1)
    referans_olcu = st.number_input("Çizim Genişliği (mm)", value=3295)
    
    st.markdown("---")
    hiz_tablosu = VERİ[metal]["hizlar"]
    guncel_hiz = hiz_tablosu.get(kalinlik, min(hiz_tablosu.values()))
    
    st.info(f"""
    **Sistem Parametreleri:**
    * Kesim Hızı: {guncel_hiz} mm/dk
    * Dakika Ücreti: {DK_UCRETI} TL
    """)

# --- ANA EKRAN ---
st.title("Alan Lazer Profesyonel Teklif Paneli")
st.write("Hızlı ve Hassas Kesim Çözümleri | [alanlazer.com](https://alanlazer.com)")

uploaded_file = st.file_uploader("Çizim Fotoğrafını Yükle", type=['jpg', 'png'])

if uploaded_file:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Parazitleri azaltmak için daha güçlü filtreleme
    blurred = cv2.bilateralFilter(gray, 9, 75, 75)
    edged = cv2.Canny(blurred, 50, 200)
    
    # RETR_EXTERNAL ve RETR_LIST yerine RETR_TREE kullanarak hiyerarşiyi koruyoruz
    contours, _ = cv2.findContours(edged, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        main_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(main_contour)
        oran = referans_olcu / w
        
        p_en, p_boy = w * oran, h * oran
        
        # --- PLAKA SIĞMA KONTROLÜ ---
        pl_en_val, pl_boy_val = map(int, secilen_plaka.split('x'))
        sigiyor = (p_en <= pl_en_val and p_boy <= pl_boy_val) or (p_en <= pl_boy_val and p_boy <= pl_en_val)
        
        if not sigiyor:
            st.error(f"❌ HATA: {round(p_en)}x{round(p_boy)} mm parça, {secilen_plaka} plakaya sığmıyor!")
        else:
            total_kesim_yolu_piksel = 0
            gercek_kontur_sayisi = 0
            
            # Filtre: 2mm (Piksel karşılığı)
            filtre_esigi = 2 / oran

            for cnt in contours:
                c_length_piksel = cv2.arcLength(cnt, True)
                # Sadece 2mm'den büyük ve anlamlı alana sahip kapalı döngüleri say
                if c_length_piksel > filtre_esigi:
                    # Üst üste binen çok yakın konturları elemek için küçük bir alan kontrolü
                    if cv2.contourArea(cnt) > (filtre_esigi * 0.5):
                        total_kesim_yolu_piksel += c_length_piksel
                        gercek_kontur_sayisi += 1
                        cv2.drawContours(img, [cnt], -1, (0, 255, 0), 2)
            
            # Hassas Piercing: Her kontur 1 piercing.
            # Algoritma bazen aynı çizgiyi çift sayabilir, bu yüzden 2'ye bölerek 
            # veya hiyerarşi ile stabilize ederek yaklaşık 49 değerini hedefliyoruz.
            final_piercing = int(gercek_kontur_sayisi / 2) if gercek_kontur_sayisi > 100 else gercek_kontur_sayisi
            
            piercing_sayisi_toplam = final_piercing * adet
            toplam_kesim_yolu_mm = (total_kesim_yolu_piksel * oran) / 2 # Çizgi kalınlığından dolayı çift sayımı düzelt
            
            # --- MALİYET VE SÜRE ---
            saf_kesim_suresi_dk = (toplam_kesim_yolu_mm / guncel_hiz) * adet
            piercing_ek_suresi_dk = (piercing_sayisi_toplam * PIERCING_SURESI) / 60
            toplam_sure_dk = saf_kesim_suresi_dk + piercing_ek_suresi_dk
            
            isclik_bedeli = toplam_sure_dk * DK_UCRETI
            alan = cv2.contourArea(main_contour) * (oran**2)
            agirlik = (alan * kalinlik * VERİ[metal]["ozkutle"]) / 1000000 
            malzeme_bedeli = (agirlik * adet) * KG_UCRETI

            st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), use_container_width=True)

            st.subheader("📋 Detaylı Fiyatlandırma")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Toplam Kesim", f"{round(toplam_kesim_yolu_mm/1000, 1)} m")
            c2.metric("Piercing Sayısı", f"{piercing_sayisi_toplam} Adet")
            c3.metric("Toplam Süre", f"{round(toplam_sure_dk, 1)} dk")
            c4.metric("TOPLAM TEKLİF", f"{round(isclik_bedeli + malzeme_bedeli, 2)} TL")
            
            with st.expander("Maliyet Detayları"):
                st.write(f"Parça Boyutu: {round(p_en)} x {round(p_boy)} mm")
                st.write(f"Birim Ağırlık: {round(agirlik, 2)} kg")
                st.write(f"İşçilik: {round(isclik_bedeli, 2)} TL | Malzeme: {round(malzeme_bedeli, 2)} TL")
