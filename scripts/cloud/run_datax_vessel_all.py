#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

CSV_ROOT = Path(
    "/home/ecs-user/oceaninsight-project1/output/ods/vessel"
)
JOB_ROOT = Path(
    "/data/oceaninsight/datax/jobs/vessel_all"
)
LOG_ROOT = Path(
    "/data/oceaninsight/datax/logs/vessel_all"
)
HDFS_DIR = "/oceaninsight/ods/vessel_activity"
DATAX = "/usr/local/bin/datax"

COLUMNS = [
    "observation_date",
    "year",
    "month",
    "year_month",
    "source_grid_lat",
    "source_grid_lon",
    "grid_lat",
    "grid_lon",
    "grid_id",
    "mmsi",
    "hours",
    "fishing_hours",
    "quality_flag",
    "source_file",
    "batch_id",
]


def hdfs_listing():
    return subprocess.run(
        ["hdfs", "dfs", "-ls", HDFS_DIR],
        text=True,
        capture_output=True,
        check=False,
    )


def hdfs_prefix_exists(prefix):
    result = hdfs_listing()

    if result.returncode != 0:
        raise RuntimeError(
            "无法读取HDFS目录：\n"
            + result.stdout
            + result.stderr
        )

    marker = f"/{prefix}_"
    return any(
        marker in line
        for line in result.stdout.splitlines()
    )


csv_files = sorted(
    CSV_ROOT.glob("vessel_activity_20[1-2][0-9].csv")
)

expected_names = [
    f"vessel_activity_{year}.csv"
    for year in range(2017, 2022)
]

actual_names = [path.name for path in csv_files]

if actual_names != expected_names:
    raise SystemExit(
        "五年船舶CSV不完整："
        f"实际发现{actual_names}"
    )

JOB_ROOT.mkdir(parents=True, exist_ok=True)
LOG_ROOT.mkdir(parents=True, exist_ok=True)

completed = 0
skipped = 0

for number, csv_path in enumerate(csv_files, start=1):
    year = csv_path.stem.rsplit("_", 1)[-1]
    prefix = f"vessel_activity_{year}"

    if hdfs_prefix_exists(prefix):
        skipped += 1
        print(
            f"===== DATAX {number}/5 跳过已有 {year} =====",
            flush=True,
        )
        continue

    job_path = JOB_ROOT / f"{prefix}.json"
    log_path = LOG_ROOT / f"{prefix}.log"

    job = {
        "job": {
            "setting": {
                "speed": {"channel": 1},
                "errorLimit": {"record": 0},
            },
            "content": [{
                "reader": {
                    "name": "txtfilereader",
                    "parameter": {
                        "path": [str(csv_path)],
                        "encoding": "UTF-8",
                        "skipHeader": True,
                        "fieldDelimiter": ",",
                        "column": [
                            {"index": index, "type": "string"}
                            for index in range(len(COLUMNS))
                        ],
                    },
                },
                "writer": {
                    "name": "hdfswriter",
                    "parameter": {
                        "defaultFS": "hdfs://127.0.0.1:9000",
                        "fileType": "text",
                        "path": HDFS_DIR,
                        "fileName": prefix,
                        "writeMode": "nonConflict",
                        "fieldDelimiter": ",",
                        "encoding": "UTF-8",
                        "column": [
                            {"name": name, "type": "string"}
                            for name in COLUMNS
                        ],
                    },
                },
            }],
        }
    }

    job_path.write_text(
        json.dumps(job, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(
        f"===== DATAX {number}/5 开始 {year} =====",
        flush=True,
    )

    with log_path.open("w", encoding="utf-8") as log_file:
        result = subprocess.run(
            [DATAX, str(job_path)],
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )

    if result.returncode != 0:
        print(f"DATAX_VESSEL_FAILED={year}", flush=True)
        print(f"失败日志={log_path}", flush=True)

        tail = log_path.read_text(
            encoding="utf-8",
            errors="replace",
        ).splitlines()[-45:]

        print("\n".join(tail), flush=True)
        sys.exit(1)

    if not hdfs_prefix_exists(prefix):
        print(
            f"任务退出码为0，但HDFS未发现{prefix}",
            flush=True,
        )
        sys.exit(1)

    completed += 1
    print(
        f"===== DATAX {number}/5 完成 {year} =====",
        flush=True,
    )

final_result = hdfs_listing()

hdfs_files = [
    line
    for line in final_result.stdout.splitlines()
    if "/vessel_activity_20" in line
]

print(f"DATAX_VESSEL_NEW_COMPLETED={completed}")
print(f"DATAX_VESSEL_EXISTING_SKIPPED={skipped}")
print(f"HDFS_VESSEL_FILE_COUNT={len(hdfs_files)}")

if len(hdfs_files) != 5:
    raise SystemExit(
        "HDFS船舶活动文件数量不是5，批量验收失败"
    )

print("DATAX_VESSEL_ALL_VERIFY=PASS")
print("DATAX_VESSEL_ALL_DONE")
