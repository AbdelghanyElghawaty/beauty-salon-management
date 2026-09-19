"""
Login Advanced — ميزات متقدمة لشاشة الدخول.
================================================
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
from login_helpers import (
    image_to_data_uri,
    generate_qr_data_uri,
    play_sound,
)


# ============================================================
# 1) Stats Preview — إحصائيات اليوم
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
                # b = (bid, cname, sname, price, barber, date, time,
                #      extra_json, extra_total, pm)
                price = (b[3] or 0) + (b[8] or 0)
                revenue += price
                customers_set.add(b[1])  # اسم العميل
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
# 2) Employee of the Month
# ============================================================
def get_employee_of_month(db):
    """
    يرجع dict فيه:
    - name: اسم الموظف
    - revenue: إيراداته في الشهر
    - bookings: عدد حجوزاته
    """
    try:
        bookings = db.list_bookings()
        now = datetime.now()
        month_start = now.replace(day=1).strftime("%Y-%m-%d")

        data = {}  # {barber: {"revenue": X, "bookings": Y}}

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

        # الأحسن حسب الإيرادات
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
        # ترجمة الشهر يدويًا
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
# 3) Employee Badge — بطاقة الموظف
# ============================================================
class EmployeeBadgeDialog(QDialog):
    """
    نافذة عرض بطاقة الموظف مع QR Code.
    البطاقة تتطبع في المتصفح (HTML).
    """

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

        # العنوان
        title = QLabel("🪪  بطاقة الموظف")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"font-size: 20px; font-weight: bold; "
            f"color: {Theme.color('primary')}; background: transparent;"
        )
        layout.addWidget(title)

        # المعاينة
        preview = QTextEdit()
        preview.setReadOnly(True)
        preview.setHtml(self._build_badge_html())
        preview.setStyleSheet(
            "QTextEdit { background-color: #ffffff; "
            "border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px; }"
        )
        layout.addWidget(preview, stretch=1)

        # الأزرار
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

        # بيانات الصالون
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

        # اللوجو
        logo_uri = None
        if shop_logo and os.path.exists(shop_logo):
            logo_uri = image_to_data_uri(shop_logo)

        # لو مفيش، دور على beauty-salon.ico أو haircut.ico
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

        # QR Code
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

        # الدور
        role_text = "سوبر أدمن" if self.user.is_admin else "موظف"

        # التاريخ
        today = datetime.now().strftime("%Y-%m-%d")

        # إحصائيات الموظف
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

        # بيانات الاتصال
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