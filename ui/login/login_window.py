"""
Login Window — Ultimate Edition.
================================================
+ Logo from beauty-salon.png (HD) with .ico fallback
+ Gradient background + custom image (60% overlay) + fade/shake animations
+ Time-based greeting + last login + Hijri date
+ Forgot password + Guest mode + Brute force protection
+ Quick theme toggle + DB status indicator
+ Custom error messages + Attempts progress bar
+ Password strength meter + Sounds + Drag window
+ Employee badge + Stats preview + Employee of the Month
+ Personal greeting + Auto-lock + Multi-language
"""

import os
import json
import time
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QWidget, QMessageBox, QCheckBox,
    QProgressBar
)
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
)
from PySide6.QtGui import (
    QFont, QColor, QIcon, QPixmap, QLinearGradient,
    QPainter, QBrush
)

from utils.theme import Theme
from ui.login.login_extras import (
    play_sound,
    get_hijri_date,
    password_strength,
    translate,
    TRANSLATIONS,
    get_today_stats,
    format_stats_text,
    get_employee_of_month,
    format_employee_of_month_text,
    EmployeeBadgeDialog,
)


# ============================================================
# Files
# ============================================================
LAST_USER_FILE = "last_user.json"
HISTORY_FILE = "login_history.json"
FAILED_ATTEMPTS_FILE = "failed_attempts.json"
SETTINGS_FILE = "login_settings.json"

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 5
AUTO_LOCK_MINUTES = 30


# ============================================================
# ترتيب ملفات اللوجو (PNG الأول للأفضل جودة)
# ============================================================
LOGO_FILES = (
    "beauty-salon.png",
    "beauty-salon-hd.png",
    "beauty-salon.ico",
    "haircut.png",
    "haircut-hd.png",
    "haircut.ico",
)


# ============================================================
# Hints rotation
# ============================================================
USERNAME_HINTS = {
    "ar": [
        "ادخل اسم المستخدم",
        "مثال: admin",
        "اسمك المسجل في النظام",
        "اكتب اسم المستخدم هنا",
    ],
    "en": [
        "Enter your username",
        "Example: admin",
        "Your registered name",
        "Type username here",
    ],
}

PASSWORD_HINTS = {
    "ar": [
        "ادخل كلمة المرور",
        "••••••••",
        "كلمة المرور السرية",
        "محمية بالكامل 🔒",
    ],
    "en": [
        "Enter your password",
        "••••••••",
        "Your secret password",
        "Fully encrypted 🔒",
    ],
}


