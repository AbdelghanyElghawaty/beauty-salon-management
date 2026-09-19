"""
Login Extras — أدوات وميزات إضافية لشاشة الدخول.
================================================
يجمع:
- Sounds (winsound.Beep)
- Hijri date
- QR Code generation
- Image to base64 (data URI)
- Password strength
- Translations (ar/en)
- Stats Preview (اليوم)
- Employee of the Month
- Employee Badge (HTML + QR Code)
"""

import os
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QTextEdit
)
from PySide6.QtCore import Qt

from theme import Theme


# ============================================================
# 1) الأصوات — Sounds
# ============================================================
def play_sound(kind="click"):
    """
    يشغّل صوت بسيط باستخدام winsound.Beep.

    الأنواع المتاحة:
    - click    : نقرة خفيفة
    - success  : نجاح (نغمة صاعدة)
    - error    : خطأ (نغمة هابطة)
    - warning  : تحذير
    - lock     : قفل الحساب
    - guest    : دخول ضيف
    - typing   : كتابة (خفيف جدًا)
    """
    try:
        import winsound
        sounds = {
            "click":   [(1000, 25)],
            "success": [(700, 60), (900, 60), (1200, 100)],
            "error":   [(500, 100), (300, 160)],
            "warning": [(600, 90)],
            "lock":    [(400, 200), (250, 250)],
            "guest":   [(500, 60), (800, 80), (1000, 60)],
            "typing":  [(1500, 8)],
        }
        for freq, dur in sounds.get(kind, [(1000, 30)]):
            try:
                winsound.Beep(freq, dur)
            except Exception:
                pass
    except Exception:
        pass


# ============================================================
# 2) التاريخ الهجري — Hijri Date
# ============================================================
HIJRI_MONTHS = [
    "محرم", "صفر", "ربيع الأول", "ربيع الآخر",
    "جمادى الأولى", "جمادى الآخرة", "رجب", "شعبان",
    "رمضان", "شوال", "ذو القعدة", "ذو الحجة",
]


def get_hijri_date():
    """
    يرجع التاريخ الهجري.
    - لو hijri-converter متثبتة → دقيق
    - لو مش متثبتة → حساب تقريبي
    """
    try:
        from hijri_converter import Gregorian
        g = datetime.now()
        h = Gregorian(g.year, g.month, g.day).to_hijri()
        return f"{h.day} {HIJRI_MONTHS[h.month - 1]} {h.year} هـ"
    except ImportError:
        pass
    except Exception:
        pass

    try:
        g = datetime.now()
        jd = int((g - datetime(622, 7, 16)).days * 1.030684)
        year = 622 + jd // 354
        month = ((jd % 354) // 29) + 1
        day = (jd % 29) + 1
        if 1 <= month <= 12:
            return f"{day} {HIJRI_MONTHS[month - 1]} {year} هـ"
    except Exception:
        pass

    return ""


# ============================================================
# 3) QR Code & Image to Data URI
# ============================================================
def generate_qr_data_uri(text):
    """يولّد QR Code كـ data URI (للاستخدام في HTML)."""
    try:
        import qrcode
        from io import BytesIO
        import base64

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=1,
        )
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_b64 = base64.b64encode(buffer.getvalue()).decode("ascii")
        return f"data:image/png;base64,{img_b64}"
    except Exception:
        return ""


def image_to_data_uri(image_path):
    """
    يحول أي صورة (ico/png/jpg) لـ data URI.
    يدعم .ico عن طريق PIL.
    """
    if not image_path or not os.path.exists(image_path):
        return None

    try:
        from PIL import Image
        from io import BytesIO
        import base64

        img = Image.open(image_path)
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        buf = BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/png;base64,{b64}"
    except Exception:
        pass

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


# ============================================================
# 4) Password Strength
# ============================================================
def password_strength(password):
    """
    يرجع (score, label, color).
    - score: 0-100
    - label: وصف بالعربي
    - color: hex color
    """
    if not password:
        return 0, "", "#94a3b8"

    score = 0
    if len(password) >= 6:
        score += 25
    if len(password) >= 10:
        score += 15
    if any(c.islower() for c in password):
        score += 15
    if any(c.isupper() for c in password):
        score += 15
    if any(c.isdigit() for c in password):
        score += 15
    if any(not c.isalnum() for c in password):
        score += 15

    if score < 40:
        return score, "ضعيف", "#ef4444"
    elif score < 70:
        return score, "متوسط", "#f59e0b"
    elif score < 90:
        return score, "قوي", "#10b981"
    else:
        return score, "قوي جداً 💪", "#10b981"


