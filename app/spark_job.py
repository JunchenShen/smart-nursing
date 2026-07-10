from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import sys
from typing import Any

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DATA_DIR = PROJECT_ROOT / "data"
REQUIRED_FILES = [
    "students.csv",
    "courses.csv",
    "resources.csv",
    "learning_events.csv",
    "assessment_scores.csv",
]


def _ensure_sample_data() -> None:
    if all((DATA_DIR / name).exists() for name in REQUIRED_FILES):
        return

    from scripts.generate_sample_data import generate_all

    generate_all(DATA_DIR)


@lru_cache(maxsize=1)
def get_spark() -> SparkSession:
    return (
        SparkSession.builder.appName("SmartCareTrainingAnalytics")
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.ui.showConsoleProgress", "false")
        .getOrCreate()
    )


def _read_csv(spark: SparkSession, name: str) -> DataFrame:
    return spark.read.option("header", True).option("inferSchema", True).csv(str(DATA_DIR / name))


@lru_cache(maxsize=1)
def load_tables() -> dict[str, DataFrame]:
    _ensure_sample_data()
    spark = get_spark()
    tables = {
        "students": _read_csv(spark, "students.csv"),
        "courses": _read_csv(spark, "courses.csv"),
        "resources": _read_csv(spark, "resources.csv"),
        "events": _read_csv(spark, "learning_events.csv"),
        "scores": _read_csv(spark, "assessment_scores.csv"),
    }
    return tables


def _round_columns(df: DataFrame, cols: list[str]) -> DataFrame:
    for col in cols:
        df = df.withColumn(col, F.round(F.col(col), 2))
    return df


def _collect(df: DataFrame, limit: int | None = None) -> list[dict[str, Any]]:
    rows = df.limit(limit).collect() if limit else df.collect()
    return [row.asDict(recursive=True) for row in rows]


def _score_level(score_col: str = "final_score") -> F.Column:
    return (
        F.when(F.col(score_col) >= 85, F.lit("优秀"))
        .when(F.col(score_col) >= 70, F.lit("达标"))
        .when(F.col(score_col) >= 60, F.lit("待巩固"))
        .otherwise(F.lit("高风险"))
    )