# ============================================================
# LOGIN WINDOW — Ultimate
# ============================================================
class LoginWindow(QDialog):
    """شاشة تسجيل الدخول — Ultimate Edition."""

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.user = None
        self.failed_attempts = self._load_failed_attempts()
        self.login_settings = self._load_login_settings()
        self.lang = self.login_settings.get("language", "ar")
        self.last_activity = time.time()

        self.setWindowTitle("تسجيل الدخول — صالون الحلاقة")
        self.setFixedSize(560, 850)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setLayoutDirection(Qt.RightToLeft)

        # لدعم سحب النافذة
        self._drag_pos = None

        # أيقونة النافذة
        self._set_window_icon()

        # stylesheet
        self._apply_stylesheet()

        self._center_on_screen()
        self._build_ui()
        self._bind_events()
        self._check_lockout()
        self._rotate_hints()
        self._start_auto_lock_timer()

        # fade in
        QTimer.singleShot(50, self._fade_in)

    # ============================================
    # Translation helper
    # ============================================
    def t(self, key, **kwargs):
        return translate(self.lang, key, **kwargs)

    # ============================================
    # Stylesheet
    # ============================================
    def _apply_stylesheet(self):
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
                border: 1px solid {Theme.color('border_strong')};
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 14px;
                selection-background-color: {Theme.color('primary')};
                selection-color: #ffffff;
            }}
            QLineEdit:focus {{
                border: 2px solid {Theme.color('primary')};
            }}
            QCheckBox {{
                color: {Theme.color('text')};
                spacing: 6px;
                background: transparent;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 2px solid {Theme.color('border_strong')};
                background-color: {Theme.color('surface')};
            }}
            QCheckBox::indicator:checked {{
                background-color: {Theme.color('primary')};
                border-color: {Theme.color('primary')};
            }}
            QProgressBar {{
                background-color: {Theme.color('surface_alt')};
                border: 1px solid {Theme.color('border')};
                border-radius: 4px;
                height: 8px;
            }}
            QProgressBar::chunk {{
                background-color: {Theme.color('warning')};
                border-radius: 4px;
            }}
        """)

    # ============================================
    # Window Icon + Logo — HD loading
    # ============================================
    def _set_window_icon(self):
        """يعين أيقونة النافذة."""
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            for icon_name in LOGO_FILES:
                icon_path = os.path.join(base_dir, icon_name)
                if os.path.exists(icon_path):
                    self.setWindowIcon(QIcon(icon_path))
                    return
        except Exception:
            pass

    def _load_logo_pixmap(self, size=90):
        """
        يحمّل اللوجو بجودة عالية.
        - يفضّل PNG على ICO
        - يستخدم SmoothTransformation للتصغير
        """
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            for logo_name in LOGO_FILES:
                logo_path = os.path.join(base_dir, logo_name)
                if not os.path.exists(logo_path):
                    continue

                pixmap = QPixmap(logo_path)
                if pixmap.isNull():
                    continue

                # لو الصورة أصغر من المطلوب، نستخدمها زي ما هي
                if pixmap.width() < size or pixmap.height() < size:
                    return pixmap

                return pixmap.scaled(
                    size, size,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
        except Exception:
            pass
        return None

    # ============================================
    # Background — Gradient + Custom Image (60% overlay)
    # ============================================
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        bg_image = None
        try:
            bg_image_path = self.db.get_setting("login_bg_image", "") or ""
            if bg_image_path and os.path.exists(bg_image_path):
                bg_image = QPixmap(bg_image_path)
        except Exception:
            pass

        if bg_image and not bg_image.isNull():
            scaled = bg_image.scaled(
                self.width(), self.height(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            x_offset = (scaled.width() - self.width()) // 2
            y_offset = (scaled.height() - self.height()) // 2
            painter.drawPixmap(-x_offset, -y_offset, scaled)

            if Theme.is_dark:
                overlay_color = QColor(0, 0, 0, 153)
            else:
                overlay_color = QColor(255, 255, 255, 153)

            painter.fillRect(self.rect(), overlay_color)
        else:
            gradient = QLinearGradient(0, 0, 0, self.height())
            top_color = QColor(Theme.color('bg'))
            bottom_color = QColor(Theme.color('surface'))

            if Theme.is_dark:
                gradient.setColorAt(0.0, top_color)
                gradient.setColorAt(0.5, bottom_color)
                gradient.setColorAt(1.0, QColor(Theme.color('bg')).darker(115))
            else:
                gradient.setColorAt(0.0, bottom_color)
                gradient.setColorAt(1.0, top_color)

            painter.fillRect(self.rect(), QBrush(gradient))

            accent = QColor(Theme.color('primary'))
            accent.setAlpha(35)
            painter.setBrush(QBrush(accent))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(-100, -100, 300, 300)
            painter.drawEllipse(
                self.width() - 200,
                self.height() - 200,
                300, 300
            )

        painter.end()
        super().paintEvent(event)

    # ============================================
    # Animations
    # ============================================
    def _fade_in(self):
        try:
            self.setWindowOpacity(0.0)
            self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
            self._fade_anim.setDuration(400)
            self._fade_anim.setStartValue(0.0)
            self._fade_anim.setEndValue(1.0)
            self._fade_anim.setEasingCurve(QEasingCurve.OutCubic)
            self._fade_anim.start()
        except Exception:
            self.setWindowOpacity(1.0)

    def _shake_window(self):
        try:
            geo = self.geometry()
            original = geo.topLeft()

            anim = QPropertyAnimation(self, b"pos")
            anim.setDuration(350)
            anim.setEasingCurve(QEasingCurve.OutElastic)

            offsets = [-12, 12, -8, 8, -4, 4, 0]
            for i, off in enumerate(offsets):
                anim.setKeyValueAt(
                    i / (len(offsets) - 1),
                    QPoint(original.x() + off, original.y())
                )

            self._shake_animation = anim
            anim.start()
        except Exception:
            pass

    # ============================================
    # Drag window
    # ============================================
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
            self._update_activity()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    # ============================================
    # Time-based Greeting
    # ============================================
    def _get_greeting(self):
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return self.t("greeting_morning")
        elif 12 <= hour < 17:
            return self.t("greeting_noon")
        elif 17 <= hour < 21:
            return self.t("greeting_evening")
        else:
            return self.t("greeting_night")

    # ============================================
    # DB Status
    # ============================================
    def _get_db_status(self):
        try:
            self.db.list_users()
            return "🟢", Theme.color('success'), self.t("db_online")
        except Exception:
            return "🔴", Theme.color('danger'), self.t("db_offline")

    # ============================================
    # Failed attempts
    # ============================================
    def _failed_path(self):
        return os.path.join(self.db.base_dir, FAILED_ATTEMPTS_FILE)

    def _load_failed_attempts(self):
        try:
            if os.path.exists(self._failed_path()):
                with open(self._failed_path(), "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _save_failed_attempts(self):
        try:
            with open(self._failed_path(), "w", encoding="utf-8") as f:
                json.dump(
                    self.failed_attempts, f,
                    ensure_ascii=False, indent=2
                )
        except Exception:
            pass

    def _record_failed_attempt(self, username):
        now = time.time()
        user_key = username.lower().strip()
        if user_key not in self.failed_attempts:
            self.failed_attempts[user_key] = []
        cutoff = now - (LOCKOUT_MINUTES * 60)
        self.failed_attempts[user_key] = [
            t for t in self.failed_attempts[user_key] if t > cutoff
        ]
        self.failed_attempts[user_key].append(now)
        self._save_failed_attempts()

    def _clear_failed_attempts(self, username):
        user_key = username.lower().strip()
        if user_key in self.failed_attempts:
            del self.failed_attempts[user_key]
            self._save_failed_attempts()

    def _check_lockout(self):
        username = self.username_entry.text().strip().lower()
        if not username or username not in self.failed_attempts:
            return False, 0

        now = time.time()
        cutoff = now - (LOCKOUT_MINUTES * 60)
        recent = [t for t in self.failed_attempts[username] if t > cutoff]

        if len(recent) >= MAX_LOGIN_ATTEMPTS:
            oldest = min(recent)
            remaining = int((oldest + LOCKOUT_MINUTES * 60) - now)
            if remaining > 0:
                return True, remaining

        return False, 0

    # ============================================
    # Auto-lock
    # ============================================
    def _update_activity(self):
        self.last_activity = time.time()

    def _start_auto_lock_timer(self):
        self._auto_lock_timer = QTimer(self)
        self._auto_lock_timer.timeout.connect(self._check_auto_lock)
        self._auto_lock_timer.start(30000)

    def _check_auto_lock(self):
        minutes = self.login_settings.get("auto_lock_minutes", AUTO_LOCK_MINUTES)
        if minutes <= 0:
            return
        idle = (time.time() - self.last_activity) / 60
        if idle >= minutes:
            try:
                self.reject()
            except Exception:
                pass

    # ============================================
    # Hints rotation
    # ============================================
    def _rotate_hints(self):
        try:
            u_hints = USERNAME_HINTS.get(self.lang, USERNAME_HINTS["ar"])
            idx = int(time.time()) % len(u_hints)
            if not self.username_entry.text():
                self.username_entry.setPlaceholderText(u_hints[idx])

            p_hints = PASSWORD_HINTS.get(self.lang, PASSWORD_HINTS["ar"])
            idx = int(time.time()) % len(p_hints)
            if not self.password_entry.text():
                self.password_entry.setPlaceholderText(p_hints[idx])
        except Exception:
            pass

        QTimer.singleShot(8000, self._rotate_hints)

    # ============================================
    # Positioning
    # ============================================
    def _center_on_screen(self):
        try:
            from PySide6.QtGui import QGuiApplication
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
        main = QVBoxLayout(self)
        main.setContentsMargins(30, 15, 30, 15)
        main.setSpacing(0)

        # ============================================
        # Top bar — Theme + Language + DB Status
        # ============================================
        top_bar = QHBoxLayout()
        top_bar.setSpacing(6)

        self.theme_btn = QPushButton("☀️" if Theme.is_dark else "🌙")
        self.theme_btn.setFixedSize(38, 38)
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.setToolTip("تبديل الوضع الليلي/النهاري")
        self.theme_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('surface')}; "
            f"color: {Theme.color('text')}; "
            f"border: 1px solid {Theme.color('border')}; "
            f"border-radius: 19px; font-size: 16px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('surface_alt')}; }}"
        )
        self.theme_btn.clicked.connect(self._toggle_theme)
        top_bar.addWidget(self.theme_btn)

        self.lang_btn = QPushButton("🌐")
        self.lang_btn.setFixedSize(38, 38)
        self.lang_btn.setCursor(Qt.PointingHandCursor)
        self.lang_btn.setToolTip("Switch language / تبديل اللغة")
        self.lang_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('surface')}; "
            f"color: {Theme.color('text')}; "
            f"border: 1px solid {Theme.color('border')}; "
            f"border-radius: 19px; font-size: 16px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('surface_alt')}; }}"
        )
        self.lang_btn.clicked.connect(self._toggle_language)
        top_bar.addWidget(self.lang_btn)

        top_bar.addStretch()

        db_icon, db_color, db_text = self._get_db_status()
        self.db_status = QLabel(f"{db_icon}  {db_text}")
        self.db_status.setStyleSheet(
            f"color: {db_color}; font-size: 11px; "
            f"background: {Theme.color('surface')}; "
            f"padding: 6px 12px; border-radius: 12px; "
            f"border: 1px solid {Theme.color('border')};"
        )
        top_bar.addWidget(self.db_status)

        main.addLayout(top_bar)
        main.addSpacing(8)

        # ============================================
        # Logo — HD
        # ============================================
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setFixedHeight(110)
        logo_label.setStyleSheet("background: transparent;")

        pixmap = self._load_logo_pixmap(100)
        if pixmap is not None:
            logo_label.setPixmap(pixmap)
        else:
            logo_label.setText("💈")
            logo_label.setStyleSheet(
                "font-size: 60px; padding: 10px; background: transparent;"
            )
        main.addWidget(logo_label)

        # ============================================
        # Shop name
        # ============================================
        shop_name = "صالون الحلاقة"
        try:
            shop_name = (
                self.db.get_setting("shop_name", "صالون الحلاقة")
                or "صالون الحلاقة"
            )
        except Exception:
            pass

        title = QLabel(shop_name)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"font-size: 22px; font-weight: bold; "
            f"color: {Theme.color('primary')}; padding: 4px; "
            f"background: transparent;"
        )
        main.addWidget(title)

        # ============================================
        # Greeting
        # ============================================
        greeting_label = QLabel(self._get_greeting())
        greeting_label.setAlignment(Qt.AlignCenter)
        greeting_label.setStyleSheet(
            f"font-size: 13px; font-weight: bold; padding: 2px; "
            f"color: {Theme.color('success')}; background: transparent;"
        )
        main.addWidget(greeting_label)

        # ============================================
        # Welcome
        # ============================================
        self.welcome_label = QLabel("")
        self.welcome_label.setAlignment(Qt.AlignCenter)
        self.welcome_label.setWordWrap(True)
        self.welcome_label.setStyleSheet(
            f"font-size: 11px; padding: 2px; "
            f"color: {Theme.color('text_muted')}; background: transparent;"
        )
        main.addWidget(self.welcome_label)

        hijri = get_hijri_date()
        if hijri:
            hijri_label = QLabel(f"📅  {hijri}")
            hijri_label.setAlignment(Qt.AlignCenter)
            hijri_label.setStyleSheet(
                f"font-size: 10px; padding: 2px; "
                f"color: {Theme.color('gold')}; background: transparent;"
            )
            main.addWidget(hijri_label)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(
            f"color: {Theme.color('border')}; "
            f"background: {Theme.color('border')}; "
            f"max-height: 1px; margin: 6px 0;"
        )
        main.addWidget(sep)

        # ============================================
        # Username
        # ============================================
        user_label = QLabel(self.t("username"))
        user_label.setAlignment(Qt.AlignRight)
        user_label.setStyleSheet(
            f"font-size: 12px; font-weight: bold; padding: 4px; "
            f"color: {Theme.color('text')}; background: transparent;"
        )
        main.addWidget(user_label)

        self.username_entry = QLineEdit()
        self.username_entry.setText(self._load_last_user())
        self.username_entry.setAlignment(Qt.AlignRight)
        self.username_entry.setMinimumHeight(42)
        self.username_entry.setClearButtonEnabled(True)
        main.addWidget(self.username_entry)

        # ============================================
        # Password
        # ============================================
        pass_label = QLabel(self.t("password"))
        pass_label.setAlignment(Qt.AlignRight)
        pass_label.setStyleSheet(
            f"font-size: 12px; font-weight: bold; padding: 4px; "
            f"color: {Theme.color('text')}; background: transparent;"
        )
        main.addWidget(pass_label)

        pass_wrap = QHBoxLayout()
        pass_wrap.setSpacing(0)

        self.password_entry = QLineEdit()
        self.password_entry.setEchoMode(QLineEdit.Password)
        self.password_entry.setAlignment(Qt.AlignRight)
        self.password_entry.setMinimumHeight(42)
        self.password_entry.setStyleSheet(
            f"QLineEdit {{ background-color: {Theme.color('surface')}; "
            f"color: {Theme.color('text')}; "
            f"border: 1px solid {Theme.color('border_strong')}; "
            f"border-top-right-radius: 0; border-bottom-right-radius: 0; "
            f"border-top-left-radius: 8px; border-bottom-left-radius: 8px; "
            f"padding: 6px 14px; font-size: 14px; }}"
            f"QLineEdit:focus {{ border: 2px solid {Theme.color('primary')}; }}"
        )

        self.show_pass_btn = QPushButton("👁")
        self.show_pass_btn.setFixedWidth(48)
        self.show_pass_btn.setMinimumHeight(42)
        self.show_pass_btn.setCursor(Qt.PointingHandCursor)
        self.show_pass_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('surface_alt')}; "
            f"color: {Theme.color('text')}; border: none; "
            f"border-top-left-radius: 8px; border-bottom-left-radius: 8px; "
            f"border-top-right-radius: 0; border-bottom-right-radius: 0; "
            f"font-size: 16px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('border_strong')}; }}"
        )
        self.show_pass_btn.setCheckable(True)

        pass_wrap.addWidget(self.show_pass_btn)
        pass_wrap.addWidget(self.password_entry)

        pass_container = QWidget()
        pass_container.setLayout(pass_wrap)
        main.addWidget(pass_container)

        # ============================================
        # Password strength
        # ============================================
        strength_row = QHBoxLayout()
        strength_row.setSpacing(8)

        self.strength_label = QLabel("")
        self.strength_label.setStyleSheet(
            f"font-size: 10px; color: {Theme.color('text_muted')}; "
            f"background: transparent; padding: 0 4px;"
        )
        strength_row.addWidget(self.strength_label)
        strength_row.addStretch()
        main.addLayout(strength_row)

        # ============================================
        # Remember + Forgot
        # ============================================
        options_row = QHBoxLayout()
        options_row.setSpacing(8)

        self.remember_cb = QCheckBox(self.t("remember_me"))
        self.remember_cb.setChecked(True)
        self.remember_cb.setStyleSheet(
            f"font-size: 12px; padding: 4px 0; "
            f"color: {Theme.color('text')}; background: transparent;"
        )
        options_row.addWidget(self.remember_cb)

        options_row.addStretch()

        self.forgot_btn = QPushButton(self.t("forgot"))
        self.forgot_btn.setCursor(Qt.PointingHandCursor)
        self.forgot_btn.setStyleSheet(
            f"QPushButton {{ background-color: transparent; "
            f"color: {Theme.color('info')}; border: none; "
            f"font-size: 11px; text-decoration: underline; padding: 4px; }}"
            f"QPushButton:hover {{ color: {Theme.color('primary')}; }}"
        )
        self.forgot_btn.clicked.connect(self._show_forgot_password)
        options_row.addWidget(self.forgot_btn)

        main.addLayout(options_row)

        # ============================================
        # Attempts bar
        # ============================================
        self.attempts_bar = QProgressBar()
        self.attempts_bar.setMaximum(MAX_LOGIN_ATTEMPTS)
        self.attempts_bar.setValue(0)
        self.attempts_bar.setTextVisible(False)
        self.attempts_bar.setFixedHeight(8)
        self.attempts_bar.setVisible(False)
        main.addWidget(self.attempts_bar)

        self.lockout_label = QLabel("")
        self.lockout_label.setAlignment(Qt.AlignCenter)
        self.lockout_label.setWordWrap(True)
        self.lockout_label.setStyleSheet(
            f"font-size: 11px; padding: 4px; "
            f"color: {Theme.color('danger')}; background: transparent;"
        )
        self.lockout_label.setVisible(False)
        main.addWidget(self.lockout_label)

        # ============================================
        # Login button
        # ============================================
        self.login_btn = QPushButton(self.t("login"))
        self.login_btn.setMinimumHeight(48)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('primary')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"font-size: 15px; font-weight: bold; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('primary_hover')}; }}"
            f"QPushButton:pressed {{ background-color: {Theme.color('primary_dark')}; }}"
            f"QPushButton:disabled {{ background-color: {Theme.color('border')}; "
            f"color: {Theme.color('text_dim')}; }}"
        )
        main.addWidget(self.login_btn)

        # ============================================
        # Guest button
        # ============================================
        self.guest_btn = QPushButton(self.t("guest"))
        self.guest_btn.setMinimumHeight(38)
        self.guest_btn.setCursor(Qt.PointingHandCursor)
        self.guest_btn.setStyleSheet(
            f"QPushButton {{ background-color: transparent; "
            f"color: {Theme.color('text_muted')}; "
            f"border: 1px dashed {Theme.color('border_strong')}; "
            f"border-radius: 8px; font-size: 11px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('surface_alt')}; "
            f"color: {Theme.color('text')}; "
            f"border-color: {Theme.color('primary')}; }}"
        )
        self.guest_btn.clicked.connect(self._guest_login)
        main.addWidget(self.guest_btn)

        # ============================================
        # Bottom row — Stats + EOTM + Badge
        # ============================================
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(6)

        stats_btn = QPushButton("📊")
        stats_btn.setFixedHeight(34)
        stats_btn.setCursor(Qt.PointingHandCursor)
        stats_btn.setToolTip(self.t("today_stats"))
        stats_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('surface')}; "
            f"color: {Theme.color('text')}; "
            f"border: 1px solid {Theme.color('border')}; "
            f"border-radius: 6px; font-size: 14px; padding: 4px 12px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('surface_alt')}; "
            f"border-color: {Theme.color('primary')}; }}"
        )
        stats_btn.clicked.connect(self._show_stats)
        bottom_row.addWidget(stats_btn)

        eotm_btn = QPushButton("🏆")
        eotm_btn.setFixedHeight(34)
        eotm_btn.setCursor(Qt.PointingHandCursor)
        eotm_btn.setToolTip(self.t("employee_of_month"))
        eotm_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('surface')}; "
            f"color: {Theme.color('text')}; "
            f"border: 1px solid {Theme.color('border')}; "
            f"border-radius: 6px; font-size: 14px; padding: 4px 12px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('surface_alt')}; "
            f"border-color: {Theme.color('gold')}; }}"
        )
        eotm_btn.clicked.connect(self._show_employee_of_month)
        bottom_row.addWidget(eotm_btn)

        badge_btn = QPushButton("🖨")
        badge_btn.setFixedHeight(34)
        badge_btn.setCursor(Qt.PointingHandCursor)
        badge_btn.setToolTip(self.t("print_badge"))
        badge_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('surface')}; "
            f"color: {Theme.color('text')}; "
            f"border: 1px solid {Theme.color('border')}; "
            f"border-radius: 6px; font-size: 14px; padding: 4px 12px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('surface_alt')}; "
            f"border-color: {Theme.color('success')}; }}"
        )
        badge_btn.clicked.connect(self._show_badge)
        bottom_row.addWidget(badge_btn)

        bottom_row.addStretch()
        main.addLayout(bottom_row)

        # ============================================
        # Footer
        # ============================================
        footer = QLabel(self.t("footer"))
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet(
            f"font-size: 10px; color: {Theme.color('text_dim')}; "
            f"padding-top: 8px; background: transparent;"
        )
        main.addWidget(footer)

        main.addStretch()

        self._update_welcome_message()

    # ============================================
    # Language toggle
    # ============================================
    def _toggle_language(self):
        self.lang = "en" if self.lang == "ar" else "ar"
        self.login_settings["language"] = self.lang
        self._save_login_settings()

        try:
            self._rebuild_ui()
        except Exception:
            pass

    def _rebuild_ui(self):
        old_layout = self.layout()
        if old_layout:
            while old_layout.count():
                item = old_layout.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()
                elif item.layout():
                    self._clear_layout(item.layout())
            QWidget().setLayout(old_layout)

        self._build_ui()
        self._bind_events()

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    # ============================================
    # Stats / EOTM / Badge
    # ============================================
    def _show_stats(self):
        stats = get_today_stats(self.db)
        text = format_stats_text(stats, self.lang)
        QMessageBox.information(self, self.t("today_stats"), text)

    def _show_employee_of_month(self):
        emp = get_employee_of_month(self.db)
        text = format_employee_of_month_text(emp, self.lang)
        QMessageBox.information(self, self.t("employee_of_month"), text)

    def _show_badge(self):
        """يعرض بطاقة الموظف."""
        username = self.username_entry.text().strip()
        if not username:
            QMessageBox.warning(
                self, "تنبيه",
                "اكتب اسم المستخدم الأول عشان تعرض بطاقته."
            )
            return

        try:
            users = self.db.list_users()
            target_user = None
            for u in users:
                if u.username.lower() == username.lower():
                    target_user = u
                    break

            if not target_user:
                QMessageBox.warning(
                    self, "خطأ",
                    f"المستخدم «{username}» مش موجود."
                )
                return

            play_sound("click")
            dlg = EmployeeBadgeDialog(
                self, db=self.db, user=target_user, lang=self.lang
            )
            dlg.exec()

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل عرض البطاقة:\n{e}")

    # ============================================
    # Theme Toggle
    # ============================================
    def _toggle_theme(self):
        try:
            new_is_dark = not Theme.is_dark
            new_mode = "dark_navy" if new_is_dark else "light_clean"
            self.db.set_setting("theme", new_mode)
            Theme.set_theme(new_mode)
            Theme.apply_to_app()
            self.theme_btn.setText("☀️" if Theme.is_dark else "🌙")
            self._apply_stylesheet()
            self.update()
        except Exception:
            pass

    # ============================================
    # Welcome message
    # ============================================
    def _update_welcome_message(self):
        username = self.username_entry.text().strip()

        if not username:
            self.welcome_label.setText("أهلاً بك في نظام إدارة الصالون")
            return

        last_login = ""
        try:
            history = self._load_history()
            if username in history:
                last_login = history[username].get("last_login", "")
        except Exception:
            pass

        if last_login:
            self.welcome_label.setText(
                f"👋  {self.t('welcome_back')}، {username}\n"
                f"🕐  {self.t('last_login')}: {last_login}"
            )
        else:
            self.welcome_label.setText(
                f"👋  {self.t('welcome_new')}، {username}"
            )

    # ============================================
    # Events
    # ============================================
    def _bind_events(self):
        self.login_btn.clicked.connect(self.try_login)
        self.password_entry.returnPressed.connect(self.try_login)
        self.username_entry.returnPressed.connect(
            lambda: self.password_entry.setFocus()
        )
        self.show_pass_btn.toggled.connect(self._toggle_password)
        self.username_entry.textChanged.connect(self._update_welcome_message)
        self.password_entry.textChanged.connect(self._update_strength)

        QTimer.singleShot(100, self._focus_first_field)

    def _focus_first_field(self):
        if self.username_entry.text():
            self.password_entry.setFocus()
        else:
            self.username_entry.setFocus()

    def _toggle_password(self, checked):
        if checked:
            self.password_entry.setEchoMode(QLineEdit.Normal)
            self.show_pass_btn.setText("🙈")
        else:
            self.password_entry.setEchoMode(QLineEdit.Password)
            self.show_pass_btn.setText("👁")

    def _update_strength(self):
        pwd = self.password_entry.text()
        if not pwd:
            self.strength_label.setText("")
            return

        score, label, color = password_strength(pwd)
        self.strength_label.setText(f"قوة كلمة المرور: {label}")
        self.strength_label.setStyleSheet(
            f"font-size: 10px; color: {color}; "
            f"background: transparent; padding: 0 4px;"
        )

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
            return
        self._update_activity()
        super().keyPressEvent(event)

    # ============================================
    # Forgot Password
    # ============================================
    def _show_forgot_password(self):
        try:
            shop_phone = self.db.get_setting("shop_phone", "") or ""
        except Exception:
            shop_phone = ""

        msg = self.t("forgot_msg", phone=shop_phone or "—")
        QMessageBox.information(self, self.t("forgot_title"), msg)

    # ============================================
    # Guest Login
    # ============================================
    def _guest_login(self):
        try:
            users = self.db.list_users()
            guest_user = None
            for u in users:
                if u.username.lower() == "guest":
                    guest_user = u
                    break

            if guest_user is None:
                self.db.add_user(
                    "guest", "guest", "employee",
                    {"view_services": True, "view_customers": True}
                )
                users = self.db.list_users()
                for u in users:
                    if u.username.lower() == "guest":
                        guest_user = u
                        break

            if guest_user is None:
                QMessageBox.warning(
                    self, "خطأ",
                    "مش قادر أنشئ حساب الضيف."
                )
                return

            play_sound("guest")
            self.user = guest_user
            self.db.set_current_user(guest_user)

            QMessageBox.information(
                self, "دخول كضيف",
                "🎭  مرحباً بك كضيف!\n\n"
                "ملاحظة: بعض الصلاحيات محدودة في الوضع التجريبي."
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل الدخول كضيف:\n{e}")

    # ============================================
    # Persistence
    # ============================================
    def _path(self, filename):
        return os.path.join(self.db.base_dir, filename)

    def _load_last_user(self):
        try:
            with open(self._path(LAST_USER_FILE), "r", encoding="utf-8") as f:
                return json.load(f).get("username", "")
        except (OSError, json.JSONDecodeError):
            return ""

    def _save_last_user(self, username):
        try:
            with open(self._path(LAST_USER_FILE), "w", encoding="utf-8") as f:
                json.dump({"username": username}, f, ensure_ascii=False)
        except OSError:
            pass

    def _load_history(self):
        try:
            with open(self._path(HISTORY_FILE), "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return {}

    def _save_history(self, username):
        try:
            history = self._load_history()
            history[username] = {
                "last_login": time.strftime("%Y-%m-%d %H:%M")
            }
            with open(self._path(HISTORY_FILE), "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def _load_login_settings(self):
        try:
            if os.path.exists(self._path(SETTINGS_FILE)):
                with open(self._path(SETTINGS_FILE), "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {"language": "ar", "auto_lock_minutes": AUTO_LOCK_MINUTES}

    def _save_login_settings(self):
        try:
            with open(self._path(SETTINGS_FILE), "w", encoding="utf-8") as f:
                json.dump(
                    self.login_settings, f,
                    ensure_ascii=False, indent=2
                )
        except Exception:
            pass

    # ============================================
    # Login
    # ============================================
    def try_login(self):
        self._update_activity()
        username = self.username_entry.text().strip()
        password = self.password_entry.text()

        if not username or not password:
            play_sound("warning")
            self._shake_window()
            QMessageBox.warning(self, "خطأ", self.t("err_empty"))
            return

        is_locked, remaining = self._check_lockout()
        if is_locked:
            play_sound("lock")
            self._shake_window()
            QMessageBox.warning(
                self,
                f"🔒  {self.t('err_locked')}",
                f"{self.t('err_try_after')} {remaining} {self.t('err_seconds')}."
            )
            return

        self.login_btn.setText("جاري التحقق...")
        self.login_btn.setEnabled(False)
        self.repaint()

        user = self.db.verify_login(username, password)

        if user is None:
            play_sound("error")
            self._record_failed_attempt(username)
            self._update_attempts_bar(username)

            self.login_btn.setText(self.t("login"))
            self.login_btn.setEnabled(True)
            self._shake_window()

            user_key = username.lower().strip()
            attempts = len(self.failed_attempts.get(user_key, []))
            remaining_attempts = MAX_LOGIN_ATTEMPTS - attempts

            try:
                users = self.db.list_users()
                user_exists = any(
                    u.username.lower() == user_key for u in users
                )
            except Exception:
                user_exists = True

            if not user_exists:
                msg = f"❌  {self.t('err_user_not_found')}: {username}"
            else:
                msg = f"❌  {self.t('err_wrong_password')}"

            if 0 < remaining_attempts <= 3:
                msg += (
                    f"\n\n⚠️  "
                    f"{self.t('err_remaining_attempts', n=remaining_attempts)}"
                )

            QMessageBox.critical(self, "خطأ", msg)
            self.password_entry.clear()
            self.password_entry.setFocus()
            return

        # ✅ نجح
        play_sound("success")
        self._clear_failed_attempts(username)
        self.attempts_bar.setVisible(False)

        if self.remember_cb.isChecked():
            self._save_last_user(username)
        self._save_history(username)

        self.user = user
        self.accept()

    def _update_attempts_bar(self, username):
        user_key = username.lower().strip()
        attempts = len(self.failed_attempts.get(user_key, []))

        if attempts > 0:
            self.attempts_bar.setVisible(True)
            self.attempts_bar.setValue(attempts)

            if attempts >= 4:
                color = Theme.color('danger')
            elif attempts >= 3:
                color = Theme.color('warning')
            else:
                color = Theme.color('success')

            self.attempts_bar.setStyleSheet(
                f"QProgressBar {{ background-color: {Theme.color('surface_alt')}; "
                f"border: 1px solid {Theme.color('border')}; "
                f"border-radius: 4px; height: 8px; }}"
                f"QProgressBar::chunk {{ background-color: {color}; "
                f"border-radius: 4px; }}"
            )
