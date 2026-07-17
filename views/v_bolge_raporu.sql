-- Bölge raporu (müşteri ikametine göre)
SELECT
  SUM(CASE WHEN m.il = 'İstanbul' THEN i.tutar ELSE 0 END) AS ISTANBUL_HACIM
FROM islem i
JOIN musteri m ON m.musteri_id = i.musteri_id
WHERE i.durum = 'BASARILI';
