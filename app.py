import streamlit as st
import cv2
import numpy as np

# 1. SAYFA YAPILANDIRMASI
st.set_page_config(page_title="Alan Lazer - Teklif Paneli", layout="wide")

# 2. ÜRETİM PARAMETRELERİ (Admin Ayarları)
DK_UCRETI = 25.0       
PIERCING_SURESI = 2.0  
KG_UCRETI = 45.0       

VERİ = {
    "Siyah Sac": {
        "ozkutle": 7.85, 
        "kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20],
        "hizlar": {0.8: 6000, 1: 5500, 2: 4500, 3: 2800, 5: 1800, 10: 800}
    },
    "Paslanmaz": {
        "ozkutle": 8.0, 
        "kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8, 10],
        "hizlar": {0.8: 7000, 2: 4500, 5: 1200, 10: 500}
    },
    "Alüminyum": {
        "ozkutle": 2.7, 
        "kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8],
        "hizlar": {0.8: 8000, 1.5: 6000, 2: 5000, 5: 1500, 8: 600}
    }
}

# 3. SIDEBAR (Sol Panel)
with st.sidebar:
    try:
        st.image("logo.png", use_container_width=True)
    except:
        st.title("ALAN LAZER")
    
    st.subheader("Üretim Seçenekleri")
    
    # Metal seçimi (Alüminyum Geri Geldi)
    metal = st.selectbox("Metal Türü", list(VERİ.keys()))
    
    # Dinamik Kalınlık Seçimi
    kalinlik_listesi = VERİ[metal]["kalinliklar"]
    kalinlik = st.selectbox("Kalınlık (mm)", kalinlik_listesi)
    
    # Plaka ve Adet
    secilen_plaka = st.selectbox("Plaka Boyutu (mm)", ["1500x6000", "1500x3000", "2500x1250", "1000x2000"])
    adet = st.number_input("Parça Adedi", min_value=1, value=1)
    referans_olcu = st.number_input("Çizimdeki Genişlik (mm)", value=3295)
    
    st.markdown("---")
    
    # Hız Hesabı
    hiz_tablosu = VERİ[metal]["hizlar"]
    # Seçilen kalınlığa en yakın hızı bulur
    guncel_hiz = hiz_tablosu.get(kalinlik, min(hiz_tablosu.values()))
    
    st.info(f"**Sistem Bilgisi:**\n- Hız: {guncel_hiz} mm/dk\n- Dakika Ücreti: {DK_UCRETI} TL")

# 4. ANA EKRAN VE ANALİZ
st.title("Alan Lazer Profesyonel Teklif Paneli")

uploaded_file = st.file_uploader("Çizim Fotoğrafını Yükle", type=['jpg', 'png', 'jpeg'])

if uploaded_file:
    # Görüntü hazırlama
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Pürüzleri ve çift çizgileri engellemek için filtreler
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 150, 255, cv2.THRESH_BINARY_INV)
    
    # Konturları hiyerarşik olarak bul (İç delikleri ve dışı ayırır)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        # En büyük konturu (Dış çerçeve) referans al
        main_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(main_contour)
        oran = referans_olcu / w
        
        # Parça Boyutları
        p_en, p_boy = w * oran, h * oran
        
        # Plaka Sığma Kontrolü
        pl_en_v, pl_boy_v = map(int, secilen_plaka.split('x'))
        sigiyor = (p_en <= pl_en_v and p_boy <= pl_boy_v) or (p_en <= pl_boy_v and p_boy <= pl_en_v)
        
        if not sigiyor:
            st.error(f"❌ HATA: {round(p_en)}x{round(p_boy)}mm boyutundaki parça {secilen_plaka} plakaya sığmıyor!")
        else:
            # --- HASSAS ANALİZ ---
            gecerli_konturlar = []
            toplam_yol_piksel = 0
            # 2mm altındaki küçük parçacıkları ve çizgi hatalarını ele (Min 10mm² alan)
            min_alan_filtresi = 10 / (oran**2)

            for i, cnt in enumerate(contours):
                # Hiyerarşide sadece ana döngüleri say (Çizginin içini/dışını ayrı saymaz)
                if hierarchy[0][i][3] == -1 or hierarchy[0][i][3] == 0:
                    if cv2.contourArea(cnt) > min_alan_filtresi:
                        gecerli_konturlar.append(cnt)
                        toplam_yol_piksel += cv2.arcLength(cnt, True)
            
            # Piercing: Her kapalı döngü 1 adet
            piercing_sayisi = len(gecerli_konturlar) * adet
            kesim_yolu_m = (toplam_yol_piksel * oran) / 1000
            
            # Maliyet ve Süre
            kesim_suresi_dk = (kesim_yolu_m * 1000 / guncel_hiz) * adet
            piercing_suresi_dk = (piercing_sayisi * PIERCING_SURESI) / 60
            toplam_sure_dk = kesim_suresi_dk + piercing_suresi_dk
            
            isclik_maliyeti = toplam_sure_dk * DK_UCRETI
            malzeme_agirlik = (cv2.contourArea(main_contour) * (oran**2) * kalinlik * VERİ[metal]["ozkutle"]) / 1e6
            malzeme_maliyeti = malzeme_agirlik * adet * KG_UCRETI
            
            # Ekrana Çizim Yap
            for cnt in gecerli_konturlar:
                cv2.drawContours(img, [cnt], -1, (0, 255, 0), 2)
            st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), use_container_width=True)
            
            # Detaylı Sonuçlar
            st.subheader("📋 Kesim Analizi ve Teklif")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Toplam Kesim", f"{round(kesim_yolu_m, 1)} m")
            c2.metric("Piercing", f"{piercing_sayisi} Adet")
            c3.metric("Tahmini Süre", f"{round(toplam_sure_dk, 1)} dk")
            c4.metric("TOPLAM FİYAT", f"{round(isclik_maliyeti + malzeme_maliyeti, 2)} TL")
            
            with st.expander("Maliyet Detayları"):
                st.write(f"**Parça Boyutu:** {round(p_en)} x {round(p_boy)} mm")
                st.write(f"**Birim Ağırlık:** {round(malzeme_agirlik, 2)} kg")
                st.write(f"**İşçilik Tutarı:** {round(isclik_maliyeti, 2)} TL")
                st.write(f"**Malzeme Tutarı:** {round(malzeme_maliyeti, 2)} TL")
