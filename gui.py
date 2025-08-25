#!/usr/bin/env python3
"""Графический интерфейс (tkinter + ttk.Notebook).

Вкладки:
- Клиенты — регистрация (подписи полей).
- Товары — добавление товара.
- Заказ — множественный выбор товаров, количество, корзина (Товар, Кол-во).
- История/Аналитика — история покупок клиента (таблица) + TOP-5 таблицами и кнопка
  «Показать график» (графики через matplotlib в отдельных окнах).
- Экспорт/Импорт — CSV/JSON для таблиц: clients, products, orders, order_items.
"""
from __future__ import annotations

import tkinter as tk
from datetime import date
from tkinter import filedialog, messagebox, ttk
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt

from db import (
    add_client_row,
    add_order_with_items,
    add_product_row,
    export_to_csv,
    export_to_json,
    get_client_purchase_history,
    get_clients,
    get_products,
    import_from_csv,
    import_from_json,
    top5_clients_by_items,
    top5_clients_by_orders,
)
from models import Client, Product


# -------- Клиенты --------
def ui_clients(tab: tk.Misc) -> None:
    frame = ttk.Frame(tab, padding=10)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Имя:").grid(row=0, column=0, sticky="w", pady=4)
    name_entry = ttk.Entry(frame)
    name_entry.grid(row=0, column=1, sticky="ew", pady=4)

    ttk.Label(frame, text="Email:").grid(row=1, column=0, sticky="w", pady=4)
    email_entry = ttk.Entry(frame)
    email_entry.grid(row=1, column=1, sticky="ew", pady=4)

    ttk.Label(frame, text="Телефон:").grid(row=2, column=0, sticky="w", pady=4)
    phone_entry = ttk.Entry(frame)
    phone_entry.grid(row=2, column=1, sticky="ew", pady=4)

    ttk.Label(frame, text="Адрес:").grid(row=3, column=0, sticky="w", pady=4)
    address_entry = ttk.Entry(frame)
    address_entry.grid(row=3, column=1, sticky="ew", pady=4)

    def register() -> None:
        try:
            client = Client(
                name_entry.get(),
                email_entry.get(),
                phone_entry.get(),
                address_entry.get(),
            )
            add_client_row(client.name, client.email, client.phone, client.address)
            messagebox.showinfo("Успех", "Клиент зарегистрирован")
            name_entry.delete(0, tk.END)
            email_entry.delete(0, tk.END)
            phone_entry.delete(0, tk.END)
            address_entry.delete(0, tk.END)
            refresh_clients_products()
        except Exception as exc:
            messagebox.showerror("Ошибка", str(exc))

    ttk.Button(frame, text="Зарегистрировать клиента", command=register).grid(
        row=4, column=0, columnspan=2, pady=8
    )
    frame.columnconfigure(1, weight=1)


# -------- Товары --------
def ui_products(tab: tk.Misc) -> None:
    frame = ttk.Frame(tab, padding=10)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Название:").grid(row=0, column=0, sticky="w", pady=4)
    name_entry = ttk.Entry(frame)
    name_entry.grid(row=0, column=1, sticky="ew", pady=4)

    ttk.Label(frame, text="Цена:").grid(row=1, column=0, sticky="w", pady=4)
    price_entry = ttk.Entry(frame)
    price_entry.grid(row=1, column=1, sticky="ew", pady=4)

    ttk.Label(frame, text="Описание:").grid(row=2, column=0, sticky="w", pady=4)
    descr_entry = ttk.Entry(frame)
    descr_entry.grid(row=2, column=1, sticky="ew", pady=4)

    def add_product() -> None:
        try:
            product = Product(name_entry.get(), float(price_entry.get()), descr_entry.get())
            add_product_row(product.name, product.price, product.description)
            messagebox.showinfo("Успех", "Товар добавлен")
            name_entry.delete(0, tk.END)
            price_entry.delete(0, tk.END)
            descr_entry.delete(0, tk.END)
            refresh_clients_products()
        except ValueError:
            messagebox.showerror("Ошибка", "Цена должна быть числом")
        except Exception as exc:
            messagebox.showerror("Ошибка", str(exc))

    ttk.Button(frame, text="Добавить товар", command=add_product).grid(
        row=3, column=0, columnspan=2, pady=8
    )
    frame.columnconfigure(1, weight=1)


