# 第2天：完成5个TODO与转换异构数据

版本：学生实操版 V1.0  
适用环境：已经完成第1天，并使用 `ecs-user` 登录ECS  
今日目标：恢复服务，解压Source，配置Python环境，完成5个TODO和12项测试，生成2份NPZ报告、300份海洋CSV、5份年度船舶活动CSV及1份船舶主数据CSV。

> 严格按顺序操作。后台命令显示PID只代表已经启动；只有日志出现指定PASS或DONE才算完成。发现已有PID、日志或输出时先检查，不要重复运行。

## 一、恢复第1天环境

### 步骤1：确认登录用户

在Workbench的Shell终端发送：

```bash
whoami
```

必须输出 `ecs-user`。如果显示 `root`，发送 `exit`，再用 `ecs-user` 重新登录。

### 步骤2：检查资源

依次发送：

```bash
nproc
```

```bash
free -h
```

```bash
df -h /
```

预期为4核、约7.3 GiB内存。今天会生成数GiB数据，可用磁盘少于20 GiB时停止。

### 步骤3：恢复HDFS

发送：

```bash
jps
```

如果已经看到 `NameNode` 和 `DataNode`，不要重复启动，直接进入步骤4。如果没有看到，依次发送：

```bash
hdfs --daemon start namenode
```

```bash
hdfs --daemon start datanode
```

```bash
sleep 5
```

```bash
jps
```

现在必须看到 `NameNode` 和 `DataNode`。这里只启动已有HDFS，绝对不要执行 `hdfs namenode -format`。

### 步骤4：确认旧目录还在

发送：

```bash
hdfs dfs -ls /oceaninsight
```

应能列出 `raw`、`ods`、`dwd`、`dws`、`ads` 和 `tmp`。

### 步骤5：恢复HiveServer2

先确认MariaDB和Hive Metastore。依次发送：

```bash
sudo systemctl is-active mariadb
```

```bash
sudo systemctl is-active oceaninsight-hive-metastore
```

两条都应输出 `active`。如果其中一条不是 `active`，依次发送：

```bash
sudo systemctl start mariadb
```

```bash
sudo systemctl start oceaninsight-hive-metastore
```

```bash
sleep 10
```

然后发送：

```bash
sudo systemctl restart oceaninsight-hiveserver2
```

发送下面的等待循环：

```bash
for i in {1..12}; do
  if sudo ss -lntp | grep -q ':10000'; then
    echo 'HIVESERVER2_PORT=PASS'
    break
  fi
  echo "等待HiveServer2：${i}/12"
  sleep 10
done
```

最多等待约2分钟，必须看到 `HIVESERVER2_PORT=PASS`。

## 二、检查并解压学生包

### 步骤6：确认四个文件存在

发送：

```bash
cd /home/ecs-user/oceaninsight-project1/packages
```

```bash
ls -lh OceanInsight-project1-source.zip \
  OceanInsight-project1-source.sha256 \
  OceanInsight-project1-starter.zip \
  OceanInsight-project1-starter.sha256
```

必须列出四个文件。Source约208 MiB，Starter很小：前者保存数据，后者保存代码和配置。

### 步骤7：再次校验两个ZIP

依次发送：

```bash
sha256sum -c OceanInsight-project1-source.sha256
```

```bash
sha256sum -c OceanInsight-project1-starter.sha256
```

必须分别看到：

```text
OceanInsight-project1-source.zip: OK
OceanInsight-project1-starter.zip: OK
```

出现 `FAILED` 时不要解压，重新上传对应ZIP。

### 步骤8：确认Starter已经解压

发送：

```bash
test -f /home/ecs-user/oceaninsight-project1/starter/pyproject.toml \
  -a -f /home/ecs-user/oceaninsight-project1/starter/.extract_verify \
  && echo 'STARTER_ALREADY_EXTRACTED=YES' \
  || echo 'STARTER_ALREADY_EXTRACTED=NO'
```

