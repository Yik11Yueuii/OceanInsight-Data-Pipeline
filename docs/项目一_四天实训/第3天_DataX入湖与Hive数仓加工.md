# 第3天：DataX入湖与Hive数仓加工

版本：学生实操版 V1.0  
适用环境：第2天全部验收通过，使用 `ecs-user` 登录ECS  
今日目标：将306份标准CSV通过DataX写入HDFS，建立3张Hive ODS外表，完成ODS全量质量检查，并用Spark构建DWD和DWS。

> 今天会扫描两千多万行数据。后台命令返回PID只表示任务启动；必须继续检查PID、日志和PASS标志。已有HDFS文件会被批量脚本跳过，不要为了“重新开始”删除成果。

## 一、开始前检查服务与成果

### 步骤1：确认用户和项目目录

发送：

```bash
whoami
```

必须输出 `ecs-user`。发送：

```bash
cd /home/ecs-user/oceaninsight-project1/starter
```

### 步骤2：运行项目预检脚本

发送：

```bash
bash scripts/cloud/preflight.sh
```

必须看到：

```text
PREFLIGHT=PASS
```

如果脚本提示HDFS未运行，只启动已有NameNode和DataNode，禁止格式化：

```bash
hdfs --daemon start namenode
hdfs --daemon start datanode
sleep 5
```

然后重新运行预检脚本。

### 步骤3：确认DataX与HDFS可用

发送：

```bash
command -v datax
```

预期输出 `/usr/local/bin/datax`。发送：

```bash
hdfs dfs -ls /oceaninsight
```

应正常列出目录。

### 步骤4：确认第2天本地成果

依次发送：

```bash
find ../output/ods/ocean -type f -name '*.csv' | wc -l
```

```bash
find ../output/ods/vessel -type f -name 'vessel_activity_*.csv' | wc -l
```

```bash
test -f ../output/ods/vessel/vessel_master.csv \
  && echo 'VESSEL_MASTER_LOCAL=PASS'
```

预期依次为 `300`、`5` 和 `VESSEL_MASTER_LOCAL=PASS`。

## 二、准备DataX目录和HDFS正式目录

### 步骤5：创建DataX作业与日志目录

发送：

```bash
sudo install -d -o ecs-user -g ecs-user \
  /data/oceaninsight/datax/jobs \
  /data/oceaninsight/datax/logs
```

作业JSON和每个任务的日志保存在数据盘目录，避免散落在项目源码中。

### 步骤6：创建三个HDFS ODS目录

发送：

```bash
hdfs dfs -mkdir -p \
  /oceaninsight/ods/ocean_observation \
  /oceaninsight/ods/vessel_activity \
  /oceaninsight/ods/vessel_master
```

发送：

```bash
hdfs dfs -ls /oceaninsight/ods
```

必须看到三个目录。

### 步骤7：记住DataX统一配置规则

本项目全部DataX作业固定使用：

```text
channel=1
errorLimit.record=0
skipHeader=true
fileType=text
writeMode=nonConflict
所有字段显式声明为string
```

CSV表头在DataX读取时已经跳过。TEXT不压缩时完全省略 `compress`，不能填写 `"compress":"NONE"`。

## 三、先把一个海洋CSV写入HDFS

### 步骤8：生成单文件DataX作业

发送完整代码块：

```bash
../.venv/bin/python - <<'PY'
import json
from pathlib import Path

names = [
    'year_month', 'indicator_code', 'depth_m', 'depth_level',
    'source_lat', 'source_lon', 'grid_lat', 'grid_lon', 'grid_id',
    'value', 'unit', 'quality_flag', 'source_file', 'batch_id',
]

job = {'job': {'setting': {
    'speed': {'channel': 1}, 'errorLimit': {'record': 0},
}, 'content': [{'reader': {'name': 'txtfilereader', 'parameter': {
    'path': ['/home/ecs-user/oceaninsight-project1/output/ods/ocean/temperature/2017-01.csv'],
    'encoding': 'UTF-8', 'skipHeader': True, 'fieldDelimiter': ',',
    'column': [{'index': i, 'type': 'string'} for i in range(14)],
}}, 'writer': {'name': 'hdfswriter', 'parameter': {
    'defaultFS': 'hdfs://127.0.0.1:9000', 'fileType': 'text',
    'path': '/oceaninsight/ods/ocean_observation',
    'fileName': 'ocean_temperature_2017_01',
    'writeMode': 'nonConflict', 'fieldDelimiter': ',', 'encoding': 'UTF-8',
    'column': [{'name': name, 'type': 'string'} for name in names],
}}}]}}

path = Path('/data/oceaninsight/datax/jobs/ocean_temperature_2017_01.json')
path.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding='utf-8')
print(path)
PY
```