# ============================================================
# 5) الترجمات — Translations
# ============================================================
TRANSLATIONS = {
    "ar": {
        "title": "تسجيل الدخول",
        "username": "اسم المستخدم",
        "password": "كلمة المرور",
        "login": "دخول",
        "remember_me": "تذكرني",
        "forgot": "نسيت كلمة المرور؟",
        "guest": "🎭  دخول كضيف (تجريبي)",
        "footer": "© 2026 — جميع الحقوق محفوظة",
        "greeting_morning": "صباح الخير 🌅",
        "greeting_noon": "نهارك سعيد ☀️",
        "greeting_evening": "مساء الخير 🌆",
        "greeting_night": "سهرة سعيدة 🌙",
        "welcome_back": "أهلاً بك مجدداً",
        "welcome_new": "أهلاً بك",
        "last_login": "آخر دخول",
        "db_online": "متصل",
        "db_offline": "غير متصل",
        "err_empty": "من فضلك ادخل اسم المستخدم وكلمة المرور",
        "err_locked": "الحساب مقفول مؤقتاً",
        "err_try_after": "جرّب تاني بعد",
        "err_seconds": "ثانية",
        "err_user_not_found": "المستخدم مش موجود في النظام",
        "err_wrong_password": "كلمة المرور غير صحيحة",
        "err_remaining_attempts": "متبقي لك {n} محاولات",
        "today_stats": "اليوم",
        "bookings": "حجز",
        "revenue": "ج.م",
        "employee_of_month": "🏆 موظف الشهر",
        "print_badge": "🖨  بطاقة الموظف",
        "forgot_title": "نسيت كلمة المرور",
        "forgot_msg": (
            "🔑  استعادة كلمة المرور\n\n"
            "لو نسيت كلمة المرور، تواصل مع المسؤول:\n\n"
            "👤  المسؤول: admin\n"
            "📞  التليفون: {phone}\n\n"
            "💡  ملاحظة:\n"
            "المسؤول فقط هو اللي يقدر يعيد تعيين كلمة المرور\n"
            "من خلال تاب «المستخدمين»."
        ),
    },
    "en": {
        "title": "Login",
        "username": "Username",
        "password": "Password",
        "login": "Login",
        "remember_me": "Remember me",
        "forgot": "Forgot password?",
        "guest": "🎭  Guest login (Demo)",
        "footer": "© 2026 — All rights reserved",
        "greeting_morning": "Good morning 🌅",
        "greeting_noon": "Good afternoon ☀️",
        "greeting_evening": "Good evening 🌆",
        "greeting_night": "Good night 🌙",
        "welcome_back": "Welcome back",
        "welcome_new": "Welcome",
        "last_login": "Last login",
        "db_online": "Online",
        "db_offline": "Offline",
        "err_empty": "Please enter username and password",
        "err_locked": "Account temporarily locked",
        "err_try_after": "Try again after",
        "err_seconds": "seconds",
        "err_user_not_found": "User not found",
        "err_wrong_password": "Incorrect password",
        "err_remaining_attempts": "{n} attempts remaining",
        "today_stats": "Today",
        "bookings": "bookings",
        "revenue": "EGP",
        "employee_of_month": "🏆 Employee of Month",
        "print_badge": "🖨  Employee Badge",
        "forgot_title": "Forgot Password",
        "forgot_msg": (
            "🔑  Password Recovery\n\n"
            "If you forgot your password, contact the admin:\n\n"
            "👤  Admin: admin\n"
            "📞  Phone: {phone}\n\n"
            "💡  Note:\n"
            "Only admin can reset passwords\n"
            "from the «Users» tab."
        ),
    },
}


def translate(lang, key, **kwargs):
    """يرجع النص المترجم مع دعم الكلمات المتغيرة."""
    text = TRANSLATIONS.get(lang, TRANSLATIONS["ar"]).get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except Exception:
            pass
    return text


