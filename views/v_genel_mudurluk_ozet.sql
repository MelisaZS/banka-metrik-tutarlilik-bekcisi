-- Genel müdürlük haftalık özeti
SELECT
  COUNT(DISTINCT CASE WHEN i.tarih >= date('now', '-30 day')
        THEN i.musteri_id END) AS AKTIF_MUSTERI,
  SUM(i.tutar) AS TOPLAM_HACIM
FROM islem i
WHERE i.durum = 'BASARILI';
