from pyspark.sql import SparkSession
from pyspark.sql import functions as F

EXPECTED_RECORDS = 18638286
EXPECTED_VESSEL_KEYS = 149660
BATCH_ID = "student-ads-20260825"

spark = (
    SparkSession.builder
    .appName("OceanInsightBuildAdsVesselClass")
    .enableHiveSupport()
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

print(f"SPARK_VERSION={spark.version}", flush=True)
print(
    f"SPARK_MASTER={spark.sparkContext.master}",
    flush=True,
)


def first_nonempty(*column_names):
    candidates = [
        F.when(
            F.length(F.trim(F.col(name))) > 0,
            F.trim(F.col(name)),
        )
        for name in column_names
    ]

    return F.coalesce(
        *candidates,
        F.lit("UNKNOWN"),
    )


def save_table(dataframe, table_name, partitions=1):
    (
        dataframe
        .coalesce(partitions)
        .write
        .format("parquet")
        .mode("overwrite")
        .saveAsTable(table_name)
    )


print(
    "===== 1/3 构建船旗国×船型年度DWS =====",
    flush=True,
)

activity = (
    spark.table("ocean_dwd.dwd_vessel_activity")
    .select(
        "mmsi",
        "year",
        "hours",
        "fishing_hours",
    )
)

master = (
    spark.table("ocean_dwd.dim_vessel_master")
    .select(
        "mmsi",
        "year",
        "flag_ais",
        "flag_registry",
        "flag_gfw",
        "vessel_class_inferred",
        "vessel_class_registry",
        "vessel_class_gfw",
    )
)

enriched = (
    activity
    .join(
        F.broadcast(master),
        on=["mmsi", "year"],
        how="inner",
    )
    .withColumn(
        "flag_code",
        first_nonempty(
            "flag_gfw",
            "flag_registry",
            "flag_ais",
        ),
    )
    .withColumn(
        "vessel_class",
        first_nonempty(
            "vessel_class_gfw",
            "vessel_class_registry",
            "vessel_class_inferred",
        ),
    )
)

flag_class_dws = (
    enriched
    .groupBy(
        "year",
        "flag_code",
        "vessel_class",
    )
    .agg(
        F.countDistinct("mmsi").alias(
            "active_vessels"
        ),
        F.sum("hours").alias("activity_hours"),
        F.sum("fishing_hours").alias(
            "fishing_hours"
        ),
        F.count("*").alias("record_count"),
    )
)

save_table(
    flag_class_dws,
    "ocean_dws.dws_vessel_flag_class_year",
    2,
)

base_stats = spark.table(
    "ocean_dws.dws_vessel_flag_class_year"
).agg(
    F.count("*").alias("rows"),
    F.countDistinct(
        "year",
        "flag_code",
        "vessel_class",
    ).alias("distinct_keys"),
    F.sum("record_count").alias("detail_rows"),
    F.sum("active_vessels").alias("vessel_keys"),
).first()

print(
    f"DWS_FLAG_CLASS_ROWS={base_stats['rows']}",
    flush=True,
)
print(
    "DWS_FLAG_CLASS_DISTINCT_KEYS="
    f"{base_stats['distinct_keys']}",
    flush=True,
)
print(
    "DWS_FLAG_CLASS_DETAIL_ROWS="
    f"{base_stats['detail_rows']}",
    flush=True,
)
print(
    "DWS_FLAG_CLASS_VESSEL_KEYS="
    f"{base_stats['vessel_keys']}",
    flush=True,
)

if base_stats["rows"] != base_stats["distinct_keys"]:
    raise RuntimeError("船旗国船型DWS业务键重复")

if base_stats["detail_rows"] != EXPECTED_RECORDS:
    raise RuntimeError("船旗国船型DWS明细回卷不一致")

if base_stats["vessel_keys"] != EXPECTED_VESSEL_KEYS:
    raise RuntimeError("船旗国船型DWS船舶键不一致")


print("===== 2/3 构建船旗国年度ADS =====", flush=True)

flag_ads = (
    spark.table(
        "ocean_dws.dws_vessel_flag_class_year"
    )
    .groupBy(
        "year",
        "flag_code",
    )
    .agg(
        F.sum("active_vessels").alias(
            "active_vessels"
        ),
        F.sum("activity_hours").alias(
            "activity_hours"
        ),
        F.sum("fishing_hours").alias(
            "fishing_hours"
        ),
        F.sum("record_count").alias(
            "record_count"
        ),
    )
    .withColumn("batch_id", F.lit(BATCH_ID))
)

save_table(
    flag_ads,
    "ocean_ads.ads_vessel_flag_year",
    1,
)

flag_stats = spark.table(
    "ocean_ads.ads_vessel_flag_year"
).agg(
    F.count("*").alias("rows"),
    F.countDistinct(
        "year",
        "flag_code",
    ).alias("distinct_keys"),
    F.sum("record_count").alias("detail_rows"),
    F.sum("active_vessels").alias("vessel_keys"),
).first()

print(
    f"ADS_VESSEL_FLAG_ROWS={flag_stats['rows']}",
    flush=True,
)
print(
    "ADS_VESSEL_FLAG_DISTINCT_KEYS="
    f"{flag_stats['distinct_keys']}",
    flush=True,
)
print(
    "ADS_VESSEL_FLAG_DETAIL_ROWS="
    f"{flag_stats['detail_rows']}",
    flush=True,
)
print(
    "ADS_VESSEL_FLAG_VESSEL_KEYS="
    f"{flag_stats['vessel_keys']}",
    flush=True,
)

if flag_stats["rows"] != flag_stats["distinct_keys"]:
    raise RuntimeError("船旗国ADS业务键重复")

if flag_stats["detail_rows"] != EXPECTED_RECORDS:
    raise RuntimeError("船旗国ADS明细回卷不一致")

if flag_stats["vessel_keys"] != EXPECTED_VESSEL_KEYS:
    raise RuntimeError("船旗国ADS船舶键不一致")


print("===== 3/3 构建船型年度ADS =====", flush=True)

class_ads = (
    spark.table(
        "ocean_dws.dws_vessel_flag_class_year"
    )
    .groupBy(
        "year",
        "vessel_class",
    )
    .agg(
        F.sum("active_vessels").alias(
            "active_vessels"
        ),
        F.sum("activity_hours").alias(
            "activity_hours"
        ),
        F.sum("fishing_hours").alias(
            "fishing_hours"
        ),
        F.sum("record_count").alias(
            "record_count"
        ),
    )
    .withColumn("batch_id", F.lit(BATCH_ID))
)

save_table(
    class_ads,
    "ocean_ads.ads_vessel_class_year",
    1,
)

class_stats = spark.table(
    "ocean_ads.ads_vessel_class_year"
).agg(
    F.count("*").alias("rows"),
    F.countDistinct(
        "year",
        "vessel_class",
    ).alias("distinct_keys"),
    F.sum("record_count").alias("detail_rows"),
    F.sum("active_vessels").alias("vessel_keys"),
).first()

print(
    f"ADS_VESSEL_CLASS_ROWS={class_stats['rows']}",
    flush=True,
)
print(
    "ADS_VESSEL_CLASS_DISTINCT_KEYS="
    f"{class_stats['distinct_keys']}",
    flush=True,
)
print(
    "ADS_VESSEL_CLASS_DETAIL_ROWS="
    f"{class_stats['detail_rows']}",
    flush=True,
)
print(
    "ADS_VESSEL_CLASS_VESSEL_KEYS="
    f"{class_stats['vessel_keys']}",
    flush=True,
)

if class_stats["rows"] != class_stats["distinct_keys"]:
    raise RuntimeError("船型ADS业务键重复")

if class_stats["detail_rows"] != EXPECTED_RECORDS:
    raise RuntimeError("船型ADS明细回卷不一致")

if class_stats["vessel_keys"] != EXPECTED_VESSEL_KEYS:
    raise RuntimeError("船型ADS船舶键不一致")

print("SPARK_ADS_VESSEL_CLASS_BUILD=PASS", flush=True)

spark.stop()
