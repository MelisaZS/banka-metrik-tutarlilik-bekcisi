# -*- coding: utf-8 -*-
"""Sentetik banka verisi üretir — bank.db (SQLite).

Gerçek müşteri verisi İÇERMEZ. Türkiye dağılımına yakın sentetik veri:
İstanbul ağırlıklı iller, mobil ağırlıklı kanallar, lognormal tutarlar.

Çalıştırma:  python generate_data.py
"""
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

random.seed(42)
KOK = Path(__file__).parent
DB = KOK / "bank.db"

ILLER = (["İstanbul"] * 35 + ["Ankara"] * 12 + ["İzmir"] * 9 +
         ["Bursa"] * 6 + ["Antalya"] * 5 + ["Konya"] * 4 +
         ["Adana"] * 4 + ["Gaziantep"] * 3 + ["Kayseri"] * 3 +
         ["Trabzon"] * 2 + ["Samsun"] * 2 + ["Diğer"] * 15)
KANALLAR = (["MOBIL"] * 54 + ["INTERNET"] * 16 + ["ATM"] * 14 +
            ["SUBE"] * 12 + ["CAGRI_MERKEZI"] * 3 + ["POS"] * 1)

N_MUSTERI = 3000
N_SUBE = 60
N_ISLEM = 40000
BUGUN = date.today()


def main():
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.executescript("""
    CREATE TABLE sube (
        sube_id INTEGER PRIMARY KEY, ad TEXT, il TEXT);
    CREATE TABLE musteri (
        musteri_id INTEGER PRIMARY KEY, il TEXT,
        durum TEXT, acilis_tarihi TEXT);
    CREATE TABLE hesap (
        hesap_id INTEGER PRIMARY KEY, musteri_id INTEGER,
        durum TEXT, bakiye REAL);
    CREATE TABLE islem (
        islem_id INTEGER PRIMARY KEY, musteri_id INTEGER,
        sube_id INTEGER, kanal TEXT, tutar REAL,
        tarih TEXT, durum TEXT);
    """)

    subeler = [(i + 1, f"Şube {i + 1:03d}", random.choice(ILLER))
               for i in range(N_SUBE)]
    cur.executemany("INSERT INTO sube VALUES (?,?,?)", subeler)

    musteriler = [(i + 1, random.choice(ILLER),
                   "AKTIF" if random.random() < 0.9 else "PASIF",
                   (BUGUN - timedelta(days=random.randint(30, 2000))).isoformat())
                  for i in range(N_MUSTERI)]
    cur.executemany("INSERT INTO musteri VALUES (?,?,?,?)", musteriler)

    hesaplar, hid = [], 0
    for m_id, *_ in musteriler:
        for _ in range(random.choice([1, 1, 1, 2, 2, 3])):
            hid += 1
            r = random.random()
            durum = "TAKIPTE" if r < 0.04 else ("KAPALI" if r < 0.12 else "ACIK")
            hesaplar.append((hid, m_id, durum,
                             round(random.lognormvariate(9, 1.4), 2)))
    cur.executemany("INSERT INTO hesap VALUES (?,?,?,?)", hesaplar)

    islemler = []
    for i in range(N_ISLEM):
        # son 30 gün daha yoğun -> zaman penceresi kaymasında anlamlı fark
        gun = random.randint(0, 29) if random.random() < 0.45 else random.randint(30, 120)
        islemler.append((i + 1, random.randint(1, N_MUSTERI),
                         random.randint(1, N_SUBE), random.choice(KANALLAR),
                         round(random.lognormvariate(6.5, 1.2), 2),
                         (BUGUN - timedelta(days=gun)).isoformat(),
                         "BASARILI" if random.random() < 0.97 else "IPTAL"))
    cur.executemany("INSERT INTO islem VALUES (?,?,?,?,?,?,?)", islemler)

    con.commit()
    con.close()
    print(f"bank.db hazır — {N_MUSTERI} müşteri, {len(hesaplar)} hesap, "
          f"{N_ISLEM} işlem, {N_SUBE} şube")


if __name__ == "__main__":
    main()
