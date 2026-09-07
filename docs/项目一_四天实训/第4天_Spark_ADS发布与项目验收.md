# 第4天：构建ADS、发布MariaDB与完成项目验收

版本：学生实操版 V1.0  
适用环境：第3天ODS、DWD和DWS全部PASS，使用 `ecs-user` 登录ECS  
今日目标：构建7张Hive ADS表，发布MariaDB，导出7份ADS CSV，完成三方对账并手动下载交付包。

> FineBI不属于项目一，本文件不创建FineBI账户、不开放3306公网端口。PID和阶段标题不代表完成，只有指定PASS才算完成。

## 一、开始前检查

### 步骤1：确认用户和目录

在Workbench Shell发送：

```bash
whoami
```

必须输出 `ecs-user`。发送：

```bash
cd /home/ecs-user/oceaninsight-project1/starter
```

### 步骤2：确认第3天三个PASS

依次发送：

```bash
grep 'SPARK_HIVE_ODS_VERIFY=PASS' /data/oceaninsight/logs/spark_hive_ods_verify.log
```

```bash
grep 'SPARK_DWD_BUILD=PASS' /data/oceaninsight/logs/spark_build_dwd.log
```

```bash
grep 'SPARK_DWS_BUILD=PASS' /data/oceaninsight/logs/spark_build_dws.log
```

缺少任何一条都不要继续。

### 步骤3：确认服务和Java 17

依次发送：

```bash
jps
```

```bash
sudo systemctl is-active mariadb
```

```bash
/usr/lib/jvm/java-17/bin/java -version
```

应看到NameNode、DataNode、两个Hive RunJar、MariaDB为 `active`，Java版本为17。

## 二、构建5张核心ADS表

### 步骤4：提交核心ADS任务

发送：

```bash
nohup env JAVA_HOME=/usr/lib/jvm/java-17 \
  spark-submit scripts/cloud/spark_build_ads_core.py \
  > /data/oceaninsight/logs/spark_build_ads_core.log 2>&1 < /dev/null &
```

立即保存PID：

```bash
echo $! > /data/oceaninsight/logs/spark_build_ads_core.pid
```

### 步骤5：等待核心ADS完成

发送：

```bash
sleep 60
```

```bash
ps -p "$(cat /data/oceaninsight/logs/spark_build_ads_core.pid)" -f
```

```bash
tail -n 100 /data/oceaninsight/logs/spark_build_ads_core.log
```

PID仍在时继续每隔60秒查看原任务，不要重复提交。最终必须看到：

```text
ADS_OCEAN_OVERVIEW_ROWS=61
ADS_OCEAN_MONTHLY_ROWS=721200
ADS_OCEAN_MONTHLY_DISTINCT_KEYS=721200
ADS_OCEAN_TREND_ROWS=2220
ADS_OCEAN_TREND_DISTINCT_KEYS=2220
ADS_OCEAN_TREND_DETAIL_ROWS=2687015
ADS_VESSEL_MONTHLY_ROWS=7404
ADS_VESSEL_MONTHLY_DISTINCT_KEYS=7404
ADS_RELATION_ROWS=226192
ADS_RELATION_DISTINCT_KEYS=226192
SPARK_ADS_CORE_BUILD=PASS
```

5张表分别是海洋总览、月度网格、指标趋势、船舶月度网格和海洋船舶关联。

## 三、构建船旗国和船型ADS

### 步骤6：提交第二段ADS任务

只有核心ADS PASS后发送：

```bash
nohup env JAVA_HOME=/usr/lib/jvm/java-17 \
  spark-submit scripts/cloud/spark_build_ads_vessel_class.py \
  > /data/oceaninsight/logs/spark_build_ads_vessel_class.log 2>&1 < /dev/null &
```

```bash
echo $! > /data/oceaninsight/logs/spark_build_ads_vessel_class.pid
```

### 步骤7：等待第二段ADS完成

发送：

```bash
sleep 60
ps -p "$(cat /data/oceaninsight/logs/spark_build_ads_vessel_class.pid)" -f
tail -n 100 /data/oceaninsight/logs/spark_build_ads_vessel_class.log
```

未完成就继续等待60秒。最终必须看到：

