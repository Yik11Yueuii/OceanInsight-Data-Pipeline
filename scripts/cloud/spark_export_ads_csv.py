import hashlib
import json
import shutil
from pathlib import Path

from pyspark.sql import SparkSession

BATCH_ID = "student-ads-20260825"

OUTPUT_ROOT = Path(
    "/home/ecs-user/oceaninsight-project1/output/ads_csv"
)
STAGE_ROOT = Path(
    "/home/ecs-user/oceaninsight-project1/output/ads_csv_stage"
)

TABLES = {
    "ads_ocean_overview": 61,
    "ads_ocean_monthly_grid": 721200,
    "ads_ocean_indicator_trend": 2220,
    "ads_vessel_monthly_grid": 7404,
    "ads_ocean_vessel_relation": 226192,
    "ads_vessel_flag_year": 687,
    "ads_vessel_class_year": 80,
}

spark = (
    SparkSession.builder
    .appName("OceanInsightExportAdsCsv")
    .enableHiveSupport()
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
STAGE_ROOT.mkdir(parents=True, exist_ok=True)

manifest_tables = []

for number, (table_name, expected_rows) in enumerate(
    TABLES.items(),
    start=1,
):
    full_table_name = f"ocean_ads.{table_name}"
    stage_path = STAGE_ROOT / table_name
    final_path = OUTPUT_ROOT / f"{table_name}.csv"
    final_tmp = OUTPUT_ROOT / f"{table_name}.csv.tmp"

    print(
        f"===== CSV {number}/{len(TABLES)} "
        f"导出 {table_name} =====",
        flush=True,
    )

    dataframe = spark.table(full_table_name)
    row_count = dataframe.count()

    if row_count != expected_rows:
        raise RuntimeError(
            f"{table_name}预期{expected_rows}行，"
            f"实际{row_count}行"
        )

    (
        dataframe
        .coalesce(1)
        .write
        .mode("overwrite")
        .option("header", True)
        .option("encoding", "UTF-8")
        .csv(stage_path.as_uri())
    )

    part_files = list(stage_path.glob("part-*.csv"))

    if len(part_files) != 1:
        raise RuntimeError(
            f"{table_name}未生成唯一CSV分片："
            f"{part_files}"
        )

    shutil.copy2(part_files[0], final_tmp)
    final_tmp.replace(final_path)

    sha256 = hashlib.sha256()
    line_count = 0

    with final_path.open("rb") as source:
        for block in iter(
            lambda: source.read(1024 * 1024),
            b"",
        ):
            sha256.update(block)
            line_count += block.count(b"\n")

    if line_count != row_count + 1:
        raise RuntimeError(
            f"{table_name}预期CSV行数"
            f"{row_count + 1}，实际{line_count}"
        )

    item = {
        "table": full_table_name,
        "file": str(final_path),
        "rows": row_count,
        "csv_lines": line_count,
        "bytes": final_path.stat().st_size,
        "sha256": sha256.hexdigest(),
        "batch_id": BATCH_ID,
    }

    manifest_tables.append(item)

    print(
        f"CSV_TABLE={table_name} "
        f"ROWS={row_count} "
        f"LINES={line_count} "
        f"BYTES={item['bytes']}",
        flush=True,
    )

manifest = {
    "batch_id": BATCH_ID,
    "table_count": len(manifest_tables),
    "tables": manifest_tables,
}

manifest_path = OUTPUT_ROOT / "ads_csv_manifest.json"
manifest_tmp = OUTPUT_ROOT / "ads_csv_manifest.json.tmp"

manifest_tmp.write_text(
    json.dumps(
        manifest,
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)

manifest_tmp.replace(manifest_path)

print(
    f"ADS_CSV_TABLE_COUNT={len(manifest_tables)}",
    flush=True,
)
print(f"ADS_CSV_MANIFEST={manifest_path}", flush=True)
print("SPARK_ADS_CSV_EXPORT=PASS", flush=True)

spark.stop()
