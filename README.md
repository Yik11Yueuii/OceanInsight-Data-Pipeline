# OceanInsight Data Pipeline

教师工作室背景下的海洋数据工程技术实践，覆盖海洋观测与船舶活动数据的格式转换、数据质量核验、离线数仓加工及分析结果发布。项目同时整理了实施步骤与可复现的技术教程。

## 项目概览

处理流程（离线批处理）：

```text
NetCDF / NPZ / Vessel ZIP
          ↓ Python 清洗与格式标准化
        DataX → HDFS → Hive ODS / DWD / DWS
                          ↓ Spark ADS
                       CSV / MariaDB → FineBI
```

- 使用 Python 处理 NetCDF/NPZ 海洋观测数据及压缩船舶记录，包含流式读取与网格化。
- 通过 DataX、HDFS、Hive、Spark 组织 ODS / DWD / DWS / ADS 加工。
- 使用执行日志、记录数核验、结果对账和测试脚本验证流程。
- 整理云服务器部署、数据处理、数仓加工和结果验收的操作教程。

## 技术栈

Python 3、NumPy / Pandas、NetCDF、DataX、HDFS、Hive、Spark、MariaDB、FineBI。

## 公开仓库目录

```text
conf/                 脱敏配置模板
datax/                数据传输任务模板
docs/                 实施记录与操作教程
scripts/cloud/        云端数据处理和发布脚本
sql/hive/             数仓建表和转换 SQL
sql/mysql/            ADS 发布表结构
src/oceaninsight/     Python 数据处理代码
tests/                测试代码
操作教程文档/         操作说明及公开示意图片
```

## 快速检查

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=src
python -m unittest discover -s tests -v
python -m oceaninsight.cli --help
```

Windows PowerShell 可使用 `.venv\Scripts\Activate.ps1` 激活虚拟环境。

> 当前公开代码保留教学 TODO。首次运行全部测试时，部分测试会因未补全 TODO 而失败；请参考 [实施教程](docs/项目一_四天实训/README.md)。这不是公开即可一键复现的生产数据平台。

## 数据与公开范围

为避免未经授权公开工作室提供的资料，**原始数据压缩包、Starter 交付包及需求规格说明书不在当前公开版本中分发**。相关教程保留技术步骤，但其中提到的数据包需要使用者通过合法授权的来源自行获取，不代表公开仓库能够独立复现全部结果。

本项目使用的是教学与演示场景数据，不代表实际海洋监测平台的生产数据。任何第三方数据的使用与再分发均应遵守其原始许可。

## 配置与使用边界

配置文件使用占位符或本地文件读取凭据，不包含用于访问实际服务器的密钥。请勿向 Git 仓库提交密码、私钥、服务器访问令牌或未经授权的数据资料。

本仓库目前未附加开源许可证；在未获得明确授权的情况下，不授予第三方复制、再发布或商业使用权。
