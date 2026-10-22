#!/usr/bin/env python3
"""Точка входа платформы: python run.py  ->  http://localhost:5000"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.main import app  # noqa: E402

if __name__ == "__main__":
    host = "0.0.0.0"           # доступ по сети (телефоны/планшеты)
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    print(f"Платформа запущена: http://localhost:{port}")
    app.run(host=host, port=port, debug=True)
