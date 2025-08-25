
"""

ООП в коде:
- Инкапсуляция — проверки корректности инкапсулированы внутри классов.  
- Наследование — пример с классом SpecialOrder, который может расширять Order.  
- Полиморфизм — одинаковый интерфейс __str__ у разных классов.
"""
from __future__ import annotations

import re
from typing import Iterable, List, Tuple


class Client:
    """Клиент интернет-магазина."""

    def __init__(self, name: str, email: str, phone: str, address: str) -> None:
        self.name = name.strip()
        if self._validate_email(email):
            self.email = email.strip()
        else:
            raise ValueError("Неверный формат email")

        if self._validate_phone(phone):
            self.phone = phone.strip()
        else:
            raise ValueError("Неверный формат телефона")

        self.address = address.strip()

    @staticmethod
    def _validate_email(email: str) -> bool:
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return re.match(pattern, email) is not None

    @staticmethod
    def _validate_phone(phone: str) -> bool:
        pattern = r'^\+?\d{10,15}$'
        return re.match(pattern, phone) is not None

    def __str__(self) -> str:
        return f"Client({self.name}, {self.email}, {self.phone}, {self.address})"


class Product:
    """Товар каталога."""

    def __init__(self, name: str, price: float, description: str = "") -> None:
        self.name = name.strip()
        try:
            self.price = float(price)
        except (TypeError, ValueError) as exc:
            raise ValueError("Цена должна быть числом") from exc
        self.description = description.strip()

    def __str__(self) -> str:
        return f"Product({self.name}, {self.price:.2f})"


OrderItem = Tuple[Product, int]


class Order:
    """Заказ: хранит список (Product, quantity)."""

    def __init__(
        self,
        order_id: int,
        client: Client,
        items: Iterable[OrderItem],
        date: str,
    ) -> None:
        self.order_id = int(order_id)
        self.client = client
        self.items: List[OrderItem] = []
        for product, qty in items:
            qty = int(qty)
            if qty <= 0:
                raise ValueError("Количество товара должно быть > 0")
            self.items.append((product, qty))
        self.date = date
        self.total_cost = sum(p.price * q for p, q in self.items)

    def __str__(self) -> str:
        return (
            f"Order({self.order_id}, Client: {self.client.name}, "
            f"Date: {self.date}, Total: {self.total_cost:.2f})"
        )


class SpecialOrder(Order):
    """Пример наследование.
    
    """

    def __init__(
        self,
        order_id: int,
        client: Client,
        items: Iterable[OrderItem],
        date: str,
        discount: float,
    ) -> None:
        super().__init__(order_id, client, items, date)
        self.discount = float(discount)
        if not 0 <= self.discount <= 100:
            raise ValueError("0..100")
        self.total_cost = self._apply_discount()

    def _apply_discount(self) -> float:
        total = sum(p.price * q for p, q in self.items)
        return total * (1 - self.discount / 100.0)


def print_order_cost(order: Order) -> str:
    return f"Total cost for order {order.order_id}: {order.total_cost:.2f}"