# ============================================================
# 6) Stats Preview — إحصائيات اليوم
# ============================================================
def get_today_stats(db):
    """
    يرجع dict فيه:
    - bookings: عدد الحجوزات اليوم
    - revenue: إجمالي الإيرادات اليوم
    - customers: عدد العملاء الفريدين اليوم
    """
    result = {"bookings": 0, "revenue": 0, "customers": 0}
    try:
        bookings = db.list_bookings()
        today = datetime.now().strftime("%Y-%m-%d")

        today_bookings = [b for b in bookings if b[5] == today]

        revenue = 0
        customers_set = set()

        for b in today_bookings:
            try:
                price = (b[3] or 0) + (b[8] or 0)
                revenue += price
                customers_set.add(b[1])
            except Exception:
                continue

        result["bookings"] = len(today_bookings)
        result["revenue"] = revenue
        result["customers"] = len(customers_set)
    except Exception:
        pass

    return result


def format_stats_text(stats, lang="ar"):
    """يرجع نص الإحصائيات منسّق."""
    if lang == "ar":
        return (
            f"📊  إحصائيات اليوم\n\n"
            f"📅  الحجوزات:  {stats['bookings']}\n"
            f"💰  الإيرادات:  {stats['revenue']:,.0f} ج.م\n"
            f"👥  العملاء:   {stats['customers']}"
        )
    else:
        return (
            f"📊  Today's Stats\n\n"
            f"📅  Bookings:  {stats['bookings']}\n"
            f"💰  Revenue:   {stats['revenue']:,.0f} EGP\n"
            f"👥  Customers: {stats['customers']}"
        )


# ============================================================
# 7) Employee of the Month
# ============================================================
def get_employee_of_month(db):
    """يرجع dict فيه بيانات موظف الشهر."""
    try:
        bookings = db.list_bookings()
        now = datetime.now()
        month_start = now.replace(day=1).strftime("%Y-%m-%d")

        data = {}

        for b in bookings:
            try:
                barber = (b[4] or "").strip() or "غير محدد"
                date = b[5]
                price = (b[3] or 0) + (b[8] or 0)

                if date >= month_start:
                    if barber not in data:
                        data[barber] = {"revenue": 0, "bookings": 0}
                    data[barber]["revenue"] += price
                    data[barber]["bookings"] += 1
            except Exception:
                continue

        if not data:
            return None

        best_name = max(data.items(), key=lambda x: x[1]["revenue"])[0]

        return {
            "name": best_name,
            "revenue": data[best_name]["revenue"],
            "bookings": data[best_name]["bookings"],
        }
    except Exception:
        return None


def format_employee_of_month_text(emp, lang="ar"):
    """يرجع نص موظف الشهر."""
    if not emp:
        if lang == "ar":
            return "🏆  موظف الشهر\n\nلا توجد بيانات هذا الشهر بعد."
        else:
            return "🏆  Employee of Month\n\nNo data available yet."

    month_name = datetime.now().strftime("%B")
    if lang == "ar":
        month_names_ar = {
            1: "يناير", 2: "فبراير", 3: "مارس", 4: "أبريل",
            5: "مايو", 6: "يونيو", 7: "يوليو", 8: "أغسطس",
            9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر",
        }
        month_name = month_names_ar[datetime.now().month]

        return (
            f"🏆  موظف الشهر ({month_name})\n\n"
            f"👨‍💼  الاسم: {emp['name']}\n"
            f"💰  الإيرادات: {emp['revenue']:,.0f} ج.م\n"
            f"📅  الحجوزات: {emp['bookings']}"
        )
    else:
        return (
            f"🏆  Employee of Month ({month_name})\n\n"
            f"👨‍💼  Name: {emp['name']}\n"
            f"💰  Revenue: {emp['revenue']:,.0f} EGP\n"
            f"📅  Bookings: {emp['bookings']}"
        )