第1天正常完成时应显示 `YES`。第1天的完整解压命令会在正式目录建立验证标志；如果显示 `NO`，不要在第2天继续覆盖或补解压，返回第1天步骤14重新完成Starter解压。

### 步骤9：通过临时目录完整解压Source

先发送：

```bash
test -f /home/ecs-user/oceaninsight-project1/source/.extract_verify \
  && echo 'SOURCE_ALREADY_EXTRACTED=YES' \
  || echo 'SOURCE_ALREADY_EXTRACTED=NO'
```

第一次应显示 `NO`。确认还没有正式目录：

```bash
cd /home/ecs-user/oceaninsight-project1
```

```bash
test ! -e source && echo 'SOURCE_TARGET_READY=YES'
```

必须看到 `SOURCE_TARGET_READY=YES`。继续发送完整代码块：

```bash
(
  set -e
  SOURCE_STAGE=$(mktemp -d \
    /home/ecs-user/oceaninsight-project1/source_extracting.XXXXXX)
  python3 -m zipfile -e \
    packages/OceanInsight-project1-source.zip \
    "$SOURCE_STAGE"
  test "$(find "$SOURCE_STAGE/ocean_nc" -type f -name '*.nc' | wc -l)" -eq 300
  test "$(find "$SOURCE_STAGE/prediction_npz" -type f -name '*.npz' | wc -l)" -eq 2
  test "$(find "$SOURCE_STAGE/vessel_zip" -type f -name '*.zip' | wc -l)" -eq 5
  test "$(find "$SOURCE_STAGE/vessel_master" -type f -name '*.csv' | wc -l)" -eq 1
  touch "$SOURCE_STAGE/.extract_verify"
  mv "$SOURCE_STAGE" source
  echo 'SOURCE_EXTRACT_VERIFY=PASS'
)
```

必须看到 `SOURCE_EXTRACT_VERIFY=PASS`。先在随机临时目录验证全部数量，再改名为正式目录；中途中断不会留下一个看似完整的 `source`。

### 步骤10：核对Source数量

依次发送：

```bash
find source/ocean_nc -type f -name '*.nc' | wc -l
```

```bash
find source/prediction_npz -type f -name '*.npz' | wc -l
```

```bash
find source/vessel_zip -type f -name '*.zip' | wc -l
```

```bash
find source/vessel_master -type f -name '*.csv' | wc -l
```

预期依次为 `300`、`2`、`5`、`1`。数量不一致时停止。

## 三、创建Python环境

### 步骤11：创建虚拟环境

发送：

```bash
cd /home/ecs-user/oceaninsight-project1
python3 -m venv .venv
```

`.venv`用于隔离本项目依赖，不污染系统Python。

### 步骤12：升级pip并安装依赖

发送：

```bash
.venv/bin/pip install \
  -i https://mirrors.aliyun.com/pypi/simple \
  --upgrade pip
```

发送：

```bash
.venv/bin/pip install \
  -i https://mirrors.aliyun.com/pypi/simple \
  -r starter/requirements.txt
```

等待NumPy、SciPy和psutil安装完成。

### 步骤13：可编辑安装Starter

发送：

```bash
.venv/bin/pip install -e starter
```

`-e`表示保存源码后立即生效，不必重复安装。验证：

```bash
.venv/bin/python -c "import oceaninsight, numpy, scipy, psutil; print('PYTHON_ENV=PASS')"
```

必须看到 `PYTHON_ENV=PASS`。

## 四、完成5个TODO

### 步骤14：打开代码并确认TODO

在Workbench左侧文件树打开：

```text
/home/ecs-user/oceaninsight-project1/starter/src/oceaninsight/core.py
```

Shell发送：

```bash
grep -n 'TODO [1-5]' \
  /home/ecs-user/oceaninsight-project1/starter/src/oceaninsight/core.py
```

应看到TODO 1—5各一处。不要改函数名、参数名或其他文件。

