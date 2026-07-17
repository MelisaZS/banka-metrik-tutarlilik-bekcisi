# Banka Metrik Tutarlılık Bekçisi (v1.1)

Rapor SQL tanımlarını tarayıp aynı metriğin farklı formüllerle hesaplandığı
yerleri (tanım kayması) ve birebir kopya raporları (gizli kopya) bulan
İş Zekası aracı. Yalnızca SQL metnini okur — müşteri verisine erişmez.

## Kurulum
```bash
pip install -r requirements.txt
python generate_data.py        # sentetik bank.db üretir
streamlit run app.py
```

## Klasör yapısı
```
app.py               Streamlit panel (üst navbar, hero, TR/EN, kurumsal yeşil tema)
generate_data.py     Sentetik Türkiye-benzeri banka verisi (SQLite)
detector/core.py     Çekirdek motor: sqlglot AST + drift/kopya tespiti
views/*.sql          15 rapor tanımı (6 bilerek gömülü tutarsızlık)
answer_key.json      Doğruluk ölçümü için cevap anahtarı
.streamlit/          Tema ayarları
```

## Doğruluk
Gömülü 6 tutarsızlığın 6'sı yakalanır; yanlış alarm 0
(recall %100, precision %100). "Doğruluk ölçümü" sekmesinden canlı izlenir.

## Notlar
- Tüm veriler sentetiktir; gerçek müşteri verisi içermez.
- Üretim hedefi: Oracle kataloğundan (ALL_VIEWS) korpus çekme.
