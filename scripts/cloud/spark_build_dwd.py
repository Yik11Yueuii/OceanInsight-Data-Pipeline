from pyspark.sql import SparkSession
from pyspark.sql import functions as F

EXPECTED_VESSEL = 18638286
EXPECTED_MASTER = 149660

spark = (
    SparkSession.builder
    .appName("OceanInsightBuildDwd")
    .enableHiveSupport()
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

print(f"SPARK_VERSION={spark.version}", flush=True)
print(
    f"SPARK_MASTER={spark.sparkContext.master}",
    flush=True,
)
print(
    "SPARK_DEFAULT_PARALLELISM="
    f"{spark.sparkContext.defaultParallelism}",
    flush=True,
)

print("===== 1/3 构建海洋DWD =====", flush=True)

ocean_dwd = (
    spark.table("ocean_ods.ods_ocean_observation")
    .where(
        (F.col("quality_flag") == "VALID")
        & F.col("value").isNotNull()
    )
)

(
    ocean_dwd
    .coalesce(8)
    .write
    .format("parquet")
    .mode("overwrite")
    .saveAsTable("ocean_dwd.dwd_ocean_observation")
)

ocean_rows = spark.table(
    "ocean_dwd.dwd_ocean_observation"
).count()

print(f"DWD_OCEAN_ROWS={ocean_rows}", flush=True)

if not 0 < ocean_rows <= 3357840:
    raise RuntimeError(
        f"海洋DWD行数异常：{ocean_rows}"
    )

print("===== 2/3 构建船舶活动DWD =====", flush=True)

vessel_dwd = (
    spark.table("ocean_ods.ods_vessel_activity")
    .where(F.col("quality_flag") == "VALID")
)

(
    vessel_dwd
    .coalesce(8)
    .write
    .format("parquet")
    .mode("overwrite")
    .saveAsTable("ocean_dwd.dwd_vessel_activity")
)

vessel_rows = spark.table(
    "ocean_dwd.dwd_vessel_activity"
).count()

print(f"DWD_VESSEL_ROWS={vessel_rows}", flush=True)

if vessel_rows != EXPECTED_VESSEL:
    raise RuntimeError(
        f"船舶DWD行数异常：{vessel_rows}"
    )

print("===== 3/3 构建船舶主数据维表 =====", flush=True)

master_dwd = spark.table(
    "ocean_ods.ods_vessel_master"
)

(
    master_dwd
    .coalesce(1)
    .write
    .format("parquet")
    .mode("overwrite")
    .saveAsTable("ocean_dwd.dim_vessel_master")
)

master_stats = spark.table(
    "ocean_dwd.dim_vessel_master"
).agg(
    F.count("*").alias("rows"),
    F.countDistinct(
        "mmsi",
        "year",
    ).alias("distinct_keys"),
).first()

print(
    f"DWD_MASTER_ROWS={master_stats['rows']}",
    flush=True,
)
print(
    "DWD_MASTER_DISTINCT_KEYS="
    f"{master_stats['distinct_keys']}",
    flush=True,
)

if master_stats["rows"] != EXPECTED_MASTER:
    raise RuntimeError("船舶维表行数异常")

if master_stats["distinct_keys"] != EXPECTED_MASTER:
    raise RuntimeError("船舶维表存在重复业务键")

print("SPARK_DWD_BUILD=PASS", flush=True)

spark.stop()
