"""
Employees Tab — تاب الموظفين الكامل.
================================================
5 تابات داخلية:
    1) 👥 قائمة الموظفين    — إضافة/تعديل/حذف
    2) 🕐 الحضور والانصراف  — تسجيل يومي
    3) 💵 السلف والخصومات   — تسجيل معاملات مالية
    4) 💰 الرواتب          — حساب تلقائي + طباعة
    5) 📊 تقارير الموظفين    — أداء وإحصائيات
"""

import os
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QAbstractItemView, QTabWidget,
    QLineEdit, QComboBox, QDateEdit, QDialog, QFormLayout,
    QTextEdit, QDoubleSpinBox, QSpinBox, QScrollArea,
    QSizePolicy, QFileDialog
)
from PySide6.QtCore import Qt, QDate, QTimer
from PySide6.QtGui import QColor, QFont, QPixmap, QIcon

from utils.theme import Theme


# ============================================================
# Dialog — إضافة/تعديل موظف
# ============================================================
class EmployeeDialog(QDialog):
    """نافذة إضافة أو تعديل موظف."""

    def __init__(self, parent=None, employee=None, users=None):
        super().__init__(parent)
        self.employee = employee
        self.users = users or []
        self.result_data = None

        is_edit = employee is not None
        self.setWindowTitle("تعديل موظف" if is_edit else "إضافة موظف جديد")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumSize(600, 700)

        self.setStyleSheet(f"""
            QDialog {{ background-color: {Theme.color('bg')}; }}
            QLabel {{ color: {Theme.color('text')}; background: transparent; font-size: 11pt; }}
            QLabel#title {{
                color: {Theme.color('primary')};
                font-size: 18px;
                font-weight: bold;
                padding: 8px;
            }}
            QLineEdit, QComboBox, QDateEdit, QTextEdit,
            QDoubleSpinBox, QSpinBox {{
                background-color: {Theme.color('surface')};
                color: {Theme.color('text')};
                border: 1px solid {Theme.color('border_strong')};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 11pt;
                min-height: 24px;
            }}
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus,
            QTextEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus {{
                border: 2px solid {Theme.color('primary')};
            }}
            QFrame#section {{
                background-color: {Theme.color('surface')};
                border: 1px solid {Theme.color('border')};
                border-radius: 10px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("✏️  تعديل موظف" if is_edit else "➕  إضافة موظف جديد")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        vbox = QVBoxLayout(content)
        vbox.setContentsMargins(2, 2, 8, 2)
        vbox.setSpacing(12)

        # القسم الأول
        sec1 = QFrame()
        sec1.setObjectName("section")
        sec1_layout = QFormLayout(sec1)
        sec1_layout.setContentsMargins(16, 14, 16, 14)
        sec1_layout.setSpacing(10)
        sec1_layout.setLabelAlignment(Qt.AlignRight)

        self.name_entry = QLineEdit()
        self.name_entry.setPlaceholderText("مثال: أحمد محمد علي")
        if is_edit:
            self.name_entry.setText(employee[1] or "")
        sec1_layout.addRow("👤  الاسم الكامل *", self.name_entry)

        self.phone_entry = QLineEdit()
        self.phone_entry.setPlaceholderText("مثال: 01012345678")
        if is_edit:
            self.phone_entry.setText(employee[2] or "")
        sec1_layout.addRow("📞  التليفون", self.phone_entry)

        self.national_id_entry = QLineEdit()
        self.national_id_entry.setPlaceholderText("14 رقم")
        if is_edit:
            self.national_id_entry.setText(employee[3] or "")
        sec1_layout.addRow("🆔  الرقم القومي", self.national_id_entry)

        self.email_entry = QLineEdit()
        self.email_entry.setPlaceholderText("example@email.com")
        if is_edit:
            self.email_entry.setText(employee[10] or "")
        sec1_layout.addRow("📧  الإيميل", self.email_entry)

        self.address_entry = QLineEdit()
        self.address_entry.setPlaceholderText("العنوان")
        if is_edit:
            self.address_entry.setText(employee[9] or "")
        sec1_layout.addRow("🏠  العنوان", self.address_entry)

        vbox.addWidget(sec1)

        # القسم الثاني
        sec2 = QFrame()
        sec2.setObjectName("section")
        sec2_layout = QFormLayout(sec2)
        sec2_layout.setContentsMargins(16, 14, 16, 14)
        sec2_layout.setSpacing(10)
        sec2_layout.setLabelAlignment(Qt.AlignRight)

        self.position_combo = QComboBox()
        self.position_combo.addItems([
            "حلاق", "كاشير", "مدير", "مساعد",
            "عامل نظافة", "موظف استقبال", "موظف"
        ])
        self.position_combo.setEditable(True)
        if is_edit and employee[4]:
            self.position_combo.setCurrentText(employee[4])
        sec2_layout.addRow("💼  الوظيفة", self.position_combo)

        self.department_entry = QLineEdit()
        self.department_entry.setPlaceholderText("مثال: قسم الحلاقة")
        if is_edit:
            self.department_entry.setText(employee[5] or "")
        sec2_layout.addRow("🏢  القسم", self.department_entry)

        self.hire_date_edit = QDateEdit()
        self.hire_date_edit.setCalendarPopup(True)
        self.hire_date_edit.setDisplayFormat("yyyy-MM-dd")
        if is_edit and employee[6]:
            try:
                d = datetime.strptime(employee[6], "%Y-%m-%d").date()
                self.hire_date_edit.setDate(QDate(d.year, d.month, d.day))
            except Exception:
                self.hire_date_edit.setDate(QDate.currentDate())
        else:
            self.hire_date_edit.setDate(QDate.currentDate())
        sec2_layout.addRow("📅  تاريخ التعيين", self.hire_date_edit)

        vbox.addWidget(sec2)

        # القسم الثالث
        sec3 = QFrame()
        sec3.setObjectName("section")
        sec3_layout = QFormLayout(sec3)
        sec3_layout.setContentsMargins(16, 14, 16, 14)
        sec3_layout.setSpacing(10)
        sec3_layout.setLabelAlignment(Qt.AlignRight)

        self.salary_spin = QDoubleSpinBox()
        self.salary_spin.setRange(0, 1000000)
        self.salary_spin.setSuffix(" ج.م")
        self.salary_spin.setDecimals(2)
        if is_edit:
            self.salary_spin.setValue(float(employee[7] or 0))
        sec3_layout.addRow("💰  الراتب الشهري", self.salary_spin)

        self.commission_spin = QDoubleSpinBox()
        self.commission_spin.setRange(0, 100)
        self.commission_spin.setSuffix(" %")
        self.commission_spin.setDecimals(2)
        if is_edit:
            self.commission_spin.setValue(float(employee[8] or 0))
        sec3_layout.addRow("🎯  نسبة العمولة", self.commission_spin)

        vbox.addWidget(sec3)

        # القسم الرابع
        sec4 = QFrame()
        sec4.setObjectName("section")
        sec4_layout = QFormLayout(sec4)
        sec4_layout.setContentsMargins(16, 14, 16, 14)
        sec4_layout.setSpacing(10)
        sec4_layout.setLabelAlignment(Qt.AlignRight)

        self.user_combo = QComboBox()
        self.user_combo.addItem("— لا يوجد —", None)
        for u in self.users:
            self.user_combo.addItem(f"{u.username} ({u.role})", u.id)
        if is_edit and employee[12]:
            for i in range(self.user_combo.count()):
                if self.user_combo.itemData(i) == employee[12]:
                    self.user_combo.setCurrentIndex(i)
                    break
        sec4_layout.addRow("🔐  ربط بحساب", self.user_combo)

        self.notes_entry = QTextEdit()
        self.notes_entry.setPlaceholderText("ملاحظات...")
        self.notes_entry.setMaximumHeight(80)
        if is_edit:
            self.notes_entry.setPlainText(employee[14] or "")
        sec4_layout.addRow("📝  ملاحظات", self.notes_entry)

        vbox.addWidget(sec4)
        vbox.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)

        btns = QHBoxLayout()
        btns.setSpacing(10)

        save_btn = QPushButton("💾  حفظ" if not is_edit else "💾  حفظ التعديلات")
        save_btn.setMinimumHeight(46)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('success')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"font-size: 13px; font-weight: bold; padding: 10px 20px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('success_hover')}; }}"
        )
        save_btn.clicked.connect(self._save)
        btns.addWidget(save_btn, 1)

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setMinimumHeight(46)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('surface_alt')}; "
            f"color: {Theme.color('text')}; border: none; border-radius: 8px; "
            f"font-size: 13px; font-weight: bold; padding: 10px 20px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('border_strong')}; }}"
        )
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(cancel_btn, 1)

        layout.addLayout(btns)

    def _save(self):
        name = self.name_entry.text().strip()
        if not name:
            QMessageBox.warning(self, "خطأ", "اسم الموظف مطلوب")
            return

        self.result_data = {
            "full_name": name,
            "phone": self.phone_entry.text().strip(),
            "national_id": self.national_id_entry.text().strip(),
            "position": self.position_combo.currentText().strip(),
            "department": self.department_entry.text().strip(),
            "hire_date": self.hire_date_edit.date().toString("yyyy-MM-dd"),
            "salary": self.salary_spin.value(),
            "commission_rate": self.commission_spin.value(),
            "address": self.address_entry.text().strip(),
            "email": self.email_entry.text().strip(),
            "user_id": self.user_combo.currentData(),
            "notes": self.notes_entry.toPlainText().strip(),
        }
        self.accept()


# ============================================================
# Tab 1: قائمة الموظفين
# ============================================================
class EmployeesListTab(QWidget):
    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user
        self.can_edit = user.is_admin or user.has_permission("edit_employees")
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(12)

        # الإحصائيات
        stats_row = QHBoxLayout()
        stats_row.setSpacing(8)

        self.stat_total = self._make_stat_card("👥  إجمالي الموظفين", "0")
        self.stat_active = self._make_stat_card("✅  نشط", "0")
        self.stat_salary = self._make_stat_card("💰  إجمالي الرواتب", "0 ج")
        self.stat_commission = self._make_stat_card("🎯  متوسط العمولة", "0%")

        stats_row.addWidget(self.stat_total, 1)
        stats_row.addWidget(self.stat_active, 1)
        stats_row.addWidget(self.stat_salary, 1)
        stats_row.addWidget(self.stat_commission, 1)
        layout.addLayout(stats_row)

        # الأزرار
        actions = QHBoxLayout()
        actions.setSpacing(8)

        if self.can_edit:
            add_btn = QPushButton("➕  إضافة موظف")
            add_btn.setMinimumHeight(42)
            add_btn.setCursor(Qt.PointingHandCursor)
            add_btn.setStyleSheet(
                f"QPushButton {{ background-color: {Theme.color('success')}; "
                f"color: white; border: none; border-radius: 8px; "
                f"font-weight: bold; font-size: 12px; padding: 8px 16px; }}"
                f"QPushButton:hover {{ background-color: {Theme.color('success_hover')}; }}"
            )
            add_btn.clicked.connect(self._add_employee)
            actions.addWidget(add_btn)

            edit_btn = QPushButton("✏️  تعديل")
            edit_btn.setMinimumHeight(42)
            edit_btn.setCursor(Qt.PointingHandCursor)
            edit_btn.setStyleSheet(
                f"QPushButton {{ background-color: {Theme.color('primary')}; "
                f"color: white; border: none; border-radius: 8px; "
                f"font-weight: bold; font-size: 12px; padding: 8px 16px; }}"
                f"QPushButton:hover {{ background-color: {Theme.color('primary_hover')}; }}"
            )
            edit_btn.clicked.connect(self._edit_employee)
            actions.addWidget(edit_btn)

            delete_btn = QPushButton("🗑️  حذف")
            delete_btn.setMinimumHeight(42)
            delete_btn.setCursor(Qt.PointingHandCursor)
            delete_btn.setStyleSheet(
                f"QPushButton {{ background-color: {Theme.color('danger')}; "
                f"color: white; border: none; border-radius: 8px; "
                f"font-weight: bold; font-size: 12px; padding: 8px 16px; }}"
                f"QPushButton:hover {{ background-color: {Theme.color('danger_hover')}; }}"
            )
            delete_btn.clicked.connect(self._delete_employee)
            actions.addWidget(delete_btn)

        refresh_btn = QPushButton("🔄  تحديث")
        refresh_btn.setMinimumHeight(42)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('surface_alt')}; "
            f"color: {Theme.color('text')}; border: none; border-radius: 8px; "
            f"font-weight: bold; font-size: 12px; padding: 8px 16px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('border_strong')}; }}"
        )
        refresh_btn.clicked.connect(self.refresh)
        actions.addWidget(refresh_btn)

        actions.addStretch()
        layout.addLayout(actions)

        # الجدول
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "#", "الاسم", "الوظيفة", "التليفون",
            "الراتب", "العمولة", "تاريخ التعيين", "الحالة", "ملاحظات"
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setLayoutDirection(Qt.RightToLeft)
        self.table.doubleClicked.connect(self._edit_employee)

        h = self.table.horizontalHeader()
        for i in range(9):
            if i in (1, 8):
                h.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                h.setSectionResizeMode(i, QHeaderView.Fixed)

        self.table.setColumnWidth(0, 45)
        self.table.setColumnWidth(2, 110)
        self.table.setColumnWidth(3, 130)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(5, 100)
        self.table.setColumnWidth(6, 120)
        self.table.setColumnWidth(7, 100)

        layout.addWidget(self.table, stretch=1)

    def _make_stat_card(self, title, value):
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background-color: {Theme.color('surface')}; "
            f"border: 1px solid {Theme.color('border')}; "
            f"border-radius: 10px; }}"
        )
        card.setMinimumHeight(75)
        v = QVBoxLayout(card)
        v.setContentsMargins(12, 8, 12, 8)
        v.setSpacing(2)

        t = QLabel(title)
        t.setStyleSheet(
            f"color: {Theme.color('text_muted')}; font-size: 10px; "
            f"font-weight: bold; background: transparent;"
        )
        t.setAlignment(Qt.AlignCenter)
        v.addWidget(t)

        val = QLabel(value)
        val.setStyleSheet(
            f"color: {Theme.color('primary')}; font-size: 15px; "
            f"font-weight: bold; background: transparent;"
        )
        val.setAlignment(Qt.AlignCenter)
        v.addWidget(val)

        card._value_label = val
        return card

    def refresh(self):
        try:
            employees = self.db.list_employees(active_only=False)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل الموظفين:\n{e}")
            return

        active = [e for e in employees if e[13] == 1]
        total_salary = sum(e[7] or 0 for e in active)
        avg_commission = (
            sum(e[8] or 0 for e in active) / len(active) if active else 0
        )

        self.stat_total._value_label.setText(str(len(employees)))
        self.stat_active._value_label.setText(str(len(active)))
        self.stat_salary._value_label.setText(f"{total_salary:,.0f} ج")
        self.stat_commission._value_label.setText(f"{avg_commission:.1f}%")

        self.table.setRowCount(len(employees))
        text_color = QColor(Theme.color("text"))
        green = QColor(Theme.color("success"))
        gray = QColor(Theme.color("text_dim"))
        gold = QColor(Theme.color("gold"))

        for row, e in enumerate(employees):
            item_id = QTableWidgetItem(str(e[0]))
            item_id.setTextAlignment(Qt.AlignCenter)
            item_id.setData(Qt.UserRole, e[0])
            item_id.setForeground(text_color)
            self.table.setItem(row, 0, item_id)

            item_name = QTableWidgetItem(str(e[1] or ""))
            item_name.setTextAlignment(Qt.AlignCenter)
            item_name.setForeground(gold if e[13] == 1 else gray)
            item_name.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.table.setItem(row, 1, item_name)

            self._add_center_item(row, 2, str(e[4] or "—"), text_color)
            self._add_center_item(row, 3, str(e[2] or "—"), text_color)
            self._add_center_item(row, 4, f"{e[7] or 0:,.0f} ج", green)
            self._add_center_item(row, 5, f"{e[8] or 0:.1f}%", text_color)
            self._add_center_item(row, 6, str(e[6] or "—"), text_color)

            status_text = "✅  نشط" if e[13] == 1 else "🚫  موقوف"
            status_color = green if e[13] == 1 else gray
            self._add_center_item(row, 7, status_text, status_color)
            self._add_center_item(row, 8, str(e[14] or "")[:50], gray)

    def _add_center_item(self, row, col, text, color):
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignCenter)
        item.setForeground(color)
        self.table.setItem(row, col, item)

    def _get_selected_id(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        item = self.table.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    def _add_employee(self):
        if not self.can_edit:
            return
        try:
            users = self.db.list_users()
        except Exception:
            users = []

        dlg = EmployeeDialog(self, employee=None, users=users)
        if dlg.exec() != QDialog.Accepted or not dlg.result_data:
            return

        try:
            self.db.add_employee(**dlg.result_data)
            QMessageBox.information(self, "تم", "✅ تم إضافة الموظف.")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل الإضافة:\n{e}")

    def _edit_employee(self):
        if not self.can_edit:
            return
        emp_id = self._get_selected_id()
        if emp_id is None:
            QMessageBox.warning(self, "تنبيه", "اختار موظف من الجدول.")
            return

        try:
            emp = self.db.get_employee(emp_id)
            users = self.db.list_users()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل التحميل:\n{e}")
            return

        if not emp:
            QMessageBox.warning(self, "خطأ", "الموظف مش موجود.")
            return

        dlg = EmployeeDialog(self, employee=emp, users=users)
        if dlg.exec() != QDialog.Accepted or not dlg.result_data:
            return

        try:
            self.db.update_employee(emp_id, **dlg.result_data)
            QMessageBox.information(self, "تم", "✅ تم تحديث البيانات.")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل التحديث:\n{e}")

    def _delete_employee(self):
        if not self.can_edit:
            return
        emp_id = self._get_selected_id()
        if emp_id is None:
            QMessageBox.warning(self, "تنبيه", "اختار موظف من الجدول.")
            return

        emp = self.db.get_employee(emp_id)
        if not emp:
            return

        reply = QMessageBox.question(
            self, "تأكيد الحذف",
            f"متأكد إنك عايز تحذف الموظف:\n\n👤  {emp[1]}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        try:
            self.db.delete_employee(emp_id)
            QMessageBox.information(self, "تم", "✅ تم حذف الموظف.")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل الحذف:\n{e}")


# ============================================================
# Tab 2: الحضور والانصراف
# ============================================================
class AttendanceTab(QWidget):
    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(12)

        # أزرار التسجيل السريع
        quick_frame = QFrame()
        quick_frame.setStyleSheet(
            f"QFrame {{ background-color: {Theme.color('surface')}; "
            f"border: 1px solid {Theme.color('primary')}; border-radius: 10px; }}"
        )
        quick_layout = QVBoxLayout(quick_frame)
        quick_layout.setContentsMargins(16, 14, 16, 14)
        quick_layout.setSpacing(10)

        quick_title = QLabel("⚡  تسجيل سريع")
        quick_title.setStyleSheet(
            f"color: {Theme.color('primary')}; font-size: 14px; "
            f"font-weight: bold; background: transparent;"
        )
        quick_layout.addWidget(quick_title)

        quick_row = QHBoxLayout()
        quick_row.setSpacing(8)

        quick_row.addWidget(QLabel("الموظف:"))
        self.quick_emp_combo = QComboBox()
        self.quick_emp_combo.setMinimumHeight(42)
        self.quick_emp_combo.setMinimumWidth(200)
        quick_row.addWidget(self.quick_emp_combo)

        checkin_btn = QPushButton("🟢  تسجيل حضور")
        checkin_btn.setMinimumHeight(42)
        checkin_btn.setCursor(Qt.PointingHandCursor)
        checkin_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('success')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"font-weight: bold; padding: 8px 20px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('success_hover')}; }}"
        )
        checkin_btn.clicked.connect(self._quick_check_in)
        quick_row.addWidget(checkin_btn)

        checkout_btn = QPushButton("🔴  تسجيل انصراف")
        checkout_btn.setMinimumHeight(42)
        checkout_btn.setCursor(Qt.PointingHandCursor)
        checkout_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('danger')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"font-weight: bold; padding: 8px 20px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('danger_hover')}; }}"
        )
        checkout_btn.clicked.connect(self._quick_check_out)
        quick_row.addWidget(checkout_btn)

        quick_row.addStretch()
        quick_layout.addLayout(quick_row)
        layout.addWidget(quick_frame)

        # الفلترة
        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)

        filter_row.addWidget(QLabel("من:"))
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_from.setMinimumHeight(38)
        filter_row.addWidget(self.date_from)

        filter_row.addWidget(QLabel("إلى:"))
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        self.date_to.setMinimumHeight(38)
        filter_row.addWidget(self.date_to)

        filter_row.addWidget(QLabel("الموظف:"))
        self.filter_emp_combo = QComboBox()
        self.filter_emp_combo.setMinimumHeight(38)
        self.filter_emp_combo.setMinimumWidth(180)
        filter_row.addWidget(self.filter_emp_combo)

        apply_btn = QPushButton("🔍  تطبيق")
        apply_btn.setMinimumHeight(38)
        apply_btn.setCursor(Qt.PointingHandCursor)
        apply_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('primary')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"font-weight: bold; padding: 6px 16px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('primary_hover')}; }}"
        )
        apply_btn.clicked.connect(self.refresh)
        filter_row.addWidget(apply_btn)

        filter_row.addStretch()
        layout.addLayout(filter_row)

        # الجدول
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "#", "الموظف", "التاريخ", "الحضور", "الانصراف",
            "ساعات العمل", "الحالة", "ملاحظات"
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setLayoutDirection(Qt.RightToLeft)

        h = self.table.horizontalHeader()
        for i in range(8):
            if i in (1, 7):
                h.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                h.setSectionResizeMode(i, QHeaderView.Fixed)

        self.table.setColumnWidth(0, 45)
        self.table.setColumnWidth(2, 110)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 90)
        self.table.setColumnWidth(5, 110)
        self.table.setColumnWidth(6, 100)

        layout.addWidget(self.table, stretch=1)

    def refresh(self):
        # حدّث قوائم الموظفين
        try:
            employees = self.db.list_employees(active_only=True)
        except Exception:
            employees = []

        # قائمة التسجيل السريع
        current_q = self.quick_emp_combo.currentData()
        self.quick_emp_combo.clear()
        for e in employees:
            self.quick_emp_combo.addItem(f"{e[1]} — {e[4]}", e[0])
        if current_q:
            for i in range(self.quick_emp_combo.count()):
                if self.quick_emp_combo.itemData(i) == current_q:
                    self.quick_emp_combo.setCurrentIndex(i)
                    break

        # قائمة الفلترة
        current_f = self.filter_emp_combo.currentData()
        self.filter_emp_combo.clear()
        self.filter_emp_combo.addItem("الكل", None)
        for e in employees:
            self.filter_emp_combo.addItem(e[1], e[0])
        if current_f:
            for i in range(self.filter_emp_combo.count()):
                if self.filter_emp_combo.itemData(i) == current_f:
                    self.filter_emp_combo.setCurrentIndex(i)
                    break

        # الجدول
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to = self.date_to.date().toString("yyyy-MM-dd")
        emp_id = self.filter_emp_combo.currentData()

        try:
            records = self.db.list_attendance(
                employee_id=emp_id,
                date_from=date_from,
                date_to=date_to
            )
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل السجل:\n{e}")
            return

        self.table.setRowCount(len(records))
        text_color = QColor(Theme.color("text"))
        green = QColor(Theme.color("success"))
        gray = QColor(Theme.color("text_dim"))

        for row, rec in enumerate(records):
            # rec = (id, emp_id, full_name, date, check_in,
            #         check_out, work_hours, status, notes)

            self._add_center(row, 0, str(rec[0]), text_color)
            self._add_center(row, 1, rec[2], text_color)
            self._add_center(row, 2, rec[3], text_color)
            self._add_center(row, 3, rec[4] or "—", green)
            self._add_center(row, 4, rec[5] or "—",
                             QColor(Theme.color("danger")) if rec[5] else gray)
            self._add_center(row, 5, f"{rec[6]:.1f}" if rec[6] else "—", text_color)
            self._add_center(row, 6, rec[7] or "—", green)
            self._add_center(row, 7, str(rec[8] or "")[:40], gray)

    def _add_center(self, row, col, text, color):
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(Qt.AlignCenter)
        item.setForeground(color)
        self.table.setItem(row, col, item)

    def _quick_check_in(self):
        emp_id = self.quick_emp_combo.currentData()
        if not emp_id:
            QMessageBox.warning(self, "تنبيه", "اختار موظف الأول.")
            return

        try:
            ok, msg = self.db.check_in_employee(emp_id)
            if ok:
                QMessageBox.information(self, "تم", f"✅ {msg}")
            else:
                QMessageBox.warning(self, "تنبيه", msg)
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل التسجيل:\n{e}")

    def _quick_check_out(self):
        emp_id = self.quick_emp_combo.currentData()
        if not emp_id:
            QMessageBox.warning(self, "تنبيه", "اختار موظف الأول.")
            return

        try:
            ok, msg = self.db.check_out_employee(emp_id)
            if ok:
                QMessageBox.information(self, "تم", f"✅ {msg}")
            else:
                QMessageBox.warning(self, "تنبيه", msg)
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل التسجيل:\n{e}")


# ============================================================
# Tab 3: السلف والخصومات
# ============================================================
class EmployeeTransactionsTab(QWidget):
    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(12)

        # إضافة معاملة جديدة
        add_frame = QFrame()
        add_frame.setStyleSheet(
            f"QFrame {{ background-color: {Theme.color('surface')}; "
            f"border: 1px solid {Theme.color('border')}; border-radius: 10px; }}"
        )
        add_layout = QVBoxLayout(add_frame)
        add_layout.setContentsMargins(16, 14, 16, 14)
        add_layout.setSpacing(10)

        title = QLabel("➕  إضافة معاملة جديدة")
        title.setStyleSheet(
            f"color: {Theme.color('primary')}; font-size: 14px; "
            f"font-weight: bold; background: transparent;"
        )
        add_layout.addWidget(title)

        row = QHBoxLayout()
        row.setSpacing(8)

        row.addWidget(QLabel("الموظف:"))
        self.emp_combo = QComboBox()
        self.emp_combo.setMinimumHeight(42)
        self.emp_combo.setMinimumWidth(180)
        row.addWidget(self.emp_combo)

        row.addWidget(QLabel("النوع:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["سلفة", "خصم", "مكافأة"])
        self.type_combo.setMinimumHeight(42)
        row.addWidget(self.type_combo)

        row.addWidget(QLabel("المبلغ:"))
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 1000000)
        self.amount_spin.setSuffix(" ج.م")
        self.amount_spin.setMinimumHeight(42)
        row.addWidget(self.amount_spin)

        row.addWidget(QLabel("السبب:"))
        self.reason_entry = QLineEdit()
        self.reason_entry.setPlaceholderText("مثال: سلفة شخصية")
        self.reason_entry.setMinimumHeight(42)
        row.addWidget(self.reason_entry, 1)

        add_btn = QPushButton("➕  إضافة")
        add_btn.setMinimumHeight(42)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('success')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"font-weight: bold; padding: 8px 20px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('success_hover')}; }}"
        )
        add_btn.clicked.connect(self._add_transaction)
        row.addWidget(add_btn)

        add_layout.addLayout(row)
        layout.addWidget(add_frame)

        # الفلترة
        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)

        filter_row.addWidget(QLabel("الموظف:"))
        self.filter_emp = QComboBox()
        self.filter_emp.setMinimumHeight(38)
        self.filter_emp.setMinimumWidth(180)
        filter_row.addWidget(self.filter_emp)

        filter_row.addWidget(QLabel("النوع:"))
        self.filter_type = QComboBox()
        self.filter_type.addItem("الكل", None)
        self.filter_type.addItem("سلفة", "advance")
        self.filter_type.addItem("خصم", "deduction")
        self.filter_type.addItem("مكافأة", "bonus")
        self.filter_type.setMinimumHeight(38)
        filter_row.addWidget(self.filter_type)

        apply_btn = QPushButton("🔍  تطبيق")
        apply_btn.setMinimumHeight(38)
        apply_btn.setCursor(Qt.PointingHandCursor)
        apply_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('primary')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"font-weight: bold; padding: 6px 16px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('primary_hover')}; }}"
        )
        apply_btn.clicked.connect(self.refresh)
        filter_row.addWidget(apply_btn)

        delete_btn = QPushButton("🗑️  حذف المختار")
        delete_btn.setMinimumHeight(38)
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('danger')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"font-weight: bold; padding: 6px 16px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('danger_hover')}; }}"
        )
        delete_btn.clicked.connect(self._delete_selected)
        filter_row.addWidget(delete_btn)

        filter_row.addStretch()
        layout.addLayout(filter_row)

        # الجدول
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "#", "الموظف", "النوع", "المبلغ", "التاريخ", "السبب", "ملاحظات"
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setLayoutDirection(Qt.RightToLeft)

        h = self.table.horizontalHeader()
        for i in range(7):
            if i in (1, 5, 6):
                h.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                h.setSectionResizeMode(i, QHeaderView.Fixed)

        self.table.setColumnWidth(0, 45)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 110)

        layout.addWidget(self.table, stretch=1)

    def refresh(self):
        # حدّث قوائم الموظفين
        try:
            employees = self.db.list_employees(active_only=True)
        except Exception:
            employees = []

        current = self.emp_combo.currentData()
        self.emp_combo.clear()
        for e in employees:
            self.emp_combo.addItem(e[1], e[0])
        if current:
            for i in range(self.emp_combo.count()):
                if self.emp_combo.itemData(i) == current:
                    self.emp_combo.setCurrentIndex(i)
                    break

        # فلتر
        current_f = self.filter_emp.currentData()
        self.filter_emp.clear()
        self.filter_emp.addItem("الكل", None)
        for e in employees:
            self.filter_emp.addItem(e[1], e[0])
        if current_f:
            for i in range(self.filter_emp.count()):
                if self.filter_emp.itemData(i) == current_f:
                    self.filter_emp.setCurrentIndex(i)
                    break

        # الجدول
        emp_id = self.filter_emp.currentData()
        txn_type = self.filter_type.currentData()

        try:
            records = self.db.list_employee_transactions(
                employee_id=emp_id, txn_type=txn_type
            )
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل التحميل:\n{e}")
            return

        # ترتيب عكسي حسب ID
        records = sorted(records, key=lambda x: x[0], reverse=True)

        self.table.setRowCount(len(records))
        text_color = QColor(Theme.color("text"))
        green = QColor(Theme.color("success"))
        red = QColor(Theme.color("danger"))
        gold = QColor(Theme.color("gold"))

        type_labels = {
            "advance": "💵  سلفة",
            "deduction": "➖  خصم",
            "bonus": "🎁  مكافأة",
        }

        for row, rec in enumerate(records):
            # rec = (id, emp_id, full_name, type, amount, date, reason, notes)

            self._add(row, 0, str(rec[0]), text_color)
            self._add(row, 1, rec[2], text_color)

            txn_type_val = rec[3]
            type_label = type_labels.get(txn_type_val, txn_type_val)
            type_color = {
                "advance": red,
                "deduction": red,
                "bonus": gold,
            }.get(txn_type_val, text_color)
            self._add(row, 2, type_label, type_color)

            self._add(row, 3, f"{rec[4]:,.0f} ج",
                      green if txn_type_val == "bonus" else red)
            self._add(row, 4, rec[5], text_color)
            self._add(row, 5, rec[6] or "—", text_color)
            self._add(row, 6, rec[7] or "", gray if False else text_color)

    def _add(self, row, col, text, color):
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(Qt.AlignCenter)
        item.setForeground(color)
        self.table.setItem(row, col, item)

    def _add_transaction(self):
        emp_id = self.emp_combo.currentData()
        if not emp_id:
            QMessageBox.warning(self, "تنبيه", "اختار موظف.")
            return

        amount = self.amount_spin.value()
        if amount <= 0:
            QMessageBox.warning(self, "تنبيه", "اكتب مبلغ صحيح.")
            return

        type_map = {"سلفة": "advance", "خصم": "deduction", "مكافأة": "bonus"}
        txn_type = type_map.get(self.type_combo.currentText(), "advance")

        try:
            self.db.add_employee_transaction(
                emp_id, txn_type, amount, self.reason_entry.text().strip()
            )
            QMessageBox.information(self, "تم", "✅ تم إضافة المعاملة.")
            self.amount_spin.setValue(0)
            self.reason_entry.clear()
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل الإضافة:\n{e}")

    def _delete_selected(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.warning(self, "تنبيه", "اختار معاملة من الجدول.")
            return

        row = rows[0].row()
        item = self.table.item(row, 0)
        if not item:
            return

        txn_id = int(item.text())

        reply = QMessageBox.question(
            self, "تأكيد", "متأكد إنك عايز تحذف المعاملة دي؟",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        try:
            self.db.delete_employee_transaction(txn_id)
            QMessageBox.information(self, "تم", "✅ تم الحذف.")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل الحذف:\n{e}")


# ============================================================
# Tab 4: الرواتب
# ============================================================
class SalariesTab(QWidget):
    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(12)

        # الحساب
        calc_frame = QFrame()
        calc_frame.setStyleSheet(
            f"QFrame {{ background-color: {Theme.color('surface')}; "
            f"border: 1px solid {Theme.color('primary')}; border-radius: 10px; }}"
        )
        calc_layout = QVBoxLayout(calc_frame)
        calc_layout.setContentsMargins(16, 14, 16, 14)
        calc_layout.setSpacing(10)

        title = QLabel("💰  حساب الراتب الشهري")
        title.setStyleSheet(
            f"color: {Theme.color('primary')}; font-size: 14px; "
            f"font-weight: bold; background: transparent;"
        )
        calc_layout.addWidget(title)

        row = QHBoxLayout()
        row.setSpacing(8)

        row.addWidget(QLabel("الموظف:"))
        self.emp_combo = QComboBox()
        self.emp_combo.setMinimumHeight(42)
        self.emp_combo.setMinimumWidth(200)
        row.addWidget(self.emp_combo)

        row.addWidget(QLabel("الشهر:"))
        self.month_combo = QComboBox()
        for i in range(12):
            d = datetime.now() - timedelta(days=30 * i)
            month_str = d.strftime("%Y-%m")
            self.month_combo.addItem(month_str, month_str)
        self.month_combo.setMinimumHeight(42)
        self.month_combo.setMinimumWidth(140)
        row.addWidget(self.month_combo)

        calc_btn = QPushButton("🧮  احسب")
        calc_btn.setMinimumHeight(42)
        calc_btn.setCursor(Qt.PointingHandCursor)
        calc_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('primary')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"font-weight: bold; padding: 8px 20px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('primary_hover')}; }}"
        )
        calc_btn.clicked.connect(self._calculate)
        row.addWidget(calc_btn)

        row.addStretch()
        calc_layout.addLayout(row)

        # نتيجة الحساب
        self.result_label = QLabel("— اختار موظف واضغط احسب —")
        self.result_label.setStyleSheet(
            f"color: {Theme.color('text_muted')}; font-size: 11px; "
            f"background: transparent; padding: 8px;"
        )
        self.result_label.setWordWrap(True)
        calc_layout.addWidget(self.result_label)

        layout.addWidget(calc_frame)

        # الجدول
        refresh_btn = QPushButton("🔄  تحديث الجدول")
        refresh_btn.setMinimumHeight(42)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('surface_alt')}; "
            f"color: {Theme.color('text')}; border: none; border-radius: 8px; "
            f"font-weight: bold; padding: 8px 16px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('border_strong')}; }}"
        )
        refresh_btn.clicked.connect(self.refresh)

        actions = QHBoxLayout()
        actions.addWidget(refresh_btn)
        actions.addStretch()
        layout.addLayout(actions)

        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "#", "الموظف", "الشهر", "الأساسي", "العمولات",
            "المكافآت", "السلف", "الخصومات", "الصافي"
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setLayoutDirection(Qt.RightToLeft)

        h = self.table.horizontalHeader()
        for i in range(9):
            if i == 1:
                h.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                h.setSectionResizeMode(i, QHeaderView.Fixed)

        self.table.setColumnWidth(0, 45)
        self.table.setColumnWidth(2, 100)
        for i in range(3, 9):
            self.table.setColumnWidth(i, 110)

        layout.addWidget(self.table, stretch=1)

    def refresh(self):
        try:
            employees = self.db.list_employees(active_only=True)
        except Exception:
            employees = []

        current = self.emp_combo.currentData()
        self.emp_combo.clear()
        for e in employees:
            self.emp_combo.addItem(f"{e[1]} — {e[4]}", e[0])
        if current:
            for i in range(self.emp_combo.count()):
                if self.emp_combo.itemData(i) == current:
                    self.emp_combo.setCurrentIndex(i)
                    break

        # الجدول
        try:
            salaries = self.db.list_salaries()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل التحميل:\n{e}")
            return

        self.table.setRowCount(len(salaries))
        text_color = QColor(Theme.color("text"))
        green = QColor(Theme.color("success"))
        red = QColor(Theme.color("danger"))

        for row, s in enumerate(salaries):
            # s = (id, emp_id, name, month, base, commissions,
            #      bonuses, advances, deductions, net, paid, paid_date)

            self._add(row, 0, str(s[0]), text_color)
            self._add(row, 1, s[2], text_color)
            self._add(row, 2, s[3], text_color)
            self._add(row, 3, f"{s[4]:,.0f}", text_color)
            self._add(row, 4, f"{s[5]:,.0f}", green)
            self._add(row, 5, f"{s[6]:,.0f}", QColor(Theme.color("gold")))
            self._add(row, 6, f"{s[7]:,.0f}", red)
            self._add(row, 7, f"{s[8]:,.0f}", red)
            self._add(row, 8, f"{s[9]:,.0f} ج", green)

    def _add(self, row, col, text, color):
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(Qt.AlignCenter)
        item.setForeground(color)
        self.table.setItem(row, col, item)

    def _calculate(self):
        emp_id = self.emp_combo.currentData()
        if not emp_id:
            QMessageBox.warning(self, "تنبيه", "اختار موظف.")
            return

        month = self.month_combo.currentData()

        try:
            result = self.db.calculate_salary(emp_id, month)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل الحساب:\n{e}")
            return

        if not result:
            QMessageBox.warning(self, "خطأ", "فشل الحساب.")
            return

        text = (
            f"👤  الموظف: {result['full_name']}\n"
            f"📅  الشهر: {result['month']}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰  الراتب الأساسي:  {result['base_salary']:,.2f} ج\n"
            f"🎯  العمولات:       {result['commissions']:,.2f} ج\n"
            f"🎁  المكافآت:       {result['bonuses']:,.2f} ج\n"
            f"➖  السلف:          {result['advances']:,.2f} ج\n"
            f"➖  الخصومات:       {result['deductions']:,.2f} ج\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💵  الصافي:         {result['net_salary']:,.2f} ج"
        )
        self.result_label.setText(text)
        self.result_label.setStyleSheet(
            f"color: {Theme.color('text')}; font-size: 12px; "
            f"background: {Theme.color('surface_alt')}; "
            f"padding: 12px; border-radius: 8px; "
            f"font-family: 'Consolas', monospace;"
        )


# ============================================================
# Tab 5: تقارير الموظفين
# ============================================================
class EmployeeReportsTab(QWidget):
    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(12)

        # الفلترة
        filter_frame = QFrame()
        filter_frame.setStyleSheet(
            f"QFrame {{ background-color: {Theme.color('surface')}; "
            f"border: 1px solid {Theme.color('border')}; border-radius: 10px; }}"
        )
        filter_layout = QVBoxLayout(filter_frame)
        filter_layout.setContentsMargins(16, 14, 16, 14)
        filter_layout.setSpacing(10)

        title = QLabel("📊  تقرير أداء الموظفين")
        title.setStyleSheet(
            f"color: {Theme.color('primary')}; font-size: 14px; "
            f"font-weight: bold; background: transparent;"
        )
        filter_layout.addWidget(title)

        row = QHBoxLayout()
        row.setSpacing(8)

        row.addWidget(QLabel("من:"))
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_from.setMinimumHeight(42)
        row.addWidget(self.date_from)

        row.addWidget(QLabel("إلى:"))
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        self.date_to.setMinimumHeight(42)
        row.addWidget(self.date_to)

        apply_btn = QPushButton("🔍  تطبيق")
        apply_btn.setMinimumHeight(42)
        apply_btn.setCursor(Qt.PointingHandCursor)
        apply_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('primary')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"font-weight: bold; padding: 8px 20px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('primary_hover')}; }}"
        )
        apply_btn.clicked.connect(self.refresh)
        row.addWidget(apply_btn)

        row.addStretch()
        filter_layout.addLayout(row)
        layout.addWidget(filter_frame)

        # الجدول
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "#", "الموظف", "الوظيفة",
            "عدد الحجوزات", "الإيرادات", "أيام الحضور", "ساعات العمل"
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setLayoutDirection(Qt.RightToLeft)

        h = self.table.horizontalHeader()
        for i in range(7):
            if i in (1, 2):
                h.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                h.setSectionResizeMode(i, QHeaderView.Fixed)

        self.table.setColumnWidth(0, 45)
        self.table.setColumnWidth(3, 130)
        self.table.setColumnWidth(4, 140)
        self.table.setColumnWidth(5, 130)
        self.table.setColumnWidth(6, 130)

        layout.addWidget(self.table, stretch=1)

    def refresh(self):
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to = self.date_to.date().toString("yyyy-MM-dd")

        try:
            employees = self.db.list_employees(active_only=True)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل التحميل:\n{e}")
            return

        self.table.setRowCount(len(employees))
        text_color = QColor(Theme.color("text"))
        green = QColor(Theme.color("success"))
        blue = QColor(Theme.color("primary"))
        gold = QColor(Theme.color("gold"))

        for row, e in enumerate(employees):
            emp_id = e[0]
            name = e[1]
            position = e[4]

            try:
                perf = self.db.get_employee_performance(
                    emp_id, date_from, date_to
                )
            except Exception:
                perf = None

            self._add(row, 0, str(emp_id), text_color)
            self._add(row, 1, name, gold)
            self._add(row, 2, position or "—", text_color)

            if perf:
                self._add(row, 3, str(perf["bookings_count"]), blue)
                self._add(row, 4, f"{perf['revenue']:,.0f} ج", green)
                self._add(row, 5, str(perf["attendance_days"]), text_color)
                self._add(row, 6, f"{perf['work_hours']:.1f}", text_color)
            else:
                self._add(row, 3, "—", text_color)
                self._add(row, 4, "—", text_color)
                self._add(row, 5, "—", text_color)
                self._add(row, 6, "—", text_color)

    def _add(self, row, col, text, color):
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(Qt.AlignCenter)
        item.setForeground(color)
        self.table.setItem(row, col, item)


# ============================================================
# Main Tab — Employees Tab
# ============================================================
class EmployeesTab(QWidget):
    """التاب الرئيسي للموظفين — بيجمع 5 تابات داخلية."""

    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # العنوان
        header = QHBoxLayout()
        title = QLabel("👥  إدارة الموظفين")
        title.setStyleSheet(
            f"font-size: 22px; font-weight: bold; "
            f"color: {Theme.color('primary')}; padding: 4px; "
            f"background: transparent;"
        )
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # الـ 5 تابات
        self.sub_tabs = QTabWidget()
        self.sub_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {Theme.color('border')};
                border-radius: 8px;
                background-color: {Theme.color('bg')};
                padding: 16px;
            }}
            QTabBar::tab {{
                background-color: {Theme.color('surface')};
                color: {Theme.color('text_muted')};
                padding: 10px 22px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 12px;
                font-weight: bold;
                min-width: 140px;
            }}
            QTabBar::tab:selected {{
                background-color: {Theme.color('primary')};
                color: #ffffff;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {Theme.color('surface_alt')};
                color: {Theme.color('text')};
            }}
        """)

        self.tab_list = EmployeesListTab(self.db, self.user)
        self.sub_tabs.addTab(self.tab_list, "  👥  قائمة الموظفين  ")

        self.tab_attendance = AttendanceTab(self.db, self.user)
        self.sub_tabs.addTab(self.tab_attendance, "  🕐  الحضور والانصراف  ")

        self.tab_transactions = EmployeeTransactionsTab(self.db, self.user)
        self.sub_tabs.addTab(self.tab_transactions, "  💵  السلف والخصومات  ")

        self.tab_salaries = SalariesTab(self.db, self.user)
        self.sub_tabs.addTab(self.tab_salaries, "  💰  الرواتب  ")

        self.tab_reports = EmployeeReportsTab(self.db, self.user)
        self.sub_tabs.addTab(self.tab_reports, "  📊  التقارير  ")

        layout.addWidget(self.sub_tabs, stretch=1)

        # حدّث التاب الحالي لما يتبدّل
        self.sub_tabs.currentChanged.connect(self._on_tab_changed)

    def _on_tab_changed(self, index):
        try:
            tab = self.sub_tabs.widget(index)
            if hasattr(tab, "refresh"):
                tab.refresh()
        except Exception:
            pass

    def refresh(self):
        """يحدّث التاب الحالي."""
        try:
            current = self.sub_tabs.currentWidget()
            if hasattr(current, "refresh"):
                current.refresh()
        except Exception:
            pass