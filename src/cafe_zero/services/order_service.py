from typing import List, Dict, Any, Optional
from cafe_zero.database.connection import get_db_connection
from cafe_zero.models.schemas import CartItem


class OrderService:
    @staticmethod
    def process_order(items: List[CartItem], payment_method: str, customer_id: Optional[int] = None) -> int:
        if not items:
            raise ValueError("سبد خرید نمی‌تواند خالی باشد.")

        # ۱. محاسبه مبلغ کل سفارش
        subtotal = sum(item.total_price for item in items)
        final_amount = subtotal

        with get_db_connection() as conn:
            cursor = conn.cursor()

            # ۲. ثبت سفارش اصلی در جدول orders
            cursor.execute("""
                INSERT INTO orders (customer_id, subtotal, final_amount, payment_method, status)
                VALUES (?, ?, ?, ?, 'in_progress')
            """, (customer_id, subtotal, final_amount, payment_method))

            order_id = cursor.lastrowid

            # ۳. ثبت اقلام فاکتور در جدول order_items
            for item in items:
                cursor.execute("""
                    INSERT INTO order_items (order_id, product_id, product_name, unit_price, quantity, total_price)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (order_id, item.product_id, item.name, item.price, item.quantity, item.total_price))

            # ۴. نسیه: فقط لاگ؛ تریگر دیتابیس current_debt را آپدیت می‌کند
            if customer_id and payment_method == 'credit':
                cursor.execute("""
                    INSERT INTO debt_transactions (customer_id, order_id, type, amount, description)
                    VALUES (?, ?, 'increase', ?, ?)
                """, (customer_id, order_id, final_amount, f"خرید نسیه فاکتور #{order_id}"))

            # ۵. محاسبه و افزودن امتیاز باشگاه مشتریان
            if customer_id:
                points_earned = int(final_amount // 10000)
                if points_earned > 0:
                    cursor.execute("""
                        UPDATE customers
                        SET loyalty_points = loyalty_points + ?
                        WHERE id = ?
                    """, (points_earned, customer_id))

            conn.commit()
            return order_id

    @staticmethod
    def get_active_orders() -> List[Dict[str, Any]]:
        """دریافت لیست سفارش‌های در حال آماده‌سازی برای صف فعال UI"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    o.id,
                    o.status,
                    o.subtotal,
                    o.final_amount,
                    o.payment_method,
                    o.created_at,
                    COALESCE(c.name, 'مشتری گذری') as customer_name
                FROM orders o
                LEFT JOIN customers c ON o.customer_id = c.id
                WHERE o.status = 'in_progress'
                ORDER BY o.created_at DESC, o.id DESC
            """)

            rows = cursor.fetchall()
            orders = []
            for row in rows:
                order_dict = dict(row)

                cursor.execute("""
                    SELECT product_name, quantity, unit_price, total_price
                    FROM order_items
                    WHERE order_id = ?
                """, (order_dict['id'],))

                items_list = [dict(item) for item in cursor.fetchall()]
                order_dict['items'] = items_list
                order_dict['items_count'] = sum(i.get('quantity', 1) for i in items_list)

                if items_list:
                    order_dict['items_summary'] = "، ".join(
                        f"{i.get('quantity', 1)}x {i.get('product_name', '')}" for i in items_list
                    )
                else:
                    order_dict['items_summary'] = "بدون آیتم"

                orders.append(order_dict)

            return orders

    @staticmethod
    def complete_order(order_id: int) -> None:
        """تغییر وضعیت سفارش از آماده‌سازی به تکمیل شده"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE orders
                SET status = 'completed'
                WHERE id = ?
            """, (order_id,))
            conn.commit()
