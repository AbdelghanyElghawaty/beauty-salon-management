"""
Activation Window — شاشة التفعيل اللي بتظهر لو الجهاز مش مفعّل.
+ دعم عرض رسالة مخصصة لو الاشتراك منتهي
+ Light/Dark theme support
"""

import sys
from PySide6.QtWidgets import (  # pyright: ignore[reportMissingImports]
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, QTimer  # pyright: ignore[reportMissingImports]
from PySide6.QtGui import QGuiApplication, QFont  # pyright: ignore[reportMissingImports]

from utils.theme import Theme


class ActivationWindow(QDialog):
    """شاشة التفعيل — المستخدم يدخل كود التفعيل اللي إنت بعتله."""

    def __init__(self, license_manager, parent=None):
        super().__init__(parent)
        self.license_manager = license_manager
        self.activated = False

        self.setWindowTitle("تفعيل البرنامج")
        self.setFixedSize(560, 620)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        # ✅ ستايل ديناميكي
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Theme.color('bg')};
            }}
            QLabel {{
                color: {Theme.color('text')};
                background: transparent;
            }}
            QLineEdit {{
                background-color: {Theme.color('surface')};
                color: {Theme.color('text')};
                border: 2px solid {Theme.color('border_strong')};
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 16px;
                font-family: 'Consolas', monospace;
                font-weight: bold;
                letter-spacing: 2px;
                selection-background-color: {Theme.color('primary')};
                selection-color: #ffffff;
            }}
            QLineEdit:focus {{
                border: 2px solid {Theme.color('primary')};
            }}
        """)

        self._center_on_screen()
        self._build_ui()

    # ============================================
    # Positioning
    # ============================================
    def _center_on_screen(self):
        try:
            screen = QGuiApplication.primaryScreen().availableGeometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)
        except Exception:
            pass

    # ============================================
    # UI
    # ============================================
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(14)

        # أيقونة
        icon = QLabel("🔒")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("font-size: 60px; background: transparent;")
        layout.addWidget(icon)

        # العنوان
        title = QLabel("تفعيل البرنامج")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"font-size: 22px; font-weight: bold; "
            f"color: {Theme.color('primary')}; background: transparent;"
        )
        layout.addWidget(title)

        subtitle = QLabel(
            "البرنامج ده محمي. عشان تفعّله، ابعت بصمة الجهاز\n"
            "للمطوّر وهيوصلك كود التفعيل."
        )
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(
            f"font-size: 12px; color: {Theme.color('text_muted')}; "
            f"background: transparent; line-height: 1.5;"
        )
        layout.addWidget(subtitle)

        # ⚠️ لو الترخيص منتهي، نعرض رسالة مختلفة
        status = self.license_manager.get_status()
        if status["expired"]:
            title.setText("انتهى الاشتراك")
            icon.setText("⏰")
            subtitle.setText(
                f"⚠️  انتهى اشتراكك بتاريخ {status['expiry_date']}\n"
                f"من فضلك تواصل مع المطور للتجديد."
            )
            subtitle.setStyleSheet(
                f"font-size: 12px; color: {Theme.color('warning')}; "
                f"background: transparent; line-height: 1.6; "
                f"font-weight: bold;"
            )
        elif status["activated"] and not status["valid"]:
            title.setText("مشكلة في الترخيص")
            icon.setText("⚠️")
            subtitle.setText(status["message"])

        # فاصل
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(
            f"color: {Theme.color('border')}; "
            f"background: {Theme.color('border')}; max-height: 1px;"
        )
        layout.addWidget(sep)

        # ============================================
        # بصمة الجهاز
        # ============================================
        hw_label = QLabel("🔑  بصمة جهازك (Hardware ID):")
        hw_label.setStyleSheet(
            f"font-size: 12px; font-weight: bold; "
            f"color: {Theme.color('text')}; background: transparent;"
        )
        layout.addWidget(hw_label)

        hw_frame = QFrame()
        hw_frame.setStyleSheet(
            f"QFrame {{ background-color: {Theme.color('surface')}; "
            f"border: 2px dashed {Theme.color('warning')}; "
            f"border-radius: 8px; }}"
        )
        hw_layout = QHBoxLayout(hw_frame)
        hw_layout.setContentsMargins(12, 10, 12, 10)
        hw_layout.setSpacing(10)

        self.hw_display = QLineEdit(self.license_manager.hardware_id)
        self.hw_display.setReadOnly(True)
        self.hw_display.setAlignment(Qt.AlignCenter)
        self.hw_display.setStyleSheet(
            f"QLineEdit {{ background-color: transparent; "
            f"color: {Theme.color('warning')}; border: none; "
            f"font-size: 16px; font-family: 'Consolas', monospace; "
            f"font-weight: bold; letter-spacing: 2px; padding: 4px; }}"
        )
        hw_layout.addWidget(self.hw_display, 1)

        copy_btn = QPushButton("📋  نسخ")
        copy_btn.setFixedSize(90, 40)
        copy_btn.setCursor(Qt.PointingHandCursor)
        copy_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('primary')}; "
            f"color: white; border: none; border-radius: 6px; "
            f"font-weight: bold; font-size: 12px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('primary_hover')}; }}"
        )
        copy_btn.clicked.connect(self._copy_hw_id)
        hw_layout.addWidget(copy_btn)

        layout.addWidget(hw_frame)

        # ============================================
        # كود التفعيل
        # ============================================
        code_label = QLabel("🔐  كود التفعيل:")
        code_label.setStyleSheet(
            f"font-size: 12px; font-weight: bold; "
            f"color: {Theme.color('text')}; background: transparent;"
        )
        layout.addWidget(code_label)

        self.code_entry = QLineEdit()
        self.code_entry.setPlaceholderText("XXXXX-XXXXX-XXXXX-XXXXX")
        self.code_entry.setMinimumHeight(50)
        self.code_entry.setAlignment(Qt.AlignCenter)
        self.code_entry.setMaxLength(23)  # 20 حرف + 3 شرطات
        self.code_entry.textChanged.connect(self._format_code)
        layout.addWidget(self.code_entry)

        # ============================================
        # أزرار
        # ============================================
        layout.addSpacing(10)

        activate_btn = QPushButton("✓  تفعيل البرنامج")
        activate_btn.setMinimumHeight(52)
        activate_btn.setCursor(Qt.PointingHandCursor)
        activate_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('success')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"font-size: 15px; font-weight: bold; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('success_hover')}; }}"
        )
        activate_btn.clicked.connect(self._activate)
        layout.addWidget(activate_btn)

        exit_btn = QPushButton("إغلاق")
        exit_btn.setMinimumHeight(42)
        exit_btn.setCursor(Qt.PointingHandCursor)
        exit_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('surface_alt')}; "
            f"color: {Theme.color('text')}; border: none; border-radius: 8px; "
            f"font-size: 13px; font-weight: bold; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('border_strong')}; }}"
        )
        exit_btn.clicked.connect(self.reject)
        layout.addWidget(exit_btn)

        # Footer
        footer = QLabel("© 2026 — البرنامج محمي بكود تفعيل")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet(
            f"font-size: 10px; color: {Theme.color('text_dim')}; "
            f"background: transparent; padding-top: 8px;"
        )
        layout.addWidget(footer)

        QTimer.singleShot(100, self.code_entry.setFocus)

    # ============================================
    # Helpers
    # ============================================
    def _copy_hw_id(self):
        """ينسخ بصمة الجهاز للحافظة."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.license_manager.hardware_id)
        QMessageBox.information(
            self, "تم النسخ",
            "تم نسخ بصمة الجهاز.\n\n"
            "ابعت البصمة دي للمطوّر عشان يوصلك كود التفعيل."
        )

    def _format_code(self, text):
        """يضيف الشرطات تلقائيًا كل 5 حروف."""
        clean = text.replace("-", "").upper()
        clean = "".join(c for c in clean if c.isalnum())
        clean = clean[:20]

        parts = [clean[i:i+5] for i in range(0, len(clean), 5)]
        formatted = "-".join(parts)

        if formatted != text:
            self.code_entry.blockSignals(True)
            self.code_entry.setText(formatted)
            self.code_entry.setCursorPosition(len(formatted))
            self.code_entry.blockSignals(False)

    def _activate(self):
        """يحاول التفعيل بالكود اللي المستخدم دخله."""
        code = self.code_entry.text().strip()

        if len(code.replace("-", "")) != 20:
            QMessageBox.warning(
                self, "كود ناقص",
                "كود التفعيل لازم يكون 20 حرف.\n"
                "تأكد إنك نسخته كامل."
            )
            return

        ok, msg = self.license_manager.activate(code)

        if ok:
            self.activated = True
            QMessageBox.information(self, "تم التفعيل", msg)
            self.accept()
        else:
            QMessageBox.critical(self, "فشل التفعيل", msg)
            self.code_entry.clear()
            self.code_entry.setFocus()