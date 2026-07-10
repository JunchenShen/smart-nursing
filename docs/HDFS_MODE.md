# HDFS 模式说明

HDFS 模式用于展示项目的大数据存储链路。它不是替代 MySQL，而是模拟真实系统中的日志湖/离线数仓入口。

## 架构位置

```text
模拟数据生成
  -> data/*.csv
  -> HDFS /smart-care-training
  -> Spark 读取 HDFS
  -> Flask API
  -> ECharts 交互看板
```

## 为什么引入 HDFS

- 学习行为日志属于追加型、大批量数据，适合落入 HDFS。
- Spark 可以直接读取 HDFS 上的 CSV，体现大数据离线分析链路。
- MySQL 更适合结构化业务数据管理，HDFS 更适合海量明细日志存储。
- 答辩时可以清楚说明“业务库 + 大数据存储 + 分析计算”的分层设计。

## 8GB 内存推荐规模

推荐使用 3000 名学员：

```bash
python scripts/generate_sample_data.py --students 3000 --event-days 180
```

大致会生成：

```text
学员：3000
课程：8
课程资源：40
学习行为日志：约 6-7 万条
考核成绩：约 1.6 万条
```

这个规模能体现 Spark/HDFS 的意义，同时对 8GB 内存机器相对友好。

## 启动 HDFS 模式

先生成推荐规模数据：

```bash
python scripts/generate_sample_data.py --students 3000 --event-days 180
```

再启动 HDFS 模式：

```bash
docker compose -f docker-compose.yml -f docker-compose.hdfs.yml up --build
```

访问系统：

```text
http://127.0.0.1:5001
```

访问 HDFS NameNode Web UI：

```text
http://127.0.0.1:9870
```

如果在 Apple Silicon Mac 上看到 `platform (linux/amd64) does not match linux/arm64/v8` 提示，说明 Hadoop 镜像通过兼容模式运行。该提示不影响本项目演示，但首次拉取和启动会更慢。

## HDFS 数据目录

上传脚本会把 CSV 上传到：

```text
hdfs://namenode:8020/smart-care-training
```

包含：

```text
students.csv
courses.csv
resources.csv
learning_events.csv
assessment_scores.csv
```

## 手动查看 HDFS 文件

```bash
docker exec smart-care-namenode hdfs dfs -ls /smart-care-training
```

查看前几行：

```bash
docker exec smart-care-namenode hdfs dfs -cat /smart-care-training/students.csv | head
```

## 停止服务

```bash
docker compose -f docker-compose.yml -f docker-compose.hdfs.yml down
```

如果需要清理 HDFS 和 MySQL 数据卷：

```bash
docker compose -f docker-compose.yml -f docker-compose.hdfs.yml down -v
```

## 数据源切换说明

后端通过 `DATA_SOURCE` 控制数据来源：

| DATA_SOURCE | 说明 |
| --- | --- |
| `csv` | 直接读取本地 `data/*.csv` |
| `mysql` | 从 MySQL 读取明细表 |
| `hdfs` | 从 HDFS 读取 CSV |

HDFS 模式下还会使用：

```text
HDFS_BASE_PATH=hdfs://namenode:8020/smart-care-training
SPARK_MASTER=local[2]
SPARK_DRIVER_MEMORY=1g
SPARK_SHUFFLE_PARTITIONS=6
```

这些参数是按 8GB 内存演示环境设置的，避免本地 Docker 同时运行 MySQL、HDFS、Spark 时过度占用资源。
