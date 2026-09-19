"""
Barber Shop Desktop App — PySide6 entry point with proper DPI handling.
+ نظام حماية بكود تفعيل مرتبط بالجهاز
+ دعم اشتراكات محددة المدة + تحذير قبل الانتهاء
+ أيقونة التطبيق من beauty-salon.png/ico
+ تفعيل جداول الموظفين والمخزون والإدارة
"""

import os
import sys

# ⚠️ مهم: لازم قبل أي import من PySide6Widgets
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication, QFont, QIcon
from PySide6.QtWidgets import QApplication, QMessageBox


# ============================================================
# ✅ إعداد DPI — قبل إنشاء QApplication
# ============================================================
try:
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
except Exception:
    pass


# ============================================================
# Imports (بعد إعداد DPI)
# ============================================================
from core.database import Database
from core.database_extended import ExtendedDatabaseMixin
from utils.theme import Theme
from ui.login.login_window import LoginWindow
from ui.main_window import MainWindow

# ✅ استيراد نظام الحماية
from core.license import LicenseManager
from ui.activation_window import ActivationWindow


# ============================================================
# ✅ AppDatabase — دمج Database + Extended
# ============================================================
class AppDatabase(ExtendedDatabaseMixin, Database):
    """
    كلاس موحّد بيجمع:
    - Database (الأساسي)
    - ExtendedDatabaseMixin (الجداول الجديدة)

    الاستخدام:
        db = AppDatabase(db_path)
        db.init_extended_schema()  # ينشئ الجداول الجديدة
    """
    pass


# ============================================================
# App Controller
# ============================================================
class AppController:
    """يتحكم في دورة حياة التطبيق (License → Login → Main → Logout)."""

    def __init__(self, db):
        self.db = db
        self.qapp = None
        self.main_window = None
        self.login_window = None
        self.license_manager = LicenseManager(db.base_dir)

    # ============================================
    # Run
    # ============================================
    def run(self):
        self.qapp = QApplication.instance() or QApplication(sys.argv)
        self.qapp.setApplicationName("Barber Shop")
        self.qapp.setOrganizationName("BarberShop")
        self.qapp.setStyle("Fusion")

        # ✅ أيقونة التطبيق كله
        self._set_app_icon()

        # ✅ نمنع التطبيق إنه يقفل لما آخر نافذة تتقفل
        self.qapp.setQuitOnLastWindowClosed(False)

        # اتجاه التطبيق RTL
        self.qapp.setLayoutDirection(Qt.RightToLeft)

        # الخط الافتراضي
        font = QFont("Segoe UI", 10)
        self.qapp.setFont(font)

        # ✅ اقرأ الـ theme من قاعدة البيانات وطبّقه
        try:
            Theme.apply_from_db(self.db)
        except Exception:
            Theme.set_dark(True)

        # تطبيق الستايل
        self.qapp.setStyleSheet(Theme.stylesheet())

        # ابدأ دورة التطبيق
        QTimer.singleShot(0, self._start)

        return self.qapp.exec()

    # ============================================
    # App Icon
    # ============================================
    def _set_app_icon(self):
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            for icon_name in (
                "beauty-salon.png",
                "beauty-salon.ico",
                "haircut.png",
                "haircut.ico",
            ):
                icon_path = os.path.join(base_dir, icon_name)
                if os.path.exists(icon_path):
                    self.qapp.setWindowIcon(QIcon(icon_path))
                    return
        except Exception:
            pass

    # ============================================
    # Start
    # ============================================
    def _start(self):
        """يشوف الترخيص الأول، لو مش مفعّل يفتح شاشة التفعيل."""
        status = self.license_manager.get_status()

        if not status["valid"]:
            self._show_activation()
            return

        # لو باقي 7 أيام أو أقل → تحذير
        if status["days_left"] is not None and status["days_left"] <= 7:
            QMessageBox.warning(
                None,
                "⚠️  الاشتراك على وشك الانتهاء",
                f"{status['message']}\n\n"
                f"من فضلك تواصل مع المطور للتجديد في أقرب وقت."
            )

        self._show_login()

    # ============================================
    # Activation
    # ============================================
    def _show_activation(self):
        dlg = ActivationWindow(self.license_manager)

        if dlg.exec() == ActivationWindow.Accepted and dlg.activated:
            QTimer.singleShot(200, self._show_login)
        else:
            self._quit()

    # ============================================
    # Login
    # ============================================
    def _show_login(self):
        if self.main_window:
            try:
                self.main_window.close()
                self.main_window.deleteLater()
            except Exception:
                pass
            self.main_window = None

        self.login_window = LoginWindow(self.db)

        if self.login_window.exec() == LoginWindow.Accepted:
            if self.login_window.user:
                self._show_main(self.login_window.user)
                return

        self._quit()

    def _show_main(self, user):
        self.main_window = MainWindow(self.db, user, app_ref=self)
        self.main_window.show()

    # ============================================
    # Relaunch
    # ============================================
    def relaunch(self):
        if self.main_window:
            try:
                self.main_window.close()
            except Exception:
                pass
            try:
                self.main_window.deleteLater()
            except Exception:
                pass
            self.main_window = None

        QTimer.singleShot(300, self._show_login)

    # ============================================
    # Quit
    # ============================================
    def quit_app(self):
        try:
            self.db.backup_now()
        except Exception:
            pass
        if self.qapp:
            self.qapp.quit()

    def _quit(self):
        try:
            self.db.backup_now()
        except Exception:
            pass
        if self.qapp:
            self.qapp.quit()


# ============================================================
# MAIN
# ============================================================
def main():
    # مسار قاعدة البيانات
    db_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "barber_shop.db"
    )

    # ✅ إنشاء AppDatabase (Database + Extended)
    db = AppDatabase(db_path)

    # ✅ إنشاء الجداول الجديدة (الموظفين + المخزون + الإدارة)
    try:
        db.init_extended_schema()
        print("✅ تم تهيئة جداول الموظفين والمخزون والإدارة.")
    except Exception as e:
        print(f"⚠️  تحذير: فشل تهيئة الجداول الجديدة: {e}")
        print("    البرنامج هيفتح بس التابات الجديدة مش هتشتغل.")

    # تشغيل التطبيق
    controller = AppController(db)
    sys.exit(controller.run())


if __name__ == "__main__":
    main()