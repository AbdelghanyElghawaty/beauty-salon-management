"""
Customers Tab — PySide6 with Soft Delete + VIP + Permanent Delete.
+ Light/Dark theme support (reads from Theme).
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QDialog, QAbstractItemView,
    QTabWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from utils.theme import Theme


VIP_THRESHOLD = 10


# ============================================================
# Customer Dialog
# ============================================================
class CustomerDialog(QDialog):
    def __init__(self, parent=None, customer_id=None, name="", phone=""):
        super().__init__(parent)
        self.customer_id = customer_id
        self.result_data = None

        self.setWindowTitle(
            "تعديل العميل" if customer_id else "إضافة عميل جديد"
        )
        self.setFixedSize(420, 300)
        self.setLayoutDirection(Qt.RightToLeft)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Theme.color('bg')};
            }}
            QLabel {{
                color: {Theme.color('text')};
                background: transparent;
                font-size: 11pt;
            }}
            QLineEdit {{
                background-color: {Theme.color('surface')};
                color: {Theme.color('text')};
                border: 1px solid {Theme.color('border_strong')};
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 11pt;
            }}
            QLineEdit:focus {{
                border: 2px solid {Theme.color('primary')};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel(
            "✏️ تعديل العميل" if customer_id else "➕ إضافة عميل جديد"
        )
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"font-size: 18px; font-weight: bold; "
            f"color: {Theme.color('primary')}; background: transparent;"
        )
        layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(
            f"color: {Theme.color('border')}; background: transparent;"
        )
        layout.addWidget(sep)

        layout.addWidget(QLabel("اسم العميل:"))
        self.name_entry = QLineEdit(name)
        self.name_entry.setMinimumHeight(42)
        self.name_entry.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.name_entry.setPlaceholderText("مثال: محمد أحمد")
        layout.addWidget(self.name_entry)

        layout.addWidget(QLabel("التليفون:"))
        self.phone_entry = QLineEdit(phone or "")
        self.phone_entry.setMinimumHeight(42)
        self.phone_entry.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.phone_entry.setPlaceholderText("مثال: 01012345678")
        layout.addWidget(self.phone_entry)

        btns = QHBoxLayout()
        btns.setSpacing(10)

        self.save_btn = QPushButton("💾  حفظ")
        self.save_btn.setMinimumHeight(44)
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('success')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"font-weight: bold; font-size: 11pt; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('success_hover')}; }}"
        )
        self.save_btn.clicked.connect(self._on_save)

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setMinimumHeight(44)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('surface_alt')}; "
            f"color: {Theme.color('text')}; border: none; border-radius: 8px; "
            f"font-weight: bold; font-size: 11pt; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('border_strong')}; }}"
        )
        cancel_btn.clicked.connect(self.reject)

        btns.addWidget(cancel_btn)
        btns.addWidget(self.save_btn)
        layout.addLayout(btns)

        self.name_entry.setFocus()

    def _on_save(self):
        name = self.name_entry.text().strip()
        phone = self.phone_entry.text().strip()

        if not name:
            QMessageBox.warning(self, "خطأ", "من فضلك ادخل اسم العميل")
            self.name_entry.setFocus()
            return

        self.result_data = {"name": name, "phone": phone}
        self.accept()


# ============================================================
# Customers Tab
# ============================================================
class CustomersTab(QWidget):
    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user
        self.can_edit = user.has_permission("edit_customers")
        self.can_edit_info = user.has_permission("edit_customer_info")

        self._build_ui()
        self.refresh()

    # ============================================
    # UI
    # ============================================
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("👥  إدارة العملاء")
        title.setStyleSheet(
            f"font-size: 22px; font-weight: bold; "
            f"color: {Theme.color('primary')}; padding: 4px; "
            f"background: transparent;"
        )
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Sub-tabs
        self.sub_tabs = QTabWidget()
        self.sub_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {Theme.color('border')};
                border-radius: 8px;
                background-color: {Theme.color('bg')};
                padding: 12px;
            }}
            QTabBar::tab {{
                background-color: {Theme.color('surface')};
                color: {Theme.color('text_muted')};
                padding: 10px 20px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 13px;
                font-weight: bold;
                min-width: 120px;
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

        self.all_tab = self._build_customers_tab_widget(mode="all")
        self.sub_tabs.addTab(self.all_tab, "  👥  كل العملاء  ")

        self.vip_tab = self._build_customers_tab_widget(mode="vip")
        self.sub_tabs.addTab(self.vip_tab, "  ⭐  العملاء المميزين  ")

        self.inactive_tab = self._build_customers_tab_widget(mode="inactive")
        self.sub_tabs.addTab(self.inactive_tab, "  🚫  العملاء المعطّلين  ")

        layout.addWidget(self.sub_tabs)

        self.sub_tabs.currentChanged.connect(lambda _: self.refresh())

    # ============================================
    # Sub-tab builder
    # ============================================
    def _build_customers_tab_widget(self, mode):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        if mode == "all" and self.can_edit:
            add_card = QFrame()
            add_card.setStyleSheet(
                f"QFrame {{ background-color: {Theme.color('surface')}; "
                f"border: 1px solid {Theme.color('border')}; border-radius: 12px; }}"
            )
            add_layout = QVBoxLayout(add_card)
            add_layout.setContentsMargins(20, 18, 20, 18)
            add_layout.setSpacing(12)

            card_title = QLabel("➕  إضافة عميل جديد")
            card_title.setStyleSheet(
                f"font-size: 15px; font-weight: bold; "
                f"color: {Theme.color('text')}; background: transparent; "
                f"padding: 0 4px;"
            )
            add_layout.addWidget(card_title)

            form_row = QHBoxLayout()
            form_row.setSpacing(12)

            name_lbl = QLabel("اسم العميل:")
            name_lbl.setStyleSheet(
                f"color: {Theme.color('text')}; background: transparent; "
                f"font-size: 11pt;"
            )
            form_row.addWidget(name_lbl)

            self.name_entry = QLineEdit()
            self.name_entry.setPlaceholderText("مثال: محمد أحمد")
            self.name_entry.setMinimumHeight(44)
            self.name_entry.setMinimumWidth(200)
            self.name_entry.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            form_row.addWidget(self.name_entry, stretch=2)

            phone_lbl = QLabel("التليفون:")
            phone_lbl.setStyleSheet(
                f"color: {Theme.color('text')}; background: transparent; "
                f"font-size: 11pt;"
            )
            form_row.addWidget(phone_lbl)

            self.phone_entry = QLineEdit()
            self.phone_entry.setPlaceholderText("مثال: 01012345678")
            self.phone_entry.setMinimumHeight(44)
            self.phone_entry.setMinimumWidth(160)
            self.phone_entry.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            form_row.addWidget(self.phone_entry, stretch=1)

            add_btn = QPushButton("➕  إضافة")
            add_btn.setMinimumHeight(44)
            add_btn.setMinimumWidth(120)
            add_btn.setCursor(Qt.PointingHandCursor)
            add_btn.setStyleSheet(
                f"QPushButton {{ background-color: {Theme.color('success')}; "
                f"color: white; border: none; border-radius: 8px; "
                f"font-weight: bold; font-size: 12px; }}"
                f"QPushButton:hover {{ background-color: {Theme.color('success_hover')}; }}"
            )
            add_btn.clicked.connect(self._add_customer)
            form_row.addWidget(add_btn)

            add_layout.addLayout(form_row)
            layout.addWidget(add_card)

        # Actions
        actions = QHBoxLayout()
        actions.setSpacing(10)

        edit_btn = QPushButton("✏️  تعديل المختار")
        edit_btn.setMinimumHeight(42)
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('primary')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"padding: 10px 20px; font-weight: bold; font-size: 12px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('primary_hover')}; }}"
        )
        edit_btn.clicked.connect(lambda: self._edit_customer(mode))
        actions.addWidget(edit_btn)

        if mode == "inactive":
            reactivate_btn = QPushButton("✅  إعادة تفعيل المختار")
            reactivate_btn.setMinimumHeight(42)
            reactivate_btn.setMinimumWidth(200)
            reactivate_btn.setCursor(Qt.PointingHandCursor)
            reactivate_btn.setStyleSheet(
                f"QPushButton {{ background-color: {Theme.color('success')}; "
                f"color: white; border-radius: 8px; padding: 10px 20px; "
                f"font-size: 13px; font-weight: bold; }}"
                f"QPushButton:hover {{ background-color: {Theme.color('success_hover')}; }}"
            )
            reactivate_btn.clicked.connect(lambda: self._toggle_customer(mode))
            actions.addWidget(reactivate_btn)

            delete_btn = QPushButton("🗑️  حذف نهائي")
            delete_btn.setMinimumHeight(42)
            delete_btn.setMinimumWidth(160)
            delete_btn.setCursor(Qt.PointingHandCursor)
            delete_btn.setStyleSheet(
                f"QPushButton {{ background-color: #7f1d1d; color: white; "
                f"border-radius: 8px; padding: 10px 20px; "
                f"font-size: 13px; font-weight: bold; }}"
                f"QPushButton:hover {{ background-color: #991b1b; }}"
            )
            delete_btn.clicked.connect(lambda: self._permanent_delete(mode))
            actions.addWidget(delete_btn)

            self.inactive_reactivate_btn = reactivate_btn
            self.inactive_delete_btn = delete_btn
            self.all_toggle_btn = None
            self.vip_toggle_btn = None

        else:
            toggle_btn = QPushButton("🚫  تعطيل / ✅  تفعيل")
            toggle_btn.setMinimumHeight(42)
            toggle_btn.setMinimumWidth(220)
            toggle_btn.setCursor(Qt.PointingHandCursor)
            toggle_btn.setStyleSheet(
                f"QPushButton {{ background-color: {Theme.color('text_dim')}; "
                f"color: white; border-radius: 8px; padding: 10px 20px; "
                f"font-size: 13px; font-weight: bold; }}"
                f"QPushButton:hover {{ background-color: {Theme.color('border_strong')}; }}"
            )
            toggle_btn.clicked.connect(lambda: self._toggle_customer(mode))
            actions.addWidget(toggle_btn)

            if mode == "all":
                self.all_toggle_btn = toggle_btn
            elif mode == "vip":
                self.vip_toggle_btn = toggle_btn

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

        titles = {
            "all": "📋  قائمة كل العملاء",
            "vip": f"⭐  العملاء المميزين ({VIP_THRESHOLD}+ نقطة)",
            "inactive": "🚫  قائمة العملاء المعطّلين",
        }
        tbl_title = QLabel(titles.get(mode, "📋"))
        tbl_title.setStyleSheet(
            f"font-size: 15px; font-weight: bold; "
            f"color: {Theme.color('text')}; background: transparent; "
            f"padding: 0 4px;"
        )
        table_layout.addWidget(tbl_title)

        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(
            ["#", "الاسم", "التليفون", "نقاط الولاء", "الحالة"]
        )
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setShowGrid(False)
        table.setMinimumHeight(320)
        table.setLayoutDirection(Qt.RightToLeft)

        header_view = table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.Fixed)
        header_view.setSectionResizeMode(1, QHeaderView.Stretch)
        header_view.setSectionResizeMode(2, QHeaderView.Fixed)
        header_view.setSectionResizeMode(3, QHeaderView.Fixed)
        header_view.setSectionResizeMode(4, QHeaderView.Fixed)

        table.setColumnWidth(0, 60)
        table.setColumnWidth(2, 160)
        table.setColumnWidth(3, 120)
        table.setColumnWidth(4, 120)

        if self.can_edit_info:
            table.doubleClicked.connect(lambda: self._edit_customer(mode))

        table.itemSelectionChanged.connect(
            lambda: self._update_toggle_button(mode)
        )

        table_layout.addWidget(table)
        layout.addWidget(table_card)

        if mode == "all":
            self.all_table = table
        elif mode == "vip":
            self.vip_table = table
        elif mode == "inactive":
            self.inactive_table = table

        return widget

    # ============================================
    # Refresh
    # ============================================
    def refresh(self):
        try:
            all_customers = self.db.list_all_customers()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل العملاء:\n{e}")
            return

        self._fill_table(self.all_table, all_customers, mode="all")

        vip_customers = [
            c for c in all_customers if c[3] >= VIP_THRESHOLD and c[4] == 1
        ]
        self._fill_table(self.vip_table, vip_customers, mode="vip")

        inactive_customers = [c for c in all_customers if c[4] == 0]
        self._fill_table(self.inactive_table, inactive_customers, mode="inactive")

        self._update_toggle_button("all")
        self._update_toggle_button("vip")

    def _fill_table(self, table, customers, mode):
        table.blockSignals(True)
        table.setRowCount(len(customers))

        gray = QColor(Theme.color("text_dim"))
        green = QColor(Theme.color("success"))
        gold = QColor(Theme.color("gold"))
        text_color = QColor(Theme.color("text"))

        italic_font = QFont()
        italic_font.setItalic(True)

        for row, (cid, name, phone, points, is_active) in enumerate(customers):
            item_id = QTableWidgetItem(str(cid))
            item_id.setTextAlignment(Qt.AlignCenter)
            item_id.setData(Qt.UserRole, cid)
            item_id.setData(Qt.UserRole + 1, is_active)
            item_id.setForeground(text_color)
            table.setItem(row, 0, item_id)

            is_vip = points >= VIP_THRESHOLD
            display_name = f"⭐ {name}" if is_vip else name
            item_name = QTableWidgetItem(display_name)
            item_name.setTextAlignment(Qt.AlignCenter)
            if is_vip:
                item_name.setForeground(gold)
            else:
                item_name.setForeground(text_color)
            table.setItem(row, 1, item_name)

            item_phone = QTableWidgetItem(phone or "—")
            item_phone.setTextAlignment(Qt.AlignCenter)
            item_phone.setForeground(text_color)
            table.setItem(row, 2, item_phone)

            item_points = QTableWidgetItem(str(points))
            item_points.setTextAlignment(Qt.AlignCenter)
            item_points.setForeground(text_color)
            table.setItem(row, 3, item_points)

            if is_active:
                item_status = QTableWidgetItem("✅  نشط")
                item_status.setForeground(green)
            else:
                item_status = QTableWidgetItem("🚫  معطّل")
                item_status.setForeground(gray)
            item_status.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 4, item_status)

            if not is_active:
                for col in range(5):
                    itm = table.item(row, col)
                    if itm:
                        itm.setForeground(gray)
                        itm.setFont(italic_font)

        table.blockSignals(False)

    # ============================================
    # Helpers
    # ============================================
    def _get_selected_info(self, mode):
        table = self._get_table(mode)
        if table is None:
            return None, None, None
        rows = table.selectionModel().selectedRows()
        if not rows:
            return None, None, None
        row_idx = rows[0].row()
        item = table.item(row_idx, 0)
        if item is None:
            return None, None, None
        name_item = table.item(row_idx, 1)
        name = name_item.text() if name_item else ""
        return item.data(Qt.UserRole), item.data(Qt.UserRole + 1), name

    def _get_table(self, mode):
        return {
            "all": self.all_table,
            "vip": self.vip_table,
            "inactive": self.inactive_table,
        }.get(mode)

    def _get_toggle_btn(self, mode):
        return {
            "all": getattr(self, "all_toggle_btn", None),
            "vip": getattr(self, "vip_toggle_btn", None),
            "inactive": None,
        }.get(mode)

    # ============================================
    # Smart Toggle Button
    # ============================================
    def _update_toggle_button(self, mode):
        if mode == "inactive":
            return

        btn = self._get_toggle_btn(mode)
        if btn is None:
            return

        try:
            cid, is_active, _ = self._get_selected_info(mode)
        except Exception:
            cid, is_active = None, None

        if cid is None:
            btn.setText("🚫  تعطيل / ✅  تفعيل")
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {Theme.color('text_dim')}; "
                f"color: white; border-radius: 8px; padding: 10px 20px; "
                f"font-size: 13px; font-weight: bold; }}"
                f"QPushButton:hover {{ background-color: {Theme.color('border_strong')}; }}"
            )
        elif is_active:
            btn.setText("🚫  تعطيل المختار")
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {Theme.color('danger')}; "
                f"color: white; border-radius: 8px; padding: 10px 20px; "
                f"font-size: 13px; font-weight: bold; }}"
                f"QPushButton:hover {{ background-color: {Theme.color('danger_hover')}; }}"
            )
        else:
            btn.setText("✅  إعادة تفعيل المختار")
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {Theme.color('success')}; "
                f"color: white; border-radius: 8px; padding: 10px 20px; "
                f"font-size: 13px; font-weight: bold; }}"
                f"QPushButton:hover {{ background-color: {Theme.color('success_hover')}; }}"
            )

    # ============================================
    # Add
    # ============================================
    def _add_customer(self):
        name = self.name_entry.text().strip()
        phone = self.phone_entry.text().strip()

        if not name:
            QMessageBox.warning(self, "خطأ", "من فضلك ادخل اسم العميل")
            return

        try:
            self.db.add_customer(name, phone)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل الإضافة:\n{e}")
            return

        self.name_entry.clear()
        self.phone_entry.clear()
        self.name_entry.setFocus()
        self.refresh()

    # ============================================
    # Edit
    # ============================================
    def _edit_customer(self, mode):
        cid, _, _ = self._get_selected_info(mode)
        if cid is None:
            QMessageBox.warning(self, "خطأ", "اختار عميل من القائمة الأول")
            return

        row = self.db.get_customer(cid)
        if not row:
            QMessageBox.warning(self, "خطأ", "العميل مش موجود")
            return

        _, name, phone, points, is_active = row

        dlg = CustomerDialog(self, customer_id=cid, name=name, phone=phone or "")
        if dlg.exec() == QDialog.Accepted:
            data = dlg.result_data
            try:
                self.db.update_customer(cid, data["name"], data["phone"])
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل التعديل:\n{e}")
                return
            self.refresh()

    # ============================================
    # Toggle Customer
    # ============================================
    def _toggle_customer(self, mode):
        cid, is_active, _ = self._get_selected_info(mode)
        if cid is None:
            QMessageBox.warning(self, "خطأ", "اختار عميل من القائمة الأول")
            return

        if is_active:
            reply = QMessageBox.question(
                self, "تعطيل العميل",
                "هل تريد تعطيل العميل؟\n\n"
                "العميل هيتخفي من قوائم الحجز الجديدة،\n"
                "لكن هيفضل في الحجوزات القديمة.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return

            try:
                self.db.deactivate_customer(cid)
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل التعطيل:\n{e}")
                return

            QMessageBox.information(self, "تم", "تم تعطيل العميل بنجاح.")

        else:
            reply = QMessageBox.question(
                self, "إعادة التفعيل",
                "العميل معطّل حاليًا.\nهل تريد إعادة تفعيله؟",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return

            try:
                self.db.activate_customer(cid)
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل التفعيل:\n{e}")
                return

            QMessageBox.information(self, "تم", "تم إعادة تفعيل العميل.")

        self.refresh()

    # ============================================
    # Permanent Delete
    # ============================================
    def _permanent_delete(self, mode):
        cid, _, name = self._get_selected_info(mode)
        if cid is None:
            QMessageBox.warning(self, "خطأ", "اختار عميل من القائمة الأول")
            return

        try:
            import sqlite3
            conn = sqlite3.connect(self.db.db_path)
            count = conn.execute(
                "SELECT COUNT(*) FROM bookings WHERE customer_id = ?",
                (cid,),
            ).fetchone()[0]
            conn.close()
        except Exception:
            count = 0

        if count > 0:
            QMessageBox.warning(
                self, "مش ممكن الحذف",
                f"العميل عنده {count} حجز مسجل.\n\n"
                f"لازم تحذف الحجوزات الأول، أو تفضل العميل معطّل.",
            )
            return

        reply = QMessageBox.warning(
            self, "⚠️ تأكيد الحذف النهائي",
            f"⚠️ تحذير!\n\n"
            f"هتحذف العميل '{name}' نهائيًا!\n"
            f"العملية دي مش قابلة للتراجع.\n\n"
            f"هل أنت متأكد؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        try:
            ok, msg = self.db.delete_customer(cid)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل الحذف:\n{e}")
            return

        if not ok:
            QMessageBox.warning(self, "مش ممكن", msg)
            return

        QMessageBox.information(self, "تم", "تم الحذف النهائي.")
        self.refresh()