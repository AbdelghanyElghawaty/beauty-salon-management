"""
Audit Log Tab — سجل العمليات (للأدمن فقط).
+ Light/Dark theme support (reads from Theme).

- عرض آخر 500 عملية افتراضيًا
- فلترة بالمستخدم / نوع العملية / الجدول / التاريخ
- نافذة تفاصيل عند الدبل كليك (JSON كامل)
- تصدير Excel
"""

import os
import json
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QDialog, QAbstractItemView,
    QComboBox, QLineEdit, QTextEdit, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QGuiApplication

from theme import Theme


try:
    import openpyxl
    from openpyxl.styles import Font as XLFont
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False


# ============================================================
# Labels
# ============================================================
ACTION_LABELS = {
    "create":         "➕  إضافة",
    "update":         "✏️  تعديل",
    "delete":         "🗑️  حذف",
    "activate":       "✅  تفعيل",
    "deactivate":     "🚫  تعطيل",
    "login":          "🔑  دخول",
    "login_failed":   "⚠️  دخول فاشل",
    "logout":         "⏻  خروج",
    "start":          "▶  بدء وردية",
    "end":            "■  إنهاء وردية",
    "restore":        "♻️  استعادة نسخة",
    "update_password": "🔐  تغيير باسورد",
    "upgrade_hash":   "🔒  ترقية تشفير",
}

TABLE_LABELS = {
    "services":  "💈 الخدمات",
    "customers": "👥 العملاء",
    "bookings":  "📅 الحجوزات",
    "shifts":    "🕐 الورديات",
    "users":     "👤 المستخدمين",
    "settings":  "⚙️ الإعدادات",
}


def _action_color(action):
    """يرجع اللون المناسب لكل نوع عملية (theme-aware)."""
    mapping = {
        "create":         "success",
        "update":         "primary",
        "delete":         "danger",
        "activate":       "success",
        "deactivate":     "warning",
        "login":          "info",
        "login_failed":   "danger",
        "logout":         "text_muted",
        "start":          "success",
        "end":            "danger",
        "restore":        "warning",
        "update_password": "primary",
        "upgrade_hash":   "info",
    }
    return Theme.color(mapping.get(action, "text"))


