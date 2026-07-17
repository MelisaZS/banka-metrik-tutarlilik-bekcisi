-- Aktif müşteri raporu (CRM ekibi)
SELECT
  COUNT(DISTINCT CASE WHEN i.tarih >= date('now', '-90 day')
        THEN i.musteri_id END) AS AKTIF_MUSTERI,
  COUNT(*) AS ISLEM_ADEDI
FROM islem i
WHERE i.durum = 'BASARILI';
