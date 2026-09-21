"""
اسکریپت مقداردهی اولیه و تمیز دیتابیس کافه صفر (Cafe Zero)
ایجاد ساختار استاندارد مطابق با connection.py به همراه داده‌های نمونه
"""
import sqlite3
from pathlib import Path

# تعیین مسیر دقیق و مستقل دیتابیس در پوشه data
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "cafe_sefr.db"

def reset_and_seed_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # فعال کردن کلیدهای خارجی
    cursor.execute("PRAGMA foreign_keys = ON;")

    # حذف جدول‌های قدیمی برای شروع کاملاً تمیز
    cursor.executescript("""
        DROP TABLE IF EXISTS debt_transactions;
        DROP TABLE IF EXISTS order_items;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS expenses;
        DROP TABLE IF EXISTS customers;
        DROP TABLE IF EXISTS products;
    """)

    # ساخت جدول‌ها کاملاً منطبق با connection.py
    cursor.executescript("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price INTEGER NOT NULL,
            cost_price INTEGER NOT NULL DEFAULT 0,
            stock INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            current_debt INTEGER DEFAULT 0,
            loyalty_points INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            subtotal INTEGER NOT NULL DEFAULT 0,
            discount INTEGER DEFAULT 0,
            final_amount INTEGER NOT NULL DEFAULT 0,
            payment_method TEXT NOT NULL DEFAULT 'cash',
            status TEXT DEFAULT 'completed',
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL
        );

        CREATE TABLE order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            unit_price INTEGER NOT NULL DEFAULT 0,
            total_price INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
        );

        CREATE TABLE expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            amount INTEGER NOT NULL,
            description TEXT,
            expense_date TEXT DEFAULT (date('now', 'localtime')),
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE debt_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            order_id INTEGER,
            type TEXT NOT NULL, -- 'increase' or 'decrease'
            amount INTEGER NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL
        );
    """)

    # درج داده‌های اولیه استاندارد و نمونه
    cursor.executescript("""
        INSERT INTO products (name, category, price, cost_price, stock) VALUES
        ('اسپرسو سینگل', 'قهوه', 35000, 15000, 50),
        ('اسپرسو دبل', 'قهوه', 45000, 20000, 50),
        ('آمریکانو', 'قهوه', 50000, 20000, 40),
        ('لاته', 'قهوه بر پایه شیر', 65000, 30000, 30),
        ('کاپوچینو', 'قهوه بر پایه شیر', 65000, 30000, 30),
        ('چای ماسالا', 'نوشیدنی گرم', 55000, 25000, 25),
        ('چیزکیک نیویورکی', 'کیک و دسر', 85000, 45000, 15);

        INSERT INTO customers (name, phone, current_debt, loyalty_points) VALUES
        ('مشتری حضوری / نقدی', '00000000000', 0, 0),
        ('علی رضایی', '09121111111', 0, 120),
        ('سارا محمدی', '09122222222', 0, 50);

        INSERT INTO expenses (title, category, amount, description) VALUES
        ('خرید دانه قهوه اسپشیالتی', 'مواد اولیه', 1200000, 'خرید هفتگی ۵ کیلو دانه قهوه'),
        ('خرید شیر پرچرب', 'مواد اولیه', 350000, '۱۰ بطری شیر برای لاته و کاپوچینو');
    """)

    conn.commit()
    conn.close()
    print("✨ دیتابیس کافه صفر با اسکیما و ستون‌های استاندارد با موفقیت بازسازی شد!")

if __name__ == "__main__":
    reset_and_seed_db()
