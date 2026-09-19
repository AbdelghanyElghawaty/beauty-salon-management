"""
Login Helpers — أدوات مساعدة لشاشة الدخول.
================================================
- Sounds (winsound.Beep)
- Hijri date
- QR Code generation (للـ Employee Badge)
- Image to base64 (data URI)
- Password strength
- Translations (ar/en)
"""

import os
from datetime import datetime


# ============================================================
# الأصوات — Sounds
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
# التاريخ الهجري — Hijri Date
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
    # المحاولة الأولى: hijri-converter
    try:
        from hijri_converter import Gregorian
        g = datetime.now()
        h = Gregorian(g.year, g.month, g.day).to_hijri()
        return f"{h.day} {HIJRI_MONTHS[h.month - 1]} {h.year} هـ"
    except ImportError:
        pass
    except Exception:
        pass

    # fallback: حساب تقريبي
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
# QR Code (للـ Employee Badge فقط)
# ============================================================
def generate_qr_data_uri(text):
    """
    يولّد QR Code كـ data URI (للاستخدام في HTML).
    يُستخدم في بطاقة الموظف (Employee Badge).
    """
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


# ============================================================
# Image to Data URI
# ============================================================
def image_to_data_uri(image_path):
    """
    يحول أي صورة (ico/png/jpg) لـ data URI.
    يدعم .ico عن طريق PIL.
    """
    if not image_path or not os.path.exists(image_path):
        return None

    # 1) PIL (يدعم ico)
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

    # 2) fallback للملفات العادية
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
# Password Strength
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
# الترجمات — Translations
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