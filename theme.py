"""
Theme — PySide6 with DPI-aware styling + Multi-theme support.
6 themes: Dark Navy / Dark Purple / Light Clean / Nord / Sunset / Forest
"""

from PySide6.QtWidgets import QApplication


# ============================================================
# COLORS — Dark Navy (Default)
# ============================================================
DARK_NAVY = {
    "bg": "#0f172a",
    "bg_alt": "#1e293b",
    "surface": "#1e293b",
    "surface_alt": "#334155",
    "border": "#334155",
    "border_strong": "#475569",

    "primary": "#3b82f6",
    "primary_hover": "#2563eb",
    "primary_dark": "#1d4ed8",

    "success": "#10b981",
    "success_hover": "#059669",

    "danger": "#ef4444",
    "danger_hover": "#dc2626",

    "warning": "#f59e0b",
    "warning_hover": "#d97706",

    "info": "#06b6d4",
    "info_hover": "#0891b2",

    "gold": "#d4af37",

    "text": "#f1f5f9",
    "text_muted": "#94a3b8",
    "text_dim": "#64748b",

    "row_alt": "#1e293b",
    "row_hover": "#334155",
    "selection": "#3b82f6",

    "statusbar": "#020617",
}


# ============================================================
# COLORS — Dark Purple
# ============================================================
DARK_PURPLE = {
    "bg": "#1a0f2e",
    "bg_alt": "#2d1b4e",
    "surface": "#2d1b4e",
    "surface_alt": "#3d2666",
    "border": "#3d2666",
    "border_strong": "#5a3a8c",

    "primary": "#a855f7",
    "primary_hover": "#9333ea",
    "primary_dark": "#7e22ce",

    "success": "#10b981",
    "success_hover": "#059669",

    "danger": "#ef4444",
    "danger_hover": "#dc2626",

    "warning": "#f59e0b",
    "warning_hover": "#d97706",

    "info": "#06b6d4",
    "info_hover": "#0891b2",

    "gold": "#fbbf24",

    "text": "#f5f3ff",
    "text_muted": "#c4b5fd",
    "text_dim": "#8b5cf6",

    "row_alt": "#2d1b4e",
    "row_hover": "#3d2666",
    "selection": "#a855f7",

    "statusbar": "#0f0820",
}


# ============================================================
# COLORS — Light Clean
# ============================================================
LIGHT_CLEAN = {
    "bg": "#f8fafc",
    "bg_alt": "#f1f5f9",
    "surface": "#ffffff",
    "surface_alt": "#f1f5f9",
    "border": "#e2e8f0",
    "border_strong": "#cbd5e1",

    "primary": "#3b82f6",
    "primary_hover": "#2563eb",
    "primary_dark": "#1d4ed8",

    "success": "#10b981",
    "success_hover": "#059669",

    "danger": "#ef4444",
    "danger_hover": "#dc2626",

    "warning": "#f59e0b",
    "warning_hover": "#d97706",

    "info": "#06b6d4",
    "info_hover": "#0891b2",

    "gold": "#d4af37",

    "text": "#0f172a",
    "text_muted": "#64748b",
    "text_dim": "#94a3b8",

    "row_alt": "#f8fafc",
    "row_hover": "#e2e8f0",
    "selection": "#3b82f6",

    "statusbar": "#1e293b",
}


# ============================================================
# COLORS — Nord (رمادي أزرق بارد)
# ============================================================
NORD = {
    "bg": "#2e3440",
    "bg_alt": "#3b4252",
    "surface": "#3b4252",
    "surface_alt": "#434c5e",
    "border": "#434c5e",
    "border_strong": "#4c566a",

    "primary": "#88c0d0",
    "primary_hover": "#8fbcbb",
    "primary_dark": "#5e81ac",

    "success": "#a3be8c",
    "success_hover": "#8faf7c",

    "danger": "#bf616a",
    "danger_hover": "#a54e56",

    "warning": "#ebcb8b",
    "warning_hover": "#d4b175",

    "info": "#81a1c1",
    "info_hover": "#6d8da8",

    "gold": "#ebcb8b",

    "text": "#eceff4",
    "text_muted": "#d8dee9",
    "text_dim": "#7b88a1",

    "row_alt": "#3b4252",
    "row_hover": "#434c5e",
    "selection": "#88c0d0",

    "statusbar": "#242933",
}


