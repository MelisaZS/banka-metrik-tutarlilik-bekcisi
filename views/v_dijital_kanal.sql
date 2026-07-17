-- Dijital kanal raporu
SELECT
  100.0 * SUM(CASE WHEN i.kanal IN ('MOBIL', 'INTERNET') THEN 1 ELSE 0 END)
        / COUNT(*) AS DIJITAL_ORAN
FROM islem i
WHERE i.durum = 'BASARILI';
