# 基于 Spark 的智慧护理培训数据分析系统

面向老年护理培训机构与医疗服务机构的培训数据分析平台。系统使用 Flask 提供 Web 服务，使用 PySpark 对学员学习行为、课程资源、考核成绩等数据进行聚合分析，并通过 ECharts 展示课程效果、薄弱环节、高风险学员和个性化培训建议。

## 项目功能

- 培训数据采集整合：支持学员、课程、课程资源、学习行为、考核成绩五类 CSV 数据。
- 多维度资源管理：按课程类别、标签、资源格式、终端类型统计培训资源使用情况。
- 学习行为分析：分析学习时长、完成情况、进度、周活跃趋势。
- 培训效果评估：统计平均成绩、通过率、成绩等级分布、课程效果排名。
- 薄弱环节识别：按护理技能标签识别薄弱项，例如失智照护、压疮预防、跌倒预防等。
- 个性化建议：根据低分课程与高风险学员生成培训优化建议。
- 可视化展示：使用 ECharts 构建 PC 端交互式数据看板。
- 交互分析：支持课程类别、护理标签、课程、风险阈值、关键词搜索等筛选，并支持图表点击联动。
- 登录与权限：支持管理员、培训教师、机构负责人三类角色。

## 技术栈

- 后端：Python、Flask
- 大数据处理：Spark、PySpark
- 数据存储：CSV 文件，可扩展到 HDFS、Hive、MySQL
- 数据库与大数据存储：MySQL 8.0、HDFS
- 前端：HTML、CSS、JavaScript、ECharts
- 部署：Docker、Linux/macOS

## 目录结构

