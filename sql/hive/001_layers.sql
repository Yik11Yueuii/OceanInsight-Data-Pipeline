-- OceanInsight 项目一最终 Hive 4 层定义。
-- DataX 已跳过 CSV 表头，因此 ODS 不设置 skip.header.line.count。
CREATE DATABASE IF NOT EXISTS ocean_ods LOCATION '/oceaninsight/ods';
CREATE DATABASE IF NOT EXISTS ocean_dwd LOCATION '/oceaninsight/dwd';
CREATE DATABASE IF NOT EXISTS ocean_dws LOCATION '/oceaninsight/dws';
CREATE DATABASE IF NOT EXISTS ocean_ads LOCATION '/oceaninsight/ads';

CREATE EXTERNAL TABLE IF NOT EXISTS ocean_ods.ods_ocean_observation (
  year_month STRING, indicator_code STRING, depth_m DOUBLE, depth_level STRING,
  source_lat DOUBLE, source_lon DOUBLE, grid_lat DOUBLE, grid_lon DOUBLE,
  grid_id STRING, value DOUBLE, unit STRING, quality_flag STRING,
  source_file STRING, batch_id STRING
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
STORED AS TEXTFILE LOCATION '/oceaninsight/ods/ocean_observation';

CREATE EXTERNAL TABLE IF NOT EXISTS ocean_ods.ods_vessel_activity (
  observation_date STRING, year INT, month INT, year_month STRING,
  source_grid_lat DOUBLE, source_grid_lon DOUBLE, grid_lat DOUBLE, grid_lon DOUBLE,
  grid_id STRING, mmsi BIGINT, hours DOUBLE, fishing_hours DOUBLE,
  quality_flag STRING, source_file STRING, batch_id STRING
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
STORED AS TEXTFILE LOCATION '/oceaninsight/ods/vessel_activity';

CREATE EXTERNAL TABLE IF NOT EXISTS ocean_ods.ods_vessel_master (
  mmsi BIGINT, year INT, imo STRING, shipname STRING, callsign STRING,
  flag_gfw STRING, flag_registry STRING, flag_ais STRING,
  vessel_class_gfw STRING, vessel_class_registry STRING, vessel_class_inferred STRING,
  self_reported_fishing_vessel STRING, length_m DOUBLE, tonnage_gt DOUBLE,
  engine_power_kw DOUBLE, registered_gear_type STRING, inferred_gear_type STRING,
  registry_public_authorization STRING, registry_data_source STRING,
  registry_record_id STRING, first_timestamp STRING, last_timestamp STRING,
  batch_id STRING, source_file STRING
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
STORED AS TEXTFILE LOCATION '/oceaninsight/ods/vessel_master';

-- DWD/DWS/ADS 由 scripts/cloud/spark_build_*.py 以 Parquet 写入并注册。
-- 本机实测类型是 EXTERNAL_TABLE；不要强制改成 MANAGED_TABLE。
