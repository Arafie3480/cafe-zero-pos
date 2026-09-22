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
