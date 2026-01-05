# materials.py - Malzeme Verileri ve Sabitler

# --- SABİT PARAMETRELER ---
DK_UCRETI = 25.0        # Dakika Başına Kesim Ücreti
PIERCING_SURESI = 2.0   # Patlatma Süresi (Saniye)
FIRE_ORANI = 1.15       # Fire Oranı (%15)
KDV_ORANI = 1.20        # KDV (%20)

# --- VARSAYILAN KG FİYATLARI ---
VARSAYILAN_FIYATLAR = {
    "Siyah Sac": 30.0,
    "Paslanmaz": 150.0,
    "Alüminyum": 220.0
}

# --- MALZEME VERİTABANI ---
# Buraya yeni kalınlıklar veya hızlar ekleyebilirsin.
VERİ = {
    "Siyah Sac": {
        "ozkutle": 7.85, 
        "kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20], 
        # Kalınlık (mm): Hız (mm/dk)
        "hizlar": {
            0.8: 6000, 
            3: 2800, 
            10: 800
        }
    },
    "Paslanmaz": {
        "ozkutle": 8.0, 
        "kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8, 10, 12, 15], 
        "hizlar": {
            0.8: 7000, 
            2: 4500, 
            10: 500
        }
    },
    "Alüminyum": {
        "ozkutle": 2.7, 
        "kalinliklar": [0.8, 1, 1.2, 1.5, 2, 3, 4, 5, 6, 8], 
        "hizlar": {
            0.8: 8000, 
            2: 5000, 
            8: 600
        }
    }
}
