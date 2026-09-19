"""
Bookings Tab — PySide6 complete file.
+ Light/Dark theme support (reads from Theme).
+ Receipt with multiple print methods + QR Code + custom color/logo
+ Uses haircut.ico as default logo
+ Uses QWebEngineView for professional receipt preview
"""

import json as _json
import os
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QDialog, QAbstractItemView,
    QLineEdit, QComboBox, QListWidget, QListWidgetItem,
    QScrollArea, QGridLayout, QSizePolicy, QTextEdit, QCalendarWidget
)
from PySide6.QtCore import Qt, QDate, QTimer
from PySide6.QtGui import QColor, QGuiApplication
from theme import Theme

# ✅ WebEngine للمعاينة الاحترافية (لو متاح)
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False


# مسار اللوجو الافتراضي (haircut.ico)
DEFAULT_LOGO_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "haircut.ico"
)


# ============================================================
# Dialog Stylesheet (dynamic)
# ============================================================
def _dialog_qss():
    """يرجع stylesheet ديناميكي للـ dialogs."""
    return f"""
    QDialog {{
        background-color: {Theme.color('bg')};
    }}
    QLabel {{
        color: {Theme.color('text')};
        background: transparent;
        font-size: 11pt;
    }}
    QLabel#cardTitle {{
        color: {Theme.color('primary')};
        font-size: 12pt;
        font-weight: bold;
        background: transparent;
        padding: 4px;
    }}
    QLabel#dialogTitle {{
        color: {Theme.color('primary')};
        font-size: 16pt;
        font-weight: bold;
        background: transparent;
        padding: 6px;
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
    QComboBox {{
        background-color: {Theme.color('surface')};
        color: {Theme.color('text')};
        border: 1px solid {Theme.color('border_strong')};
        border-radius: 6px;
        padding: 4px 12px;
        font-size: 11pt;
    }}
    QComboBox:focus {{
        border: 2px solid {Theme.color('primary')};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 30px;
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
    QListWidget {{
        background-color: {Theme.color('surface')};
        color: {Theme.color('text')};
        border: 1px solid {Theme.color('border_strong')};
        border-radius: 6px;
        padding: 6px;
        font-size: 11pt;
    }}
    QListWidget::item {{
        padding: 8px;
        border-radius: 4px;
    }}
    QListWidget::item:selected {{
        background-color: {Theme.color('primary')};
        color: #ffffff;
    }}
    QFrame#card {{
        background-color: {Theme.color('surface')};
        border: 1px solid {Theme.color('border')};
        border-radius: 10px;
    }}
    QFrame#totalCard {{
        background-color: {Theme.color('surface')};
        border: 1px solid {Theme.color('primary')};
        border-radius: 10px;
    }}
    QFrame#separator {{
        background-color: {Theme.color('border')};
        border: none;
    }}
    QCalendarWidget QWidget {{
        background-color: {Theme.color('bg')};
        color: {Theme.color('text')};
    }}
    QCalendarWidget QAbstractItemView:enabled {{
        background-color: {Theme.color('bg')};
        color: {Theme.color('text')};
        selection-background-color: {Theme.color('primary')};
        selection-color: #ffffff;
        outline: none;
    }}
    QCalendarWidget QToolButton {{
        background-color: {Theme.color('surface')};
        color: {Theme.color('text')};
        border: none;
        padding: 8px;
        font-size: 11pt;
        font-weight: bold;
    }}
    QCalendarWidget QToolButton:hover {{
        background-color: {Theme.color('surface_alt')};
    }}
    QCalendarWidget QMenu {{
        background-color: {Theme.color('surface')};
        color: {Theme.color('text')};
    }}
    QCalendarWidget QSpinBox {{
        background-color: {Theme.color('surface')};
        color: {Theme.color('text')};
    }}
    QCalendarWidget QWidget#qt_calendar_navigationbar {{
        background-color: {Theme.color('surface')};
    }}
    """