### 步骤15：运行修改前测试

发送：

```bash
cd /home/ecs-user/oceaninsight-project1/starter
../.venv/bin/python -m unittest discover -s tests -v
```

5项核心测试因 `NotImplementedError` 失败是正确现象，证明Starter没有夹带答案。

> 最初服务器实操时是11项测试；收口阶段新增“主数据已有血缘字段时覆盖而不重复追加”的回归测试，因此最终学生包应为12项。新增测试不改变5个TODO。

### 步骤16：TODO 1——经度标准化

在 `core.py` 中将 `normalize_lon` 整个函数替换为：

```python
def normalize_lon(lon: float) -> float:
    """Normalize longitude to [-180, 180), keeping 180 as -180."""
    return ((float(lon) + 180.0) % 360.0) - 180.0
```

作用：把0—360度经度统一为-180—180度，例如200度变成-160度。

### 步骤17：TODO 2——映射2°网格

将 `grid_cell` 整个函数替换为：

```python
def grid_cell(lat: float, lon: float, size: float = 2.0) -> tuple[float, float, str]:
    lon = normalize_lon(lon)
    lat_ll = math.floor(float(lat) / size) * size
    lon_ll = math.floor(lon / size) * size
    return lat_ll, lon_ll, f"g{size:g}_{lat_ll:+06.1f}_{lon_ll:+07.1f}"
```

作用：把坐标落到2°×2°网格左下角，并生成稳定的 `grid_id`。

### 步骤18：TODO 3——区域判断

将 `in_region` 整个函数替换为：

```python
def in_region(lat: float, lon: float, bounds: dict) -> bool:
    lon = normalize_lon(lon)
    return (
        bounds["lat_min"] <= float(lat) <= bounds["lat_max"]
        and bounds["lon_min"] <= lon <= bounds["lon_max"]
    )
```

作用：判断坐标是否在10°N—50°N、120°E—160°E内，边界点也保留。

### 步骤19：TODO 4——深度分层

将 `depth_level` 整个函数替换为：

```python
def depth_level(depth_m: float) -> str:
    depth = float(depth_m)
    if depth <= 10:
        return "SURFACE"
    if depth <= 200:
        return "SHALLOW"
    if depth <= 750:
        return "MIDDLE"
    return "DEEP"
```

作用：划分表层、浅层、中层和深层，判断顺序不能颠倒。

### 步骤20：TODO 5——流速与流向

将 `current_metrics` 整个函数替换为：

```python
def current_metrics(u: float, v: float) -> tuple[float, float]:
    """Return speed and oceanographic direction-to in degrees clockwise from north."""
    speed = math.hypot(float(u), float(v))
    direction = (math.degrees(math.atan2(float(u), float(v))) + 360.0) % 360.0
    return speed, direction
```

作用：由东西向 `u` 和南北向 `v` 计算流速及从正北顺时针计量的流向。

### 步骤21：保存并检查语法

按 `Ctrl+S` 保存。Shell发送：

```bash
../.venv/bin/python -m py_compile src/oceaninsight/core.py
```

没有输出表示语法正确；出现 `SyntaxError` 时返回编辑器检查缩进。

### 步骤22：运行最终测试

发送：

```bash
../.venv/bin/python -m unittest discover -s tests -v
```

必须看到：

```text
Ran 12 tests

OK
```

## 五、生成NPZ报告

NPZ没有真实日期、经纬度和深度，只生成结构报告，不伪造业务字段，也不与海洋或船舶数据关联。

### 步骤23：创建目录并生成两份报告

发送：

```bash
mkdir -p ../output/npz_reports
```

```bash
../.venv/bin/python -m oceaninsight.cli npz \
  --input ../source/prediction_npz/train_data_target.npz \
  --output ../output/npz_reports/train_data_target.json
```

```bash
../.venv/bin/python -m oceaninsight.cli npz \
  --input ../source/prediction_npz/test_data.npz \
  --output ../output/npz_reports/test_data.json
```

