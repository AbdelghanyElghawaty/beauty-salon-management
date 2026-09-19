"""
Management Tab — تاب الإدارة الكامل.
================================================
4 تابات داخلية:
    1) 📊 Dashboard     — ملخص شامل
    2) 💼 المصاريف       — إضافة/عرض/حذف
    3) 💰 الأرباح والخسائر — تقرير تفصيلي
    4) 📈 التحليلات      — رسوم بيانية
"""

import os
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QAbstractItemView, QTabWidget,
    QLineEdit, QComboBox, QDateEdit, QDialog, QFormLayout,
    QTextEdit, QDoubleSpinBox, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QDate, QTimer
from PySide6.QtGui import QColor, QFont

from utils.theme import Theme


# ============================================================
# Dialog — إضافة مصروف
# ============================================================
class ExpenseDialog(QDialog):
    """نافذة إضافة مصروف."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.result_data = None

        self.setWindowTitle("إضافة مصروف جديد")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumSize(500, 500)

        self.setStyleSheet(f"""
            QDialog {{ background-color: {Theme.color('bg')}; }}
            QLabel {{ color: {Theme.color('text')}; background: transparent; font-size: 11pt; }}
            QLabel#title {{
                color: {Theme.color('primary')};
                font-size: 18px;
                font-weight: bold;
                padding: 8px;
            }}
            QLineEdit, QComboBox, QDateEdit, QTextEdit, QDoubleSpinBox {{
                background-color: {Theme.color('surface')};
                color: {Theme.color('text')};
                border: 1px solid {Theme.color('border_strong')};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 11pt;
                min-height: 24px;
            }}
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus,
            QTextEdit:focus, QDoubleSpinBox:focus {{
                border: 2px solid {Theme.color('primary')};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("💼  إضافة مصروف جديد")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight)

        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.addItems([
            "إيجار", "كهرباء", "مياه", "غاز", "إنترنت",
            "رواتب", "صيانة", "تسويق", "شراء مستلزمات",
            "نظافة", "مواصلات", "أخرى"
        ])
        form.addRow("📂  الفئة *", self.category_combo)

        self.description_entry = QLineEdit()
        self.description_entry.setPlaceholderText("مثال: فاتورة كهرباء شهر سبتمبر")
        form.addRow("📝  الوصف", self.description_entry)

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, 10000000)
        self.amount_spin.setSuffix(" ج.م")
        self.amount_spin.setDecimals(2)
        self.amount_spin.setValue(100)
        form.addRow("💰  المبلغ *", self.amount_spin)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(QDate.currentDate())
        form.addRow("📅  التاريخ", self.date_edit)

        self.payment_combo = QComboBox()
        self.payment_combo.addItems(["كاش", "تحويل بنكي", "شيك", "كارت"])
        self.payment_combo.setEditable(True)
        form.addRow("💳  طريقة الدفع", self.payment_combo)

        self.receipt_entry = QLineEdit()
        self.receipt_entry.setPlaceholderText("رقم الفاتورة / الإيصال")
        form.addRow("🧾  رقم الإيصال", self.receipt_entry)

        self.notes_entry = QTextEdit()
        self.notes_entry.setPlaceholderText("ملاحظات...")
        self.notes_entry.setMaximumHeight(80)
        form.addRow("📋  ملاحظات", self.notes_entry)

        layout.addLayout(form)
        layout.addStretch()

        btns = QHBoxLayout()
        btns.setSpacing(10)

        save_btn = QPushButton("💾  حفظ")
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
        category = self.category_combo.currentText().strip()
        if not category:
            QMessageBox.warning(self, "خطأ", "الفئة مطلوبة")
            return

        amount = self.amount_spin.value()
        if amount <= 0:
            QMessageBox.warning(self, "خطأ", "المبلغ لازم يكون أكبر من صفر")
            return

        self.result_data = {
            "category": category,
            "description": self.description_entry.text().strip(),
            "amount": amount,
            "date": self.date_edit.date().toString("yyyy-MM-dd"),
            "payment_method": self.payment_combo.currentText().strip(),
            "receipt_number": self.receipt_entry.text().strip(),
            "notes": self.notes_entry.toPlainText().strip(),
        }
        self.accept()


