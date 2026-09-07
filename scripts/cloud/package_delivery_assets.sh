#!/usr/bin/env bash
set -euo pipefail
project_root="${PROJECT_ROOT:-/home/ecs-user/oceaninsight-project1}"
cd "$project_root"
mkdir -p output/delivery
for path in starter/scripts/cloud starter/sql output/ads_csv/ads_csv_manifest.json; do
  test -e "$path" || { echo "ERROR：缺少 $path" >&2; exit 2; }
done
source_count=$(find starter/scripts/cloud starter/sql -type f \( -name '*.sh' -o -name '*.py' -o -name '*.sql' \) | wc -l)
test "$source_count" -ge 19 || { echo "ERROR：脚本数量异常：$source_count" >&2; exit 3; }
tar --exclude='__pycache__' --exclude='*.pyc' -czf output/delivery/OceanInsight-project1-server-scripts.tar.gz starter/scripts/cloud starter/sql
tar -tzf output/delivery/OceanInsight-project1-server-scripts.tar.gz | grep -q 'spark_build_dwd.py'
(cd output/delivery && sha256sum OceanInsight-project1-server-scripts.tar.gz > OceanInsight-project1-server-scripts.tar.gz.sha256)
tar -czf output/delivery/OceanInsight-project1-ads-csv.tar.gz output/ads_csv
tar -tzf output/delivery/OceanInsight-project1-ads-csv.tar.gz | grep -q 'ads_csv_manifest.json'
(cd output/delivery && sha256sum OceanInsight-project1-ads-csv.tar.gz > OceanInsight-project1-ads-csv.tar.gz.sha256)
echo "DELIVERY_ASSET_PACKAGE=PASS"
