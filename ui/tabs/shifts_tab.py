"""
Shifts Tab — PySide6 with full DPI-aware centering.
Handles Windows Scale (125%, 150%) correctly.
+ Light/Dark theme support (reads from Theme).
"""

import os
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QDialog, QAbstractItemView,
    QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor, QGuiApplication

from utils.theme import Theme


try:
    import openpyxl
    from openpyxl.styles import Font
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False


# ============================================================
# Stat Card
# ============================================================
class StatCard(QFrame):
    """بطاقة صغيرة: عنوان فوق + قيمة تحت."""

    def __init__(self, label_text, value_text,
                 value_color=None,
                 border_color=None,
                 parent=None):
        super().__init__(parent)

        if border_color is None:
            border_color = Theme.color("border")
        if value_color is None:
            value_color = Theme.color("text")

        self.setStyleSheet(
            f"QFrame {{ background-color: {Theme.color('surface')}; "
            f"border: 1px solid {border_color}; border-radius: 12px; }}"
        )
        self.setMinimumHeight(75)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(2)

        label = QLabel(label_text)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(
            f"color: {Theme.color('text_muted')}; font-size: 11px; "
            f"font-weight: bold; background: transparent; padding: 2px;"
        )
        layout.addWidget(label)

        value = QLabel(str(value_text))
        value.setAlignment(Qt.AlignCenter)
        value.setWordWrap(True)
        value.setStyleSheet(
            f"color: {value_color}; font-size: 14px; font-weight: bold; "
            f"background: transparent; padding: 2px;"
        )
        layout.addWidget(value)


