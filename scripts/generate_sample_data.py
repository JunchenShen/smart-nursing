from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path


SEED = 20260709


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


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _student_name(index: int) -> str:
    surnames = "赵钱孙李周吴郑王冯陈刘杨黄何郭马罗梁宋唐许"
    given = ["静", "伟", "芳", "敏", "磊", "娜", "强", "洋", "婷", "杰", "慧", "超", "雪", "鹏", "琳"]
    return f"{surnames[index % len(surnames)]}{given[index % len(given)]}"


def generate_all(data_dir: str | Path = "data", student_count: int = 120) -> None:
    random.seed(SEED)
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
                "platform": random.choices(["mobile", "pc"], weights=[0.64, 0.36], k=1)[0],
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
        base_ability = random.normalvariate(74, 10)
        chosen_courses = random.sample(courses, random.randint(4, 7))
        for course in chosen_courses:
            course_resources = [res for res in resources if res["course_id"] == course["course_id"]]
            study_minutes = 0
            progress_values = []
            completed_count = 0
            for res in course_resources:
                if random.random() < 0.84:
                    progress = max(8, min(100, int(random.normalvariate(76, 22))))
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
                            "event_date": (start_day + timedelta(days=random.randint(0, 84))).isoformat(),
                            "duration_minutes": actual_minutes,
                            "progress_percent": progress,
                            "completed": completed,
                            "device": random.choices(["mobile", "pc"], weights=[0.67, 0.33], k=1)[0],
                        }
                    )

            avg_progress = sum(progress_values) / len(progress_values) if progress_values else 0
            difficulty_penalty = {"初级": 0, "中级": 5, "高级": 9}[course["difficulty"]]
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
    generate_all()
    print("Sample training data generated in ./data")
