#!/usr/bin/env bash
set -euo pipefail
[ "$(id -un)" = "ecs-user" ] || { echo "ERROR：请切回 ecs-user" >&2; exit 2; }
jps | grep -q NameNode || hdfs --daemon start namenode
jps | grep -q DataNode || hdfs --daemon start datanode
sleep 5
hdfs dfs -ls /oceaninsight >/dev/null
sudo systemctl restart oceaninsight-hiveserver2
for i in {1..12}; do
  sudo ss -lntp | grep -q ':10000' && break
  echo "等待 HiveServer2：第 ${i}/12 次检查"
  sleep 10
done
jps
sudo ss -lntp | grep -E ':(3306|9000|9083|10000)\b'
beeline -u 'jdbc:hive2://127.0.0.1:10000/default' -n ecs-user --silent=true -e 'SHOW DATABASES;'
echo "SERVICE_RECOVERY=PASS"
