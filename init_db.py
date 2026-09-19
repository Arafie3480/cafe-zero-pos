import os
import sqlite3

def reset_and_seed_db():
    # مسیر دقیق دیتابیس پروژه
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    db_path = os.path.join(data_dir, "cafe_sefr.db")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # ۱. پاکسازی جداول قدیمی (برای ریست کامل دیتابیس تستی)
    cursor.executescript('''
        DROP TABLE IF EXISTS debt_transactions;
        DROP TABLE IF EXISTS order_items;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS expenses;
        DROP TABLE IF EXISTS customers;
        DROP TABLE IF EXISTS products;

        -- ساختار استاندارد جداول پروژه
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            price INTEGER NOT NULL
        );

        CREATE TABLE customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            debt INTEGER DEFAULT 0,
            loyalty_points INTEGER DEFAULT 0
        );

        CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            total_amount INTEGER NOT NULL,
            payment_method TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        );

        CREATE TABLE order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product_name TEXT,
            quantity INTEGER,
            price INTEGER,
            FOREIGN KEY(order_id) REFERENCES orders(id)
        );

        CREATE TABLE expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT,
            amount INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE debt_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            amount INTEGER NOT NULL,
            type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        );
    ''')

    # ۲. دیتای تستی/نمونه برای محصولات و منو
    products_seed = [
        ('اسپرسو سینگل', 'قهوه گرم', 45000),
        ('اسپرسو دوبل', 'قهوه گرم', 60000),
        ('امریکانو', 'قهوه گرم', 65000),
        ('لاته', 'قهوه گرم', 85000),
        ('کاپوچینو', 'قهوه گرم', 85000),
        ('آیس لاته', 'نوشیدنی سرد', 90000),
        ('شیک شکلات', 'بار سرد', 120000),
        ('چیز کیک', 'کیک و دسر', 110000),
    ]
    cursor.executemany("INSERT INTO products (name, category, price) VALUES (?, ?, ?)", products_seed)

    # ۳. مشتری نمونه و تست
    cursor.execute("INSERT INTO customers (name, phone, debt, loyalty_points) VALUES (?, ?, ?, ?)", 
                   ('مشتری نمونه', '09120000000', 0, 0))

    conn.commit()
    conn.close()
    print("✨ دیتابیس کافه صفر ریست شد و با اطلاعات اولیه استاندارد آماده به کار است!")

if __name__ == "__main__":
    reset_and_seed_db()
