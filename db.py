"""Доступ к данным (SQLite) и экспорт/импорт CSV/JSON.

Таблицы:
- clients(id, name, email UNIQUE, phone, address)
- products(id, name, price, description)
- orders(id, client_id, date, total_cost)
- order_items(id, order_id, product_id, quantity, unit_price)

ООП:
- Инкапсуляция: валидации и расчёты 
- Полиморфизм: вывод и функции
- Наследование: расширяемость Order, не меняя БД.
"""
from __future__ import annotations

import csv
import json
import sqlite3
from typing import Iterable, List, Sequence, Tuple

DB_NAME = "shop.db"


def init_db() -> None:
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            total_cost REAL NOT NULL,
            FOREIGN KEY(client_id) REFERENCES clients(id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
        """
    )
    conn.commit()
    conn.close()


# ---------------- CRUD ----------------
def add_client_row(name: str, email: str, phone: str, address: str) -> None:
    conn = sqlite3.connect(DB_NAME)
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO clients (name, email, phone, address) VALUES (?, ?, ?, ?)",
            (name, email, phone, address),
        )
        conn.commit()
    finally:
        conn.close()


def add_product_row(name: str, price: float, description: str) -> None:
    conn = sqlite3.connect(DB_NAME)
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO products (name, price, description) VALUES (?, ?, ?)",
            (name, float(price), description),
        )
        conn.commit()
    finally:
        conn.close()


def get_clients() -> List[Tuple[int, str, str]]:
    conn = sqlite3.connect(DB_NAME)
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name, email FROM clients ORDER BY name")
        return cur.fetchall()
    finally:
        conn.close()


def get_products() -> List[Tuple[int, str, float]]:
    conn = sqlite3.connect(DB_NAME)
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name, price FROM products ORDER BY name")
        rows = cur.fetchall()
        return [(pid, name, float(price)) for pid, name, price in rows]
    finally:
        conn.close()


def add_order_with_items(
    client_id: int, items: Sequence[Tuple[int, int]], date: str
) -> int:
    """Создаёт заказ и строки заказа.
    items: список кортежей (product_id, quantity).
    Возвращает order_id.
    """
    if not items:
        raise ValueError("Пустая корзина")
    conn = sqlite3.connect(DB_NAME)
    try:
        cur = conn.cursor()

        total = 0.0
        prices = {}
        for pid, qty in items:
            if int(qty) <= 0:
                raise ValueError("Количество товара должно быть > 0")
            cur.execute("SELECT price FROM products WHERE id = ?", (pid,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Товар id={pid} не найден")
            price = float(row[0])
            prices[pid] = price
            total += price * int(qty)

        cur.execute(
            "INSERT INTO orders (client_id, date, total_cost) VALUES (?, ?, ?)",
            (client_id, date, total),
        )
        order_id = cur.lastrowid

        for pid, qty in items:
            cur.execute(
                """
                INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                VALUES (?, ?, ?, ?)
                """,
                (order_id, pid, int(qty), prices[pid]),
            )

        conn.commit()
        return int(order_id)
    finally:
        conn.close()


# -------- История и аналитика --------
def get_client_purchase_history(client_id: int):
    conn = sqlite3.connect(DB_NAME)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT p.name,
                   COALESCE(SUM(oi.quantity), 0) as total_qty,
                   MAX(o.date) as last_date
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            JOIN products p ON p.id = oi.product_id
            WHERE o.client_id = ?
            GROUP BY p.name
            ORDER BY total_qty DESC, last_date DESC
            """,
            (client_id,),
        )
        return cur.fetchall()
    finally:
        conn.close()


def top5_clients_by_orders():
    conn = sqlite3.connect(DB_NAME)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT c.name, c.email, COUNT(o.id) as orders_count
            FROM clients c
            LEFT JOIN orders o ON o.client_id = c.id
            GROUP BY c.id
            ORDER BY orders_count DESC, c.name ASC
            LIMIT 5
            """
        )
        return cur.fetchall()
    finally:
        conn.close()


def top5_clients_by_items():
    conn = sqlite3.connect(DB_NAME)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT c.name, c.email, COALESCE(SUM(oi.quantity), 0) as items_count
            FROM clients c
            LEFT JOIN orders o ON o.client_id = c.id
            LEFT JOIN order_items oi ON oi.order_id = o.id
            GROUP BY c.id
            ORDER BY items_count DESC, c.name ASC
            LIMIT 5
            """
        )
        return cur.fetchall()
    finally:
        conn.close()


# -------- Экспорт / Импорт --------
def export_to_csv(filename: str, table: str) -> None:
    conn = sqlite3.connect(DB_NAME)
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM {table}")
        rows = cur.fetchall()
        headers = [d[0] for d in cur.description]
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
    finally:
        conn.close()


def import_from_csv(filename: str, table: str) -> None:
    conn = sqlite3.connect(DB_NAME)
    try:
        cur = conn.cursor()
        with open(filename, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
            placeholders = ",".join(["?"] * len(headers))
            cols = ",".join(headers)
            for row in reader:
                cur.execute(
                    f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", row
                )
        conn.commit()
    finally:
        conn.close()


def export_to_json(filename: str, table: str) -> None:
    conn = sqlite3.connect(DB_NAME)
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM {table}")
        rows = cur.fetchall()
        headers = [d[0] for d in cur.description]
        data = [dict(zip(headers, r)) for r in rows]
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    finally:
        conn.close()


def import_from_json(filename: str, table: str) -> None:
    conn = sqlite3.connect(DB_NAME)
    try:
        cur = conn.cursor()
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not data:
            return
        headers = list(data[0].keys())
        placeholders = ",".join(["?"] * len(headers))
        cols = ",".join(headers)
        for rec in data:
            values = [rec.get(h) for h in headers]
            cur.execute(
                f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", values
            )
        conn.commit()
    finally:
        conn.close()