### 步骤24：验收NPZ形状

发送完整代码块：

```bash
../.venv/bin/python - <<'PY'
import json
from pathlib import Path
root = Path('../output/npz_reports')
train = json.loads((root / 'train_data_target.json').read_text())
test = json.loads((root / 'test_data.json').read_text())
assert train['arrays']['data_train']['shape'] == [16625, 37, 12]
assert train['arrays']['target_train']['shape'] == [16625, 37, 1]
assert test['arrays']['data_test']['shape'] == [8625, 37, 12]
print('NPZ_REPORT_VERIFY=PASS')
PY
```

必须看到 `NPZ_REPORT_VERIFY=PASS`。

## 六、转换一个NC文件

### 步骤25：转换2017年1月温度NC

发送：

```bash
mkdir -p ../output/smoke
```

```bash
../.venv/bin/python -m oceaninsight.cli \
  --config conf/pipeline.json \
  nc \
  --input ../source/ocean_nc/temperature/IAPv4_Temp_monthly_1_6000m_year_2017_month_01.nc \
  --output ../output/smoke/temperature_2017-01.csv \
  --manifest ../output/smoke/temperature_2017-01.manifest.json \
  --batch-id student-nc-smoke
```

### 步骤26：验收单个NC

发送完整代码块：

```bash
../.venv/bin/python - <<'PY'
import json
from pathlib import Path
csv_path = Path('../output/smoke/temperature_2017-01.csv')
report = json.loads(Path('../output/smoke/temperature_2017-01.manifest.json').read_text())
stats = report['metrics']['nc']
with csv_path.open(encoding='utf-8') as stream:
    lines = sum(1 for _ in stream)
assert stats['input_cells'] == 6400
assert stats['output_rows'] == 6400
assert stats['invalid_values'] == 1464
assert lines == 6401
print('NC_SMOKE_VERIFY=PASS')
PY
```

必须看到 `NC_SMOKE_VERIFY=PASS`。6401行包括表头；缺失值留空并标为 `MISSING`。

## 七、后台转换300个NC

### 步骤27：确认正式输出为空

发送：

```bash
test ! -e ../output/ods/ocean \
  && echo 'NC_OUTPUT_READY=YES' \
  || echo 'NC_OUTPUT_READY=NO'
```

第一次必须显示 `YES`。脚本检测到已有正式输出会停止，防止覆盖。

### 步骤28：启动后台任务并保存PID

发送：

```bash
sudo install -d -o ecs-user -g ecs-user \
  /data/oceaninsight/logs
```

这条命令在目录不存在时创建它，并确保 `ecs-user` 能写日志；目录已经存在时也会修正所有者。

```bash
nohup bash scripts/cloud/run_nc_all.sh \
  > /data/oceaninsight/logs/run_nc_all.log 2>&1 < /dev/null &
```

终端显示的数字是PID，不代表完成。立即发送：

```bash
echo $! > /data/oceaninsight/logs/run_nc_all.pid
```

```bash
cat /data/oceaninsight/logs/run_nc_all.pid
```

### 步骤29：等待并查看原任务

先等待60秒：

```bash
sleep 60
```

```bash
ps -p "$(cat /data/oceaninsight/logs/run_nc_all.pid)" -f
```

```bash
tail -n 40 /data/oceaninsight/logs/run_nc_all.log
```

PID存在表示仍在运行；PID不存在可能已经结束。日志仍显示 `NC 数字/300` 时继续等待60秒，再查看同一个PID和日志，不要重启。最终必须看到：

```text
NC_CSV_COUNT=300
NC_MANIFEST_COUNT=300
NC_ALL_VERIFY=PASS
NC_ALL_DONE
```

### 步骤30：扫描NC日志和数量

发送：

```bash
grep -E 'Traceback|Error|FAIL' /data/oceaninsight/logs/run_nc_all.log \
  || echo 'NC_LOG_ERROR_SCAN=PASS'
```