```text
DWS_FLAG_CLASS_ROWS=1691
DWS_FLAG_CLASS_DISTINCT_KEYS=1691
DWS_FLAG_CLASS_DETAIL_ROWS=18638286
DWS_FLAG_CLASS_VESSEL_KEYS=149660
ADS_VESSEL_FLAG_ROWS=687
ADS_VESSEL_FLAG_DISTINCT_KEYS=687
ADS_VESSEL_FLAG_DETAIL_ROWS=18638286
ADS_VESSEL_FLAG_VESSEL_KEYS=149660
ADS_VESSEL_CLASS_ROWS=80
ADS_VESSEL_CLASS_DISTINCT_KEYS=80
ADS_VESSEL_CLASS_DETAIL_ROWS=18638286
ADS_VESSEL_CLASS_VESSEL_KEYS=149660
SPARK_ADS_VESSEL_CLASS_BUILD=PASS
```

船旗国和船型空值统一归为 `UNKNOWN`；两条路线均完整回卷18,638,286条活动和149,660个主数据业务键。

## 四、验收7张Hive ADS表

### 步骤8：查看表名

发送：

```bash
beeline -u 'jdbc:hive2://127.0.0.1:10000/default' -n ecs-user \
  -e 'SHOW TABLES IN ocean_ads;'
```

必须看到：

```text
ads_ocean_overview
ads_ocean_monthly_grid
ads_ocean_indicator_trend
ads_vessel_monthly_grid
ads_ocean_vessel_relation
ads_vessel_flag_year
ads_vessel_class_year
```

### 步骤9：核对Hive七表行数

发送完整代码块：

```bash
for item in ads_ocean_overview:61 ads_ocean_monthly_grid:721200 \
  ads_ocean_indicator_trend:2220 ads_vessel_monthly_grid:7404 \
  ads_ocean_vessel_relation:226192 ads_vessel_flag_year:687 \
  ads_vessel_class_year:80
do
  table="${item%%:*}"; expected="${item##*:}"
  actual=$(beeline -u 'jdbc:hive2://127.0.0.1:10000/default' \
    -n ecs-user --silent=true --showHeader=false --outputformat=tsv2 \
    -e "SELECT COUNT(*) FROM ocean_ads.${table};" 2>/dev/null \
    | grep -E '^[0-9]+$' | tail -n 1)
  echo "${table}=${actual} expected=${expected}"
  test "$actual" = "$expected" || exit 1
done
echo 'HIVE_ADS_ROWS_VERIFY=PASS'
```

必须看到 `HIVE_ADS_ROWS_VERIFY=PASS`。

### 步骤10：检查ADS表格式

发送：

```bash
beeline -u 'jdbc:hive2://127.0.0.1:10000/default' -n ecs-user \
  --silent=true --showHeader=false --outputformat=tsv2 \
  -e 'DESCRIBE FORMATTED ocean_ads.ads_ocean_monthly_grid;' \
  | grep -E 'Table Type:|InputFormat:|Location:'
```

实测正确状态是 `EXTERNAL_TABLE`、Parquet和 `/oceaninsight/ads/...` Location，不要求 `MANAGED_TABLE`。

## 五、创建MariaDB七张结果表

### 步骤11：检查私有配置和JDBC驱动

发送：

```bash
stat -c '%a %U %n' "$HOME/.config/oceaninsight/ads-db.cnf"
```

必须显示权限600、所有者 `ecs-user`。不要 `cat` 密码文件。发送：

```bash
test -f /opt/hive/lib/mysql-connector-j-8.4.0.jar \
  && echo 'MYSQL_CONNECTOR=PASS'
```

### 步骤12：执行建表SQL

发送：

```bash
mariadb --defaults-extra-file="$HOME/.config/oceaninsight/ads-db.cnf" \
  < sql/mysql/001_ads_schema.sql
```

没有SQL错误才继续。最终SQL已用反引号引用 `year_month`；`YEAR_MONTH` 是MariaDB关键字，不能删除反引号。

### 步骤13：确认七张表为空

发送：

