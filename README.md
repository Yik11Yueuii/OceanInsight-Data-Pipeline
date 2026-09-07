# OceanInsight Data Pipeline

面向海洋大数据的数据工程实践项目，覆盖多源海洋与船舶数据采集、清洗转换、DataX 入湖、Hive 数仓加工、Spark ADS 构建与 MariaDB 数据发布。

## 项目概览

项目使用 2017—2021 年海洋环境与船舶教学数据，构建从原始数据到分析应用层的完整处理链路：

1. 解析 NetCDF 海洋温度、盐度、溶解氧、热含量与海流数据。
2. 以流式方式处理年度船舶 ZIP 数据，避免整体解压造成资源浪费。
3. 对多源数据进行质量校验、空间网格化和标准化转换。
4. 使用 DataX 将数据写入 HDFS，并通过 Hive 建立 ODS、DWD、DWS 分层。
5. 使用 Spark 构建 ADS 指标，并发布到 CSV 或 MariaDB，供可视化分析使用。

## 技术栈

- Python 3
- NetCDF / NumPy / Pandas
- Hadoop HDFS / DataX
- Hive / Spark
- MariaDB

## 目录结构

```text
conf/               项目及云端服务配置模板
datax/              DataX 作业模板
docs/               Markdown 实训教程与实施记录
scripts/cloud/      数据处理、数仓加工和发布脚本
sql/hive/           Hive 分层建表与转换 SQL
sql/mysql/          MariaDB ADS 表结构与权限 SQL
src/oceaninsight/   Python 数据处理程序
tests/              单元测试
操作教程文档/       可离线查看的 HTML 操作教程
数据包/             原始教学数据、Starter 包及 SHA-256 校验文件
需求分析文档/       项目需求规格说明书
```

## 快速开始

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=src
python -m unittest discover -s tests -v
python -m oceaninsight.cli --help
```

Windows PowerShell 激活虚拟环境：

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "src"
```

完整环境搭建、数据处理和数仓发布步骤请参阅 [`docs/项目一_四天实训/README.md`](docs/项目一_四天实训/README.md)。

> 当前公开版本保留了 5 个教学 TODO。初次运行 12 项测试时应有 7 项通过、5 项因 `NotImplementedError` 失败；按第 2 天教程完成 TODO 后应全部通过。

## 数据说明

- `OceanInsight-project1-source.zip` 包含教学使用的 NetCDF、NPZ 与年度船舶数据，使用 Git LFS 管理。
- `OceanInsight-project1-starter.zip` 是代码与配置的原始交付包。
- 对应 `.sha256` 文件可用于验证下载完整性。
- 数据仅用于学习、实验和项目演示；二次使用前请确认原始数据许可及适用范围。

## 配置安全

仓库配置文件仅保留脱敏占位符。部署时请通过本地配置或环境变量提供真实密码，不要将凭据提交到 Git。

## License

本仓库暂未附加开源许可证。未经明确授权，默认保留所有权利。