# ============================================================
# Calendar Dialog
# ============================================================
class CalendarDialog(QDialog):
    def __init__(self, parent=None, initial_date=None):
        super().__init__(parent)
        self.setWindowTitle("اختيار التاريخ")
        self.setFixedSize(380, 480)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet(_dialog_qss())
        self.selected_date = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("📅  اختار التاريخ")
        title.setObjectName("dialogTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        try:
            self.calendar = QCalendarWidget()
            self.calendar.setGridVisible(True)
            self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
            self.calendar.setLayoutDirection(Qt.RightToLeft)

            if initial_date:
                try:
                    d = QDate(initial_date.year, initial_date.month, initial_date.day)
                    self.calendar.setSelectedDate(d)
                except Exception:
                    pass

            self.calendar.clicked.connect(self._on_date_clicked)
            layout.addWidget(self.calendar)
        except Exception:
            layout.addWidget(QLabel("أدخل التاريخ بصيغة YYYY-MM-DD"))

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setFixedSize(120, 42)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('surface_alt')}; "
            f"color: {Theme.color('text')}; border: none; border-radius: 6px; "
            f"font-weight: bold; font-size: 11pt; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('border_strong')}; }}"
        )
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def _on_date_clicked(self, qdate):
        try:
            self.selected_date = f"{qdate.year():04d}-{qdate.month():02d}-{qdate.day():02d}"
            self.accept()
        except Exception:
            pass

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(30, self._center)

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
# Booking Dialog
# ============================================================
class BookingDialog(QDialog):
    """نافذة الحجز."""

    def __init__(self, parent=None, db=None, booking_id=None, current=None):
        super().__init__(parent)
        self.db = db
        self.booking_id = booking_id
        self.result_data = None

        self.setWindowTitle("تعديل الحجز" if booking_id else "حجز جديد")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet(_dialog_qss())

        if current is None:
            current = {
                "customer": "",
                "service_id": None,
                "extra_ids": [],
                "barber": "",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": "10:00",
                "payment_method": "cash",
            }

        self.services = db.list_services()

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(10)

        title = QLabel("✏️  تعديل الحجز" if booking_id else "➕  حجز جديد")
        title.setObjectName("dialogTitle")
        title.setAlignment(Qt.AlignCenter)
        title.setMinimumHeight(38)
        root.addWidget(title)

        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFixedHeight(1)
        root.addWidget(sep)

        scroll = QScrollArea()
        scroll.setObjectName("bookingScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        content = QWidget()
        content.setLayoutDirection(Qt.RightToLeft)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(2, 2, 8, 4)
        content_layout.setSpacing(10)

        card1 = self._make_card(content_layout, "📋  البيانات الأساسية")
        form1 = QGridLayout()
        form1.setContentsMargins(2, 2, 2, 2)
        form1.setHorizontalSpacing(10)
        form1.setVerticalSpacing(6)

        form1.addWidget(self._label("اسم العميل *"), 0, 0, 1, 3)
        self.customer_entry = QLineEdit(current["customer"])
        self.customer_entry.setFixedHeight(44)
        self.customer_entry.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.customer_entry.setPlaceholderText("مثال: محمد أحمد")
        form1.addWidget(self.customer_entry, 1, 0, 1, 3)

        form1.addWidget(self._label("الخدمة الأساسية *"), 2, 0, 1, 3)
        self.main_service_cb = QComboBox()
        self.main_service_cb.setFixedHeight(44)
        self.main_service_cb.setLayoutDirection(Qt.RightToLeft)
        for sid, name, price in self.services:
            self.main_service_cb.addItem(f"{name}  ({price:.0f} ج)", sid)

        if current["service_id"] is not None:
            for i in range(self.main_service_cb.count()):
                if self.main_service_cb.itemData(i) == current["service_id"]:
                    self.main_service_cb.setCurrentIndex(i)
                    break
        form1.addWidget(self.main_service_cb, 3, 0, 1, 3)

        form1.addWidget(self._label("الحلاق"), 4, 0)
        form1.addWidget(self._label("التاريخ *"), 4, 1)
        form1.addWidget(self._label("الوقت *"), 4, 2)

        self.barber_entry = QLineEdit(current["barber"])
        self.barber_entry.setFixedHeight(44)
        self.barber_entry.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.barber_entry.setPlaceholderText("اسم الحلاق")
        form1.addWidget(self.barber_entry, 5, 0)

        date_wrap = QWidget()
        date_wrap.setStyleSheet("background: transparent;")
        date_inner = QHBoxLayout(date_wrap)
        date_inner.setContentsMargins(0, 0, 0, 0)
        date_inner.setSpacing(5)

        self.date_entry = QLineEdit(current["date"])
        self.date_entry.setFixedHeight(44)
        self.date_entry.setAlignment(Qt.AlignCenter)
        date_inner.addWidget(self.date_entry, 1)

        date_btn = QPushButton("📅")
        date_btn.setFixedSize(44, 44)
        date_btn.setCursor(Qt.PointingHandCursor)
        date_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('primary')}; "
            f"color: white; border: none; border-radius: 7px; "
            f"font-size: 13pt; padding: 0; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('primary_hover')}; }}"
        )
        date_btn.clicked.connect(self._open_calendar)
        date_inner.addWidget(date_btn)
        form1.addWidget(date_wrap, 5, 1)

        self.time_entry = QLineEdit(current["time"])
        self.time_entry.setFixedHeight(44)
        self.time_entry.setAlignment(Qt.AlignCenter)
        self.time_entry.setPlaceholderText("HH:MM")
        form1.addWidget(self.time_entry, 5, 2)

        for col in range(3):
            form1.setColumnStretch(col, 1)

        card1.layout().addLayout(form1)
        content_layout.addWidget(card1)

        card2 = self._make_card(content_layout, "💳  طريقة الدفع")
        pay_row = QHBoxLayout()
        pay_row.setContentsMargins(0, 0, 0, 0)
        pay_row.setSpacing(8)

        self.payment_var = current.get("payment_method", "cash")
        self.cash_btn = self._pay_btn("💵  كاش", "cash")
        self.card_btn = self._pay_btn("💳  فيزا / كارت", "card")
        self.wallet_btn = self._pay_btn("📱  محفظة", "wallet")

        pay_row.addWidget(self.cash_btn, 1)
        pay_row.addWidget(self.card_btn, 1)
        pay_row.addWidget(self.wallet_btn, 1)

        card2.layout().addLayout(pay_row)
        content_layout.addWidget(card2)
        self._refresh_payment_buttons()

        card3 = self._make_card(content_layout, "➕  الخدمات الإضافية (اختياري)")
        extras_layout = QVBoxLayout()
        extras_layout.setContentsMargins(0, 0, 0, 0)
        extras_layout.setSpacing(7)

        add_row = QHBoxLayout()
        add_row.setContentsMargins(0, 0, 0, 0)
        add_row.setSpacing(8)

        self.extra_cb = QComboBox()
        self.extra_cb.setFixedHeight(44)
        self.extra_cb.setLayoutDirection(Qt.RightToLeft)
        for sid, name, price in self.services:
            self.extra_cb.addItem(f"{name}  ({price:.0f} ج)", sid)
        add_row.addWidget(self.extra_cb, 1)

        add_extra_btn = QPushButton("➕  إضافة")
        add_extra_btn.setFixedSize(120, 44)
        add_extra_btn.setCursor(Qt.PointingHandCursor)
        add_extra_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('success')}; "
            f"color: white; border: none; border-radius: 7px; "
            f"font-weight: bold; font-size: 11pt; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('success_hover')}; }}"
        )
        add_extra_btn.clicked.connect(self._add_extra)
        add_row.addWidget(add_extra_btn)
        extras_layout.addLayout(add_row)

        self.extra_list = QListWidget()
        self.extra_list.setMinimumHeight(64)
        self.extra_list.setMaximumHeight(110)
        self.extra_list.setLayoutDirection(Qt.RightToLeft)
        extras_layout.addWidget(self.extra_list)

        remove_extra_btn = QPushButton("🗑  حذف الخدمة المختارة")
        remove_extra_btn.setFixedHeight(40)
        remove_extra_btn.setCursor(Qt.PointingHandCursor)
        remove_extra_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('danger')}; "
            f"color: white; border: none; border-radius: 7px; "
            f"font-weight: bold; font-size: 10.5pt; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('danger_hover')}; }}"
        )
        remove_extra_btn.clicked.connect(self._remove_extra)
        extras_layout.addWidget(remove_extra_btn)

        card3.layout().addLayout(extras_layout)
        content_layout.addWidget(card3)

        self.extra_ids = list(current["extra_ids"])
        self._render_extra_list()

        total_card = QFrame()
        total_card.setObjectName("totalCard")
        total_layout = QHBoxLayout(total_card)
        total_layout.setContentsMargins(16, 8, 16, 8)
        total_layout.setSpacing(8)

        total_title = QLabel("💰  الإجمالي")
        total_title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        total_title.setStyleSheet(
            f"font-size: 12.5pt; font-weight: bold; "
            f"color: {Theme.color('text')}; background: transparent;"
        )
        total_layout.addWidget(total_title)

        total_layout.addStretch()

        self.total_label = QLabel("0.00 ج")
        self.total_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.total_label.setStyleSheet(
            f"font-size: 18pt; font-weight: bold; "
            f"color: {Theme.color('success')}; background: transparent;"
        )
        total_layout.addWidget(self.total_label)
        content_layout.addWidget(total_card)

        content_layout.addStretch(1)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        footer = QHBoxLayout()
        footer.setContentsMargins(0, 2, 0, 0)
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

        save_btn = QPushButton("✓  تأكيد الحجز" if not booking_id else "✓  حفظ التعديل")
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

        self.main_service_cb.currentIndexChanged.connect(self._update_total)
        self._update_total()

        self.setMinimumSize(620, 560)
        self.resize(760, 760)

    def _label(self, text):
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl.setMinimumHeight(24)
        lbl.setStyleSheet(
            f"QLabel {{ color: {Theme.color('text')}; font-size: 10.5pt; "
            f"font-weight: bold; background: transparent; padding: 0 2px; }}"
        )
        return lbl

    def _make_card(self, parent, title):
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 11, 14, 11)
        layout.setSpacing(6)

        title_lbl = QLabel(title)
        title_lbl.setObjectName("cardTitle")
        title_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        title_lbl.setMinimumHeight(30)
        layout.addWidget(title_lbl)
        layout.addSpacing(3)

        parent.addWidget(card)
        return card

    def _pay_btn(self, text, value):
        btn = QPushButton(text)
        btn.setMinimumHeight(46)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: self._select_payment(value))
        return btn

    def _select_payment(self, value):
        self.payment_var = value
        self._refresh_payment_buttons()

    def _refresh_payment_buttons(self):
        styles = {
            "cash": (Theme.color("success"), Theme.color("success_hover")),
            "card": (Theme.color("primary"), Theme.color("primary_hover")),
            "wallet": (Theme.color("warning"), Theme.color("warning_hover")),
        }
        for btn, value in [
            (self.cash_btn, "cash"),
            (self.card_btn, "card"),
            (self.wallet_btn, "wallet"),
        ]:
            if value == self.payment_var:
                bg, hover = styles[value]
                btn.setStyleSheet(
                    f"QPushButton {{ background-color: {bg}; color: white; "
                    f"border: 2px solid {hover}; border-radius: 7px; "
                    f"font-weight: bold; font-size: 10.5pt; padding: 6px 10px; }}"
                    f"QPushButton:hover {{ background-color: {hover}; }}"
                )
            else:
                btn.setStyleSheet(
                    f"QPushButton {{ background-color: {Theme.color('surface_alt')}; "
                    f"color: {Theme.color('text_muted')}; "
                    f"border: 1px solid {Theme.color('border_strong')}; "
                    f"border-radius: 7px; font-weight: bold; font-size: 10.5pt; "
                    f"padding: 6px 10px; }}"
                    f"QPushButton:hover {{ background-color: {Theme.color('border_strong')}; "
                    f"color: {Theme.color('text')}; }}"
                )

    def _open_calendar(self):
        try:
            current = datetime.strptime(
                self.date_entry.text().strip(), "%Y-%m-%d"
            ).date()
        except ValueError:
            current = datetime.now().date()

        dlg = CalendarDialog(self, initial_date=current)
        if dlg.exec() == QDialog.Accepted and dlg.selected_date:
            self.date_entry.setText(dlg.selected_date)

    def _add_extra(self):
        sid = self.extra_cb.currentData()
        if sid is None:
            return
        if sid in self.extra_ids:
            QMessageBox.information(self, "ملاحظة", "الخدمة دي مضافة بالفعل.")
            return
        self.extra_ids.append(sid)
        self._render_extra_list()
        self._update_total()

    def _remove_extra(self):
        row = self.extra_list.currentRow()
        if row < 0:
            return
        if 0 <= row < len(self.extra_ids):
            self.extra_ids.pop(row)
            self._render_extra_list()
            self._update_total()

    def _render_extra_list(self):
        self.extra_list.clear()
        for sid in self.extra_ids:
            for s in self.services:
                if s[0] == sid:
                    item = QListWidgetItem(f"{s[1]}   ({s[2]:.0f} ج)")
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.extra_list.addItem(item)
                    break

    def _update_total(self):
        total = 0.0
        sid = self.main_service_cb.currentData()
        if sid is not None:
            for s in self.services:
                if s[0] == sid:
                    total += s[2]
                    break
        for sid in self.extra_ids:
            for s in self.services:
                if s[0] == sid:
                    total += s[2]
                    break
        self.total_label.setText(f"{total:.2f} ج")

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(30, self._fit_and_center)

    def _fit_and_center(self):
        try:
            screen = QGuiApplication.primaryScreen()
            if screen is None:
                return
            geo = screen.availableGeometry()
            sw, sh = geo.width(), geo.height()

            w = min(780, max(620, int(sw * 0.72)))
            h = min(820, max(560, int(sh * 0.88)))

            h = min(h, max(560, sh - 40))
            w = min(w, max(620, sw - 40))

            self.resize(w, h)

            x = geo.x() + (sw - w) // 2
            y = geo.y() + (sh - h) // 2
            self.move(max(x, 0), max(y, 0))
        except Exception:
            pass

    def _save(self):
        cust_name = self.customer_entry.text().strip()
        if not cust_name:
            QMessageBox.warning(self, "خطأ", "اكتب اسم العميل")
            return

        sid = self.main_service_cb.currentData()
        if sid is None:
            QMessageBox.warning(self, "خطأ", "اختار الخدمة الأساسية")
            return

        barber = self.barber_entry.text().strip() or "غير محدد"
        date_ = self.date_entry.text().strip()
        time_ = self.time_entry.text().strip()

        try:
            datetime.strptime(date_, "%Y-%m-%d")
            datetime.strptime(time_, "%H:%M")
        except ValueError:
            QMessageBox.warning(
                self, "خطأ",
                "صيغة التاريخ (YYYY-MM-DD) أو الوقت (HH:MM) غلط"
            )
            return

        if self.db.is_slot_taken(
            barber, date_, time_, exclude_booking_id=self.booking_id
        ):
            if QMessageBox.question(
                self,
                "الميعاد محجوز",
                f"الحلاق {barber} عنده حجز تاني في {date_} الساعة {time_}.\nتحفظ برضو؟"
            ) != QMessageBox.Yes:
                return

        cust_id = None
        for cid, cname, _phone, _ in self.db.list_customers():
            if cname.strip().lower() == cust_name.lower():
                cust_id = cid
                break

        if cust_id is None:
            self.db.add_customer(cust_name, "")
            for cid, cname, _phone, _ in self.db.list_customers():
                if cname.strip().lower() == cust_name.lower():
                    cust_id = cid
                    break

        if cust_id is None:
            QMessageBox.critical(self, "خطأ", "فشل إنشاء العميل")
            return

        self.result_data = {
            "customer_id": cust_id,
            "service_id": sid,
            "extra_ids": list(self.extra_ids),
            "barber": barber,
            "date": date_,
            "time": time_,
            "payment_method": self.payment_var,
        }
        self.accept()


