from pyspark.sql import SparkSession
from pyspark.sql import functions as F

EXPECTED_OCEAN = 3357840
EXPECTED_VESSEL = 18638286
EXPECTED_MASTER = 149660

spark = (
    SparkSession.builder
    .appName("OceanInsightHiveOdsVerify")
    .enableHiveSupport()
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

print(f"SPARK_VERSION={spark.version}")
print(
    "SPARK_MASTER="
    f"{spark.sparkContext.master}"
)
print(
    "SPARK_DEFAULT_PARALLELISM="
    f"{spark.sparkContext.defaultParallelism}"
)
print(
    "SPARK_SQL_SHUFFLE_PARTITIONS="
    f"{spark.conf.get('spark.sql.shuffle.partitions')}"
)

ocean = spark.table(
    "ocean_ods.ods_ocean_observation"
)

ocean_stats = ocean.agg(
    F.count("*").alias("rows"),
    F.sum(
        F.when(
            F.col("quality_flag").isNull()
            | ~F.col("quality_flag").isin(
                "VALID",
                "MISSING",
            ),
            1,
        ).otherwise(0)
    ).alias("bad_quality"),
    F.sum(
        F.when(
            F.col("year_month").isNull()
            | F.col("indicator_code").isNull()
            | F.col("grid_id").isNull(),
            1,
        ).otherwise(0)
    ).alias("bad_keys"),
    F.sum(
        F.when(
            (
                (F.col("quality_flag") == "MISSING")
                & F.col("value").isNotNull()
            )
            | (
                (F.col("quality_flag") == "VALID")
                & F.col("value").isNull()
            ),
            1,
        ).otherwise(0)
    ).alias("value_flag_mismatch"),
).first()

print(f"OCEAN_ROWS={ocean_stats['rows']}")
print(
    "OCEAN_BAD_QUALITY="
    f"{ocean_stats['bad_quality']}"
)
print(f"OCEAN_BAD_KEYS={ocean_stats['bad_keys']}")
print(
    "OCEAN_VALUE_FLAG_MISMATCH="
    f"{ocean_stats['value_flag_mismatch']}"
)

vessel = spark.table(
    "ocean_ods.ods_vessel_activity"
)

vessel_stats = vessel.agg(
    F.count("*").alias("rows"),
    F.sum(
        F.when(
            F.col("quality_flag").isNull()
            | (F.col("quality_flag") != "VALID"),
            1,
        ).otherwise(0)
    ).alias("bad_quality"),
    F.sum(
        F.when(
            F.col("observation_date").isNull()
            | F.col("year_month").isNull()
            | F.col("grid_id").isNull()
            | F.col("mmsi").isNull(),
            1,
        ).otherwise(0)
    ).alias("bad_keys"),
).first()

print(f"VESSEL_ROWS={vessel_stats['rows']}")
print(
    "VESSEL_BAD_QUALITY="
    f"{vessel_stats['bad_quality']}"
)
print(f"VESSEL_BAD_KEYS={vessel_stats['bad_keys']}")

master = spark.table(
    "ocean_ods.ods_vessel_master"
)

master_stats = master.agg(
    F.count("*").alias("rows"),
    F.countDistinct(
        "mmsi",
        "year",
    ).alias("distinct_keys"),
    F.sum(
        F.when(
            F.col("batch_id")
            != "student-vessel-master",
            1,
        ).otherwise(0)
    ).alias("bad_batch"),
    F.sum(
        F.when(
            F.col("source_file")
            != "vessel_master.csv",
            1,
        ).otherwise(0)
    ).alias("bad_source"),
).first()

print(f"MASTER_ROWS={master_stats['rows']}")
print(
    "MASTER_DISTINCT_KEYS="
    f"{master_stats['distinct_keys']}"
)
print(
    "MASTER_BAD_BATCH="
    f"{master_stats['bad_batch']}"
)
print(
    "MASTER_BAD_SOURCE="
    f"{master_stats['bad_source']}"
)

assert ocean_stats["rows"] == EXPECTED_OCEAN
assert ocean_stats["bad_quality"] == 0
assert ocean_stats["bad_keys"] == 0
assert ocean_stats["value_flag_mismatch"] == 0

assert vessel_stats["rows"] == EXPECTED_VESSEL
assert vessel_stats["bad_quality"] == 0
assert vessel_stats["bad_keys"] == 0

assert master_stats["rows"] == EXPECTED_MASTER
assert master_stats["distinct_keys"] == EXPECTED_MASTER
assert master_stats["bad_batch"] == 0
assert master_stats["bad_source"] == 0

print("SPARK_HIVE_ODS_VERIFY=PASS")

spark.stop()
