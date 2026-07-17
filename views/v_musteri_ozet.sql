-- Müşteri özet raporu
SELECT
  COUNT(DISTINCT m.musteri_id) AS TOPLAM_MUSTERI
FROM musteri m
JOIN hesap h ON h.musteri_id = m.musteri_id
WHERE m.durum = 'AKTIF';
