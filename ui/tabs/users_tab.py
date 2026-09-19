"""
Users Tab — PySide6 كامل لإدارة المستخدمين والصلاحيات.
+ Light/Dark theme support (reads from Theme).
+ Permission Presets (قوالب جاهزة)
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QDialog, QAbstractItemView,
    QLineEdit, QCheckBox, QComboBox, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QGuiApplication

from core.auth import (
    PERMISSIONS,
    PERMISSION_PRESETS,
    PERMISSION_KEYS,
    get_preset_keys,
)
from utils.theme import Theme


# ============================================================
# Shared dialog stylesheet (dynamic)
# ============================================================
def _dialog_qss():
    return f"""
    QDialog {{
        background-color: {Theme.color('bg')};
    }}
    QLabel {{
        color: {Theme.color('text')};
        background: transparent;
        font-size: 11pt;
    }}
    QLabel#dialogTitle {{
        color: {Theme.color('primary')};
        font-size: 16pt;
        font-weight: bold;
        padding: 6px;
        background: transparent;
    }}
    QLabel#sectionTitle {{
        color: {Theme.color('primary')};
        font-size: 11.5pt;
        font-weight: bold;
        padding: 6px 2px;
        background: transparent;
    }}
    QLabel#hintBox {{
        color: {Theme.color('text_muted')};
        font-size: 10pt;
        background: {Theme.color('bg')};
        padding: 8px;
        border-radius: 6px;
    }}
    QLabel#adminHint {{
        color: {Theme.color('warning')};
        font-size: 10.5pt;
        font-weight: bold;
        background: {Theme.color('bg')};
        padding: 10px;
        border-radius: 6px;
        border: 1px solid {Theme.color('warning')};
    }}
    QLineEdit {{
        background-color: {Theme.color('surface')};
        color: {Theme.color('text')};
        border: 1px solid {Theme.color('border_strong')};
        border-radius: 6px;
        padding: 6px 12px;
        font-size: 11pt;
    }}
    QLineEdit:focus {{
        border: 2px solid {Theme.color('primary')};
    }}
    QComboBox {{
        background-color: {Theme.color('surface')};
        color: {Theme.color('text')};
        border: 1px solid {Theme.color('border_strong')};
        border-radius: 6px;
        padding: 6px 12px;
        font-size: 11pt;
        min-height: 22px;
    }}
    QComboBox:focus {{
        border: 2px solid {Theme.color('primary')};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 26px;
    }}
    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 7px solid {Theme.color('text_muted')};
        margin-right: 10px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {Theme.color('surface')};
        color: {Theme.color('text')};
        border: 1px solid {Theme.color('border_strong')};
        selection-background-color: {Theme.color('primary')};
        selection-color: #ffffff;
        padding: 6px;
        outline: none;
    }}
    QCheckBox {{
        color: {Theme.color('text')};
        spacing: 8px;
        font-size: 11pt;
        padding: 4px;
        background: transparent;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 2px solid {Theme.color('border_strong')};
        background-color: {Theme.color('surface')};
    }}
    QCheckBox::indicator:hover {{
        border-color: {Theme.color('primary')};
    }}
    QCheckBox::indicator:checked {{
        background-color: {Theme.color('primary')};
        border-color: {Theme.color('primary')};
    }}
    QFrame#card {{
        background-color: {Theme.color('surface')};
        border: 1px solid {Theme.color('border')};
        border-radius: 10px;
    }}
    QFrame#separator {{
        background-color: {Theme.color('border')};
        border: none;
    }}
    QScrollArea {{
        background: transparent;
        border: none;
    }}
    QScrollBar:vertical {{
        background: {Theme.color('bg')};
        width: 10px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical {{
        background: {Theme.color('border_strong')};
        border-radius: 5px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {Theme.color('primary')};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    """


# ============================================================
# Add / Edit User Dialog
# ============================================================
class UserDialog(QDialog):
    """حوار إضافة أو تعديل مستخدم."""

    def __init__(self, parent=None, user_id=None, username="",
                 role="employee", permissions=None):
        super().__init__(parent)
        self.user_id = user_id
        self.result_data = None

        self.setWindowTitle("تعديل مستخدم" if user_id else "إضافة مستخدم جديد")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet(_dialog_qss())

        self.setMinimumSize(620, 700)
        self.resize(720, 780)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(12)

        title = QLabel(
            "✏️  تعديل المستخدم" if user_id else "➕  إضافة مستخدم جديد"
        )
        title.setObjectName("dialogTitle")
        title.setAlignment(Qt.AlignCenter)
        root.addWidget(title)

        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFixedHeight(1)
        root.addWidget(sep)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        content.setLayoutDirection(Qt.RightToLeft)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(2, 2, 10, 2)
        content_layout.setSpacing(14)

        # ============================================
        # Card 1: البيانات الأساسية
        # ============================================
        card1 = QFrame()
        card1.setObjectName("card")
        c1_layout = QVBoxLayout(card1)
        c1_layout.setContentsMargins(16, 14, 16, 14)
        c1_layout.setSpacing(10)

        c1_title = QLabel("📋  البيانات الأساسية")
        c1_title.setObjectName("sectionTitle")
        c1_layout.addWidget(c1_title)

        c1_layout.addWidget(QLabel("اسم المستخدم *"))
        self.username_entry = QLineEdit(username)
        self.username_entry.setMinimumHeight(44)
        self.username_entry.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.username_entry.setPlaceholderText("مثال: ahmed")
        c1_layout.addWidget(self.username_entry)

        if user_id is None:
            c1_layout.addWidget(QLabel("كلمة المرور *"))
            self.password_entry = QLineEdit()
            self.password_entry.setEchoMode(QLineEdit.Password)
            self.password_entry.setMinimumHeight(44)
            self.password_entry.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.password_entry.setPlaceholderText("4 حروف على الأقل")
            c1_layout.addWidget(self.password_entry)

            c1_layout.addWidget(QLabel("تأكيد كلمة المرور *"))
            self.confirm_entry = QLineEdit()
            self.confirm_entry.setEchoMode(QLineEdit.Password)
            self.confirm_entry.setMinimumHeight(44)
            self.confirm_entry.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.confirm_entry.setPlaceholderText("أعد كتابة كلمة المرور")
            c1_layout.addWidget(self.confirm_entry)
        else:
            self.password_entry = None
            self.confirm_entry = None

            hint = QLabel(
                "ℹ️  لتغيير كلمة المرور، استخدم زر «🔑 تغيير كلمة المرور» "
                "من قائمة المستخدمين."
            )
            hint.setObjectName("hintBox")
            hint.setWordWrap(True)
            c1_layout.addWidget(hint)

        c1_layout.addWidget(QLabel("الدور *"))
        self.role_combo = QComboBox()
        self.role_combo.setMinimumHeight(44)
        self.role_combo.setLayoutDirection(Qt.RightToLeft)
        self.role_combo.addItem("👤  موظف", "employee")
        self.role_combo.addItem("👑  سوبر أدمن", "admin")
        for i in range(self.role_combo.count()):
            if self.role_combo.itemData(i) == role:
                self.role_combo.setCurrentIndex(i)
                break
        c1_layout.addWidget(self.role_combo)

        content_layout.addWidget(card1)

        # ============================================
        # Card 2: الصلاحيات
        # ============================================
        card2 = QFrame()
        card2.setObjectName("card")
        c2_layout = QVBoxLayout(card2)
        c2_layout.setContentsMargins(16, 14, 16, 14)
        c2_layout.setSpacing(10)

        c2_title = QLabel("⚙️  الصلاحيات")
        c2_title.setObjectName("sectionTitle")
        c2_layout.addWidget(c2_title)

        self.admin_hint = QLabel(
            "👑  السوبر أدمن معاه كل الصلاحيات تلقائيًا — مش محتاج تحدد حاجة."
        )
        self.admin_hint.setObjectName("adminHint")
        self.admin_hint.setWordWrap(True)
        c2_layout.addWidget(self.admin_hint)

        # ============================================
        # ✅ Presets — قوالب جاهزة
        # ============================================
        preset_label = QLabel("🎯  قالب جاهز (تطبيق سريع):")
        preset_label.setStyleSheet(
            f"color: {Theme.color('text')}; font-size: 11pt; "
            f"font-weight: bold; background: transparent; padding: 4px;"
        )
        c2_layout.addWidget(preset_label)

        self.preset_combo = QComboBox()
        self.preset_combo.setMinimumHeight(42)
        self.preset_combo.setLayoutDirection(Qt.RightToLeft)
        self.preset_combo.addItem("— اختر قالب —", None)
        for pk, pd in PERMISSION_PRESETS.items():
            self.preset_combo.addItem(
                f"{pd['name']}   —   {pd['description']}",
                pk
            )
        self.preset_combo.currentIndexChanged.connect(self._apply_preset)
        c2_layout.addWidget(self.preset_combo)

        # فاصل
        sep2 = QFrame()
        sep2.setObjectName("separator")
        sep2.setFixedHeight(1)
        c2_layout.addWidget(sep2)

        # ============================================
        # أزرار سريعة
        # ============================================
        quick_row = QHBoxLayout()
        quick_row.setSpacing(8)

        select_all_btn = QPushButton("✅  تحديد الكل")
        select_all_btn.setMinimumHeight(38)
        select_all_btn.setCursor(Qt.PointingHandCursor)
        select_all_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('success')}; "
            f"color: white; border: none; border-radius: 6px; "
            f"padding: 6px 14px; font-weight: bold; font-size: 10.5pt; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('success_hover')}; }}"
        )
        select_all_btn.clicked.connect(lambda: self._set_all(True))
        quick_row.addWidget(select_all_btn)

        clear_all_btn = QPushButton("⬜  إلغاء الكل")
        clear_all_btn.setMinimumHeight(38)
        clear_all_btn.setCursor(Qt.PointingHandCursor)
        clear_all_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('text_dim')}; "
            f"color: white; border: none; border-radius: 6px; "
            f"padding: 6px 14px; font-weight: bold; font-size: 10.5pt; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('border_strong')}; }}"
        )
        clear_all_btn.clicked.connect(lambda: self._set_all(False))
        quick_row.addWidget(clear_all_btn)

        quick_row.addStretch()
        c2_layout.addLayout(quick_row)

        # ============================================
        # الـ checkboxes
        # ============================================
        self.perm_checks = {}

        # قسم المجموعات (نفس ترتيب PERMISSIONS)
        groups = [
            ("🛠️  الخدمات والأسعار", [
                "view_services", "edit_services",
            ]),
            ("👥  العملاء", [
                "view_customers", "edit_customers", "edit_customer_info",
            ]),
            ("📅  الحجوزات", [
                "view_bookings", "edit_bookings",
            ]),
            ("🕐  الورديات", [
                "view_shifts", "manage_shifts", "export_shifts",
            ]),
            ("📊  التقارير", [
                "view_reports",
            ]),
            ("👥  الموظفين", [
                "view_employees", "edit_employees",
                "manage_attendance",
                "manage_employee_transactions", "manage_salaries",
            ]),
            ("📦  المخزون", [
                "view_inventory", "edit_inventory",
                "manage_stock_in", "manage_stock_out",
                "view_inventory_reports",
            ]),
            ("💼  الإدارة والمالية", [
                "view_management", "view_dashboard",
                "manage_expenses", "view_profit_loss",
                "view_analytics",
            ]),
            ("⚙️  متقدم", [
                "view_audit_log", "manage_users",
                "manage_settings", "backup_restore",
            ]),
        ]

        # خريطة لسرعة الوصول
        perm_map = {k: label for k, label in PERMISSIONS}

        for group_name, keys in groups:
            # عنوان المجموعة
            grp_label = QLabel(group_name)
            grp_label.setStyleSheet(
                f"color: {Theme.color('primary')}; font-size: 11pt; "
                f"font-weight: bold; padding: 8px 4px 4px 4px; "
                f"background: transparent;"
            )
            c2_layout.addWidget(grp_label)

            for key in keys:
                label = perm_map.get(key, key)
                cb = QCheckBox(label)
                cb.setMinimumHeight(30)
                cb.setChecked(bool((permissions or {}).get(key, False)))
                c2_layout.addWidget(cb)
                self.perm_checks[key] = cb

        content_layout.addWidget(card2)
        content_layout.addStretch(1)

        scroll.setWidget(content)
        root.addWidget(scroll, stretch=1)

        # Footer
        footer = QHBoxLayout()
        footer.setSpacing(10)

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setFixedHeight(46)
        cancel_btn.setMinimumWidth(140)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('surface_alt')}; "
            f"color: {Theme.color('text')}; border: none; border-radius: 7px; "
            f"font-weight: bold; font-size: 11.5pt; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('border_strong')}; }}"
        )
        cancel_btn.clicked.connect(self.reject)
        footer.addWidget(cancel_btn, 1)

        save_btn = QPushButton(
            "✓  حفظ التعديل" if user_id else "✓  إضافة المستخدم"
        )
        save_btn.setFixedHeight(46)
        save_btn.setMinimumWidth(220)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('success')}; "
            f"color: white; border: none; border-radius: 7px; "
            f"font-weight: bold; font-size: 11.5pt; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('success_hover')}; }}"
        )
        save_btn.clicked.connect(self._save)
        footer.addWidget(save_btn, 1)

        root.addLayout(footer)

        self.role_combo.currentIndexChanged.connect(self._on_role_changed)
        self._on_role_changed()

        QTimer.singleShot(30, self._center)

    # ============================================
    # Presets
    # ============================================
    def _apply_preset(self, idx):
        """يطبق قالب صلاحيات جاهز."""
        preset_key = self.preset_combo.currentData()
        if not preset_key:
            return

        preset = PERMISSION_PRESETS.get(preset_key)
        if not preset:
            return

        preset_keys = set(preset.get("keys", []))

        # طبّق على الـ checkboxes
        for key, cb in self.perm_checks.items():
            cb.setChecked(key in preset_keys)

        # رسالة تأكيد
        count = len(preset_keys)
        QMessageBox.information(
            self, "تم التطبيق",
            f"✅ تم تطبيق القالب: {preset['name']}\n\n"
            f"عدد الصلاحيات: {count}"
        )

    # ============================================
    # Role change
    # ============================================
    def _on_role_changed(self):
        role = self.role_combo.currentData()
        is_admin = (role == "admin")

        self.admin_hint.setVisible(is_admin)
        for cb in self.perm_checks.values():
            cb.setEnabled(not is_admin)
            if is_admin:
                cb.setChecked(True)

    # ============================================
    # Quick select
    # ============================================
    def _set_all(self, value):
        if self.role_combo.currentData() == "admin":
            return
        for cb in self.perm_checks.values():
            cb.setChecked(value)

    # ============================================
    # Save
    # ============================================
    def _save(self):
        username = self.username_entry.text().strip()
        if not username:
            QMessageBox.warning(self, "خطأ", "اكتب اسم المستخدم")
            return

        role = self.role_combo.currentData()

        password = None
        if self.user_id is None:
            password = self.password_entry.text()
            confirm = self.confirm_entry.text()

            if not password:
                QMessageBox.warning(self, "خطأ", "اكتب كلمة المرور")
                return
            if len(password) < 4:
                QMessageBox.warning(
                    self, "خطأ", "كلمة المرور لازم 4 حروف على الأقل"
                )
                return
            if password != confirm:
                QMessageBox.warning(self, "خطأ", "كلمتا المرور غير متطابقتين")
                return

        permissions = {}
        if role != "admin":
            for key, cb in self.perm_checks.items():
                permissions[key] = cb.isChecked()

        self.result_data = {
            "username": username,
            "password": password,
            "role": role,
            "permissions": permissions,
        }
        self.accept()

    def _center(self):
        try:
            screen = QGuiApplication.primaryScreen()
            if screen is None:
                return
            geo = screen.availableGeometry()
            w = min(self.width(), geo.width() - 40)
            h = min(self.height(), geo.height() - 40)
            self.resize(w, h)
            x = geo.x() + (geo.width() - w) // 2
            y = geo.y() + (geo.height() - h) // 2
            self.move(max(x, 0), max(y, 0))
        except Exception:
            pass


# ============================================================
# Change Password Dialog
# ============================================================
class ChangePasswordDialog(QDialog):
    def __init__(self, parent=None, username=""):
        super().__init__(parent)
        self.result_data = None

        self.setWindowTitle(f"تغيير كلمة المرور — {username}")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet(_dialog_qss())
        self.setFixedSize(460, 380)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)

        title = QLabel("🔑  تغيير كلمة المرور")
        title.setObjectName("dialogTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        info = QLabel(f"المستخدم: <b>{username}</b>")
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet(
            f"font-size: 12pt; padding: 6px; "
            f"color: {Theme.color('text')}; background: transparent;"
        )
        layout.addWidget(info)

        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        layout.addWidget(QLabel("كلمة المرور الجديدة:"))
        self.pass1 = QLineEdit()
        self.pass1.setEchoMode(QLineEdit.Password)
        self.pass1.setMinimumHeight(44)
        self.pass1.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.pass1.setPlaceholderText("4 حروف على الأقل")
        layout.addWidget(self.pass1)

        layout.addWidget(QLabel("تأكيد كلمة المرور:"))
        self.pass2 = QLineEdit()
        self.pass2.setEchoMode(QLineEdit.Password)
        self.pass2.setMinimumHeight(44)
        self.pass2.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.pass2.setPlaceholderText("أعد كتابة كلمة المرور")
        layout.addWidget(self.pass2)

        layout.addStretch(1)

        btns = QHBoxLayout()
        btns.setSpacing(10)

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setFixedHeight(44)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('surface_alt')}; "
            f"color: {Theme.color('text')}; border: none; border-radius: 7px; "
            f"font-weight: bold; font-size: 11pt; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('border_strong')}; }}"
        )
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(cancel_btn)

        save_btn = QPushButton("✓  حفظ")
        save_btn.setFixedHeight(44)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('success')}; "
            f"color: white; border: none; border-radius: 7px; "
            f"font-weight: bold; font-size: 11pt; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('success_hover')}; }}"
        )
        save_btn.clicked.connect(self._save)
        btns.addWidget(save_btn)

        layout.addLayout(btns)

        QTimer.singleShot(30, self._center)

    def _save(self):
        p1 = self.pass1.text()
        p2 = self.pass2.text()

        if not p1:
            QMessageBox.warning(self, "خطأ", "اكتب كلمة المرور الجديدة")
            return
        if len(p1) < 4:
            QMessageBox.warning(self, "خطأ", "كلمة المرور لازم 4 حروف على الأقل")
            return
        if p1 != p2:
            QMessageBox.warning(self, "خطأ", "كلمتا المرور غير متطابقتين")
            return

        self.result_data = {"password": p1}
        self.accept()

    def _center(self):
        try:
            screen = QGuiApplication.primaryScreen()
            if screen is None:
                return
            geo = screen.availableGeometry()
            x = geo.x() + (geo.width() - self.width()) // 2
            y = geo.y() + (geo.height() - self.height()) // 2
            self.move(max(x, 0), max(y, 0))
        except Exception:
            pass


# ============================================================
# Users Tab
# ============================================================
class UsersTab(QWidget):
    """تاب إدارة المستخدمين."""

    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.current_user = user

        self._build_ui()
        self.refresh()

    # ============================================
    # UI
    # ============================================
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("👤  إدارة المستخدمين")
        title.setStyleSheet(
            f"font-size: 22px; font-weight: bold; "
            f"color: {Theme.color('primary')}; padding: 4px; "
            f"background: transparent;"
        )
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        actions = QHBoxLayout()
        actions.setSpacing(8)

        add_btn = QPushButton("➕  إضافة مستخدم")
        add_btn.setMinimumHeight(42)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('success')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"padding: 10px 20px; font-weight: bold; font-size: 12px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('success_hover')}; }}"
        )
        add_btn.clicked.connect(self._add_user)
        actions.addWidget(add_btn)

        edit_btn = QPushButton("✏️  تعديل الصلاحيات")
        edit_btn.setMinimumHeight(42)
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('primary')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"padding: 10px 20px; font-weight: bold; font-size: 12px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('primary_hover')}; }}"
        )
        edit_btn.clicked.connect(self._edit_user)
        actions.addWidget(edit_btn)

        rename_btn = QPushButton("📝  تعديل الاسم")
        rename_btn.setMinimumHeight(42)
        rename_btn.setCursor(Qt.PointingHandCursor)
        rename_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('warning')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"padding: 10px 20px; font-weight: bold; font-size: 12px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('warning_hover')}; }}"
        )
        rename_btn.clicked.connect(self._rename_user)
        actions.addWidget(rename_btn)

        pass_btn = QPushButton("🔑  تغيير كلمة المرور")
        pass_btn.setMinimumHeight(42)
        pass_btn.setCursor(Qt.PointingHandCursor)
        pass_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('info')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"padding: 10px 20px; font-weight: bold; font-size: 12px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('info_hover')}; }}"
        )
        pass_btn.clicked.connect(self._change_password)
        actions.addWidget(pass_btn)

        delete_btn = QPushButton("🗑️  حذف")
        delete_btn.setMinimumHeight(42)
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('danger')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"padding: 10px 20px; font-weight: bold; font-size: 12px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('danger_hover')}; }}"
        )
        delete_btn.clicked.connect(self._delete_user)
        actions.addWidget(delete_btn)

        actions.addStretch()
        layout.addLayout(actions)

        # Table
        table_card = QFrame()
        table_card.setStyleSheet(
            f"QFrame {{ background-color: {Theme.color('surface')}; "
            f"border: 1px solid {Theme.color('border')}; border-radius: 12px; }}"
        )
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(16, 16, 16, 16)
        table_layout.setSpacing(10)

        tbl_title = QLabel("📋  قائمة المستخدمين")
        tbl_title.setStyleSheet(
            f"font-size: 14px; font-weight: bold; "
            f"color: {Theme.color('primary')}; background: transparent; "
            f"padding: 0 4px;"
        )
        tbl_title.setAlignment(Qt.AlignRight)
        table_layout.addWidget(tbl_title)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["#", "اسم المستخدم", "الدور", "الصلاحيات", "ملاحظات"]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setMinimumHeight(380)
        self.table.setLayoutDirection(Qt.RightToLeft)

        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Fixed)
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        h.setSectionResizeMode(2, QHeaderView.Fixed)
        h.setSectionResizeMode(3, QHeaderView.Fixed)
        h.setSectionResizeMode(4, QHeaderView.Stretch)

        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(2, 160)
        self.table.setColumnWidth(3, 140)

        self.table.doubleClicked.connect(self._edit_user)

        table_layout.addWidget(self.table)
        layout.addWidget(table_card)

    # ============================================
    # Refresh
    # ============================================
    def refresh(self):
        try:
            users = self.db.list_users()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل المستخدمين:\n{e}")
            return

        self.table.blockSignals(True)
        self.table.setRowCount(len(users))

        gold = QColor(Theme.color("gold"))
        blue = QColor(Theme.color("primary"))
        gray = QColor(Theme.color("text_muted"))
        text_color = QColor(Theme.color("text"))
        orange = QColor(Theme.color("warning"))

        for row, u in enumerate(users):
            item_id = QTableWidgetItem(str(u.id))
            item_id.setTextAlignment(Qt.AlignCenter)
            item_id.setData(Qt.UserRole, u.id)
            item_id.setData(Qt.UserRole + 1, u.role)
            item_id.setData(Qt.UserRole + 2, u.username)
            item_id.setForeground(text_color)
            self.table.setItem(row, 0, item_id)

            name_text = u.username
            if u.id == self.current_user.id:
                name_text += "  (أنت)"
            item_name = QTableWidgetItem(name_text)
            item_name.setTextAlignment(Qt.AlignCenter)
            if u.id == self.current_user.id:
                item_name.setForeground(gold)
                f = QFont()
                f.setBold(True)
                item_name.setFont(f)
            else:
                item_name.setForeground(text_color)
            self.table.setItem(row, 1, item_name)

            if u.is_admin:
                item_role = QTableWidgetItem("👑  سوبر أدمن")
                item_role.setForeground(gold)
            else:
                item_role = QTableWidgetItem("👤  موظف")
                item_role.setForeground(blue)
            item_role.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, item_role)

            if u.is_admin:
                perm_text = "كل الصلاحيات"
                perm_color = gold
            else:
                active = sum(1 for v in u.permissions.values() if v)
                total = len(PERMISSIONS)
                perm_text = f"{active} / {total}"
                perm_color = blue if active > 0 else gray
            item_perm = QTableWidgetItem(perm_text)
            item_perm.setTextAlignment(Qt.AlignCenter)
            item_perm.setForeground(perm_color)
            self.table.setItem(row, 3, item_perm)

            note = ""
            if u.id == self.current_user.id:
                note = "أنت"
            elif u.is_admin:
                note = "—"
            elif sum(1 for v in u.permissions.values() if v) == 0:
                note = "⚠️  بدون صلاحيات"
            item_note = QTableWidgetItem(note)
            item_note.setTextAlignment(Qt.AlignCenter)
            if "⚠️" in note:
                item_note.setForeground(orange)
            else:
                item_note.setForeground(text_color)
            self.table.setItem(row, 4, item_note)

        self.table.blockSignals(False)

    # ============================================
    # Helpers
    # ============================================
    def _get_selected_user(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        row_idx = rows[0].row()
        item = self.table.item(row_idx, 0)
        if item is None:
            return None
        return {
            "id": item.data(Qt.UserRole),
            "role": item.data(Qt.UserRole + 1),
            "username": item.data(Qt.UserRole + 2),
        }

    # ============================================
    # Add User
    # ============================================
    def _add_user(self):
        dlg = UserDialog(self, user_id=None)
        if dlg.exec() != QDialog.Accepted or not dlg.result_data:
            return

        data = dlg.result_data
        ok = self.db.add_user(
            data["username"], data["password"],
            data["role"], data["permissions"],
        )

        if not ok:
            QMessageBox.warning(
                self, "خطأ",
                "اسم المستخدم ده موجود بالفعل. اختار اسم تاني."
            )
            return

        QMessageBox.information(self, "تم", "تم إضافة المستخدم بنجاح.")
        self.refresh()

    # ============================================
    # Edit User
    # ============================================
    def _edit_user(self):
        sel = self._get_selected_user()
        if not sel:
            QMessageBox.warning(self, "خطأ", "اختار مستخدم من القائمة الأول")
            return

        try:
            users = self.db.list_users()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل البيانات:\n{e}")
            return

        target = None
        for u in users:
            if u.id == sel["id"]:
                target = u
                break

        if target is None:
            QMessageBox.warning(self, "خطأ", "المستخدم مش موجود.")
            return

        dlg = UserDialog(
            self, user_id=target.id,
            username=target.username,
            role=target.role,
            permissions=target.permissions,
        )
        if dlg.exec() != QDialog.Accepted or not dlg.result_data:
            return

        data = dlg.result_data

        if data["username"] != target.username:
            ok, msg = self.db.update_username(target.id, data["username"])
            if not ok:
                QMessageBox.warning(self, "خطأ", msg)

        try:
            import sqlite3
            conn = sqlite3.connect(self.db.db_path)
            conn.execute(
                "UPDATE users SET role = ? WHERE id = ?",
                (data["role"], target.id),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تعديل الدور:\n{e}")
            return

        self.db.update_user_permissions(target.id, data["permissions"])

        QMessageBox.information(self, "تم", "تم تعديل بيانات المستخدم.")
        self.refresh()

    # ============================================
    # Rename User
    # ============================================
    def _rename_user(self):
        sel = self._get_selected_user()
        if not sel:
            QMessageBox.warning(self, "خطأ", "اختار مستخدم من القائمة الأول")
            return

        old_name = sel["username"]

        dlg = QDialog(self)
        dlg.setWindowTitle("تعديل اسم المستخدم")
        dlg.setLayoutDirection(Qt.RightToLeft)
        dlg.setStyleSheet(_dialog_qss())
        dlg.setFixedSize(460, 260)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)

        title = QLabel("📝  تعديل اسم المستخدم")
        title.setObjectName("dialogTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        layout.addWidget(QLabel("الاسم الجديد:"))
        entry = QLineEdit(old_name)
        entry.setMinimumHeight(44)
        entry.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(entry)

        layout.addStretch(1)

        btns = QHBoxLayout()
        btns.setSpacing(10)

        cancel = QPushButton("إلغاء")
        cancel.setFixedHeight(42)
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('surface_alt')}; "
            f"color: {Theme.color('text')}; border: none; border-radius: 7px; "
            f"font-weight: bold; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('border_strong')}; }}"
        )
        cancel.clicked.connect(dlg.reject)
        btns.addWidget(cancel)

        save = QPushButton("✓  حفظ")
        save.setFixedHeight(42)
        save.setCursor(Qt.PointingHandCursor)
        save.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('success')}; "
            f"color: white; border: none; border-radius: 7px; "
            f"font-weight: bold; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('success_hover')}; }}"
        )

        def do_save():
            new_name = entry.text().strip()
            if not new_name:
                QMessageBox.warning(dlg, "خطأ", "اكتب الاسم الجديد")
                return
            ok, msg = self.db.update_username(sel["id"], new_name)
            if not ok:
                QMessageBox.warning(dlg, "خطأ", msg)
                return
            QMessageBox.information(dlg, "تم", msg)
            dlg.accept()

        save.clicked.connect(do_save)
        btns.addWidget(save)

        layout.addLayout(btns)

        if dlg.exec() == QDialog.Accepted:
            self.refresh()

    # ============================================
    # Change Password
    # ============================================
    def _change_password(self):
        sel = self._get_selected_user()
        if not sel:
            QMessageBox.warning(self, "خطأ", "اختار مستخدم من القائمة الأول")
            return

        dlg = ChangePasswordDialog(self, username=sel["username"])
        if dlg.exec() != QDialog.Accepted or not dlg.result_data:
            return

        ok, msg = self.db.update_user_password(
            sel["id"], dlg.result_data["password"]
        )
        if not ok:
            QMessageBox.warning(self, "خطأ", msg)
            return

        QMessageBox.information(self, "تم", msg)

    # ============================================
    # Delete User
    # ============================================
    def _delete_user(self):
        sel = self._get_selected_user()
        if not sel:
            QMessageBox.warning(self, "خطأ", "اختار مستخدم من القائمة الأول")
            return

        if sel["id"] == self.current_user.id:
            QMessageBox.warning(
                self, "مش ممكن",
                "ماينفعش تحذف حسابك وأنت مسجل بيه."
            )
            return

        if sel["role"] == "admin" and self.db.count_admins() <= 1:
            QMessageBox.warning(
                self, "مش ممكن",
                "ماينفعش تحذف آخر سوبر أدمن في النظام."
            )
            return

        reply = QMessageBox.question(
            self, "تأكيد الحذف",
            f"متأكد إنك عايز تحذف المستخدم «{sel['username']}»؟\n\n"
            f"الحذف نهائي ومش هينفع نرجعه.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        ok = self.db.delete_user(sel["id"])
        if not ok:
            QMessageBox.warning(self, "مش ممكن", "فشل الحذف.")
            return

        QMessageBox.information(self, "تم", "تم حذف المستخدم.")
        self.refresh()