# ============================================================
# Bookings Tab
# ============================================================
class BookingsTab(QWidget):
    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user
        self.can_edit = user.has_permission("edit_bookings")

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("📅  إدارة الحجوزات")
        title.setStyleSheet(
            f"font-size: 18pt; font-weight: bold; "
            f"color: {Theme.color('primary')}; background: transparent;"
        )
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        actions = QHBoxLayout()
        actions.setSpacing(8)

        if self.can_edit:
            new_btn = QPushButton("➕  حجز جديد")
            new_btn.setFixedHeight(44)
            new_btn.setCursor(Qt.PointingHandCursor)
            new_btn.setStyleSheet(
                f"QPushButton {{ background-color: {Theme.color('danger')}; "
                f"color: white; border: none; border-radius: 6px; "
                f"padding: 10px 20px; font-weight: bold; font-size: 11pt; }}"
                f"QPushButton:hover {{ background-color: {Theme.color('danger_hover')}; }}"
            )
            new_btn.clicked.connect(self._open_new_dialog)
            actions.addWidget(new_btn)

            edit_btn = QPushButton("✏️  تعديل المختار")
            edit_btn.setFixedHeight(44)
            edit_btn.setCursor(Qt.PointingHandCursor)
            edit_btn.setStyleSheet(
                f"QPushButton {{ background-color: {Theme.color('primary')}; "
                f"color: white; border: none; border-radius: 6px; "
                f"padding: 10px 20px; font-weight: bold; font-size: 11pt; }}"
                f"QPushButton:hover {{ background-color: {Theme.color('primary_hover')}; }}"
            )
            edit_btn.clicked.connect(self._open_edit_dialog)
            actions.addWidget(edit_btn)

            delete_btn = QPushButton("🗑️  حذف المختار")
            delete_btn.setFixedHeight(44)
            delete_btn.setCursor(Qt.PointingHandCursor)
            delete_btn.setStyleSheet(
                f"QPushButton {{ background-color: {Theme.color('danger')}; "
                f"color: white; border: none; border-radius: 6px; "
                f"padding: 10px 20px; font-weight: bold; font-size: 11pt; }}"
                f"QPushButton:hover {{ background-color: {Theme.color('danger_hover')}; }}"
            )
            delete_btn.clicked.connect(self._delete_booking)
            actions.addWidget(delete_btn)

        receipt_btn = QPushButton("🖨️  طباعة إيصال")
        receipt_btn.setFixedHeight(44)
        receipt_btn.setCursor(Qt.PointingHandCursor)
        receipt_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('text_dim')}; "
            f"color: white; border: none; border-radius: 6px; "
            f"padding: 10px 20px; font-weight: bold; font-size: 11pt; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('border_strong')}; }}"
        )
        receipt_btn.clicked.connect(self._show_receipt)
        actions.addWidget(receipt_btn)

        actions.addStretch()
        layout.addLayout(actions)

        table_card = QFrame()
        table_card.setStyleSheet(
            f"QFrame {{ background-color: {Theme.color('surface')}; "
            f"border: 1px solid {Theme.color('border')}; border-radius: 10px; }}"
        )
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(14, 14, 14, 14)
        table_layout.setSpacing(8)

        tbl_title = QLabel("📋  قائمة الحجوزات")
        tbl_title.setStyleSheet(
            f"font-size: 12pt; font-weight: bold; "
            f"color: {Theme.color('primary')}; background: transparent;"
        )
        tbl_title.setAlignment(Qt.AlignRight)
        table_layout.addWidget(tbl_title)

        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(
            ["#", "العميل", "الخدمة", "إضافية", "الإجمالي", "الدفع", "الحلاق", "التاريخ", "الوقت"]
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
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        h.setSectionResizeMode(3, QHeaderView.Stretch)
        h.setSectionResizeMode(4, QHeaderView.Fixed)
        h.setSectionResizeMode(5, QHeaderView.Fixed)
        h.setSectionResizeMode(6, QHeaderView.Fixed)
        h.setSectionResizeMode(7, QHeaderView.Fixed)
        h.setSectionResizeMode(8, QHeaderView.Fixed)

        for i, w in [(0, 50), (4, 110), (5, 100), (6, 100), (7, 110), (8, 90)]:
            self.table.setColumnWidth(i, w)

        if self.can_edit:
            self.table.doubleClicked.connect(self._open_edit_dialog)

        table_layout.addWidget(self.table)
        layout.addWidget(table_card)

    def refresh(self):
        try:
            bookings = self.db.list_bookings()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل الحجوزات:\n{e}")
            return

        services = {s[0]: s[1] for s in self.db.list_services()}
        pm_labels = {"cash": "كاش", "card": "فيزا", "wallet": "محفظة"}

        self.table.blockSignals(True)
        self.table.setRowCount(len(bookings))

        green = QColor(Theme.color("success"))
        text_color = QColor(Theme.color("text"))

        for row, b in enumerate(bookings):
            try:
                bid, cname, sname, price, barber, date, time_, extra_json, extra_total, pm = b
            except Exception:
                continue

            item_id = QTableWidgetItem(str(bid))
            item_id.setTextAlignment(Qt.AlignCenter)
            item_id.setData(Qt.UserRole, bid)
            item_id.setForeground(text_color)
            self.table.setItem(row, 0, item_id)

            self.table.setItem(row, 1, self._item(cname))
            self.table.setItem(row, 2, self._item(sname))

            try:
                extra_ids = _json.loads(extra_json) if extra_json else []
            except Exception:
                extra_ids = []
            extra_names = ", ".join(services.get(i, "") for i in extra_ids) or "—"
            self.table.setItem(row, 3, self._item(extra_names))

            total = price + (extra_total or 0)
            item_total = QTableWidgetItem(f"{total:.2f} ج")
            item_total.setTextAlignment(Qt.AlignCenter)
            item_total.setForeground(green)
            self.table.setItem(row, 4, item_total)

            self.table.setItem(row, 5, self._item(pm_labels.get(pm or "cash", pm or "cash")))
            self.table.setItem(row, 6, self._item(barber))
            self.table.setItem(row, 7, self._item(date))
            self.table.setItem(row, 8, self._item(time_))

        self.table.blockSignals(False)

    def _item(self, text):
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(Qt.AlignCenter)
        item.setForeground(QColor(Theme.color("text")))
        return item

    def _get_selected_booking_id(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        row_idx = rows[0].row()
        item = self.table.item(row_idx, 0)
        return item.data(Qt.UserRole) if item else None

    def _open_new_dialog(self):
        if not self.db.get_open_shift():
            QMessageBox.warning(self, "مفيش وردية مفتوحة", "لازم تبدأ وردية الأول من تاب الورديات.")
            return

        current = {
            "customer": "",
            "service_id": None,
            "extra_ids": [],
            "barber": "",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": "10:00",
            "payment_method": "cash",
        }

        dlg = BookingDialog(self, db=self.db, booking_id=None, current=current)
        if dlg.exec() == QDialog.Accepted and dlg.result_data:
            data = dlg.result_data
            try:
                self.db.add_booking(
                    data["customer_id"], data["service_id"],
                    data["barber"], data["date"], data["time"],
                    extra_service_ids=data["extra_ids"],
                    payment_method=data["payment_method"],
                )
                QMessageBox.information(self, "تم", "تم إضافة الحجز.")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل الإضافة:\n{e}")
                return
            self.refresh()

    def _open_edit_dialog(self):
        if not self.can_edit:
            return
        bid = self._get_selected_booking_id()
        if bid is None:
            QMessageBox.warning(self, "خطأ", "اختار حجز من القائمة الأول")
            return

        row = self.db.get_booking(bid)
        if not row:
            return

        try:
            extra_ids = _json.loads(row[9]) if row[9] else []
        except Exception:
            extra_ids = []

        current = {
            "customer": row[3],
            "service_id": row[2],
            "extra_ids": extra_ids,
            "barber": row[6],
            "date": row[7],
            "time": row[8],
            "payment_method": row[11] or "cash",
        }

        dlg = BookingDialog(self, db=self.db, booking_id=bid, current=current)
        if dlg.exec() == QDialog.Accepted and dlg.result_data:
            data = dlg.result_data
            try:
                self.db.update_booking(
                    bid, data["customer_id"], data["service_id"],
                    data["barber"], data["date"], data["time"],
                    extra_service_ids=data["extra_ids"],
                    payment_method=data["payment_method"],
                )
                QMessageBox.information(self, "تم", "تم تعديل الحجز.")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل التعديل:\n{e}")
                return
            self.refresh()

    def _delete_booking(self):
        if not self.can_edit:
            return
        bid = self._get_selected_booking_id()
        if bid is None:
            QMessageBox.warning(self, "خطأ", "اختار حجز من القائمة الأول")
            return

        if QMessageBox.question(
            self, "تأكيد", f"متأكد إنك عايز تحذف الحجز #{bid}؟"
        ) != QMessageBox.Yes:
            return

        try:
            self.db.delete_booking(bid)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل الحذف:\n{e}")
            return
        self.refresh()

    # ============================================
    # Receipt
    # ============================================
    def _show_receipt(self):
        bid = self._get_selected_booking_id()
        if bid is None:
            QMessageBox.warning(self, "خطأ", "اختار حجز من القائمة الأول")
            return

        row = self.db.get_booking(bid)
        if not row:
            return

        try:
            extra_ids = _json.loads(row[9]) if row[9] else []
        except Exception:
            extra_ids = []

        services = {s[0]: s[1] for s in self.db.list_services()}
        extra_names = [services.get(i, "") for i in extra_ids]
        extra_names = [n for n in extra_names if n]

        service_display = row[4]
        if extra_names:
            service_display += " + " + " + ".join(extra_names)

        total_price = row[5] + (row[10] or 0)
        pm = row[11] or "cash"
        pm_labels = {"cash": "كاش", "card": "فيزا / كارت", "wallet": "محفظة إلكترونية"}
        payment_label = pm_labels.get(pm, pm)

        self._show_receipt_dialog(bid, row[3], service_display, total_price,
                                   row[6], row[7], row[8], payment_label)

    def _show_receipt_dialog(self, bid, customer, service, price,
                              barber, date, time_, payment_label):
        dlg = QDialog(self)
        dlg.setWindowTitle(f"إيصال #{bid}")
        dlg.setMinimumSize(600, 800)
        dlg.setLayoutDirection(Qt.RightToLeft)
        dlg.setStyleSheet(_dialog_qss())

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        now = datetime.now()
        print_time = now.strftime("%Y-%m-%d  |  %I:%M:%S %p")

        try:
            shop_name = self.db.get_setting("shop_name", "صالون الحلاقة") or "صالون الحلاقة"
            shop_phone = self.db.get_setting("shop_phone", "") or ""
            shop_address = self.db.get_setting("shop_address", "") or ""
            shop_logo = self.db.get_setting("shop_logo", "") or ""
            receipt_color = self.db.get_setting("receipt_color", "#3b82f6") or "#3b82f6"
        except Exception:
            shop_name = "صالون الحلاقة"
            shop_phone = ""
            shop_address = ""
            shop_logo = ""
            receipt_color = "#3b82f6"

        receipt_data = {
            "bid": bid,
            "customer": customer,
            "service": service,
            "price": price,
            "barber": barber,
            "date": date,
            "time": time_,
            "payment_label": payment_label,
            "print_time": print_time,
            "shop_name": shop_name,
            "shop_phone": shop_phone,
            "shop_address": shop_address,
            "shop_logo": shop_logo,
            "receipt_color": receipt_color,
        }

        # ✅ المعاينة — WebEngine (شكل احترافي) أو QTextEdit (شكل بسيط)
        if HAS_WEBENGINE:
            preview = QWebEngineView()
            preview.setStyleSheet(
                "QWebEngineView { background-color: #ffffff; "
                "border: 1px solid #cbd5e1; border-radius: 8px; }"
            )
            preview.setHtml(self._build_receipt_html(receipt_data))
            preview.setMinimumHeight(450)
        else:
            preview = QTextEdit()
            preview.setReadOnly(True)
            preview.setStyleSheet(
                "QTextEdit { background-color: #ffffff; "
                "border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px; }"
            )
            preview.setHtml(self._build_simple_receipt_html(receipt_data))

        layout.addWidget(preview, stretch=1)

        print_title = QLabel("🖨  اختر طريقة الطباعة:")
        print_title.setStyleSheet(
            f"color: {Theme.color('text')}; font-size: 11pt; "
            f"font-weight: bold; padding: 4px; background: transparent;"
        )
        layout.addWidget(print_title)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        quick_print_btn = QPushButton("⚡  طباعة سريعة")
        quick_print_btn.setMinimumHeight(46)
        quick_print_btn.setCursor(Qt.PointingHandCursor)
        quick_print_btn.setToolTip("طباعة مباشرة على الطابعة الافتراضية")
        quick_print_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('success')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"font-weight: bold; font-size: 11pt; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('success_hover')}; }}"
        )
        quick_print_btn.clicked.connect(
            lambda: self._quick_print(receipt_data, dlg)
        )
        btn_row.addWidget(quick_print_btn, 1)

        choose_printer_btn = QPushButton("🖨  اختر طابعة")
        choose_printer_btn.setMinimumHeight(46)
        choose_printer_btn.setCursor(Qt.PointingHandCursor)
        choose_printer_btn.setToolTip("اختيار الطابعة وضبط الإعدادات")
        choose_printer_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('primary')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"font-weight: bold; font-size: 11pt; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('primary_hover')}; }}"
        )
        choose_printer_btn.clicked.connect(
            lambda: self._print_with_dialog(receipt_data, dlg)
        )
        btn_row.addWidget(choose_printer_btn, 1)

        browser_print_btn = QPushButton("🌐  عبر المتصفح")
        browser_print_btn.setMinimumHeight(46)
        browser_print_btn.setCursor(Qt.PointingHandCursor)
        browser_print_btn.setToolTip("فتح الإيصال في المتصفح للطباعة")
        browser_print_btn.setStyleSheet(
            f"QPushButton {{ background-color: #8b5cf6; color: white; "
            f"border: none; border-radius: 8px; font-weight: bold; "
            f"font-size: 11pt; }}"
            f"QPushButton:hover {{ background-color: #7c3aed; }}"
        )
        browser_print_btn.clicked.connect(
            lambda: self._browser_print(receipt_data, dlg)
        )
        btn_row.addWidget(browser_print_btn, 1)

        layout.addLayout(btn_row)

        btn_row2 = QHBoxLayout()
        btn_row2.setSpacing(8)

        save_pdf_btn = QPushButton("💾  حفظ PDF")
        save_pdf_btn.setMinimumHeight(42)
        save_pdf_btn.setCursor(Qt.PointingHandCursor)
        save_pdf_btn.setStyleSheet(
            f"QPushButton {{ background-color: #f59e0b; color: white; "
            f"border: none; border-radius: 8px; font-weight: bold; "
            f"font-size: 11pt; }}"
            f"QPushButton:hover {{ background-color: #d97706; }}"
        )
        save_pdf_btn.clicked.connect(
            lambda: self._save_receipt_pdf(receipt_data, dlg)
        )
        btn_row2.addWidget(save_pdf_btn, 1)

        save_png_btn = QPushButton("🖼  حفظ صورة")
        save_png_btn.setMinimumHeight(42)
        save_png_btn.setCursor(Qt.PointingHandCursor)
        save_png_btn.setStyleSheet(
            f"QPushButton {{ background-color: #06b6d4; color: white; "
            f"border: none; border-radius: 8px; font-weight: bold; "
            f"font-size: 11pt; }}"
            f"QPushButton:hover {{ background-color: #0891b2; }}"
        )
        save_png_btn.clicked.connect(
            lambda: self._save_receipt_png(receipt_data, dlg)
        )
        btn_row2.addWidget(save_png_btn, 1)

        close_btn = QPushButton("إغلاق")
        close_btn.setMinimumHeight(42)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('surface_alt')}; "
            f"color: {Theme.color('text')}; border: none; border-radius: 8px; "
            f"font-weight: bold; font-size: 11pt; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('border_strong')}; }}"
        )
        close_btn.clicked.connect(dlg.reject)
        btn_row2.addWidget(close_btn, 1)

        layout.addLayout(btn_row2)

        QTimer.singleShot(30, lambda: self._center_dialog(dlg))
        dlg.exec()

    # ============================================
    # Helper: تحويل أي صورة لـ data URI (يدعم ico)
    # ============================================
    def _image_to_data_uri(self, image_path, size_px=90):
        """يحول أي صورة (ico/png/jpg) لـ data URI جاهز للاستخدام في HTML."""
        if not image_path or not os.path.exists(image_path):
            return None

        # 1) نحاول بـ PIL (يدعم .ico)
        try:
            from PIL import Image
            from io import BytesIO
            import base64

            img = Image.open(image_path)
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            buf = BytesIO()
            img.save(buf, format="PNG")
            logo_b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            return f"data:image/png;base64,{logo_b64}"
        except Exception:
            pass

        # 2) fallback: نقرأ الملف مباشرة لو png/jpg
        try:
            import base64
            ext = os.path.splitext(image_path)[1].lower().replace(".", "")
            if ext in ("png", "jpg", "jpeg", "gif", "bmp", "webp"):
                if ext == "jpg":
                    ext = "jpeg"
                with open(image_path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("ascii")
                return f"data:image/{ext};base64,{b64}"
        except Exception:
            pass

        return None

    def _get_logo_html(self, shop_logo, color="#3b82f6",
                       size_px=90, border_color="#ffffff"):
        """يرجع HTML للوجو — يدعم ico + png + إيموجي fallback."""
        # 1) نحاول من الإعدادات
        uri = self._image_to_data_uri(shop_logo)
        if uri:
            return (
                f'<img src="{uri}" '
                f'style="width: {size_px}px; height: {size_px}px; '
                f'border-radius: 50%; object-fit: cover; '
                f'border: 3px solid {border_color}; padding: 3px; '
                f'background: #ffffff;" />'
            )

        # 2) نحاول من haircut.ico الافتراضي
        if os.path.exists(DEFAULT_LOGO_PATH):
            uri = self._image_to_data_uri(DEFAULT_LOGO_PATH)
            if uri:
                return (
                    f'<img src="{uri}" '
                    f'style="width: {size_px}px; height: {size_px}px; '
                    f'border-radius: 50%; object-fit: cover; '
                    f'border: 3px solid {border_color}; padding: 3px; '
                    f'background: #ffffff;" />'
                )

        # 3) fallback: إيموجي
        return (
            f'<div style="width: {size_px}px; height: {size_px}px; '
            f'margin: 0 auto; background: #ffffff; border-radius: 50%; '
            f'display: flex; align-items: center; justify-content: center; '
            f'font-size: {int(size_px * 0.55)}px; '
            f'box-shadow: 0 4px 12px rgba(0,0,0,0.15);">💈</div>'
        )

    # ============================================
    # بناء HTML الإيصال
    # ============================================
    def _build_receipt_html(self, data):
        bid = data["bid"]
        customer = data["customer"]
        service = data["service"]
        price = data["price"]
        barber = data["barber"]
        date = data["date"]
        time_ = data["time"]
        payment_label = data["payment_label"]
        print_time = data["print_time"]
        shop_name = data["shop_name"]
        shop_phone = data["shop_phone"]
        shop_address = data["shop_address"]
        shop_logo = data["shop_logo"]
        color = data["receipt_color"]

        # ============================================
        # QR Code
        # ============================================
        qr_data_uri = ""
        try:
            import importlib
            from io import BytesIO
            import base64

            qrcode = importlib.import_module("qrcode")
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=4,
                border=1,
            )
            qr.add_data(
                f"رقم الإيصال: {bid}\n"
                f"العميل: {customer}\n"
                f"الخدمة: {service}\n"
                f"المبلغ: {price} ج\n"
                f"التاريخ: {date} {time_}"
            )
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            img_b64 = base64.b64encode(buffer.getvalue()).decode("ascii")
            qr_data_uri = f"data:image/png;base64,{img_b64}"
        except Exception:
            pass

        qr_html = ""
        if qr_data_uri:
            qr_html = (
                '<div class="qr-wrap">'
                f'<img src="{qr_data_uri}" style="width: 100px; height: 100px;" />'
                '<p class="qr-hint">امسح الكود للتحقق</p>'
                '</div>'
            )

        # ============================================
        # الشعار (Logo) — haircut.ico أو من الإعدادات
        # ============================================
        logo_html = self._get_logo_html(shop_logo, color=color, size_px=90)

        # ============================================
        # بيانات إضافية للصالون
        # ============================================
        shop_extra = ""
        if shop_phone:
            shop_extra += (
                f'<div style="font-size: 12px; '
                f'color: rgba(255,255,255,0.95); margin-top: 4px;">'
                f'📞 {shop_phone}</div>'
            )
        if shop_address:
            shop_extra += (
                f'<div style="font-size: 12px; '
                f'color: rgba(255,255,255,0.95); margin-top: 2px;">'
                f'📍 {shop_address}</div>'
            )

        html = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
        font-family: 'Segoe UI', 'Tahoma', sans-serif;
        background: #f8fafc;
        color: #0f172a;
        padding: 20px;
        direction: rtl;
    }}
    .receipt {{
        max-width: 420px;
        margin: 0 auto;
        background: #ffffff;
        border-radius: 20px;
        overflow: hidden;
        box-shadow: 0 8px 32px rgba(0,0,0,0.12);
        border: 1px solid #e2e8f0;
    }}
    .header {{
        background: linear-gradient(135deg, {color} 0%, {color}dd 100%);
        padding: 28px 24px;
        text-align: center;
        color: white;
        position: relative;
        overflow: hidden;
    }}
    .header::before {{
        content: '';
        position: absolute;
        top: -50%; right: -50%;
        width: 200%; height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.15) 0%, transparent 70%);
        pointer-events: none;
    }}
    .logo-wrap {{
        position: relative;
        z-index: 2;
        display: inline-block;
    }}
    .shop-name {{
        font-size: 24px;
        font-weight: bold;
        margin-top: 12px;
        letter-spacing: 0.5px;
        position: relative;
        z-index: 2;
    }}
    .shop-extra {{
        position: relative;
        z-index: 2;
        margin-top: 8px;
    }}
    .receipt-number {{
        background: #f1f5f9;
        padding: 12px 24px;
        text-align: center;
        border-bottom: 1px solid #e2e8f0;
    }}
    .receipt-number span {{
        display: inline-block;
        background: white;
        color: {color};
        padding: 6px 20px;
        border-radius: 20px;
        font-size: 14px;
        font-weight: bold;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06);
    }}
    .content {{ padding: 24px; }}
    .info-card {{
        background: #f8fafc;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
        border: 1px solid #e2e8f0;
    }}
    .info-row {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0;
        border-bottom: 1px solid #e2e8f0;
    }}
    .info-row:last-child {{ border-bottom: none; }}
    .info-label {{
        color: #64748b;
        font-size: 13px;
        font-weight: 600;
    }}
    .info-value {{
        color: #0f172a;
        font-size: 14px;
        font-weight: bold;
        text-align: left;
    }}
    .section-title {{
        font-size: 14px;
        font-weight: bold;
        color: {color};
        padding: 8px 0;
        margin-top: 8px;
        border-bottom: 2px dashed #e2e8f0;
    }}
    .total-box {{
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 22px;
        border-radius: 16px;
        text-align: center;
        margin: 20px 0;
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.3);
    }}
    .total-label {{
        font-size: 13px;
        opacity: 0.95;
        margin-bottom: 6px;
    }}
    .total-value {{
        font-size: 32px;
        font-weight: bold;
        letter-spacing: 1px;
    }}
    .total-currency {{
        font-size: 18px;
        opacity: 0.95;
        margin-right: 4px;
    }}
    .payment-wrap {{
        text-align: center;
        margin: 16px 0;
    }}
    .payment-badge {{
        display: inline-block;
        background: #eff6ff;
        color: {color};
        padding: 8px 18px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: bold;
        border: 1px solid #dbeafe;
    }}
    .qr-wrap {{
        text-align: center;
        margin-top: 20px;
        padding-top: 20px;
        border-top: 2px dashed #e2e8f0;
    }}
    .qr-wrap img {{
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        padding: 6px;
        background: white;
    }}
    .qr-hint {{
        font-size: 10px;
        color: #94a3b8;
        margin-top: 6px;
    }}
    .footer {{
        background: #f8fafc;
        text-align: center;
        padding: 20px 24px;
        border-top: 1px solid #e2e8f0;
    }}
    .thanks {{
        font-size: 16px;
        font-weight: bold;
        color: {color};
        margin-bottom: 4px;
    }}
    .thanks-sub {{
        font-size: 12px;
        color: #64748b;
        margin-bottom: 12px;
    }}
    .print-time {{
        font-size: 10px;
        color: #94a3b8;
        font-family: 'Consolas', monospace;
        padding-top: 10px;
        border-top: 1px solid #e2e8f0;
    }}