# ============================================================
# Details Dialog
# ============================================================
class AuditDetailsDialog(QDialog):
    """نافذة تفاصيل عملية من السجل."""

    def __init__(self, parent=None, entry=None):
        super().__init__(parent)
        self.setWindowTitle("تفاصيل العملية")
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
            QLabel#title {{
                color: {Theme.color('primary')};
                font-size: 15pt;
                font-weight: bold;
                padding: 4px;
                background: transparent;
            }}
            QLabel#fieldName {{
                color: {Theme.color('text_muted')};
                font-size: 10pt;
                font-weight: bold;
                background: transparent;
            }}
            QLabel#fieldValue {{
                color: {Theme.color('text')};
                font-size: 11pt;
                background: transparent;
            }}
            QLabel#sectionLabel {{
                color: {Theme.color('primary')};
                font-size: 11pt;
                font-weight: bold;
                padding: 4px 0;
                background: transparent;
            }}
            QTextEdit {{
                background-color: {Theme.color('surface')};
                color: {Theme.color('text')};
                border: 1px solid {Theme.color('border')};
                border-radius: 6px;
                padding: 8px;
                font-family: 'Consolas', monospace;
                font-size: 10pt;
            }}
            QFrame#separator {{
                background-color: {Theme.color('border')};
                border: none;
            }}
        """)

        self.resize(680, 620)
        self.setMinimumSize(520, 460)

        main = QVBoxLayout(self)
        main.setContentsMargins(22, 20, 22, 20)
        main.setSpacing(12)

        entry_id = entry[0] if entry else "?"
        title = QLabel(f"📄  تفاصيل العملية #{entry_id}")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        main.addWidget(title)

        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFixedHeight(1)
        main.addWidget(sep)

        if not entry:
            main.addWidget(QLabel("لا توجد بيانات."))
            self._add_close_btn(main)
            return

        eid, username, action, table_name, record_id, old_val, new_val, ts = entry

        action_text = ACTION_LABELS.get(action, action)
        table_text = TABLE_LABELS.get(table_name, table_name or "—")

        # ---- معلومات أساسية ----
        info_grid = QGridLayout()
        info_grid.setHorizontalSpacing(14)
        info_grid.setVerticalSpacing(8)

        self._add_field(info_grid, 0, 0, "المستخدم:", username or "—")
        self._add_field(info_grid, 0, 1, "العملية:", action_text)
        self._add_field(info_grid, 1, 0, "الجدول:", table_text)
        self._add_field(info_grid, 1, 1, "رقم السجل:", str(record_id or "—"))
        self._add_field(info_grid, 2, 0, "التاريخ:", ts or "—")
        info_grid.setColumnStretch(0, 1)
        info_grid.setColumnStretch(1, 1)
        main.addLayout(info_grid)

        sep2 = QFrame()
        sep2.setObjectName("separator")
        sep2.setFixedHeight(1)
        main.addWidget(sep2)

        # ---- القيم ----
        lbl1 = QLabel("📥  القيمة القديمة (JSON):")
        lbl1.setObjectName("sectionLabel")
        main.addWidget(lbl1)
        main.addWidget(self._json_view(old_val), stretch=1)

        lbl2 = QLabel("📤  القيمة الجديدة (JSON):")
        lbl2.setObjectName("sectionLabel")
        main.addWidget(lbl2)
        main.addWidget(self._json_view(new_val), stretch=1)

        self._add_close_btn(main)

        QTimer.singleShot(30, self._center)

    def _add_field(self, grid, row, col, name, value):
        wrap = QWidget()
        wrap.setStyleSheet("background: transparent;")
        v = QHBoxLayout(wrap)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(8)

        n = QLabel(name)
        n.setObjectName("fieldName")
        n.setMinimumWidth(80)
        v.addWidget(n)

        val = QLabel(str(value))
        val.setObjectName("fieldValue")
        val.setWordWrap(True)
        v.addWidget(val, stretch=1)

        grid.addWidget(wrap, row, col)

    def _json_view(self, raw):
        view = QTextEdit()
        view.setReadOnly(True)
        view.setMinimumHeight(100)
        view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        if not raw:
            view.setPlainText("(لا يوجد)")
            view.setStyleSheet(
                f"QTextEdit {{ background-color: {Theme.color('bg')}; "
                f"color: {Theme.color('text_dim')}; "
                f"border: 1px solid {Theme.color('border')}; "
                f"border-radius: 6px; padding: 8px; "
                f"font-family: 'Consolas', monospace; font-size: 10pt; }}"
            )
            return view

        try:
            data = json.loads(raw)
            pretty = json.dumps(data, ensure_ascii=False, indent=2)
            view.setPlainText(pretty)
        except Exception:
            view.setPlainText(str(raw))
        return view

    def _add_close_btn(self, layout):
        row = QHBoxLayout()
        row.addStretch()
        btn = QPushButton("إغلاق")
        btn.setFixedSize(140, 42)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('surface_alt')}; "
            f"color: {Theme.color('text')}; border: none; border-radius: 6px; "
            f"font-weight: bold; font-size: 11pt; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('border_strong')}; }}"
        )
        btn.clicked.connect(self.accept)
        row.addWidget(btn)
        layout.addLayout(row)

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
# Audit Tab
# ============================================================
class AuditTab(QWidget):
    """تاب عرض سجل العمليات — للأدمن فقط."""

    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user

        self._build_ui()
        self.refresh()

    # ============================================
    # UI
    # ============================================
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # ---- العنوان ----
        header = QHBoxLayout()
        title = QLabel("📜  سجل العمليات")
        title.setStyleSheet(
            f"font-size: 22px; font-weight: bold; "
            f"color: {Theme.color('primary')}; padding: 4px; "
            f"background: transparent;"
        )
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # ---- Filters Card ----
        filters_card = QFrame()
        filters_card.setStyleSheet(
            f"QFrame {{ background-color: {Theme.color('surface')}; "
            f"border: 1px solid {Theme.color('border')}; border-radius: 12px; }}"
        )
        filters_layout = QVBoxLayout(filters_card)
        filters_layout.setContentsMargins(18, 14, 18, 14)
        filters_layout.setSpacing(10)

        f_title = QLabel("🔍  فلترة")
        f_title.setStyleSheet(
            f"font-size: 13px; font-weight: bold; "
            f"color: {Theme.color('primary')}; background: transparent; "
            f"padding: 0 4px;"
        )
        filters_layout.addWidget(f_title)

        row1 = QHBoxLayout()
        row1.setSpacing(10)

        row1.addWidget(self._lbl("المستخدم:"))
        self.user_filter = QComboBox()
        self.user_filter.setMinimumHeight(38)
        self.user_filter.setMinimumWidth(150)
        self.user_filter.addItem("الكل", None)
        row1.addWidget(self.user_filter)

        row1.addWidget(self._lbl("العملية:"))
        self.action_filter = QComboBox()
        self.action_filter.setMinimumHeight(38)
        self.action_filter.setMinimumWidth(150)
        self.action_filter.addItem("الكل", None)
        for key, label in ACTION_LABELS.items():
            self.action_filter.addItem(label, key)
        row1.addWidget(self.action_filter)

        row1.addWidget(self._lbl("الجدول:"))
        self.table_filter = QComboBox()
        self.table_filter.setMinimumHeight(38)
        self.table_filter.setMinimumWidth(150)
        self.table_filter.addItem("الكل", None)
        for key, label in TABLE_LABELS.items():
            self.table_filter.addItem(label, key)
        row1.addWidget(self.table_filter)

        row1.addStretch()
        filters_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(10)

        row2.addWidget(self._lbl("من:"))
        self.date_from = QLineEdit()
        self.date_from.setPlaceholderText("YYYY-MM-DD")
        self.date_from.setMinimumHeight(38)
        self.date_from.setMaximumWidth(150)
        self.date_from.setAlignment(Qt.AlignCenter)
        row2.addWidget(self.date_from)

        row2.addWidget(self._lbl("إلى:"))
        self.date_to = QLineEdit()
        self.date_to.setPlaceholderText("YYYY-MM-DD")
        self.date_to.setMinimumHeight(38)
        self.date_to.setMaximumWidth(150)
        self.date_to.setAlignment(Qt.AlignCenter)
        row2.addWidget(self.date_to)

        apply_btn = QPushButton("🔍  تطبيق الفلتر")
        apply_btn.setMinimumHeight(38)
        apply_btn.setMinimumWidth(140)
        apply_btn.setCursor(Qt.PointingHandCursor)
        apply_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('primary')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"font-weight: bold; font-size: 12px; padding: 6px 14px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('primary_hover')}; }}"
        )
        apply_btn.clicked.connect(self.refresh)
        row2.addWidget(apply_btn)

        clear_btn = QPushButton("↺  مسح الفلتر")
        clear_btn.setMinimumHeight(38)
        clear_btn.setMinimumWidth(120)
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('surface_alt')}; "
            f"color: {Theme.color('text')}; border: none; border-radius: 8px; "
            f"font-weight: bold; font-size: 12px; padding: 6px 14px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('border_strong')}; }}"
        )
        clear_btn.clicked.connect(self._clear_filters)
        row2.addWidget(clear_btn)

        row2.addStretch()

        export_btn = QPushButton("📊  تصدير Excel")
        export_btn.setMinimumHeight(38)
        export_btn.setMinimumWidth(160)
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('success')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"font-weight: bold; font-size: 12px; padding: 6px 14px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('success_hover')}; }}"
        )
        export_btn.clicked.connect(self._export_excel)
        row2.addWidget(export_btn)

        filters_layout.addLayout(row2)
        layout.addWidget(filters_card)

        # ---- Table Card ----
        table_card = QFrame()
        table_card.setStyleSheet(
            f"QFrame {{ background-color: {Theme.color('surface')}; "
            f"border: 1px solid {Theme.color('border')}; border-radius: 12px; }}"
        )
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(16, 16, 16, 16)
        table_layout.setSpacing(10)

        self.count_label = QLabel("📋  السجل (0 عملية)")
        self.count_label.setStyleSheet(
            f"font-size: 14px; font-weight: bold; "
            f"color: {Theme.color('primary')}; background: transparent; "
            f"padding: 0 4px;"
        )
        table_layout.addWidget(self.count_label)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["#", "المستخدم", "العملية", "الجدول", "#السجل", "التاريخ"]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setMinimumHeight(400)
        self.table.setLayoutDirection(Qt.RightToLeft)

        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Fixed)
        h.setSectionResizeMode(1, QHeaderView.Fixed)
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        h.setSectionResizeMode(3, QHeaderView.Stretch)
        h.setSectionResizeMode(4, QHeaderView.Fixed)
        h.setSectionResizeMode(5, QHeaderView.Stretch)

        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(4, 90)

        self.table.doubleClicked.connect(self._show_details)

        table_layout.addWidget(self.table)
        layout.addWidget(table_card)

        self._reload_user_filter()

    def _lbl(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {Theme.color('text')}; font-size: 12px; "
            f"font-weight: bold; background: transparent; padding: 0 4px;"
        )
        return lbl

    # ============================================
    # Filters
    # ============================================
    def _reload_user_filter(self):
        try:
            current = self.user_filter.currentData()
            self.user_filter.blockSignals(True)
            self.user_filter.clear()
            self.user_filter.addItem("الكل", None)
            for uname in self.db.list_audit_usernames():
                self.user_filter.addItem(uname, uname)
            if current:
                for i in range(self.user_filter.count()):
                    if self.user_filter.itemData(i) == current:
                        self.user_filter.setCurrentIndex(i)
                        break
            self.user_filter.blockSignals(False)
        except Exception:
            pass

    def _clear_filters(self):
        self.user_filter.setCurrentIndex(0)
        self.action_filter.setCurrentIndex(0)
        self.table_filter.setCurrentIndex(0)
        self.date_from.clear()
        self.date_to.clear()
        self.refresh()

    # ============================================
    # Refresh
    # ============================================
    def refresh(self):
        username = self.user_filter.currentData()
        action = self.action_filter.currentData()
        table_name = self.table_filter.currentData()
        date_from = self.date_from.text().strip() or None
        date_to = self.date_to.text().strip() or None

        try:
            entries = self.db.list_audit_log(
                limit=500,
                username=username,
                action=action,
                table_name=table_name,
                date_from=date_from,
                date_to=date_to,
            )
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل السجل:\n{e}")
            return

        self.count_label.setText(f"📋  السجل ({len(entries)} عملية)")

        self.table.blockSignals(True)
        self.table.setRowCount(len(entries))

        text_color = QColor(Theme.color("text"))

        for row, entry in enumerate(entries):
            eid, uname, act, tbl, rec_id, _old, _new, ts = entry

            item_id = QTableWidgetItem(str(eid))
            item_id.setTextAlignment(Qt.AlignCenter)
            item_id.setData(Qt.UserRole, eid)
            item_id.setForeground(text_color)
            self.table.setItem(row, 0, item_id)

            item_user = QTableWidgetItem(uname or "—")
            item_user.setTextAlignment(Qt.AlignCenter)
            item_user.setForeground(text_color)
            self.table.setItem(row, 1, item_user)

            act_text = ACTION_LABELS.get(act, act)
            item_act = QTableWidgetItem(act_text)
            item_act.setTextAlignment(Qt.AlignCenter)
            item_act.setForeground(QColor(_action_color(act)))
            self.table.setItem(row, 2, item_act)

            item_tbl = QTableWidgetItem(TABLE_LABELS.get(tbl, tbl or "—"))
            item_tbl.setTextAlignment(Qt.AlignCenter)
            item_tbl.setForeground(text_color)
            self.table.setItem(row, 3, item_tbl)

            item_rec = QTableWidgetItem(str(rec_id) if rec_id is not None else "—")
            item_rec.setTextAlignment(Qt.AlignCenter)
            item_rec.setForeground(text_color)
            self.table.setItem(row, 4, item_rec)

            item_ts = QTableWidgetItem(ts or "—")
            item_ts.setTextAlignment(Qt.AlignCenter)
            item_ts.setForeground(text_color)
            self.table.setItem(row, 5, item_ts)

        self.table.blockSignals(False)

        self._reload_user_filter()

    # ============================================
    # Details
    # ============================================
    def _get_selected_entry_id(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        row_idx = rows[0].row()
        item = self.table.item(row_idx, 0)
        if item is None:
            return None
        return item.data(Qt.UserRole)

    def _show_details(self):
        eid = self._get_selected_entry_id()
        if eid is None:
            return
        try:
            entry = self.db.get_audit_entry(eid)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل التفاصيل:\n{e}")
            return
        if not entry:
            QMessageBox.warning(self, "خطأ", "العملية مش موجودة.")
            return

        dlg = AuditDetailsDialog(self, entry=entry)
        dlg.exec()

    # ============================================
    # Export Excel
    # ============================================
    def _export_excel(self):
        if not HAS_OPENPYXL:
            QMessageBox.critical(
                self, "غير متاح",
                "التصدير لـ Excel محتاج مكتبة openpyxl.\n\n"
                "ثبّتها بالأمر:\n"
                "pip install openpyxl"
            )
            return

        try:
            username = self.user_filter.currentData()
            action = self.action_filter.currentData()
            table_name = self.table_filter.currentData()
            date_from = self.date_from.text().strip() or None
            date_to = self.date_to.text().strip() or None

            entries = self.db.list_audit_log(
                limit=10000,
                username=username, action=action, table_name=table_name,
                date_from=date_from, date_to=date_to,
            )

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "سجل العمليات"

            ws.append([
                "#", "المستخدم", "العملية", "الجدول",
                "رقم السجل", "التاريخ", "القيمة القديمة", "القيمة الجديدة",
            ])
            for cell in ws[1]:
                cell.font = XLFont(bold=True)

            for entry in entries:
                eid, uname, act, tbl, rec_id, old_val, new_val, ts = entry
                ws.append([
                    eid,
                    uname or "",
                    ACTION_LABELS.get(act, act),
                    TABLE_LABELS.get(tbl, tbl or ""),
                    rec_id if rec_id is not None else "",
                    ts or "",
                    old_val or "",
                    new_val or "",
                ])

            for col in ws.columns:
                max_len = 0
                col_letter = col[0].column_letter
                for cell in col:
                    if cell.value is not None:
                        max_len = max(max_len, len(str(cell.value)))
                ws.column_dimensions[col_letter].width = min(max_len + 2, 60)

            reports_dir = os.path.join(self.db.base_dir, "reports")
            os.makedirs(reports_dir, exist_ok=True)
            stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            file_path = os.path.join(reports_dir, f"audit_log_{stamp}.xlsx")
            wb.save(file_path)

            if os.name == "nt":
                os.startfile(file_path)

            QMessageBox.information(
                self, "تم",
                f"تم حفظ التقرير في:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل التصدير: {e}")