这段代码只负责生成JSON，没有运行DataX。它显式声明14列，防止列错位。

### 步骤9：运行海洋单文件作业

发送：

```bash
datax /data/oceaninsight/datax/jobs/ocean_temperature_2017_01.json \
  > /data/oceaninsight/datax/logs/ocean_temperature_2017_01.log 2>&1
```

该文件只有6,400条，等待重新出现提示符。查看日志：

```bash
tail -n 30 /data/oceaninsight/datax/logs/ocean_temperature_2017_01.log
```

必须看到读出6,400条、读写失败0条。

### 步骤10：验收HDFS海洋冒烟文件

发送：

```bash
hdfs dfs -ls /oceaninsight/ods/ocean_observation \
  | grep 'ocean_temperature_2017_01_'
```

DataX会在文件名前追加或生成随机后缀，因此用前缀查找。发送：

```bash
hdfs dfs -cat \
  '/oceaninsight/ods/ocean_observation/ocean_temperature_2017_01_*' \
  | wc -l
```

必须输出 `6400`。DataX已跳过CSV的一行表头，所以HDFS只保存业务数据。

## 四、串行写入全部300份海洋CSV

### 步骤11：启动海洋批量调度脚本

发送：

```bash
nohup ../.venv/bin/python scripts/cloud/run_datax_ocean_all.py \
  > /data/oceaninsight/datax/logs/ocean_all_driver.log 2>&1 < /dev/null &
```

立即保存PID：

```bash
echo $! > /data/oceaninsight/datax/logs/ocean_all_driver.pid
```

脚本逐份生成Job和日志，发现刚才成功的2017-01温度文件会跳过，其他299份串行执行。

### 步骤12：等待并查看海洋入湖任务

先等待60秒：

```bash
sleep 60
```

```bash
ps -p "$(cat /data/oceaninsight/datax/logs/ocean_all_driver.pid)" -f
```

```bash
tail -n 40 /data/oceaninsight/datax/logs/ocean_all_driver.log
```

看到 `DATAX 数字/300` 表示仍在处理。继续每隔60秒查看原PID和日志，不要重复启动。最终必须看到：

```text
DATAX_NEW_COMPLETED=299
DATAX_EXISTING_SKIPPED=1
HDFS_OCEAN_FILE_COUNT=300
DATAX_OCEAN_ALL_VERIFY=PASS
DATAX_OCEAN_ALL_DONE
```

跳过1份就是步骤9完成的文件，不是漏传。

### 步骤13：全量对账海洋HDFS数据

发送：

```bash
hdfs dfs -cat '/oceaninsight/ods/ocean_observation/*' \
  | awk -F',' 'NF!=14{bad++} END{print "HDFS_OCEAN_ROWS=" NR; print "HDFS_BAD_COLUMN_ROWS=" bad+0; if(NR==3357840 && bad==0) print "DATAX_OCEAN_ROWS_VERIFY=PASS"}'
```

扫描约577.6 MiB数据需要等待。必须看到：

```text
HDFS_OCEAN_ROWS=3357840
HDFS_BAD_COLUMN_ROWS=0
DATAX_OCEAN_ROWS_VERIFY=PASS
```

## 五、把五年船舶活动写入HDFS

### 步骤14：生成并启动2017 DataX作业

发送完整代码块：

```bash
../.venv/bin/python - <<'PY'
import json
from pathlib import Path
names = [
    'observation_date','year','month','year_month','source_grid_lat',
    'source_grid_lon','grid_lat','grid_lon','grid_id','mmsi','hours',
    'fishing_hours','quality_flag','source_file','batch_id',
]
job = {'job': {'setting': {'speed': {'channel': 1}, 'errorLimit': {'record': 0}},
'content': [{'reader': {'name': 'txtfilereader', 'parameter': {
'path': ['/home/ecs-user/oceaninsight-project1/output/ods/vessel/vessel_activity_2017.csv'],
'encoding': 'UTF-8', 'skipHeader': True, 'fieldDelimiter': ',',
'column': [{'index': i, 'type': 'string'} for i in range(15)]}},
'writer': {'name': 'hdfswriter', 'parameter': {
'defaultFS': 'hdfs://127.0.0.1:9000', 'fileType': 'text',
'path': '/oceaninsight/ods/vessel_activity', 'fileName': 'vessel_activity_2017',
'writeMode': 'nonConflict', 'fieldDelimiter': ',', 'encoding': 'UTF-8',
'column': [{'name': n, 'type': 'string'} for n in names]}}}]}}
Path('/data/oceaninsight/datax/jobs/vessel_activity_2017.json').write_text(
    json.dumps(job, ensure_ascii=False, indent=2), encoding='utf-8')
PY
```

