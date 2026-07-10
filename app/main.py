from __future__ import annotations

from flask import Flask, jsonify, render_template

from spark_job import build_dashboard, get_skill_scores

app = Flask(__name__, template_folder="../templates", static_folder="../static")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "service": "SmartCare Training Analytics"})


@app.route("/api/dashboard")
def dashboard():
    return jsonify(build_dashboard())


@app.route("/api/chart")
def chart_data():
    return jsonify(get_skill_scores())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