# ============================================================
# Stat Card Helper
# ============================================================
def make_stat_card(title, value, color=None, border_color=None):
    """يبني بطاقة إحصائية."""
    if color is None:
        color = Theme.color("primary")
    if border_color is None:
        border_color = Theme.color("border")

    card = QFrame()
    card.setStyleSheet(
        f"QFrame {{ background-color: {Theme.color('surface')}; "
        f"border: 2px solid {border_color}; border-radius: 12px; }}"
    )
    card.setMinimumHeight(95)

    v = QVBoxLayout(card)
    v.setContentsMargins(14, 10, 14, 10)
    v.setSpacing(2)

    t = QLabel(title)
    t.setStyleSheet(
        f"color: {Theme.color('text_muted')}; font-size: 11px; "
        f"font-weight: bold; background: transparent;"
    )
    t.setAlignment(Qt.AlignCenter)
    v.addWidget(t)

    val = QLabel(value)
    val.setStyleSheet(
        f"color: {color}; font-size: 20px; "
        f"font-weight: bold; background: transparent;"
    )
    val.setAlignment(Qt.AlignCenter)
    v.addWidget(val)

    card._value_label = val
    return card


# ============================================================
# Tab 1: Dashboard
# ============================================================
class DashboardTab(QWidget):
    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(14)

        # ============================================
        # ملخص اليوم
        # ============================================
        today_title = QLabel("📅  ملخص اليوم")
        today_title.setStyleSheet(
            f"font-size: 16px; font-weight: bold; "
            f"color: {Theme.color('primary')}; padding: 4px; "
            f"background: transparent;"
        )
        layout.addWidget(today_title)

        today_row = QHBoxLayout()
        today_row.setSpacing(10)

        self.card_bookings_today = make_stat_card(
            "📅  حجوزات اليوم", "0",
            Theme.color("primary"), Theme.color("primary")
        )
        self.card_revenue_today = make_stat_card(
            "💰  إيرادات اليوم", "0 ج",
            Theme.color("success"), Theme.color("success")
        )
        self.card_expenses_today = make_stat_card(
            "💼  مصاريف اليوم", "0 ج",
            Theme.color("danger"), Theme.color("danger")
        )
        self.card_profit_today = make_stat_card(
            "📈  ربح اليوم", "0 ج",
            Theme.color("gold"), Theme.color("gold")
        )

        today_row.addWidget(self.card_bookings_today, 1)
        today_row.addWidget(self.card_revenue_today, 1)
        today_row.addWidget(self.card_expenses_today, 1)
        today_row.addWidget(self.card_profit_today, 1)
        layout.addLayout(today_row)

        # ============================================
        # ملخص الشهر
        # ============================================
        month_title = QLabel("📆  ملخص الشهر الحالي")
        month_title.setStyleSheet(
            f"font-size: 16px; font-weight: bold; "
            f"color: {Theme.color('primary')}; padding: 4px; "
            f"background: transparent;"
        )
        layout.addWidget(month_title)

        month_row = QHBoxLayout()
        month_row.setSpacing(10)

        self.card_revenue_month = make_stat_card("💰  إيرادات الشهر", "0 ج")
        self.card_expenses_month = make_stat_card("💼  مصاريف الشهر", "0 ج")
        self.card_salaries_month = make_stat_card("👥  رواتب الشهر", "0 ج")
        self.card_profit_month = make_stat_card("📈  ربح الشهر", "0 ج",
                                                 Theme.color("success"))

        month_row.addWidget(self.card_revenue_month, 1)
        month_row.addWidget(self.card_expenses_month, 1)
        month_row.addWidget(self.card_salaries_month, 1)
        month_row.addWidget(self.card_profit_month, 1)
        layout.addLayout(month_row)

        # ============================================
        # تنبيهات سريعة
        # ============================================
        alerts_title = QLabel("⚠️  تنبيهات سريعة")
        alerts_title.setStyleSheet(
            f"font-size: 16px; font-weight: bold; "
            f"color: {Theme.color('primary')}; padding: 4px; "
            f"background: transparent;"
        )
        layout.addWidget(alerts_title)

        alerts_row = QHBoxLayout()
        alerts_row.setSpacing(10)

        self.card_low_stock = make_stat_card(
            "📦  منتجات قرب تخلص", "0",
            Theme.color("danger"), Theme.color("danger")
        )
        self.card_expiring = make_stat_card(
            "📅  منتجات قرب تنتهي", "0",
            Theme.color("warning"), Theme.color("warning")
        )
        self.card_employees = make_stat_card(
            "👥  الموظفين النشطين", "0",
            Theme.color("info"), Theme.color("info")
        )
        self.card_attendance = make_stat_card(
            "✅  حضور اليوم", "0",
            Theme.color("success"), Theme.color("success")
        )

        alerts_row.addWidget(self.card_low_stock, 1)
        alerts_row.addWidget(self.card_expiring, 1)
        alerts_row.addWidget(self.card_employees, 1)
        alerts_row.addWidget(self.card_attendance, 1)
        layout.addLayout(alerts_row)

        # زر تحديث
        refresh_btn = QPushButton("🔄  تحديث البيانات")
        refresh_btn.setMinimumHeight(46)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('primary')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"font-size: 13px; font-weight: bold; padding: 10px 20px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('primary_hover')}; }}"
        )
        refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(refresh_btn)

        layout.addStretch()

    def refresh(self):
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            month_start = datetime.now().replace(day=1).strftime("%Y-%m-%d")
            month_end = today

            # ==== اليوم ====
            summary_today = self.db.get_today_summary()
            self.card_bookings_today._value_label.setText(
                str(summary_today["bookings_count"])
            )
            self.card_revenue_today._value_label.setText(
                f"{summary_today['bookings_revenue']:,.0f} ج"
            )
            self.card_expenses_today._value_label.setText(
                f"{summary_today['expenses']:,.0f} ج"
            )
            profit_today = (
                summary_today["bookings_revenue"] - summary_today["expenses"]
            )
            self.card_profit_today._value_label.setText(f"{profit_today:,.0f} ج")

            # ==== الشهر ====
            report = self.db.get_profit_loss_report(month_start, month_end)
            self.card_revenue_month._value_label.setText(
                f"{report['total_revenue']:,.0f} ج"
            )
            self.card_expenses_month._value_label.setText(
                f"{report['expenses']:,.0f} ج"
            )
            self.card_salaries_month._value_label.setText(
                f"{report['salaries']:,.0f} ج"
            )
            self.card_profit_month._value_label.setText(
                f"{report['profit']:,.0f} ج"
            )

            # ==== التنبيهات ====
            low_stock = self.db.get_low_stock_items()
            self.card_low_stock._value_label.setText(str(len(low_stock)))

            # منتجات قرب تنتهي
            try:
                items = self.db.list_inventory_items(active_only=True)
                cutoff = (datetime.now() + timedelta(days=30)).date()
                expiring = 0
                for i in items:
                    if i[13]:
                        try:
                            d = datetime.strptime(i[13], "%Y-%m-%d").date()
                            if d <= cutoff:
                                expiring += 1
                        except Exception:
                            pass
                self.card_expiring._value_label.setText(str(expiring))
            except Exception:
                pass

            # الموظفين النشطين
            employees = self.db.list_employees(active_only=True)
            self.card_employees._value_label.setText(str(len(employees)))

            # حضور اليوم
            today_att = self.db.get_today_attendance()
            att_count = sum(1 for a in today_att if a[3])  # check_in موجود
            self.card_attendance._value_label.setText(
                f"{att_count} / {len(today_att)}"
            )

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل البيانات:\n{e}")


