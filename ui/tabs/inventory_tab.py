"""
Inventory Tab — تاب المخزون الكامل.
================================================
5 تابات داخلية:
    1) 📦 المنتجات       — إضافة/تعديل/حذف
    2) 📥 الوارد          — تسجيل كميات جديدة
    3) 📤 الصادر          — استهلاك/مبيعات
    4) ⚠️ التنبيهات       — منتجات قرب تخلص
    5) 📊 تقارير المخزون  — القيمة والأرباح
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
# Dialog — إضافة/تعديل منتج
# ============================================================
class ItemDialog(QDialog):
    """نافذة إضافة أو تعديل منتج."""

    def __init__(self, parent=None, item=None, categories=None):
        super().__init__(parent)
        self.item = item
        self.categories = categories or []
        self.result_data = None

        is_edit = item is not None
        self.setWindowTitle("تعديل منتج" if is_edit else "إضافة منتج جديد")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumSize(600, 650)

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

        title = QLabel("✏️  تعديل منتج" if is_edit else "➕  إضافة منتج جديد")
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

        # ============================================
        # القسم الأول: البيانات الأساسية
        # ============================================
        sec1 = QFrame()
        sec1.setObjectName("section")
        sec1_layout = QFormLayout(sec1)
        sec1_layout.setContentsMargins(16, 14, 16, 14)
        sec1_layout.setSpacing(10)
        sec1_layout.setLabelAlignment(Qt.AlignRight)

        self.name_entry = QLineEdit()
        self.name_entry.setPlaceholderText("مثال: جل حلاقة")
        if is_edit:
            self.name_entry.setText(item[1] or "")
        sec1_layout.addRow("📦  اسم المنتج *", self.name_entry)

        self.barcode_entry = QLineEdit()
        self.barcode_entry.setPlaceholderText("اختياري")
        if is_edit:
            self.barcode_entry.setText(item[2] or "")
        sec1_layout.addRow("🏷️  الباركود", self.barcode_entry)

        self.category_combo = QComboBox()
        self.category_combo.addItem("— بدون فئة —", None)
        for cat in self.categories:
            # cat = (id, name, color, icon)
            self.category_combo.addItem(f"{cat[3]}  {cat[1]}", cat[0])
        if is_edit and item[3]:
            for i in range(self.category_combo.count()):
                if self.category_combo.itemData(i) == item[3]:
                    self.category_combo.setCurrentIndex(i)
                    break
        sec1_layout.addRow("📂  الفئة", self.category_combo)

        vbox.addWidget(sec1)

        # ============================================
        # القسم الثاني: الكمية والوحدة
        # ============================================
        sec2 = QFrame()
        sec2.setObjectName("section")
        sec2_layout = QFormLayout(sec2)
        sec2_layout.setContentsMargins(16, 14, 16, 14)
        sec2_layout.setSpacing(10)
        sec2_layout.setLabelAlignment(Qt.AlignRight)

        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setRange(0, 1000000)
        self.quantity_spin.setDecimals(2)
        if is_edit:
            self.quantity_spin.setValue(float(item[7] or 0))
        sec2_layout.addRow("🔢  الكمية الحالية", self.quantity_spin)

        self.unit_combo = QComboBox()
        self.unit_combo.addItems([
            "قطعة", "علبة", "كيلو", "جرام", "لتر",
            "مل", "أنبوبة", "كرتونة", "دستة"
        ])
        self.unit_combo.setEditable(True)
        if is_edit and item[8]:
            self.unit_combo.setCurrentText(item[8])
        sec2_layout.addRow("⚖️  الوحدة", self.unit_combo)

        self.min_qty_spin = QDoubleSpinBox()
        self.min_qty_spin.setRange(0, 1000000)
        self.min_qty_spin.setDecimals(2)
        self.min_qty_spin.setValue(5)
        if is_edit:
            self.min_qty_spin.setValue(float(item[9] or 5))
        sec2_layout.addRow("⚠️  الحد الأدنى (للتنبيه)", self.min_qty_spin)

        vbox.addWidget(sec2)

        # ============================================
        # القسم الثالث: الأسعار
        # ============================================
        sec3 = QFrame()
        sec3.setObjectName("section")
        sec3_layout = QFormLayout(sec3)
        sec3_layout.setContentsMargins(16, 14, 16, 14)
        sec3_layout.setSpacing(10)
        sec3_layout.setLabelAlignment(Qt.AlignRight)

        self.purchase_spin = QDoubleSpinBox()
        self.purchase_spin.setRange(0, 1000000)
        self.purchase_spin.setSuffix(" ج.م")
        self.purchase_spin.setDecimals(2)
        if is_edit:
            self.purchase_spin.setValue(float(item[10] or 0))
        sec3_layout.addRow("💰  سعر الشراء", self.purchase_spin)

        self.selling_spin = QDoubleSpinBox()
        self.selling_spin.setRange(0, 1000000)
        self.selling_spin.setSuffix(" ج.م")
        self.selling_spin.setDecimals(2)
        if is_edit:
            self.selling_spin.setValue(float(item[11] or 0))
        sec3_layout.addRow("🏷️  سعر البيع", self.selling_spin)

        vbox.addWidget(sec3)

        # ============================================
        # القسم الرابع: معلومات إضافية
        # ============================================
        sec4 = QFrame()
        sec4.setObjectName("section")
        sec4_layout = QFormLayout(sec4)
        sec4_layout.setContentsMargins(16, 14, 16, 14)
        sec4_layout.setSpacing(10)
        sec4_layout.setLabelAlignment(Qt.AlignRight)

        self.supplier_entry = QLineEdit()
        self.supplier_entry.setPlaceholderText("اسم المورد (اختياري)")
        if is_edit:
            self.supplier_entry.setText(item[12] or "")
        sec4_layout.addRow("🏭  المورد", self.supplier_entry)

        self.expiry_check = QComboBox()
        self.expiry_check.addItems(["لا يوجد", "يوجد تاريخ صلاحية"])
        self.expiry_check.currentIndexChanged.connect(self._toggle_expiry)
        sec4_layout.addRow("📅  تاريخ الصلاحية", self.expiry_check)

        self.expiry_date = QDateEdit()
        self.expiry_date.setCalendarPopup(True)
        self.expiry_date.setDisplayFormat("yyyy-MM-dd")
        self.expiry_date.setDate(QDate.currentDate().addMonths(6))
        self.expiry_date.setVisible(False)
        if is_edit and item[13]:
            try:
                d = datetime.strptime(item[13], "%Y-%m-%d").date()
                self.expiry_date.setDate(QDate(d.year, d.month, d.day))
                self.expiry_check.setCurrentIndex(1)
                self.expiry_date.setVisible(True)
            except Exception:
                pass
        sec4_layout.addRow("", self.expiry_date)

        self.notes_entry = QTextEdit()
        self.notes_entry.setPlaceholderText("ملاحظات...")
        self.notes_entry.setMaximumHeight(80)
        if is_edit:
            self.notes_entry.setPlainText(item[15] or "")
        sec4_layout.addRow("📝  ملاحظات", self.notes_entry)

        vbox.addWidget(sec4)
        vbox.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)

        # الأزرار
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

    def _toggle_expiry(self, idx):
        self.expiry_date.setVisible(idx == 1)

    def _save(self):
        name = self.name_entry.text().strip()
        if not name:
            QMessageBox.warning(self, "خطأ", "اسم المنتج مطلوب")
            return

        expiry = None
        if self.expiry_check.currentIndex() == 1:
            expiry = self.expiry_date.date().toString("yyyy-MM-dd")

        self.result_data = {
            "name": name,
            "barcode": self.barcode_entry.text().strip() or None,
            "category_id": self.category_combo.currentData(),
            "quantity": self.quantity_spin.value(),
            "unit": self.unit_combo.currentText().strip(),
            "min_quantity": self.min_qty_spin.value(),
            "purchase_price": self.purchase_spin.value(),
            "selling_price": self.selling_spin.value(),
            "supplier": self.supplier_entry.text().strip(),
            "expiry_date": expiry,
            "notes": self.notes_entry.toPlainText().strip(),
        }
        self.accept()


# ============================================================
# Tab 1: المنتجات
# ============================================================
class ItemsTab(QWidget):
    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user
        self.can_edit = user.is_admin or user.has_permission("edit_inventory")
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(12)

        # الإحصائيات
        stats_row = QHBoxLayout()
        stats_row.setSpacing(8)

        self.stat_total = self._make_stat_card("📦  إجمالي المنتجات", "0")
        self.stat_low = self._make_stat_card("⚠️  قرب تخلص", "0")
        self.stat_value = self._make_stat_card("💰  قيمة المخزون", "0 ج")
        self.stat_profit = self._make_stat_card("📈  الربح المتوقع", "0 ج")

        stats_row.addWidget(self.stat_total, 1)
        stats_row.addWidget(self.stat_low, 1)
        stats_row.addWidget(self.stat_value, 1)
        stats_row.addWidget(self.stat_profit, 1)
        layout.addLayout(stats_row)

        # الأزرار
        actions = QHBoxLayout()
        actions.setSpacing(8)

        if self.can_edit:
            add_btn = QPushButton("➕  إضافة منتج")
            add_btn.setMinimumHeight(42)
            add_btn.setCursor(Qt.PointingHandCursor)
            add_btn.setStyleSheet(
                f"QPushButton {{ background-color: {Theme.color('success')}; "
                f"color: white; border: none; border-radius: 8px; "
                f"font-weight: bold; font-size: 12px; padding: 8px 16px; }}"
                f"QPushButton:hover {{ background-color: {Theme.color('success_hover')}; }}"
            )
            add_btn.clicked.connect(self._add_item)
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
            edit_btn.clicked.connect(self._edit_item)
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
            delete_btn.clicked.connect(self._delete_item)
            actions.addWidget(delete_btn)

        # البحث والفلترة
        search = QLineEdit()
        search.setPlaceholderText("🔍  ابحث بالاسم أو الباركود...")
        search.setMinimumHeight(42)
        search.textChanged.connect(self.refresh)
        self.search_input = search
        actions.addWidget(search, 1)

        cat_filter = QComboBox()
        cat_filter.setMinimumHeight(42)
        cat_filter.setMinimumWidth(180)
        cat_filter.addItem("كل الفئات", None)
        self.cat_filter = cat_filter
        self.cat_filter.currentIndexChanged.connect(self.refresh)
        actions.addWidget(cat_filter)

        refresh_btn = QPushButton("🔄")
        refresh_btn.setMinimumHeight(42)
        refresh_btn.setMaximumWidth(60)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('surface_alt')}; "
            f"color: {Theme.color('text')}; border: none; border-radius: 8px; "
            f"font-weight: bold; font-size: 14px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('border_strong')}; }}"
        )
        refresh_btn.clicked.connect(self.refresh)
        actions.addWidget(refresh_btn)

        layout.addLayout(actions)

        # الجدول
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "#", "المنتج", "الفئة", "الكمية", "الوحدة",
            "شراء", "بيع", "الربح/وحدة", "الحالة", "المورد"
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setLayoutDirection(Qt.RightToLeft)
        self.table.doubleClicked.connect(self._edit_item)

        h = self.table.horizontalHeader()
        for i in range(10):
            if i in (1, 9):
                h.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                h.setSectionResizeMode(i, QHeaderView.Fixed)

        self.table.setColumnWidth(0, 45)
        self.table.setColumnWidth(2, 130)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 80)
        self.table.setColumnWidth(5, 90)
        self.table.setColumnWidth(6, 90)
        self.table.setColumnWidth(7, 100)
        self.table.setColumnWidth(8, 110)

        layout.addWidget(self.table, stretch=1)

    def _make_stat_card(self, title, value):
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background-color: {Theme.color('surface')}; "
            f"border: 1px solid {Theme.color('border')}; border-radius: 10px; }}"
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
        # حدّث فلتر الفئات
        try:
            categories = self.db.list_inventory_categories()
        except Exception:
            categories = []

        current = self.cat_filter.currentData()
        self.cat_filter.blockSignals(True)
        self.cat_filter.clear()
        self.cat_filter.addItem("كل الفئات", None)
        for cat in categories:
            self.cat_filter.addItem(f"{cat[3]}  {cat[1]}", cat[0])
        if current:
            for i in range(self.cat_filter.count()):
                if self.cat_filter.itemData(i) == current:
                    self.cat_filter.setCurrentIndex(i)
                    break
        self.cat_filter.blockSignals(False)

        # اجلب المنتجات
        cat_id = self.cat_filter.currentData()
        try:
            items = self.db.list_inventory_items(category_id=cat_id)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل التحميل:\n{e}")
            return

        # فلترة بالبحث
        q = self.search_input.text().strip().lower()
        if q:
            items = [
                i for i in items
                if q in (i[1] or "").lower() or q in (i[2] or "").lower()
            ]

        # الإحصائيات
        low_count = sum(1 for i in items if (i[7] or 0) <= (i[9] or 0))
        total_cost = sum((i[7] or 0) * (i[10] or 0) for i in items)
        total_profit = sum(
            (i[7] or 0) * ((i[11] or 0) - (i[10] or 0)) for i in items
        )

        self.stat_total._value_label.setText(str(len(items)))
        self.stat_low._value_label.setText(str(low_count))
        self.stat_value._value_label.setText(f"{total_cost:,.0f} ج")
        self.stat_profit._value_label.setText(f"{total_profit:,.0f} ج")

        # الجدول
        self.table.setRowCount(len(items))
        text_color = QColor(Theme.color("text"))
        green = QColor(Theme.color("success"))
        red = QColor(Theme.color("danger"))
        gold = QColor(Theme.color("gold"))
        gray = QColor(Theme.color("text_dim"))

        for row, i in enumerate(items):
            # i = (id, name, barcode, cat_id, cat_name, cat_color,
            #      cat_icon, quantity, unit, min_quantity,
            #      purchase, selling, supplier, expiry, is_active, notes)

            item_id = QTableWidgetItem(str(i[0]))
            item_id.setTextAlignment(Qt.AlignCenter)
            item_id.setData(Qt.UserRole, i[0])
            item_id.setForeground(text_color)
            self.table.setItem(row, 0, item_id)

            self._add(row, 1, i[1] or "", text_color, bold=True)

            cat_text = f"{i[6] or ''}  {i[4] or '—'}"
            self._add(row, 2, cat_text, text_color)

            # الكمية
            qty = i[7] or 0
            min_qty = i[9] or 0
            qty_color = red if qty <= min_qty else green
            self._add(row, 3, f"{qty:g}", qty_color, bold=True)
            self._add(row, 4, i[8] or "", text_color)
            self._add(row, 5, f"{i[10] or 0:,.0f}", text_color)
            self._add(row, 6, f"{i[11] or 0:,.0f}", text_color)

            # الربح
            profit = (i[11] or 0) - (i[10] or 0)
            profit_color = green if profit > 0 else red
            self._add(row, 7, f"{profit:,.0f}", profit_color)

            # الحالة
            if qty <= 0:
                status, sc = "❌  خلص", red
            elif qty <= min_qty:
                status, sc = "⚠️  قرب تخلص", gold
            else:
                status, sc = "✅  متوفر", green
            self._add(row, 8, status, sc, bold=True)

            self._add(row, 9, i[12] or "—", text_color)

    def _add(self, row, col, text, color, bold=False):
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(Qt.AlignCenter)
        item.setForeground(color)
        if bold:
            f = QFont()
            f.setBold(True)
            item.setFont(f)
        self.table.setItem(row, col, item)

    def _get_selected_id(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        item = self.table.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    def _add_item(self):
        if not self.can_edit:
            return
        try:
            categories = self.db.list_inventory_categories()
        except Exception:
            categories = []

        dlg = ItemDialog(self, item=None, categories=categories)
        if dlg.exec() != QDialog.Accepted or not dlg.result_data:
            return

        try:
            new_id = self.db.add_inventory_item(**dlg.result_data)
            if new_id:
                QMessageBox.information(self, "تم", "✅ تم إضافة المنتج.")
            else:
                QMessageBox.warning(self, "خطأ", "الباركود مكرر.")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل الإضافة:\n{e}")

    def _edit_item(self):
        if not self.can_edit:
            return
        item_id = self._get_selected_id()
        if item_id is None:
            QMessageBox.warning(self, "تنبيه", "اختار منتج من الجدول.")
            return

        try:
            item = self.db.get_inventory_item(item_id)
            categories = self.db.list_inventory_categories()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل التحميل:\n{e}")
            return

        if not item:
            return

        dlg = ItemDialog(self, item=item, categories=categories)
        if dlg.exec() != QDialog.Accepted or not dlg.result_data:
            return

        try:
            self.db.update_inventory_item(item_id, **dlg.result_data)
            QMessageBox.information(self, "تم", "✅ تم التحديث.")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل التحديث:\n{e}")

    def _delete_item(self):
        if not self.can_edit:
            return
        item_id = self._get_selected_id()
        if item_id is None:
            QMessageBox.warning(self, "تنبيه", "اختار منتج من الجدول.")
            return

        item = self.db.get_inventory_item(item_id)
        if not item:
            return

        reply = QMessageBox.question(
            self, "تأكيد الحذف",
            f"متأكد إنك عايز تحذف:\n\n📦  {item[1]}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        try:
            self.db.delete_inventory_item(item_id)
            QMessageBox.information(self, "تم", "✅ تم الحذف.")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل الحذف:\n{e}")


# ============================================================
# Tab 2: الوارد
# ============================================================
class StockInTab(QWidget):
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

        # إضافة وارد
        add_frame = QFrame()
        add_frame.setStyleSheet(
            f"QFrame {{ background-color: {Theme.color('surface')}; "
            f"border: 1px solid {Theme.color('success')}; border-radius: 10px; }}"
        )
        add_layout = QVBoxLayout(add_frame)
        add_layout.setContentsMargins(16, 14, 16, 14)
        add_layout.setSpacing(10)

        title = QLabel("📥  تسجيل وارد جديد")
        title.setStyleSheet(
            f"color: {Theme.color('success')}; font-size: 14px; "
            f"font-weight: bold; background: transparent;"
        )
        add_layout.addWidget(title)

        row = QHBoxLayout()
        row.setSpacing(8)

        row.addWidget(QLabel("المنتج:"))
        self.item_combo = QComboBox()
        self.item_combo.setMinimumHeight(42)
        self.item_combo.setMinimumWidth(250)
        row.addWidget(self.item_combo)

        row.addWidget(QLabel("الكمية:"))
        self.qty_spin = QDoubleSpinBox()
        self.qty_spin.setRange(0.01, 100000)
        self.qty_spin.setValue(1)
        self.qty_spin.setMinimumHeight(42)
        row.addWidget(self.qty_spin)

        row.addWidget(QLabel("سعر الوحدة:"))
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 100000)
        self.price_spin.setSuffix(" ج")
        self.price_spin.setMinimumHeight(42)
        row.addWidget(self.price_spin)

        row.addWidget(QLabel("السبب:"))
        self.reason_entry = QLineEdit()
        self.reason_entry.setPlaceholderText("شراء جديد / مرتجع...")
        self.reason_entry.setMinimumHeight(42)
        row.addWidget(self.reason_entry, 1)

        add_btn = QPushButton("📥  تسجيل")
        add_btn.setMinimumHeight(42)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('success')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"font-weight: bold; padding: 8px 20px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('success_hover')}; }}"
        )
        add_btn.clicked.connect(self._add_movement)
        row.addWidget(add_btn)

        add_layout.addLayout(row)
        layout.addWidget(add_frame)

        # الجدول
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "#", "التاريخ", "المنتج", "الكمية",
            "سعر الوحدة", "الإجمالي", "السبب"
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setLayoutDirection(Qt.RightToLeft)

        h = self.table.horizontalHeader()
        for i in range(7):
            if i in (2, 6):
                h.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                h.setSectionResizeMode(i, QHeaderView.Fixed)

        self.table.setColumnWidth(0, 45)
        self.table.setColumnWidth(1, 110)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(5, 130)

        layout.addWidget(self.table, stretch=1)

    def refresh(self):
        # حدّث قائمة المنتجات
        try:
            items = self.db.list_inventory_items(active_only=True)
        except Exception:
            items = []

        current = self.item_combo.currentData()
        self.item_combo.clear()
        for i in items:
            self.item_combo.addItem(
                f"{i[1]}  (متاح: {i[7] or 0:g} {i[8] or ''})", i[0]
            )
        if current:
            for idx in range(self.item_combo.count()):
                if self.item_combo.itemData(idx) == current:
                    self.item_combo.setCurrentIndex(idx)
                    break

        # الجدول
        try:
            movements = self.db.list_inventory_movements(movement_type="in")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل التحميل:\n{e}")
            return

        self.table.setRowCount(len(movements))
        text_color = QColor(Theme.color("text"))
        green = QColor(Theme.color("success"))

        for row, m in enumerate(movements):
            # m = (id, item_id, item_name, type, quantity,
            #      unit_price, total_price, reason, ref, date, notes)

            self._add(row, 0, str(m[0]), text_color)
            self._add(row, 1, m[9], text_color)
            self._add(row, 2, m[2], text_color, bold=True)
            self._add(row, 3, f"+ {m[4]:g}", green, bold=True)
            self._add(row, 4, f"{m[5]:,.2f} ج", text_color)
            self._add(row, 5, f"{m[6]:,.2f} ج", green, bold=True)
            self._add(row, 6, m[7] or "—", text_color)

    def _add(self, row, col, text, color, bold=False):
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(Qt.AlignCenter)
        item.setForeground(color)
        if bold:
            f = QFont()
            f.setBold(True)
            item.setFont(f)
        self.table.setItem(row, col, item)

    def _add_movement(self):
        item_id = self.item_combo.currentData()
        if not item_id:
            QMessageBox.warning(self, "تنبيه", "اختار منتج.")
            return

        qty = self.qty_spin.value()
        if qty <= 0:
            QMessageBox.warning(self, "تنبيه", "الكمية لازم أكبر من صفر.")
            return

        try:
            ok, msg = self.db.add_inventory_movement(
                item_id, "in", qty,
                unit_price=self.price_spin.value(),
                reason=self.reason_entry.text().strip() or "وارد"
            )
            if ok:
                QMessageBox.information(self, "تم", f"✅ {msg}")
                self.qty_spin.setValue(1)
                self.price_spin.setValue(0)
                self.reason_entry.clear()
                self.refresh()
            else:
                QMessageBox.warning(self, "تنبيه", msg)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل التسجيل:\n{e}")


# ============================================================
# Tab 3: الصادر
# ============================================================
class StockOutTab(QWidget):
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

        add_frame = QFrame()
        add_frame.setStyleSheet(
            f"QFrame {{ background-color: {Theme.color('surface')}; "
            f"border: 1px solid {Theme.color('danger')}; border-radius: 10px; }}"
        )
        add_layout = QVBoxLayout(add_frame)
        add_layout.setContentsMargins(16, 14, 16, 14)
        add_layout.setSpacing(10)

        title = QLabel("📤  تسجيل صادر جديد")
        title.setStyleSheet(
            f"color: {Theme.color('danger')}; font-size: 14px; "
            f"font-weight: bold; background: transparent;"
        )
        add_layout.addWidget(title)

        row = QHBoxLayout()
        row.setSpacing(8)

        row.addWidget(QLabel("المنتج:"))
        self.item_combo = QComboBox()
        self.item_combo.setMinimumHeight(42)
        self.item_combo.setMinimumWidth(250)
        row.addWidget(self.item_combo)

        row.addWidget(QLabel("الكمية:"))
        self.qty_spin = QDoubleSpinBox()
        self.qty_spin.setRange(0.01, 100000)
        self.qty_spin.setValue(1)
        self.qty_spin.setMinimumHeight(42)
        row.addWidget(self.qty_spin)

        row.addWidget(QLabel("السبب:"))
        self.reason_combo = QComboBox()
        self.reason_combo.setEditable(True)
        self.reason_combo.addItems([
            "استهلاك داخلي", "بيع", "تالف", "هدية", "مرتجع"
        ])
        self.reason_combo.setMinimumHeight(42)
        row.addWidget(self.reason_combo)

        row.addWidget(QLabel("ملاحظات:"))
        self.notes_entry = QLineEdit()
        self.notes_entry.setPlaceholderText("اختياري")
        self.notes_entry.setMinimumHeight(42)
        row.addWidget(self.notes_entry, 1)

        add_btn = QPushButton("📤  تسجيل")
        add_btn.setMinimumHeight(42)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('danger')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"font-weight: bold; padding: 8px 20px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('danger_hover')}; }}"
        )
        add_btn.clicked.connect(self._add_movement)
        row.addWidget(add_btn)

        add_layout.addLayout(row)
        layout.addWidget(add_frame)

        # الجدول
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "#", "التاريخ", "المنتج", "الكمية",
            "سعر الوحدة", "الإجمالي", "السبب"
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setLayoutDirection(Qt.RightToLeft)

        h = self.table.horizontalHeader()
        for i in range(7):
            if i in (2, 6):
                h.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                h.setSectionResizeMode(i, QHeaderView.Fixed)

        self.table.setColumnWidth(0, 45)
        self.table.setColumnWidth(1, 110)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(5, 130)

        layout.addWidget(self.table, stretch=1)

    def refresh(self):
        try:
            items = self.db.list_inventory_items(active_only=True)
        except Exception:
            items = []

        current = self.item_combo.currentData()
        self.item_combo.clear()
        for i in items:
            self.item_combo.addItem(
                f"{i[1]}  (متاح: {i[7] or 0:g} {i[8] or ''})", i[0]
            )
        if current:
            for idx in range(self.item_combo.count()):
                if self.item_combo.itemData(idx) == current:
                    self.item_combo.setCurrentIndex(idx)
                    break

        try:
            movements = self.db.list_inventory_movements(movement_type="out")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل التحميل:\n{e}")
            return

        self.table.setRowCount(len(movements))
        text_color = QColor(Theme.color("text"))
        red = QColor(Theme.color("danger"))

        for row, m in enumerate(movements):
            self._add(row, 0, str(m[0]), text_color)
            self._add(row, 1, m[9], text_color)
            self._add(row, 2, m[2], text_color, bold=True)
            self._add(row, 3, f"− {m[4]:g}", red, bold=True)
            self._add(row, 4, f"{m[5]:,.2f} ج", text_color)
            self._add(row, 5, f"{m[6]:,.2f} ج", red, bold=True)
            self._add(row, 6, m[7] or "—", text_color)

    def _add(self, row, col, text, color, bold=False):
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(Qt.AlignCenter)
        item.setForeground(color)
        if bold:
            f = QFont()
            f.setBold(True)
            item.setFont(f)
        self.table.setItem(row, col, item)

    def _add_movement(self):
        item_id = self.item_combo.currentData()
        if not item_id:
            QMessageBox.warning(self, "تنبيه", "اختار منتج.")
            return

        qty = self.qty_spin.value()
        if qty <= 0:
            QMessageBox.warning(self, "تنبيه", "الكمية لازم أكبر من صفر.")
            return

        try:
            ok, msg = self.db.add_inventory_movement(
                item_id, "out", qty,
                reason=self.reason_combo.currentText().strip() or "صادر",
                notes=self.notes_entry.text().strip()
            )
            if ok:
                QMessageBox.information(self, "تم", f"✅ {msg}")
                self.qty_spin.setValue(1)
                self.notes_entry.clear()
                self.refresh()
            else:
                QMessageBox.warning(self, "تنبيه", msg)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل التسجيل:\n{e}")


# ============================================================
# Tab 4: التنبيهات
# ============================================================
class AlertsTab(QWidget):
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

        # بطاقات تحذير
        stats_row = QHBoxLayout()
        stats_row.setSpacing(8)

        self.stat_out = self._make_stat_card("❌  خلص", "0", "#ef4444")
        self.stat_low = self._make_stat_card("⚠️  قرب تخلص", "0", "#f59e0b")
        self.stat_expiring = self._make_stat_card("📅  قرب تنتهي", "0", "#8b5cf6")

        stats_row.addWidget(self.stat_out, 1)
        stats_row.addWidget(self.stat_low, 1)
        stats_row.addWidget(self.stat_expiring, 1)
        layout.addLayout(stats_row)

        refresh_btn = QPushButton("🔄  تحديث التنبيهات")
        refresh_btn.setMinimumHeight(42)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('primary')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"font-weight: bold; padding: 8px 16px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('primary_hover')}; }}"
        )
        refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(refresh_btn)

        # الجدول
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "#", "المنتج", "الكمية الحالية", "الحد الأدنى",
            "الحالة", "إجراء"
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setLayoutDirection(Qt.RightToLeft)

        h = self.table.horizontalHeader()
        for i in range(6):
            if i == 1:
                h.setSectionResizeMode(i, QHeaderView.Stretch)
            else:
                h.setSectionResizeMode(i, QHeaderView.Fixed)

        self.table.setColumnWidth(0, 45)
        self.table.setColumnWidth(2, 130)
        self.table.setColumnWidth(3, 130)
        self.table.setColumnWidth(4, 150)
        self.table.setColumnWidth(5, 150)

        layout.addWidget(self.table, stretch=1)

    def _make_stat_card(self, title, value, color):
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background-color: {Theme.color('surface')}; "
            f"border: 2px solid {color}; border-radius: 10px; }}"
        )
        card.setMinimumHeight(80)
        v = QVBoxLayout(card)
        v.setContentsMargins(12, 8, 12, 8)
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

    def refresh(self):
        try:
            all_items = self.db.list_inventory_items(active_only=True)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل التحميل:\n{e}")
            return

        # فلترة
        out_items = [i for i in all_items if (i[7] or 0) <= 0]
        low_items = [
            i for i in all_items
            if 0 < (i[7] or 0) <= (i[9] or 0)
        ]

        # قرب تنتهي (30 يوم)
        expiring = []
        try:
            today = datetime.now().date()
            cutoff = today + timedelta(days=30)
            for i in all_items:
                if i[13]:
                    try:
                        d = datetime.strptime(i[13], "%Y-%m-%d").date()
                        if d <= cutoff:
                            expiring.append(i)
                    except Exception:
                        pass
        except Exception:
            pass

        self.stat_out._value_label.setText(str(len(out_items)))
        self.stat_low._value_label.setText(str(len(low_items)))
        self.stat_expiring._value_label.setText(str(len(expiring)))

        # الجدول
        alerts = out_items + low_items + expiring
        # إزالة التكرار
        seen = set()
        unique_alerts = []
        for item in alerts:
            if item[0] not in seen:
                unique_alerts.append(item)
                seen.add(item[0])

        self.table.setRowCount(len(unique_alerts))
        text_color = QColor(Theme.color("text"))
        red = QColor(Theme.color("danger"))
        gold = QColor(Theme.color("gold"))
        purple = QColor("#8b5cf6")

        for row, i in enumerate(unique_alerts):
            self._add(row, 0, str(i[0]), text_color)
            self._add(row, 1, i[1] or "", text_color, bold=True)

            qty = i[7] or 0
            min_qty = i[9] or 0

            self._add(row, 2, f"{qty:g} {i[8] or ''}",
                      red if qty <= 0 else gold, bold=True)
            self._add(row, 3, f"{min_qty:g} {i[8] or ''}", text_color)

            if qty <= 0:
                status, sc = "❌  خلص خالص", red
            elif qty <= min_qty:
                status, sc = "⚠️  قرب تخلص", gold
            else:
                status, sc = "📅  قرب تنتهي", purple

            self._add(row, 4, status, sc, bold=True)

            # إجراء
            suggestion = "🛒  اطلب من المورد" if qty <= min_qty else "⏰  استخدم قريب"
            self._add(row, 5, suggestion, text_color)

    def _add(self, row, col, text, color, bold=False):
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(Qt.AlignCenter)
        item.setForeground(color)
        if bold:
            f = QFont()
            f.setBold(True)
            item.setFont(f)
        self.table.setItem(row, col, item)


# ============================================================
# Tab 5: تقارير المخزون
# ============================================================
class InventoryReportsTab(QWidget):
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

        # بطاقات إحصائية
        stats_row = QHBoxLayout()
        stats_row.setSpacing(8)

        self.stat_items = self._make_stat_card("📦  عدد المنتجات", "0")
        self.stat_cost = self._make_stat_card("💰  قيمة الشراء", "0 ج")
        self.stat_selling = self._make_stat_card("🏷️  قيمة البيع", "0 ج")
        self.stat_profit = self._make_stat_card("📈  الربح المتوقع", "0 ج")

        stats_row.addWidget(self.stat_items, 1)
        stats_row.addWidget(self.stat_cost, 1)
        stats_row.addWidget(self.stat_selling, 1)
        stats_row.addWidget(self.stat_profit, 1)
        layout.addLayout(stats_row)

        # تقرير حسب الفئة
        cat_title = QLabel("📊  التوزيع حسب الفئة")
        cat_title.setStyleSheet(
            f"color: {Theme.color('primary')}; font-size: 14px; "
            f"font-weight: bold; background: transparent; padding: 4px;"
        )
        layout.addWidget(cat_title)

        self.cat_table = QTableWidget()
        self.cat_table.setColumnCount(5)
        self.cat_table.setHorizontalHeaderLabels([
            "الفئة", "عدد المنتجات", "قيمة الشراء",
            "قيمة البيع", "الربح المتوقع"
        ])
        self.cat_table.verticalHeader().setVisible(False)
        self.cat_table.setAlternatingRowColors(True)
        self.cat_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.cat_table.setShowGrid(False)
        self.cat_table.setLayoutDirection(Qt.RightToLeft)

        h = self.cat_table.horizontalHeader()
        for i in range(5):
            h.setSectionResizeMode(i, QHeaderView.Stretch)

        layout.addWidget(self.cat_table, stretch=1)

    def _make_stat_card(self, title, value):
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background-color: {Theme.color('surface')}; "
            f"border: 1px solid {Theme.color('border')}; border-radius: 10px; }}"
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
            stats = self.db.get_inventory_value()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل التحميل:\n{e}")
            return

        self.stat_items._value_label.setText(str(stats["items_count"]))
        self.stat_cost._value_label.setText(f"{stats['cost_value']:,.0f} ج")
        self.stat_selling._value_label.setText(f"{stats['selling_value']:,.0f} ج")
        profit = stats["selling_value"] - stats["cost_value"]
        self.stat_profit._value_label.setText(f"{profit:,.0f} ج")

        # تقرير الفئات
        try:
            items = self.db.list_inventory_items(active_only=True)
            categories = self.db.list_inventory_categories()
        except Exception:
            return

        # اجمع حسب الفئة
        by_cat = {}
        for i in items:
            cat_id = i[3]
            cat_name = i[4] or "بدون فئة"
            cat_icon = i[6] or "📦"

            if cat_id not in by_cat:
                by_cat[cat_id] = {
                    "name": f"{cat_icon}  {cat_name}",
                    "count": 0,
                    "cost": 0,
                    "selling": 0,
                }

            by_cat[cat_id]["count"] += 1
            by_cat[cat_id]["cost"] += (i[7] or 0) * (i[10] or 0)
            by_cat[cat_id]["selling"] += (i[7] or 0) * (i[11] or 0)

        self.cat_table.setRowCount(len(by_cat))
        text_color = QColor(Theme.color("text"))
        green = QColor(Theme.color("success"))

        for row, (cat_id, data) in enumerate(by_cat.items()):
            profit = data["selling"] - data["cost"]

            self._add_cat(row, 0, data["name"], text_color, bold=True)
            self._add_cat(row, 1, str(data["count"]), text_color)
            self._add_cat(row, 2, f"{data['cost']:,.0f} ج", text_color)
            self._add_cat(row, 3, f"{data['selling']:,.0f} ج", text_color)
            self._add_cat(row, 4, f"{profit:,.0f} ج", green, bold=True)

    def _add_cat(self, row, col, text, color, bold=False):
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(Qt.AlignCenter)
        item.setForeground(color)
        if bold:
            f = QFont()
            f.setBold(True)
            item.setFont(f)
        self.cat_table.setItem(row, col, item)


# ============================================================
# Main Tab — Inventory Tab
# ============================================================
class InventoryTab(QWidget):
    """التاب الرئيسي للمخزون — بيجمع 5 تابات داخلية."""

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
        title = QLabel("📦  إدارة المخزون")
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
                min-width: 130px;
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

        self.tab_items = ItemsTab(self.db, self.user)
        self.sub_tabs.addTab(self.tab_items, "  📦  المنتجات  ")

        self.tab_in = StockInTab(self.db, self.user)
        self.sub_tabs.addTab(self.tab_in, "  📥  الوارد  ")

        self.tab_out = StockOutTab(self.db, self.user)
        self.sub_tabs.addTab(self.tab_out, "  📤  الصادر  ")

        self.tab_alerts = AlertsTab(self.db, self.user)
        self.sub_tabs.addTab(self.tab_alerts, "  ⚠️  التنبيهات  ")

        self.tab_reports = InventoryReportsTab(self.db, self.user)
        self.sub_tabs.addTab(self.tab_reports, "  📊  التقارير  ")

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