# ============================================================
# COLORS — Sunset (برتقالي داكن دافئ)
# ============================================================
SUNSET = {
    "bg": "#1c1917",
    "bg_alt": "#292524",
    "surface": "#292524",
    "surface_alt": "#3f3f3f",
    "border": "#44403c",
    "border_strong": "#57534e",

    "primary": "#f97316",
    "primary_hover": "#ea580c",
    "primary_dark": "#c2410c",

    "success": "#22c55e",
    "success_hover": "#16a34a",

    "danger": "#ef4444",
    "danger_hover": "#dc2626",

    "warning": "#eab308",
    "warning_hover": "#ca8a04",

    "info": "#06b6d4",
    "info_hover": "#0891b2",

    "gold": "#fbbf24",

    "text": "#fafaf9",
    "text_muted": "#a8a29e",
    "text_dim": "#78716c",

    "row_alt": "#292524",
    "row_hover": "#3f3f3f",
    "selection": "#f97316",

    "statusbar": "#0c0a09",
}


# ============================================================
# COLORS — Forest (أخضر داكن طبيعي)
# ============================================================
FOREST = {
    "bg": "#0f1f14",
    "bg_alt": "#1a2e22",
    "surface": "#1a2e22",
    "surface_alt": "#254230",
    "border": "#254230",
    "border_strong": "#3a6b4b",

    "primary": "#22c55e",
    "primary_hover": "#16a34a",
    "primary_dark": "#15803d",

    "success": "#4ade80",
    "success_hover": "#22c55e",

    "danger": "#ef4444",
    "danger_hover": "#dc2626",

    "warning": "#fbbf24",
    "warning_hover": "#f59e0b",

    "info": "#06b6d4",
    "info_hover": "#0891b2",

    "gold": "#fbbf24",

    "text": "#dcfce7",
    "text_muted": "#86efac",
    "text_dim": "#4ade80",

    "row_alt": "#1a2e22",
    "row_hover": "#254230",
    "selection": "#22c55e",

    "statusbar": "#0a1810",
}


# ============================================================
# قائمة الثيمات المتاحة
# ============================================================
THEMES = {
    "dark_navy": {
        "name": "🌙  Dark Navy",
        "colors": DARK_NAVY,
        "is_dark": True,
    },
    "dark_purple": {
        "name": "🖤  Dark Purple",
        "colors": DARK_PURPLE,
        "is_dark": True,
    },
    "light_clean": {
        "name": "☀️  Light Clean",
        "colors": LIGHT_CLEAN,
        "is_dark": False,
    },
    "nord": {
        "name": "❄️  Nord",
        "colors": NORD,
        "is_dark": True,
    },
    "sunset": {
        "name": "🌅  Sunset",
        "colors": SUNSET,
        "is_dark": True,
    },
    "forest": {
        "name": "🌲  Forest",
        "colors": FOREST,
        "is_dark": True,
    },
}


