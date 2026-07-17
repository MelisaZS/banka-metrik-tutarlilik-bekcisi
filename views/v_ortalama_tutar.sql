-- Ortalama işlem tutarı
SELECT
  AVG(i.tutar) AS ORTALAMA_TUTAR
FROM islem i
WHERE i.durum = 'BASARILI';