</style>
</head>
<body>
    <div class="receipt">

        <div class="header">
            <div class="logo-wrap">
                {logo_html}
            </div>
            <div class="shop-name">{shop_name}</div>
            <div class="shop-extra">{shop_extra}</div>
        </div>

        <div class="receipt-number">
            <span>🧾 إيصال #{bid}</span>
        </div>

        <div class="content">

            <div class="info-card">
                <div class="info-row">
                    <span class="info-label">👤 العميل</span>
                    <span class="info-value">{customer}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">✂️ الحلاق</span>
                    <span class="info-value">{barber}</span>
                </div>
            </div>

            <div class="section-title">📋 تفاصيل الخدمة</div>
            <div class="info-card">
                <div class="info-row">
                    <span class="info-label">الخدمة</span>
                    <span class="info-value">{service}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">📅 التاريخ</span>
                    <span class="info-value">{date}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">🕐 الوقت</span>
                    <span class="info-value">{time_}</span>
                </div>
            </div>

            <div class="section-title">💰 المبلغ</div>
            <div class="total-box">
                <div class="total-label">الإجمالي المدفوع</div>
                <div class="total-value">
                    {float(price):.2f}
                    <span class="total-currency">ج.م</span>
                </div>
            </div>

            <div class="payment-wrap">
                <span class="payment-badge">💳 {payment_label}</span>
            </div>

            {qr_html}

        </div>

        <div class="footer">
            <div class="thanks">شكراً لزيارتكم 🌟</div>
            <div class="thanks-sub">نتشرف بخدمتكم مرة أخرى</div>
            <div class="print-time">🕐 وقت الطباعة: {print_time}</div>
        </div>

    </div>