使用后台方式运行，发送：

```bash
nohup datax /data/oceaninsight/datax/jobs/vessel_activity_2017.json \
  > /data/oceaninsight/datax/logs/vessel_activity_2017.log 2>&1 < /dev/null &
```

立即保存PID：

```bash
echo $! > /data/oceaninsight/datax/logs/vessel_activity_2017.pid
```

实测约41秒。先等待30秒：

```bash
sleep 30
```

检查原PID：

```bash
ps -p "$(cat /data/oceaninsight/datax/logs/vessel_activity_2017.pid)" -f
```

查看日志：

```bash
tail -n 30 /data/oceaninsight/datax/logs/vessel_activity_2017.log
```

必须看到读出2,928,426条、失败0条。

### 步骤15：验收2017 HDFS文件

发送：

```bash
hdfs dfs -cat '/oceaninsight/ods/vessel_activity/vessel_activity_2017_*' \
  | awk -F',' 'NF!=15{bad++} END{print "ROWS=" NR; print "BAD_COLUMNS=" bad+0; if(NR==2928426 && bad==0) print "DATAX_VESSEL_2017_VERIFY=PASS"}'
```

必须看到 `DATAX_VESSEL_2017_VERIFY=PASS`。

> 不使用 `hdfs dfs -cat ... | head` 作为正式验收。`head`读取几行后会主动关闭管道，HDFS可能提示 `Unable to write to output stream`；这不是文件损坏。

### 步骤16：启动2018—2021批量入湖

发送：

```bash
nohup ../.venv/bin/python scripts/cloud/run_datax_vessel_all.py \
  > /data/oceaninsight/datax/logs/vessel_all_driver.log 2>&1 < /dev/null &
```

```bash
echo $! > /data/oceaninsight/datax/logs/vessel_all_driver.pid
```

脚本会跳过已有2017，只串行写入其余4年。

### 步骤17：等待并查看船舶入湖任务

发送：

```bash
sleep 60
```

```bash
ps -p "$(cat /data/oceaninsight/datax/logs/vessel_all_driver.pid)" -f
```

```bash
tail -n 40 /data/oceaninsight/datax/logs/vessel_all_driver.log
```

未完成就继续等待60秒查看原日志。最终必须看到：

```text
DATAX_VESSEL_NEW_COMPLETED=4
DATAX_VESSEL_EXISTING_SKIPPED=1
HDFS_VESSEL_FILE_COUNT=5
DATAX_VESSEL_ALL_VERIFY=PASS
DATAX_VESSEL_ALL_DONE
```

### 步骤18：全量对账五年HDFS活动数据

发送：

```bash
hdfs dfs -cat '/oceaninsight/ods/vessel_activity/*' \
  | awk -F',' 'NF!=15{bad++} END{print "HDFS_VESSEL_ROWS=" NR; print "HDFS_BAD_COLUMN_ROWS=" bad+0; if(NR==18638286 && bad==0) print "DATAX_VESSEL_ROWS_VERIFY=PASS"}'
```

扫描约2.4 GiB需要几分钟。必须看到18,638,286行、异常列0和 `DATAX_VESSEL_ROWS_VERIFY=PASS`。

## 六、把船舶主数据写入HDFS

### 步骤19：生成24列DataX作业

发送完整代码块：

