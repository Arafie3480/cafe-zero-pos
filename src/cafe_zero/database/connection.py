import sqlite3
from contextlib import contextmanager
from ..config import DB_PATH

@contextmanager
def get_db_connection():
    """مدیریت اتصال به پایگاه داده با فعال‌سازی کلید خارجی و مدیریت خودکار تراکنش‌ها"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_database():
    """ساخت ساختار دیتابیس، تریگرها و همگام‌سازی خودکار در زمان بالا آمدن برنامه"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # ۱. ساخت جداول
        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price INTEGER NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            current_debt INTEGER DEFAULT 0,
            loyalty_points INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            total_amount INTEGER NOT NULL,
            discount INTEGER DEFAULT 0,
            final_amount INTEGER NOT NULL,
            payment_method TEXT NOT NULL,
            status TEXT DEFAULT 'in_progress',
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price INTEGER NOT NULL,
            total_price INTEGER NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            amount INTEGER NOT NULL,
            description TEXT,
            date TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS debt_transactions (
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

        -- ۲. تریگرها: دیتابیس خودکار به محض ثبت تراکنش، بدهی مشتری را آپدیت می‌کند
        CREATE TRIGGER IF NOT EXISTS trg_auto_increase_debt
        AFTER INSERT ON debt_transactions
        WHEN NEW.type = 'increase'
        BEGIN
            UPDATE customers 
            SET current_debt = COALESCE(current_debt, 0) + NEW.amount 
            WHERE id = NEW.customer_id;
        END;

        CREATE TRIGGER IF NOT EXISTS trg_auto_decrease_debt
        AFTER INSERT ON debt_transactions
        WHEN NEW.type = 'decrease'
        BEGIN
            UPDATE customers 
            SET current_debt = MAX(0, COALESCE(current_debt, 0) - NEW.amount) 
            WHERE id = NEW.customer_id;
        END;
        """)
        
        # ۳. منوی اولیه در صورت خالی بودن
        cursor.execute("SELECT COUNT(*) FROM products")
        if cursor.fetchone()[0] == 0:
            default_products = [
                ('اسپرسو سینگل', 'hot_coffee', 45000),
                ('اسپرسو دبل', 'hot_coffee', 55000),
                ('آمریکانو', 'hot_coffee', 60000),
                ('لاته', 'hot_coffee', 75000),
                ('کاپوچینو', 'hot_coffee', 75000),
                ('موکا', 'hot_coffee', 85000),
                ('آیس آمریکانو', 'cold_coffee', 65000),
                ('آیس لاته', 'cold_coffee', 80000),
                ('کوکاکولا', 'cold_drinks', 30000),
                ('آب معدنی', 'cold_drinks', 15000),
                ('چای سیاه', 'tea', 35000),
                ('ماسالا', 'tea', 70000),
                ('چیزکیک نیویورکی', 'cake', 95000),
                ('کوکی شکلاتی', 'cake', 45000),
            ]
            cursor.executemany(
                "INSERT INTO products (name, category, price) VALUES (?, ?, ?)",
                default_products
            )

        # ۴. سینک خودکار در استارت‌آپ (Self-Healing)
        cursor.execute("""
        UPDATE customers
        SET current_debt = COALESCE((
            SELECT
              COALESCE(SUM(CASE WHEN type='increase' THEN amount ELSE 0 END), 0) -
              COALESCE(SUM(CASE WHEN type IN ('decrease', 'payment') THEN amount ELSE 0 END), 0)
            FROM debt_transactions dt
            WHERE dt.customer_id = customers.id
        ), 0);
        """)
