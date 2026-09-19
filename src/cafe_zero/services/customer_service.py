from __future__ import annotations
from typing import List, Dict, Any, Optional
from ..database.connection import get_db_connection

class CustomerService:
    """
    سرویس مدیریت مشتریان منطبق بر قرارداد UI:
      - get_all()
      - create(name, phone)
      - settle_debt(customer_id, amount)
    """

    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM customers ORDER BY name ASC")
            return [dict(r) for r in cur.fetchall()]

    @staticmethod
    def create(name: str, phone: str) -> int:
        name = (name or "").strip()
        phone = (phone or "").strip()
        if not name or not phone:
            raise ValueError("نام و شماره تماس نمی‌توانند خالی باشند")

        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO customers (name, phone) VALUES (?, ?)",
                (name, phone),
            )
            return int(cur.lastrowid)

    @staticmethod
    def settle_debt(customer_id: int, amount: int) -> bool:
        try:
            amount = int(amount)
        except Exception:
            return False

        if amount <= 0:
            return False

        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT current_debt FROM customers WHERE id = ?", (customer_id,))
            row = cur.fetchone()
            if not row:
                return False

            current_debt = row["current_debt"] or 0
            if current_debt < amount:
                return False

            # فقط درج تراکنش؛ تریگر دیتابیس خودش ستون current_debt را کم می‌کند
            cur.execute(
                """
                INSERT INTO debt_transactions (customer_id, type, amount, description)
                VALUES (?, 'decrease', ?, 'تسویه بدهی')
                """,
                (customer_id, amount),
            )
            return True

    @staticmethod
    def get_by_id(customer_id: int) -> Optional[Dict[str, Any]]:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
            r = cur.fetchone()
            return dict(r) if r else None