# ============================================================
# Shift Details Dialog
# ============================================================
class ShiftDetailsDialog(QDialog):
    """حوار تفاصيل الوردية."""

    def __init__(self, parent=None, shift=None):
        super().__init__(parent)
        self.shift = shift
        self._centered = False

        shift_id = shift.get("id", "?")
        self.setWindowTitle(f"تفاصيل الوردية #{shift_id}")
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
            QLabel#dialogTitle {{
                color: {Theme.color('primary')};
                font-size: 20px;
                font-weight: bold;
                padding: 6px;
                background: transparent;
            }}
            QLabel#sectionHeading {{
                color: {Theme.color('primary')};
                font-size: 14px;
                font-weight: bold;
                padding: 6px 4px;
                background: transparent;
            }}
            QFrame#separator {{
                background-color: {Theme.color('border')};
                border: none;
            }}
            QTableWidget {{
                background-color: {Theme.color('bg')};
                alternate-background-color: {Theme.color('surface')};
                color: {Theme.color('text')};
                border: 1px solid {Theme.color('border')};
                border-radius: 8px;
                gridline-color: {Theme.color('surface')};
                selection-background-color: {Theme.color('primary')};
                selection-color: #ffffff;
                font-size: 12px;
            }}
            QTableWidget::item {{
                padding: 6px;
                border: none;
            }}
            QHeaderView::section {{
                background-color: {Theme.color('surface')};
                color: {Theme.color('text')};
                padding: 8px 6px;
                border: none;
                border-bottom: 2px solid {Theme.color('primary')};
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton#dialogCloseBtn {{
                background-color: {Theme.color('surface_alt')};
                color: {Theme.color('text')};
                border: 1px solid {Theme.color('border_strong')};
                border-radius: 8px;
                padding: 10px 32px;
                font-size: 13px;
                font-weight: bold;
                min-height: 24px;
            }}
            QPushButton#dialogCloseBtn:hover {{
                background-color: {Theme.color('border_strong')};
            }}
        """)

        self.resize(800, 680)
        self.setMinimumSize(450, 400)

        # ============================================
        # QScrollArea لكل المحتوى — عشان يدعم أي حجم
        # ============================================
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
        )

        content = QWidget()
        content.setStyleSheet("background: transparent;")

        main = QVBoxLayout(content)
        main.setContentsMargins(18, 18, 18, 18)
        main.setSpacing(10)

        # ---- العنوان ----
        title = QLabel(f"📄  تفاصيل الوردية #{shift_id}")
        title.setObjectName("dialogTitle")
        title.setAlignment(Qt.AlignCenter)
        main.addWidget(title)

        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFixedHeight(1)
        main.addWidget(sep)

        # ---- بطاقات المعلومات ----
        info_grid = QGridLayout()
        info_grid.setSpacing(8)

        info_grid.addWidget(StatCard(
            "رقم الوردية", str(shift.get("id", "—")),
        ), 0, 0)

        info_grid.addWidget(StatCard(
            "عدد الحجوزات", str(shift.get("total_bookings", 0)),
        ), 0, 1)

        info_grid.addWidget(StatCard(
            "البداية", shift.get("start_time", "—"),
        ), 1, 0)

        info_grid.addWidget(StatCard(
            "النهاية", shift.get("end_time") or "مازالت مفتوحة",
        ), 1, 1)

        main.addLayout(info_grid)

        # ---- بطاقة الإجمالي ----
        main.addWidget(StatCard(
            "💰  إجمالي الإيرادات",
            f"{shift.get('total_revenue', 0):.2f} ج",
            value_color=Theme.color("success"),
            border_color=Theme.color("success"),
        ))

        # ---- طرق الدفع ----
        pay_title = QLabel("💳  توزيع الإيرادات حسب طريقة الدفع:")
        pay_title.setObjectName("sectionHeading")
        pay_title.setAlignment(Qt.AlignRight)
        main.addWidget(pay_title)

        pay_grid = QGridLayout()
        pay_grid.setSpacing(8)

        cash = shift.get("cash_total", 0) or 0
        card_val = shift.get("card_total", 0) or 0
        wallet = shift.get("wallet_total", 0) or 0

        pay_grid.addWidget(StatCard(
            "💵  كاش", f"{cash:.2f} ج",
            value_color=Theme.color("success"),
        ), 0, 0)

        pay_grid.addWidget(StatCard(
            "💳  فيزا / كارت", f"{card_val:.2f} ج",
            value_color=Theme.color("primary"),
        ), 0, 1)

        pay_grid.addWidget(StatCard(
            "📱  محفظة إلكترونية", f"{wallet:.2f} ج",
            value_color=Theme.color("warning"),
        ), 0, 2)

        main.addLayout(pay_grid)

        # ---- الحجوزات ----
        bookings_title = QLabel("📋  الحجوزات خلال الوردية:")
        bookings_title.setObjectName("sectionHeading")
        bookings_title.setAlignment(Qt.AlignRight)
        main.addWidget(bookings_title)

        bookings_table = self._build_bookings_table(shift)
        bookings_table.setMinimumHeight(180)
        main.addWidget(bookings_table)

        # ---- زر الإغلاق ----
        close_btn = QPushButton("إغلاق")
        close_btn.setObjectName("dialogCloseBtn")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setFixedHeight(46)
        close_btn.setMinimumWidth(200)
        close_btn.clicked.connect(self.reject)

        footer = QHBoxLayout()
        footer.addStretch(1)
        footer.addWidget(close_btn)
        footer.addStretch(1)
        main.addLayout(footer)

        main.addStretch(1)

        scroll.setWidget(content)

        # الحوار كله = scroll area
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    # ============================================
    # DPI-aware Centering
    # ============================================
    def showEvent(self, event):
        super().showEvent(event)
        if not self._centered:
            QTimer.singleShot(0, self._do_center)
            QTimer.singleShot(80, self._do_center)
            QTimer.singleShot(200, self._do_center)

    def _do_center(self):
        try:
            screen = QGuiApplication.primaryScreen()
            if screen is None:
                return
            geo = screen.availableGeometry()
            sw, sh = geo.width(), geo.height()

            w = min(800, int(sw * 0.70))
            h = min(720, int(sh * 0.85))
            w = max(w, 450)
            h = max(h, 400)

            self.resize(w, h)

            x = geo.x() + (sw - w) // 2
            y = geo.y() + (sh - h) // 2
            self.move(max(x, 0), max(y, 0))
            self._centered = True
        except Exception:
            pass

    # ============================================
    # Bookings Table
    # ============================================
    def _build_bookings_table(self, shift):
        bookings = shift.get("bookings", [])

        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(
            ["الوقت", "العميل", "الخدمة", "السعر", "الحلاق"]
        )
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setShowGrid(False)
        table.setLayoutDirection(Qt.RightToLeft)

        # ✅ إعدادات تجعل الجدول يتأقلم مع أي حجم
        table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        header = table.horizontalHeader()
        for i in range(5):
            header.setSectionResizeMode(i, QHeaderView.Stretch)

        if not bookings:
            table.setRowCount(1)
            empty = QTableWidgetItem("لا توجد حجوزات خلال هذه الوردية")
            empty.setTextAlignment(Qt.AlignCenter)
            empty.setForeground(QColor(Theme.color("text_dim")))
            table.setSpan(0, 0, 1, 5)
            table.setItem(0, 0, empty)
            return table

        table.setRowCount(len(bookings))
        green = QColor(Theme.color("success"))
        text_color = QColor(Theme.color("text"))

        for row, b in enumerate(bookings):
            try:
                bid, cname, sname, price, barber, date, time_ = b[:7]
                extra_total = b[8] if len(b) > 8 else 0
                total = price + (extra_total or 0)

                for col, val in enumerate(
                    [str(time_), cname, sname, f"{total:.2f} ج", barber]
                ):
                    item = QTableWidgetItem(val)
                    item.setTextAlignment(Qt.AlignCenter)
                    if col == 3:
                        item.setForeground(green)
                    else:
                        item.setForeground(text_color)
                    table.setItem(row, col, item)
            except Exception:
                continue

        return table


# ============================================================
# Shifts Tab (main)
# ============================================================
class ShiftsTab(QWidget):
    """تاب إدارة الورديات."""

    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user
        self.can_manage = user.has_permission("manage_shifts")
        self.can_export = user.has_permission("export_shifts")

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("🕐  إدارة الورديات")
        title.setStyleSheet(
            f"font-size: 22px; font-weight: bold; "
            f"color: {Theme.color('primary')}; padding: 4px; "
            f"background: transparent;"
        )
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # ============================================
        # Status Card
        # ============================================
        status_card = QFrame()
        status_card.setStyleSheet(
            f"QFrame {{ background-color: {Theme.color('surface')}; "
            f"border: 1px solid {Theme.color('border')}; border-radius: 12px; }}"
        )
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(24, 20, 24, 20)
        status_layout.setSpacing(16)

        card_title = QLabel("📊  حالة الوردية الحالية")
        card_title.setStyleSheet(
            f"font-size: 15px; font-weight: bold; "
            f"color: {Theme.color('text')}; background: transparent; "
            f"padding: 0 4px;"
        )
        card_title.setAlignment(Qt.AlignRight)
        status_layout.addWidget(card_title)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setMinimumHeight(56)
        status_layout.addWidget(self.status_label)

        if self.can_manage:
            btns_row = QHBoxLayout()
            btns_row.setSpacing(12)
            btns_row.addStretch()

            self.start_btn = QPushButton("▶  بدء وردية")
            self.start_btn.setMinimumHeight(48)
            self.start_btn.setMinimumWidth(180)
            self.start_btn.setCursor(Qt.PointingHandCursor)
            self.start_btn.setStyleSheet(
                f"QPushButton {{ background-color: {Theme.color('success')}; "
                f"color: white; border: none; border-radius: 8px; "
                f"font-size: 13px; font-weight: bold; padding: 10px 20px; }}"
                f"QPushButton:hover {{ background-color: {Theme.color('success_hover')}; }}"
                f"QPushButton:disabled {{ background-color: {Theme.color('border')}; "
                f"color: {Theme.color('text_dim')}; }}"
            )
            self.start_btn.clicked.connect(self._start_shift)
            btns_row.addWidget(self.start_btn)

            self.end_btn = QPushButton("■  إنهاء الوردية")
            self.end_btn.setMinimumHeight(48)
            self.end_btn.setMinimumWidth(180)
            self.end_btn.setCursor(Qt.PointingHandCursor)
            self.end_btn.setStyleSheet(
                f"QPushButton {{ background-color: {Theme.color('danger')}; "
                f"color: white; border: none; border-radius: 8px; "
                f"font-size: 13px; font-weight: bold; padding: 10px 20px; }}"
                f"QPushButton:hover {{ background-color: {Theme.color('danger_hover')}; }}"
                f"QPushButton:disabled {{ background-color: {Theme.color('border')}; "
                f"color: {Theme.color('text_dim')}; }}"
            )
            self.end_btn.clicked.connect(self._end_shift)
            btns_row.addWidget(self.end_btn)

            btns_row.addStretch()
            status_layout.addLayout(btns_row)

        layout.addWidget(status_card)

        # ============================================
        # Actions
        # ============================================
        actions = QHBoxLayout()
        actions.setSpacing(10)

        details_btn = QPushButton("📄  عرض تفاصيل الوردية")
        details_btn.setMinimumHeight(42)
        details_btn.setCursor(Qt.PointingHandCursor)
        details_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('primary')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"font-size: 13px; font-weight: bold; padding: 10px 20px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('primary_hover')}; }}"
        )
        details_btn.clicked.connect(self._view_details)
        actions.addWidget(details_btn)

        if self.can_export:
            export_btn = QPushButton("📊  تصدير Excel")
            export_btn.setMinimumHeight(42)
            export_btn.setCursor(Qt.PointingHandCursor)
            export_btn.setStyleSheet(
                f"QPushButton {{ background-color: {Theme.color('success')}; "
                f"color: white; border: none; border-radius: 8px; "
                f"font-size: 13px; font-weight: bold; padding: 10px 20px; }}"
                f"QPushButton:hover {{ background-color: {Theme.color('success_hover')}; }}"
            )
            export_btn.clicked.connect(self._export_excel)
            actions.addWidget(export_btn)

        actions.addStretch()
        layout.addLayout(actions)

        # ============================================
        # Table Card
        # ============================================
        table_card = QFrame()
        table_card.setStyleSheet(
            f"QFrame {{ background-color: {Theme.color('surface')}; "
            f"border: 1px solid {Theme.color('border')}; border-radius: 12px; }}"
        )
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(16, 16, 16, 16)
        table_layout.setSpacing(10)

        tbl_title = QLabel("📋  سجل الورديات")
        tbl_title.setStyleSheet(
            f"font-size: 15px; font-weight: bold; "
            f"color: {Theme.color('text')}; background: transparent; "
            f"padding: 0 4px;"
        )
        tbl_title.setAlignment(Qt.AlignRight)
        table_layout.addWidget(tbl_title)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["#", "البداية", "النهاية", "الإيرادات", "عدد الحجوزات", "الحالة"]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setMinimumHeight(280)
        self.table.setLayoutDirection(Qt.RightToLeft)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.setSectionResizeMode(5, QHeaderView.Fixed)

        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(3, 140)
        self.table.setColumnWidth(4, 130)
        self.table.setColumnWidth(5, 120)

        self.table.doubleClicked.connect(self._view_details)

        table_layout.addWidget(self.table)
        layout.addWidget(table_card)

    # ============================================
    # Refresh
    # ============================================
    def refresh(self):
        try:
            shifts = self.db.list_shifts()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل الورديات:\n{e}")
            return

        self._update_status_card()

        self.table.blockSignals(True)
        self.table.setRowCount(len(shifts))

        green = QColor(Theme.color("success"))
        gray = QColor(Theme.color("text_dim"))
        text_color = QColor(Theme.color("text"))

        for row, (sid, start, end, revenue, count, status) in enumerate(shifts):
            item_id = QTableWidgetItem(str(sid))
            item_id.setTextAlignment(Qt.AlignCenter)
            item_id.setData(Qt.UserRole, sid)
            item_id.setForeground(text_color)
            self.table.setItem(row, 0, item_id)

            item_start = QTableWidgetItem(str(start))
            item_start.setTextAlignment(Qt.AlignCenter)
            item_start.setForeground(text_color)
            self.table.setItem(row, 1, item_start)

            item_end = QTableWidgetItem(end or "—")
            item_end.setTextAlignment(Qt.AlignCenter)
            item_end.setForeground(text_color)
            self.table.setItem(row, 2, item_end)

            item_rev = QTableWidgetItem(f"{(revenue or 0):.2f} ج")
            item_rev.setTextAlignment(Qt.AlignCenter)
            item_rev.setForeground(text_color)
            self.table.setItem(row, 3, item_rev)

            item_count = QTableWidgetItem(str(count or 0))
            item_count.setTextAlignment(Qt.AlignCenter)
            item_count.setForeground(text_color)
            self.table.setItem(row, 4, item_count)

            if status == "open":
                item_status = QTableWidgetItem("🟢  مفتوحة")
                item_status.setForeground(green)
            else:
                item_status = QTableWidgetItem("⚪  مغلقة")
                item_status.setForeground(gray)
            item_status.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, item_status)

        self.table.blockSignals(False)

    def _update_status_card(self):
        try:
            open_shift = self.db.get_open_shift()
        except Exception:
            open_shift = None

        if open_shift:
            time_part = open_shift[1][11:16] if len(open_shift[1]) >= 16 else open_shift[1]
            self.status_label.setText(
                f"🟢  وردية مفتوحة حاليًا من الساعة {time_part}"
            )
            self.status_label.setStyleSheet(
                f"font-size: 18px; font-weight: bold; "
                f"color: {Theme.color('success')}; padding: 10px; "
                f"background: transparent;"
            )
        else:
            self.status_label.setText("⚪  لا توجد وردية مفتوحة حاليًا")
            self.status_label.setStyleSheet(
                f"font-size: 18px; font-weight: bold; "
                f"color: {Theme.color('text_muted')}; padding: 10px; "
                f"background: transparent;"
            )

        if self.can_manage:
            try:
                if open_shift:
                    self.start_btn.setEnabled(False)
                    self.end_btn.setEnabled(True)
                else:
                    self.start_btn.setEnabled(True)
                    self.end_btn.setEnabled(False)
            except Exception:
                pass

    # ============================================
    # Actions
    # ============================================
    def _start_shift(self):
        try:
            result = self.db.start_shift()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل بدء الوردية:\n{e}")
            return

        if result is None:
            QMessageBox.warning(
                self, "تنبيه",
                "فيه وردية مفتوحة بالفعل.\n"
                "لازم تنهيها الأول قبل ما تبدأ وردية جديدة."
            )
            return

        time_part = result[11:16] if len(result) >= 16 else result
        QMessageBox.information(
            self, "تم", f"✅  بدأت الوردية الساعة {time_part}"
        )
        self.refresh()

    def _end_shift(self):
        try:
            open_shift = self.db.get_open_shift()
        except Exception:
            open_shift = None

        if not open_shift:
            QMessageBox.warning(self, "تنبيه", "مفيش وردية مفتوحة دلوقتي.")
            return

        reply = QMessageBox.question(
            self, "تأكيد",
            "متأكد إنك عايز تنهي الوردية دلوقتي؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        try:
            result = self.db.end_shift()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل إنهاء الوردية:\n{e}")
            return

        self.refresh()

        if result:
            dlg = ShiftDetailsDialog(self, shift=result)
            dlg.exec()

    def _get_selected_shift_id(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        row_idx = rows[0].row()
        item = self.table.item(row_idx, 0)
        if item is None:
            return None
        return item.data(Qt.UserRole)

    def _view_details(self):
        sid = self._get_selected_shift_id()
        if sid is None:
            QMessageBox.warning(self, "خطأ", "اختار وردية من القائمة الأول")
            return

        try:
            details = self.db.get_shift_details(sid)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل التفاصيل:\n{e}")
            return

        if not details:
            QMessageBox.warning(self, "خطأ", "الوردية مش موجودة.")
            return

        dlg = ShiftDetailsDialog(self, shift=details)
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
            wb = openpyxl.Workbook()

            ws1 = wb.active
            ws1.title = "الشفتات"
            ws1.append([
                "#", "البداية", "النهاية", "الإيرادات",
                "عدد الحجوزات", "كاش", "كارت", "محفظة", "الحالة",
            ])
            for cell in ws1[1]:
                cell.font = Font(bold=True)

            for sid, start, end, revenue, count, status in self.db.list_shifts():
                details = self.db.get_shift_details(sid) or {}
                ws1.append([
                    sid, start, end or "—",
                    revenue or 0, count or 0,
                    details.get("cash_total", 0),
                    details.get("card_total", 0),
                    details.get("wallet_total", 0),
                    "مفتوحة" if status == "open" else "مغلقة",
                ])

            ws2 = wb.create_sheet("الحجوزات")
            ws2.append([
                "الوردية#", "الوقت", "العميل", "الخدمة",
                "السعر", "الحلاق", "التاريخ",
            ])
            for cell in ws2[1]:
                cell.font = Font(bold=True)

            for sid, *_ in self.db.list_shifts():
                details = self.db.get_shift_details(sid)
                if not details:
                    continue
                for b in details.get("bookings", []):
                    try:
                        bid, cname, sname, price, barber, date, time_ = b[:7]
                        extra_total = b[8] if len(b) > 8 else 0
                        total = price + (extra_total or 0)
                        ws2.append([sid, time_, cname, sname,
                                     total, barber, date])
                    except Exception:
                        continue

            reports_dir = os.path.join(self.db.base_dir, "reports")
            os.makedirs(reports_dir, exist_ok=True)
            stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            file_path = os.path.join(reports_dir, f"shifts_{stamp}.xlsx")
            wb.save(file_path)

            if os.name == "nt":
                os.startfile(file_path)

            QMessageBox.information(
                self, "تم",
                f"تم حفظ التقرير في:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل التصدير:\n{e}")