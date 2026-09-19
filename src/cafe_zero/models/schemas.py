from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class CartItem:
    product_id: int
    name: str
    price: int
    quantity: int

    @property
    def total_price(self) -> int:
        return self.price * self.quantity

@dataclass
class FinancialSummary:
    target_date: str
    total_sales: int
    total_expenses: int
    net_profit: int
    orders_count: int
    pos_sales: int
    cash_sales: int
    credit_sales: int