def build_dashboard() -> dict[str, Any]:
    tables = load_tables()
    students = tables["students"]
    courses = tables["courses"]
    resources = tables["resources"]
    events = tables["events"]
    scores = tables["scores"]

    course_scores = scores.join(courses, "course_id")
    event_features = (
        events.groupBy("student_id", "course_id")
        .agg(
            F.sum("duration_minutes").alias("study_minutes"),
            F.sum("completed").alias("completed_resources"),
            F.countDistinct("resource_id").alias("accessed_resources"),
            F.avg("progress_percent").alias("avg_progress"),
            F.max("event_date").alias("last_event_date"),
        )
        .join(scores, ["student_id", "course_id"], "right")
        .fillna({"study_minutes": 0, "completed_resources": 0, "accessed_resources": 0, "avg_progress": 0})
    )

    learner_course = (
        event_features.join(students, "student_id").join(courses, "course_id")
        .withColumn("score_level", _score_level())
        .withColumn(
            "risk_score",
            F.greatest(
                F.lit(0),
                F.lit(100)
                - F.col("final_score") * 0.72
                - F.col("avg_progress") * 0.18
                - F.least(F.col("study_minutes") / 12, F.lit(10)),
            ),
        )
    )

    overview_row = learner_course.agg(
        F.countDistinct("student_id").alias("student_count"),
        F.countDistinct("course_id").alias("course_count"),
        F.round(F.avg("final_score"), 2).alias("avg_score"),
        F.round(F.avg("avg_progress"), 2).alias("avg_progress"),
        F.round(F.sum("study_minutes") / 60, 2).alias("total_study_hours"),
        F.round(F.avg(F.when(F.col("final_score") >= 60, 1).otherwise(0)) * 100, 2).alias("pass_rate"),
        F.sum(F.when(F.col("risk_score") >= 38, 1).otherwise(0)).alias("risk_records"),
    ).first()

    course_effect = (
        learner_course.groupBy("course_id", "course_name", "category", "tag")
        .agg(
            F.countDistinct("student_id").alias("learners"),
            F.avg("final_score").alias("avg_score"),
            F.avg("avg_progress").alias("avg_progress"),
            F.sum("study_minutes").alias("study_minutes"),
            (F.avg(F.when(F.col("final_score") >= 60, 1).otherwise(0)) * 100).alias("pass_rate"),
        )
    )
    course_effect = _round_columns(course_effect, ["avg_score", "avg_progress", "pass_rate"]).orderBy("avg_score")

    tag_weakness = (
        learner_course.groupBy("tag")
        .agg(
            F.count("*").alias("records"),
            F.avg("final_score").alias("avg_score"),
            (F.avg(F.when(F.col("final_score") < 60, 1).otherwise(0)) * 100).alias("weak_rate"),
        )
    )
    tag_weakness = _round_columns(tag_weakness, ["avg_score", "weak_rate"]).orderBy(F.desc("weak_rate"), "avg_score")

    format_usage = (
        events.join(resources, "resource_id")
        .groupBy("format")
        .agg(
            F.count("*").alias("views"),
            F.sum("completed").alias("completed"),
            F.avg("progress_percent").alias("avg_progress"),
        )
        .withColumn("completion_rate", F.col("completed") / F.col("views") * 100)
    )
    format_usage = _round_columns(format_usage, ["avg_progress", "completion_rate"]).orderBy(F.desc("views"))

    weekly_activity = (
        events.withColumn("week", F.date_format(F.date_trunc("week", F.to_date("event_date")), "MM-dd"))
        .groupBy("week")
        .agg(
            F.round(F.sum("duration_minutes") / 60, 2).alias("study_hours"),
            F.countDistinct("student_id").alias("active_students"),
            F.count("*").alias("events"),
        )
        .orderBy("week")
    )

    score_distribution = (
        learner_course.withColumn("score_level", _score_level())
        .groupBy("score_level")
        .count()
        .orderBy(F.expr("array_position(array('优秀','达标','待巩固','高风险'), score_level)"))
    )

    risk_window = Window.partitionBy("student_id").orderBy(F.desc("risk_score"))
    learner_risk = (
        learner_course.withColumn("rn", F.row_number().over(risk_window))
        .where(F.col("rn") == 1)
        .select(
            "student_name",
            "organization",
            "course_name",
            "tag",
            F.round("final_score", 2).alias("final_score"),
            F.round("avg_progress", 2).alias("avg_progress"),
            F.round("study_minutes", 2).alias("study_minutes"),
            F.round("risk_score", 2).alias("risk_score"),
        )
        .orderBy(F.desc("risk_score"))
    )

    weak_courses = course_effect.orderBy("avg_score").limit(3).select("course_name", "tag").collect()
    recommendations = [
        {
            "title": f"加强「{row['course_name']}」专项训练",
            "detail": f"该课程平均成绩偏低，建议增加{row['tag']}情境案例、短测验和课后复盘任务。",
        }
        for row in weak_courses
    ]
    recommendations.extend(
        [
            {
                "title": "对高风险学员建立跟踪清单",
                "detail": "优先关注成绩低、学习进度慢、学习时长不足的学员，安排导师一对一补训。",
            },
            {
                "title": "优化课程资源格式组合",
                "detail": "结合资源完成率调整视频、文档、题库和实操清单比例，提高移动端学习效率。",
            },
        ]
    )

    return {
        "overview": overview_row.asDict(),
        "course_effect": _collect(course_effect),
        "tag_weakness": _collect(tag_weakness),
        "format_usage": _collect(format_usage),
        "weekly_activity": _collect(weekly_activity),
        "score_distribution": _collect(score_distribution),
        "learner_risk": _collect(learner_risk, 10),
        "recommendations": recommendations[:5],
    }


def get_skill_scores() -> dict[str, list[Any]]:
    dashboard = build_dashboard()
    return {
        "categories": [item["course_name"] for item in dashboard["course_effect"]],
        "values": [item["avg_score"] for item in dashboard["course_effect"]],
    }