```bash
../.venv/bin/python - <<'PY'
import json
from pathlib import Path
names = [
'mmsi','year','imo','shipname','callsign','flag_gfw','flag_registry','flag_ais',
'vessel_class_gfw','vessel_class_registry','vessel_class_inferred',
'self_reported_fishing_vessel','length_m','tonnage_gt','engine_power_kw',
'registered_gear_type','inferred_gear_type','registry_public_authorization',
'registry_data_source','registry_record_id','first_timestamp','last_timestamp',
'batch_id','source_file']
job = {'job': {'setting': {'speed': {'channel': 1}, 'errorLimit': {'record': 0}},
'content': [{'reader': {'name': 'txtfilereader', 'parameter': {
'path': ['/home/ecs-user/oceaninsight-project1/output/ods/vessel/vessel_master.csv'],
'encoding': 'UTF-8', 'skipHeader': True, 'fieldDelimiter': ',',
'column': [{'index': i, 'type': 'string'} for i in range(24)]}},
'writer': {'name': 'hdfswriter', 'parameter': {
'defaultFS': 'hdfs://127.0.0.1:9000', 'fileType': 'text',
'path': '/oceaninsight/ods/vessel_master','fileName': 'vessel_master',
'writeMode': 'nonConflict','fieldDelimiter': ',','encoding': 'UTF-8',
'column': [{'name': n, 'type': 'string'} for n in names]}}}]}}
Path('/data/oceaninsight/datax/jobs/vessel_master.json').write_text(
json.dumps(job, ensure_ascii=False, indent=2), encoding='utf-8')
print('VESSEL_MASTER_JOB=READY')
PY
```

必须看到 `VESSEL_MASTER_JOB=READY`。

### 步骤20：运行并严格验收主数据

发送：

```bash
datax /data/oceaninsight/datax/jobs/vessel_master.json \
  > /data/oceaninsight/datax/logs/vessel_master.log 2>&1
```

查看日志：

```bash
tail -n 30 /data/oceaninsight/datax/logs/vessel_master.log
```

应读出149,660条、失败0条。继续发送：

```bash
hdfs dfs -cat '/oceaninsight/ods/vessel_master/vessel_master_*' \
  | awk -F',' 'NF!=24{badcol++} $23!="student-vessel-master"{badbatch++} $24!="vessel_master.csv"{badsource++} END{print "ROWS=" NR; print "BAD_COLUMNS=" badcol+0; print "BAD_BATCH=" badbatch+0; print "BAD_SOURCE=" badsource+0; if(NR==149660 && badcol==0 && badbatch==0 && badsource==0) print "DATAX_VESSEL_MASTER_VERIFY=PASS"}'
```

必须看到 `DATAX_VESSEL_MASTER_VERIFY=PASS`。DataX可能静默忽略额外列，所以不能只看“失败0”。

## 七、创建Hive四层数据库和三张ODS外表

### 步骤21：执行最终Hive建表SQL

发送：

```bash
beeline -u 'jdbc:hive2://127.0.0.1:10000/default' \
  -n ecs-user \
  -f sql/hive/001_layers.sql
```

SQL会创建 `ocean_ods`、`ocean_dwd`、`ocean_dws`、`ocean_ads` 四个数据库，以及三张ODS外表。

### 步骤22：核对三张表类型和Location

发送：

```bash
beeline -u 'jdbc:hive2://127.0.0.1:10000/default' -n ecs-user \
  -e "SHOW TABLES IN ocean_ods;"
```

应看到 `ods_ocean_observation`、`ods_vessel_activity`、`ods_vessel_master`。发送：

```bash
for t in ods_ocean_observation ods_vessel_activity ods_vessel_master; do
  beeline -u 'jdbc:hive2://127.0.0.1:10000/default' -n ecs-user \
    --silent=true --showHeader=false --outputformat=tsv2 \
    -e "DESCRIBE FORMATTED ocean_ods.${t};" \
    | grep -E 'Table Type:|Location:'
done
```

三张表必须是 `EXTERNAL_TABLE`，Location分别指向三个DataX正式目录。

> DataX已经跳过每个CSV表头，Hive表不能再设置 `skip.header.line.count`，否则每个HDFS文件会误丢第一条业务记录。

## 八、使用Spark全量验收ODS

### 步骤23：提交ODS验收任务

发送：

```bash
nohup env JAVA_HOME=/usr/lib/jvm/java-17 \
  spark-submit scripts/cloud/spark_hive_ods_verify.py \
  > /data/oceaninsight/logs/spark_hive_ods_verify.log 2>&1 < /dev/null &
```

```bash
echo $! > /data/oceaninsight/logs/spark_hive_ods_verify.pid
```

### 步骤24：等待ODS验收完成

先等待60秒，再检查：

```bash
sleep 60
ps -p "$(cat /data/oceaninsight/logs/spark_hive_ods_verify.pid)" -f
tail -n 60 /data/oceaninsight/logs/spark_hive_ods_verify.log
```

