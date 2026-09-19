"""
Authentication / authorization helpers.

Two roles:
- "admin"    -> always has every permission (bypasses the permissions dict).
- "employee" -> only has whatever is explicitly turned on in `permissions`.

الصلاحيات مقسمة لمجموعات:
- الخدمات والأسعار
- العملاء
- الحجوزات
- الورديات
- التقارير
- الموظفين
- المخزون
- الإدارة والمالية
- متقدم
"""

# ============================================================
# قائمة الصلاحيات — مقسمة لمجموعات
# ============================================================
PERMISSIONS = [
    # ---------- الخدمات والأسعار ----------
    ("view_services", "عرض الأسعار والخدمات"),
    ("edit_services", "تعديل / إضافة / حذف الخدمات"),

    # ---------- العملاء ----------
    ("view_customers", "عرض العملاء"),
    ("edit_customers", "إضافة / حذف العملاء"),
    ("edit_customer_info", "تعديل بيانات العملاء (الاسم / التليفون)"),

    # ---------- الحجوزات ----------
    ("view_bookings", "عرض الحجوزات"),
    ("edit_bookings", "إضافة / حذف حجوزات وطباعة إيصالات"),

    # ---------- الورديات ----------
    ("view_shifts", "عرض الورديات"),
    ("manage_shifts", "بدء / إنهاء الورديات"),
    ("export_shifts", "تصدير الورديات Excel"),

    # ---------- التقارير ----------
    ("view_reports", "عرض التقارير"),

    # ---------- الموظفين ----------
    ("view_employees", "عرض الموظفين"),
    ("edit_employees", "إضافة / تعديل / حذف الموظفين"),
    ("manage_attendance", "تسجيل الحضور والانصراف"),
    ("manage_employee_transactions", "إدارة السلف والخصومات والمكافآت"),
    ("manage_salaries", "إدارة وحساب الرواتب"),

    # ---------- المخزون ----------
    ("view_inventory", "عرض المخزون"),
    ("edit_inventory", "إضافة / تعديل / حذف المنتجات"),
    ("manage_stock_in", "تسجيل الوارد (شراء منتجات)"),
    ("manage_stock_out", "تسجيل الصادر (استهلاك/بيع)"),
    ("view_inventory_reports", "عرض تقارير المخزون"),

    # ---------- الإدارة والمالية ----------
    ("view_management", "عرض لوحة الإدارة"),
    ("view_dashboard", "عرض Dashboard المالي"),
    ("manage_expenses", "إضافة / حذف المصاريف"),
    ("view_profit_loss", "عرض تقرير الأرباح والخسائر"),
    ("view_analytics", "عرض التحليلات والرسوم البيانية"),

    # ---------- متقدم ----------
    ("view_audit_log", "عرض سجل العمليات"),
    ("manage_users", "إدارة المستخدمين والصلاحيات"),
    ("manage_settings", "تعديل إعدادات البرنامج"),
    ("backup_restore", "النسخ الاحتياطي والاستعادة"),
]


