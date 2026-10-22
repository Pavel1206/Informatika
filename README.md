# 🎓 Информационная платформа для студентов и преподавателей

Кроссплатформенное веб-приложение (Windows / macOS / Linux / любые браузеры,
включая мобильные — адаптивная вёрстка). Стек: **Python 3.10+, Flask, SQLite**.

## Быстрый старт

```bash
pip install -r requirements.txt
python run.py                # откройте http://localhost:5000
```

## Функциональность

### 1. Авторизация (`/login`, `/register`)
- Отдельные роли: **студент** и **преподаватель**; выбор роли при входе.
- **Пароли хранятся только в зашифрованном виде** — необратимый хеш
  `scrypt + соль` (werkzeug `generate_password_hash/check_password_hash`).
  В открытом виде пароли не сохраняются нигде (ни в БД, ни в логах).
- Кабинет студента: свои практические работы (по группе) и результаты экзамена.
- Кабинет преподавателя: все работы (+ удаление) и таблица результатов демоэкзамена.

### 2. Практические работы — python-скрипт (`scripts/create_practical.py`)
Заготовка дорабатывается под ваши нужды (поля, проверки, форматы заданий).
Три режима:
```bash
python scripts/create_practical.py --json examples/practical.json
python scripts/create_practical.py --title "Работа 1" --group ИС-21 --task "Задание А" --task "Задание Б"
python scripts/create_practical.py --interactive
```
Работы сразу появляются в кабинете платформы (`/practicals/<id>`).

### 3. Демоэкзамен — интегрированный html-стенд (`/demo-exam`)
Файлы: `app/templates/demo_exam.html` + `app/static/exam.js`.
⚠️ **Интеграция вашего готового html-файла**: замените содержимое блока
`<div id="exam-stand">` и массив `QUESTIONS` в `exam.js` на свой стенд.
В коде вашего файла в момент завершения экзамена вызовите:
```js
window.finishExam({ score, max_score, passed, details }) // или просто finishExam()
```
Результат уйдёт в БД через `POST /api/exam-result` и будет виден преподавателю.

## Управление пользователями (удаление)

Войдите как **преподаватель** → в меню появится пункт **«Пользователи»** (`/users`):
список всех студентов и преподавателей с фильтрами по ролям и кнопкой **«Удалить»**
(с подтверждением). Особенности:
- удалять может только преподаватель;
- нельзя удалить собственную учётную запись;
- вместе с пользователем удаляются его результаты экзаменов; созданные им
  практические работы остаются (просто без автора).

Альтернатива без веб-интерфейса (из папки проекта):
```powershell
python -c "from app import database as db; [print(u['id'], u['role'], u['login'], u['full_name']) for u in db.list_users()]"
python -c "from app import database as db; print(db.delete_user(ИД))"
```

## Структура проекта
```
run.py                     — точка входа
app/main.py                — маршруты Flask (авторизация, работы, экзамен)
app/database.py            — схема SQLite и функции доступа к данным
app/templates/*.html       — страницы (login, register, dashboard, demo_exam…)
app/static/style.css       — оформление (адаптивное)
app/static/exam.js         — логика демоэкзамена
scripts/create_practical.py— python-скрипт создания практических работ
examples/practical.json    — пример данных для скрипта
instance/platform.db       — база (создаётся автоматически)
```

## Тестовые данные
Создайте аккаунты через `/register` (например: преподаватель `ivanov/secret123`,
студент `petrov/stud123`, группа ИС-21) — либо используйте регистрацию в UI.