class Theme:
    COLORS = DARK_NAVY
    is_dark = True
    current_name = "dark_navy"

    @classmethod
    def set_theme(cls, name):
        """يغير الثيم الحالي."""
        if name not in THEMES:
            name = "dark_navy"
        theme_data = THEMES[name]
        cls.COLORS = theme_data["colors"]
        cls.is_dark = theme_data["is_dark"]
        cls.current_name = name

    @classmethod
    def set_dark(cls, dark=True):
        """لـ backward compatibility — بيختار dark_navy أو light_clean."""
        cls.set_theme("dark_navy" if dark else "light_clean")

    @classmethod
    def color(cls, key):
        return cls.COLORS.get(key, "#000000")

    @classmethod
    def list_themes(cls):
        """يرجع قائمة الثيمات المتاحة."""
        return list(THEMES.keys())

    @classmethod
    def get_theme_name(cls, key):
        """يرجع اسم الثيم بالعربي."""
        return THEMES.get(key, {}).get("name", key)

    # ============================================
    # ✅ تطبيق من قاعدة البيانات
    # ============================================
    @classmethod
    def apply_from_db(cls, db):
        """يقرأ theme من settings ويطبّقه."""
        try:
            mode = db.get_setting("theme", "dark_navy")
            if mode in THEMES:
                cls.set_theme(mode)
                return True
            # fallback: القيم القديمة (dark/light)
            cls.set_dark(mode != "light")
            return True
        except Exception:
            cls.set_theme("dark_navy")
            return False

    @classmethod
    def apply_to_app(cls):
        """يطبّق الـ stylesheet الحالي على QApplication."""
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(cls.stylesheet())

    # ============================================
    # Stylesheet — DPI-friendly (pt)
    # ============================================
    @classmethod
    def stylesheet(cls):
        c = cls.COLORS
        return f"""
        /* ============ Global ============ */
        QWidget {{
            background-color: {c['bg']};
            color: {c['text']};
            font-family: "Segoe UI", "Tahoma", sans-serif;
            font-size: 10pt;
        }}

        QMainWindow, QDialog {{
            background-color: {c['bg']};
        }}

        /* ============ Header ============ */
        QFrame#header {{
            background-color: {c['surface']};
            border-bottom: 2px solid {c['primary']};
        }}

        QLabel#headerTitle {{
            color: {c['text']};
            font-size: 17pt;
            font-weight: bold;
            padding: 4px;
        }}

        QLabel#headerSubtitle {{
            color: {c['gold']};
            font-size: 8pt;
        }}

        QLabel#userInfo {{
            color: {c['text_muted']};
            font-size: 9pt;
        }}

        /* ============ Buttons ============ */
        QPushButton {{
            background-color: {c['primary']};
            color: #ffffff;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 10pt;
            font-weight: bold;
            min-height: 18px;
        }}
        QPushButton:hover {{
            background-color: {c['primary_hover']};
        }}
        QPushButton:pressed {{
            background-color: {c['primary_dark']};
        }}
        QPushButton:disabled {{
            background-color: {c['border']};
            color: {c['text_dim']};
        }}

        QPushButton#success {{
            background-color: {c['success']};
        }}
        QPushButton#success:hover {{
            background-color: {c['success_hover']};
        }}

        QPushButton#danger {{
            background-color: {c['danger']};
        }}
        QPushButton#danger:hover {{
            background-color: {c['danger_hover']};
        }}

        QPushButton#warning {{
            background-color: {c['warning']};
        }}
        QPushButton#warning:hover {{
            background-color: {c['warning_hover']};
        }}

        QPushButton#info {{
            background-color: {c['info']};
        }}
        QPushButton#info:hover {{
            background-color: {c['info_hover']};
        }}

        QPushButton#ghost {{
            background-color: transparent;
            border: 1px solid {c['border_strong']};
            color: {c['text']};
        }}
        QPushButton#ghost:hover {{
            background-color: {c['surface_alt']};
        }}

        /* ============ Inputs ============ */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {c['surface']};
            color: {c['text']};
            border: 1px solid {c['border_strong']};
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 10pt;
            selection-background-color: {c['primary']};
            selection-color: #ffffff;
        }}
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border: 2px solid {c['primary']};
        }}
        QLineEdit:disabled {{
            background-color: {c['bg_alt']};
            color: {c['text_dim']};
        }}

        QComboBox {{
            background-color: {c['surface']};
            color: {c['text']};
            border: 1px solid {c['border_strong']};
            border-radius: 6px;
            padding: 6px 12px;
            min-height: 20px;
            font-size: 10pt;
        }}
        QComboBox:focus {{
            border: 2px solid {c['primary']};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 6px solid {c['text_muted']};
            margin-right: 6px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {c['surface']};
            color: {c['text']};
            border: 1px solid {c['border_strong']};
            selection-background-color: {c['primary']};
            selection-color: #ffffff;
            padding: 4px;
            outline: none;
        }}

        /* ============ Tables ============ */
        QTableWidget, QTableView {{
            background-color: {c['surface']};
            alternate-background-color: {c['row_alt']};
            color: {c['text']};
            border: 1px solid {c['border']};
            border-radius: 6px;
            gridline-color: {c['border']};
            selection-background-color: {c['primary']};
            selection-color: #ffffff;
            font-size: 10pt;
            outline: none;
        }}
        QTableWidget::item {{
            padding: 6px;
            border: none;
        }}
        QTableWidget::item:selected {{
            background-color: {c['primary']};
            color: #ffffff;
        }}

        QHeaderView::section {{
            background-color: {c['surface_alt']};
            color: {c['text']};
            padding: 10px 6px;
            border: none;
            border-bottom: 2px solid {c['primary']};
            font-size: 10pt;
            font-weight: bold;
        }}
        QHeaderView::section:hover {{
            background-color: {c['border_strong']};
        }}

        QTableCornerButton::section {{
            background-color: {c['surface_alt']};
            border: none;
        }}

        /* ============ Tabs ============ */
        QTabWidget::pane {{
            background-color: {c['bg']};
            border: 1px solid {c['border']};
            border-radius: 6px;
            top: -1px;
        }}
        QTabBar {{
            qproperty-drawBase: 0;
        }}
        QTabBar::tab {{
            background-color: {c['surface']};
            color: {c['text_muted']};
            border: 1px solid {c['border']};
            border-bottom: none;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            padding: 10px 20px;
            margin-right: 2px;
            font-size: 10pt;
            font-weight: bold;
            min-width: 80px;
        }}
        QTabBar::tab:hover {{
            background-color: {c['surface_alt']};
            color: {c['text']};
        }}
        QTabBar::tab:selected {{
            background-color: {c['primary']};
            color: #ffffff;
            border-color: {c['primary']};
        }}

        /* ============ Cards ============ */
        QFrame#card {{
            background-color: {c['surface']};
            border: 1px solid {c['border']};
            border-radius: 10px;
        }}

        QLabel#cardTitle {{
            color: {c['text']};
            font-size: 12pt;
            font-weight: bold;
            padding: 4px;
        }}

        QLabel#sectionTitle {{
            color: {c['primary']};
            font-size: 14pt;
            font-weight: bold;
            padding: 4px;
        }}

        /* ============ Labels ============ */
        QLabel {{
            background-color: transparent;
            color: {c['text']};
        }}

        QLabel#muted {{
            color: {c['text_muted']};
        }}

        /* ============ Scrollbar ============ */
        QScrollBar:vertical {{
            background: {c['bg_alt']};
            width: 10px;
            border-radius: 5px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background: {c['border_strong']};
            border-radius: 5px;
            min-height: 24px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {c['primary']};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        QScrollBar:horizontal {{
            background: {c['bg_alt']};
            height: 10px;
            border-radius: 5px;
        }}
        QScrollBar::handle:horizontal {{
            background: {c['border_strong']};
            border-radius: 5px;
            min-width: 24px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {c['primary']};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}

        /* ============ Status bar ============ */
        QStatusBar {{
            background-color: {c['statusbar']};
            color: {c['text_muted']};
            border-top: 1px solid {c['border']};
            padding: 3px;
        }}

        /* ============ Message box ============ */
        QMessageBox {{
            background-color: {c['surface']};
        }}
        QMessageBox QLabel {{
            color: {c['text']};
            font-size: 10pt;
        }}

        /* ============ Checkbox ============ */
        QCheckBox {{
            color: {c['text']};
            spacing: 6px;
        }}
        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border-radius: 3px;
            border: 2px solid {c['border_strong']};
            background-color: {c['surface']};
        }}
        QCheckBox::indicator:hover {{
            border-color: {c['primary']};
        }}
        QCheckBox::indicator:checked {{
            background-color: {c['primary']};
            border-color: {c['primary']};
        }}

        /* ============ Radio ============ */
        QRadioButton {{
            color: {c['text']};
            spacing: 6px;
        }}
        QRadioButton::indicator {{
            width: 16px;
            height: 16px;
            border-radius: 8px;
            border: 2px solid {c['border_strong']};
            background-color: {c['surface']};
        }}
        QRadioButton::indicator:checked {{
            background-color: {c['primary']};
            border-color: {c['primary']};
        }}

        /* ============ Tooltip ============ */
        QToolTip {{
            background-color: {c['surface_alt']};
            color: {c['text']};
            border: 1px solid {c['primary']};
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 9pt;
        }}
        """