```text
.
├── app/
│   ├── main.py              # Flask 入口与 API
│   └── spark_job.py         # Spark 数据读取与分析逻辑
├── data/                    # 生成或导入的训练数据
├── database/
│   └── init.sql             # MySQL 建库建表脚本
├── docs/
│   ├── DATA_GENERATION.md   # 模拟数据客观规律说明
│   ├── AUTH_ROLES.md        # 登录与角色权限说明
│   ├── HDFS_MODE.md         # HDFS 模式说明
│   └── INTERACTION_DESIGN.md # 页面交互设计说明
├── scripts/
│   ├── generate_sample_data.py
│   ├── import_to_mysql.py
│   └── upload_to_hdfs.sh
├── static/
│   └── js/echarts.min.js
├── templates/
│   └── index.html           # 可视化看板页面
├── Dockerfile
├── docker-compose.hdfs.yml
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 数据说明

如果没有真实数据，可以直接使用项目内置脚本生成模拟数据。模拟数据不是随便写死的几条记录，而是按照护理培训业务结构生成，包括学员报名、课程资源访问、学习进度、考试成绩等，适合课程设计演示。

生成的数据文件如下：

| 文件 | 含义 | 关键字段 |
| --- | --- | --- |
| `students.csv` | 学员信息 | 学员编号、姓名、年龄、机构、岗位、学习终端 |
| `courses.csv` | 课程信息 | 课程编号、课程名称、类别、标签、难度、课时 |
| `resources.csv` | 资源信息 | 资源编号、课程编号、资源标题、格式、时长、终端 |
| `learning_events.csv` | 学习行为日志 | 学员编号、课程编号、资源编号、日期、学习分钟、进度、是否完成 |
| `assessment_scores.csv` | 考核成绩 | 学员编号、课程编号、期中成绩、期末成绩、实操成绩、出勤率 |

手动生成数据：

```bash
python scripts/generate_sample_data.py
```

系统启动时如果发现 `data/` 缺少 CSV，也会自动生成一份示例数据。

### 模拟数据的客观规律

数据生成脚本遵循以下可解释规则：

- 学员基础能力近似服从正态分布，大多数学员集中在中等水平。
- 初级、中级、高级课程设置不同难度惩罚，课程越难平均成绩越低。
- 学习时长、资源完成数量、学习进度会正向影响考试成绩。
- 移动端学习占比较高，用于模拟护理培训中的碎片化学习场景。
- 资源访问不是 100%，用于模拟漏学、跳学和重点学习行为。

详细说明见：[docs/DATA_GENERATION.md](docs/DATA_GENERATION.md)。

### 扩大数据规模

默认生成 3000 名学员。该规模按 8GB 内存电脑设计，通常会产生约 6-7 万条学习行为日志和约 1.6 万条成绩记录。

可以通过参数调整规模：

```bash
python scripts/generate_sample_data.py --students 1000 --event-days 180
```

8GB 内存推荐演示规模：

```bash
python scripts/generate_sample_data.py --students 3000 --event-days 180
```

如果机器内存为 16GB 或以上，可以尝试 5000-10000 名学员。

## 页面交互说明

系统登录后进入培训分析工作台。页面不再采用长页面堆叠，而是分为四个业务页签：

- 总览：核心指标、课程效果对比、成绩等级分布。
- 课程与薄弱项：薄弱标签分析和课程明细表。
- 风险跟踪：高风险学员清单和培训优化建议。
- 资源与趋势：资源格式使用表现和周学习活跃趋势。

看板支持培训管理场景中的交互分析：

- 按课程类别筛选，例如基础护理、临床技能、安全照护。
- 按护理标签筛选，例如失智照护、跌倒预防、压疮预防。
- 按风险阈值筛选高风险学员。
- 搜索学员姓名、机构、课程和标签。
- 点击“标签薄弱环节”图表中的标签，自动筛选该护理标签。
- 个性化培训建议会随当前筛选条件更新。

交互设计说明见：[docs/INTERACTION_DESIGN.md](docs/INTERACTION_DESIGN.md)。

## 登录与角色权限

系统提供三类演示账户：

| 角色 | 账号 | 默认密码 | 说明 |
| --- | --- | --- | --- |
| 管理员 | `admin` | `admin123` | 查看全局指标和全部风险学员 |
| 培训教师 | `teacher` | `teacher123` | 查看负责护理标签下的数据 |
| 机构负责人 | `org` | `org123` | 查看本机构风险学员 |

详细说明见：[docs/AUTH_ROLES.md](docs/AUTH_ROLES.md)。

## 本地运行

建议先在你已有的 Python 环境中运行。如果后续要新建或修改 conda 环境，需要先确认后再操作。

```bash
pip install -r requirements.txt
python app/main.py
```

浏览器打开：

```text
http://127.0.0.1:5000
```

## Docker 运行

构建镜像：

```bash
docker build -t smart-care-training .
```

启动容器：

```bash
docker run --rm -p 5000:5000 smart-care-training
```

访问：

```text
http://127.0.0.1:5000
```

## Docker Compose + MySQL 运行

如果需要体现数据库技术栈，推荐使用 Compose 模式。该模式会启动：

- `mysql`：MySQL 8.0 明细数据库。
- `importer`：把 `data/*.csv` 导入 MySQL。
- `web`：Flask + Spark 分析服务，设置 `DATA_SOURCE=mysql` 后从 MySQL 读取数据。

启动：

```bash
docker compose up --build
```

访问：

```text
http://127.0.0.1:5001
```

MySQL 本机连接信息：

```text
host: 127.0.0.1
port: 3307
database: smart_care_training
user: training_user
password: training_pass
```

停止：

```bash
docker compose down
```

如果要连同 MySQL 数据卷一起清理：

```bash
docker compose down -v
```

## Docker Compose + HDFS 运行

如果需要体现 HDFS 大数据存储技术栈，可以使用 HDFS 模式。该模式会启动：

- `namenode`：HDFS NameNode。
- `datanode`：HDFS DataNode。
- `hdfs-uploader`：把 `data/*.csv` 上传到 HDFS。
- `web`：Flask + Spark 分析服务，设置 `DATA_SOURCE=hdfs` 后从 HDFS 读取数据。

按 8GB 内存推荐先生成 3000 名学员数据：

```bash
python scripts/generate_sample_data.py --students 3000 --event-days 180
```

启动：

```bash
docker compose -f docker-compose.yml -f docker-compose.hdfs.yml up --build
```

访问系统：

```text
http://127.0.0.1:5001
```

访问 HDFS NameNode 页面：

```text
http://127.0.0.1:9870
```

查看 HDFS 文件：

```bash
docker exec smart-care-namenode hdfs dfs -ls /smart-care-training
```

详细说明见：[docs/HDFS_MODE.md](docs/HDFS_MODE.md)。

## API 接口

健康检查：

```text
GET /api/health
```

看板完整数据：

```text
GET /api/dashboard
```

兼容旧图表示例接口：

```text
GET /api/chart
```

## 如何替换为真实数据

将真实数据整理成 `data/` 下同名 CSV，并保持字段名一致即可。真实场景中可以按以下方式扩展：

- 从 MySQL 导入学员、课程、考试成绩等结构化数据。
- 从移动端、PC 端埋点日志导入学习行为数据。
- 将 CSV 替换为 HDFS 或 Hive 表，在 `app/spark_job.py` 中改用 `spark.read.table()` 或 HDFS 路径读取。
- 将 Spark 分析结果定时写入 MySQL/Redis，前端接口直接读取缓存结果。

当前项目已经提供 MySQL 建表和导入脚本：

- 建表脚本：`database/init.sql`
- 导入脚本：`scripts/import_to_mysql.py`
- HDFS 上传脚本：`scripts/upload_to_hdfs.sh`
- MySQL 编排文件：`docker-compose.yml`
- HDFS 编排文件：`docker-compose.hdfs.yml`

## 可扩展方向

- 增加登录与角色权限：管理员、培训教师、机构负责人。
- 增加课程资源管理后台：上传视频、文档、题库、实操清单。
- 接入 Hive 数仓：建立 ODS、DWD、DWS、ADS 分层。
- 接入 Redis：缓存看板指标，提高接口响应速度。
- 使用 JMeter 做接口压测，分析 Spark 本地模式与集群模式性能差异。
- 使用 Nginx + Docker Compose 做部署编排。