# -------- Заказ --------
def ui_order(tab: tk.Misc) -> None:
    global clients_map, products_data, cart_items, combo_client_order
    global list_products, qty_entry, cart_tree, date_entry

    cart_items = {}  # product_id -> (name, qty)

    frame = ttk.Frame(tab, padding=10)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Клиент:").grid(row=0, column=0, sticky="w", pady=4)
    combo_client_order = ttk.Combobox(frame, state="readonly")
    combo_client_order.grid(row=0, column=1, sticky="ew", pady=4)

    ttk.Label(frame, text="Список товаров (множественный выбор):").grid(
        row=1, column=0, sticky="w", pady=4
    )
    list_products = tk.Listbox(frame, selectmode=tk.MULTIPLE, height=10)
    list_products.grid(row=1, column=1, sticky="nsew", pady=4)

    ttk.Label(frame, text="Количество для выбранных:").grid(
        row=2, column=0, sticky="w", pady=4
    )
    qty_entry = ttk.Entry(frame)
    qty_entry.grid(row=2, column=1, sticky="ew", pady=4)

    ttk.Button(frame, text="Добавить в корзину", command=add_selected_to_cart).grid(
        row=3, column=0, columnspan=2, pady=6
    )

    cart_tree = ttk.Treeview(frame, columns=("name", "qty"), show="headings", height=10)
    cart_tree.heading("name", text="Товар")
    cart_tree.heading("qty", text="Кол-во")
    cart_tree.column("name", width=220, anchor="w")
    cart_tree.column("qty", width=80, anchor="center")
    cart_tree.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=6)

    buttons = ttk.Frame(frame)
    buttons.grid(row=5, column=0, columnspan=2, pady=4)
    ttk.Button(buttons, text="Удалить выделенное", command=remove_selected_from_cart).pack(
        side="left", padx=5
    )
    ttk.Button(buttons, text="Очистить корзину", command=clear_cart).pack(
        side="left", padx=5
    )

    ttk.Label(frame, text="Дата заказа (YYYY-MM-DD):").grid(
        row=6, column=0, sticky="w", pady=4
    )
    date_entry = ttk.Entry(frame)
    date_entry.insert(0, str(date.today()))
    date_entry.grid(row=6, column=1, sticky="ew", pady=4)

    ttk.Button(frame, text="Оформить заказ", command=place_order).grid(
        row=7, column=0, columnspan=2, pady=10
    )

    frame.columnconfigure(1, weight=1)
    frame.rowconfigure(1, weight=1)
    frame.rowconfigure(4, weight=1)


def add_selected_to_cart() -> None:
    selections = list_products.curselection()
    if not selections:
        messagebox.showerror("Ошибка", "Выберите товары слева")
        return
    try:
        qty = int(qty_entry.get().strip())
        if qty <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Ошибка", "Количество должно быть положительным целым числом")
        return

    for idx in selections:
        pid, name, _price = products_data[idx]
        if pid in cart_items:
            cart_items[pid] = (name, cart_items[pid][1] + qty)
        else:
            cart_items[pid] = (name, qty)
    refresh_cart_tree()


def remove_selected_from_cart() -> None:
    selected = cart_tree.selection()
    if not selected:
        return
    names_to_remove = {cart_tree.item(iid, "values")[0] for iid in selected}
    to_delete = [pid for pid, (name, _qty) in cart_items.items() if name in names_to_remove]
    for pid in to_delete:
        del cart_items[pid]
    refresh_cart_tree()


def clear_cart() -> None:
    cart_items.clear()
    refresh_cart_tree()


def refresh_cart_tree() -> None:
    for row in cart_tree.get_children():
        cart_tree.delete(row)
    for _pid, (name, qty) in cart_items.items():
        cart_tree.insert("", "end", values=(name, qty))


def place_order() -> None:
    if not cart_items:
        messagebox.showerror("Ошибка", "Корзина пуста")
        return
    label = combo_client_order.get()
    if not label:
        messagebox.showerror("Ошибка", "Выберите клиента")
        return
    client_id = clients_map.get(label)
    if not client_id:
        messagebox.showerror("Ошибка", "Некорректный клиент")
        return
    items = [(pid, qty) for pid, (_name, qty) in cart_items.items()]
    try:
        order_id = add_order_with_items(client_id, items, date_entry.get().strip() or str(date.today()))
        messagebox.showinfo("Успех", f"Заказ №{order_id} оформлен")
        clear_cart()
    except Exception as exc:
        messagebox.showerror("Ошибка", str(exc))


