CREATE DATABASE IF NOT EXISTS ocean_insight_ads
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ocean_insight_ads;

CREATE TABLE IF NOT EXISTS ads_ocean_overview (
  scope_type VARCHAR(16) NOT NULL,
  `year_month` CHAR(7) NOT NULL,
  input_rows BIGINT NOT NULL,
  valid_rows BIGINT NOT NULL,
  valid_rate DOUBLE NOT NULL,
  grid_count BIGINT NOT NULL,
  indicator_count BIGINT NOT NULL,
  batch_id VARCHAR(64) NOT NULL,
  refreshed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (scope_type, `year_month`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS ads_ocean_monthly_grid (
  `year_month` CHAR(7) NOT NULL,
  grid_id VARCHAR(32) NOT NULL,
  depth_level VARCHAR(16) NOT NULL,
  indicator_code VARCHAR(32) NOT NULL,
  value_avg DOUBLE,
  value_min DOUBLE,
  value_max DOUBLE,
  sample_count BIGINT NOT NULL,
  batch_id VARCHAR(64) NOT NULL,
  refreshed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`year_month`, grid_id, depth_level, indicator_code)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS ads_ocean_indicator_trend (
  `year_month` CHAR(7) NOT NULL,
  depth_level VARCHAR(16) NOT NULL,
  indicator_code VARCHAR(32) NOT NULL,
  value_avg DOUBLE,
  value_min DOUBLE,
  value_max DOUBLE,
  value_stddev DOUBLE,
  valid_grids BIGINT NOT NULL,
  sample_count BIGINT NOT NULL,
  batch_id VARCHAR(64) NOT NULL,
  refreshed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`year_month`, depth_level, indicator_code)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS ads_vessel_monthly_grid (
  `year_month` CHAR(7) NOT NULL,
  grid_id VARCHAR(32) NOT NULL,
  active_vessels BIGINT NOT NULL,
  activity_hours DOUBLE NOT NULL,
  fishing_hours DOUBLE NOT NULL,
  record_count BIGINT NOT NULL,
  batch_id VARCHAR(64) NOT NULL,
  refreshed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`year_month`, grid_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS ads_ocean_vessel_relation (
  `year_month` CHAR(7) NOT NULL,
  grid_id VARCHAR(32) NOT NULL,
  depth_level VARCHAR(16) NOT NULL,
  indicator_code VARCHAR(32) NOT NULL,
  ocean_value_avg DOUBLE,
  ocean_value_min DOUBLE,
  ocean_value_max DOUBLE,
  ocean_sample_count BIGINT NOT NULL,
  active_vessels BIGINT NOT NULL,
  activity_hours DOUBLE NOT NULL,
  fishing_hours DOUBLE NOT NULL,
  vessel_record_count BIGINT NOT NULL,
  batch_id VARCHAR(64) NOT NULL,
  refreshed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`year_month`, grid_id, depth_level, indicator_code)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS ads_vessel_flag_year (
  year INT NOT NULL,
  flag_code VARCHAR(64) NOT NULL,
  active_vessels BIGINT NOT NULL,
  activity_hours DOUBLE NOT NULL,
  fishing_hours DOUBLE NOT NULL,
  record_count BIGINT NOT NULL,
  batch_id VARCHAR(64) NOT NULL,
  refreshed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (year, flag_code)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS ads_vessel_class_year (
  year INT NOT NULL,
  vessel_class VARCHAR(64) NOT NULL,
  active_vessels BIGINT NOT NULL,
  activity_hours DOUBLE NOT NULL,
  fishing_hours DOUBLE NOT NULL,
  record_count BIGINT NOT NULL,
  batch_id VARCHAR(64) NOT NULL,
  refreshed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (year, vessel_class)
) ENGINE=InnoDB;