```bash
find ../output/ods/ocean -type f -name '*.csv' | wc -l
```

必须看到 `NC_LOG_ERROR_SCAN=PASS` 和 `300`。

## 八、流式转换2017年船舶ZIP

年度ZIP内部是逐日CSV。程序逐成员、逐行读取，不整体解压，可减少磁盘占用。

### 步骤31：启动2017任务并保存PID

发送：

```bash
mkdir -p ../output/ods/vessel
```

```bash
nohup ../.venv/bin/python -m oceaninsight.cli \
  --config conf/pipeline.json \
  vessel \
  --input ../source/vessel_zip/vessel-teaching-2017.zip \
  --output ../output/ods/vessel/vessel_activity_2017.csv \
  --manifest ../output/ods/vessel/vessel_activity_2017.manifest.json \
  --batch-id student-vessel-2017 \
  > /data/oceaninsight/logs/vessel_2017.log 2>&1 < /dev/null &
```

```bash
echo $! > /data/oceaninsight/logs/vessel_2017.pid
```

### 步骤32：等待并查看2017任务

发送：

```bash
sleep 60
```

```bash
ps -p "$(cat /data/oceaninsight/logs/vessel_2017.pid)" -f
```

```bash
tail -n 30 /data/oceaninsight/logs/vessel_2017.log
```

PID仍在时再等待60秒。实测关键结果为：

```text
"files": 123
"input_rows": 2928426
"output_rows": 2928426
"invalid_rows": 0
"outside_region_rows": 0
```

### 步骤33：逐行验收2017结果

发送完整代码块：

```bash
../.venv/bin/python - <<'PY'
import csv
from pathlib import Path
path = Path('../output/ods/vessel/vessel_activity_2017.csv')
rows, bad = 0, 0
months, years = set(), set()
with path.open(encoding='utf-8', newline='') as stream:
    for row in csv.DictReader(stream):
        rows += 1
        months.add(row['month']); years.add(row['year'])
        lat, lon = float(row['source_grid_lat']), float(row['source_grid_lon'])
        if row['quality_flag'] != 'VALID' or not (10 <= lat <= 50 and 120 <= lon <= 160):
            bad += 1
assert rows == 2928426
assert months == {'01', '04', '07', '10'}
assert years == {'2017'}
assert bad == 0
print('VESSEL_2017_VERIFY=PASS')
PY
```

扫描约385 MiB文件需要时间。必须看到 `VESSEL_2017_VERIFY=PASS`。

## 九、串行转换2018—2021年

### 步骤34：启动四年任务

发送：

```bash
nohup bash scripts/cloud/run_vessel_2018_2021.sh \
  > /data/oceaninsight/logs/run_vessel_2018_2021.log 2>&1 < /dev/null &
```

```bash
echo $! > /data/oceaninsight/logs/run_vessel_2018_2021.pid
```

脚本严格按2018、2019、2020、2021串行执行。不要开四个终端并发运行。

### 步骤35：等待并查看四年任务

实测约2分42秒。先发送：

```bash
sleep 60
```

```bash
ps -p "$(cat /data/oceaninsight/logs/run_vessel_2018_2021.pid)" -f
```

```bash
tail -n 40 /data/oceaninsight/logs/run_vessel_2018_2021.log
```

未完成时继续等待60秒查看原日志。只有看到下面一行才完成：

```text
VESSEL_2018_2021_ALL_DONE
```

### 步骤36：验收五年汇总

发送完整代码块：

```bash
../.venv/bin/python - <<'PY'
import json
from pathlib import Path
root = Path('../output/ods/vessel')
rows = 0
size = 0
for year in range(2017, 2022):
    csv_path = root / f'vessel_activity_{year}.csv'
    report = json.loads((root / f'vessel_activity_{year}.manifest.json').read_text())
    stats = report['metrics']['vessel']
    rows += stats['output_rows']; size += csv_path.stat().st_size
    assert stats['invalid_rows'] == 0
assert rows == 18638286
assert size == 2567548151
assert len(list(root.glob('vessel_activity_*.csv'))) == 5
assert not list(root.glob('*.tmp'))
print(f'VESSEL_TOTAL_ROWS={rows}')
print('VESSEL_FIVE_YEAR_VERIFY=PASS')
PY
```