# -------- История / Аналитика --------
def ui_history(tab: tk.Misc) -> None:
    global combo_client_hist, hist_tree, top_tree
    frame = ttk.Frame(tab, padding=10)
    frame.pack(fill="both", expand=True)

    header = ttk.LabelFrame(frame, text="История покупок клиента")
    header.grid(row=0, column=0, sticky="ew", padx=2, pady=4, columnspan=3)
    ttk.Label(header, text="Клиент:").grid(row=0, column=0, sticky="w", padx=4, pady=4)
    combo_client_hist = ttk.Combobox(header, state="readonly")
    combo_client_hist.grid(row=0, column=1, sticky="ew", padx=4, pady=4)
    ttk.Button(header, text="Показать историю", command=show_history).grid(row=0, column=2, padx=6, pady=4)
    header.columnconfigure(1, weight=1)

    hist_tree = ttk.Treeview(frame, columns=("name", "qty", "last"), show="headings", height=10)
    hist_tree.heading("name", text="Товар")
    hist_tree.heading("qty", text="Всего куплено")
    hist_tree.heading("last", text="Последняя дата")
    hist_tree.column("name", width=240, anchor="w")
    hist_tree.column("qty", width=140, anchor="center")
    hist_tree.column("last", width=160, anchor="center")
    hist_tree.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=6)

    ttk.Label(frame, text="Аналитика — TOP-5 клиентов").grid(row=2, column=0, sticky="w")

    ttk.Button(frame, text="Топ-5 по заказам", command=show_top_by_orders).grid(row=2, column=1, sticky="e", padx=4)
    ttk.Button(frame, text="Показать график", command=plot_top_by_orders).grid(row=2, column=2, sticky="w", padx=4)

    ttk.Button(frame, text="Топ-5 по товарам", command=show_top_by_items).grid(row=3, column=1, sticky="e", padx=4)
    ttk.Button(frame, text="Показать график", command=plot_top_by_items).grid(row=3, column=2, sticky="w", padx=4)

    top_tree = ttk.Treeview(frame, columns=("name", "email", "metric"), show="headings", height=8)
    top_tree.heading("name", text="Клиент")
    top_tree.heading("email", text="Email")
    top_tree.heading("metric", text="Значение")
    top_tree.column("name", width=240, anchor="w")
    top_tree.column("email", width=240, anchor="w")
    top_tree.column("metric", width=120, anchor="center")
    top_tree.grid(row=4, column=0, columnspan=3, sticky="nsew", pady=6)

    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(1, weight=1)
    frame.rowconfigure(4, weight=1)


def show_history() -> None:
    for row in hist_tree.get_children():
        hist_tree.delete(row)
    label = combo_client_hist.get()
    if not label:
        return
    cid = clients_map.get(label)
    rows = get_client_purchase_history(cid)
    for name, total_qty, last_date in rows:
        hist_tree.insert("", "end", values=(name, total_qty, last_date or ""))


def _fill_top_table(rows, metric_title: str) -> None:
    for row in top_tree.get_children():
        top_tree.delete(row)
    top_tree.heading("metric", text=metric_title)
    for name, email, metric in rows:
        top_tree.insert("", "end", values=(name, email, metric))


def show_top_by_orders() -> None:
    rows = top5_clients_by_orders()
    _fill_top_table(rows, "Кол-во заказов")


def plot_top_by_orders() -> None:
    rows = top5_clients_by_orders()
    if not rows:
        messagebox.showinfo("Информация", "Нет данных для анализа")
        return
    names = [r[0] for r in rows]
    values = [int(r[2]) for r in rows]
    plt.figure(figsize=(8, 4))
    plt.bar(names, values)
    plt.title("Топ-5 клиентов по числу заказов")
    plt.xlabel("Клиент")
    plt.ylabel("Количество заказов")
    plt.xticks(rotation=25)
    plt.tight_layout()
    plt.show()


def show_top_by_items() -> None:
    rows = top5_clients_by_items()
    _fill_top_table(rows, "Кол-во товаров")


