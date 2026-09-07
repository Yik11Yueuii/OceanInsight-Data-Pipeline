-- 仅在已经确定 FineBI 出口公网 IP 后，由管理员替换占位符并执行。
-- 禁止使用 '%'、0.0.0.0/0，禁止复用 ads_writer。
CREATE USER IF NOT EXISTS 'finebi_reader'@'<FINEBI_SOURCE_IP>' IDENTIFIED BY '<RANDOM_STRONG_PASSWORD>';
GRANT SELECT ON ocean_insight_ads.* TO 'finebi_reader'@'<FINEBI_SOURCE_IP>';
ALTER USER 'finebi_reader'@'<FINEBI_SOURCE_IP>' WITH MAX_USER_CONNECTIONS 5;
FLUSH PRIVILEGES;

-- 验收：SHOW GRANTS 输出只能包含 USAGE 与 ocean_insight_ads.* 的 SELECT。
SHOW GRANTS FOR 'finebi_reader'@'<FINEBI_SOURCE_IP>';
