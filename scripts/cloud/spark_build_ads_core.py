from pyspark.sql import SparkSession
from pyspark.sql import functions as F

BATCH_ID = "student-ads-20260825"

spark = (
    SparkSession.builder
    .appName("OceanInsightBuildAdsCore")
    .enableHiveSupport()
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

print(f"SPARK_VERSION={spark.version}", flush=True)
print(
    f"SPARK_MASTER={spark.sparkContext.master}",
    flush=True,
)


def save_table(dataframe, table_name, partitions=4):
    (
        dataframe
        .coalesce(partitions)
        .write
        .format("parquet")
        .mode("overwrite")
        .saveAsTable(table_name)
    )


print("===== 1/5 构建海洋总览主题 =====", flush=True)

ocean_ods = spark.table(
    "ocean_ods.ods_ocean_observation"
)

valid_condition = (
    (F.col("quality_flag") == "VALID")
    & F.col("value").isNotNull()
)

monthly_overview = (
    ocean_ods
    .groupBy("year_month")
    .agg(
        F.count("*").alias("input_rows"),
        F.sum(
            F.when(valid_condition, 1).otherwise(0)
        ).alias("valid_rows"),
        F.countDistinct("grid_id").alias("grid_count"),
        F.countDistinct("indicator_code").alias(
            "indicator_count"
        ),
    )
    .withColumn("scope_type", F.lit("MONTH"))
)

all_overview = (
    ocean_ods
    .agg(
        F.count("*").alias("input_rows"),
        F.sum(
            F.when(valid_condition, 1).otherwise(0)
        ).alias("valid_rows"),
        F.countDistinct("grid_id").alias("grid_count"),
        F.countDistinct("indicator_code").alias(
            "indicator_count"
        ),
    )
    .withColumn("year_month", F.lit("ALL"))
    .withColumn("scope_type", F.lit("ALL"))
)

overview = (
    monthly_overview
    .unionByName(all_overview)
    .withColumn(
        "valid_rate",
        F.col("valid_rows") / F.col("input_rows"),
    )
    .withColumn("batch_id", F.lit(BATCH_ID))
    .select(
        "scope_type",
        "year_month",
        "input_rows",
        "valid_rows",
        "valid_rate",
        "grid_count",
        "indicator_count",
        "batch_id",
    )
)

save_table(
    overview,
    "ocean_ads.ads_ocean_overview",
    1,
)

overview_rows = spark.table(
    "ocean_ads.ads_ocean_overview"
).count()

print(
    f"ADS_OCEAN_OVERVIEW_ROWS={overview_rows}",
    flush=True,
)

if overview_rows != 61:
    raise RuntimeError(
        f"海洋总览预期61行，实际{overview_rows}行"
    )


print("===== 2/5 构建海洋月度网格主题 =====", flush=True)

ocean_monthly = (
    spark.table(
        "ocean_dws.dws_ocean_monthly_grid"
    )
    .withColumn("batch_id", F.lit(BATCH_ID))
)

save_table(
    ocean_monthly,
    "ocean_ads.ads_ocean_monthly_grid",
    4,
)

ocean_monthly_stats = spark.table(
    "ocean_ads.ads_ocean_monthly_grid"
).agg(
    F.count("*").alias("rows"),
    F.countDistinct(
        "year_month",
        "grid_id",
        "depth_level",
        "indicator_code",
    ).alias("distinct_keys"),
).first()

print(
    "ADS_OCEAN_MONTHLY_ROWS="
    f"{ocean_monthly_stats['rows']}",
    flush=True,
)
print(
    "ADS_OCEAN_MONTHLY_DISTINCT_KEYS="
    f"{ocean_monthly_stats['distinct_keys']}",
    flush=True,
)

if ocean_monthly_stats["rows"] != 721200:
    raise RuntimeError("海洋月度网格行数异常")

if (
    ocean_monthly_stats["distinct_keys"]
    != ocean_monthly_stats["rows"]
):
    raise RuntimeError("海洋月度网格业务键重复")


print("===== 3/5 构建海洋指标趋势主题 =====", flush=True)

ocean_trend = (
    spark.table(
        "ocean_dwd.dwd_ocean_observation"
    )
    .groupBy(
        "year_month",
        "depth_level",
        "indicator_code",
    )
    .agg(
        F.avg("value").alias("value_avg"),
        F.min("value").alias("value_min"),
        F.max("value").alias("value_max"),
        F.stddev_pop("value").alias("value_stddev"),
        F.countDistinct("grid_id").alias("valid_grids"),
        F.count("*").alias("sample_count"),
    )
    .withColumn("batch_id", F.lit(BATCH_ID))
)

save_table(
    ocean_trend,
    "ocean_ads.ads_ocean_indicator_trend",
    2,
)

trend_stats = spark.table(
    "ocean_ads.ads_ocean_indicator_trend"
).agg(
    F.count("*").alias("rows"),
    F.countDistinct(
        "year_month",
        "depth_level",
        "indicator_code",
    ).alias("distinct_keys"),
    F.sum("sample_count").alias("detail_rows"),
).first()

print(
    f"ADS_OCEAN_TREND_ROWS={trend_stats['rows']}",
    flush=True,
)
print(
    "ADS_OCEAN_TREND_DISTINCT_KEYS="
    f"{trend_stats['distinct_keys']}",
    flush=True,
)
print(
    "ADS_OCEAN_TREND_DETAIL_ROWS="
    f"{trend_stats['detail_rows']}",
    flush=True,
)

if trend_stats["rows"] != trend_stats["distinct_keys"]:
    raise RuntimeError("海洋趋势业务键重复")

if trend_stats["detail_rows"] != 2687015:
    raise RuntimeError("海洋趋势明细回卷不一致")


print("===== 4/5 构建船舶月度网格主题 =====", flush=True)

vessel_monthly = (
    spark.table(
        "ocean_dws.dws_vessel_monthly_grid"
    )
    .withColumn("batch_id", F.lit(BATCH_ID))
)

save_table(
    vessel_monthly,
    "ocean_ads.ads_vessel_monthly_grid",
    2,
)

vessel_monthly_stats = spark.table(
    "ocean_ads.ads_vessel_monthly_grid"
).agg(
    F.count("*").alias("rows"),
    F.countDistinct(
        "year_month",
        "grid_id",
    ).alias("distinct_keys"),
).first()

print(
    "ADS_VESSEL_MONTHLY_ROWS="
    f"{vessel_monthly_stats['rows']}",
    flush=True,
)
print(
    "ADS_VESSEL_MONTHLY_DISTINCT_KEYS="
    f"{vessel_monthly_stats['distinct_keys']}",
    flush=True,
)

if vessel_monthly_stats["rows"] != 7404:
    raise RuntimeError("船舶月度网格行数异常")

if (
    vessel_monthly_stats["distinct_keys"]
    != vessel_monthly_stats["rows"]
):
    raise RuntimeError("船舶月度网格业务键重复")


print("===== 5/5 构建海洋船舶关联主题 =====", flush=True)

ocean_for_relation = spark.table(
    "ocean_dws.dws_ocean_monthly_grid"
).alias("o")

vessel_for_relation = spark.table(
    "ocean_dws.dws_vessel_monthly_grid"
).alias("v")

relation = (
    ocean_for_relation
    .join(
        vessel_for_relation,
        on=[
            F.col("o.year_month")
            == F.col("v.year_month"),
            F.col("o.grid_id")
            == F.col("v.grid_id"),
        ],
        how="inner",
    )
    .select(
        F.col("o.year_month").alias("year_month"),
        F.col("o.grid_id").alias("grid_id"),
        F.col("o.depth_level").alias("depth_level"),
        F.col("o.indicator_code").alias(
            "indicator_code"
        ),
        F.col("o.value_avg").alias("ocean_value_avg"),
        F.col("o.value_min").alias("ocean_value_min"),
        F.col("o.value_max").alias("ocean_value_max"),
        F.col("o.sample_count").alias(
            "ocean_sample_count"
        ),
        F.col("v.active_vessels").alias(
            "active_vessels"
        ),
        F.col("v.activity_hours").alias(
            "activity_hours"
        ),
        F.col("v.fishing_hours").alias(
            "fishing_hours"
        ),
        F.col("v.record_count").alias(
            "vessel_record_count"
        ),
        F.lit(BATCH_ID).alias("batch_id"),
    )
)

save_table(
    relation,
    "ocean_ads.ads_ocean_vessel_relation",
    4,
)

relation_stats = spark.table(
    "ocean_ads.ads_ocean_vessel_relation"
).agg(
    F.count("*").alias("rows"),
    F.countDistinct(
        "year_month",
        "grid_id",
        "depth_level",
        "indicator_code",
    ).alias("distinct_keys"),
    F.min("ocean_sample_count").alias(
        "min_ocean_samples"
    ),
    F.min("active_vessels").alias(
        "min_active_vessels"
    ),
).first()

print(
    f"ADS_RELATION_ROWS={relation_stats['rows']}",
    flush=True,
)
print(
    "ADS_RELATION_DISTINCT_KEYS="
    f"{relation_stats['distinct_keys']}",
    flush=True,
)
print(
    "ADS_RELATION_MIN_OCEAN_SAMPLES="
    f"{relation_stats['min_ocean_samples']}",
    flush=True,
)
print(
    "ADS_RELATION_MIN_ACTIVE_VESSELS="
    f"{relation_stats['min_active_vessels']}",
    flush=True,
)

if not 0 < relation_stats["rows"] <= 1000000:
    raise RuntimeError("关联主题规模异常")

if (
    relation_stats["distinct_keys"]
    != relation_stats["rows"]
):
    raise RuntimeError("关联主题业务键重复")

if relation_stats["min_ocean_samples"] < 1:
    raise RuntimeError("关联主题存在空海洋样本")

if relation_stats["min_active_vessels"] < 1:
    raise RuntimeError("关联主题存在零船舶分组")

print("SPARK_ADS_CORE_BUILD=PASS", flush=True)

spark.stop()
