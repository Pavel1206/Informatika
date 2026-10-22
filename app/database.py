"""Слой работы с базой данных (SQLite).

Таблицы:
    users        -- пользователи (студенты/преподаватели), пароли хранятся
                    только в виде криптографических хешей (scrypt)
    practicals   -- практические работы, создаваемые преподавателем
                    через scripts/create_practical.py
    exam_results -- результаты демоэкзамена (интегрированный html-стенд)
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "instance" / "platform.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_db():
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    login         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,               -- никогда не храним пароль в открытом виде
    role          TEXT NOT NULL CHECK (role IN ('student', 'teacher')),
    full_name     TEXT NOT NULL DEFAULT '',
    group_name    TEXT NOT NULL DEFAULT '',
    subject       TEXT NOT NULL DEFAULT '',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS practicals (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT NOT NULL,
    subject      TEXT NOT NULL DEFAULT '',
    group_name   TEXT NOT NULL DEFAULT '',
    description  TEXT NOT NULL DEFAULT '',
    tasks_json   TEXT NOT NULL DEFAULT '[]',   -- JSON-список заданий, легко расширять
    deadline     TEXT NOT NULL DEFAULT '',
    created_by   INTEGER REFERENCES users(id),
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS exam_results (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER REFERENCES users(id),
    score        REAL NOT NULL DEFAULT 0,
    max_score    REAL NOT NULL DEFAULT 0,
    passed       INTEGER NOT NULL DEFAULT 0,
    details_json TEXT NOT NULL DEFAULT '{}',
    finished_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def init_db() -> None:
    with get_db() as db:
        db.executescript(SCHEMA)


# ---------- users ----------

def insert_user(login: str, password_hash: str, role: str,
                full_name: str = "", group_name: str = "", subject: str = "") -> int:
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO users (login, password_hash, role, full_name, group_name, subject) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (login, password_hash, role, full_name, group_name, subject),
        )
        return cur.lastrowid


def get_user_by_login(login: str):
    with get_db() as db:
        return db.execute("SELECT * FROM users WHERE login = ?", (login,)).fetchone()


def get_user_by_id(user_id: int):
    with get_db() as db:
        return db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


# ---------- practicals ----------

def insert_practical(title: str, subject: str, group_name: str, description: str,
                     tasks_json: str, deadline: str, created_by: int | None = None) -> int:
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO practicals (title, subject, group_name, description, "
            "tasks_json, deadline, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (title, subject, group_name, description, tasks_json, deadline, created_by),
        )
        return cur.lastrowid


def list_practicals(group_name: str | None = None):
    with get_db() as db:
        if group_name:
            return db.execute(
                "SELECT p.*, u.full_name AS teacher_name FROM practicals p "
                "LEFT JOIN users u ON u.id = p.created_by "
                "WHERE p.group_name = ? OR p.group_name = '' ORDER BY p.created_at DESC",
                (group_name,),
            ).fetchall()
        return db.execute(
            "SELECT p.*, u.full_name AS teacher_name FROM practicals p "
            "LEFT JOIN users u ON u.id = p.created_by ORDER BY p.created_at DESC"
        ).fetchall()


def delete_practical(practical_id: int) -> None:
    with get_db() as db:
        db.execute("DELETE FROM practicals WHERE id = ?", (practical_id,))


# ---------- exam results ----------

def insert_exam_result(user_id: int | None, score: float, max_score: float,
                       passed: bool, details_json: str = "{}") -> int:
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO exam_results (user_id, score, max_score, passed, details_json) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, score, max_score, int(passed), details_json),
        )
        return cur.lastrowid


def list_exam_results(limit: int = 50):
    with get_db() as db:
        return db.execute(
            "SELECT e.*, u.login, u.full_name FROM exam_results e "
            "LEFT JOIN users u ON u.id = e.user_id "
            "ORDER BY e.finished_at DESC LIMIT ?", (limit,),
        ).fetchall()