def plot_top_by_items() -> None:
    rows = top5_clients_by_items()
    if not rows:
        messagebox.showinfo("Информация", "Нет данных для анализа")
        return
    names = [r[0] for r in rows]
    values = [int(r[2]) for r in rows]
    plt.figure(figsize=(8, 4))
    plt.bar(names, values)
    plt.title("Топ-5 клиентов по числу купленных товаров")
    plt.xlabel("Клиент")
    plt.ylabel("Количество товаров")
    plt.xticks(rotation=25)
    plt.tight_layout()
    plt.show()


# -------- Экспорт/Импорт --------
def ui_io(tab: tk.Misc) -> None:
    frame = ttk.Frame(tab, padding=10)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Таблица:").grid(row=0, column=0, sticky="w")
    table_combo = ttk.Combobox(
        frame, state="readonly", values=["clients", "products", "orders", "order_items"]
    )
    table_combo.grid(row=0, column=1, sticky="ew")

    def do_export_csv() -> None:
        table = table_combo.get()
        if not table:
            messagebox.showerror("Ошибка", "Выберите таблицу")
            return
        fname = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV", "*.csv")]
        )
        if not fname:
            return
        export_to_csv(fname, table)
        messagebox.showinfo("Готово", f"Экспортировано в {fname}")

    def do_export_json() -> None:
        table = table_combo.get()
        if not table:
            messagebox.showerror("Ошибка", "Выберите таблицу")
            return
        fname = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("JSON", "*.json")]
        )
        if not fname:
            return
        export_to_json(fname, table)
        messagebox.showinfo("Готово", f"Экспортировано в {fname}")

    def do_import_csv() -> None:
        table = table_combo.get()
        if not table:
            messagebox.showerror("Ошибка", "Выберите таблицу")
            return
        fname = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not fname:
            return
        import_from_csv(fname, table)
        messagebox.showinfo("Готово", f"Импортировано из {fname}")
        refresh_clients_products()

    def do_import_json() -> None:
        table = table_combo.get()
        if not table:
            messagebox.showerror("Ошибка", "Выберите таблицу")
            return
        fname = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not fname:
            return
        import_from_json(fname, table)
        messagebox.showinfo("Готово", f"Импортировано из {fname}")
        refresh_clients_products()

    ttk.Button(frame, text="Экспорт CSV", command=do_export_csv).grid(row=1, column=0, pady=8)
    ttk.Button(frame, text="Экспорт JSON", command=do_export_json).grid(row=1, column=1, pady=8)
    ttk.Button(frame, text="Импорт CSV", command=do_import_csv).grid(row=2, column=0, pady=8)
    ttk.Button(frame, text="Импорт JSON", command=do_import_json).grid(row=2, column=1, pady=8)
    frame.columnconfigure(1, weight=1)


# -------- Общие --------
def refresh_clients_products() -> None:
    global products_data, clients_map

    clients = get_clients()
    client_labels = [f"{name} <{email}>" for (cid, name, email) in clients]
    client_ids = [cid for (cid, _n, _e) in clients]
    clients_map = dict(zip(client_labels, client_ids))

    products = get_products()
    products_data = [(pid, name, price) for (pid, name, price) in products]

    # Заказ
    combo_client_order["values"] = client_labels
    list_products.delete(0, tk.END)
    for _pid, name, price in products_data:
        list_products.insert(tk.END, f"{name} ({price:.2f})")

    # История
    combo_client_hist["values"] = client_labels


def main_window() -> None:
    root = tk.Tk()
    root.title("Менеджер интернет-магазина")
    root.geometry("1024x720")

    nb = ttk.Notebook(root)
    tab_clients = ttk.Frame(nb)
    tab_products = ttk.Frame(nb)
    tab_order = ttk.Frame(nb)
    tab_history = ttk.Frame(nb)
    tab_io = ttk.Frame(nb)

    nb.add(tab_clients, text="Клиенты")
    nb.add(tab_products, text="Товары")
    nb.add(tab_order, text="Заказ")
    nb.add(tab_history, text="История/Аналитика")
    nb.add(tab_io, text="Экспорт/Импорт")
    nb.pack(fill="both", expand=True)

    ui_clients(tab_clients)
    ui_products(tab_products)
    ui_order(tab_order)
    ui_history(tab_history)
    ui_io(tab_io)

    refresh_clients_products()
    root.mainloop()
