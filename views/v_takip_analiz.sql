-- Takipteki hesaplar analizi
SELECT
  100.0 * SUM(CASE WHEN h.durum = 'TAKIPTE' THEN 1 ELSE 0 END)
        / COUNT(*) AS TAKIP_ORANI
FROM hesap h;
