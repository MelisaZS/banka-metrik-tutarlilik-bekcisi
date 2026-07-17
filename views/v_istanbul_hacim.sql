-- İstanbul bölge hacim raporu (şube lokasyonuna göre)
SELECT
  SUM(CASE WHEN s.il = 'İstanbul' THEN i.tutar ELSE 0 END) AS ISTANBUL_HACIM
FROM islem i
JOIN sube s ON s.sube_id = i.sube_id
WHERE i.durum = 'BASARILI';
