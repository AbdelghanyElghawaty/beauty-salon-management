"""
Database Extended — الإضافات على قاعدة البيانات الأساسية.
==========================================================
Mix In Class بيضيف جداول ودوال جديدة بدون تعديل database.py الأصلي.

الجداول الجديدة:
----------------
👥 الموظفين:
    - employees              : الموظفين
    - attendance             : الحضور والانصراف
    - employee_transactions  : السلف والخصومات والمكافآت
    - salaries               : الرواتب الشهرية

📦 المخزون:
    - inventory_categories   : فئات المنتجات
    - inventory_items        : المنتجات
    - inventory_movements    : حركات الوارد/الصادر
    - suppliers              : الموردين

💼 الإدارة:
    - expenses               : المصاريف
    - other_revenues         : إيرادات إضافية
    - finance_settings       : الإعدادات المالية

الاستخدام:
---------
    from database import Database
    from database_extended import ExtendedDatabaseMixin

    class AppDatabase(ExtendedDatabaseMixin, Database):
        pass

    db = AppDatabase(db_path)
"""

import os
import sqlite3
from datetime import datetime, timedelta


# ============================================================
# Connection Helper
# ============================================================
def _get_conn_ext(db_path):
    """اتصال SQLite آمن للجداول الجديدة."""
    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA busy_timeout = 10000")
    except Exception:
        pass
    return conn