# ============================================================
# Tab 2: المصاريف
# ============================================================
class ExpensesTab(QWidget):
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

        # الإحصائيات
        stats_row = QHBoxLayout()
        stats_row.setSpacing(8)

        self.stat_total = make_stat_card("💰  إجمالي المصاريف", "0 ج")
        self.stat_month = make_stat_card("📆  مصاريف الشهر", "0 ج")
        self.stat_count = make_stat_card("📊  عدد العمليات", "0")
        self.stat_avg = make_stat_card("📈  متوسط العملية", "0 ج")

        stats_row.addWidget(self.stat_total, 1)
        stats_row.addWidget(self.stat_month, 1)
        stats_row.addWidget(self.stat_count, 1)
        stats_row.addWidget(self.stat_avg, 1)
        layout.addLayout(stats_row)

        # الأزرار
        actions = QHBoxLayout()
        actions.setSpacing(8)

        add_btn = QPushButton("➕  إضافة مصروف")
        add_btn.setMinimumHeight(42)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('success')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"font-weight: bold; font-size: 12px; padding: 8px 16px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('success_hover')}; }}"
        )
        add_btn.clicked.connect(self._add_expense)
        actions.addWidget(add_btn)

        delete_btn = QPushButton("🗑️  حذف المختار")
        delete_btn.setMinimumHeight(42)
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('danger')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"font-weight: bold; font-size: 12px; padding: 8px 16px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('danger_hover')}; }}"
        )
        delete_btn.clicked.connect(self._delete_expense)
        actions.addWidget(delete_btn)

        # الفلترة
        actions.addWidget(QLabel("من:"))
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_from.setMinimumHeight(42)
        actions.addWidget(self.date_from)

        actions.addWidget(QLabel("إلى:"))
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        self.date_to.setMinimumHeight(42)
        actions.addWidget(self.date_to)

        apply_btn = QPushButton("🔍")
        apply_btn.setMinimumHeight(42)
        apply_btn.setMaximumWidth(50)
        apply_btn.setCursor(Qt.PointingHandCursor)
        apply_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('primary')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"font-weight: bold; font-size: 14px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('primary_hover')}; }}"
        )
        apply_btn.clicked.connect(self.refresh)
        actions.addWidget(apply_btn)

        actions.addStretch()
        layout.addLayout(actions)

        # الجدول
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "#", "التاريخ", "الفئة", "الوصف",
            "المبلغ", "طريقة الدفع", "رقم الإيصال"
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setLayoutDirection(Qt.RightToLeft)

        h = self.table.horizontalHeader()
        for i in range(7):
            if i in (2, 3):
                h.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                h.setSectionResizeMode(i, QHeaderView.Fixed)

        self.table.setColumnWidth(0, 45)
        self.table.setColumnWidth(1, 110)
        self.table.setColumnWidth(4, 130)
        self.table.setColumnWidth(5, 130)
        self.table.setColumnWidth(6, 140)

        layout.addWidget(self.table, stretch=1)

    def refresh(self):
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to = self.date_to.date().toString("yyyy-MM-dd")

        try:
            expenses = self.db.list_expenses(
                date_from=date_from, date_to=date_to
            )
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل التحميل:\n{e}")
            return

        # الإحصائيات
        total = sum(e[3] or 0 for e in expenses)
        count = len(expenses)
        avg = total / count if count > 0 else 0

        # الشهر الحالي
        month_start = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        month_total = sum(
            e[3] or 0 for e in expenses if e[4] >= month_start
        )

        self.stat_total._value_label.setText(f"{total:,.0f} ج")
        self.stat_month._value_label.setText(f"{month_total:,.0f} ج")
        self.stat_count._value_label.setText(str(count))
        self.stat_avg._value_label.setText(f"{avg:,.0f} ج")

        # الجدول
        self.table.setRowCount(len(expenses))
        text_color = QColor(Theme.color("text"))
        red = QColor(Theme.color("danger"))

        for row, e in enumerate(expenses):
            # e = (id, category, description, amount, date,
            #      payment_method, receipt_number, notes)

            self._add(row, 0, str(e[0]), text_color)
            self._add(row, 1, e[4], text_color)
            self._add(row, 2, e[1], text_color, bold=True)
            self._add(row, 3, e[2] or "—", text_color)
            self._add(row, 4, f"{e[3]:,.2f} ج", red, bold=True)
            self._add(row, 5, e[5] or "—", text_color)
            self._add(row, 6, e[6] or "—", text_color)

    def _add(self, row, col, text, color, bold=False):
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(Qt.AlignCenter)
        item.setForeground(color)
        if bold:
            f = QFont()
            f.setBold(True)
            item.setFont(f)
        self.table.setItem(row, col, item)

    def _add_expense(self):
        dlg = ExpenseDialog(self)
        if dlg.exec() != QDialog.Accepted or not dlg.result_data:
            return

        try:
            self.db.add_expense(**dlg.result_data)
            QMessageBox.information(self, "تم", "✅ تم إضافة المصروف.")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل الإضافة:\n{e}")

    def _delete_expense(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.warning(self, "تنبيه", "اختار مصروف.")
            return

        row = rows[0].row()
        item = self.table.item(row, 0)
        if not item:
            return

        expense_id = int(item.text())

        reply = QMessageBox.question(
            self, "تأكيد", "متأكد إنك عايز تحذف المصروف ده؟",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        try:
            self.db.delete_expense(expense_id)
            QMessageBox.information(self, "تم", "✅ تم الحذف.")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل الحذف:\n{e}")


# ============================================================
# Tab 3: الأرباح والخسائر
# ============================================================
class ProfitLossTab(QWidget):
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
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(16, 14, 16, 14)
        filter_layout.setSpacing(10)

        filter_layout.addWidget(QLabel("📅  من:"))
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_from.setMinimumHeight(40)
        filter_layout.addWidget(self.date_from)

        filter_layout.addWidget(QLabel("إلى:"))
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        self.date_to.setMinimumHeight(40)
        filter_layout.addWidget(self.date_to)

        # أزرار سريعة
        today_btn = QPushButton("اليوم")
        today_btn.setMinimumHeight(40)
        today_btn.setCursor(Qt.PointingHandCursor)
        today_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('surface_alt')}; "
            f"color: {Theme.color('text')}; border: none; border-radius: 6px; "
            f"font-weight: bold; padding: 6px 14px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('border_strong')}; }}"
        )
        today_btn.clicked.connect(lambda: self._quick_range(0))
        filter_layout.addWidget(today_btn)

        week_btn = QPushButton("أسبوع")
        week_btn.setMinimumHeight(40)
        week_btn.setCursor(Qt.PointingHandCursor)
        week_btn.setStyleSheet(today_btn.styleSheet())
        week_btn.clicked.connect(lambda: self._quick_range(7))
        filter_layout.addWidget(week_btn)

        month_btn = QPushButton("شهر")
        month_btn.setMinimumHeight(40)
        month_btn.setCursor(Qt.PointingHandCursor)
        month_btn.setStyleSheet(today_btn.styleSheet())
        month_btn.clicked.connect(lambda: self._quick_range(30))
        filter_layout.addWidget(month_btn)

        year_btn = QPushButton("سنة")
        year_btn.setMinimumHeight(40)
        year_btn.setCursor(Qt.PointingHandCursor)
        year_btn.setStyleSheet(today_btn.styleSheet())
        year_btn.clicked.connect(lambda: self._quick_range(365))
        filter_layout.addWidget(year_btn)

        apply_btn = QPushButton("🔍  تطبيق")
        apply_btn.setMinimumHeight(40)
        apply_btn.setCursor(Qt.PointingHandCursor)
        apply_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('primary')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"font-weight: bold; padding: 6px 16px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('primary_hover')}; }}"
        )
        apply_btn.clicked.connect(self.refresh)
        filter_layout.addWidget(apply_btn)

        filter_layout.addStretch()
        layout.addWidget(filter_frame)

        # ============================================
        # بطاقات الملخص
        # ============================================
        summary_grid = QGridLayout()
        summary_grid.setSpacing(10)

        self.card_revenue = make_stat_card("💰  إجمالي الإيرادات", "0 ج",
                                            Theme.color("success"),
                                            Theme.color("success"))
        self.card_expenses = make_stat_card("💼  المصاريف", "0 ج",
                                             Theme.color("danger"),
                                             Theme.color("danger"))
        self.card_salaries = make_stat_card("👥  الرواتب", "0 ج",
                                             Theme.color("warning"),
                                             Theme.color("warning"))
        self.card_profit = make_stat_card("📈  صافي الربح", "0 ج",
                                           Theme.color("gold"),
                                           Theme.color("gold"))

        summary_grid.addWidget(self.card_revenue, 0, 0)
        summary_grid.addWidget(self.card_expenses, 0, 1)
        summary_grid.addWidget(self.card_salaries, 1, 0)
        summary_grid.addWidget(self.card_profit, 1, 1)

        layout.addLayout(summary_grid)

        # ============================================
        # تفصيل التقرير
        # ============================================
        detail_frame = QFrame()
        detail_frame.setStyleSheet(
            f"QFrame {{ background-color: {Theme.color('surface')}; "
            f"border: 1px solid {Theme.color('border')}; border-radius: 10px; }}"
        )
        detail_layout = QVBoxLayout(detail_frame)
        detail_layout.setContentsMargins(20, 16, 20, 16)
        detail_layout.setSpacing(10)

        detail_title = QLabel("📊  تفصيل التقرير")
        detail_title.setStyleSheet(
            f"color: {Theme.color('primary')}; font-size: 15px; "
            f"font-weight: bold; background: transparent;"
        )
        detail_layout.addWidget(detail_title)

        self.detail_label = QLabel("— اضغط تطبيق لتحميل التقرير —")
        self.detail_label.setStyleSheet(
            f"color: {Theme.color('text')}; font-size: 12px; "
            f"background: {Theme.color('surface_alt')}; "
            f"padding: 16px; border-radius: 8px; "
            f"font-family: 'Consolas', monospace;"
        )
        self.detail_label.setWordWrap(True)
        detail_layout.addWidget(self.detail_label)

        layout.addWidget(detail_frame)
        layout.addStretch()

    def _quick_range(self, days):
        today = datetime.now()
        self.date_from.setDate(QDate(today.year, today.month, today.day).addDays(-days))
        self.date_to.setDate(QDate.currentDate())
        self.refresh()

    def refresh(self):
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to = self.date_to.date().toString("yyyy-MM-dd")

        try:
            report = self.db.get_profit_loss_report(date_from, date_to)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل التقرير:\n{e}")
            return

        # البطاقات
        self.card_revenue._value_label.setText(
            f"{report['total_revenue']:,.0f} ج"
        )
        self.card_expenses._value_label.setText(
            f"{report['expenses']:,.0f} ج"
        )
        self.card_salaries._value_label.setText(
            f"{report['salaries']:,.0f} ج"
        )
        self.card_profit._value_label.setText(
            f"{report['profit']:,.0f} ج"
        )

        # التفاصيل
        detail = (
            f"📅  الفترة: {date_from}  →  {date_to}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💰  الإيرادات:\n"
            f"   • حجوزات:      {report['bookings_revenue']:>12,.2f} ج\n"
            f"   • أخرى:        {report['other_revenue']:>12,.2f} ج\n"
            f"   ─────────────────────────────\n"
            f"   • الإجمالي:    {report['total_revenue']:>12,.2f} ج\n\n"
            f"💸  التكاليف:\n"
            f"   • مصاريف:      {report['expenses']:>12,.2f} ج\n"
            f"   • رواتب:       {report['salaries']:>12,.2f} ج\n"
            f"   ─────────────────────────────\n"
            f"   • الإجمالي:    {report['total_costs']:>12,.2f} ج\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📈  صافي الربح:    {report['profit']:>12,.2f} ج\n"
            f"📊  هامش الربح:     {report['margin']:>11,.2f} %"
        )
        self.detail_label.setText(detail)


