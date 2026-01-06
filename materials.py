# materials.py - Malzeme Verileri ve Sabitler

# --- SABİT PARAMETRELER ---
DK_UCRETI = 35.0        # Dakika Başına Kesim Ücreti
PIERCING_SURESI = 3.0   # Patlatma Süresi (Saniye)
FIRE_ORANI = 1.15       # Fire Oranı (%15)
KDV_ORANI = 1.20        # KDV (%20)

# --- VARSAYILAN KG FİYATLARI ---
VARSAYILAN_FIYATLAR = {
    "DKP / HRP(Siyah Sac)": 29.0,
    "Paslanmaz": 150.0,
    "Alüminyum": 220.0
}

# --- MALZEME VERİTABANI ---
VERİ = {
    "DKP / HRP(Siyah Sac)": {
        "ozkutle": 8.0, 
        "kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20], 
        "hizlar": {
            0.8: 6000,
            1: 6000,
            1.2: 6000,
            1.5: 6000,
            2: 5000,
            3: 3750,
            4: 3000,
            5: 2750,
            6: 2250,
            8: 1750,
            10: 1500,
            12: 1200,
            15: 1900,
            20: 600
        }
    },
    "Paslanmaz": {
        "ozkutle": 8.0, 
        "kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8, 10], 
        "hizlar": {
            0.8: 8000,
            1: 7000,
            1.2: 6600,
            1.5: 6000,
            2: 5000,
            3: 4500,
            4: 4000,
            5: 3000,
            6: 2000,
            8: 1000,
            10: 750
        }
    },
    "Alüminyum": {
        "ozkutle": 2.7, 
        "kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8], 
        "hizlar": {
            0.8: 7000,
            1: 6500,
            1.2: 6000,
            1.5: 5500,
            2: 5000,
            3: 4500,
            4: 4000,
            5: 3000,
            6: 2000,
            8: 1000
        }
    }
}
