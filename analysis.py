"""Отдельные аналит. функции (графики и табличные выгрузки)"""
from __future__ import annotations

import sqlite3
from typing import Tuple

import matplotlib.pyplot as plt
import pandas as pd

DB_NAME = "shop.db"


def orders_by_date_table() -> pd.DataFrame:
    """Таблица: число заказов по датам."""
    conn = sqlite3.connect(DB_NAME)
    try:
        df = pd.read_sql_query("SELECT date FROM orders", conn)
    finally:
        conn.close()
    if df.empty:
        return pd.DataFrame(columns=["date", "orders"])
    out = df.groupby("date").size().reset_index(name="orders")
    return out.sort_values("date")

def plot_orders_by_date() -> None:
    table = orders_by_date_table()
    if table.empty:
        print("Нет данных для отображения")
        return
    plt.figure(figsize=(8, 4))
    plt.plot(table["date"], table["orders"], marker="o")
    plt.title("Динамика количества заказов по датам")
    plt.xlabel("Дата")
    plt.ylabel("Количество заказов")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def top5_clients_tables() -> Tuple[pd.DataFrame, pd.DataFrame]:
    conn = sqlite3.connect(DB_NAME)
    try:
        top_orders = pd.read_sql_query(
            """
            SELECT c.name, c.email, COUNT(o.id) AS orders_count
            FROM clients c
            LEFT JOIN orders o ON o.client_id = c.id
            GROUP BY c.id
            ORDER BY orders_count DESC, c.name ASC
            LIMIT 5
            """
            , conn,
        )
        top_items = pd.read_sql_query(
            """
            SELECT c.name, c.email, COALESCE(SUM(oi.quantity), 0) AS items_count
            FROM clients c
            LEFT JOIN orders o ON o.client_id = c.id
            LEFT JOIN order_items oi ON oi.order_id = o.id
            GROUP BY c.id
            ORDER BY items_count DESC, c.name ASC
            LIMIT 5
            """
            , conn,
        )
    finally:
        conn.close()
    return top_orders, top_items


def plot_top5(df: pd.DataFrame, value_col: str, title: str) -> None:
    if df.empty:
        print("Нет данных для отображения")
        return
    plt.figure(figsize=(8, 4))
    plt.bar(df["name"], df[value_col])
    plt.title(title)
    plt.xlabel("Клиент")
    plt.ylabel("Значение")
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.show()
