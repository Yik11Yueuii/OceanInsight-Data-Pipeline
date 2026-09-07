#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT=/home/ecs-user/oceaninsight-project1
STARTER_ROOT=$PROJECT_ROOT/starter
PYTHON_BIN=$PROJECT_ROOT/.venv/bin/python
SOURCE_ROOT=$PROJECT_ROOT/source/ocean_nc
OUTPUT_ROOT=$PROJECT_ROOT/output/ods/ocean

cd "$STARTER_ROOT"
mkdir -p "$OUTPUT_ROOT"

mapfile -d '' nc_files < <(
  find "$SOURCE_ROOT" \
    -type f \
    -name '*.nc' \
    -print0 |
  sort -z
)

if [ "${#nc_files[@]}" -ne 300 ]; then
  echo "NC文件应为300个，实际为${#nc_files[@]}个"
  exit 1
fi

index=0

for input_path in "${nc_files[@]}"
do
  index=$((index + 1))
  indicator=$(basename "$(dirname "$input_path")")
  filename=$(basename "$input_path")

  if [[ "$filename" =~ year_([0-9]{4})_month_([0-9]{1,2}) ]]
  then
    year="${BASH_REMATCH[1]}"
    month_number=$((10#${BASH_REMATCH[2]}))
    printf -v month '%02d' "$month_number"
    year_month="${year}-${month}"
  else
    echo "无法从文件名解析年月：$filename"
    exit 1
  fi

  output_dir="$OUTPUT_ROOT/$indicator"
  output_path="$output_dir/$year_month.csv"
  manifest_path="$output_dir/$year_month.manifest.json"

  mkdir -p "$output_dir"

  if [ -e "$output_path" ] \
    || [ -e "$output_path.tmp" ] \
    || [ -e "$manifest_path" ]
  then
    echo "检测到已有输出，停止：$output_path"
    exit 1
  fi

  echo "===== NC $index/300 $indicator $year_month ====="

  "$PYTHON_BIN" \
    -m oceaninsight.cli \
    --config conf/pipeline.json \
    nc \
    --input "$input_path" \
    --output "$output_path" \
    --manifest "$manifest_path" \
    --batch-id "student-nc-${indicator}-${year_month}"
done

csv_count=$(
  find "$OUTPUT_ROOT" \
    -type f \
    -name '*.csv' |
  wc -l
)

manifest_count=$(
  find "$OUTPUT_ROOT" \
    -type f \
    -name '*.manifest.json' |
  wc -l
)

echo "NC_CSV_COUNT=$csv_count"
echo "NC_MANIFEST_COUNT=$manifest_count"

if [ "$csv_count" -ne 300 ] \
  || [ "$manifest_count" -ne 300 ]
then
  echo 'NC_ALL_VERIFY=FAIL'
  exit 1
fi

echo 'NC_ALL_VERIFY=PASS'
echo 'NC_ALL_DONE'