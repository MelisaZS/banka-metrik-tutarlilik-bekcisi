-- Şube performans karnesi
SELECT
  COUNT(CASE WHEN i.tarih >= date('now', '-90 day')
        THEN i.musteri_id END) AS AKTIF_MUSTERI,
  COUNT(DISTINCT i.sube_id) AS SUBE_SAYISI
FROM islem i
WHERE i.durum = 'BASARILI';
