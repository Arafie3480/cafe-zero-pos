from datetime import date
from typing import Optional
from cafe_zero.database.connection import get_db_connection
from cafe_zero.models.schemas import FinancialSummary

class AccountingService:
    @staticmethod
    def get_daily_financials(target_date: Optional[str] = None) -> FinancialSummary:
        if not target_date:
            target_date = date.today().isoformat()

        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT 
                    COALESCE(SUM(final_amount), 0) as total_sales,
                    COUNT(id) as total_orders
                FROM orders
                WHERE DATE(created_at) = ?
            """, (target_date,))
            sales_row = cursor.fetchone()

            cursor.execute("""
                SELECT payment_method, COALESCE(SUM(final_amount), 0) as amount
                FROM orders
                WHERE DATE(created_at) = ?
                GROUP BY payment_method
            """, (target_date,))
            method_map = {row["payment_method"]: row["amount"] for row in cursor.fetchall()}

            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) as total_expenses
                FROM expenses
                WHERE expense_date = ?
            """, (target_date,))
            expense_row = cursor.fetchone()

        total_sales = sales_row["total_sales"]
        total_expenses = expense_row["total_expenses"]

        return FinancialSummary(
            target_date=target_date,
            total_sales=total_sales,
            total_expenses=total_expenses,
            net_profit=total_sales - total_expenses,
            orders_count=sales_row["total_orders"],
            pos_sales=method_map.get("pos", 0),
            cash_sales=method_map.get("cash", 0),
            credit_sales=method_map.get("credit", 0)
        )

    @staticmethod
    def record_expense(title: str, category: str, amount: int, description: str = "") -> None:
        if not title.strip() or amount <= 0:
            raise ValueError("عنوان و مبلغ هزینه باید معتبر باشند.")

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO expenses (title, category, amount, description)
                VALUES (?, ?, ?, ?)
            """, (title.strip(), category, amount, description.strip()))
