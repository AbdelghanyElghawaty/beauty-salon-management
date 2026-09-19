"""
SMS / WhatsApp notifications via Twilio.

This uses only Python's standard library (urllib), so no extra package
installs are needed beyond what the rest of the app already requires.

IMPORTANT — this feature needs:
  1. An internet connection at the moment of sending.
  2. A Twilio account (https://www.twilio.com) with an Account SID, an Auth
     Token, and a Twilio phone number capable of sending SMS (or an approved
     WhatsApp sender for WhatsApp messages). Twilio charges per message.

Settings are stored in a small JSON file next to the database, so they
persist across runs without touching the SQLite schema.
"""

import os
import json
import urllib.request
import urllib.parse
import urllib.error
import base64


SETTINGS_FILENAME = "notifications_settings.json"

DEFAULT_SETTINGS = {
    "enabled": False,
    "channel": "sms",  # "sms" or "whatsapp"
    "account_sid": "",
    "auth_token": "",
    "from_number": "",  # e.g. "+15551234567" (or Twilio WhatsApp sender for whatsapp channel)
}


class NotificationSettings:
    def __init__(self, base_dir):
        self.path = os.path.join(base_dir, SETTINGS_FILENAME)
        self.data = dict(DEFAULT_SETTINGS)
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                self.data.update(saved)
            except (json.JSONDecodeError, OSError):
                pass

    def save(self, **kwargs):
        self.data.update(kwargs)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    @property
    def is_configured(self):
        return bool(self.data["account_sid"] and self.data["auth_token"] and self.data["from_number"])


def send_message(settings: NotificationSettings, to_number, body):
    """
    Send an SMS or WhatsApp message through Twilio's REST API.
    Returns (success: bool, info: str).
    """
    if not settings.is_configured:
        return False, "إعدادات الإشعارات ناقصة. من فضلك اكتب بيانات Twilio في الإعدادات الأول."

    to_number = to_number.strip()
    if not to_number:
        return False, "العميل ده مالوش رقم تليفون مسجل."

    account_sid = settings.data["account_sid"]
    auth_token = settings.data["auth_token"]
    from_number = settings.data["from_number"]
    channel = settings.data.get("channel", "sms")

    if channel == "whatsapp":
        to_number = to_number if to_number.startswith("whatsapp:") else f"whatsapp:{to_number}"
        from_number = from_number if from_number.startswith("whatsapp:") else f"whatsapp:{from_number}"

    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    payload = urllib.parse.urlencode({"To": to_number, "From": from_number, "Body": body}).encode("utf-8")

    credentials = base64.b64encode(f"{account_sid}:{auth_token}".encode("utf-8")).decode("utf-8")
    request = urllib.request.Request(url, data=payload, method="POST")
    request.add_header("Authorization", f"Basic {credentials}")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            if response.status in (200, 201):
                return True, "تم إرسال الرسالة بنجاح."
            return False, f"رد غير متوقع من الخدمة (كود {response.status})."
    except urllib.error.HTTPError as e:
        try:
            error_body = json.loads(e.read().decode("utf-8"))
            message = error_body.get("message", str(e))
        except Exception:
            message = str(e)
        return False, f"فشل الإرسال: {message}"
    except urllib.error.URLError as e:
        return False, f"مفيش اتصال بالإنترنت أو الخدمة مش متاحة دلوقتي: {e.reason}"
    except Exception as e:
        return False, f"حصل خطأ غير متوقع: {e}"


def build_booking_confirmation(customer_name, service_name, date, time_):
    return (
        f"أهلاً {customer_name}، تم تأكيد حجزك في صالون الحلاقة.\n"
        f"الخدمة: {service_name}\n"
        f"الموعد: {date} الساعة {time_}\n"
        f"نتشرف بزيارتك!"
    )

