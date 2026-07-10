from __future__ import annotations

import csv
import os
import time
from pathlib import Path
from typing import Iterable

import pymysql


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", PROJECT_ROOT / "data"))

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "training_user"),
    "password": os.getenv("DB_PASSWORD", "training_pass"),
    "database": os.getenv("DB_NAME", "smart_care_training"),
    "charset": "utf8mb4",
    "autocommit": False,
}

TABLE_FILES = [
    ("students", "students.csv"),
    ("courses", "courses.csv"),
    ("resources", "resources.csv"),
    ("learning_events", "learning_events.csv"),
    ("assessment_scores", "assessment_scores.csv"),
]


def _connect_with_retry(retries: int = 30, delay: float = 2.0):
    last_error = None
    for _ in range(retries):
        try:
            return pymysql.connect(**DB_CONFIG)
        except pymysql.MySQLError as exc:
            last_error = exc
            time.sleep(delay)
    raise RuntimeError(f"Cannot connect to MySQL after {retries} retries: {last_error}")


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return list(reader.fieldnames or []), list(reader)


def _insert_rows(cursor, table: str, fields: list[str], rows: Iterable[dict[str, str]]) -> int:
    placeholders = ", ".join(["%s"] * len(fields))
    columns = ", ".join(f"`{field}`" for field in fields)
    update_clause = ", ".join(f"`{field}` = VALUES(`{field}`)" for field in fields)
    sql = f"INSERT INTO `{table}` ({columns}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {update_clause}"
    values = [tuple(row[field] for field in fields) for row in rows]
    if not values:
        return 0
    cursor.executemany(sql, values)
    return len(values)


def import_all() -> None:
    connection = _connect_with_retry()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            for table, _ in reversed(TABLE_FILES):
                cursor.execute(f"TRUNCATE TABLE `{table}`")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

            for table, filename in TABLE_FILES:
                fields, rows = _read_csv(DATA_DIR / filename)
                count = _insert_rows(cursor, table, fields, rows)
                print(f"Imported {count} rows into {table}")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    import_all()