# ============================================================
# ExtendedDatabaseMixin
# ============================================================
class ExtendedDatabaseMixin:
    """
    Mix In — يضاف على كلاس Database الأصلي.
    لازم يكون عنده: self.db_path, self._log_action(), self.base_dir
    """

    # ============================================
    # Initialization — إنشاء الجداول
    # ============================================
    def init_extended_schema(self):
        """ينشئ الجداول الجديدة لو مش موجودة."""
        conn = _get_conn_ext(self.db_path)
        c = conn.cursor()

        # ============================================
        # 🗄️ الموظفين
        # ============================================
        c.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                phone TEXT,
                national_id TEXT,
                position TEXT DEFAULT 'موظف',
                department TEXT,
                hire_date TEXT,
                salary REAL DEFAULT 0,
                commission_rate REAL DEFAULT 0,
                address TEXT,
                email TEXT,
                photo_path TEXT,
                user_id INTEGER,
                is_active INTEGER DEFAULT 1,
                notes TEXT,
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                check_in TEXT,
                check_out TEXT,
                work_hours REAL DEFAULT 0,
                status TEXT DEFAULT 'حاضر',
                notes TEXT,
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
                UNIQUE(employee_id, date)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS employee_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                reason TEXT,
                notes TEXT,
                created_at TEXT,
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS salaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                month TEXT NOT NULL,
                base_salary REAL DEFAULT 0,
                commissions REAL DEFAULT 0,
                bonuses REAL DEFAULT 0,
                advances REAL DEFAULT 0,
                deductions REAL DEFAULT 0,
                net_salary REAL DEFAULT 0,
                paid INTEGER DEFAULT 0,
                paid_date TEXT,
                notes TEXT,
                created_at TEXT,
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
                UNIQUE(employee_id, month)
            )
        """)

        # ============================================
        # 📦 المخزون
        # ============================================
        c.execute("""
            CREATE TABLE IF NOT EXISTS inventory_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                color TEXT DEFAULT '#3b82f6',
                icon TEXT DEFAULT '📦'
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS inventory_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                barcode TEXT UNIQUE,
                category_id INTEGER,
                quantity REAL DEFAULT 0,
                unit TEXT DEFAULT 'قطعة',
                min_quantity REAL DEFAULT 5,
                purchase_price REAL DEFAULT 0,
                selling_price REAL DEFAULT 0,
                supplier TEXT,
                expiry_date TEXT,
                is_active INTEGER DEFAULT 1,
                notes TEXT,
                created_at TEXT,
                FOREIGN KEY (category_id) REFERENCES inventory_categories(id)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS inventory_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit_price REAL DEFAULT 0,
                total_price REAL DEFAULT 0,
                reason TEXT,
                reference TEXT,
                date TEXT NOT NULL,
                notes TEXT,
                created_at TEXT,
                FOREIGN KEY (item_id) REFERENCES inventory_items(id) ON DELETE CASCADE
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                address TEXT,
                email TEXT,
                notes TEXT,
                created_at TEXT
            )
        """)

        # ============================================
        # 💼 الإدارة
        # ============================================
        c.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                description TEXT,
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                payment_method TEXT DEFAULT 'cash',
                receipt_number TEXT,
                notes TEXT,
                created_at TEXT
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS other_revenues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT,
                description TEXT,
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                notes TEXT,
                created_at TEXT
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS finance_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # ============================================
        # Indexes
        # ============================================
        c.execute("CREATE INDEX IF NOT EXISTS idx_attendance_emp_date "
                  "ON attendance(employee_id, date)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_attendance_date "
                  "ON attendance(date)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_emp_trans_emp "
                  "ON employee_transactions(employee_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_inv_mov_item "
                  "ON inventory_movements(item_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_inv_mov_date "
                  "ON inventory_movements(date)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_expenses_date "
                  "ON expenses(date)")

        conn.commit()
        conn.close()

        # ✅ بيانات افتراضية للفئات
        self._seed_inventory_categories()

    def _seed_inventory_categories(self):
        """يضيف فئات افتراضية للمخزون."""
        conn = _get_conn_ext(self.db_path)
        count = conn.execute(
            "SELECT COUNT(*) FROM inventory_categories"
        ).fetchone()[0]

        if count == 0:
            defaults = [
                ("منتجات الحلاقة", "#3b82f6", "💈"),
                ("أدوات ومعدات", "#10b981", "✂️"),
                ("أصباغ ومواد", "#f59e0b", "🎨"),
                ("مستحضرات عناية", "#8b5cf6", "🧴"),
                ("مشروبات", "#ef4444", "☕"),
                ("مستهلكات", "#64748b", "🧻"),
            ]
            conn.executemany(
                "INSERT INTO inventory_categories (name, color, icon) "
                "VALUES (?, ?, ?)",
                defaults
            )
            conn.commit()

        conn.close()

    # ============================================
    # 🗄️ الموظفين — Employees
    # ============================================
    def add_employee(self, full_name, phone="", national_id="",
                     position="موظف", department="", hire_date=None,
                     salary=0, commission_rate=0, address="",
                     email="", photo_path="", user_id=None,
                     notes=""):
        """يضيف موظف جديد."""
        if hire_date is None:
            hire_date = datetime.now().strftime("%Y-%m-%d")

        conn = _get_conn_ext(self.db_path)
        cur = conn.execute("""
            INSERT INTO employees
            (full_name, phone, national_id, position, department,
             hire_date, salary, commission_rate, address, email,
             photo_path, user_id, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            full_name, phone, national_id, position, department,
            hire_date, salary, commission_rate, address, email,
            photo_path, user_id, notes,
            datetime.now().isoformat(timespec="seconds")
        ))
        new_id = cur.lastrowid
        conn.commit()
        conn.close()

        try:
            self._log_action("create", "employees", new_id,
                             new_value={"full_name": full_name,
                                        "position": position})
        except Exception:
            pass
        return new_id

    def list_employees(self, active_only=True):
        """يرجع قائمة الموظفين."""
        conn = _get_conn_ext(self.db_path)
        query = "SELECT * FROM employees"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY full_name"
        rows = conn.execute(query).fetchall()
        conn.close()
        return rows

    def get_employee(self, emp_id):
        """يرجع موظف بالـ ID."""
        conn = _get_conn_ext(self.db_path)
        row = conn.execute(
            "SELECT * FROM employees WHERE id = ?", (emp_id,)
        ).fetchone()
        conn.close()
        return row

    def update_employee(self, emp_id, **kwargs):
        """يحدّث بيانات موظف."""
        if not kwargs:
            return

        allowed = [
            "full_name", "phone", "national_id", "position",
            "department", "hire_date", "salary", "commission_rate",
            "address", "email", "photo_path", "user_id",
            "is_active", "notes",
        ]
        fields = [k for k in kwargs.keys() if k in allowed]
        if not fields:
            return

        set_clause = ", ".join(f"{f} = ?" for f in fields)
        values = [kwargs[f] for f in fields] + [emp_id]

        conn = _get_conn_ext(self.db_path)
        conn.execute(
            f"UPDATE employees SET {set_clause} WHERE id = ?",
            values
        )
        conn.commit()
        conn.close()

        try:
            self._log_action("update", "employees", emp_id,
                             new_value=kwargs)
        except Exception:
            pass

    def delete_employee(self, emp_id):
        """يحذف موظف (Soft delete)."""
        conn = _get_conn_ext(self.db_path)
        conn.execute(
            "UPDATE employees SET is_active = 0 WHERE id = ?",
            (emp_id,)
        )
        conn.commit()
        conn.close()

        try:
            self._log_action("deactivate", "employees", emp_id)
        except Exception:
            pass

    def count_employees(self, active_only=True):
        """يرجع عدد الموظفين."""
        conn = _get_conn_ext(self.db_path)
        query = "SELECT COUNT(*) FROM employees"
        if active_only:
            query += " WHERE is_active = 1"
        count = conn.execute(query).fetchone()[0]
        conn.close()
        return count

    # ============================================
    # 🕐 الحضور والانصراف — Attendance
    # ============================================
    def check_in_employee(self, emp_id, time_str=None, notes=""):
        """تسجيل حضور موظف."""
        if time_str is None:
            time_str = datetime.now().strftime("%H:%M")

        today = datetime.now().strftime("%Y-%m-%d")

        conn = _get_conn_ext(self.db_path)
        existing = conn.execute(
            "SELECT id, check_in FROM attendance "
            "WHERE employee_id = ? AND date = ?",
            (emp_id, today)
        ).fetchone()

        if existing and existing[1]:
            conn.close()
            return False, "الموظف مسجل حضوره بالفعل النهاردة."

        if existing:
            conn.execute(
                "UPDATE attendance SET check_in = ?, status = 'حاضر' "
                "WHERE id = ?",
                (time_str, existing[0])
            )
        else:
            conn.execute("""
                INSERT INTO attendance
                (employee_id, date, check_in, status, notes)
                VALUES (?, ?, ?, 'حاضر', ?)
            """, (emp_id, today, time_str, notes))

        conn.commit()
        conn.close()
        return True, f"تم تسجيل الحضور الساعة {time_str}"

    def check_out_employee(self, emp_id, time_str=None):
        """تسجيل انصراف موظف."""
        if time_str is None:
            time_str = datetime.now().strftime("%H:%M")

        today = datetime.now().strftime("%Y-%m-%d")

        conn = _get_conn_ext(self.db_path)
        row = conn.execute(
            "SELECT id, check_in FROM attendance "
            "WHERE employee_id = ? AND date = ?",
            (emp_id, today)
        ).fetchone()

        if not row:
            conn.close()
            return False, "الموظف مسجلش حضوره النهاردة."

        att_id, check_in = row
        if not check_in:
            conn.close()
            return False, "الموظف مسجلش حضوره النهاردة."

        # احسب ساعات العمل
        try:
            h1, m1 = map(int, check_in.split(":"))
            h2, m2 = map(int, time_str.split(":"))
            hours = (h2 + m2 / 60) - (h1 + m1 / 60)
            if hours < 0:
                hours += 24
        except Exception:
            hours = 0

        conn.execute(
            "UPDATE attendance SET check_out = ?, work_hours = ? "
            "WHERE id = ?",
            (time_str, round(hours, 2), att_id)
        )
        conn.commit()
        conn.close()
        return True, f"تم تسجيل الانصراف الساعة {time_str} ({hours:.1f} ساعة)"

    def list_attendance(self, employee_id=None, date_from=None,
                        date_to=None, limit=500):
        """يرجع سجلات الحضور."""
        conn = _get_conn_ext(self.db_path)
        query = """
            SELECT a.id, a.employee_id, e.full_name, a.date,
                   a.check_in, a.check_out, a.work_hours,
                   a.status, a.notes
            FROM attendance a
            JOIN employees e ON e.id = a.employee_id
            WHERE 1=1
        """
        params = []

        if employee_id:
            query += " AND a.employee_id = ?"
            params.append(employee_id)
        if date_from:
            query += " AND a.date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND a.date <= ?"
            params.append(date_to)

        query += " ORDER BY a.date DESC, a.check_in DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(query, params).fetchall()
        conn.close()
        return rows

    def get_today_attendance(self):
        """يرجع حضور النهاردة لكل الموظفين."""
        today = datetime.now().strftime("%Y-%m-%d")
        conn = _get_conn_ext(self.db_path)
        rows = conn.execute("""
            SELECT e.id, e.full_name, e.position,
                   a.check_in, a.check_out, a.work_hours, a.status
            FROM employees e
            LEFT JOIN attendance a
                ON a.employee_id = e.id AND a.date = ?
            WHERE e.is_active = 1
            ORDER BY e.full_name
        """, (today,)).fetchall()
        conn.close()
        return rows

    # ============================================
    # 💵 السلف والخصومات
    # ============================================
    def add_employee_transaction(self, employee_id, txn_type,
                                 amount, reason="", notes="",
                                 date=None):
        """
        يضيف حركة مالية للموظف.
        txn_type: advance / deduction / bonus
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        conn = _get_conn_ext(self.db_path)
        cur = conn.execute("""
            INSERT INTO employee_transactions
            (employee_id, type, amount, date, reason, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (employee_id, txn_type, amount, date, reason, notes,
              datetime.now().isoformat(timespec="seconds")))
        new_id = cur.lastrowid
        conn.commit()
        conn.close()

        try:
            self._log_action("create", "employee_transactions", new_id,
                             new_value={"employee_id": employee_id,
                                        "type": txn_type,
                                        "amount": amount})
        except Exception:
            pass
        return new_id

    def list_employee_transactions(self, employee_id=None,
                                   txn_type=None, month=None,
                                   limit=500):
        """يرجع حركات الموظفين."""
        conn = _get_conn_ext(self.db_path)
        query = """
            SELECT t.id, t.employee_id, e.full_name, t.type,
                   t.amount, t.date, t.reason, t.notes
            FROM employee_transactions t
            JOIN employees e ON e.id = t.employee_id
            WHERE 1=1
        """
        params = []

        if employee_id:
            query += " AND t.employee_id = ?"
            params.append(employee_id)
        if txn_type:
            query += " AND t.type = ?"
            params.append(txn_type)
        if month:
            query += " AND t.date LIKE ?"
            params.append(f"{month}%")

        query += " ORDER BY t.date DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(query, params).fetchall()
        conn.close()
        return rows

    def delete_employee_transaction(self, txn_id):
        """يحذف حركة مالية."""
        conn = _get_conn_ext(self.db_path)
        conn.execute(
            "DELETE FROM employee_transactions WHERE id = ?",
            (txn_id,)
        )
        conn.commit()
        conn.close()

    # ============================================
    # 💰 الرواتب — Salaries
    # ============================================
    def calculate_salary(self, employee_id, month):
        """
        يحسب راتب الموظف لشهر معين.
        month: YYYY-MM

        طريقة الحساب:
        net = base + commissions + bonuses - advances - deductions
        """
        conn = _get_conn_ext(self.db_path)

        # بيانات الموظف
        emp = conn.execute(
            "SELECT salary, commission_rate, full_name "
            "FROM employees WHERE id = ?", (employee_id,)
        ).fetchone()

        if not emp:
            conn.close()
            return None

        base_salary = emp[0] or 0
        commission_rate = emp[1] or 0
        full_name = emp[2]

        # العمولات = إيرادات الحجوزات × نسبة العمولة
        commissions = 0
        try:
            bookings = conn.execute("""
                SELECT COALESCE(SUM(s.price + COALESCE(b.extra_services_total, 0)), 0)
                FROM bookings b
                JOIN services s ON s.id = b.service_id
                WHERE b.barber = ? AND b.date LIKE ?
            """, (full_name, f"{month}%")).fetchone()[0] or 0
            commissions = bookings * (commission_rate / 100)
        except Exception:
            pass

        # المكافآت
        bonuses = conn.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM employee_transactions
            WHERE employee_id = ? AND type = 'bonus'
            AND date LIKE ?
        """, (employee_id, f"{month}%")).fetchone()[0] or 0

        # السلف
        advances = conn.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM employee_transactions
            WHERE employee_id = ? AND type = 'advance'
            AND date LIKE ?
        """, (employee_id, f"{month}%")).fetchone()[0] or 0

        # الخصومات
        deductions = conn.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM employee_transactions
            WHERE employee_id = ? AND type = 'deduction'
            AND date LIKE ?
        """, (employee_id, f"{month}%")).fetchone()[0] or 0

        conn.close()

        net = base_salary + commissions + bonuses - advances - deductions

        return {
            "employee_id": employee_id,
            "full_name": full_name,
            "month": month,
            "base_salary": round(base_salary, 2),
            "commissions": round(commissions, 2),
            "bonuses": round(bonuses, 2),
            "advances": round(advances, 2),
            "deductions": round(deductions, 2),
            "net_salary": round(net, 2),
        }

    def save_salary(self, employee_id, month, data, paid=False):
        """يحفظ راتب شهري."""
        conn = _get_conn_ext(self.db_path)
        paid_date = datetime.now().strftime("%Y-%m-%d") if paid else None

        try:
            conn.execute("""
                INSERT INTO salaries
                (employee_id, month, base_salary, commissions,
                 bonuses, advances, deductions, net_salary,
                 paid, paid_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(employee_id, month) DO UPDATE SET
                    base_salary = excluded.base_salary,
                    commissions = excluded.commissions,
                    bonuses = excluded.bonuses,
                    advances = excluded.advances,
                    deductions = excluded.deductions,
                    net_salary = excluded.net_salary,
                    paid = excluded.paid,
                    paid_date = excluded.paid_date
            """, (
                employee_id, month,
                data.get("base_salary", 0),
                data.get("commissions", 0),
                data.get("bonuses", 0),
                data.get("advances", 0),
                data.get("deductions", 0),
                data.get("net_salary", 0),
                1 if paid else 0,
                paid_date,
                datetime.now().isoformat(timespec="seconds")
            ))
            conn.commit()
        except Exception as e:
            conn.close()
            return False, str(e)

        conn.close()
        return True, "تم حفظ الراتب."

    def list_salaries(self, employee_id=None, month=None, limit=200):
        """يرجع الرواتب."""
        conn = _get_conn_ext(self.db_path)
        query = """
            SELECT s.id, s.employee_id, e.full_name, s.month,
                   s.base_salary, s.commissions, s.bonuses,
                   s.advances, s.deductions, s.net_salary,
                   s.paid, s.paid_date
            FROM salaries s
            JOIN employees e ON e.id = s.employee_id
            WHERE 1=1
        """
        params = []

        if employee_id:
            query += " AND s.employee_id = ?"
            params.append(employee_id)
        if month:
            query += " AND s.month = ?"
            params.append(month)

        query += " ORDER BY s.month DESC, e.full_name LIMIT ?"
        params.append(limit)

        rows = conn.execute(query, params).fetchall()
        conn.close()
        return rows

    def mark_salary_paid(self, salary_id):
        """يحدد راتب كمدفوع."""
        conn = _get_conn_ext(self.db_path)
        conn.execute("""
            UPDATE salaries
            SET paid = 1, paid_date = ?
            WHERE id = ?
        """, (datetime.now().strftime("%Y-%m-%d"), salary_id))
        conn.commit()
        conn.close()

    # ============================================
    # 📦 المخزون — Categories
    # ============================================
    def list_inventory_categories(self):
        """يرجع فئات المخزون."""
        conn = _get_conn_ext(self.db_path)
        rows = conn.execute(
            "SELECT id, name, color, icon FROM inventory_categories "
            "ORDER BY name"
        ).fetchall()
        conn.close()
        return rows

    def add_inventory_category(self, name, color="#3b82f6", icon="📦"):
        """يضيف فئة جديدة."""
        try:
            conn = _get_conn_ext(self.db_path)
            cur = conn.execute(
                "INSERT INTO inventory_categories (name, color, icon) "
                "VALUES (?, ?, ?)",
                (name, color, icon)
            )
            new_id = cur.lastrowid
            conn.commit()
            conn.close()
            return new_id
        except sqlite3.IntegrityError:
            return None

    # ============================================
    # 📦 المخزون — Items
    # ============================================
    def add_inventory_item(self, name, category_id=None, barcode=None,
                           quantity=0, unit="قطعة", min_quantity=5,
                           purchase_price=0, selling_price=0,
                           supplier="", expiry_date=None, notes=""):
        """يضيف منتج للمخزون."""
        conn = _get_conn_ext(self.db_path)
        try:
            cur = conn.execute("""
                INSERT INTO inventory_items
                (name, barcode, category_id, quantity, unit,
                 min_quantity, purchase_price, selling_price,
                 supplier, expiry_date, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name, barcode or None, category_id,
                quantity, unit, min_quantity,
                purchase_price, selling_price,
                supplier, expiry_date, notes,
                datetime.now().isoformat(timespec="seconds")
            ))
            new_id = cur.lastrowid
            conn.commit()
            conn.close()

            try:
                self._log_action("create", "inventory_items", new_id,
                                 new_value={"name": name,
                                            "quantity": quantity})
            except Exception:
                pass
            return new_id
        except sqlite3.IntegrityError:
            conn.close()
            return None

    def list_inventory_items(self, category_id=None,
                             active_only=True, low_stock_only=False):
        """يرجع قائمة المنتجات."""
        conn = _get_conn_ext(self.db_path)
        query = """
            SELECT i.id, i.name, i.barcode, i.category_id,
                   c.name as category_name, c.color as category_color,
                   c.icon as category_icon,
                   i.quantity, i.unit, i.min_quantity,
                   i.purchase_price, i.selling_price,
                   i.supplier, i.expiry_date,
                   i.is_active, i.notes
            FROM inventory_items i
            LEFT JOIN inventory_categories c ON c.id = i.category_id
            WHERE 1=1
        """
        params = []

        if active_only:
            query += " AND i.is_active = 1"
        if category_id:
            query += " AND i.category_id = ?"
            params.append(category_id)
        if low_stock_only:
            query += " AND i.quantity <= i.min_quantity"

        query += " ORDER BY i.name"
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return rows

    def get_inventory_item(self, item_id):
        """يرجع منتج بالـ ID."""
        conn = _get_conn_ext(self.db_path)
        row = conn.execute(
            "SELECT * FROM inventory_items WHERE id = ?",
            (item_id,)
        ).fetchone()
        conn.close()
        return row

    def update_inventory_item(self, item_id, **kwargs):
        """يحدّث منتج."""
        if not kwargs:
            return

        allowed = [
            "name", "barcode", "category_id", "quantity",
            "unit", "min_quantity", "purchase_price",
            "selling_price", "supplier", "expiry_date",
            "is_active", "notes",
        ]
        fields = [k for k in kwargs.keys() if k in allowed]
        if not fields:
            return

        set_clause = ", ".join(f"{f} = ?" for f in fields)
        values = [kwargs[f] for f in fields] + [item_id]

        conn = _get_conn_ext(self.db_path)
        conn.execute(
            f"UPDATE inventory_items SET {set_clause} WHERE id = ?",
            values
        )
        conn.commit()
        conn.close()

    def delete_inventory_item(self, item_id):
        """يحذف منتج (Soft delete)."""
        conn = _get_conn_ext(self.db_path)
        conn.execute(
            "UPDATE inventory_items SET is_active = 0 WHERE id = ?",
            (item_id,)
        )
        conn.commit()
        conn.close()

    # ============================================
    # 📦 المخزون — Movements
    # ============================================
    def add_inventory_movement(self, item_id, movement_type,
                               quantity, unit_price=0, reason="",
                               reference="", notes="", date=None):
        """
        يضيف حركة مخزون (وارد/صادر).
        movement_type: 'in' أو 'out'
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        total = quantity * unit_price

        conn = _get_conn_ext(self.db_path)

        # احسب الكمية الجديدة
        item = conn.execute(
            "SELECT quantity, name FROM inventory_items WHERE id = ?",
            (item_id,)
        ).fetchone()

        if not item:
            conn.close()
            return False, "المنتج مش موجود."

        current_qty = item[0] or 0

        if movement_type == "in":
            new_qty = current_qty + quantity
        elif movement_type == "out":
            if quantity > current_qty:
                conn.close()
                return False, f"الكمية المتاحة {current_qty} بس."
            new_qty = current_qty - quantity
        else:
            conn.close()
            return False, "نوع الحركة غلط."

        # احفظ الحركة
        conn.execute("""
            INSERT INTO inventory_movements
            (item_id, type, quantity, unit_price, total_price,
             reason, reference, date, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item_id, movement_type, quantity, unit_price, total,
            reason, reference, date, notes,
            datetime.now().isoformat(timespec="seconds")
        ))

        # حدّث الكمية
        conn.execute(
            "UPDATE inventory_items SET quantity = ? WHERE id = ?",
            (new_qty, item_id)
        )

        conn.commit()
        conn.close()

        try:
            self._log_action(
                "create" if movement_type == "in" else "update",
                "inventory_movements", item_id,
                new_value={"type": movement_type, "quantity": quantity}
            )
        except Exception:
            pass

        return True, f"تم التسجيل. الكمية الجديدة: {new_qty}"

    def list_inventory_movements(self, item_id=None,
                                 movement_type=None,
                                 date_from=None, date_to=None,
                                 limit=500):
        """يرجع حركات المخزون."""
        conn = _get_conn_ext(self.db_path)
        query = """
            SELECT m.id, m.item_id, i.name, m.type,
                   m.quantity, m.unit_price, m.total_price,
                   m.reason, m.reference, m.date, m.notes
            FROM inventory_movements m
            JOIN inventory_items i ON i.id = m.item_id
            WHERE 1=1
        """
        params = []

        if item_id:
            query += " AND m.item_id = ?"
            params.append(item_id)
        if movement_type:
            query += " AND m.type = ?"
            params.append(movement_type)
        if date_from:
            query += " AND m.date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND m.date <= ?"
            params.append(date_to)

        query += " ORDER BY m.date DESC, m.id DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(query, params).fetchall()
        conn.close()
        return rows

    def get_low_stock_items(self):
        """يرجع المنتجات اللي وصلت للحد الأدنى."""
        conn = _get_conn_ext(self.db_path)
        rows = conn.execute("""
            SELECT id, name, quantity, min_quantity, unit
            FROM inventory_items
            WHERE is_active = 1 AND quantity <= min_quantity
            ORDER BY quantity ASC
        """).fetchall()
        conn.close()
        return rows

    def get_inventory_value(self):
        """يرجع قيمة المخزون."""
        conn = _get_conn_ext(self.db_path)
        row = conn.execute("""
            SELECT
                COALESCE(SUM(quantity * purchase_price), 0),
                COALESCE(SUM(quantity * selling_price), 0),
                COUNT(*)
            FROM inventory_items
            WHERE is_active = 1
        """).fetchone()
        conn.close()
        return {
            "cost_value": row[0],
            "selling_value": row[1],
            "items_count": row[2],
        }

    # ============================================
    # 💼 المصاريف — Expenses
    # ============================================
    def add_expense(self, category, amount, description="",
                    payment_method="cash", receipt_number="",
                    notes="", date=None):
        """يضيف مصروف."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        conn = _get_conn_ext(self.db_path)
        cur = conn.execute("""
            INSERT INTO expenses
            (category, description, amount, date, payment_method,
             receipt_number, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            category, description, amount, date, payment_method,
            receipt_number, notes,
            datetime.now().isoformat(timespec="seconds")
        ))
        new_id = cur.lastrowid
        conn.commit()
        conn.close()

        try:
            self._log_action("create", "expenses", new_id,
                             new_value={"category": category,
                                        "amount": amount})
        except Exception:
            pass
        return new_id

    def list_expenses(self, date_from=None, date_to=None,
                      category=None, limit=500):
        """يرجع المصاريف."""
        conn = _get_conn_ext(self.db_path)
        query = """
            SELECT id, category, description, amount, date,
                   payment_method, receipt_number, notes
            FROM expenses WHERE 1=1
        """
        params = []

        if date_from:
            query += " AND date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND date <= ?"
            params.append(date_to)
        if category:
            query += " AND category = ?"
            params.append(category)

        query += " ORDER BY date DESC, id DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(query, params).fetchall()
        conn.close()
        return rows

    def delete_expense(self, expense_id):
        """يحذف مصروف."""
        conn = _get_conn_ext(self.db_path)
        conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        conn.commit()
        conn.close()

    # ============================================
    # 💰 الإيرادات الإضافية
    # ============================================
    def add_other_revenue(self, source, amount, description="",
                          notes="", date=None):
        """يضيف إيراد إضافي."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        conn = _get_conn_ext(self.db_path)
        cur = conn.execute("""
            INSERT INTO other_revenues
            (source, description, amount, date, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            source, description, amount, date, notes,
            datetime.now().isoformat(timespec="seconds")
        ))
        new_id = cur.lastrowid
        conn.commit()
        conn.close()
        return new_id

    def list_other_revenues(self, date_from=None, date_to=None,
                            limit=500):
        """يرجع الإيرادات الإضافية."""
        conn = _get_conn_ext(self.db_path)
        query = """
            SELECT id, source, description, amount, date, notes
            FROM other_revenues WHERE 1=1
        """
        params = []

        if date_from:
            query += " AND date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND date <= ?"
            params.append(date_to)

        query += " ORDER BY date DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(query, params).fetchall()
        conn.close()
        return rows

    # ============================================
    # 📊 تقارير شاملة
    # ============================================
    def get_profit_loss_report(self, date_from, date_to):
        """تقرير الأرباح والخسائر."""
        conn = _get_conn_ext(self.db_path)

        # إيرادات الحجوزات
        bookings_revenue = conn.execute("""
            SELECT COALESCE(SUM(s.price + COALESCE(b.extra_services_total, 0)), 0)
            FROM bookings b
            JOIN services s ON s.id = b.service_id
            WHERE b.date >= ? AND b.date <= ?
        """, (date_from, date_to)).fetchone()[0] or 0

        # إيرادات أخرى
        other_revenue = conn.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM other_revenues
            WHERE date >= ? AND date <= ?
        """, (date_from, date_to)).fetchone()[0] or 0

        # المصاريف
        expenses = conn.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM expenses
            WHERE date >= ? AND date <= ?
        """, (date_from, date_to)).fetchone()[0] or 0

        # الرواتب المدفوعة
        salaries = conn.execute("""
            SELECT COALESCE(SUM(net_salary), 0) FROM salaries
            WHERE paid = 1 AND paid_date >= ? AND paid_date <= ?
        """, (date_from, date_to)).fetchone()[0] or 0

        conn.close()

        total_revenue = bookings_revenue + other_revenue
        total_costs = expenses + salaries
        profit = total_revenue - total_costs
        margin = (profit / total_revenue * 100) if total_revenue > 0 else 0

        return {
            "bookings_revenue": round(bookings_revenue, 2),
            "other_revenue": round(other_revenue, 2),
            "total_revenue": round(total_revenue, 2),
            "expenses": round(expenses, 2),
            "salaries": round(salaries, 2),
            "total_costs": round(total_costs, 2),
            "profit": round(profit, 2),
            "margin": round(margin, 2),
        }

    def get_employee_performance(self, employee_id, date_from, date_to):
        """أداء موظف في فترة."""
        conn = _get_conn_ext(self.db_path)

        emp = conn.execute(
            "SELECT full_name FROM employees WHERE id = ?",
            (employee_id,)
        ).fetchone()

        if not emp:
            conn.close()
            return None

        name = emp[0]

        # عدد الحجوزات والإيرادات
        row = conn.execute("""
            SELECT COUNT(*),
                   COALESCE(SUM(s.price + COALESCE(b.extra_services_total, 0)), 0)
            FROM bookings b
            JOIN services s ON s.id = b.service_id
            WHERE b.barber = ?
              AND b.date >= ? AND b.date <= ?
        """, (name, date_from, date_to)).fetchone()

        # الحضور
        att = conn.execute("""
            SELECT
                COUNT(*) as days,
                COALESCE(SUM(work_hours), 0) as hours
            FROM attendance
            WHERE employee_id = ?
              AND date >= ? AND date <= ?
              AND check_in IS NOT NULL
        """, (employee_id, date_from, date_to)).fetchone()

        conn.close()

        return {
            "employee_id": employee_id,
            "full_name": name,
            "bookings_count": row[0] or 0,
            "revenue": round(row[1] or 0, 2),
            "attendance_days": att[0] or 0,
            "work_hours": round(att[1] or 0, 2),
        }

    def get_today_summary(self):
        """ملخص اليوم (للـ Dashboard)."""
        today = datetime.now().strftime("%Y-%m-%d")
        conn = _get_conn_ext(self.db_path)

        # الحجوزات
        bookings = conn.execute("""
            SELECT COUNT(*),
                   COALESCE(SUM(s.price + COALESCE(b.extra_services_total, 0)), 0)
            FROM bookings b
            JOIN services s ON s.id = b.service_id
            WHERE b.date = ?
        """, (today,)).fetchone()

        # مصاريف النهاردة
        expenses = conn.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM expenses
            WHERE date = ?
        """, (today,)).fetchone()[0] or 0

        # حضور النهاردة
        attendance = conn.execute("""
            SELECT COUNT(*) FROM attendance
            WHERE date = ? AND check_in IS NOT NULL
        """, (today,)).fetchone()[0] or 0

        # منتجات قرب تخلص
        low_stock = conn.execute("""
            SELECT COUNT(*) FROM inventory_items
            WHERE is_active = 1 AND quantity <= min_quantity
        """).fetchone()[0] or 0

        conn.close()

        return {
            "bookings_count": bookings[0] or 0,
            "bookings_revenue": round(bookings[1] or 0, 2),
            "expenses": round(expenses, 2),
            "attendance_count": attendance,
            "low_stock_count": low_stock,
        }