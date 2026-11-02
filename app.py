import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg
from psycopg.rows import dict_row

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_db():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured")
    return psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row
    )


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id SERIAL PRIMARY KEY,
                role TEXT NOT NULL,
                company TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Applied',
                applied_date DATE NOT NULL,
                interview_date DATE
            )
        """)


@app.route("/")
def home():
    return jsonify({"message": "Job Application Tracker API is running"})


@app.route("/api/applications", methods=["GET"])
def get_applications():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM applications ORDER BY id DESC"
        ).fetchall()
    return jsonify(rows)


@app.route("/api/applications", methods=["POST"])
def add_application():
    data = request.get_json() or {}
    role = data.get("role", "").strip()
    company = data.get("company", "").strip()
    applied_date = data.get("applied_date")
    status = data.get("status", "Applied")
    interview_date = data.get("interview_date") or None

    if not role or not company or not applied_date:
        return jsonify({"error": "Role, company and date are required"}), 400

    with get_db() as conn:
        row = conn.execute("""
            INSERT INTO applications
            (role, company, status, applied_date, interview_date)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
        """, (role, company, status, applied_date, interview_date)).fetchone()

    return jsonify(row), 201


@app.route("/api/applications/<int:app_id>", methods=["PUT"])
def update_application(app_id):
    data = request.get_json() or {}

    with get_db() as conn:
        row = conn.execute("""
            UPDATE applications
            SET role = %s, company = %s, status = %s,
                applied_date = %s, interview_date = %s
            WHERE id = %s
            RETURNING *
        """, (
            data.get("role", "").strip(),
            data.get("company", "").strip(),
            data.get("status", "Applied"),
            data.get("applied_date"),
            data.get("interview_date") or None,
            app_id
        )).fetchone()

    if not row:
        return jsonify({"error": "Application not found"}), 404
    return jsonify(row)


@app.route("/api/applications/<int:app_id>", methods=["DELETE"])
def delete_application(app_id):
    with get_db() as conn:
        row = conn.execute("""
            DELETE FROM applications WHERE id = %s RETURNING id
        """, (app_id,)).fetchone()

    if not row:
        return jsonify({"error": "Application not found"}), 404
    return jsonify({"message": "Application deleted"})


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
