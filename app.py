import hashlib
import hmac
import os
import sqlite3
from functools import wraps

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

DATABASE_PATH = os.environ.get("AVI_HEALTH_DB", "avi_health.db")
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("AVI_HEALTH_SECRET", "development-only-change-me")

NAV_ITEMS = [
    ("Overview", "dashboard"),
    ("AI Copilot", "copilot"),
    ("Medical Records", "records"),
    ("Medications", "medications"),
    ("Health Tracking", "tracking"),
    ("Doctor Visit", "doctor"),
]


def get_db():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mail TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS health_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                details TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )


def hash_password(password):
    salt = os.urandom(16)
    password_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 150_000)
    return f"pbkdf2_sha256${salt.hex()}${password_hash.hex()}"


def verify_password(password, stored_hash):
    try:
        algorithm, salt_hex, password_hex = stored_hash.split("$", 2)
        if algorithm != "pbkdf2_sha256":
            return False
        expected = bytes.fromhex(password_hex)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 150_000)
        return hmac.compare_digest(expected, actual)
    except (TypeError, ValueError):
        return False


def get_current_user_id():
    with get_db() as connection:
        row = connection.execute(
            "SELECT id FROM users WHERE mail = ?", (session.get("user_mail"),)
        ).fetchone()
    return row["id"] if row else None


def login_required(view):
    @wraps(view)
    def protected_view(*args, **kwargs):
        if not session.get("user_mail"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return protected_view


init_db()


@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/dashboard")
@login_required
def home():
    with get_db() as connection:
        records = connection.execute(
            """
            SELECT id, title, category, details, created_at, updated_at
            FROM health_records
            WHERE user_id = ?
            ORDER BY updated_at DESC, id DESC
            """,
            (get_current_user_id(),),
        ).fetchall()
    return render_template(
        "dashboard.html",
        active="Overview",
        nav_items=NAV_ITEMS,
        user_name=session["user_mail"].split("@")[0].replace(".", " ").title(),
        records=[dict(record) for record in records],
    )


@app.route("/login")
def login():
    if session.get("user_mail"):
        return redirect(url_for("home"))
    return render_template("login.html", mode="login")


@app.route("/register")
def register_page():
    if session.get("user_mail"):
        return redirect(url_for("home"))
    return render_template("login.html", mode="register")


@app.post("/login")
def login_submit():
    mail = (request.form.get("mail") or "").strip().lower()
    password = request.form.get("password") or ""

    with get_db() as connection:
        user = connection.execute(
            "SELECT mail, password_hash FROM users WHERE mail = ?", (mail,)
        ).fetchone()

    if not user or not verify_password(password, user["password_hash"]):
        return render_template("login.html", mode="login", error="Invalid mail ID or password."), 401

    session.clear()
    session["user_mail"] = user["mail"]
    return redirect(url_for("home"))


@app.post("/register")
def register():
    mail = (request.form.get("mail") or "").strip().lower()
    password = request.form.get("password") or ""
    confirm_password = request.form.get("confirm_password") or ""

    if not mail or "@" not in mail:
        return render_template("login.html", mode="register", error="Enter a valid mail ID."), 400
    if len(password) < 8:
        return render_template("login.html", mode="register", error="Password must be at least 8 characters."), 400
    if password != confirm_password:
        return render_template("login.html", mode="register", error="Passwords do not match."), 400

    with get_db() as connection:
        try:
            connection.execute(
                "INSERT INTO users (mail, password_hash) VALUES (?, ?)",
                (mail, hash_password(password)),
            )
        except sqlite3.IntegrityError:
            return render_template("login.html", mode="register", error="This mail ID is already registered."), 400

    session.clear()
    session["user_mail"] = mail
    return redirect(url_for("home"))


@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.post("/api/copilot")
@login_required
def copilot():
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify({"answer": "Please enter a question."}), 400

    return jsonify({
        "answer": (
            "I can help you organize health information and prepare "
            "questions for a healthcare professional. For medical diagnosis "
            "or treatment decisions, consult a qualified clinician."
        )
    })


@app.route("/records")
@login_required
def records_page():
    return redirect(url_for("home"))


@app.get("/records/api")
@login_required
def records():
    user_id = get_current_user_id()
    with get_db() as connection:
        rows = connection.execute(
            """
            SELECT id, title, category, details, created_at, updated_at
            FROM health_records
            WHERE user_id = ?
            ORDER BY updated_at DESC, id DESC
            """,
            (user_id,),
        ).fetchall()
    return jsonify({"records": [dict(row) for row in rows]})


@app.post("/records")
@login_required
def create_record():
    title = (request.form.get("title") or "").strip()
    category = (request.form.get("category") or "").strip()
    details = (request.form.get("details") or "").strip()

    if not title or not category or not details:
        return jsonify({"error": "Title, category, and details are required."}), 400
    if len(title) > 120 or len(category) > 40 or len(details) > 2000:
        return jsonify({"error": "One or more fields exceed the allowed length."}), 400

    with get_db() as connection:
        cursor = connection.execute(
            """
            INSERT INTO health_records (user_id, title, category, details)
            VALUES (?, ?, ?, ?)
            """,
            (get_current_user_id(), title, category, details),
        )
        row = connection.execute(
            "SELECT * FROM health_records WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return jsonify({"record": dict(row)}), 201


@app.patch("/records/<int:record_id>")
@login_required
def update_record(record_id):
    allowed_fields = {"title", "category", "details"}
    updates = {key: value for key, value in request.form.items() if key in allowed_fields}
    if not updates:
        return jsonify({"error": "Provide a field to update."}), 400

    for field in updates:
        if len(updates[field].strip()) > {"title": 120, "category": 40, "details": 2000}[field]:
            return jsonify({"error": "One or more fields exceed the allowed length."}), 400

    assignments = ", ".join(f"{field} = ?" for field in updates)
    values = [updates[field].strip() for field in updates]
    values.extend([record_id, get_current_user_id()])

    with get_db() as connection:
        cursor = connection.execute(
            f"""
            UPDATE health_records
            SET {assignments}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            """,
            values,
        )
        if cursor.rowcount == 0:
            return jsonify({"error": "Record not found."}), 404
        row = connection.execute(
            "SELECT * FROM health_records WHERE id = ?", (record_id,)
        ).fetchone()
    return jsonify({"record": dict(row)})


@app.delete("/records/<int:record_id>")
@login_required
def delete_record(record_id):
    with get_db() as connection:
        cursor = connection.execute(
            "DELETE FROM health_records WHERE id = ? AND user_id = ?",
            (record_id, get_current_user_id()),
        )
    if cursor.rowcount == 0:
        return jsonify({"error": "Record not found."}), 404
    return "", 204


@app.route("/section/<section>")
@login_required
def section(section):
    labels = {
        "copilot": "AI Copilot",
        "records": "Medical Records",
        "medications": "Medications",
        "tracking": "Health Tracking",
        "doctor": "Doctor Visit",
    }
    title = labels.get(section, "Overview")
    return render_template("section.html", active=title, nav_items=NAV_ITEMS, section=title)


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
