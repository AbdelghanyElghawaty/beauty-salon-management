"""
Main Window — PySide6 layout with tabs + header + status bar.
+ Light/Dark theme support (reads from Theme).
+ Custom logo from beauty-salon.png in header
+ Employee / Inventory / Management tabs
"""

import os
from datetime import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QTabWidget, QStatusBar, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor, QIcon, QPixmap

from utils.theme import Theme


class MainWindow(QMainWindow):
    """النافذة الرئيسية — Header + Tabs + Status bar."""

    def __init__(self, db, user, app_ref=None):
        super().__init__()
        self.db = db
        self.user = user
        self.app_ref = app_ref
        self._logging_out = False

        # ✅ اقرأ اسم الصالون من DB
        try:
            self.shop_name = (
                db.get_setting("shop_name", "صالون الحلاقة")
                or "صالون الحلاقة"
            )
        except Exception:
            self.shop_name = "صالون الحلاقة"

        self.setWindowTitle(f"نظام إدارة {self.shop_name}")
        self.resize(1400, 850)
        self.setMinimumSize(1200, 720)

        # ✅ أيقونة النافذة
        self._set_window_icon()

        # العنصر المركزي
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ============================================
        # Header
        # ============================================
        main_layout.addWidget(self._build_header())

        # ============================================
        # Content — Tabs
        # ============================================
        content = QWidget()
        content.setStyleSheet("background-color: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 16, 16, 8)
        content_layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        content_layout.addWidget(self.tabs)

        self._build_tabs()

        main_layout.addWidget(content, stretch=1)

        # ============================================
        # Status bar
        # ============================================
        self._build_statusbar()

        # ============================================
        # Timer for clock
        # ============================================
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._tick_clock)
        self._clock_timer.start(1000)

        self._tick_clock()
        self._update_shift_status()

    # ============================================
    # Window Icon
    # ============================================
    def _set_window_icon(self):
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            for icon_name in ("beauty-salon.png", "beauty-salon.ico",
                              "haircut.png", "haircut.ico"):
                icon_path = os.path.join(base_dir, icon_name)
                if os.path.exists(icon_path):
                    self.setWindowIcon(QIcon(icon_path))
                    return
        except Exception:
            pass

    def _load_logo_pixmap(self, size=44):
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            for logo_name in ("beauty-salon.png", "beauty-salon.ico",
                              "haircut.png", "haircut.ico"):
                logo_path = os.path.join(base_dir, logo_name)
                if os.path.exists(logo_path):
                    pixmap = QPixmap(logo_path)
                    if not pixmap.isNull():
                        # لو الصورة كبيرة، صغّرها بجودة
                        if pixmap.width() >= size and pixmap.height() >= size:
                            return pixmap.scaled(
                                size, size,
                                Qt.KeepAspectRatio,
                                Qt.SmoothTransformation
                            )
                        return pixmap
        except Exception:
            pass
        return None

    # ============================================
    # Header
    # ============================================
    def _build_header(self):
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(76)

        header.setStyleSheet(
            f"QFrame#header {{ "
            f"background-color: {Theme.color('surface')}; "
            f"border-bottom: 2px solid {Theme.color('primary')}; "
            f"}}"
        )

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(16)

        # ---- يمين: الشعار + الاسم ----
        right = QHBoxLayout()
        right.setSpacing(12)

        logo = QLabel()
        logo.setFixedSize(52, 52)
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet("background: transparent;")

        pixmap = self._load_logo_pixmap(48)
        if pixmap is not None:
            logo.setPixmap(pixmap)
        else:
            logo.setText("💈")
            logo.setStyleSheet(
                "font-size: 32px; background: transparent;"
            )

        right.addWidget(logo)

        name_wrap = QVBoxLayout()
        name_wrap.setSpacing(0)

        self.shop_name_label = QLabel(self.shop_name)
        self.shop_name_label.setStyleSheet(
            f"color: {Theme.color('text')}; font-size: 17pt; "
            f"font-weight: bold; padding: 4px; background: transparent;"
        )
        name_wrap.addWidget(self.shop_name_label)

        subtitle = QLabel("Barber Shop · Management")
        subtitle.setStyleSheet(
            f"color: {Theme.color('gold')}; font-size: 8pt; "
            f"background: transparent;"
        )
        name_wrap.addWidget(subtitle)

        right.addLayout(name_wrap)
        right.addStretch()

        layout.addLayout(right, stretch=1)

        # ---- وسط: بيانات المستخدم ----
        role = "سوبر أدمن" if self.user.is_admin else "يوزر عادي"
        self.user_label = QLabel(
            f"مسجل الدخول: {self.user.username} ({role})"
        )
        self.user_label.setStyleSheet(
            f"color: {Theme.color('text_muted')}; font-size: 9pt; "
            f"background: transparent;"
        )
        layout.addWidget(self.user_label)

        # ---- يسار: الحالة + أزرار ----
        self.shift_status_label = QLabel("")
        self.shift_status_label.setStyleSheet(
            f"color: {Theme.color('success')}; font-size: 12px; "
            f"font-weight: bold; padding: 0 12px; background: transparent;"
        )
        layout.addWidget(self.shift_status_label)

        logout_btn = QPushButton("⏻  تسجيل خروج")
        logout_btn.setMinimumHeight(38)
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('danger')}; "
            f"color: white; border: none; border-radius: 6px; "
            f"padding: 8px 16px; font-size: 10pt; font-weight: bold; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('danger_hover')}; }}"
        )
        logout_btn.clicked.connect(self.logout)
        layout.addWidget(logout_btn)

        return header

    def refresh_header(self):
        try:
            new_name = (
                self.db.get_setting("shop_name", "صالون الحلاقة")
                or "صالون الحلاقة"
            )
            self.shop_name = new_name
            self.shop_name_label.setText(new_name)
            self.setWindowTitle(f"نظام إدارة {new_name}")
        except Exception:
            pass

    # ============================================
    # Tabs
    # ============================================
    def _build_tabs(self):
        from ui.tabs.services_tab import ServicesTab
        from ui.tabs.customers_tab import CustomersTab
        from ui.tabs.bookings_tab import BookingsTab
        from ui.tabs.shifts_tab import ShiftsTab
        from ui.tabs.users_tab import UsersTab

        # ✅ التابات الجديدة
        from ui.tabs.employees_tab import EmployeesTab
        from ui.tabs.inventory_tab import InventoryTab
        from ui.tabs.management_tab import ManagementTab

        self.tab_widgets = []

        user = self.user
        db = self.db

        # ============================================
        # التاب الأساسية (زي ما هي)
        # ============================================
        if user.has_permission("view_services"):
            tab = ServicesTab(db, user)
            self.tabs.addTab(tab, "  💈  الأسعار والخدمات  ")
            self.tab_widgets.append(tab)

        if user.has_permission("view_customers"):
            tab = CustomersTab(db, user)
            self.tabs.addTab(tab, "  👥  العملاء  ")
            self.tab_widgets.append(tab)

        if user.has_permission("view_bookings"):
            tab = BookingsTab(db, user)
            self.tabs.addTab(tab, "  📅  الحجوزات  ")
            self.tab_widgets.append(tab)

        if user.has_permission("view_shifts"):
            tab = ShiftsTab(db, user)
            self.tabs.addTab(tab, "  🕐  الورديات  ")
            self.tab_widgets.append(tab)

        # ============================================
        # ✅ تاب الموظفين (جديد)
        # ============================================
        if user.is_admin or user.has_permission("view_employees"):
            try:
                tab = EmployeesTab(db, user)
                self.tabs.addTab(tab, "  👥  الموظفين  ")
                self.tab_widgets.append(tab)
            except Exception as e:
                print(f"⚠️  فشل تحميل تاب الموظفين: {e}")

        # ============================================
        # ✅ تاب المخزون (جديد)
        # ============================================
        if user.is_admin or user.has_permission("view_inventory"):
            try:
                tab = InventoryTab(db, user)
                self.tabs.addTab(tab, "  📦  المخزون  ")
                self.tab_widgets.append(tab)
            except Exception as e:
                print(f"⚠️  فشل تحميل تاب المخزون: {e}")

        # ============================================
        # ✅ تاب الإدارة (جديد)
        # ============================================
        if user.is_admin or user.has_permission("view_management"):
            try:
                tab = ManagementTab(db, user)
                self.tabs.addTab(tab, "  💼  الإدارة  ")
                self.tab_widgets.append(tab)
            except Exception as e:
                print(f"⚠️  فشل تحميل تاب الإدارة: {e}")

        # ============================================
        # تاب التقارير
        # ============================================
        if user.has_permission("view_reports"):
            try:
                from ui.tabs.reports_tab import ReportsTab
                tab = ReportsTab(db, user)
                self.tabs.addTab(tab, "  📊  التقارير  ")
                self.tab_widgets.append(tab)
            except ImportError:
                pass

        # ============================================
        # تاب السجل — للأدمن بس
        # ============================================
        if user.is_admin:
            try:
                from ui.tabs.audit_tab import AuditTab
                tab = AuditTab(db, user)
                self.tabs.addTab(tab, "  📜  سجل العمليات  ")
                self.tab_widgets.append(tab)
            except ImportError:
                pass

        if user.is_admin:
            tab = UsersTab(db, user)
            self.tabs.addTab(tab, "  👤  المستخدمين  ")
            self.tab_widgets.append(tab)

        if user.is_admin:
            try:
                from ui.tabs.settings_tab import SettingsTab
                tab = SettingsTab(db, user)
                self.tabs.addTab(tab, "  ⚙️  الإعدادات  ")
                self.tab_widgets.append(tab)
            except ImportError:
                pass

        # ربط تغيير التاب
        self.tabs.currentChanged.connect(self._on_tab_changed)

    def _on_tab_changed(self, index):
        try:
            tab = self.tabs.widget(index)
            if hasattr(tab, "refresh"):
                tab.refresh()
            self.refresh_header()
        except Exception:
            pass

    # ============================================
    # Status bar
    # ============================================
    def _build_statusbar(self):
        status = QStatusBar()
        self.setStatusBar(status)

        status.setStyleSheet(
            f"QStatusBar {{ background-color: {Theme.color('statusbar')}; "
            f"color: {Theme.color('text_muted')}; "
            f"border-top: 1px solid {Theme.color('border')}; padding: 3px; }}"
        )

        self.status_label = QLabel("● جاهز")
        self.status_label.setStyleSheet(
            f"color: {Theme.color('success')}; font-weight: bold; "
            f"padding: 0 10px; background: transparent;"
        )
        status.addPermanentWidget(self.status_label)

        self.clock_label = QLabel("")
        self.clock_label.setStyleSheet(
            f"color: {Theme.color('text_muted')}; padding: 0 10px; "
            f"background: transparent;"
        )
        status.addWidget(self.clock_label)

    def _tick_clock(self):
        try:
            if not hasattr(self, "clock_label") or self.clock_label is None:
                return
            now = datetime.now()
            text = now.strftime("%Y-%m-%d  |  %I:%M:%S %p")
            self.clock_label.setText("🕐  " + text)
        except (RuntimeError, AttributeError):
            pass
        except Exception:
            pass

    # ============================================
    # Shift status
    # ============================================
    def _update_shift_status(self):
        try:
            open_shift = self.db.get_open_shift()
            if open_shift:
                time_part = (
                    open_shift[1][11:16]
                    if len(open_shift[1]) >= 16
                    else open_shift[1]
                )
                self.shift_status_label.setText(f"🟢 وردية من {time_part}")
                self.shift_status_label.setStyleSheet(
                    f"color: {Theme.color('success')}; font-size: 12px; "
                    f"font-weight: bold; padding: 0 12px; "
                    f"background: transparent;"
                )
            else:
                self.shift_status_label.setText("⚪ مفيش وردية")
                self.shift_status_label.setStyleSheet(
                    f"color: {Theme.color('text_muted')}; font-size: 12px; "
                    f"font-weight: bold; padding: 0 12px; "
                    f"background: transparent;"
                )
        except Exception:
            pass

    # ============================================
    # Logout
    # ============================================
    def logout(self):
        reply = QMessageBox.question(
            self, "تسجيل خروج",
            "متأكد إنك عايز تسجل خروج؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        self._logging_out = True

        try:
            if hasattr(self, "_clock_timer") and self._clock_timer is not None:
                self._clock_timer.stop()
                self._clock_timer = None
        except Exception:
            pass

        try:
            self.db.logout_current_user()
        except Exception:
            pass

        try:
            self.db.backup_now()
        except Exception:
            pass

        self.close()

        if self.app_ref:
            try:
                self.app_ref.relaunch()
            except Exception:
                pass

    # ============================================
    # Close
    # ============================================
    def closeEvent(self, event):
        try:
            if hasattr(self, "_clock_timer") and self._clock_timer is not None:
                self._clock_timer.stop()
                self._clock_timer = None
        except Exception:
            pass

        try:
            self.db.backup_now()
        except Exception:
            pass

        event.accept()

        if not self._logging_out:
            if self.app_ref and hasattr(self.app_ref, "quit_app"):
                try:
                    self.app_ref.quit_app()
                except Exception:
                    pass