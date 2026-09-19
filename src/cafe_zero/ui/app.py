import tkinter as tk
from tkinter import ttk, messagebox
from cafe_zero.database.connection import get_db_connection
from cafe_zero.models.schemas import CartItem
from cafe_zero.services.order_service import OrderService
from cafe_zero.services.accounting_service import AccountingService
from cafe_zero.services.customer_service import CustomerService

def format_toman(val: int) -> str:
    return f"{val:,} تومان"

class QuickAddCustomerDialog(tk.Toplevel):
    def __init__(self, parent, on_success_callback):
        super().__init__(parent)
        self.title("افزودن سریع مشتری")
        self.geometry("340x190")
        self.resizable(False, False)
        self.on_success = on_success_callback
        self.transient(parent)
        self.grab_set()

        frm = tk.Frame(self, padx=15, pady=15)
        frm.pack(fill="both", expand=True)

        tk.Label(frm, text="نام و نام خانوادگی:").grid(row=0, column=1, sticky="e", pady=5)
        self.ent_name = tk.Entry(frm, justify="right")
        self.ent_name.grid(row=0, column=0, pady=5, padx=5)

        tk.Label(frm, text="شماره تلفن:").grid(row=1, column=1, sticky="e", pady=5)
        self.ent_phone = tk.Entry(frm, justify="right")
        self.ent_phone.grid(row=1, column=0, pady=5, padx=5)

        btn_save = tk.Button(frm, text="ذخیره و انتخاب در سفارش", bg="#2ECC71", fg="white", font=("Helvetica", 9, "bold"), command=self.save)
        btn_save.grid(row=2, column=0, columnspan=2, pady=12, sticky="ew")

        self.ent_name.focus_set()

    def save(self):
        name = self.ent_name.get().strip()
        phone = self.ent_phone.get().strip()
        if not name or not phone:
            messagebox.showwarning("خطا", "نام و شماره تلفن الزامی هستند.", parent=self)
            return

        try:
            cid = CustomerService.create(name, phone)
            self.on_success(cid)
            self.destroy()
        except Exception as e:
            messagebox.showerror("خطا در ثبت", f"خطا در ثبت مشتری:\n{e}", parent=self)


class CafeZeroApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("سامانه مدیریت و حسابداری کافه صفر")
        self.geometry("1260x740")
        self.minsize(1080, 650)

        self.cart: dict[int, CartItem] = {}
        self.cached_customers = []

        self._build_header()
        self._build_tabs()
        
        # لود اولیه داده‌ها
        self.load_menu()
        self.refresh_customer_combobox()
        self.load_customers_table()
        self.load_expenses()
        self.refresh_stats()
        self.refresh_active_orders()

    def _build_header(self):
        hdr = tk.Frame(self, bg="#2C3E50", height=60)
        hdr.pack(fill="x", side="top")

        lbl_title = tk.Label(hdr, text="☕️ کافه صـفـر", font=("Helvetica", 16, "bold"), fg="#ECF0F1", bg="#2C3E50")
        lbl_title.pack(side="right", padx=20, pady=12)

        stats_box = tk.Frame(hdr, bg="#2C3E50")
        stats_box.pack(side="left", padx=20)

        self.lbl_profit = tk.Label(stats_box, text="سود خالص: ۰", font=("Helvetica", 11, "bold"), fg="#2ECC71", bg="#2C3E50")
        self.lbl_profit.pack(side="left", padx=12)

        self.lbl_expense = tk.Label(stats_box, text="هزینه: ۰", font=("Helvetica", 11, "bold"), fg="#E74C3C", bg="#2C3E50")
        self.lbl_expense.pack(side="left", padx=12)

        self.lbl_sales = tk.Label(stats_box, text="فروش: ۰", font=("Helvetica", 11, "bold"), fg="#F39C12", bg="#2C3E50")
        self.lbl_sales.pack(side="left", padx=12)

    def _build_tabs(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        t_order = ttk.Frame(notebook)
        notebook.add(t_order, text=" ثبت و مدیریت سفارش‌ها (میز کار) ")
        self._build_order_tab(t_order)

        t_cust = ttk.Frame(notebook)
        notebook.add(t_cust, text=" مدیریت مشتریان و نسیه ")
        self._build_customer_tab(t_cust)

        t_exp = ttk.Frame(notebook)
        notebook.add(t_exp, text=" ثبت هزینه‌ها ")
        self._build_expense_tab(t_exp)

    def _build_order_tab(self, parent):
        # منوی محصولات
        left = tk.LabelFrame(parent, text="منوی محصولات", padx=8, pady=8)
        left.pack(side="left", fill="both", expand=True, padx=4, pady=4)

        self.tree_menu = ttk.Treeview(left, columns=("id", "name", "cat", "price"), show="headings", height=14)
        self.tree_menu.heading("id", text="کد")
        self.tree_menu.heading("name", text="عنوان")
        self.tree_menu.heading("cat", text="دسته")
        self.tree_menu.heading("price", text="قیمت")
        self.tree_menu.column("id", width=35, anchor="center")
        self.tree_menu.column("price", width=85, anchor="center")
        self.tree_menu.pack(fill="both", expand=True)

        tk.Button(left, text="➕ افزودن به فاکتور جاری", bg="#3498DB", fg="white", font=("Helvetica", 10, "bold"), command=self.add_item).pack(fill="x", pady=6)

        # فاکتور جاری
        middle = tk.LabelFrame(parent, text="فاکتور جاری", padx=8, pady=8, width=320)
        middle.pack(side="left", fill="both", padx=4, pady=4)

        self.tree_cart = ttk.Treeview(middle, columns=("name", "qty", "total"), show="headings", height=8)
        self.tree_cart.heading("name", text="آیتم")
        self.tree_cart.heading("qty", text="تعداد")
        self.tree_cart.heading("total", text="جمع")
        self.tree_cart.column("qty", width=40, anchor="center")
        self.tree_cart.column("total", width=90, anchor="center")
        self.tree_cart.pack(fill="both", expand=True)

        tk.Button(middle, text="🗑 حذف / کاهش یک عدد", fg="red", command=self.remove_item).pack(pady=3)

        # مشتری و افزودن سریع
        f_cust_select = tk.Frame(middle)
        f_cust_select.pack(fill="x", pady=4)
        tk.Label(f_cust_select, text="مشتری:").pack(side="right")
        tk.Button(f_cust_select, text="➕ جدید", font=("Helvetica", 8, "bold"), bg="#E8F8F5", command=self.open_quick_add_customer).pack(side="left")
        
        self.cmb_customers = ttk.Combobox(middle, state="readonly")
        self.cmb_customers.pack(fill="x", pady=2)

        # روش پرداخت
        self.pay_mode = tk.StringVar(value="pos")
        f_pay = tk.Frame(middle)
        f_pay.pack(fill="x", pady=4)
        tk.Radiobutton(f_pay, text="کارت‌خوان", value="pos", variable=self.pay_mode).pack(side="right")
        tk.Radiobutton(f_pay, text="نقدی", value="cash", variable=self.pay_mode).pack(side="right", padx=4)
        tk.Radiobutton(f_pay, text="نسیه", value="credit", variable=self.pay_mode).pack(side="right")

        self.lbl_cart_total = tk.Label(middle, text="مبلغ کل: ۰ تومان", font=("Helvetica", 11, "bold"), fg="#2C3E50")
        self.lbl_cart_total.pack(pady=6)

        tk.Button(middle, text="🚀 ثبت نهایی سفارش", bg="#2ECC71", fg="white", font=("Helvetica", 11, "bold"), command=self.checkout).pack(fill="x", pady=4)

        # صف زنده
        right = tk.LabelFrame(parent, text="سفارش‌های در حال آماده‌سازی (صف زنده)", padx=8, pady=8)
        right.pack(side="right", fill="both", expand=True, padx=4, pady=4)

        self.tree_active = ttk.Treeview(right, columns=("id", "time", "cust", "items"), show="headings", height=14)
        self.tree_active.heading("id", text="شماره")
        self.tree_active.heading("time", text="ساعت")
        self.tree_active.heading("cust", text="مشتری")
        self.tree_active.heading("items", text="اقلام سفارش")
        self.tree_active.column("id", width=50, anchor="center")
        self.tree_active.column("time", width=65, anchor="center")
        self.tree_active.column("cust", width=85, anchor="center")
        self.tree_active.pack(fill="both", expand=True)

        f_act_btns = tk.Frame(right)
        f_act_btns.pack(fill="x", pady=6)

        tk.Button(f_act_btns, text="✅ تحویل داده شد (حذف از صف)", bg="#27AE60", fg="white", font=("Helvetica", 10, "bold"), command=self.deliver_order).pack(side="right", fill="x", expand=True, padx=2)
        tk.Button(f_act_btns, text="🔄 بروزرسانی", bg="#BDC3C7", command=self.refresh_active_orders).pack(side="left", padx=2)

    def open_quick_add_customer(self):
        def on_added(new_id):
            self.refresh_customer_combobox()
            self.load_customers_table()
            # ست کردن مشتری جدید داخل کمبوباکس
            for idx, c in enumerate(self.cached_customers):
                if c["id"] == new_id:
                    self.cmb_customers.current(idx + 1)
                    break
        QuickAddCustomerDialog(self, on_added)

    def refresh_active_orders(self):
        try:
            self.tree_active.delete(*self.tree_active.get_children())
            orders = OrderService.get_active_orders()
            for o in orders:
                created = str(o["created_at"])
                time_part = created.split(" ")[1][:5] if " " in created else created
                self.tree_active.insert("", "end", values=(f"#{o['id']}", time_part, o["customer_name"], o["items_summary"]))
        except Exception as e:
            print(f"Active orders refresh error: {e}")

    def deliver_order(self):
        sel = self.tree_active.selection()
        if not sel:
            messagebox.showinfo("راهنما", "لطفاً سفارش تحویل داده شده را از لیست انتخاب کنید.")
            return
        vals = self.tree_active.item(sel[0])["values"]
        order_id = int(str(vals[0]).replace("#", ""))
        
        OrderService.complete_order(order_id)
        self.refresh_active_orders()

    def load_menu(self):
        self.tree_menu.delete(*self.tree_menu.get_children())
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, category, price FROM products WHERE is_active = 1")
            for row in cursor.fetchall():
                self.tree_menu.insert("", "end", values=(row["id"], row["name"], row["category"], format_toman(row["price"])))

    def refresh_customer_combobox(self):
        self.cached_customers = CustomerService.get_all()
        opts = ["-- مشتری گذری --"] + [f"{c['name']} ({c['phone']})" for c in self.cached_customers]
        self.cmb_customers["values"] = opts
        if not self.cmb_customers.get() or self.cmb_customers.current() == -1:
            self.cmb_customers.current(0)

    def add_item(self):
        sel = self.tree_menu.selection()
        if not sel:
            return
        vals = self.tree_menu.item(sel[0])["values"]
        p_id = int(vals[0])
        name = str(vals[1])
        price = int(str(vals[3]).replace(" تومان", "").replace(",", ""))

        if p_id in self.cart:
            cur = self.cart[p_id]
            self.cart[p_id] = CartItem(p_id, name, price, cur.quantity + 1)
        else:
            self.cart[p_id] = CartItem(p_id, name, price, 1)
        self.redraw_cart()

    def remove_item(self):
        sel = self.tree_cart.selection()
        if not sel:
            return
        idx = self.tree_cart.index(sel[0])
        p_id = list(self.cart.keys())[idx]
        if self.cart[p_id].quantity > 1:
            item = self.cart[p_id]
            self.cart[p_id] = CartItem(item.product_id, item.name, item.price, item.quantity - 1)
        else:
            del self.cart[p_id]
        self.redraw_cart()

    def redraw_cart(self):
        self.tree_cart.delete(*self.tree_cart.get_children())
        total = 0
        for item in self.cart.values():
            total += item.total_price
            self.tree_cart.insert("", "end", values=(item.name, item.quantity, format_toman(item.total_price)))
        self.lbl_cart_total.config(text=f"مبلغ کل: {format_toman(total)}")

    def checkout(self):
        if not self.cart:
            messagebox.showwarning("خطا", "سبد خرید خالی است.")
            return

        idx = self.cmb_customers.current()
        customer_id = None
        if idx > 0 and (idx - 1) < len(self.cached_customers):
            customer_id = self.cached_customers[idx - 1]["id"]

        method = self.pay_mode.get()

        if method == "credit" and customer_id is None:
            messagebox.showwarning("خطا در ثبت نسیه", "برای خرید نسیه، حتماً باید یک مشتری مشخص انتخاب شود (نمی‌توان برای مشتری گذری نسیه زد).")
            return

        try:
            OrderService.process_order(
                items=list(self.cart.values()),
                payment_method=method,
                customer_id=customer_id
            )
            self.cart.clear()
            self.redraw_cart()
            self.refresh_stats()
            self.refresh_active_orders()
            self.load_customers_table()
            messagebox.showinfo("موفقیت", "سفارش با موفقیت ثبت و به صف سفارش‌ها افزوده شد. ✅")
        except Exception as ex:
            messagebox.showerror("خطای ثبت سفارش", f"خطایی رخ داد:\n{ex}")

    def _build_customer_tab(self, parent):
        top = tk.LabelFrame(parent, text="افزودن مشتری جدید", padx=10, pady=10)
        top.pack(fill="x", padx=10, pady=5)

        tk.Label(top, text="نام:").grid(row=0, column=3, padx=5)
        self.ent_cname = tk.Entry(top, justify="right")
        self.ent_cname.grid(row=0, column=2, padx=5)

        tk.Label(top, text="تلفن:").grid(row=0, column=1, padx=5)
        self.ent_cphone = tk.Entry(top)
        self.ent_cphone.grid(row=0, column=0, padx=5)

        tk.Button(top, text="ثبت مشتری", bg="#2ECC71", fg="white", command=self.save_cust).grid(row=0, column=4, padx=10)

        self.tree_cust = ttk.Treeview(parent, columns=("id", "name", "phone", "debt", "points"), show="headings")
        self.tree_cust.heading("id", text="کد")
        self.tree_cust.heading("name", text="نام")
        self.tree_cust.heading("phone", text="تلفن")
        self.tree_cust.heading("debt", text="بدهی (نسیه)")
        self.tree_cust.heading("points", text="امتیاز باشگاه")
        self.tree_cust.pack(fill="both", expand=True, padx=10, pady=5)

        f_settle = tk.Frame(parent)
        f_settle.pack(fill="x", padx=10, pady=5)
        tk.Label(f_settle, text="مبلغ تسویه بدهی (تومان):").pack(side="right", padx=5)
        self.ent_settle = tk.Entry(f_settle)
        self.ent_settle.pack(side="right", padx=5)
        tk.Button(f_settle, text="تسویه حساب", bg="#F39C12", fg="white", command=self.settle_cust).pack(side="right", padx=10)

    def save_cust(self):
        try:
            CustomerService.create(self.ent_cname.get(), self.ent_cphone.get())
            self.ent_cname.delete(0, tk.END)
            self.ent_cphone.delete(0, tk.END)
            self.load_customers_table()
            self.refresh_customer_combobox()
            messagebox.showinfo("موفقیت", "مشتری افزوده شد.")
        except Exception as e:
            messagebox.showerror("خطا", str(e))

    def load_customers_table(self):
        if not hasattr(self, 'tree_cust'):
            return
        self.tree_cust.delete(*self.tree_cust.get_children())
        for c in CustomerService.get_all():
            self.tree_cust.insert("", "end", values=(c["id"], c["name"], c["phone"], format_toman(c["current_debt"]), c["loyalty_points"]))

    def settle_cust(self):
        sel = self.tree_cust.selection()
        if not sel:
            messagebox.showwarning("انتخاب", "یک مشتری را انتخاب کنید.")
            return
        cid = self.tree_cust.item(sel[0])["values"][0]
        try:
            amt = int(self.ent_settle.get().strip())
            CustomerService.settle_debt(cid, amt)
            self.ent_settle.delete(0, tk.END)
            self.load_customers_table()
            messagebox.showinfo("ثبت شد", "تسویه با موفقیت ثبت شد.")
        except ValueError:
            messagebox.showerror("خطا", "مبلغ عددی نامعتبر است.")
        except Exception as e:
            messagebox.showerror("خطا", str(e))

    def _build_expense_tab(self, parent):
        box = tk.LabelFrame(parent, text="ثبت هزینه جدید", padx=15, pady=15)
        box.pack(fill="x", padx=15, pady=10)

        tk.Label(box, text="عنوان:").grid(row=0, column=3, sticky="e", pady=5)
        self.ent_exp_t = tk.Entry(box, justify="right")
        self.ent_exp_t.grid(row=0, column=2, padx=5)

        tk.Label(box, text="مبلغ (تومان):").grid(row=0, column=1, sticky="e", pady=5)
        self.ent_exp_a = tk.Entry(box)
        self.ent_exp_a.grid(row=0, column=0, padx=5)

        tk.Label(box, text="دسته‌بندی:").grid(row=1, column=3, sticky="e", pady=5)
        self.cmb_exp_c = ttk.Combobox(box, values=["مواد اولیه", "قبوض و جاری", "حقوق پرسنل", "متفرقه"], state="readonly")
        self.cmb_exp_c.current(0)
        self.cmb_exp_c.grid(row=1, column=2, padx=5)

        tk.Button(box, text="ثبت هزینه", bg="#E74C3C", fg="white", command=self.save_exp).grid(row=1, column=0, columnspan=2, pady=10, sticky="ew")

        self.tree_exp = ttk.Treeview(parent, columns=("title", "cat", "amount", "date"), show="headings")
        self.tree_exp.heading("title", text="عنوان")
        self.tree_exp.heading("cat", text="دسته‌بندی")
        self.tree_exp.heading("amount", text="مبلغ")
        self.tree_exp.heading("date", text="تاریخ")
        self.tree_exp.pack(fill="both", expand=True, padx=15, pady=10)

    def save_exp(self):
        try:
            AccountingService.record_expense(
                self.ent_exp_t.get(),
                self.cmb_exp_c.get(),
                int(self.ent_exp_a.get().strip())
            )
            self.ent_exp_t.delete(0, tk.END)
            self.ent_exp_a.delete(0, tk.END)
            self.load_expenses()
            self.refresh_stats()
            messagebox.showinfo("موفقیت", "هزینه ثبت شد.")
        except Exception as e:
            messagebox.showerror("خطا", str(e))

    def load_expenses(self):
        if not hasattr(self, 'tree_exp'):
            return
        self.tree_exp.delete(*self.tree_exp.get_children())
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT title, category, amount, created_at FROM expenses ORDER BY id DESC LIMIT 50")
            for row in cursor.fetchall():
                self.tree_exp.insert("", "end", values=(row["title"], row["category"], format_toman(row["amount"]), row["created_at"]))

    def refresh_stats(self):
        summary = AccountingService.get_daily_financials()
        self.lbl_sales.config(text=f"فروش امروز: {format_toman(summary.total_sales)}")
        self.lbl_expense.config(text=f"هزینه‌های امروز: {format_toman(summary.total_expenses)}")
        self.lbl_profit.config(text=f"سود خالص: {format_toman(summary.net_profit)}")
