#!/bin/bash

# Cafe Zero Setup Script
echo "Starting project cleanup and git initialization..."

# 1. Create .gitignore
cat << 'EOF' > .gitignore
__pycache__/
*.pyc
.venv/
data/cafe_sefr.db
.pytest_cache/
*.egg-info/
EOF
echo "[+] .gitignore created."

# 2. Create tests folder and test file
mkdir -p tests
cat << 'EOF' > tests/test_services.py
import pytest
from cafe_zero.database.connection import DatabaseManager
from cafe_zero.services.customer_service import CustomerService

@pytest.fixture
def db_session(tmp_path):
    db_file = tmp_path / "test_cafe.db"
    manager = DatabaseManager(db_path=str(db_file))
    manager.init_db()
    return manager

def test_customer_creation(db_session):
    service = CustomerService(db_session)
    customer = service.create(name="علی رضایی", phone="09121111111")
    assert customer is not None
    assert customer.name == "علی رضایی"
    assert customer.debt == 0
EOF
echo "[+] tests/test_services.py created."

# 3. Create README.md
cat << 'EOF' > README.md
# ☕ Cafe Zero | سیستم هوشمند مدیریت سفارشات و مالی کافه

سیستم مدیریت دسکتاپ برای کافه‌ها.

## 🚀 راهنمای نصب
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install pytest
pytest tests/
python main.py
