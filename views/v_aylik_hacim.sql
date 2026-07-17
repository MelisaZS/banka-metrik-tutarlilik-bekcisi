-- Aylık işlem hacmi
SELECT
  SUM(i.tutar) AS AYLIK_HACIM
FROM islem i
WHERE i.durum = 'BASARILI' AND i.tarih >= date('now', '-30 day');
