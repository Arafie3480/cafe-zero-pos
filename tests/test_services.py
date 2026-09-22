"""
تست‌های خودکار برای بررسی صحت عملکرد دیتابیس و سرویس‌ها
"""
import pytest
import sqlite3
from unittest.mock import patch
from cafe_zero.database import connection


@pytest.fixture
def mock_db(tmp_path):
    """ایجاد دیتابیس تستی موقت برای هر تست به صورت ایزوله"""
    test_db_path = tmp_path / "test_cafe.db"
    
    # موقتاً مسیر DB_PATH رو به دیتابیس تستی تغییر میدیم
    with patch.object(connection, "DB_PATH", str(test_db_path)):
        connection.init_database()
        yield


def test_init_database_products(mock_db):
    """تست این‌که آیا محصولات اولیه به درستی وارد دیتابیس می‌شوند"""
    with connection.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products;")
        count = cursor.fetchone()[0]
        # باید حداقل ۱۴ آیتم اولیه ثبت شده باشد
        assert count >= 14


def test_customer_debt_trigger(mock_db):
    """تست عملکرد تریگر خودکار افزایش و کاهش بدهی مشتریان"""
    with connection.get_db_connection() as conn:
        cursor = conn.cursor()
        
        # ۱. ایجاد مشتری تست
        cursor.execute(
            "INSERT INTO customers (name, phone) VALUES (?, ?);",
            ("مشتری تستی", "09120000000")
        )
        customer_id = cursor.lastrowid

        # ۲. افزایش بدهی با ثبت تراکنش
        cursor.execute(
            "INSERT INTO debt_transactions (customer_id, type, amount, description) VALUES (?, ?, ?, ?);",
            (customer_id, "increase", 50000, "خرید نسیه")
        )

        # بررسی اعمال تریگر افزایش
        cursor.execute("SELECT current_debt FROM customers WHERE id = ?;", (customer_id,))
        debt = cursor.fetchone()[0]
        assert debt == 50000

        # ۳. کاهش بدهی (تسویه)
        cursor.execute(
            "INSERT INTO debt_transactions (customer_id, type, amount, description) VALUES (?, ?, ?, ?);",
            (customer_id, "decrease", 20000, "پرداخت نقدی")
        )

        # بررسی اعمال تریگر کاهش
        cursor.execute("SELECT current_debt FROM customers WHERE id = ?;", (customer_id,))
        new_debt = cursor.fetchone()[0]
        assert new_debt == 30000
