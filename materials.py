# materials.py - Malzeme, Lazer ve Büküm Verileri

# ==========================================
# 1. GENEL MALİYET VE FİRE AYARLARI
# ==========================================
DK_UCRETI = 45.0        # Dakika Başına Kesim Ücreti (TL)
FIRE_ORANI = 1.20       # Fire Oranı (%20 -> 1.20 ile çarpılır)
KDV_ORANI = 1.20        # KDV Oranı (%20)

# ==========================================
# 2. BÜKÜM (ABKANT) FİYATLANDIRMA KURALLARI
# ==========================================
# Eğer toplam ağırlık bu limiti geçerse, kalınlığa bakılmaksızın toptan fiyat uygulanır.
BUKUM_TOPTAN_LIMIT_KG = 100.0   
BUKUM_TOPTAN_FIYAT = 30.0       # Toptan birim fiyatı (TL/kg)

# Kalınlığa Göre Standart Büküm Baz Fiyatları (TL/kg)
# (100 kg altındaki işlerde kullanılır)
BUKUM_F_0_2_MM = 100.0    # 0.8mm - 2.0mm arası (dahil değil)
BUKUM_F_2_5_MM = 80.0     # 2.0mm - 5.0mm arası (dahil değil)
BUKUM_F_5_6_MM = 60.0     # 5.0mm - 6.0mm arası (dahil değil)
BUKUM_F_6_10_MM = 40.0    # 6.0mm - 10.0mm arası (dahil)
BUKUM_F_STANDART = 100.0  # Tanımsız aralıklar için varsayılan

# ==========================================
# 3. PIERCING (PATLATMA) SÜRELERİ (Saniye)
# ==========================================
# Mantık: Kalınlık (mm) : Süre (sn)
PIERCING_SURELERI = {
    0.8: 1.0,
    1.0: 1.0,
    1.2: 1.0,
    1.5: 1.0,
    2.0: 1.0,
    3.0: 1.0,
    4.0: 1.0,
    5.0: 1.0,
    6.0: 1.5,
    8.0: 2.0,
    10.0: 3.0,
    12.0: 4.5,
    15.0: 6.0,
    20.0: 7.5
}

# ==========================================
# 4. VARSAYILAN SAC KG FİYATLARI (TL)
# ==========================================
VARSAYILAN_FIYATLAR = {
    "DKP / HRP(Siyah Sac)": 29.0,
    "Paslanmaz": 150.0,
    "Alüminyum": 220.0
}

# ==========================================
# 5. MALZEME VERİTABANI (Hız, Özkütle, Kalınlıklar)
# ==========================================
VERİ = {
    "DKP / HRP(Siyah Sac)": {
        "ozkutle": 7.85, 
        "kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20], 
        "hizlar": {
            0.8: 6000, 1: 6000, 1.2: 6000, 1.5: 6000, 2: 5000,
            3: 3750, 4: 3000, 5: 2750, 6: 2250, 8: 1750,
            10: 1500, 12: 1200, 15: 1900, 20: 600
        }
    },
    "Paslanmaz": {
        "ozkutle": 8.0, 
        "kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8, 10], 
        "hizlar": {
            0.8: 8000, 1: 7000, 1.2: 6600, 1.5: 6000, 2: 5000,
            3: 4500, 4: 4000, 5: 3000, 6: 2000, 8: 1000, 10: 750
        }
    },
    "Alüminyum": {
        "ozkutle": 2.7, 
        "kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8], 
        "hizlar": {
            0.8: 7000, 1: 6500, 1.2: 6000, 1.5: 5500, 2: 5000,
            3: 4500, 4: 4000, 5: 3000, 6: 2000, 8: 1000
        }
    }
}
