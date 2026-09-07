#!/usr/bin/env bash
set -euo pipefail
[ "$(id -un)" = "ecs-user" ] || { echo "ERROR：请切回 ecs-user" >&2; exit 2; }
date --iso-8601=seconds
echo "cpu_count=$(nproc)"
free -h
df -h /
java -version 2>&1 | head -n 1
/usr/lib/jvm/java-17/bin/java -version 2>&1 | head -n 1
jps
sudo systemctl is-active mariadb oceaninsight-hive-metastore oceaninsight-hiveserver2
sudo ss -lntp | grep -E ':(3306|9000|9083|10000)\b' || true
hdfs dfs -ls /oceaninsight
beeline -u 'jdbc:hive2://127.0.0.1:10000/default' -n ecs-user --silent=true -e 'SHOW DATABASES;'
echo "PREFLIGHT=PASS"
