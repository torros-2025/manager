"""Начальный файл """
from __future__ import annotations

from db import init_db
from gui import main_window


def main() -> None:
    init_db()
    main_window()


if __name__ == "__main__":
    main()
