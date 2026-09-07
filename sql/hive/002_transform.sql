-- 项目一最终只读验收 SQL。构建由已实测 Spark 脚本完成，本文件不重复写表。
SELECT 'ods_ocean_observation' AS table_name, COUNT(*) AS row_count FROM ocean_ods.ods_ocean_observation
UNION ALL SELECT 'ods_vessel_activity', COUNT(*) FROM ocean_ods.ods_vessel_activity
UNION ALL SELECT 'ods_vessel_master', COUNT(*) FROM ocean_ods.ods_vessel_master;

SELECT 'dwd_ocean_observation' AS table_name, COUNT(*) AS row_count FROM ocean_dwd.dwd_ocean_observation
UNION ALL SELECT 'dwd_vessel_activity', COUNT(*) FROM ocean_dwd.dwd_vessel_activity
UNION ALL SELECT 'dim_vessel_master', COUNT(*) FROM ocean_dwd.dim_vessel_master;

SELECT 'dws_ocean_monthly_grid' AS table_name, COUNT(*) AS row_count FROM ocean_dws.dws_ocean_monthly_grid
UNION ALL SELECT 'dws_vessel_monthly_grid', COUNT(*) FROM ocean_dws.dws_vessel_monthly_grid
UNION ALL SELECT 'dws_vessel_flag_class_year', COUNT(*) FROM ocean_dws.dws_vessel_flag_class_year;

SELECT 'ads_ocean_overview' AS table_name, COUNT(*) AS row_count FROM ocean_ads.ads_ocean_overview
UNION ALL SELECT 'ads_ocean_monthly_grid', COUNT(*) FROM ocean_ads.ads_ocean_monthly_grid
UNION ALL SELECT 'ads_ocean_indicator_trend', COUNT(*) FROM ocean_ads.ads_ocean_indicator_trend
UNION ALL SELECT 'ads_vessel_monthly_grid', COUNT(*) FROM ocean_ads.ads_vessel_monthly_grid
UNION ALL SELECT 'ads_ocean_vessel_relation', COUNT(*) FROM ocean_ads.ads_ocean_vessel_relation
UNION ALL SELECT 'ads_vessel_flag_year', COUNT(*) FROM ocean_ads.ads_vessel_flag_year
UNION ALL SELECT 'ads_vessel_class_year', COUNT(*) FROM ocean_ads.ads_vessel_class_year;