# ============================================================
# 8) Employee Badge — بطاقة الموظف
# ============================================================
class EmployeeBadgeDialog(QDialog):
    """نافذة عرض بطاقة الموظف مع QR Code."""

    def __init__(self, parent=None, db=None, user=None, lang="ar"):
        super().__init__(parent)
        self.db = db
        self.user = user
        self.lang = lang

        self.setWindowTitle("🪪  بطاقة الموظف")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumSize(600, 780)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("🪪  بطاقة الموظف")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"font-size: 20px; font-weight: bold; "
            f"color: {Theme.color('primary')}; background: transparent;"
        )
        layout.addWidget(title)

        preview = QTextEdit()
        preview.setReadOnly(True)
        preview.setHtml(self._build_badge_html())
        preview.setStyleSheet(
            "QTextEdit { background-color: #ffffff; "
            "border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px; }"
        )
        layout.addWidget(preview, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        print_btn = QPushButton("🖨  طباعة البطاقة")
        print_btn.setMinimumHeight(46)
        print_btn.setMinimumWidth(200)
        print_btn.setCursor(Qt.PointingHandCursor)
        print_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('success')}; "
            f"color: white; border: none; border-radius: 8px; "
            f"font-weight: bold; font-size: 13px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('success_hover')}; }}"
        )
        print_btn.clicked.connect(self._print_badge)
        btn_row.addWidget(print_btn)

        close_btn = QPushButton("إغلاق")
        close_btn.setMinimumHeight(46)
        close_btn.setMinimumWidth(140)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(
            f"QPushButton {{ background-color: {Theme.color('surface_alt')}; "
            f"color: {Theme.color('text')}; border: none; border-radius: 8px; "
            f"font-weight: bold; font-size: 13px; }}"
            f"QPushButton:hover {{ background-color: {Theme.color('border_strong')}; }}"
        )
        close_btn.clicked.connect(self.reject)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

    def _build_badge_html(self):
        """يبني HTML للبطاقة."""
        try:
            shop_name = self.db.get_setting("shop_name", "صالون الحلاقة") or "صالون الحلاقة"
            shop_phone = self.db.get_setting("shop_phone", "") or ""
            shop_address = self.db.get_setting("shop_address", "") or ""
            shop_logo = self.db.get_setting("shop_logo", "") or ""
            color = self.db.get_setting("receipt_color", "#3b82f6") or "#3b82f6"
        except Exception:
            shop_name = "صالون الحلاقة"
            shop_phone = ""
            shop_address = ""
            shop_logo = ""
            color = "#3b82f6"

        logo_uri = None
        if shop_logo and os.path.exists(shop_logo):
            logo_uri = image_to_data_uri(shop_logo)

        if not logo_uri:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            for name in (
                "beauty-salon.ico", "beauty-salon.png",
                "haircut.ico", "haircut.png"
            ):
                p = os.path.join(base_dir, name)
                if os.path.exists(p):
                    logo_uri = image_to_data_uri(p)
                    break

        if logo_uri:
            logo_html = (
                f'<img src="{logo_uri}" '
                f'style="width: 110px; height: 110px; border-radius: 50%; '
                f'object-fit: cover; border: 4px solid #ffffff; '
                f'box-shadow: 0 4px 16px rgba(0,0,0,0.25);" />'
            )
        else:
            logo_html = '<div style="font-size: 64px;">💈</div>'

        qr_text = (
            f"Barber Shop Employee Badge\n"
            f"Name: {self.user.username}\n"
            f"Role: {self.user.role}\n"
            f"Shop: {shop_name}\n"
            f"Issued: {datetime.now().strftime('%Y-%m-%d')}"
        )
        qr_uri = generate_qr_data_uri(qr_text)

        qr_html = ""
        if qr_uri:
            qr_html = (
                '<div style="text-align: center; margin-top: 18px;">'
                f'<img src="{qr_uri}" style="width: 140px; height: 140px; '
                f'border: 2px solid #e2e8f0; border-radius: 12px; padding: 6px; '
                f'background: #ffffff;" />'
                '<div style="font-size: 10px; color: #94a3b8; margin-top: 6px;">'
                'امسح الكود للتحقق'
                '</div>'
                '</div>'
            )

        role_text = "سوبر أدمن" if self.user.is_admin else "موظف"
        today = datetime.now().strftime("%Y-%m-%d")

        try:
            bookings = self.db.list_bookings()
            my_bookings = [
                b for b in bookings
                if (b[4] or "").strip() == self.user.username
            ]
            total_revenue = sum(
                (b[3] or 0) + (b[8] or 0) for b in my_bookings
            )
            total_bookings = len(my_bookings)
        except Exception:
            total_revenue = 0
            total_bookings = 0

        contact_lines = []
        if shop_phone:
            contact_lines.append(f"📞 {shop_phone}")
        if shop_address:
            contact_lines.append(f"📍 {shop_address}")
        contact_html = "<br/>".join(contact_lines)

        html = f"""
        <!DOCTYPE html>
        <html dir="rtl" lang="ar">
        <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Segoe UI', 'Tahoma', sans-serif;
                background: #f8fafc;
                padding: 20px;
                margin: 0;
            }}
            .badge {{
                max-width: 400px;
                margin: 0 auto;
                background: #ffffff;
                border-radius: 20px;
                overflow: hidden;
                box-shadow: 0 8px 32px rgba(0,0,0,0.15);
            }}
            .header {{
                background: linear-gradient(135deg, {color} 0%, {color}dd 100%);
                padding: 30px 24px;
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
            .shop-name {{
                font-size: 22px;
                font-weight: bold;
                margin-top: 12px;
                position: relative;
                z-index: 2;
            }}
            .shop-info {{
                font-size: 11px;
                margin-top: 6px;
                opacity: 0.95;
                position: relative;
                z-index: 2;
            }}
            .badge-title {{
                background: #ffffff;
                color: {color};
                font-size: 14px;
                font-weight: bold;
                padding: 12px 24px;
                text-align: center;
                border-bottom: 2px dashed #e2e8f0;
            }}
            .info {{
                padding: 24px;
            }}
            .info-row {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 12px 0;
                border-bottom: 1px solid #f1f5f9;
            }}
            .info-row:last-child {{
                border-bottom: none;
            }}
            .label {{
                color: #64748b;
                font-size: 13px;
                font-weight: 600;
            }}
            .value {{
                color: #0f172a;
                font-size: 14px;
                font-weight: bold;
            }}
            .role-badge {{
                background: {color};
                color: white;
                padding: 4px 14px;
                border-radius: 14px;
                font-size: 12px;
                font-weight: bold;
            }}
            .stats-box {{
                background: #eff6ff;
                padding: 16px;
                border-radius: 12px;
                margin: 16px 0;
                text-align: center;
                border: 1px solid #dbeafe;
            }}
            .stats-title {{
                color: {color};
                font-size: 13px;
                font-weight: bold;
                margin-bottom: 8px;
            }}
            .stats-value {{
                color: #0f172a;
                font-size: 17px;
                font-weight: bold;
            }}
            .footer {{
                background: #f8fafc;
                text-align: center;
                padding: 16px;
                border-top: 1px solid #e2e8f0;
                font-size: 11px;
                color: #94a3b8;
            }}
        </style>
        </head>
        <body>
            <div class="badge">
                <div class="header">
                    {logo_html}
                    <div class="shop-name">{shop_name}</div>
                    <div class="shop-info">{contact_html}</div>
                </div>

                <div class="badge-title">🪪  بطاقة موظف</div>

                <div class="info">
                    <div class="info-row">
                        <span class="label">👤 الاسم</span>
                        <span class="value">{self.user.username}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">🎭 الدور</span>
                        <span class="value">
                            <span class="role-badge">{role_text}</span>
                        </span>
                    </div>
                    <div class="info-row">
                        <span class="label">📅 تاريخ الإصدار</span>
                        <span class="value">{today}</span>
                    </div>

                    <div class="stats-box">
                        <div class="stats-title">📊  إحصائيات الموظف</div>
                        <div class="stats-value">
                            {total_bookings} حجز  ·  {total_revenue:,.0f} ج.م
                        </div>
                    </div>

                    {qr_html}
                </div>

                <div class="footer">
                    بطاقة صادرة إلكترونيًا — {shop_name}
                </div>
            </div>
        </body>
        </html>
        """
        return html

    def _print_badge(self):
        """يفتح البطاقة في المتصفح للطباعة."""
        try:
            receipts_dir = os.path.join(self.db.base_dir, "badges")
            os.makedirs(receipts_dir, exist_ok=True)

            stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            html_path = os.path.join(
                receipts_dir,
                f"badge_{self.user.username}_{stamp}.html"
            )

            with open(html_path, "w", encoding="utf-8") as f:
                f.write(self._build_badge_html())

            if os.name == "nt":
                os.startfile(html_path)

            play_sound("success")

            QMessageBox.information(
                self, "تم",
                f"✅ تم فتح البطاقة في المتصفح.\n\n"
                f"📁 الملف: {os.path.basename(html_path)}\n\n"
                f"للطباعة: اضغط Ctrl+P في المتصفح"
            )
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل الطباعة:\n{e}")