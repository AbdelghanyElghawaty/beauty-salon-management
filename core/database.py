"""
Database layer — PySide6 compatible with Soft Delete for services & customers.
+ Audit Log (سجل العمليات)
+ PBKDF2 password hashing مع دعم SHA256 القديم
+ Reports with date range filters
+ Settings (key-value) للإعدادات العامة
"""

import os
import json
import shutil
import hashlib
import hmac
import secrets
import sqlite3
from datetime import datetime, timedelta
from core.auth import User

# تعطيل cachier للتوافق مع Nuitka (مش محتاجينه أصلاً)
def cachier(*args, **kwargs):
    def decorator(func):
        func.clear_cache = lambda: None
        return func
    return decorator

def _get_conn(db_path):
    """اتصال SQLite آمن — WAL mode لتجنب database is locked."""
    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA busy_timeout = 10000")
    except Exception:
        pass
    return conn


def _date_clause(date_from, date_to, column="bookings.date"):
    """يبني شرط WHERE للفلتر بالتاريخ."""
    clauses = []
    params = []
    if date_from:
        clauses.append(f"{column} >= ?")
        params.append(date_from)
    if date_to:
        clauses.append(f"{column} <= ?")
        params.append(date_to)
    if clauses:
        return " AND " + " AND ".join(clauses), params
    return "", params


# ============================================================
# Cached read queries
# ============================================================
@cachier(stale_after=timedelta(minutes=10))
def _list_services(db_path):
    conn = _get_conn(db_path)
    rows = conn.execute(
        "SELECT id, name, price FROM services WHERE is_active = 1 ORDER BY name"
    ).fetchall()
    conn.close()
    return rows


@cachier(stale_after=timedelta(minutes=10))
def _list_all_services(db_path):
    conn = _get_conn(db_path)
    rows = conn.execute(
        "SELECT id, name, price, is_active FROM services "
        "ORDER BY is_active DESC, name"
    ).fetchall()
    conn.close()
    return rows


@cachier(stale_after=timedelta(minutes=10))
def _list_customers(db_path):
    conn = _get_conn(db_path)
    rows = conn.execute(
        "SELECT id, name, phone, loyalty_points FROM customers "
        "WHERE is_active = 1 ORDER BY name"
    ).fetchall()
    conn.close()
    return rows


@cachier(stale_after=timedelta(minutes=10))
def _list_all_customers(db_path):
    conn = _get_conn(db_path)
    rows = conn.execute(
        "SELECT id, name, phone, loyalty_points, is_active FROM customers "
        "ORDER BY is_active DESC, name"
    ).fetchall()
    conn.close()
    return rows


@cachier(stale_after=timedelta(minutes=5))
def _list_bookings(db_path):
    conn = _get_conn(db_path)
    rows = conn.execute("""
        SELECT bookings.id, customers.name, services.name, services.price,
               bookings.barber, bookings.date, bookings.time,
               bookings.extra_services, bookings.extra_services_total,
               bookings.payment_method
        FROM bookings
        JOIN customers ON bookings.customer_id = customers.id
        JOIN services ON bookings.service_id = services.id
        ORDER BY bookings.date, bookings.time
    """).fetchall()
    conn.close()
    return rows


@cachier(stale_after=timedelta(minutes=5))
def _revenue_report(db_path):
    conn = _get_conn(db_path)
    total = conn.execute("""
        SELECT COALESCE(SUM(services.price + COALESCE(bookings.extra_services_total, 0)), 0)
        FROM bookings JOIN services ON bookings.service_id = services.id
    """).fetchone()[0]
    count = conn.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
    conn.close()
    return {"total_revenue": total, "total_bookings": count}


@cachier(stale_after=timedelta(minutes=5))
def _popular_services_report(db_path):
    conn = _get_conn(db_path)
    rows = conn.execute("""
        SELECT services.name, COUNT(*) as cnt
        FROM bookings JOIN services ON bookings.service_id = services.id
        GROUP BY services.name
        ORDER BY cnt DESC
    """).fetchall()
    conn.close()
    return rows


