# migrate_expenses.py
import sqlite3
from pathlib import Path

db_path = Path("data") / "cafe_sefr.db"

con = sqlite3.connect(db_path)
cur = con.cursor()

# ستون‌های فعلی جدول expenses
cur.execute("PRAGMA table_info(expenses)")
existing_cols = {row[1] for row in cur.fetchall()}
print("BEFORE:", existing_cols)

# اضافه کردن ستون‌ها اگر وجود ندارند
if "title" not in existing_cols:
    cur.execute("ALTER TABLE expenses ADD COLUMN title TEXT NOT NULL DEFAULT 'Expense'")

if "expense_date" not in existing_cols:
    cur.execute("ALTER TABLE expenses ADD COLUMN expense_date TEXT")

if "created_at" not in existing_cols:
    cur.execute("ALTER TABLE expenses ADD COLUMN created_at TEXT")

# انتقال داده از ستون قدیمی date به ستون‌های جدید
# (اگر date وجود داشته باشد)
if "date" in existing_cols:
    cur.execute("""
        UPDATE expenses
        SET
          expense_date = COALESCE(expense_date, date),
          created_at   = COALESCE(created_at,   date)
    """)

con.commit()

cur.execute("PRAGMA table_info(expenses)")
print("AFTER:", [row[1] for row in cur.fetchall()])

con.close()
print("Done.")