</body>
</html>"""
        return html

    # ============================================
    # HTML بسيط للطباعة المباشرة (Qt compatible)
    # ============================================
    def _build_simple_receipt_html(self, data):
        """يبني HTML بسيط للإيصال — للطباعة المباشرة (Qt compatible)."""
        bid = data["bid"]
        customer = data["customer"]
        service = data["service"]
        price = data["price"]
        barber = data["barber"]
        date = data["date"]
        time_ = data["time"]
        payment_label = data["payment_label"]
        print_time = data["print_time"]
        shop_name = data["shop_name"]
        shop_phone = data["shop_phone"]
        shop_address = data["shop_address"]
        shop_logo = data["shop_logo"]

        # ✅ الشعار — haircut.ico أو من الإعدادات
        logo_uri = None
        if shop_logo and os.path.exists(shop_logo):
            logo_uri = self._image_to_data_uri(shop_logo)
        if not logo_uri and os.path.exists(DEFAULT_LOGO_PATH):
            logo_uri = self._image_to_data_uri(DEFAULT_LOGO_PATH)

        if logo_uri:
            logo_html = (
                f'<img src="{logo_uri}" width="70" height="70" '
                f'style="display: block; margin: 0 auto 8px auto;" />'
            )
        else:
            logo_html = '<div style="font-size: 40pt;">💈</div>'

        # بيانات الصالون
        shop_lines = []
        if shop_phone:
            shop_lines.append(f"📞 {shop_phone}")
        if shop_address:
            shop_lines.append(f"📍 {shop_address}")
        shop_info = "<br/>".join(shop_lines)

        html = f"""
        <!DOCTYPE html>
        <html dir="rtl" lang="ar">
        <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Segoe UI', 'Tahoma', sans-serif;
                color: #0f172a;
                padding: 10px;
            }}
            .container {{ max-width: 500px; margin: 0 auto; }}
            .header {{
                text-align: center;
                border-bottom: 2px solid #0f172a;
                padding-bottom: 10px;
                margin-bottom: 12px;
            }}
            .shop-name {{
                font-size: 20pt;
                font-weight: bold;
                color: #1e40af;
                margin-bottom: 4px;
            }}
            .shop-info {{
                font-size: 10pt;
                color: #64748b;
                line-height: 1.5;
            }}
            .receipt-num {{
                text-align: center;
                font-size: 13pt;
                font-weight: bold;
                color: #1e40af;
                background: #eff6ff;
                padding: 6px;
                margin: 10px 0;
                border-radius: 4px;
            }}
            .info-table {{
                width: 100%;
                margin: 10px 0;
                border-collapse: collapse;
            }}
            .info-table td {{
                padding: 6px 8px;
                border-bottom: 1px solid #e2e8f0;
                font-size: 11pt;
            }}
            .info-table td:first-child {{
                color: #64748b;
                font-weight: bold;
                width: 40%;
            }}
            .info-table td:last-child {{
                color: #0f172a;
                font-weight: bold;
            }}
            .section-title {{
                font-size: 12pt;
                font-weight: bold;
                color: #1e40af;
                padding: 8px 0 4px 0;
                margin-top: 10px;
                border-bottom: 2px solid #1e40af;
            }}
            .total-box {{
                background: #10b981;
                color: white;
                padding: 12px;
                text-align: center;
                margin: 12px 0;
                border-radius: 6px;
            }}
            .total-label {{
                font-size: 10pt;
                margin-bottom: 4px;
            }}
            .total-value {{
                font-size: 18pt;
                font-weight: bold;
            }}
            .payment {{
                text-align: center;
                font-size: 11pt;
                color: #1e40af;
                font-weight: bold;
                margin: 10px 0;
            }}
            .footer {{
                text-align: center;
                border-top: 2px solid #0f172a;
                padding-top: 10px;
                margin-top: 15px;
                font-size: 11pt;
            }}
            .thanks {{
                font-size: 13pt;
                font-weight: bold;
                color: #1e40af;
                margin: 6px 0;
            }}
            .print-time {{
                font-size: 9pt;
                color: #94a3b8;
                margin-top: 8px;
            }}
        </style>
        </head>
        <body>
            <div class="container">

                <div class="header">
                    <div>{logo_html}</div>
                    <div class="shop-name">{shop_name}</div>
                    <div class="shop-info">{shop_info}</div>
                </div>

                <div class="receipt-num">🧾 إيصال #{bid}</div>

                <table class="info-table">
                    <tr><td>👤 العميل</td><td>{customer}</td></tr>
                    <tr><td>✂️ الحلاق</td><td>{barber}</td></tr>
                </table>

                <div class="section-title">📋 تفاصيل الخدمة</div>

                <table class="info-table">
                    <tr><td>الخدمة</td><td>{service}</td></tr>
                    <tr><td>📅 التاريخ</td><td>{date}</td></tr>
                    <tr><td>🕐 الوقت</td><td>{time_}</td></tr>
                </table>

                <div class="section-title">💰 المبلغ</div>

                <div class="total-box">
                    <div class="total-label">الإجمالي المدفوع</div>
                    <div class="total-value">{float(price):.2f} ج.م</div>
                </div>

                <div class="payment">💳 طريقة الدفع: {payment_label}</div>

                <div class="footer">
                    <div class="thanks">شكراً لزيارتكم 🌟</div>
                    <div>نتشرف بخدمتكم مرة أخرى</div>
                    <div class="print-time">🕐 وقت الطباعة: {print_time}</div>
                </div>

            </div>
        </body>
        </html>
        """
        return html

    # ============================================
    # 1) طباعة سريعة
    # ============================================
    def _quick_print(self, data, parent=None):
        """طباعة سريعة — تنسيق نصي مرتب (بدون متصفح)."""
        try:
            from PySide6.QtPrintSupport import QPrinter
            from PySide6.QtGui import QTextDocument, QPageSize

            text_html = self._build_simple_receipt_html(data)

            printer = QPrinter(QPrinter.HighResolution)
            try:
                printer.setPageSize(QPageSize(QPageSize.A5))
            except Exception:
                pass

            doc = QTextDocument()
            doc.setHtml(text_html)
            doc.print_(printer)

            QMessageBox.information(
                parent, "تم",
                f"✅ تم إرسال الإيصال للطابعة.\n\n"
                f"🕐 وقت الطباعة: {data['print_time']}"
            )
        except Exception as e:
            QMessageBox.critical(parent, "خطأ", f"فشل الطباعة:\n{e}")

    # ============================================
    # 2) طباعة مع اختيار طابعة
    # ============================================
    def _print_with_dialog(self, data, parent=None):
        """طباعة مع اختيار الطابعة — تنسيق نصي مرتب."""
        try:
            from PySide6.QtPrintSupport import QPrinter, QPrintDialog
            from PySide6.QtGui import QTextDocument, QPageSize

            printer = QPrinter(QPrinter.HighResolution)
            try:
                printer.setPageSize(QPageSize(QPageSize.A5))
            except Exception:
                pass

            print_dlg = QPrintDialog(printer, parent)
            print_dlg.setWindowTitle("اختر الطابعة والإعدادات")
            print_dlg.setLayoutDirection(Qt.RightToLeft)

            if print_dlg.exec() != QDialog.Accepted:
                return

            text_html = self._build_simple_receipt_html(data)

            doc = QTextDocument()
            doc.setHtml(text_html)
            doc.print_(printer)

            QMessageBox.information(
                parent, "تم",
                f"✅ تم إرسال الإيصال للطابعة.\n\n"
                f"🕐 وقت الطباعة: {data['print_time']}"
            )
        except Exception as e:
            QMessageBox.critical(parent, "خطأ", f"فشل الطباعة:\n{e}")

    # ============================================
    # 3) طباعة عبر المتصفح
    # ============================================
    def _browser_print(self, data, parent=None):
        try:
            receipts_dir = os.path.join(self.db.base_dir, "receipts")
            os.makedirs(receipts_dir, exist_ok=True)

            stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            html_path = os.path.join(
                receipts_dir, f"receipt_{data['bid']}_{stamp}.html"
            )

            with open(html_path, "w", encoding="utf-8") as f:
                f.write(self._build_receipt_html(data))

            if os.name == "nt":
                os.startfile(html_path)

            QMessageBox.information(
                parent, "تم",
                f"تم فتح الإيصال في المتصفح.\n\n"
                f"وقت الطباعة: {data['print_time']}\n\n"
                f"من المتصفح:\n"
                f"- اضغط Ctrl+P للطباعة\n"
                f"- أو اختار طباعة من قائمة الملف"
            )
        except Exception as e:
            QMessageBox.critical(parent, "خطأ", f"فشل الفتح:\n{e}")

    # ============================================
    # حفظ PDF
    # ============================================
    def _save_receipt_pdf(self, data, parent=None):
        """يحفظ الإيصال كـ HTML جاهز للطباعة PDF من المتصفح (صفحة واحدة)."""
        try:
            receipts_dir = os.path.join(self.db.base_dir, "receipts")
            os.makedirs(receipts_dir, exist_ok=True)

            stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            html_path = os.path.join(
                receipts_dir, f"receipt_{data['bid']}_{stamp}.html"
            )

            html_content = self._build_receipt_html(data)

            print_css = """
            <style>
                @media print {
                    @page {
                        size: A4;
                        margin: 8mm;
                    }
                    html, body {
                        width: 100%;
                        height: auto;
                        margin: 0 !important;
                        padding: 0 !important;
                        background: #ffffff !important;
                    }
                    body {
                        zoom: 0.75;
                    }
                    .receipt {
                        box-shadow: none !important;
                        border: 1px solid #cbd5e1 !important;
                        max-width: 100% !important;
                        page-break-inside: avoid !important;
                        page-break-after: avoid !important;
                        margin: 0 auto !important;
                    }
                    .header { padding: 16px 20px !important; }
                    .shop-name { font-size: 20px !important; margin-top: 8px !important; }
                    .content { padding: 16px !important; }
                    .receipt-number { padding: 8px 16px !important; }
                    .info-card { padding: 10px !important; margin-bottom: 10px !important; }
                    .info-row { padding: 6px 0 !important; }
                    .total-box { padding: 14px !important; margin: 12px 0 !important; }
                    .total-value { font-size: 24px !important; }
                    .qr-wrap { margin-top: 10px !important; padding-top: 10px !important; }
                    .qr-wrap img { width: 80px !important; height: 80px !important; }
                    .footer { padding: 12px 16px !important; }
                    .thanks { font-size: 14px !important; }
                }
            </style>
            """
            html_content = html_content.replace("</head>", print_css + "</head>")

            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            if os.name == "nt":
                os.startfile(html_path)

            QMessageBox.information(
                parent, "تم",
                f"✅ تم فتح الإيصال في المتصفح.\n\n"
                f"📁 الملف: {os.path.basename(html_path)}\n\n"
                f"لحفظه كـ PDF:\n"
                f"1. اضغط Ctrl+P\n"
                f"2. اختار \"Save as PDF\"\n"
                f"3. تأكد من:\n"
                f"   • Paper size: A4\n"
                f"   • Margins: Default\n"
                f"   • Scale: Default\n"
                f"4. اضغط Save\n\n"
                f"✅ الإيصال هيطلع على صفحة واحدة"
            )
        except Exception as e:
            QMessageBox.critical(parent, "خطأ", f"فشل الحفظ:\n{e}")

    # ============================================
    # حفظ صورة PNG (عبر المتصفح)
    # ============================================
    def _save_receipt_png(self, data, parent=None):
        """حفظ الإيصال كصورة عبر HTML (يفتح في المتصفح)."""
        QMessageBox.information(
            parent, "ملاحظة",
            "حفظ الإيصال كصورة:\n\n"
            "1. هيتم فتح الإيصال في المتصفح\n"
            "2. اعمل Right Click على الإيصال\n"
            "3. اختار \"Save image as...\"\n"
            "4. أو استخدم أداة Screenshot\n\n"
            "اضغط OK لفتح الإيصال."
        )

        try:
            receipts_dir = os.path.join(self.db.base_dir, "receipts")
            os.makedirs(receipts_dir, exist_ok=True)

            stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            html_path = os.path.join(
                receipts_dir, f"receipt_{data['bid']}_{stamp}.html"
            )

            with open(html_path, "w", encoding="utf-8") as f:
                f.write(self._build_receipt_html(data))

            if os.name == "nt":
                os.startfile(html_path)
        except Exception as e:
            QMessageBox.critical(parent, "خطأ", f"فشل:\n{e}")

    def _center_dialog(self, dlg):
        try:
            screen = QGuiApplication.primaryScreen()
            if screen is None:
                return
            geo = screen.availableGeometry()
            x = geo.x() + (geo.width() - dlg.width()) // 2
            y = geo.y() + (geo.height() - dlg.height()) // 2
            dlg.move(max(x, 0), max(y, 0))
        except Exception:
            pass