"""
Services Tab — PySide6 with Soft Delete + Smart Toggle Button.
+ Light/Dark theme support (reads from Theme).
+ Permanent Delete (حذف نهائي)
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QDialog, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from utils.theme import Theme


# ============================================================
# Service Dialog
# ============================================================
class ServiceDialog(QDialog):
    """حوار إضافة/تعديل خدمة."""

    def __init__(self, parent=None, service_id=None, name="", price=0.0):
        super().__init__(parent)
        self.service_id = service_id
        self.result_data = None

        self.setWindowTitle(
            "تعديل الخدمة" if service_id else "إضافة خدمة جديدة"
        )
        self.setFixedSize(420, 300)
        self.setLayoutDirection(Qt.RightToLeft)

        # ✅ Stylesheet ديناميكي
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

        # عنوان
        title = QLabel(
            "✏️ تعديل الخدمة" if service_id else "➕ إضافة خدمة جديدة"
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

        # اسم الخدمة
        layout.addWidget(QLabel("اسم الخدمة:"))
        self.name_entry = QLineEdit(name)
        self.name_entry.setMinimumHeight(42)
        self.name_entry.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.name_entry.setPlaceholderText("مثال: حلاقة شعر")
        layout.addWidget(self.name_entry)

        # السعر
        layout.addWidget(QLabel("السعر:"))
        self.price_entry = QLineEdit(str(price) if price else "")
        self.price_entry.setMinimumHeight(42)
        self.price_entry.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.price_entry.setPlaceholderText("مثال: 50")
        layout.addWidget(self.price_entry)

        # أزرار
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
        price_str = self.price_entry.text().strip()

        if not name:
            QMessageBox.warning(self, "خطأ", "من فضلك ادخل اسم الخدمة")
            self.name_entry.setFocus()
            return

        try:
            price = float(price_str)
        except ValueError:
            QMessageBox.warning(self, "خطأ", "من فضلك ادخل سعر صحيح")
            self.price_entry.setFocus()
            return

        self.result_data = {"name": name, "price": price}
        self.accept()


# ============================================================
# Services Tab
# ============================================================
class ServicesTab(QWidget):
    """تاب إدارة الخدمات والأسعار مع Soft Delete + زر ذكي."""

    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user
        self.can_edit = user.has_permission("edit_services")

        self._build_ui()
        self.refresh()

    # ============================================
    # UI
    # ============================================
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # ============================================
        # العنوان
        # ============================================
        header = QHBoxLayout()
        title = QLabel("💈  إدارة الخدمات والأسعار")
        title.setStyleSheet(
            f"font-size: 22px; font-weight: bold; "
            f"color: {Theme.color('primary')}; padding: 4px; "
            f"background: transparent;"
        )
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # ============================================
        # Add Card
        # ============================================
        if self.can_edit:
            add_card = QFrame()
            add_card.setObjectName("card")
            add_card.setStyleSheet(
                f"QFrame#card {{ background-color: {Theme.color('surface')}; "
                f"border: 1px solid {Theme.color('border')}; border-radius: 12px; }}"
            )
            add_layout = QVBoxLayout(add_card)
            add_layout.setContentsMargins(20, 18, 20, 18)
            add_layout.setSpacing(12)

            card_title = QLabel("➕  إضافة خدمة جديدة")
            card_title.setStyleSheet(
                f"font-size: 15px; font-weight: bold; "
                f"color: {Theme.color('text')}; background: transparent; "
                f"padding: 0 4px;"
            )
            add_layout.addWidget(card_title)

            form_row = QHBoxLayout()
            form_row.setSpacing(12)

            name_lbl = QLabel("اسم الخدمة:")
            name_lbl.setStyleSheet(
                f"color: {Theme.color('text')}; background: transparent; "
                f"font-size: 11pt;"
            )
            form_row.addWidget(name_lbl)

            self.name_entry = QLineEdit()
            self.name_entry.setPlaceholderText("مثال: حلاقة شعر")
            self.name_entry.setMinimumHeight(44)
            self.name_entry.setMinimumWidth(220)
            self.name_entry.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            form_row.addWidget(self.name_entry, stretch=2)

            price_lbl = QLabel("السعر:")
            price_lbl.setStyleSheet(
                f"color: {Theme.color('text')}; background: transparent; "
                f"font-size: 11pt;"
            )
            form_row.addWidget(price_lbl)

            self.price_entry = QLineEdit()
            self.price_entry.setPlaceholderText("مثال: 50")
            self.price_entry.setMinimumHeight(44)
            self.price_entry.setMaximumWidth(140)
            self.price_entry.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            form_row.addWidget(self.price_entry, stretch=1)

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
            add_btn.clicked.connect(self._add_service)
            form_row.addWidget(add_btn)

            add_layout.addLayout(form_row)
            layout.addWidget(add_card)

        # ============================================
        # Actions
        # ============================================
        if self.can_edit:
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
            edit_btn.clicked.connect(self._edit_service)
            actions.addWidget(edit_btn)

            # ✅ الزر الذكي — النص واللون يتغير حسب الاختيار
            self.toggle_btn = QPushButton("🚫  تعطيل / ✅  تفعيل")
            self.toggle_btn.setMinimumHeight(42)
            self.toggle_btn.setMinimumWidth(220)
            self.toggle_btn.setCursor(Qt.PointingHandCursor)
            self.toggle_btn.setStyleSheet(
                f"QPushButton {{ background-color: {Theme.color('text_dim')}; "
                f"color: white; border-radius: 8px; padding: 10px 20px; "
                f"font-size: 13px; font-weight: bold; }}"
                f"QPushButton:hover {{ background-color: {Theme.color('border_strong')}; }}"
            )
            self.toggle_btn.clicked.connect(self._toggle_service)
            actions.addWidget(self.toggle_btn)

            # ✅ زر الحذف النهائي
            self.delete_btn = QPushButton("🗑️  حذف نهائي")
            self.delete_btn.setMinimumHeight(42)
            self.delete_btn.setMinimumWidth(160)
            self.delete_btn.setCursor(Qt.PointingHandCursor)
            self.delete_btn.setStyleSheet(
                f"QPushButton {{ background-color: #7f1d1d; "
                f"color: white; border-radius: 8px; padding: 10px 20px; "
                f"font-size: 13px; font-weight: bold; }}"
                f"QPushButton:hover {{ background-color: #991b1b; }}"
            )
            self.delete_btn.clicked.connect(self._permanent_delete)
            actions.addWidget(self.delete_btn)

            actions.addStretch()
            layout.addLayout(actions)
        else:
            self.toggle_btn = None
            self.delete_btn = None

        # ============================================
        # Table
        # ============================================
        table_card = QFrame()
        table_card.setObjectName("card")
        table_card.setStyleSheet(
            f"QFrame#card {{ background-color: {Theme.color('surface')}; "
            f"border: 1px solid {Theme.color('border')}; border-radius: 12px; }}"
        )
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(16, 16, 16, 16)
        table_layout.setSpacing(10)

        tbl_title = QLabel("📋  قائمة الخدمات")
        tbl_title.setStyleSheet(
            f"font-size: 15px; font-weight: bold; "
            f"color: {Theme.color('text')}; background: transparent; "
            f"padding: 0 4px;"
        )
        table_layout.addWidget(tbl_title)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["#", "الخدمة", "السعر", "الحالة"]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setMinimumHeight(350)
        self.table.setLayoutDirection(Qt.RightToLeft)

        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.Fixed)
        header_view.setSectionResizeMode(1, QHeaderView.Stretch)
        header_view.setSectionResizeMode(2, QHeaderView.Fixed)
        header_view.setSectionResizeMode(3, QHeaderView.Fixed)

        self.table.setColumnWidth(0, 70)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 130)

        if self.can_edit:
            self.table.doubleClicked.connect(self._edit_service)
            self.table.itemSelectionChanged.connect(self._update_toggle_button)

        table_layout.addWidget(self.table)
        layout.addWidget(table_card)

    # ============================================
    # Refresh
    # ============================================
    def refresh(self):
        try:
            services = self.db.list_all_services()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل الخدمات:\n{e}")
            return

        self.table.blockSignals(True)
        self.table.setRowCount(len(services))

        # ✅ ألوان ديناميكية
        green = QColor(Theme.color("success"))
        gray = QColor(Theme.color("text_dim"))
        text_color = QColor(Theme.color("text"))

        italic_font = QFont()
        italic_font.setItalic(True)

        for row, (sid, name, price, is_active) in enumerate(services):
            item_id = QTableWidgetItem(str(sid))
            item_id.setTextAlignment(Qt.AlignCenter)
            item_id.setData(Qt.UserRole, sid)
            item_id.setData(Qt.UserRole + 1, is_active)
            item_id.setForeground(text_color)
            self.table.setItem(row, 0, item_id)

            item_name = QTableWidgetItem(name)
            item_name.setTextAlignment(Qt.AlignCenter)
            item_name.setForeground(text_color)
            self.table.setItem(row, 1, item_name)

            item_price = QTableWidgetItem(f"{price:.2f} ج")
            item_price.setTextAlignment(Qt.AlignCenter)
            item_price.setForeground(text_color)
            self.table.setItem(row, 2, item_price)

            if is_active:
                item_status = QTableWidgetItem("✅  نشطة")
                item_status.setForeground(green)
            else:
                item_status = QTableWidgetItem("🚫  معطّلة")
                item_status.setForeground(gray)
            item_status.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, item_status)

            if not is_active:
                for col in range(4):
                    itm = self.table.item(row, col)
                    if itm:
                        itm.setForeground(gray)
                        itm.setFont(italic_font)

        self.table.blockSignals(False)

        if self.can_edit and hasattr(self, "toggle_btn") and self.toggle_btn is not None:
            self._update_toggle_button()

    # ============================================
    # Add
    # ============================================
    def _add_service(self):
        name = self.name_entry.text().strip()
        price_str = self.price_entry.text().strip()

        if not name:
            QMessageBox.warning(self, "خطأ", "من فضلك ادخل اسم الخدمة")
            return

        try:
            price = float(price_str)
        except ValueError:
            QMessageBox.warning(self, "خطأ", "من فضلك ادخل سعر صحيح")
            return

        try:
            self.db.add_service(name, price)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل الإضافة:\n{e}")
            return

        self.name_entry.clear()
        self.price_entry.clear()
        self.name_entry.setFocus()
        self.refresh()

    # ============================================
    # Helpers
    # ============================================
    def _get_selected_info(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None, None
        row_idx = rows[0].row()
        item = self.table.item(row_idx, 0)
        if item is None:
            return None, None
        return item.data(Qt.UserRole), item.data(Qt.UserRole + 1)

    # ============================================
    # ✅ Smart Toggle Button
    # ============================================
    def _update_toggle_button(self):
        if not hasattr(self, "toggle_btn") or self.toggle_btn is None:
            return

        try:
            sid, is_active = self._get_selected_info()
        except Exception:
            sid, is_active = None, None

        if sid is None:
            self.toggle_btn.setText("🚫  تعطيل / ✅  تفعيل")
            self.toggle_btn.setStyleSheet(
                f"QPushButton {{"
                f"background-color: {Theme.color('text_dim')}; color: white;"
                f"border-radius: 8px; padding: 10px 20px;"
                f"font-size: 13px; font-weight: bold;"
                f"}}"
                f"QPushButton:hover {{ background-color: {Theme.color('border_strong')}; }}"
                f"QPushButton:disabled {{ background-color: {Theme.color('border')}; "
                f"color: {Theme.color('text_dim')}; }}"
            )

        elif is_active:
            self.toggle_btn.setText("🚫  تعطيل المختار")
            self.toggle_btn.setStyleSheet(
                f"QPushButton {{"
                f"background-color: {Theme.color('danger')}; color: white;"
                f"border-radius: 8px; padding: 10px 20px;"
                f"font-size: 13px; font-weight: bold;"
                f"}}"
                f"QPushButton:hover {{ background-color: {Theme.color('danger_hover')}; }}"
            )

        else:
            self.toggle_btn.setText("✅  إعادة تفعيل المختار")
            self.toggle_btn.setStyleSheet(
                f"QPushButton {{"
                f"background-color: {Theme.color('success')}; color: white;"
                f"border-radius: 8px; padding: 10px 20px;"
                f"font-size: 13px; font-weight: bold;"
                f"}}"
                f"QPushButton:hover {{ background-color: {Theme.color('success_hover')}; }}"
            )

    # ============================================
    # Edit
    # ============================================
    def _edit_service(self):
        sid, _ = self._get_selected_info()
        if sid is None:
            QMessageBox.warning(self, "خطأ", "اختار خدمة من القائمة الأول")
            return

        row = self.db.get_service(sid)
        if not row:
            QMessageBox.warning(self, "خطأ", "الخدمة مش موجودة")
            return

        _, name, price, is_active = row

        dlg = ServiceDialog(self, service_id=sid, name=name, price=price)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.result_data
            try:
                self.db.update_service(sid, data["name"], data["price"])
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل التعديل:\n{e}")
                return
            self.refresh()

    # ============================================
    # Toggle Service
    # ============================================
    def _toggle_service(self):
        sid, is_active = self._get_selected_info()
        if sid is None:
            QMessageBox.warning(self, "خطأ", "اختار خدمة من القائمة الأول")
            return

        if is_active:
            reply = QMessageBox.question(
                self, "تعطيل الخدمة",
                "هل تريد تعطيل الخدمة؟\n\n"
                "الخدمة هتختفي من قوائم الحجز الجديدة،\n"
                "لكن هتفضل في الحجوزات القديمة.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return

            try:
                self.db.deactivate_service(sid)
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل التعطيل:\n{e}")
                return

            QMessageBox.information(self, "تم", "تم تعطيل الخدمة بنجاح.")

        else:
            reply = QMessageBox.question(
                self, "إعادة التفعيل",
                "الخدمة معطّلة حاليًا.\n"
                "هل تريد إعادة تفعيلها؟",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return

            try:
                self.db.activate_service(sid)
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل التفعيل:\n{e}")
                return

            QMessageBox.information(self, "تم", "تم إعادة تفعيل الخدمة.")

        self.refresh()

    # ============================================
    # ✅ Permanent Delete — حذف نهائي
    # ============================================
    def _permanent_delete(self):
        """حذف نهائي للخدمة (لو مفيش حجوزات مرتبطة)."""
        sid, is_active = self._get_selected_info()
        if sid is None:
            QMessageBox.warning(self, "خطأ", "اختار خدمة من القائمة الأول")
            return

        # احصل على اسم الخدمة
        try:
            service = self.db.get_service(sid)
            if not service:
                QMessageBox.warning(self, "خطأ", "الخدمة مش موجودة")
                return
            service_name = service[1]
        except Exception:
            service_name = "الخدمة"

        # ✅ تأكيد مزدوج
        reply = QMessageBox.warning(
            self, "⚠️  تأكيد الحذف النهائي",
            f"⚠️  تحذير مهم!\n\n"
            f"هتحذف الخدمة «{service_name}» نهائيًا!\n\n"
            f"• الخدمة هتتشال من قاعدة البيانات\n"
            f"• مش هينفع نرجعها تاني\n"
            f"• لو عايز توقفها مؤقتًا فقط، استخدم «تعطيل»\n\n"
            f"متأكد إنك عايز تكمل؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        # ✅ نفذ الحذف
        try:
            ok, msg = self.db.delete_service(sid)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل الحذف:\n{e}")
            return

        if not ok:
            QMessageBox.warning(
                self, "مش ممكن الحذف",
                f"{msg}\n\n"
                f"💡  الحل:\n"
                f"• استخدم «تعطيل» بدل الحذف\n"
                f"• أو احذف الحجوزات المرتبطة الأول"
            )
            return

        QMessageBox.information(self, "تم", "✅ تم حذف الخدمة نهائيًا.")
        self.refresh()