from __future__ import annotations

import csv
import random
import argparse
from datetime import date, timedelta
from pathlib import Path


SEED = 20260709
DEFAULT_STUDENT_COUNT = 3000
DEFAULT_EVENT_DAYS = 84
BASE_ABILITY_MEAN = 74
BASE_ABILITY_STDDEV = 10
RESOURCE_ACCESS_PROBABILITY = 0.84
PROGRESS_MEAN = 76
PROGRESS_STDDEV = 22
MOBILE_PLATFORM_WEIGHT = 0.64
MOBILE_EVENT_WEIGHT = 0.67
COURSE_COUNT_RANGE = (4, 7)
DIFFICULTY_PENALTY = {"初级": 0, "中级": 5, "高级": 9}


COURSES = [
    ("C001", "老年基础照护", "基础护理", "生活照护", "初级", 16),
    ("C002", "失智老人沟通与陪伴", "认知照护", "失智照护", "中级", 12),
    ("C003", "压疮预防与翻身转移", "临床技能", "压疮预防", "中级", 14),
    ("C004", "慢病监测与用药提醒", "健康管理", "慢病管理", "中级", 18),
    ("C005", "跌倒风险识别与应急处理", "安全照护", "跌倒预防", "高级", 10),
    ("C006", "康复训练辅助实操", "康复护理", "康复训练", "高级", 20),
    ("C007", "感染防控与清洁消毒", "院感管理", "感染防控", "初级", 8),
    ("C008", "临终关怀与心理支持", "人文照护", "心理支持", "高级", 10),
]