# ============================================================
# Tab 4: التحليلات
# ============================================================
class AnalyticsTab(QWidget):
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
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(16, 14, 16, 14)
        filter_layout.setSpacing(10)

        filter_layout.addWidget(QLabel("📅  من:"))
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_from.setMinimumHeight(40)
        filter_layout.addWidget(self.date_from)

        filter_layout.addWidget(QLabel("إلى:"))
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        self.date_to.setMinimumHeight(40)
        filter_layout.addWidget(self.date_to)

        apply_btn = QPushButton("🔍  تحديث التحليلات")
        apply_btn.setMinimumHeight(40)
        apply_btn.setCursor(Qt.PointingHandCursor)
        apply_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('primary')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"font-weight: bold; padding: 6px 16px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('primary_hover')}; }}"
        )
        apply_btn.clicked.connect(self.refresh)
        filter_layout.addWidget(apply_btn)

        filter_layout.addStretch()
        layout.addWidget(filter_frame)

        # جدول المصاريف حسب الفئة
        cat_title = QLabel("💼  المصاريف حسب الفئة")
        cat_title.setStyleSheet(
            f"font-size: 14px; font-weight: bold; "
            f"color: {Theme.color('primary')}; padding: 4px; "
            f"background: transparent;"
        )
        layout.addWidget(cat_title)

        self.cat_table = QTableWidget()
        self.cat_table.setColumnCount(4)
        self.cat_table.setHorizontalHeaderLabels([
            "الفئة", "عدد العمليات", "إجمالي المصاريف", "النسبة %"
        ])
        self.cat_table.verticalHeader().setVisible(False)
        self.cat_table.setAlternatingRowColors(True)
        self.cat_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.cat_table.setShowGrid(False)
        self.cat_table.setLayoutDirection(Qt.RightToLeft)

        h = self.cat_table.horizontalHeader()
        for i in range(4):
            h.setSectionResizeMode(i, QHeaderView.Stretch)

        layout.addWidget(self.cat_table, stretch=1)

    def refresh(self):
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to = self.date_to.date().toString("yyyy-MM-dd")

        try:
            expenses = self.db.list_expenses(
                date_from=date_from, date_to=date_to
            )
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل التحميل:\n{e}")
            return

        # اجمع حسب الفئة
        by_cat = {}
        total = 0
        for e in expenses:
            cat = e[1] or "أخرى"
            amount = e[3] or 0
            if cat not in by_cat:
                by_cat[cat] = {"count": 0, "total": 0}
            by_cat[cat]["count"] += 1
            by_cat[cat]["total"] += amount
            total += amount

        # رتّب تنازليًا
        sorted_cats = sorted(
            by_cat.items(), key=lambda x: x[1]["total"], reverse=True
        )

        self.cat_table.setRowCount(len(sorted_cats))
        text_color = QColor(Theme.color("text"))
        red = QColor(Theme.color("danger"))
        gold = QColor(Theme.color("gold"))

        for row, (cat, data) in enumerate(sorted_cats):
            pct = (data["total"] / total * 100) if total > 0 else 0

            self._add(row, 0, cat, text_color, bold=True)
            self._add(row, 1, str(data["count"]), text_color)
            self._add(row, 2, f"{data['total']:,.2f} ج", red, bold=True)
            self._add(row, 3, f"{pct:.1f}%", gold)

    def _add(self, row, col, text, color, bold=False):
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(Qt.AlignCenter)
        item.setForeground(color)
        if bold:
            f = QFont()
            f.setBold(True)
            item.setFont(f)
        self.cat_table.setItem(row, col, item)


