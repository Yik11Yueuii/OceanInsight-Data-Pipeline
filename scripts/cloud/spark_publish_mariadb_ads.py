import configparser
from pathlib import Path

from pyspark.sql import SparkSession

TABLES = [
    (
        "ads_ocean_monthly_grid",
        721200,
        2,
    ),
    (
        "ads_ocean_indicator_trend",
        2220,
        1,
    ),
    (
        "ads_vessel_monthly_grid",
        7404,
        1,
    ),
    (
        "ads_ocean_vessel_relation",
        226192,
        2,
    ),
    (
        "ads_vessel_flag_year",
        687,
        1,
    ),
    (
        "ads_vessel_class_year",
        80,
        1,
    ),
]

cnf_path = (
    Path.home()
    / ".config/oceaninsight/ads-db.cnf"
)

config = configparser.RawConfigParser()
loaded = config.read(cnf_path, encoding="utf-8")

if not loaded or not config.has_section("client"):
    raise RuntimeError("无法读取ADS私有配置")

client = config["client"]

host = client.get("host", "127.0.0.1")
port = client.get("port", "3306")
user = client.get("user")
password = client.get("password")

if not user or not password:
    raise RuntimeError("ADS私有配置缺少账户信息")

jdbc_url = (
    f"jdbc:mysql://{host}:{port}/ocean_insight_ads"
    "?useSSL=false"
    "&allowPublicKeyRetrieval=true"
    "&serverTimezone=Asia%2FShanghai"
    "&rewriteBatchedStatements=true"
)

properties = {
    "user": user,
    "password": password,
    "driver": "com.mysql.cj.jdbc.Driver",
    "batchsize": "5000",
    "isolationLevel": "READ_COMMITTED",
}

spark = (
    SparkSession.builder
    .appName("OceanInsightPublishMariaDbAds")
    .enableHiveSupport()
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

for number, (
    table_name,
    expected_rows,
    partitions,
) in enumerate(TABLES, start=1):
    print(
        f"===== JDBC {number}/{len(TABLES)} "
        f"发布 {table_name} =====",
        flush=True,
    )

    source = spark.table(
        f"ocean_ads.{table_name}"
    )

    source_rows = source.count()

    print(
        f"JDBC_SOURCE_TABLE={table_name} "
        f"ROWS={source_rows}",
        flush=True,
    )

    if source_rows != expected_rows:
        raise RuntimeError(
            f"{table_name}预期{expected_rows}行，"
            f"实际{source_rows}行"
        )

    (
        source
        .coalesce(partitions)
        .write
        .mode("append")
        .jdbc(
            url=jdbc_url,
            table=table_name,
            properties=properties,
        )
    )

    print(
        f"JDBC_WRITE_TABLE={table_name} "
        f"ROWS={source_rows} PASS",
        flush=True,
    )

print("SPARK_JDBC_ADS_ALL_WRITE=PASS", flush=True)

spark.stop()
