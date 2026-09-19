import sys
from pathlib import Path

# اضافه کردن پوشه src به عنوان ریشه جستجوی ماژول‌ها به شکل تمیز
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from cafe_zero.database.connection import init_database
from cafe_zero.ui.app import CafeZeroApp

def main():
    init_database()
    app = CafeZeroApp()
    app.mainloop()

if __name__ == "__main__":
    main()