必须看到18,638,286行和 `VESSEL_FIVE_YEAR_VERIFY=PASS`。

## 十、筛选船舶主数据

### 步骤37：运行筛选脚本

脚本从五年活动CSV收集唯一 `(mmsi, year)`，只保留实际出现的主数据，并覆盖旧血缘字段。

发送：

```bash
../.venv/bin/python scripts/cloud/filter_vessel_master.py
```

关键结果应为：

```text
"required_keys": 149660
"input_rows": 149660
"output_rows": 149660
"missing_keys": 0
"output_bytes": 33171404
```

### 步骤38：验收主数据

发送完整代码块：

```bash
../.venv/bin/python - <<'PY'
import csv
from pathlib import Path
path = Path('../output/ods/vessel/vessel_master.csv')
with path.open(encoding='utf-8', newline='') as stream:
    reader = csv.DictReader(stream)
    fields = reader.fieldnames or []
    rows, bad, keys = 0, 0, set()
    for row in reader:
        rows += 1; keys.add((row['mmsi'], row['year']))
        if row['batch_id'] != 'student-vessel-master' or row['source_file'] != 'vessel_master.csv':
            bad += 1
assert len(fields) == 24
assert fields.count('batch_id') == 1
assert fields.count('source_file') == 1
assert rows == 149660 and len(keys) == 149660 and bad == 0
print('VESSEL_MASTER_VERIFY=PASS')
PY
```

必须看到 `VESSEL_MASTER_VERIFY=PASS`。两个血缘字段各只有一列，没有重复追加成26列。

## 十一、第2天最终验收

### 步骤39：核对成果数量

依次发送：

```bash
find ../output/npz_reports -type f -name '*.json' | wc -l
```

```bash
find ../output/ods/ocean -type f -name '*.csv' | wc -l
```

```bash
find ../output/ods/ocean -type f -name '*.manifest.json' | wc -l
```

```bash
find ../output/ods/vessel -type f -name 'vessel_activity_*.csv' | wc -l
```

```bash
find ../output -type f -name '*.tmp' | wc -l
```

预期依次为 `2`、`300`、`300`、`5`、`0`。

### 步骤40：核对完成标志和磁盘

发送：

```bash
grep -E 'NC_ALL_VERIFY=PASS|NC_ALL_DONE' \
  /data/oceaninsight/logs/run_nc_all.log
```

```bash
grep 'VESSEL_2018_2021_ALL_DONE' \
  /data/oceaninsight/logs/run_vessel_2018_2021.log
```

```bash
df -h /
```

实测此阶段完成后系统盘仍有约81 GiB可用。

## 十二、第2天验收表

| 验收项 | 通过标准 |
|---|---|
| 学生代码 | 5个TODO完成，`Ran 12 tests`、`OK` |
| NPZ | 2份JSON，`NPZ_REPORT_VERIFY=PASS` |
| 单个NC | 6,400条、1,464个缺失，`NC_SMOKE_VERIFY=PASS` |
| 全部NC | 300个CSV和Manifest，`NC_ALL_VERIFY=PASS` |
| 2017船舶 | 2,928,426条，`VESSEL_2017_VERIFY=PASS` |
| 五年船舶 | 18,638,286条，`VESSEL_FIVE_YEAR_VERIFY=PASS` |
| 船舶主数据 | 149,660行、149,660唯一键、24列 |
| 临时文件 | `.tmp`数量为0 |

全部通过后，第2天完成。不要删除 `source`、`starter`、`output`、PID或日志；第3天将通过DataX写入HDFS并建立Hive ODS。