# ============================================================
# قائمة الصلاحيات الجاهزة (Presets)
# ============================================================
PERMISSION_PRESETS = {
    "full_access": {
        "name": "🔓  وصول كامل",
        "description": "كل الصلاحيات ما عدا إدارة المستخدمين",
        "keys": [
            k for k, _ in PERMISSIONS
            if k != "manage_users"
        ],
    },

    "manager": {
        "name": "👔  مدير",
        "description": "إدارة كاملة للفرع بدون إعدادات النظام",
        "keys": [
            "view_services", "edit_services",
            "view_customers", "edit_customers", "edit_customer_info",
            "view_bookings", "edit_bookings",
            "view_shifts", "manage_shifts", "export_shifts",
            "view_reports",
            "view_employees", "edit_employees",
            "manage_attendance", "manage_employee_transactions",
            "manage_salaries",
            "view_inventory", "edit_inventory",
            "manage_stock_in", "manage_stock_out",
            "view_inventory_reports",
            "view_management", "view_dashboard",
            "manage_expenses", "view_profit_loss", "view_analytics",
        ],
    },

    "barber": {
        "name": "✂️  حلاق",
        "description": "الموظف العادي — حجوزات وعملاء فقط",
        "keys": [
            "view_services",
            "view_customers", "edit_customers",
            "view_bookings", "edit_bookings",
            "view_shifts",
        ],
    },

    "cashier": {
        "name": "💵  كاشير",
        "description": "الكاشير — حجوزات ومدفوعات وورديات",
        "keys": [
            "view_services",
            "view_customers", "edit_customers", "edit_customer_info",
            "view_bookings", "edit_bookings",
            "view_shifts", "manage_shifts",
            "view_inventory", "manage_stock_out",
        ],
    },

    "stock_manager": {
        "name": "📦  مسؤول مخزون",
        "description": "إدارة المخزون فقط",
        "keys": [
            "view_services",
            "view_inventory", "edit_inventory",
            "manage_stock_in", "manage_stock_out",
            "view_inventory_reports",
        ],
    },

    "hr": {
        "name": "👥  مسؤول موظفين",
        "description": "إدارة الموظفين والحضور والرواتب",
        "keys": [
            "view_employees", "edit_employees",
            "manage_attendance", "manage_employee_transactions",
            "manage_salaries",
            "view_reports",
        ],
    },

    "accountant": {
        "name": "🧾  محاسب",
        "description": "المالية والمصاريف والتقارير",
        "keys": [
            "view_management", "view_dashboard",
            "manage_expenses", "view_profit_loss", "view_analytics",
            "view_reports",
            "manage_salaries",
        ],
    },

    "viewer": {
        "name": "👁️  عارض فقط",
        "description": "عرض فقط بدون أي تعديل",
        "keys": [
            "view_services",
            "view_customers",
            "view_bookings",
            "view_shifts",
            "view_reports",
            "view_employees",
            "view_inventory",
            "view_management",
            "view_dashboard",
            "view_profit_loss",
            "view_analytics",
        ],
    },
}


# ============================================================
# قائمة المفاتيح
# ============================================================
PERMISSION_KEYS = [key for key, _ in PERMISSIONS]


# ============================================================
# خريطة الصلاحيات — للوصول السريع
# ============================================================
PERMISSION_LABELS = {key: label for key, label in PERMISSIONS}


# ============================================================
# دوال مساعدة
# ============================================================
def get_permissions_by_group():
    """يرجع الصلاحيات مقسمة لمجموعات."""
    groups = {
        "🛠️  الخدمات والأسعار": [
            "view_services", "edit_services",
        ],
        "👥  العملاء": [
            "view_customers", "edit_customers",
            "edit_customer_info",
        ],
        "📅  الحجوزات": [
            "view_bookings", "edit_bookings",
        ],
        "🕐  الورديات": [
            "view_shifts", "manage_shifts", "export_shifts",
        ],
        "📊  التقارير": [
            "view_reports",
        ],
        "👥  الموظفين": [
            "view_employees", "edit_employees",
            "manage_attendance",
            "manage_employee_transactions", "manage_salaries",
        ],
        "📦  المخزون": [
            "view_inventory", "edit_inventory",
            "manage_stock_in", "manage_stock_out",
            "view_inventory_reports",
        ],
        "💼  الإدارة والمالية": [
            "view_management", "view_dashboard",
            "manage_expenses", "view_profit_loss",
            "view_analytics",
        ],
        "⚙️  متقدم": [
            "view_audit_log", "manage_users",
            "manage_settings", "backup_restore",
        ],
    }
    return groups


def get_preset_keys(preset_key):
    """يرجع مفاتيح preset معين."""
    preset = PERMISSION_PRESETS.get(preset_key)
    if not preset:
        return []
    return preset.get("keys", [])


# ============================================================
# User Class
# ============================================================
class User:
    def __init__(self, user_id, username, role, permissions):
        self.id = user_id
        self.username = username
        self.role = role  # "admin" or "employee"
        self.permissions = permissions or {}

    @property
    def is_admin(self):
        return self.role == "admin"

    def has_permission(self, key):
        if self.is_admin:
            return True
        return bool(self.permissions.get(key, False))

    def count_active_permissions(self):
        """يرجع عدد الصلاحيات النشطة."""
        if self.is_admin:
            return len(PERMISSIONS)
        return sum(1 for v in self.permissions.values() if v)

    def get_role_display(self):
        """يرجع الدور بالعربي."""
        if self.is_admin:
            return "👑  سوبر أدمن"
        return "👤  موظف"
