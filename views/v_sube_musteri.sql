-- Şube bazlı müşteri raporu
SELECT
  COUNT(m.musteri_id) AS TOPLAM_MUSTERI
FROM musteri m
JOIN hesap h ON h.musteri_id = m.musteri_id
WHERE m.durum = 'AKTIF';