# ============================================================
# Main Tab — Management Tab
# ============================================================
class ManagementTab(QWidget):
    """التاب الرئيسي للإدارة — بيجمع 4 تابات داخلية."""

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
        title = QLabel("💼  الإدارة والمالية")
        title.setStyleSheet(
            f"font-size: 22px; font-weight: bold; "
            f"color: {Theme.color('primary')}; padding: 4px; "
            f"background: transparent;"
        )
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # التابات
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

        self.tab_dashboard = DashboardTab(self.db, self.user)
        self.sub_tabs.addTab(self.tab_dashboard, "  📊  Dashboard  ")

        self.tab_expenses = ExpensesTab(self.db, self.user)
        self.sub_tabs.addTab(self.tab_expenses, "  💼  المصاريف  ")

        self.tab_pl = ProfitLossTab(self.db, self.user)
        self.sub_tabs.addTab(self.tab_pl, "  💰  الأرباح والخسائر  ")

        self.tab_analytics = AnalyticsTab(self.db, self.user)
        self.sub_tabs.addTab(self.tab_analytics, "  📈  التحليلات  ")

        layout.addWidget(self.sub_tabs, stretch=1)

        self.sub_tabs.currentChanged.connect(self._on_tab_changed)

    def _on_tab_changed(self, index):
        try:
            tab = self.sub_tabs.widget(index)
            if hasattr(tab, "refresh"):
                tab.refresh()
        except Exception:
            pass

    def refresh(self):
        try:
            current = self.sub_tabs.currentWidget()
            if hasattr(current, "refresh"):
                current.refresh()
        except Exception:
            pass