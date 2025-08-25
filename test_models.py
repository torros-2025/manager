"""Тест """
from __future__ import annotations

import unittest

from models import Client, Order, Product, SpecialOrder, print_order_cost


class TestModels(unittest.TestCase):
    def test_client_creation(self) -> None:
        client = Client("Иван Иванов", "ivan@example.com", "+71234567890", "Москва")
        self.assertEqual(client.name, "Иван Иванов")
        self.assertEqual(client.email, "ivan@example.com")
        self.assertEqual(client.phone, "+71234567890")
        self.assertEqual(client.address, "Москва")

    def test_print_order_cost(self) -> None:
        order = Order(
            1,
            Client("Пётр Петров", "petr@example.com", "+71234567891", "СПб"),
            [(Product("Товар1", 100.0), 1), (Product("Товар2", 50.0), 2)],
            "2023-10-01",
        )
        result = print_order_cost(order)
        self.assertIn("Total", result)

    def test_special_order_discount(self) -> None:
        special = SpecialOrder(
            2,
            Client("Сидор Сидоров", "sidor@example.com", "+71234567892", "Нск"),
            [(Product("A", 200.0), 1)],
            "2023-10-02",
            discount=10,
        )
        expected = sum(p.price * q for p, q in special.items) * 0.9
        self.assertAlmostEqual(special.total_cost, expected, places=6)


if __name__ == "__main__":
    unittest.main()
