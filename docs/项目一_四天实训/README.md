# OceanInsight 项目一：四天学生实训入口

> 当前状态：四天Markdown正文已完成命令级审校。请使用同批次发放的最终 `source.zip + starter.zip` 及SHA256文件，不要混用历史压缩包。HTML版将在Markdown确认后另行生成。

本目录是学生唯一操作入口。请严格按第1天到第4天顺序执行，不要跳天，不要同时运行两个全量任务。

1. [第1天：购买ECS与安装完整环境](第1天_购买ECS与安装完整环境.md)
2. [第2天：完成TODO与转换异构数据](第2天_完成TODO与转换异构数据.md)
3. [第3天：DataX入湖与Hive数仓加工](第3天_DataX入湖与Hive数仓加工.md)
4. [第4天：Spark ADS发布与项目验收](第4天_Spark_ADS发布与项目验收.md)

统一约定：ECS 用户为 `ecs-user`，项目目录为 `/home/ecs-user/oceaninsight-project1`，所有命令均在阿里云 Workbench 的 Shell 终端执行。出现 `PASS` 才进入下一步。

本教程不包含 FineBI。FineBI 数据连接、数据集和仪表板从项目二开始。

## 四条安全红线

- NameNode 只在第1天首次初始化时格式化一次，以后绝不再次格式化。
- 不展示、复制或提交 `~/.config/oceaninsight/*.cnf` 中的密码。
- 不使用 `chmod 777`，不把数据库端口向 `0.0.0.0/0` 开放。
- Workbench 断开后先查看原 PID 和日志，禁止直接重复启动同一任务。

## 每天结束前

看到当天最后一个 PASS 后，保存终端日志。停止按量付费 ECS 时选择“节省停机模式”，不要释放实例；再次启动后先按教程恢复 HDFS 和 HiveServer2。
