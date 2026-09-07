from pyspark.sql import SparkSession
from pyspark.sql import functions as F

EXPECTED_OCEAN_DETAIL = 2687015
EXPECTED_VESSEL_DETAIL = 18638286

spark = (
    SparkSession.builder
    .appName("OceanInsightBuildDws")
    .enableHiveSupport()
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

print(f"SPARK_VERSION={spark.version}", flush=True)
print(
    f"SPARK_MASTER={spark.sparkContext.master}",
    flush=True,
)

print("===== 1/2 构建海洋月度网格DWS =====", flush=True)

ocean_dws = (
    spark.table("ocean_dwd.dwd_ocean_observation")
    .groupBy(
        "year_month",
        "grid_id",
        "depth_level",
        "indicator_code",
    )
    .agg(
        F.avg("value").alias("value_avg"),
        F.min("value").alias("value_min"),
        F.max("value").alias("value_max"),
        F.count("*").alias("sample_count"),
    )
)

(
    ocean_dws
    .coalesce(4)
    .write
    .format("parquet")
    .mode("overwrite")
    .saveAsTable("ocean_dws.dws_ocean_monthly_grid")
)

ocean_stats = spark.table(
    "ocean_dws.dws_ocean_monthly_grid"
).agg(
    F.count("*").alias("rows"),
    F.countDistinct(
        "year_month",
        "grid_id",
        "depth_level",
        "indicator_code",
    ).alias("distinct_keys"),
    F.sum("sample_count").alias("detail_rows"),
    F.min("sample_count").alias("min_samples"),
).first()

print(f"DWS_OCEAN_ROWS={ocean_stats['rows']}", flush=True)
print(
    "DWS_OCEAN_DISTINCT_KEYS="
    f"{ocean_stats['distinct_keys']}",
    flush=True,
)
print(
    "DWS_OCEAN_DETAIL_ROWS="
    f"{ocean_stats['detail_rows']}",
    flush=True,
)
print(
    "DWS_OCEAN_MIN_SAMPLES="
    f"{ocean_stats['min_samples']}",
    flush=True,
)

if not 0 < ocean_stats["rows"] <= 1000000:
    raise RuntimeError("海洋DWS结果规模异常")

if ocean_stats["distinct_keys"] != ocean_stats["rows"]:
    raise RuntimeError("海洋DWS业务键重复")

if ocean_stats["detail_rows"] != EXPECTED_OCEAN_DETAIL:
    raise RuntimeError("海洋DWS明细汇总行数不一致")

if ocean_stats["min_samples"] < 1:
    raise RuntimeError("海洋DWS存在空分组")

print("===== 2/2 构建船舶月度网格DWS =====", flush=True)

vessel_dws = (
    spark.table("ocean_dwd.dwd_vessel_activity")
    .groupBy(
        "year_month",
        "grid_id",
    )
    .agg(
        F.countDistinct("mmsi").alias("active_vessels"),
        F.sum("hours").alias("activity_hours"),
        F.sum("fishing_hours").alias("fishing_hours"),
        F.count("*").alias("record_count"),
    )
)

(
    vessel_dws
    .coalesce(4)
    .write
    .format("parquet")
    .mode("overwrite")
    .saveAsTable("ocean_dws.dws_vessel_monthly_grid")
)

vessel_stats = spark.table(
    "ocean_dws.dws_vessel_monthly_grid"
).agg(
    F.count("*").alias("rows"),
    F.countDistinct(
        "year_month",
        "grid_id",
    ).alias("distinct_keys"),
    F.sum("record_count").alias("detail_rows"),
    F.min("active_vessels").alias("min_vessels"),
    F.min("record_count").alias("min_records"),
).first()

print(
    f"DWS_VESSEL_ROWS={vessel_stats['rows']}",
    flush=True,
)
print(
    "DWS_VESSEL_DISTINCT_KEYS="
    f"{vessel_stats['distinct_keys']}",
    flush=True,
)
print(
    "DWS_VESSEL_DETAIL_ROWS="
    f"{vessel_stats['detail_rows']}",
    flush=True,
)
print(
    "DWS_VESSEL_MIN_VESSELS="
    f"{vessel_stats['min_vessels']}",
    flush=True,
)
print(
    "DWS_VESSEL_MIN_RECORDS="
    f"{vessel_stats['min_records']}",
    flush=True,
)

if not 0 < vessel_stats["rows"] <= 1000000:
    raise RuntimeError("船舶DWS结果规模异常")

if vessel_stats["distinct_keys"] != vessel_stats["rows"]:
    raise RuntimeError("船舶DWS业务键重复")

if vessel_stats["detail_rows"] != EXPECTED_VESSEL_DETAIL:
    raise RuntimeError("船舶DWS明细汇总行数不一致")

if vessel_stats["min_vessels"] < 1:
    raise RuntimeError("船舶DWS存在零船舶分组")

if vessel_stats["min_records"] < 1:
    raise RuntimeError("船舶DWS存在空分组")

print("SPARK_DWS_BUILD=PASS", flush=True)

spark.stop()
