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

# 3. SIDEBAR (Üretim Seçenekleri)
with st.sidebar:
    st.title("ALAN LAZER")
    metal = st.selectbox("Metal Türü", list(VERİ.keys()))
    kalinlik = st.selectbox("Kalınlık (mm)", VERİ[metal]["kalinliklar"])
    secilen_plaka = st.selectbox("Plaka Boyutu (mm)", ["1500x6000", "1500x3000", "2500x1250"])
    adet = st.number_input("Parça Adedi", min_value=1, value=1)
    referans_olcu = st.number_input("Çizimdeki Genişlik (mm)", value=3295.0)
    
    # Hız belirleme
    hiz_listesi = VERİ[metal]["hizlar"]
    guncel_hiz = hiz_listesi.get(kalinlik, min(hiz_listesi.values()))

# 4. ANA PANEL
st.title("Profesyonel Teklif Paneli")
uploaded_file = st.file_uploader("Çizim Fotoğrafını Yükle", type=['jpg', 'png', 'jpeg'])

if uploaded_file:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # IZGARA VE GÜRÜLTÜ TEMİZLEME
    # Otsu threshold ile en net siyah-beyaz ayrımı yapılır
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # İnce ızgara çizgilerini yok etmek için morfolojik temizlik
    kernel = np.ones((2,2), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    
    # Hiyerarşik Kontur Analizi
    contours, hierarchy = cv2.findContours(binary, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours and hierarchy is not None:
        main_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(main_contour)
        oran = referans_olcu / w
        
        gecerli_konturlar = []
        toplam_yol_piksel = 0

        for i, cnt in enumerate(contours):
            # 1. Filtre: Sadece ana çerçeve ve içindeki ilk seviye delikleri say
            # 2. Filtre: Çok küçük ızgara parçalarını ele (Alan kontrolü)
            parent_idx = hierarchy[0][i][3]
            if parent_idx == -1 or parent_idx == 0:
                cevre = cv2.arcLength(cnt, True)
                alan = cv2.contourArea(cnt)
                
                # Gerçek bir kesim yolu olması için minimum çevre ve alan şartı
                if (cevre * oran > 10.0) and (alan * (oran**2) > 5.0):
                    gecerli_konturlar.append(cnt)
                    toplam_yol_piksel += cevre
        
        # ANALİTİK SONUÇLAR
        piercing_basi = len(gecerli_konturlar)
        kesim_yolu_m = (toplam_yol_piksel * oran) / 1000
        
        # Maliyet ve Süre
        # Toplam yol üzerinden süre hesabı
        sure_dk = (kesim_yolu_m * 1000 / guncel_hiz) * adet + (piercing_basi * adet * PIERCING_SURESI / 60)
        agirlik = (cv2.contourArea(main_contour) * (oran**2) * kalinlik * VERİ[metal]["ozkutle"]) / 1e6
        toplam_fiyat = (sure_dk * DK_UCRETI) + (agirlik * adet * KG_UCRETI)

        # GÖRSELLEŞTİRME: Sadece tespit edilen yeşil hatlar
        output_img = img.copy()
        cv2.drawContours(output_img, gecerli_konturlar, -1, (0, 255, 0), 2)
        st.image(cv2.cvtColor(output_img, cv2.COLOR_BGR2RGB), use_container_width=True)
        
        # SONUÇ TABLOSU
        st.subheader("📋 Kesim Analizi ve Teklif")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Toplam Kesim", f"{round(kesim_yolu_m * adet, 1)} m")
        c2.metric("Piercing Adedi", f"{piercing_basi * adet}")
        c3.metric("Tahmini Süre", f"{round(sure_dk, 1)} dk")
        c4.metric("TOPLAM FİYAT", f"{round(toplam_fiyat, 2)} TL")
        
        with st.expander("Maliyet Detayları"):
            st.write(f"**Birim Başına Piercing:** {piercing_basi} adet")
            st.write(f"**Parça Ağırlığı:** {round(agirlik, 2)} kg")
            st.write(f"**Kesim Hızı:** {guncel_hiz} mm/dk")
