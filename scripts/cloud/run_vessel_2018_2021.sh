#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT=/home/ecs-user/oceaninsight-project1
STARTER_ROOT=$PROJECT_ROOT/starter
PYTHON_BIN=$PROJECT_ROOT/.venv/bin/python
SOURCE_DIR=$PROJECT_ROOT/source/vessel_zip
OUTPUT_DIR=$PROJECT_ROOT/output/ods/vessel

cd "$STARTER_ROOT"
mkdir -p "$OUTPUT_DIR"

for year in 2018 2019 2020 2021
do
  input_path="$SOURCE_DIR/vessel-teaching-${year}.zip"
  output_path="$OUTPUT_DIR/vessel_activity_${year}.csv"
  manifest_path="$OUTPUT_DIR/vessel_activity_${year}.manifest.json"

  if [ -e "$output_path" ] || [ -e "$output_path.tmp" ] || [ -e "$manifest_path" ]; then
    echo "检测到${year}已有输出或临时文件，停止以避免覆盖"
    exit 1
  fi

  echo "===== $(date '+%F %T') 开始处理 ${year} ====="

  "$PYTHON_BIN" \
    -m oceaninsight.cli \
    --config conf/pipeline.json \
    vessel \
    --input "$input_path" \
    --output "$output_path" \
    --manifest "$manifest_path" \
    --batch-id "student-vessel-${year}"

  echo "===== $(date '+%F %T') 完成 ${year} ====="
  ls -lh "$output_path" "$manifest_path"
done

echo 'VESSEL_2018_2021_ALL_DONE'
