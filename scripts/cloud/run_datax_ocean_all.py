#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

CSV_ROOT = Path(
    "/home/ecs-user/oceaninsight-project1/output/ods/ocean"
)
JOB_ROOT = Path(
    "/data/oceaninsight/datax/jobs/ocean_all"
)
LOG_ROOT = Path(
    "/data/oceaninsight/datax/logs/ocean_all"
)
HDFS_DIR = "/oceaninsight/ods/ocean_observation"
DATAX = "/usr/local/bin/datax"

COLUMNS = [
    "year_month",
    "indicator_code",
    "depth_m",
    "depth_level",
    "source_lat",
    "source_lon",
    "grid_lat",
    "grid_lon",
    "grid_id",
    "value",
    "unit",
    "quality_flag",
    "source_file",
    "batch_id",
]


def run(command, *, capture=True):
    return subprocess.run(
        command,
        text=True,
        capture_output=capture,
        check=False,
    )


def hdfs_prefix_exists(prefix):
    result = run(["hdfs", "dfs", "-ls", HDFS_DIR])
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


csv_files = sorted(CSV_ROOT.glob("*/*.csv"))

if len(csv_files) != 300:
    raise SystemExit(
        f"期望300份海洋CSV，实际发现{len(csv_files)}份"
    )

JOB_ROOT.mkdir(parents=True, exist_ok=True)
LOG_ROOT.mkdir(parents=True, exist_ok=True)

completed = 0
skipped = 0

for number, csv_path in enumerate(csv_files, start=1):
    indicator = csv_path.parent.name
    year_month = csv_path.stem
    safe_month = year_month.replace("-", "_")
    prefix = f"ocean_{indicator}_{safe_month}"

    if hdfs_prefix_exists(prefix):
        skipped += 1
        print(
            f"===== DATAX {number}/300 跳过已有 "
            f"{indicator} {year_month} =====",
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
        f"===== DATAX {number}/300 开始 "
        f"{indicator} {year_month} =====",
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
        print(
            f"DATAX_OCEAN_FAILED={indicator}/{year_month}",
            flush=True,
        )
        print(f"失败日志={log_path}", flush=True)

        tail = log_path.read_text(
            encoding="utf-8",
            errors="replace",
        ).splitlines()[-40:]

        print("\n".join(tail), flush=True)
        sys.exit(1)

    if not hdfs_prefix_exists(prefix):
        print(
            f"DataX退出码为0，但未发现HDFS文件：{prefix}",
            flush=True,
        )
        sys.exit(1)

    completed += 1
    print(
        f"===== DATAX {number}/300 完成 "
        f"{indicator} {year_month} =====",
        flush=True,
    )

final_ls = run(["hdfs", "dfs", "-ls", HDFS_DIR])

hdfs_files = [
    line
    for line in final_ls.stdout.splitlines()
    if "/ocean_" in line
]

print(f"DATAX_NEW_COMPLETED={completed}")
print(f"DATAX_EXISTING_SKIPPED={skipped}")
print(f"HDFS_OCEAN_FILE_COUNT={len(hdfs_files)}")

if len(hdfs_files) != 300:
    raise SystemExit(
        "HDFS海洋文件数量不是300，批量验收失败"
    )

print("DATAX_OCEAN_ALL_VERIFY=PASS")
print("DATAX_OCEAN_ALL_DONE")