PID仍在且没有异常就继续等待60秒。最终必须看到海洋3,357,840、船舶18,638,286、主数据149,660，各类异常为0，以及：

```text
SPARK_HIVE_ODS_VERIFY=PASS
```

## 九、构建DWD清洗层

### 步骤25：提交DWD任务

只有ODS PASS后发送：

```bash
nohup env JAVA_HOME=/usr/lib/jvm/java-17 \
  spark-submit scripts/cloud/spark_build_dwd.py \
  > /data/oceaninsight/logs/spark_build_dwd.log 2>&1 < /dev/null &
```

```bash
echo $! > /data/oceaninsight/logs/spark_build_dwd.pid
```

### 步骤26：等待DWD PASS

发送：

```bash
sleep 60
ps -p "$(cat /data/oceaninsight/logs/spark_build_dwd.pid)" -f
tail -n 60 /data/oceaninsight/logs/spark_build_dwd.log
```

日志阶段标题只代表正在处理，不代表完成。最终必须看到：

```text
DWD_OCEAN_ROWS=2687015
DWD_VESSEL_ROWS=18638286
DWD_MASTER_ROWS=149660
DWD_MASTER_DISTINCT_KEYS=149660
SPARK_DWD_BUILD=PASS
```

海洋DWD剔除了670,825条明确标记为 `MISSING` 的记录；船舶活动全部有效，行数不变。

## 十、构建DWS汇总层

### 步骤27：提交DWS任务

只有DWD PASS后发送：

```bash
nohup env JAVA_HOME=/usr/lib/jvm/java-17 \
  spark-submit scripts/cloud/spark_build_dws.py \
  > /data/oceaninsight/logs/spark_build_dws.log 2>&1 < /dev/null &
```

```bash
echo $! > /data/oceaninsight/logs/spark_build_dws.pid
```

### 步骤28：等待DWS PASS

发送：

```bash
sleep 60
ps -p "$(cat /data/oceaninsight/logs/spark_build_dws.pid)" -f
tail -n 80 /data/oceaninsight/logs/spark_build_dws.log
```

未完成时继续等待60秒并查看原日志。最终必须看到：

```text
DWS_OCEAN_ROWS=721200
DWS_OCEAN_DISTINCT_KEYS=721200
DWS_OCEAN_DETAIL_ROWS=2687015
DWS_VESSEL_ROWS=7404
DWS_VESSEL_DISTINCT_KEYS=7404
DWS_VESSEL_DETAIL_ROWS=18638286
SPARK_DWS_BUILD=PASS
```

## 十一、第3天最终验收

### 步骤29：查看DWD和DWS表

发送：

```bash
beeline -u 'jdbc:hive2://127.0.0.1:10000/default' -n ecs-user \
  -e "SHOW TABLES IN ocean_dwd; SHOW TABLES IN ocean_dws;"
```

应看到3张DWD表和2张DWS表。

### 步骤30：检查表格式与服务

发送：

```bash
beeline -u 'jdbc:hive2://127.0.0.1:10000/default' -n ecs-user \
  --silent=true --showHeader=false --outputformat=tsv2 \
  -e "DESCRIBE FORMATTED ocean_dws.dws_ocean_monthly_grid;" \
  | grep -E 'Table Type:|InputFormat:|Location:'
```

本机实测Spark注册结果为 `EXTERNAL_TABLE`、Parquet和正确HDFS Location；不要把 `MANAGED_TABLE` 当作通过条件。

发送：

```bash
jps
```

```bash
df -h /
```

确认NameNode、DataNode、Hive进程仍在，磁盘空间充足。

## 十二、第3天验收表

| 验收项 | 通过标准 |
|---|---|
| 海洋DataX | HDFS 300文件、3,357,840行、14列异常0 |
| 船舶活动DataX | HDFS 5文件、18,638,286行、15列异常0 |
| 船舶主数据DataX | 149,660行、24列及血缘异常0 |
| Hive ODS | 3张外表指向正确HDFS目录 |
| Spark ODS验收 | `SPARK_HIVE_ODS_VERIFY=PASS` |
| DWD | 2,687,015海洋、18,638,286活动、149,660主数据，PASS |
| DWS | 721,200海洋、7,404船舶，明细完整回卷，PASS |

全部通过后，第3天完成。不要删除HDFS数据、Hive表、Spark日志、DataX Job或日志；第4天将在DWS基础上构建ADS、发布MariaDB并导出最终CSV。