FORMATS = ["video", "document", "quiz", "checklist", "case"]
ORGANIZATIONS = ["安心护理培训中心", "康养医院护理部", "颐和养老服务站", "社区卫生服务中心"]
POSITIONS = ["护理员", "护士", "培训学员", "养老顾问"]
SURNAMES = [
    "赵", "钱", "孙", "李", "周", "吴", "郑", "王", "冯", "陈",
    "褚", "卫", "蒋", "沈", "韩", "杨", "朱", "秦", "尤", "许",
    "何", "吕", "施", "张", "孔", "曹", "严", "华", "金", "魏",
    "陶", "姜", "戚", "谢", "邹", "喻", "柏", "水", "窦", "章",
    "云", "苏", "潘", "葛", "奚", "范", "彭", "郎", "鲁", "韦",
]
GIVEN_FIRST = [
    "子", "文", "思", "嘉", "明", "欣", "若", "雨", "泽", "昊",
    "雅", "梓", "晨", "宇", "佳", "俊", "依", "启", "承", "诗",
    "静", "安", "乐", "睿", "书", "涵", "一", "宏", "亦", "清",
]
GIVEN_SECOND = [
    "涵", "轩", "怡", "宁", "琪", "然", "彤", "航", "妍", "杰",
    "萱", "辰", "瑜", "诺", "霖", "阳", "琳", "哲", "悦", "凯",
    "慧", "泽", "洋", "坤", "洁", "博", "璇", "铭", "雯", "远",
]
NAME_POOL_SIZE = len(SURNAMES) * len(GIVEN_FIRST) * len(GIVEN_SECOND)


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _student_name(index: int) -> str:
    if index >= NAME_POOL_SIZE:
        raise ValueError(f"student_count exceeds unique three-character name pool: {NAME_POOL_SIZE}")

    second_index = index % len(GIVEN_SECOND)
    first_index = (index // len(GIVEN_SECOND)) % len(GIVEN_FIRST)
    surname_index = (index // (len(GIVEN_FIRST) * len(GIVEN_SECOND))) % len(SURNAMES)
    return f"{SURNAMES[surname_index]}{GIVEN_FIRST[first_index]}{GIVEN_SECOND[second_index]}"


def generate_all(
    data_dir: str | Path = "data",
    student_count: int = DEFAULT_STUDENT_COUNT,
    event_days: int = DEFAULT_EVENT_DAYS,
    seed: int = SEED,
) -> None:
    random.seed(seed)
    data_dir = Path(data_dir)

    courses = [
        {
            "course_id": course_id,
            "course_name": name,
            "category": category,
            "tag": tag,
            "difficulty": difficulty,
            "hours": hours,
        }
        for course_id, name, category, tag, difficulty, hours in COURSES
    ]

    students = []
    for index in range(student_count):
        students.append(
            {
                "student_id": f"S{index + 1:04d}",
                "student_name": _student_name(index),
                "age": random.randint(22, 54),
                "organization": random.choice(ORGANIZATIONS),
                "position": random.choice(POSITIONS),
                "platform": random.choices(["mobile", "pc"], weights=[MOBILE_PLATFORM_WEIGHT, 1 - MOBILE_PLATFORM_WEIGHT], k=1)[0],
                "enroll_date": (date(2026, 3, 1) + timedelta(days=random.randint(0, 55))).isoformat(),
            }
        )

    resources = []
    resource_id = 1
    for course in courses:
        for seq in range(1, 6):
            fmt = FORMATS[(resource_id + seq) % len(FORMATS)]
            resources.append(
                {
                    "resource_id": f"R{resource_id:04d}",
                    "course_id": course["course_id"],
                    "resource_title": f"{course['course_name']}资源{seq}",
                    "format": fmt,
                    "duration_minutes": random.randint(6, 38) if fmt == "video" else random.randint(4, 22),
                    "terminal": random.choice(["mobile", "pc", "both"]),
                }
            )
            resource_id += 1

    events = []
    scores = []
    start_day = date(2026, 4, 1)
    for student in students:
        base_ability = random.normalvariate(BASE_ABILITY_MEAN, BASE_ABILITY_STDDEV)
        chosen_courses = random.sample(courses, random.randint(*COURSE_COUNT_RANGE))
        for course in chosen_courses:
            course_resources = [res for res in resources if res["course_id"] == course["course_id"]]
            study_minutes = 0
            progress_values = []
            completed_count = 0
            for res in course_resources:
                if random.random() < RESOURCE_ACCESS_PROBABILITY:
                    progress = max(8, min(100, int(random.normalvariate(PROGRESS_MEAN, PROGRESS_STDDEV))))
                    completed = 1 if progress >= random.randint(70, 92) else 0
                    actual_minutes = max(2, int(res["duration_minutes"] * progress / 100 + random.randint(-2, 7)))
                    study_minutes += actual_minutes
                    completed_count += completed
                    progress_values.append(progress)
                    events.append(
                        {
                            "event_id": f"E{len(events) + 1:06d}",
                            "student_id": student["student_id"],
                            "course_id": course["course_id"],
                            "resource_id": res["resource_id"],
                            "event_date": (start_day + timedelta(days=random.randint(0, event_days - 1))).isoformat(),
                            "duration_minutes": actual_minutes,
                            "progress_percent": progress,
                            "completed": completed,
                            "device": random.choices(["mobile", "pc"], weights=[MOBILE_EVENT_WEIGHT, 1 - MOBILE_EVENT_WEIGHT], k=1)[0],
                        }
                    )

            avg_progress = sum(progress_values) / len(progress_values) if progress_values else 0
            difficulty_penalty = DIFFICULTY_PENALTY[course["difficulty"]]
            engagement_bonus = min(12, study_minutes / max(1, int(course["hours"])) / 6) + completed_count * 1.2
            midterm = max(35, min(100, base_ability - difficulty_penalty + engagement_bonus + random.normalvariate(0, 8)))
            final_score = max(30, min(100, midterm * 0.42 + avg_progress * 0.28 + base_ability * 0.3 + random.normalvariate(0, 6)))
            practical = max(30, min(100, final_score + random.normalvariate(0, 7)))
            scores.append(
                {
                    "student_id": student["student_id"],
                    "course_id": course["course_id"],
                    "midterm_score": round(midterm, 2),
                    "final_score": round(final_score, 2),
                    "practical_score": round(practical, 2),
                    "attendance_rate": round(max(40, min(100, avg_progress + random.normalvariate(6, 10))), 2),
                }
            )

    _write_csv(data_dir / "students.csv", list(students[0].keys()), students)
    _write_csv(data_dir / "courses.csv", list(courses[0].keys()), courses)
    _write_csv(data_dir / "resources.csv", list(resources[0].keys()), resources)
    _write_csv(data_dir / "learning_events.csv", list(events[0].keys()), events)
    _write_csv(data_dir / "assessment_scores.csv", list(scores[0].keys()), scores)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate explainable smart-care training sample data.")
    parser.add_argument("--data-dir", default="data", help="Output directory for CSV files.")
    parser.add_argument("--students", type=int, default=DEFAULT_STUDENT_COUNT, help="Number of students to generate.")
    parser.add_argument("--event-days", type=int, default=DEFAULT_EVENT_DAYS, help="Learning event date range in days.")
    parser.add_argument("--seed", type=int, default=SEED, help="Random seed for reproducible experiments.")
    args = parser.parse_args()

    generate_all(args.data_dir, args.students, args.event_days, args.seed)
    print(f"Sample training data generated in {args.data_dir} with {args.students} students.")
