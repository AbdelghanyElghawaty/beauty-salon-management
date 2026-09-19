"""
Settings Tab — الإعدادات.
+ Light/Dark theme support (reads from Theme).

3 تابات داخلية:
- 🏪 الإعدادات العامة (اسم الصالون، التليفون، العنوان، العملة)
- 💾 النسخ الاحتياطي (عرض، إنشاء، استعادة، حذف)
- 🎨 المظهر (6 ثيمات + صورة خلفية)
"""

import os
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QAbstractItemView, QTabWidget,
    QLineEdit, QSizePolicy, QFileDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPixmap

from theme import Theme


# ============================================================
# ClickableFrame — QFrame قابل للضغط
# ============================================================
class ClickableFrame(QFrame):
    """QFrame بيستقبل click زي QPushButton."""

    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


# ============================================================
# Settings Tab
# ============================================================
class SettingsTab(QWidget):
    """تاب الإعدادات — 3 أقسام داخلية."""

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

        header = QHBoxLayout()
        title = QLabel("⚙️  الإعدادات")
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
                padding: 16px;
            }}
            QTabBar::tab {{
                background-color: {Theme.color('surface')};
                color: {Theme.color('text_muted')};
                padding: 10px 22px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 12px;
                font-weight: bold;
                min-width: 140px;
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

        self.tab_general = self._build_general_tab()
        self.sub_tabs.addTab(self.tab_general, "  🏪  الإعدادات العامة  ")

        self.tab_backup = self._build_backup_tab()
        self.sub_tabs.addTab(self.tab_backup, "  💾  النسخ الاحتياطي  ")

        self.tab_theme = self._build_theme_tab()
        self.sub_tabs.addTab(self.tab_theme, "  🎨  المظهر  ")

        layout.addWidget(self.sub_tabs, stretch=1)

    # ============================================
    # Tab 1: General
    # ============================================
    def _build_general_tab(self):
        widget = QWidget()
        w_layout = QVBoxLayout(widget)
        w_layout.setContentsMargins(4, 4, 4, 4)
        w_layout.setSpacing(14)

        desc = QLabel(
            "دي البيانات الأساسية للصالون. هتظهر في الهيدر والإيصالات المطبوعة."
        )
        desc.setStyleSheet(
            f"color: {Theme.color('text_muted')}; font-size: 11px; "
            f"background: transparent; padding: 4px;"
        )
        desc.setWordWrap(True)
        w_layout.addWidget(desc)

        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background-color: {Theme.color('surface')}; "
            f"border: 1px solid {Theme.color('border')}; border-radius: 12px; }}"
        )
        form = QGridLayout(card)
        form.setContentsMargins(24, 20, 24, 20)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(14)

        form.addWidget(self._lbl("🏪  اسم الصالون *"), 0, 0)
        self.shop_name_entry = QLineEdit()
        self.shop_name_entry.setMinimumHeight(44)
        self.shop_name_entry.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.shop_name_entry.setPlaceholderText("مثال: صالون النخبة")
        form.addWidget(self.shop_name_entry, 0, 1, 1, 2)

        form.addWidget(self._lbl("📞  رقم التليفون"), 1, 0)
        self.shop_phone_entry = QLineEdit()
        self.shop_phone_entry.setMinimumHeight(44)
        self.shop_phone_entry.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.shop_phone_entry.setPlaceholderText("مثال: 01012345678")
        form.addWidget(self.shop_phone_entry, 1, 1, 1, 2)

        form.addWidget(self._lbl("📍  العنوان"), 2, 0)
        self.shop_address_entry = QLineEdit()
        self.shop_address_entry.setMinimumHeight(44)
        self.shop_address_entry.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.shop_address_entry.setPlaceholderText("مثال: شارع الجمهورية، المنصورة")
        form.addWidget(self.shop_address_entry, 2, 1, 1, 2)

        form.addWidget(self._lbl("💱  رمز العملة"), 3, 0)
        self.currency_entry = QLineEdit()
        self.currency_entry.setMinimumHeight(44)
        self.currency_entry.setMaximumWidth(160)
        self.currency_entry.setAlignment(Qt.AlignCenter)
        self.currency_entry.setPlaceholderText("ج.م")
        form.addWidget(self.currency_entry, 3, 1)

        form.setColumnStretch(1, 1)
        form.setColumnStretch(2, 1)

        w_layout.addWidget(card)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        save_btn = QPushButton("💾  حفظ الإعدادات")
        save_btn.setMinimumHeight(46)
        save_btn.setMinimumWidth(220)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('success')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"font-weight: bold; font-size: 13px; padding: 10px 20px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('success_hover')}; }}"
        )
        save_btn.clicked.connect(self._save_general)
        btn_row.addWidget(save_btn)

        w_layout.addLayout(btn_row)
        w_layout.addStretch(1)

        return widget

    def _lbl(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {Theme.color('text')}; font-size: 12px; "
            f"font-weight: bold; background: transparent; padding: 0 4px;"
        )
        return lbl

    # ============================================
    # Tab 2: Backup
    # ============================================
    def _build_backup_tab(self):
        widget = QWidget()
        w_layout = QVBoxLayout(widget)
        w_layout.setContentsMargins(4, 4, 4, 4)
        w_layout.setSpacing(14)

        desc = QLabel(
            "النسخ الاحتياطية بتتحفظ تلقائيًا عند كل تسجيل خروج/إغلاق للبرنامج.\n"
            "تقدر كمان تعمل نسخة يدوية في أي وقت."
        )
        desc.setStyleSheet(
            f"color: {Theme.color('text_muted')}; font-size: 11px; "
            f"background: transparent; padding: 4px;"
        )
        desc.setWordWrap(True)
        w_layout.addWidget(desc)

        actions = QHBoxLayout()
        actions.setSpacing(10)

        create_btn = QPushButton("➕  إنشاء نسخة الآن")
        create_btn.setMinimumHeight(44)
        create_btn.setCursor(Qt.PointingHandCursor)
        create_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('success')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"font-weight: bold; font-size: 12px; padding: 10px 20px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('success_hover')}; }}"
        )
        create_btn.clicked.connect(self._create_backup)
        actions.addWidget(create_btn)

        restore_btn = QPushButton("♻️  استعادة المختار")
        restore_btn.setMinimumHeight(44)
        restore_btn.setCursor(Qt.PointingHandCursor)
        restore_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('warning')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"font-weight: bold; font-size: 12px; padding: 10px 20px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('warning_hover')}; }}"
        )
        restore_btn.clicked.connect(self._restore_backup)
        actions.addWidget(restore_btn)

        open_folder_btn = QPushButton("📂  فتح مجلد النسخ")
        open_folder_btn.setMinimumHeight(44)
        open_folder_btn.setCursor(Qt.PointingHandCursor)
        open_folder_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('primary')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"font-weight: bold; font-size: 12px; padding: 10px 20px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('primary_hover')}; }}"
        )
        open_folder_btn.clicked.connect(self._open_backups_folder)
        actions.addWidget(open_folder_btn)

        actions.addStretch()
        w_layout.addLayout(actions)

        self.backup_table = QTableWidget()
        self.backup_table.setColumnCount(5)
        self.backup_table.setHorizontalHeaderLabels(
            ["#", "التاريخ", "الحجم", "المسار", ""]
        )
        self.backup_table.verticalHeader().setVisible(False)
        self.backup_table.setAlternatingRowColors(True)
        self.backup_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.backup_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.backup_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.backup_table.setShowGrid(False)
        self.backup_table.setMinimumHeight(300)
        self.backup_table.setLayoutDirection(Qt.RightToLeft)

        h = self.backup_table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Fixed)
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        h.setSectionResizeMode(2, QHeaderView.Fixed)
        h.setSectionResizeMode(3, QHeaderView.Stretch)
        h.setSectionResizeMode(4, QHeaderView.Fixed)

        self.backup_table.setColumnWidth(0, 50)
        self.backup_table.setColumnWidth(2, 100)
        self.backup_table.setColumnWidth(4, 60)

        w_layout.addWidget(self.backup_table, stretch=1)

        return widget

    # ============================================
    # Tab 3: Theme — 6 ثيمات + صورة خلفية
    # ============================================
    def _build_theme_tab(self):
        widget = QWidget()

        # ✅ ScrollArea عشان المحتوى كبير
        from PySide6.QtWidgets import QScrollArea
        outer = QVBoxLayout(widget)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
        )

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        w_layout = QVBoxLayout(content)
        w_layout.setContentsMargins(4, 4, 4, 4)
        w_layout.setSpacing(14)

        desc = QLabel(
            "اختار الثيم اللي يريحك + خلفية شاشة الدخول."
        )
        desc.setStyleSheet(
            f"color: {Theme.color('text_muted')}; font-size: 11px; "
            f"background: transparent; padding: 4px;"
        )
        desc.setWordWrap(True)
        w_layout.addWidget(desc)

        # ============================================
        # 6 بطاقات ثيمات
        # ============================================
        self.theme_cards = {}

        themes_config = [
            ("dark_navy",   "🌙", "Dark Navy",   "أزرق داكن",    "#0f172a", "#3b82f6", "#f1f5f9"),
            ("dark_purple", "🖤", "Dark Purple", "بنفسجي داكن",  "#1a0f2e", "#a855f7", "#f5f3ff"),
            ("light_clean", "☀️", "Light Clean", "فاتح نظيف",    "#f8fafc", "#3b82f6", "#0f172a"),
            ("nord",        "❄️", "Nord",        "رمادي أزرق",   "#2e3440", "#88c0d0", "#eceff4"),
            ("sunset",      "🌅", "Sunset",      "برتقالي دافئ", "#1c1917", "#f97316", "#fafaf9"),
            ("forest",      "🌲", "Forest",      "أخضر طبيعي",   "#0f1f14", "#22c55e", "#dcfce7"),
        ]

        row1 = QHBoxLayout()
        row1.setSpacing(14)
        for cfg in themes_config[:3]:
            card = self._make_theme_card(*cfg)
            self.theme_cards[cfg[0]] = card
            row1.addWidget(card, 1)
        w_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(14)
        for cfg in themes_config[3:]:
            card = self._make_theme_card(*cfg)
            self.theme_cards[cfg[0]] = card
            row2.addWidget(card, 1)
        w_layout.addLayout(row2)

        # ============================================
        # قسم صورة الخلفية
        # ============================================
        w_layout.addSpacing(20)

        sep_bg = QFrame()
        sep_bg.setFrameShape(QFrame.HLine)
        sep_bg.setStyleSheet(
            f"color: {Theme.color('border')}; "
            f"background: {Theme.color('border')}; max-height: 1px;"
        )
        w_layout.addWidget(sep_bg)

        bg_title = QLabel("🖼  خلفية شاشة الدخول")
        bg_title.setStyleSheet(
            f"font-size: 14px; font-weight: bold; "
            f"color: {Theme.color('primary')}; padding: 8px 4px; "
            f"background: transparent;"
        )
        w_layout.addWidget(bg_title)

        bg_desc = QLabel(
            "اختار صورة خلفية تظهر خلف شاشة تسجيل الدخول "
            "(بتعتيم 60% عشان النص يبقى واضح)."
        )
        bg_desc.setStyleSheet(
            f"color: {Theme.color('text_muted')}; font-size: 11px; "
            f"padding: 0 4px 8px 4px; background: transparent;"
        )
        bg_desc.setWordWrap(True)
        w_layout.addWidget(bg_desc)

        bg_card = QFrame()
        bg_card.setStyleSheet(
            f"QFrame {{ background-color: {Theme.color('surface')}; "
            f"border: 1px solid {Theme.color('border')}; border-radius: 10px; }}"
        )
        bg_layout = QHBoxLayout(bg_card)
        bg_layout.setContentsMargins(16, 14, 16, 14)
        bg_layout.setSpacing(10)

        self.bg_static_label = QLabel("لم يتم اختيار صورة")
        self.bg_static_label.setStyleSheet(
            f"color: {Theme.color('text_muted')}; font-size: 10pt; "
            f"padding: 6px; background: transparent;"
        )
        self.bg_static_label.setWordWrap(True)
        bg_layout.addWidget(self.bg_static_label, 1)

        pick_static_btn = QPushButton("📁  اختيار صورة")
        pick_static_btn.setMinimumHeight(40)
        pick_static_btn.setCursor(Qt.PointingHandCursor)
        pick_static_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('primary')}; "
            f"color: white; border: none; border-radius: 6px; "
            f"font-weight: bold; font-size: 11px; padding: 6px 14px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('primary_hover')}; }}"
        )
        pick_static_btn.clicked.connect(self._pick_bg_static)
        bg_layout.addWidget(pick_static_btn)

        clear_static_btn = QPushButton("🗑")
        clear_static_btn.setFixedSize(40, 40)
        clear_static_btn.setCursor(Qt.PointingHandCursor)
        clear_static_btn.setToolTip("حذف الصورة")
        clear_static_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('danger')}; "
            f"color: white; border: none; border-radius: 6px; font-size: 14px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('danger_hover')}; }}"
        )
        clear_static_btn.clicked.connect(self._clear_bg_static)
        bg_layout.addWidget(clear_static_btn)

        w_layout.addWidget(bg_card)

        w_layout.addStretch(1)

        scroll.setWidget(content)
        outer.addWidget(scroll)

        self._refresh_theme_cards()
        self._load_bg_settings()
        return widget

    def _make_theme_card(self, key, icon, title, subtitle,
                         bg_color, accent_color, text_color):
        """يبني بطاقة ثيم كـ QFrame قابل للضغط."""
        card = ClickableFrame()
        card.setFixedHeight(170)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        card.setCursor(Qt.PointingHandCursor)
        card.setProperty("theme_key", key)
        card.setProperty("bg_color", bg_color)
        card.setProperty("accent_color", accent_color)
        card.setProperty("text_color", text_color)
        card.clicked.connect(lambda k=key: self._change_theme(k))

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignCenter)

        icon_lbl = QLabel(icon)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        icon_lbl.setStyleSheet(
            "font-size: 38px; background: transparent; border: none;"
        )
        layout.addWidget(icon_lbl)

        title_lbl = QLabel(title)
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        title_lbl.setStyleSheet(
            f"font-size: 15px; font-weight: bold; "
            f"color: {text_color}; background: transparent; border: none;"
        )
        layout.addWidget(title_lbl)

        subtitle_lbl = QLabel(subtitle)
        subtitle_lbl.setAlignment(Qt.AlignCenter)
        subtitle_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        subtitle_lbl.setStyleSheet(
            f"font-size: 10px; color: {text_color}cc; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(subtitle_lbl)

        preview = QHBoxLayout()
        preview.setSpacing(6)
        preview.setAlignment(Qt.AlignCenter)
        preview.addStretch()

        for color in [accent_color, bg_color]:
            dot = QLabel()
            dot.setFixedSize(22, 22)
            dot.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            dot.setStyleSheet(
                f"background-color: {color}; "
                f"border-radius: 11px; "
                f"border: 2px solid {text_color}44;"
            )
            preview.addWidget(dot)

        preview.addStretch()
        layout.addLayout(preview)

        return card

    def _refresh_theme_cards(self):
        """يحدّث شكل البطاقات حسب الثيم الحالي."""
        current = Theme.current_name

        for key, card in self.theme_cards.items():
            bg = card.property("bg_color") or "#0f172a"
            accent = card.property("accent_color") or "#3b82f6"

            if key == current:
                card.setStyleSheet(
                    f"QFrame {{ "
                    f"background-color: {bg}; "
                    f"border: 3px solid {accent}; "
                    f"border-radius: 12px; "
                    f"}}"
                )
            else:
                card.setStyleSheet(
                    f"QFrame {{ "
                    f"background-color: {bg}; "
                    f"border: 2px solid #475569; "
                    f"border-radius: 12px; "
                    f"}}"
                )

    # ============================================
    # Background settings
    # ============================================
    def _load_bg_settings(self):
        """يحمّل إعدادات صورة الخلفية."""
        try:
            static_path = self.db.get_setting("login_bg_image", "") or ""
            if static_path and os.path.exists(static_path):
                self.bg_static_label.setText(
                    f"✅  {os.path.basename(static_path)}"
                )
                self.bg_static_label.setStyleSheet(
                    f"color: {Theme.color('success')}; font-size: 10pt; "
                    f"padding: 6px; background: transparent; "
                    f"font-weight: bold;"
                )
            else:
                self.bg_static_label.setText("لم يتم اختيار صورة")
                self.bg_static_label.setStyleSheet(
                    f"color: {Theme.color('text_muted')}; font-size: 10pt; "
                    f"padding: 6px; background: transparent;"
                )
        except Exception:
            pass

    def _pick_bg_static(self):
        """يختار صورة خلفية."""
        path, _ = QFileDialog.getOpenFileName(
            self, "اختار صورة خلفية", "",
            "الصور (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if not path:
            return
        try:
            self.db.set_setting("login_bg_image", path)
            self._load_bg_settings()
            QMessageBox.information(
                self, "تم",
                "✅ تم حفظ صورة الخلفية.\n\n"
                "هتظهر عند فتح شاشة الدخول في المرة الجاية."
            )
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل الحفظ:\n{e}")

    def _clear_bg_static(self):
        """يحذف صورة الخلفية."""
        try:
            self.db.set_setting("login_bg_image", "")
            self._load_bg_settings()
            QMessageBox.information(self, "تم", "✅ تم حذف صورة الخلفية.")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل الحذف:\n{e}")

    # ============================================
    # Refresh
    # ============================================
    def refresh(self):
        self._load_general()
        self._load_backups()
        self._refresh_theme_cards()
        self._load_bg_settings()

    def _load_general(self):
        try:
            self.shop_name_entry.setText(
                self.db.get_setting("shop_name", "صالون الحلاقة") or ""
            )
            self.shop_phone_entry.setText(
                self.db.get_setting("shop_phone", "") or ""
            )
            self.shop_address_entry.setText(
                self.db.get_setting("shop_address", "") or ""
            )
            self.currency_entry.setText(
                self.db.get_setting("currency", "ج.م") or ""
            )
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل الإعدادات:\n{e}")

    def _load_backups(self):
        try:
            backups = self.db.list_backups()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل النسخ:\n{e}")
            return

        self.backup_table.setRowCount(len(backups))
        gray = QColor(Theme.color("text_muted"))
        blue = QColor(Theme.color("primary"))
        text_color = QColor(Theme.color("text"))

        for row, path in enumerate(backups):
            filename = os.path.basename(path)

            display_date = filename
            try:
                base = filename.replace("barber_shop_", "").replace(".db", "")
                dt = datetime.strptime(base, "%Y-%m-%d_%H-%M-%S")
                display_date = dt.strftime("%Y-%m-%d  |  %I:%M:%S %p")
            except Exception:
                pass

            try:
                size_bytes = os.path.getsize(path)
                if size_bytes < 1024:
                    size_str = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    size_str = f"{size_bytes / 1024:.1f} KB"
                else:
                    size_str = f"{size_bytes / (1024 * 1024):.2f} MB"
            except Exception:
                size_str = "—"

            i0 = QTableWidgetItem(str(row + 1))
            i0.setTextAlignment(Qt.AlignCenter)
            i0.setData(Qt.UserRole, path)
            i0.setForeground(text_color)
            self.backup_table.setItem(row, 0, i0)

            i1 = QTableWidgetItem(display_date)
            i1.setTextAlignment(Qt.AlignCenter)
            i1.setForeground(text_color)
            self.backup_table.setItem(row, 1, i1)

            i2 = QTableWidgetItem(size_str)
            i2.setTextAlignment(Qt.AlignCenter)
            i2.setForeground(blue)
            self.backup_table.setItem(row, 2, i2)

            i3 = QTableWidgetItem(filename)
            i3.setTextAlignment(Qt.AlignCenter)
            i3.setForeground(gray)
            self.backup_table.setItem(row, 3, i3)

            del_btn = QPushButton("🗑️")
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setStyleSheet(
                f"QPushButton {{ background-color: {Theme.color('danger')}; "
                f"color: white; border: none; border-radius: 6px; "
                f"font-size: 14px; }}"
                f"QPushButton:hover {{ background-color: {Theme.color('danger_hover')}; }}"
            )
            del_btn.clicked.connect(
                lambda _, p=path: self._delete_backup(p)
            )
            self.backup_table.setCellWidget(row, 4, del_btn)

    # ============================================
    # Actions — General
    # ============================================
    def _save_general(self):
        shop_name = self.shop_name_entry.text().strip()
        if not shop_name:
            QMessageBox.warning(self, "خطأ", "اسم الصالون مطلوب")
            return

        try:
            self.db.set_many_settings({
                "shop_name": shop_name,
                "shop_phone": self.shop_phone_entry.text().strip(),
                "shop_address": self.shop_address_entry.text().strip(),
                "currency": self.currency_entry.text().strip() or "ج.م",
            })
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل الحفظ:\n{e}")
            return

        QMessageBox.information(
            self, "تم",
            "تم حفظ الإعدادات.\n\n"
            "ℹ️  اسم الصالون الجديد هيظهر بعد إعادة تسجيل الدخول."
        )

    # ============================================
    # Actions — Backup
    # ============================================
    def _create_backup(self):
        try:
            path = self.db.backup_now()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل إنشاء النسخة:\n{e}")
            return

        QMessageBox.information(
            self, "تم",
            f"تم إنشاء النسخة:\n{os.path.basename(path)}"
        )
        self._load_backups()

    def _get_selected_backup(self):
        rows = self.backup_table.selectionModel().selectedRows()
        if not rows:
            return None
        row_idx = rows[0].row()
        item = self.backup_table.item(row_idx, 0)
        if item is None:
            return None
        return item.data(Qt.UserRole)

    def _restore_backup(self):
        path = self._get_selected_backup()
        if not path:
            QMessageBox.warning(self, "خطأ", "اختار نسخة من الجدول الأول")
            return

        filename = os.path.basename(path)

        reply = QMessageBox.warning(
            self, "⚠️ تأكيد الاستعادة",
            f"⚠️ تحذير مهم!\n\n"
            f"هتستعيد النسخة:\n{filename}\n\n"
            f"ده هيمسح كل البيانات الحالية ويرجعها للنسخة دي!\n"
            f"العملية مش قابلة للتراجع.\n\n"
            f"متأكد إنك عايز تكمل؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        try:
            self.db.restore_backup(path)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل الاستعادة:\n{e}")
            return

        QMessageBox.information(
            self, "تم",
            "✅ تم استعادة النسخة بنجاح.\n\n"
            "⚠️  لازم تقفل البرنامج وتفتحه تاني عشان التغييرات تظهر."
        )

    def _delete_backup(self, path):
        if not path:
            return
        filename = os.path.basename(path)

        reply = QMessageBox.question(
            self, "تأكيد الحذف",
            f"متأكد إنك عايز تحذف النسخة دي؟\n\n{filename}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        try:
            os.remove(path)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل الحذف:\n{e}")
            return

        QMessageBox.information(self, "تم", "تم حذف النسخة.")
        self._load_backups()

    def _open_backups_folder(self):
        backups_dir = os.path.join(self.db.base_dir, "backups")
        os.makedirs(backups_dir, exist_ok=True)
        try:
            if os.name == "nt":
                os.startfile(backups_dir)
            else:
                import subprocess
                subprocess.Popen(["xdg-open", backups_dir])
        except Exception:
            QMessageBox.information(
                self, "المسار",
                f"مجلد النسخ:\n{backups_dir}"
            )

    # ============================================
    # Actions — Theme
    # ============================================
    def _change_theme(self, mode):
        if mode == Theme.current_name:
            return

        try:
            self.db.set_setting("theme", mode)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل حفظ الثيم:\n{e}")
            return

        Theme.set_theme(mode)
        Theme.apply_to_app()
        self._refresh_theme_cards()

        try:
            main_window = self.window()
            if main_window and hasattr(main_window, "refresh_header"):
                main_window.refresh_header()
        except Exception:
            pass