-- Risk izleme raporu
SELECT
  100.0 * SUM(CASE WHEN h.durum = 'TAKIPTE' THEN 1 ELSE 0 END)
        / SUM(CASE WHEN h.durum <> 'KAPALI' THEN 1 ELSE 0 END) AS TAKIP_ORANI
FROM hesap h;
