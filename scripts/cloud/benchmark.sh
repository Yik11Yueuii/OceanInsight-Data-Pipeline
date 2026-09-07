#!/usr/bin/env bash
set -euo pipefail
# 全链路已经封板；这里只读核对，不重复执行数据任务。
project_root="${PROJECT_ROOT:-/home/ecs-user/oceaninsight-project1}"
"$project_root/starter/scripts/cloud/preflight.sh"
hdfs dfs -du -h /oceaninsight/ods /oceaninsight/dwd /oceaninsight/dws /oceaninsight/ads
python3 - "$project_root/output/ads_csv/ads_csv_manifest.json" <<'PY'
import json, sys
from pathlib import Path
m = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert m["table_count"] == 7
assert m["batch_id"] == "student-ads-20260825"
print("PROJECT1_DELIVERY_CHECK=PASS")
PY
