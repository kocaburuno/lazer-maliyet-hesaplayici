import streamlit as st
import cv2
import numpy as np

# 1. SAYFA YAPILANDIRMASI
st.set_page_config(page_title="Teklif Paneli", layout="wide")

# 2. ÜRETİM PARAMETRELERİ (İlk verdiğiniz tabloya tam sadık kalındı)
DK_UCRETI = 25.0       
PIERCING_SURESI = 2.0  
KG_UCRETI = 45.0       

VERİ = {
    "Siyah Sac": {"ozkutle": 7.85, "kalinliklar": [0.8, 1, 2, 3, 5, 10, 20], "hizlar": {0.8: 6000, 3: 2800, 10: 800}},
    "Paslanmaz": {"ozkutle": 8.0, "kalinliklar": [0.8, 1, 2, 5, 10], "hizlar": {0.8: 7000, 2: 4500, 10: 500}},
    "Alüminyum": {"ozkutle": 2.7, "kalinliklar": [0.8, 1, 2, 5, 8], "hizlar": {0.8: 8000, 2: 5000, 8: 600}}
}

# 3. SIDEBAR
with st.sidebar:
    st.title("ALAN LAZER")
    metal = st.selectbox("Metal Türü", list(VERİ.keys()))
    kalinlik = st.selectbox("Kalınlık (mm)", VERİ[metal]["kalinliklar"])
    adet = st.number_input("Parça Adedi", min_value=1, value=1)
    referans_olcu = st.number_input("Çizimdeki Genişlik (mm)", value=3295.0)
    
    hiz_listesi = VERİ[metal]["hizlar"]
    guncel_hiz = hiz_listesi.get(kalinlik, min(hiz_listesi.values()))

# 4. ANA PANEL
st.title("Profesyonel Teklif Paneli")
uploaded_file = st.file_uploader("Çizim Fotoğrafını Yükle", type=['jpg', 'png', 'jpeg'])

if uploaded_file:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 3x Piercing hatasını önlemek için morfolojik sadeleştirme
    _, binary = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)
    kernel = np.ones((3,3), np.uint8)
    binary = cv2.dilate(binary, kernel, iterations=1) # Çizgileri birleştirerek tek hat oluşturur
    
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        main_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(main_contour)
        oran = referans_olcu / w
        
        # Sadece belirli bir alan aralığındaki konturları "Piercing" kabul et
        # Bu, grid çizgilerini ve çizgi kalınlığı farklarını eler
        gecerli_konturlar = []
        toplam_yol_piksel = 0
        
        # Önemli: En dış çerçeve + içerideki odalar
        for cnt in contours:
            cevre = cv2.arcLength(cnt, True)
            area = cv2.contourArea(cnt)
            
            # Gürültüleri ve çok ince çizgileri temizle
            if cevre * oran > 20.0: 
                gecerli_konturlar.append(cnt)
                toplam_yol_piksel += cevre
        
        # Sonuçlar
        piercing_basi = len(gecerli_konturlar)
        kesim_m = (toplam_yol_piksel * oran) / 1000
        sure_dk = (kesim_m * 1000 / guncel_hiz) * adet + (piercing_basi * adet * PIERCING_SURESI / 60)
        agirlik = (cv2.contourArea(main_contour) * (oran**2) * kalinlik * VERİ[metal]["ozkutle"]) / 1e6
        fiyat = (sure_dk * DK_UCRETI) + (agirlik * adet * KG_UCRETI)

        # Görselleştirme
        output_img = img.copy()
        cv2.drawContours(output_img, gecerli_konturlar, -1, (0, 255, 0), 2)
        st.image(cv2.cvtColor(output_img, cv2.COLOR_BGR2RGB), use_container_width=True)
        
        # Tablo
        st.subheader("📋 Kesim Analizi ve Teklif")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Toplam Kesim", f"{round(kesim_m * adet, 1)} m")
        c2.metric("Piercing Adedi", f"{piercing_basi * adet}")
        c3.metric("Tahmini Süre", f"{round(sure_dk, 1)} dk")
        c4.metric("TOPLAM FİYAT", f"{round(fiyat, 2)} TL")
