-- Günlük işlem sayısı
SELECT
  COUNT(*) AS GUNLUK_ISLEM
FROM islem i
WHERE i.durum = 'BASARILI' AND i.tarih >= date('now', '-1 day');