```bash
for table in ads_ocean_overview ads_ocean_monthly_grid \
  ads_ocean_indicator_trend ads_vessel_monthly_grid \
  ads_ocean_vessel_relation ads_vessel_flag_year ads_vessel_class_year
do
  mariadb --defaults-extra-file="$HOME/.config/oceaninsight/ads-db.cnf" \
    --batch --skip-column-names ocean_insight_ads \
    -e "SELECT '${table}',COUNT(*) FROM ${table};"
done
```

七张表都必须是0行。发布脚本使用 `append`，非0时停止，不要重复发布。

## 六、先发布MariaDB总览表

### 步骤14：提交单表试发布

发送：

```bash
nohup env JAVA_HOME=/usr/lib/jvm/java-17 spark-submit \
  --jars /opt/hive/lib/mysql-connector-j-8.4.0.jar \
  scripts/cloud/spark_publish_mariadb_overview.py \
  > /data/oceaninsight/logs/publish_mariadb_overview.log 2>&1 < /dev/null &
```

```bash
echo $! > /data/oceaninsight/logs/publish_mariadb_overview.pid
```

脚本从权限600的CNF读取连接信息，不会在命令或日志中显示密码。

### 步骤15：等待并验收总览表

发送：

```bash
sleep 30
ps -p "$(cat /data/oceaninsight/logs/publish_mariadb_overview.pid)" -f
tail -n 60 /data/oceaninsight/logs/publish_mariadb_overview.log
```

必须看到：

```text
HIVE_OVERVIEW_ROWS=61
SPARK_JDBC_OVERVIEW_WRITE=PASS
```

发送：

```bash
mariadb --defaults-extra-file="$HOME/.config/oceaninsight/ads-db.cnf" \
  --batch --skip-column-names ocean_insight_ads \
  -e "SELECT COUNT(*),COUNT(DISTINCT CONCAT(scope_type,'|',\`year_month\`)),COUNT(DISTINCT batch_id),MIN(batch_id),MAX(batch_id) FROM ads_ocean_overview;"
```

预期为61行、61个唯一键、1个批次，最小和最大批次均为 `student-ads-20260825`。

## 七、发布MariaDB其余六表

### 步骤16：提交六表任务

发送：

```bash
nohup env JAVA_HOME=/usr/lib/jvm/java-17 spark-submit \
  --jars /opt/hive/lib/mysql-connector-j-8.4.0.jar \
  scripts/cloud/spark_publish_mariadb_ads.py \
  > /data/oceaninsight/logs/publish_mariadb_ads.log 2>&1 < /dev/null &
```

```bash
echo $! > /data/oceaninsight/logs/publish_mariadb_ads.pid
```

### 步骤17：等待六表发布完成

发送：

```bash
sleep 60
ps -p "$(cat /data/oceaninsight/logs/publish_mariadb_ads.pid)" -f
tail -n 100 /data/oceaninsight/logs/publish_mariadb_ads.log
```

未完成就继续等待60秒。每张表应出现 `JDBC_WRITE_TABLE=... PASS`，最后必须看到 `SPARK_JDBC_ADS_ALL_WRITE=PASS`。不要再次运行发布脚本。

### 步骤18：核对MariaDB行数和批次

发送：

```bash
for item in ads_ocean_overview:61 ads_ocean_monthly_grid:721200 \
  ads_ocean_indicator_trend:2220 ads_vessel_monthly_grid:7404 \
  ads_ocean_vessel_relation:226192 ads_vessel_flag_year:687 \
  ads_vessel_class_year:80
do
  table="${item%%:*}"; expected="${item##*:}"
  result=$(mariadb --defaults-extra-file="$HOME/.config/oceaninsight/ads-db.cnf" \
    --batch --skip-column-names ocean_insight_ads \
    -e "SELECT COUNT(*),COUNT(DISTINCT batch_id),MIN(batch_id),MAX(batch_id) FROM ${table};")
  echo "${table} ${result} expected=${expected}"
  test "$(printf '%s\n' "$result" | awk '{print $1}')" = "$expected" || exit 1
done
echo 'MARIADB_ADS_VERIFY=PASS'
```

每行批次数必须为1，最小和最大批次必须为 `student-ads-20260825`。

## 八、导出7份ADS CSV

### 步骤19：提交CSV导出任务

先确认输出不存在：