@cachier(stale_after=timedelta(minutes=1))
def _list_shifts(db_path):
    conn = _get_conn(db_path)
    rows = conn.execute(
        "SELECT id, start_time, end_time, total_revenue, total_bookings, status "
        "FROM shifts ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return rows


# ============================================================
# Database class
# ============================================================
class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.base_dir = os.path.dirname(db_path)
        self.receipts_dir = os.path.join(self.base_dir, "receipts")
        self._current_user = None
        self._init_schema()
        self._seed_default_services()
        self._seed_default_admin()
        self._seed_default_settings()

    # ============================================
    # SETUP
    # ============================================
    def _init_schema(self):
        conn = _get_conn(self.db_path)
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                price REAL NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                loyalty_points INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                service_id INTEGER NOT NULL,
                barber TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                created_at TEXT,
                extra_services TEXT,
                extra_services_total REAL DEFAULT 0,
                payment_method TEXT DEFAULT 'cash',
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (service_id) REFERENCES services(id)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS shifts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TEXT NOT NULL,
                end_time TEXT,
                total_revenue REAL,
                total_bookings INTEGER,
                cash_total REAL DEFAULT 0,
                card_total REAL DEFAULT 0,
                wallet_total REAL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'open'
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'employee',
                permissions TEXT NOT NULL DEFAULT '{}'
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                action TEXT NOT NULL,
                table_name TEXT,
                record_id INTEGER,
                old_value TEXT,
                new_value TEXT,
                timestamp TEXT NOT NULL
            )
        """)
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_timestamp
            ON audit_log(timestamp DESC)
        """)
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_user
            ON audit_log(user_id)
        """)
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_table
            ON audit_log(table_name, record_id)
        """)

        # --- settings (key-value) ---
        c.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        conn.commit()

        # ============================================
        # MIGRATIONS
        # ============================================
        c.execute("PRAGMA table_info(services)")
        svc_columns = [row[1] for row in c.fetchall()]
        if "is_active" not in svc_columns:
            c.execute(
                "ALTER TABLE services ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1"
            )
            conn.commit()

        c.execute("PRAGMA table_info(customers)")
        cust_columns = [row[1] for row in c.fetchall()]
        if "is_active" not in cust_columns:
            c.execute(
                "ALTER TABLE customers ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1"
            )
            conn.commit()
        if "loyalty_points" not in cust_columns:
            c.execute(
                "ALTER TABLE customers ADD COLUMN loyalty_points "
                "INTEGER NOT NULL DEFAULT 0"
            )
            conn.commit()

        c.execute("PRAGMA table_info(bookings)")
        columns = [row[1] for row in c.fetchall()]
        if "created_at" not in columns:
            c.execute("ALTER TABLE bookings ADD COLUMN created_at TEXT")
            c.execute(
                "UPDATE bookings SET created_at = date || ' ' || time "
                "WHERE created_at IS NULL"
            )
            conn.commit()
        if "extra_services" not in columns:
            c.execute("ALTER TABLE bookings ADD COLUMN extra_services TEXT")
            conn.commit()
        if "extra_services_total" not in columns:
            c.execute(
                "ALTER TABLE bookings ADD COLUMN extra_services_total REAL DEFAULT 0"
            )
            conn.commit()
        if "payment_method" not in columns:
            c.execute(
                "ALTER TABLE bookings ADD COLUMN payment_method TEXT DEFAULT 'cash'"
            )
            c.execute(
                "UPDATE bookings SET payment_method = 'cash' "
                "WHERE payment_method IS NULL"
            )
            conn.commit()

        c.execute("PRAGMA table_info(shifts)")
        shift_columns = [row[1] for row in c.fetchall()]
        for col in ("cash_total", "card_total", "wallet_total"):
            if col not in shift_columns:
                c.execute(f"ALTER TABLE shifts ADD COLUMN {col} REAL DEFAULT 0")
                conn.commit()

        conn.close()

    def _seed_default_services(self):
        if self.list_services():
            return
        defaults = [
            ("حلاقة شعر", 50.0),
            ("تهذيب لحية", 30.0),
            ("شعر ولحية", 70.0),
            ("حلاقة أطفال", 35.0),
            ("صبغة شعر", 120.0),
        ]
        conn = _get_conn(self.db_path)
        conn.executemany(
            "INSERT INTO services (name, price) VALUES (?, ?)", defaults
        )
        conn.commit()
        conn.close()
        _list_services.clear_cache()
        _list_all_services.clear_cache()

    def _seed_default_admin(self):
        conn = _get_conn(self.db_path)
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if count == 0:
            conn.execute(
                "INSERT INTO users (username, password_hash, role, permissions) "
                "VALUES (?, ?, 'admin', '{}')",
                ("admin", self._hash_password("admin")),
            )
            conn.commit()
        conn.close()

    # ============================================
    # SETTINGS
    # ============================================
    _DEFAULT_SETTINGS = {
        "shop_name": "صالون الحلاقة",
        "shop_phone": "",
        "shop_address": "",
        "currency": "ج.م",
        "theme": "dark",   # "dark" أو "light"
    }

    def _seed_default_settings(self):
        """يضيف القيم الافتراضية للإعدادات لو مش موجودة."""
        conn = _get_conn(self.db_path)
        for key, value in self._DEFAULT_SETTINGS.items():
            existing = conn.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ).fetchone()
            if not existing:
                conn.execute(
                    "INSERT INTO settings (key, value) VALUES (?, ?)",
                    (key, str(value)),
                )
        conn.commit()
        conn.close()

    def get_setting(self, key, default=None):
        """يرجع قيمة إعداد معين."""
        conn = _get_conn(self.db_path)
        row = conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        conn.close()
        if row is None:
            return default
        return row[0]

    def set_setting(self, key, value):
        """يحفظ قيمة إعداد (insert أو update)."""
        conn = _get_conn(self.db_path)
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, str(value)),
        )
        conn.commit()
        conn.close()
        self._log_action("update", "settings", None,
                         new_value={"key": key})

    def get_all_settings(self):
        """يرجع كل الإعدادات كـ dict."""
        conn = _get_conn(self.db_path)
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
        conn.close()
        return {k: v for k, v in rows}

    def set_many_settings(self, settings_dict):
        """يحفظ عدة إعدادات مرة واحدة."""
        if not settings_dict:
            return
        conn = _get_conn(self.db_path)
        for key, value in settings_dict.items():
            conn.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, str(value)),
            )
        conn.commit()
        conn.close()
        self._log_action("update", "settings", None,
                         new_value={"keys": list(settings_dict.keys())})

    # ============================================
    # PASSWORD HASHING — PBKDF2 + Backward Compat
    # ============================================
    _PBKDF2_ITERATIONS = 200_000
    _PBKDF2_ALGO = "sha256"
    _SALT_BYTES = 32

    @classmethod
    def _hash_password(cls, password):
        salt = secrets.token_hex(cls._SALT_BYTES)
        pwd_hash = hashlib.pbkdf2_hmac(
            cls._PBKDF2_ALGO,
            password.encode("utf-8"),
            bytes.fromhex(salt),
            cls._PBKDF2_ITERATIONS,
        ).hex()
        return f"pbkdf2_{cls._PBKDF2_ALGO}${cls._PBKDF2_ITERATIONS}${salt}${pwd_hash}"

    @classmethod
    def _verify_password(cls, password, stored_hash):
        if not stored_hash:
            return False
        if stored_hash.startswith("pbkdf2_"):
            try:
                parts = stored_hash.split("$")
                if len(parts) != 4:
                    return False
                algo_part, iters_str, salt, expected = parts
                algo = algo_part.replace("pbkdf2_", "")
                iterations = int(iters_str)
                computed = hashlib.pbkdf2_hmac(
                    algo,
                    password.encode("utf-8"),
                    bytes.fromhex(salt),
                    iterations,
                ).hex()
                return hmac.compare_digest(computed, expected)
            except Exception:
                return False
        try:
            legacy = hashlib.sha256(password.encode("utf-8")).hexdigest()
            return hmac.compare_digest(legacy, stored_hash)
        except Exception:
            return False

    @staticmethod
    def _is_legacy_hash(stored_hash):
        if not stored_hash:
            return False
        if stored_hash.startswith("pbkdf2_"):
            return False
        return len(stored_hash) == 64 and all(
            c in "0123456789abcdef" for c in stored_hash.lower()
        )

    # ============================================
    # AUDIT LOG — Core
    # ============================================
    def set_current_user(self, user):
        self._current_user = user

    def _log_action(self, action, table_name=None, record_id=None,
                    old_value=None, new_value=None):
        try:
            user_id = None
            username = "system"
            if self._current_user is not None:
                user_id = getattr(self._current_user, "id", None)
                username = getattr(self._current_user, "username", "system")

            old_json = None
            new_json = None
            if old_value is not None:
                try:
                    old_json = json.dumps(old_value, ensure_ascii=False)
                except Exception:
                    old_json = str(old_value)
            if new_value is not None:
                try:
                    new_json = json.dumps(new_value, ensure_ascii=False)
                except Exception:
                    new_json = str(new_value)

            conn = _get_conn(self.db_path)
            conn.execute(
                "INSERT INTO audit_log "
                "(user_id, username, action, table_name, record_id, "
                "old_value, new_value, timestamp) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (user_id, username, action, table_name, record_id,
                 old_json, new_json,
                 datetime.now().isoformat(timespec="seconds")),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    # ============================================
    # AUDIT LOG — Queries
    # ============================================
    def list_audit_log(self, limit=500, username=None, action=None,
                       table_name=None, date_from=None, date_to=None):
        conn = _get_conn(self.db_path)
        query = ("SELECT id, username, action, table_name, record_id, "
                 "old_value, new_value, timestamp FROM audit_log WHERE 1=1")
        params = []

        if username:
            query += " AND username = ?"
            params.append(username)
        if action:
            query += " AND action = ?"
            params.append(action)
        if table_name:
            query += " AND table_name = ?"
            params.append(table_name)
        if date_from:
            query += " AND timestamp >= ?"
            params.append(date_from)
        if date_to:
            query += " AND timestamp <= ?"
            params.append(date_to + "T23:59:59")

        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(query, params).fetchall()
        conn.close()
        return rows

    def get_audit_entry(self, entry_id):
        conn = _get_conn(self.db_path)
        row = conn.execute(
            "SELECT id, username, action, table_name, record_id, "
            "old_value, new_value, timestamp "
            "FROM audit_log WHERE id = ?",
            (entry_id,),
        ).fetchone()
        conn.close()
        return row

    def list_audit_usernames(self):
        conn = _get_conn(self.db_path)
        rows = conn.execute(
            "SELECT DISTINCT username FROM audit_log "
            "WHERE username IS NOT NULL ORDER BY username"
        ).fetchall()
        conn.close()
        return [r[0] for r in rows]

    def clear_audit_log(self, older_than_days=None):
        conn = _get_conn(self.db_path)
        if older_than_days is None:
            conn.execute("DELETE FROM audit_log")
        else:
            cutoff = (datetime.now() -
                      timedelta(days=older_than_days)).isoformat(timespec="seconds")
            conn.execute("DELETE FROM audit_log WHERE timestamp < ?", (cutoff,))
        conn.commit()
        conn.close()

    # ============================================
    # SERVICES
    # ============================================
    def list_services(self):
        return _list_services(self.db_path)

    def list_all_services(self):
        return _list_all_services(self.db_path)

    def get_service(self, service_id):
        conn = _get_conn(self.db_path)
        row = conn.execute(
            "SELECT id, name, price, is_active FROM services WHERE id = ?",
            (service_id,),
        ).fetchone()
        conn.close()
        return row

    def add_service(self, name, price):
        conn = _get_conn(self.db_path)
        cur = conn.execute(
            "INSERT INTO services (name, price) VALUES (?, ?)", (name, price)
        )
        new_id = cur.lastrowid
        conn.commit()
        conn.close()
        _list_services.clear_cache()
        _list_all_services.clear_cache()
        self._log_action(
            "create", "services", new_id,
            new_value={"name": name, "price": price},
        )

    def update_service(self, service_id, name, price):
        old = self.get_service(service_id)
        old_data = None
        if old:
            old_data = {"name": old[1], "price": old[2], "is_active": old[3]}

        conn = _get_conn(self.db_path)
        conn.execute(
            "UPDATE services SET name = ?, price = ? WHERE id = ?",
            (name, price, service_id),
        )
        conn.commit()
        conn.close()
        _list_services.clear_cache()
        _list_all_services.clear_cache()
        self._log_action(
            "update", "services", service_id,
            old_value=old_data,
            new_value={"name": name, "price": price},
        )

    def deactivate_service(self, service_id):
        conn = _get_conn(self.db_path)
        conn.execute(
            "UPDATE services SET is_active = 0 WHERE id = ?", (service_id,)
        )
        conn.commit()
        conn.close()
        _list_services.clear_cache()
        _list_all_services.clear_cache()
        self._log_action("deactivate", "services", service_id)

    def activate_service(self, service_id):
        conn = _get_conn(self.db_path)
        conn.execute(
            "UPDATE services SET is_active = 1 WHERE id = ?", (service_id,)
        )
        conn.commit()
        conn.close()
        _list_services.clear_cache()
        _list_all_services.clear_cache()
        self._log_action("activate", "services", service_id)

    def delete_service(self, service_id):
        conn = _get_conn(self.db_path)
        count = conn.execute(
            "SELECT COUNT(*) FROM bookings WHERE service_id = ?", (service_id,)
        ).fetchone()[0]
        if count > 0:
            conn.close()
            return False, f"فيه {count} حجز مرتبط. استخدم التعطيل بدل الحذف."

        old = conn.execute(
            "SELECT name, price FROM services WHERE id = ?", (service_id,)
        ).fetchone()
        conn.execute("DELETE FROM services WHERE id = ?", (service_id,))
        conn.commit()
        conn.close()
        _list_services.clear_cache()
        _list_all_services.clear_cache()
        self._log_action(
            "delete", "services", service_id,
            old_value={"name": old[0], "price": old[1]} if old else None,
        )
        return True, "تم الحذف."

    def service_is_active(self, service_id):
        conn = _get_conn(self.db_path)
        row = conn.execute(
            "SELECT is_active FROM services WHERE id = ?", (service_id,)
        ).fetchone()
        conn.close()
        return bool(row[0]) if row else False

    # ============================================
    # CUSTOMERS
    # ============================================
    def list_customers(self):
        return _list_customers(self.db_path)

    def list_all_customers(self):
        return _list_all_customers(self.db_path)

    def get_customer(self, customer_id):
        conn = _get_conn(self.db_path)
        row = conn.execute(
            "SELECT id, name, phone, loyalty_points, is_active "
            "FROM customers WHERE id = ?",
            (customer_id,),
        ).fetchone()
        conn.close()
        return row

    def add_customer(self, name, phone):
        conn = _get_conn(self.db_path)
        cur = conn.execute(
            "INSERT INTO customers (name, phone) VALUES (?, ?)", (name, phone)
        )
        new_id = cur.lastrowid
        conn.commit()
        conn.close()
        _list_customers.clear_cache()
        _list_all_customers.clear_cache()
        self._log_action("create", "customers", new_id,
                         new_value={"name": name, "phone": phone})

    def update_customer(self, customer_id, name, phone):
        old = self.get_customer(customer_id)
        old_data = None
        if old:
            old_data = {"name": old[1], "phone": old[2]}

        conn = _get_conn(self.db_path)
        conn.execute(
            "UPDATE customers SET name = ?, phone = ? WHERE id = ?",
            (name, phone, customer_id),
        )
        conn.commit()
        conn.close()
        _list_customers.clear_cache()
        _list_all_customers.clear_cache()
        _list_bookings.clear_cache()
        self._log_action("update", "customers", customer_id,
                         old_value=old_data,
                         new_value={"name": name, "phone": phone})

    def deactivate_customer(self, customer_id):
        conn = _get_conn(self.db_path)
        conn.execute(
            "UPDATE customers SET is_active = 0 WHERE id = ?", (customer_id,)
        )
        conn.commit()
        conn.close()
        _list_customers.clear_cache()
        _list_all_customers.clear_cache()
        self._log_action("deactivate", "customers", customer_id)

    def activate_customer(self, customer_id):
        conn = _get_conn(self.db_path)
        conn.execute(
            "UPDATE customers SET is_active = 1 WHERE id = ?", (customer_id,)
        )
        conn.commit()
        conn.close()
        _list_customers.clear_cache()
        _list_all_customers.clear_cache()
        self._log_action("activate", "customers", customer_id)

    def delete_customer(self, customer_id):
        conn = _get_conn(self.db_path)
        count = conn.execute(
            "SELECT COUNT(*) FROM bookings WHERE customer_id = ?", (customer_id,)
        ).fetchone()[0]
        if count > 0:
            conn.close()
            return False, f"العميل عنده {count} حجز. استخدم التعطيل بدل الحذف."

        old = conn.execute(
            "SELECT name, phone FROM customers WHERE id = ?", (customer_id,)
        ).fetchone()
        conn.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
        conn.commit()
        conn.close()
        _list_customers.clear_cache()
        _list_all_customers.clear_cache()
        self._log_action("delete", "customers", customer_id,
                         old_value={"name": old[0], "phone": old[1]} if old else None)
        return True, "تم حذف العميل."

    def customer_is_active(self, customer_id):
        conn = _get_conn(self.db_path)
        row = conn.execute(
            "SELECT is_active FROM customers WHERE id = ?", (customer_id,)
        ).fetchone()
        conn.close()
        return bool(row[0]) if row else False

    # ============================================
    # BOOKINGS
    # ============================================
    def list_bookings(self):
        return _list_bookings(self.db_path)

    def get_booking(self, booking_id):
        conn = _get_conn(self.db_path)
        row = conn.execute("""
            SELECT bookings.id, bookings.customer_id, bookings.service_id,
                   customers.name, services.name, services.price,
                   bookings.barber, bookings.date, bookings.time,
                   bookings.extra_services, bookings.extra_services_total,
                   bookings.payment_method
            FROM bookings
            JOIN customers ON bookings.customer_id = customers.id
            JOIN services ON bookings.service_id = services.id
            WHERE bookings.id = ?
        """, (booking_id,)).fetchone()
        conn.close()
        return row

    def is_slot_taken(self, barber, date, time_, exclude_booking_id=None):
        conn = _get_conn(self.db_path)
        if exclude_booking_id is None:
            row = conn.execute(
                "SELECT COUNT(*) FROM bookings "
                "WHERE barber = ? AND date = ? AND time = ?",
                (barber, date, time_),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT COUNT(*) FROM bookings "
                "WHERE barber = ? AND date = ? AND time = ? AND id != ?",
                (barber, date, time_, exclude_booking_id),
            ).fetchone()
        conn.close()
        return row[0] > 0

    def add_booking(self, customer_id, service_id, barber, date, time_,
                    extra_service_ids=None, payment_method="cash"):
        created_at = datetime.now().isoformat(timespec="seconds")
        extra_ids = list(extra_service_ids or [])
        extra_total = 0.0

        if extra_ids:
            placeholders = ",".join("?" * len(extra_ids))
            conn = _get_conn(self.db_path)
            rows = conn.execute(
                f"SELECT id, price FROM services WHERE id IN ({placeholders})",
                extra_ids,
            ).fetchall()
            extra_total = sum(r[1] for r in rows)
            conn.close()

        conn = _get_conn(self.db_path)
        cur = conn.execute(
            "INSERT INTO bookings (customer_id, service_id, barber, date, time, "
            "created_at, extra_services, extra_services_total, payment_method) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (customer_id, service_id, barber, date, time_, created_at,
             json.dumps(extra_ids), extra_total, payment_method),
        )
        new_id = cur.lastrowid
        conn.execute(
            "UPDATE customers SET loyalty_points = loyalty_points + 1 "
            "WHERE id = ?",
            (customer_id,),
        )
        conn.commit()
        conn.close()
        _list_bookings.clear_cache()
        _list_customers.clear_cache()
        _list_all_customers.clear_cache()
        _revenue_report.clear_cache()
        _popular_services_report.clear_cache()

        self._log_action("create", "bookings", new_id, new_value={
            "customer_id": customer_id, "service_id": service_id,
            "barber": barber, "date": date, "time": time_,
            "extra_ids": extra_ids, "payment_method": payment_method,
        })

    def update_booking(self, booking_id, customer_id, service_id, barber,
                       date, time_, extra_service_ids=None,
                       payment_method="cash"):
        old = self.get_booking(booking_id)
        old_data = None
        if old:
            old_data = {
                "customer_id": old[1], "service_id": old[2],
                "barber": old[6], "date": old[7], "time": old[8],
                "payment_method": old[11],
            }

        extra_ids = list(extra_service_ids or [])
        extra_total = 0.0
        if extra_ids:
            placeholders = ",".join("?" * len(extra_ids))
            conn = _get_conn(self.db_path)
            rows = conn.execute(
                f"SELECT id, price FROM services WHERE id IN ({placeholders})",
                extra_ids,
            ).fetchall()
            extra_total = sum(r[1] for r in rows)
            conn.close()

        conn = _get_conn(self.db_path)
        conn.execute(
            "UPDATE bookings SET customer_id = ?, service_id = ?, barber = ?, "
            "date = ?, time = ?, extra_services = ?, extra_services_total = ?, "
            "payment_method = ? WHERE id = ?",
            (customer_id, service_id, barber, date, time_,
             json.dumps(extra_ids), extra_total, payment_method, booking_id),
        )
        conn.commit()
        conn.close()
        _list_bookings.clear_cache()
        _list_customers.clear_cache()
        _list_all_customers.clear_cache()
        _revenue_report.clear_cache()
        _popular_services_report.clear_cache()

        self._log_action("update", "bookings", booking_id,
                         old_value=old_data,
                         new_value={
                             "customer_id": customer_id, "service_id": service_id,
                             "barber": barber, "date": date, "time": time_,
                             "extra_ids": extra_ids, "payment_method": payment_method,
                         })

    def delete_booking(self, booking_id):
        conn = _get_conn(self.db_path)
        old = conn.execute(
            "SELECT customer_id, service_id, barber, date, time "
            "FROM bookings WHERE id = ?", (booking_id,)
        ).fetchone()
        conn.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
        conn.commit()
        conn.close()
        _list_bookings.clear_cache()
        _revenue_report.clear_cache()
        _popular_services_report.clear_cache()

        self._log_action(
            "delete", "bookings", booking_id,
            old_value={"customer_id": old[0], "service_id": old[1],
                       "barber": old[2], "date": old[3], "time": old[4]}
            if old else None,
        )

    def _bookings_between(self, start_time, end_time):
        conn = _get_conn(self.db_path)
        rows = conn.execute("""
            SELECT bookings.id, customers.name, services.name, services.price,
                   bookings.barber, bookings.date, bookings.time,
                   bookings.extra_services, bookings.extra_services_total,
                   bookings.payment_method
            FROM bookings
            JOIN customers ON bookings.customer_id = customers.id
            JOIN services ON bookings.service_id = services.id
            WHERE bookings.created_at BETWEEN ? AND ?
            ORDER BY bookings.created_at
        """, (start_time, end_time)).fetchall()
        conn.close()
        return rows

    # ============================================
    # REPORTS (Global)
    # ============================================
    def revenue_report(self):
        return _revenue_report(self.db_path)

    def popular_services_report(self):
        return _popular_services_report(self.db_path)

    def revenue_by_barber(self):
        conn = _get_conn(self.db_path)
        rows = conn.execute("""
            SELECT bookings.barber, COUNT(*) as cnt,
                   SUM(services.price + COALESCE(bookings.extra_services_total, 0)) as total
            FROM bookings JOIN services ON bookings.service_id = services.id
            GROUP BY bookings.barber
            ORDER BY total DESC
        """).fetchall()
        conn.close()
        return rows

    def busiest_weekdays(self):
        conn = _get_conn(self.db_path)
        rows = conn.execute("SELECT date FROM bookings").fetchall()
        conn.close()
        weekday_names = ["الإثنين", "الثلاثاء", "الأربعاء", "الخميس",
                          "الجمعة", "السبت", "الأحد"]
        counts = {name: 0 for name in weekday_names}
        for (date_str,) in rows:
            try:
                d = datetime.strptime(date_str, "%Y-%m-%d")
                counts[weekday_names[d.weekday()]] += 1
            except ValueError:
                continue
        return [(name, counts[name]) for name in weekday_names]

    def busiest_hours(self):
        conn = _get_conn(self.db_path)
        rows = conn.execute("SELECT time FROM bookings").fetchall()
        conn.close()
        counts = {}
        for (time_str,) in rows:
            hour = time_str.split(":")[0].zfill(2) if ":" in time_str else time_str
            counts[hour] = counts.get(hour, 0) + 1
        return sorted(counts.items())

    def revenue_over_time(self):
        conn = _get_conn(self.db_path)
        rows = conn.execute("""
            SELECT bookings.date,
                   SUM(services.price + COALESCE(bookings.extra_services_total, 0))
            FROM bookings JOIN services ON bookings.service_id = services.id
            GROUP BY bookings.date
            ORDER BY bookings.date
        """).fetchall()
        conn.close()
        return rows

    def inactive_customers(self, days_threshold=30):
        conn = _get_conn(self.db_path)
        rows = conn.execute("""
            SELECT customers.id, customers.name, customers.phone,
                   MAX(bookings.date) as last_visit
            FROM customers
            LEFT JOIN bookings ON bookings.customer_id = customers.id
            GROUP BY customers.id
        """).fetchall()
        conn.close()
        cutoff = datetime.now() - timedelta(days=days_threshold)
        result = []
        for cid, name, phone, last_visit in rows:
            if last_visit is None:
                result.append((cid, name, phone, "لم يحجز من قبل"))
                continue
            try:
                last_date = datetime.strptime(last_visit, "%Y-%m-%d")
                if last_date < cutoff:
                    result.append((cid, name, phone, last_visit))
            except ValueError:
                continue
        return result

    # ============================================
    # REPORTS — مع فلتر التاريخ
    # ============================================
    def revenue_report_range(self, date_from=None, date_to=None):
        clause, params = _date_clause(date_from, date_to)
        conn = _get_conn(self.db_path)
        query = f"""
            SELECT COALESCE(SUM(services.price + COALESCE(bookings.extra_services_total, 0)), 0),
                   COUNT(*)
            FROM bookings JOIN services ON bookings.service_id = services.id
            WHERE 1=1 {clause}
        """
        row = conn.execute(query, params).fetchone()
        conn.close()
        return {"total_revenue": row[0], "total_bookings": row[1]}

    def popular_services_report_range(self, date_from=None, date_to=None):
        clause, params = _date_clause(date_from, date_to)
        conn = _get_conn(self.db_path)
        query = f"""
            SELECT services.name, COUNT(*) as cnt,
                   SUM(services.price + COALESCE(bookings.extra_services_total, 0)) as total
            FROM bookings JOIN services ON bookings.service_id = services.id
            WHERE 1=1 {clause}
            GROUP BY services.name
            ORDER BY cnt DESC
        """
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return rows

    def revenue_by_barber_range(self, date_from=None, date_to=None):
        clause, params = _date_clause(date_from, date_to)
        conn = _get_conn(self.db_path)
        query = f"""
            SELECT bookings.barber, COUNT(*) as cnt,
                   SUM(services.price + COALESCE(bookings.extra_services_total, 0)) as total
            FROM bookings JOIN services ON bookings.service_id = services.id
            WHERE 1=1 {clause}
            GROUP BY bookings.barber
            ORDER BY total DESC
        """
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return rows

    def busiest_weekdays_range(self, date_from=None, date_to=None):
        clause, params = _date_clause(date_from, date_to)
        conn = _get_conn(self.db_path)
        query = f"SELECT date FROM bookings WHERE 1=1 {clause}"
        rows = conn.execute(query, params).fetchall()
        conn.close()

        weekday_names = ["الإثنين", "الثلاثاء", "الأربعاء", "الخميس",
                          "الجمعة", "السبت", "الأحد"]
        counts = {name: 0 for name in weekday_names}
        for (date_str,) in rows:
            try:
                d = datetime.strptime(date_str, "%Y-%m-%d")
                counts[weekday_names[d.weekday()]] += 1
            except ValueError:
                continue
        return [(name, counts[name]) for name in weekday_names]

    def busiest_hours_range(self, date_from=None, date_to=None):
        clause, params = _date_clause(date_from, date_to)
        conn = _get_conn(self.db_path)
        query = f"SELECT time FROM bookings WHERE 1=1 {clause}"
        rows = conn.execute(query, params).fetchall()
        conn.close()

        counts = {}
        for (time_str,) in rows:
            hour = time_str.split(":")[0].zfill(2) if ":" in time_str else time_str
            counts[hour] = counts.get(hour, 0) + 1
        return sorted(counts.items())

    def revenue_over_time_range(self, date_from=None, date_to=None):
        clause, params = _date_clause(date_from, date_to)
        conn = _get_conn(self.db_path)
        query = f"""
            SELECT bookings.date,
                   SUM(services.price + COALESCE(bookings.extra_services_total, 0))
            FROM bookings JOIN services ON bookings.service_id = services.id
            WHERE 1=1 {clause}
            GROUP BY bookings.date
            ORDER BY bookings.date
        """
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return rows

    def payment_breakdown_range(self, date_from=None, date_to=None):
        clause, params = _date_clause(date_from, date_to)
        conn = _get_conn(self.db_path)
        query = f"""
            SELECT COALESCE(bookings.payment_method, 'cash') as pm,
                   COUNT(*) as cnt,
                   SUM(services.price + COALESCE(bookings.extra_services_total, 0)) as total
            FROM bookings JOIN services ON bookings.service_id = services.id
            WHERE 1=1 {clause}
            GROUP BY pm
        """
        rows = conn.execute(query, params).fetchall()
        conn.close()

        result = {"cash": {"count": 0, "total": 0.0},
                  "card": {"count": 0, "total": 0.0},
                  "wallet": {"count": 0, "total": 0.0}}
        for pm, cnt, total in rows:
            key = pm if pm in result else "cash"
            result[key] = {"count": cnt, "total": total or 0.0}
        return result

    def count_customers_range(self, date_from=None, date_to=None):
        clause, params = _date_clause(date_from, date_to)
        conn = _get_conn(self.db_path)
        query = f"""
            SELECT COUNT(DISTINCT bookings.customer_id)
            FROM bookings
            WHERE 1=1 {clause}
        """
        row = conn.execute(query, params).fetchone()
        conn.close()
        return row[0] if row else 0

    def inactive_customers_range(self, date_from=None, date_to=None):
        conn = _get_conn(self.db_path)
        if date_from:
            query = """
                SELECT customers.id, customers.name, customers.phone,
                       MAX(bookings.date) as last_visit
                FROM customers
                LEFT JOIN bookings ON bookings.customer_id = customers.id
                WHERE customers.is_active = 1
                GROUP BY customers.id
                HAVING last_visit IS NULL OR last_visit < ?
                ORDER BY last_visit
            """
            rows = conn.execute(query, (date_from,)).fetchall()
        else:
            query = """
                SELECT customers.id, customers.name, customers.phone,
                       MAX(bookings.date) as last_visit
                FROM customers
                LEFT JOIN bookings ON bookings.customer_id = customers.id
                WHERE customers.is_active = 1
                GROUP BY customers.id
                ORDER BY last_visit
            """
            rows = conn.execute(query).fetchall()
        conn.close()

        result = []
        for cid, name, phone, last_visit in rows:
            result.append((cid, name, phone, last_visit or "لم يحجز من قبل"))
        return result

    # ============================================
    # BACKUP / RESTORE
    # ============================================
    def backup_now(self):
        os.makedirs(self.base_dir, exist_ok=True)
        backups_dir = os.path.join(self.base_dir, "backups")
        os.makedirs(backups_dir, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_path = os.path.join(backups_dir, f"barber_shop_{stamp}.db")
        shutil.copy2(self.db_path, backup_path)
        return backup_path

    def list_backups(self):
        backups_dir = os.path.join(self.base_dir, "backups")
        if not os.path.isdir(backups_dir):
            return []
        files = [f for f in os.listdir(backups_dir) if f.endswith(".db")]
        files.sort(reverse=True)
        return [os.path.join(backups_dir, f) for f in files]

    def restore_backup(self, backup_path):
        shutil.copy2(backup_path, self.db_path)
        _list_services.clear_cache()
        _list_all_services.clear_cache()
        _list_customers.clear_cache()
        _list_all_customers.clear_cache()
        _list_bookings.clear_cache()
        _revenue_report.clear_cache()
        _popular_services_report.clear_cache()
        _list_shifts.clear_cache()
        self._log_action("restore", None, None,
                         new_value={"backup_path": backup_path})

    # ============================================
    # SHIFTS
    # ============================================
    def get_open_shift(self):
        conn = _get_conn(self.db_path)
        row = conn.execute(
            "SELECT id, start_time FROM shifts WHERE status = 'open' "
            "ORDER BY id DESC LIMIT 1"
        ).fetchone()
        conn.close()
        return row

    def start_shift(self):
        if self.get_open_shift():
            return None
        conn = _get_conn(self.db_path)
        start_time = datetime.now().isoformat(timespec="seconds")
        cur = conn.execute(
            "INSERT INTO shifts (start_time, status) VALUES (?, 'open')",
            (start_time,),
        )
        new_id = cur.lastrowid
        conn.commit()
        conn.close()
        _list_shifts.clear_cache()
        self._log_action("start", "shifts", new_id,
                         new_value={"start_time": start_time})
        return start_time

    def end_shift(self):
        open_shift = self.get_open_shift()
        if not open_shift:
            return None
        shift_id, start_time = open_shift
        end_time = datetime.now().isoformat(timespec="seconds")
        bookings = self._bookings_between(start_time, end_time)

        cash_total = 0.0
        card_total = 0.0
        wallet_total = 0.0
        total_revenue = 0.0
        for b in bookings:
            amount = b[3] + (b[8] or 0)
            total_revenue += amount
            pm = b[9] or "cash"
            if pm == "cash":
                cash_total += amount
            elif pm == "card":
                card_total += amount
            elif pm == "wallet":
                wallet_total += amount

        total_bookings = len(bookings)

        conn = _get_conn(self.db_path)
        conn.execute(
            "UPDATE shifts SET end_time = ?, total_revenue = ?, "
            "total_bookings = ?, cash_total = ?, card_total = ?, "
            "wallet_total = ?, status = 'closed' WHERE id = ?",
            (end_time, total_revenue, total_bookings,
             cash_total, card_total, wallet_total, shift_id),
        )
        conn.commit()
        conn.close()
        _list_shifts.clear_cache()

        self._log_action("end", "shifts", shift_id, new_value={
            "total_revenue": total_revenue,
            "total_bookings": total_bookings,
            "cash_total": cash_total,
            "card_total": card_total,
            "wallet_total": wallet_total,
        })

        return {
            "id": shift_id,
            "start_time": start_time,
            "end_time": end_time,
            "total_revenue": total_revenue,
            "total_bookings": total_bookings,
            "cash_total": cash_total,
            "card_total": card_total,
            "wallet_total": wallet_total,
            "status": "closed",
            "bookings": bookings,
        }

    def list_shifts(self):
        return _list_shifts(self.db_path)

    def get_shift_details(self, shift_id):
        conn = _get_conn(self.db_path)
        shift = conn.execute(
            "SELECT id, start_time, end_time, total_revenue, "
            "total_bookings, cash_total, card_total, wallet_total, status "
            "FROM shifts WHERE id = ?",
            (shift_id,),
        ).fetchone()
        conn.close()
        if not shift:
            return None
        (sid, start_time, end_time, total_revenue, total_bookings,
         cash_total, card_total, wallet_total, status) = shift

        bookings = self._bookings_between(
            start_time,
            end_time or datetime.now().isoformat(timespec="seconds"),
        )

        if cash_total is None and card_total is None and wallet_total is None:
            cash_total = card_total = wallet_total = 0.0
            for b in bookings:
                amount = b[3] + (b[8] or 0)
                pm = b[9] or "cash"
                if pm == "cash":
                    cash_total += amount
                elif pm == "card":
                    card_total += amount
                elif pm == "wallet":
                    wallet_total += amount

        return {
            "id": sid,
            "start_time": start_time,
            "end_time": end_time,
            "total_revenue": total_revenue if total_revenue is not None
                             else sum((b[3] + (b[8] or 0)) for b in bookings),
            "total_bookings": total_bookings if total_bookings is not None
                              else len(bookings),
            "cash_total": cash_total or 0,
            "card_total": card_total or 0,
            "wallet_total": wallet_total or 0,
            "status": status,
            "bookings": bookings,
        }

    # ============================================
    # USERS / AUTH
    # ============================================
    def verify_login(self, username, password):
        conn = _get_conn(self.db_path)
        row = conn.execute(
            "SELECT id, username, password_hash, role, permissions "
            "FROM users WHERE username = ?",
            (username.strip(),),
        ).fetchone()
        conn.close()

        if not row:
            self._log_action("login_failed", "users", None,
                             new_value={"username": username})
            return None

        user_id, uname, password_hash, role, permissions_json = row

        if not self._verify_password(password, password_hash):
            self._log_action("login_failed", "users", user_id,
                             new_value={"username": username})
            return None

        if self._is_legacy_hash(password_hash):
            try:
                new_hash = self._hash_password(password)
                conn = _get_conn(self.db_path)
                conn.execute(
                    "UPDATE users SET password_hash = ? WHERE id = ?",
                    (new_hash, user_id),
                )
                conn.commit()
                conn.close()
                self._log_action("upgrade_hash", "users", user_id,
                                 new_value={"username": uname,
                                            "reason": "auto-upgrade from SHA256"})
            except Exception:
                pass

        user = User(user_id, uname, role, json.loads(permissions_json))
        self.set_current_user(user)
        self._log_action("login", "users", user_id,
                         new_value={"username": uname, "role": role})
        return user

    def list_users(self):
        conn = _get_conn(self.db_path)
        rows = conn.execute(
            "SELECT id, username, role, permissions FROM users "
            "ORDER BY username"
        ).fetchall()
        conn.close()
        return [User(uid, uname, role, json.loads(perms))
                for uid, uname, role, perms in rows]

    def add_user(self, username, password, role, permissions=None):
        conn = _get_conn(self.db_path)
        try:
            cur = conn.execute(
                "INSERT INTO users (username, password_hash, role, permissions) "
                "VALUES (?, ?, ?, ?)",
                (username.strip(), self._hash_password(password), role,
                 json.dumps(permissions or {})),
            )
            new_id = cur.lastrowid
            conn.commit()
            self._log_action("create", "users", new_id,
                             new_value={"username": username, "role": role,
                                        "permissions": permissions or {}})
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def update_user_permissions(self, user_id, permissions):
        conn = _get_conn(self.db_path)
        old = conn.execute(
            "SELECT permissions FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        conn.execute(
            "UPDATE users SET permissions = ? WHERE id = ?",
            (json.dumps(permissions), user_id),
        )
        conn.commit()
        conn.close()
        self._log_action("update", "users", user_id,
                         old_value={"permissions": json.loads(old[0])} if old else None,
                         new_value={"permissions": permissions})

    def update_username(self, user_id, new_username):
        new_username = new_username.strip()
        if not new_username:
            return False, "اسم المستخدم ماينفعش يكون فاضي."
        conn = _get_conn(self.db_path)
        try:
            old = conn.execute(
                "SELECT username FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            if not old:
                conn.close()
                return False, "المستخدم مش موجود."

            conn.execute(
                "UPDATE users SET username = ? WHERE id = ?",
                (new_username, user_id),
            )
            conn.commit()
            conn.close()

            self._log_action("update", "users", user_id,
                             old_value={"username": old[0]},
                             new_value={"username": new_username})
            return True, "تم تغيير اسم المستخدم."
        except sqlite3.IntegrityError:
            conn.close()
            return False, "الاسم ده مستخدم بالفعل."
        except Exception as e:
            conn.close()
            return False, f"خطأ: {e}"

    def update_user_password(self, user_id, new_password):
        if not new_password or len(new_password) < 4:
            return False, "كلمة المرور لازم 4 حروف على الأقل."
        conn = _get_conn(self.db_path)
        try:
            old = conn.execute(
                "SELECT username FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            if not old:
                conn.close()
                return False, "المستخدم مش موجود."

            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (self._hash_password(new_password), user_id),
            )
            conn.commit()
            conn.close()

            self._log_action("update_password", "users", user_id,
                             new_value={"username": old[0]})
            return True, "تم تغيير كلمة المرور."
        except Exception as e:
            conn.close()
            return False, f"خطأ: {e}"

    def count_admins(self):
        conn = _get_conn(self.db_path)
        count = conn.execute(
            "SELECT COUNT(*) FROM users WHERE role = 'admin'"
        ).fetchone()[0]
        conn.close()
        return count

    def delete_user(self, user_id):
        conn = _get_conn(self.db_path)
        row = conn.execute(
            "SELECT role, username FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if row and row[0] == "admin" and self.count_admins() <= 1:
            conn.close()
            return False
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        self._log_action("delete", "users", user_id,
                         old_value={"username": row[1], "role": row[0]}
                         if row else None)
        return True

    def logout_current_user(self):
        self._log_action("logout", "users",
                         getattr(self._current_user, "id", None))
        self._current_user = None