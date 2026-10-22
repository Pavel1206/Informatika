#!/usr/bin/env python3
"""Скрипт создания практических работ для учебной платформы.

ЭТОТ ФАЙЛ — дорабатываемая заготовка: замените/дополните логику своими
полями и проверками, пока здесь реализованы основные сценарии.

Использование:

  # 1) из JSON-файла (удобно для пакетного импорта / шаблонов):
  python scripts/create_practical.py --json examples/practical.json

  # 2) параметрами командной строки:
  python scripts/create_practical.py --title "Работа 1" --subject "Python" \
      --group ИС-21 --deadline 2026-11-01 \
      --task "Вывести Hello World" --task "Написать калькулятор"

  # 3) интерактивный режим (вопросы в консоли):
  python scripts/create_practical.py --interactive

JSON-формат файла практической работы (расширяйте поле tasks при доработке):
{
  "title": "Практическая работа №1",
  "subject": "Программирование",
  "group_name": "ИС-21",
  "description": "Основы Python",
  "deadline": "2026-11-01",
  "tasks": [
    {"title": "Задание 1", "text": "Описание задания", "points": 5},
    "Просто текст задания"
  ]
}
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# позволяем запускать скрипт из любой директории проекта
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import database as db  # noqa: E402


def load_from_json(path: str) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not data.get("title"):
        raise ValueError("В JSON обязательно поле 'title'")
    return data


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Создание практической работы")
    src = p.add_mutually_exclusive_group()
    src.add_argument("--json", help="путь к JSON-файлу с описанием работы")
    src.add_argument("--interactive", action="store_true", help="анкетный режим")
    p.add_argument("--title")
    p.add_argument("--subject", default="")
    p.add_argument("--group", default="", help="название группы ('' = все группы)")
    p.add_argument("--description", default="")
    p.add_argument("--deadline", default="", help="ГГГГ-ММ-ДД")
    p.add_argument("--task", action="append", default=[],
                   help="текст задания; можно повторять несколько раз")
    p.add_argument("--teacher-login", help="логин преподавателя-создателя (опционально)")
    return p


def interactive_mode() -> dict:
    print("=== Создание практической работы (интерактивный режим) ===")
    title = input("Название работы: ").strip()
    if not title:
        sys.exit("Название не может быть пустым.")
    return {
        "title": title,
        "subject": input("Предмет: ").strip(),
        "group_name": input("Группа (пусто = все группы): ").strip(),
        "description": input("Краткое описание: ").strip(),
        "deadline": input("Срок сдачи ГГГГ-ММ-ДД (или пусто): ").strip(),
        "tasks": collect_tasks_from_prompt(),
    }


def collect_tasks_from_prompt() -> list:
    tasks = []
    print("Вводите задания по одному. Пустая строка — конец списка.")
    while True:
        text = input(f"Задание {len(tasks) + 1}: ").strip()
        if not text:
            break
        points_raw = input("    Баллы (по умолчанию 1): ").strip() or "1"
        try:
            points = int(points_raw)
        except ValueError:
            points = 1
        tasks.append({"title": f"Задание {len(tasks) + 1}", "text": text, "points": points})
    return tasks


def save_practical(data: dict, teacher_login: str | None = None) -> int:
    teacher_id = None
    if teacher_login:
        user = db.get_user_by_login(teacher_login.lower())
        if user and user["role"] == "teacher":
            teacher_id = user["id"]
        else:
            print(f"Внимание: преподаватель '{teacher_login}' не найден — "
                  f"работа создается без автора.")
    pid = db.insert_practical(
        title=data["title"],
        subject=data.get("subject", ""),
        group_name=data.get("group_name", ""),
        description=data.get("description", ""),
        tasks_json=json.dumps(data.get("tasks", []), ensure_ascii=False),
        deadline=data.get("deadline", ""),
        created_by=teacher_id,
    )
    print(f"✔ Практическая работа «{data['title']}» создана, id = {pid}")
    return pid


def main(argv=None) -> None:
    args = build_parser().parse_args(argv)
    db.init_db()

    if args.json:
        data = load_from_json(args.json)
    elif args.interactive:
        data = interactive_mode()
    else:  # параметры CLI (заполняются через --title и т.д.)
        if not args.title:
            p_err = ("Укажите источник данных: --json ФАЙЛ, --interactive "
                     "или минимум --title \"Название\"")
            sys.exit(p_err)
        data = {
            "title": args.title,
            "subject": args.subject,
            "group_name": args.group,
            "description": args.description,
            "deadline": args.deadline,
            "tasks": [{"title": f"Задание {i}", "text": t, "points": 1}
                      for i, t in enumerate(args.task, 1)],
        }

    save_practical(data, teacher_login=args.teacher_login)


if __name__ == "__main__":
    main()