```bash
test ! -e ../output/ads_csv \
  && echo 'ADS_CSV_OUTPUT_READY=YES' \
  || echo 'ADS_CSV_OUTPUT_READY=NO'
```

第一次必须显示 `YES`。发送：

```bash
nohup env JAVA_HOME=/usr/lib/jvm/java-17 \
  spark-submit scripts/cloud/spark_export_ads_csv.py \
  > /data/oceaninsight/logs/export_ads_csv.log 2>&1 < /dev/null &
```

```bash
echo $! > /data/oceaninsight/logs/export_ads_csv.pid
```

脚本使用 `file:///home/...` 本地URI；没有 `file:///` 时Spark会误写入HDFS。

### 步骤20：等待CSV导出完成

发送：

```bash
sleep 60
ps -p "$(cat /data/oceaninsight/logs/export_ads_csv.pid)" -f
tail -n 100 /data/oceaninsight/logs/export_ads_csv.log
```

未完成就继续等待60秒。最终必须看到：

```text
ADS_CSV_TABLE_COUNT=7
ADS_CSV_MANIFEST=/home/ecs-user/oceaninsight-project1/output/ads_csv/ads_csv_manifest.json
SPARK_ADS_CSV_EXPORT=PASS
```

### 步骤21：验收CSV和Manifest

发送完整代码块：

```bash
../.venv/bin/python - <<'PY'
import hashlib, json
from pathlib import Path
root = Path('../output/ads_csv')
m = json.loads((root/'ads_csv_manifest.json').read_text())
expected = {'ads_ocean_overview':61,'ads_ocean_monthly_grid':721200,
'ads_ocean_indicator_trend':2220,'ads_vessel_monthly_grid':7404,
'ads_ocean_vessel_relation':226192,'ads_vessel_flag_year':687,
'ads_vessel_class_year':80}
assert m['table_count'] == 7 and m['batch_id'] == 'student-ads-20260825'
for item in m['tables']:
    name = item['table'].split('.')[-1]; path = root/f'{name}.csv'
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    assert item['rows'] == expected[name]
    assert item['csv_lines'] == expected[name] + 1
    assert item['sha256'] == digest.hexdigest()
print('ADS_CSV_MANIFEST_VERIFY=PASS')
PY
```

必须看到 `ADS_CSV_MANIFEST_VERIFY=PASS`。7份CSV约118 MiB，每份有1行表头。

## 九、三方对账

### 步骤22：核对统一结果

| ADS表 | Hive | MariaDB | CSV数据行 |
|---|---:|---:|---:|
| `ads_ocean_overview` | 61 | 61 | 61 |
| `ads_ocean_monthly_grid` | 721,200 | 721,200 | 721,200 |
| `ads_ocean_indicator_trend` | 2,220 | 2,220 | 2,220 |
| `ads_vessel_monthly_grid` | 7,404 | 7,404 | 7,404 |
| `ads_ocean_vessel_relation` | 226,192 | 226,192 | 226,192 |
| `ads_vessel_flag_year` | 687 | 687 | 687 |
| `ads_vessel_class_year` | 80 | 80 | 80 |

步骤9、18、21全部PASS即完成三方行数、批次和SHA256对账。构建脚本还自动确认：海洋趋势回卷2,687,015条，船舶月度/船旗国/船型均回卷18,638,286条，船旗国和船型均回卷149,660个船舶业务键。

## 十、打包并手动下载CSV

### 步骤23：在ECS打包

发送：

```bash
bash scripts/cloud/package_delivery_assets.sh
```

必须看到 `DELIVERY_ASSET_PACKAGE=PASS`。发送：

```bash
cd /home/ecs-user/oceaninsight-project1/output/delivery
ls -lh OceanInsight-project1-ads-csv.tar.gz \
  OceanInsight-project1-ads-csv.tar.gz.sha256
```

压缩包约30.4 MiB。发送：

```bash
sha256sum -c OceanInsight-project1-ads-csv.tar.gz.sha256
```

必须看到 `OceanInsight-project1-ads-csv.tar.gz: OK`。

### 步骤24：在Workbench手动下载

这一步操作文件管理器，不在Shell输入：

