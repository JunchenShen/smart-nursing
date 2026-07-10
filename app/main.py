from __future__ import annotations

import os
from copy import deepcopy
from functools import wraps
from typing import Any, Callable

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from spark_job import build_dashboard, get_skill_scores

app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "smart-care-training-dev-secret")


def _hash_password(env_name: str, default: str) -> str:
    return generate_password_hash(os.getenv(env_name, default))


USERS = {
    "admin": {
        "password_hash": _hash_password("ADMIN_PASSWORD", "admin123"),
        "name": "系统管理员",
        "role": "admin",
        "role_name": "管理员",
        "permissions": ["全局指标", "课程分析", "风险学员", "资源趋势", "用户权限"],
    },
    "teacher": {
        "password_hash": _hash_password("TEACHER_PASSWORD", "teacher123"),
        "name": "培训教师",
        "role": "teacher",
        "role_name": "培训教师",
        "permissions": ["课程分析", "薄弱标签", "风险学员"],
        "allowed_tags": ["压疮预防", "跌倒预防", "感染防控"],
    },
    "org": {
        "password_hash": _hash_password("ORG_PASSWORD", "org123"),
        "name": "机构负责人",
        "role": "organization_manager",
        "role_name": "机构负责人",
        "permissions": ["机构风险学员", "培训建议"],
        "organization": "安心护理培训中心",
    },
}


def _public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in user.items() if key != "password_hash"}


def current_user() -> dict[str, Any] | None:
    username = session.get("username")
    if not username:
        return None
    user = USERS.get(username)
    if not user:
        session.clear()
        return None
    return {"username": username, **user}


def login_required(view: Callable):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            if request.path.startswith("/api/"):
                return jsonify({"error": "unauthorized"}), 401
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def _filter_rows(rows: list[dict[str, Any]], **equals: Any) -> list[dict[str, Any]]:
    result = rows
    for key, expected in equals.items():
        if expected is None:
            continue
        if isinstance(expected, list):
            result = [row for row in result if row.get(key) in expected]
        else:
            result = [row for row in result if row.get(key) == expected]
    return result


def _apply_role_scope(dashboard: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
    scoped = deepcopy(dashboard)
    role = user["role"]

    if role == "teacher":
        tags = user.get("allowed_tags", [])
        scoped["course_effect"] = _filter_rows(scoped["course_effect"], tag=tags)
        scoped["tag_weakness"] = _filter_rows(scoped["tag_weakness"], tag=tags)
        scoped["learner_risk"] = _filter_rows(scoped["learner_risk"], tag=tags)
    elif role == "organization_manager":
        organization = user.get("organization")
        scoped["learner_risk"] = _filter_rows(scoped["learner_risk"], organization=organization)

    scoped["auth"] = _public_user(user)
    return scoped


@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if current_user():
            return redirect(url_for("index"))
        return render_template("login.html", error="")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    user = USERS.get(username)
    if not user or not check_password_hash(user["password_hash"], password):
        return render_template("login.html", error="账号或密码不正确"), 401

    session["username"] = username
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/api/me")
@login_required
def me():
    user = current_user()
    return jsonify(_public_user(user or {}))


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "service": "SmartCare Training Analytics"})


@app.route("/api/dashboard")
@login_required
def dashboard():
    user = current_user()
    return jsonify(_apply_role_scope(build_dashboard(), user or {}))


@app.route("/api/chart")
@login_required
def chart_data():
    return jsonify(get_skill_scores())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
