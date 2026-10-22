"""Информационная платформа для студентов и преподавателей.

Кроссплатформенное веб-приложение (Flask): работает на Windows/macOS/Linux,
доступно из браузера любого устройства, включая мобильные (адаптивная вёрстка).

Функциональность:
  1. Авторизация студентов и преподавателей (пароли — только в виде хешей scrypt);
  2. Практические работы (создаются внешним python-скриптом scripts/create_practical.py);
  3. Демоэкзамен — интегрированный html-стенд (app/templates/demo_exam.html),
     результаты сохраняются в базу платформы.
"""

from __future__ import annotations

import json
from functools import wraps

from flask import (Flask, flash, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from app import database as db

app = Flask(__name__)
app.secret_key = "dev-secret-change-me"  # в продакшене задавать через ENV

db.init_db()


# ---------- декораторы доступа ----------

def login_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        def inner(*args, **kwargs):
            uid = session.get("user_id")
            if not uid:
                return redirect(url_for("login"))
            user = db.get_user_by_id(uid)
            if user is None or (roles and user["role"] not in roles):
                session.clear()
                flash("Требуется повторный вход.", "warning")
                return redirect(url_for("login"))
            return fn(*args, **kwargs)
        return inner
    return wrapper


@app.context_processor
def inject_user():
    uid = session.get("user_id")
    user = db.get_user_by_id(uid) if uid else None
    return {"current_user": user}


# ---------- 1. авторизация ----------

@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        login_name = (request.form.get("login") or "").strip().lower()
        password = request.form.get("password") or ""
        role = request.form.get("role") or ""
        user = db.get_user_by_login(login_name)
        # проверка: пользователь существует, роль совпадает,
        # пароль сверяется с ХЕШЕМ (открытый пароль нигде не хранится)
        if user and user["role"] == role and check_password_hash(
                user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))
        error = "Неверный логин, пароль или роль."
    return render_template("login.html", error=error)


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        login_name = (request.form.get("login") or "").strip().lower()
        password = request.form.get("password") or ""
        password2 = request.form.get("password2") or ""
        role = request.form.get("role") or "student"
        full_name = (request.form.get("full_name") or "").strip()
        group_name = (request.form.get("group_name") or "").strip()
        subject = (request.form.get("subject") or "").strip()

        if role not in ("student", "teacher"):
            error = "Некорректная роль."
        elif not login_name or len(password) < 6:
            error = "Укажите логин и пароль не короче 6 символов."
        elif password != password2:
            error = "Пароли не совпадают."
        elif db.get_user_by_login(login_name):
            error = "Такой логин уже занят."
        else:
            # шифрование пароля: генерируем необратимый хеш (scrypt + salt)
            db.insert_user(login_name, generate_password_hash(password),
                           role, full_name, group_name, subject)
            flash("Регистрация завершена. Войдите в систему.", "success")
            return redirect(url_for("login"))
    return render_template("register.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------- главная (кабинет) ----------

@app.route("/dashboard")
@login_required("student", "teacher")
def dashboard():
    user = db.get_user_by_id(session["user_id"])
    practicals = db.list_practicals(user["group_name"] or None)
    results = db.list_exam_results() if user["role"] == "teacher" else []
    my_results = [r for r in db.list_exam_results() if r["user_id"] == user["id"]]
    return render_template("dashboard.html", practicals=practicals,
                           results=results, my_results=my_results)


# ---------- 2. практические работы ----------

@app.route("/practicals/<int:pid>")
@login_required("student", "teacher")
def practical_detail(pid: int):
    with db.get_db() as conn:
        row = conn.execute(
            "SELECT p.*, u.full_name AS teacher_name FROM practicals p "
            "LEFT JOIN users u ON u.id = p.created_by WHERE p.id = ?", (pid,)
        ).fetchone()
    if row is None:
        flash("Практическая работа не найдена.", "warning")
        return redirect(url_for("dashboard"))
    tasks = json.loads(row["tasks_json"] or "[]")
    return render_template("practical_detail.html", p=row, tasks=tasks)


@app.route("/practicals/<int:pid>/delete", methods=["POST"])
@login_required("teacher")
def practical_delete(pid: int):
    db.delete_practical(pid)
    flash("Практическая работа удалена.", "success")
    return redirect(url_for("dashboard"))


# ---------- 3. демоэкзамен (интегрированный html-стенд) ----------

@app.route("/demo-exam")
@login_required("student", "teacher")
def demo_exam():
    return render_template("demo_exam.html")


@app.route("/api/exam-result", methods=["POST"])
@login_required("student", "teacher")
def save_exam_result():
    """Принимает итог демоэкзамена из html-стенда и сохраняет в БД."""
    data = request.get_json(silent=True) or {}
    try:
        score = float(data.get("score", 0))
        max_score = float(data.get("max_score", 0))
    except (TypeError, ValueError):
        return {"ok": False, "error": "bad payload"}, 400
    passed = bool(data.get("passed"))
    details = json.dumps(data.get("details", {}), ensure_ascii=False)
    rid = db.insert_exam_result(session["user_id"], score, max_score, passed, details)
    return {"ok": True, "result_id": rid}


if __name__ == "__main__":
    # host=0.0.0.0 делает платформу доступной по локальной сети
    # (телефоны/планшеты студентов при размещении на сервере)
    app.run(host="0.0.0.0", port=5000, debug=True)