1. 进入 `/home/ecs-user/oceaninsight-project1/output/delivery`。
2. 右键下载 `OceanInsight-project1-ads-csv.tar.gz`。
3. 右键下载 `OceanInsight-project1-ads-csv.tar.gz.sha256`。
4. 等待文件任务中心两项都显示绿色“完成”。

### 步骤25：在Windows校验下载包

打开学生电脑的Windows PowerShell，发送：

```powershell
Set-Location "$env:USERPROFILE\Downloads"
```

```powershell
$expected=(Get-Content .\OceanInsight-project1-ads-csv.tar.gz.sha256).Split()[0].ToUpper()
$actual=(Get-FileHash .\OceanInsight-project1-ads-csv.tar.gz -Algorithm SHA256).Hash.ToUpper()
if($actual -eq $expected){'ADS_DOWNLOAD_SHA256=PASS'}else{'ADS_DOWNLOAD_SHA256=FAIL'}
```

必须看到 `ADS_DOWNLOAD_SHA256=PASS`。

### 步骤26：在Windows解压检查

继续发送：

```powershell
tar -xzf .\OceanInsight-project1-ads-csv.tar.gz
```

```powershell
(Get-ChildItem .\output\ads_csv -Filter 'ads_*.csv' -File).Count
```

必须输出 `7`。发送：

```powershell
Test-Path .\output\ads_csv\ads_csv_manifest.json
```

必须输出 `True`。学生无需Codex即可完成下载与验证。

## 十一、项目一最终验收

### 步骤27：重新运行12项测试

回到Workbench Shell发送：

```bash
cd /home/ecs-user/oceaninsight-project1/starter
../.venv/bin/python -m unittest discover -s tests -v
```

必须看到 `Ran 12 tests` 和 `OK`。

### 步骤28：检查8个核心PASS

发送完整代码块：

```bash
for pair in \
  'spark_hive_ods_verify.log|SPARK_HIVE_ODS_VERIFY=PASS' \
  'spark_build_dwd.log|SPARK_DWD_BUILD=PASS' \
  'spark_build_dws.log|SPARK_DWS_BUILD=PASS' \
  'spark_build_ads_core.log|SPARK_ADS_CORE_BUILD=PASS' \
  'spark_build_ads_vessel_class.log|SPARK_ADS_VESSEL_CLASS_BUILD=PASS' \
  'publish_mariadb_overview.log|SPARK_JDBC_OVERVIEW_WRITE=PASS' \
  'publish_mariadb_ads.log|SPARK_JDBC_ADS_ALL_WRITE=PASS' \
  'export_ads_csv.log|SPARK_ADS_CSV_EXPORT=PASS'
do
  file="${pair%%|*}"; marker="${pair#*|}"
  grep -Fq "$marker" "/data/oceaninsight/logs/$file" || exit 1
  echo "$marker"
done
echo 'PROJECT1_ALL_PASS_MARKERS=PASS'
```

必须显示8个PASS和 `PROJECT1_ALL_PASS_MARKERS=PASS`。

### 步骤29：检查服务、端口和磁盘

依次发送：

```bash
jps
```

```bash
sudo ss -lntp | grep -E ':(3306|9000|9083|10000)\b'
```

```bash
df -h /
```

```bash
hdfs dfs -du -h /oceaninsight
```

实测最终系统盘约使用19 GiB、剩余约76 GiB。不要删除服务器数据、日志或备份。

## 十二、最终通过标准

| 范围 | 通过标准 |
|---|---|
| 学生代码 | 5个TODO完成，12项测试OK |
| 异构转换 | 2份NPZ、300份NC、5年船舶、149,660条主数据 |
| ODS | 海洋3,357,840、活动18,638,286、主数据149,660 |
| DWD/DWS | 清洗、唯一键和明细回卷全部PASS |
| Hive ADS | 7张表行数、业务键、回卷正确 |
| MariaDB | 7张表，批次唯一为 `student-ads-20260825` |
| CSV | 7份CSV、Manifest及逐文件SHA256正确 |
| 下载 | 本机包SHA256通过，解出7份CSV和Manifest |
| 保留 | 服务正常，不删除数据、日志、备份，不释放ECS |

以上全部通过，项目一四天实验完成。项目二的FineBI安全接入另行讲解；项目一结束时不要开放MariaDB公网3306。
