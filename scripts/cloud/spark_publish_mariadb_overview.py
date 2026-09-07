import configparser
from pathlib import Path

from pyspark.sql import SparkSession

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

spark = (
    SparkSession.builder
    .appName("OceanInsightMariaDbOverviewVerify")
    .enableHiveSupport()
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

source = spark.table(
    "ocean_ads.ads_ocean_overview"
)

source_rows = source.count()

print(
    f"HIVE_OVERVIEW_ROWS={source_rows}",
    flush=True,
)

if source_rows != 61:
    raise RuntimeError("Hive总览表行数异常")

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
    "batchsize": "1000",
    "isolationLevel": "READ_COMMITTED",
}

(
    source
    .coalesce(1)
    .write
    .mode("append")
    .jdbc(
        url=jdbc_url,
        table="ads_ocean_overview",
        properties=properties,
    )
)

print(
    "SPARK_JDBC_OVERVIEW_WRITE=PASS",
    flush=True,
)

spark.stop()
