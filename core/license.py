"""
License — نظام حماية البرنامج بكود تفعيل مرتبط بالجهاز.
+ دعم تاريخ انتهاء الصلاحية (اشتراكات محددة المدة)
+ حماية ضد التلاعب بساعة النظام
+ حماية ضد نقل البرنامج لجهاز تاني
+ ✅ بصمة متسامحة: بتتسامح مع تغيير قطعة واحدة (رام/هارد...)
+ ✅ PowerShell CIM بدل wmic (شغالة على Windows 10 و 11)
+ 🔐 المفتاح السري يُقرأ من متغير بيئة (.env) — مش مكتوب في الكود
"""

import os
import json
import uuid
import hmac
import hashlib
import platform
import subprocess
from datetime import datetime, timedelta

# ============================================================
# ✅ تحميل متغيرات البيئة من ملف .env
# ============================================================
try:
    from dotenv import load_dotenv

    # ندوّر على ملف .env جنب ملف license.py أو في المجلد الأب
    _base = os.path.dirname(os.path.abspath(__file__))
    _env_path = os.path.join(_base, ".env")

    if os.path.exists(_env_path):
        load_dotenv(_env_path)
    else:
        # fallback: يقرأ من البيئة العادية
        load_dotenv()
except ImportError:
    # python-dotenv مش مثبتة → نعتمد على متغيرات البيئة بس
    pass


# ============================================================
# 🔐 المفتاح السري — يُقرأ من متغير البيئة (مش في الكود)
# ============================================================
SECRET_KEY = os.environ.get("BARBER_SHOP_KEY")

if not SECRET_KEY:
    raise RuntimeError(
        "\n"
        "=====================================================\n"
        "❌ خطأ حرج: مفتاح التشفير BARBER_SHOP_KEY غير موجود!\n"
        "=====================================================\n"
        "\n"
        "الحل:\n"
        "  1. اتأكد إن فيه ملف .env في مجلد المشروع\n"
        "  2. اتأكد إن فيه السطر ده جواه:\n"
        "     BARBER_SHOP_KEY=المفتاح_بتاعك\n"
        "  3. أو ضيف متغير البيئة في نظام التشغيل:\n"
        "     $env:BARBER_SHOP_KEY='المفتاح_بتاعك'\n"
        "\n"
        "⚠️  لو المفتاح ضاع، كل التراخيص الحالية هتبقى غلط!\n"
        "=====================================================\n"
    )


# اسم ملف الترخيص اللي بيتحفظ جنب البرنامج
LICENSE_FILE = "license.key"

# ✅ كم مكون من مكونات البصمة لازم يتطابق عشان نعتبره نفس الجهاز
# (كل ما الرقم يقل كل ما التسامحة تزيد — 2 من 5 ميزان كويس)
MIN_COMPONENT_MATCHES = 2


# ============================================================
# PowerShell CIM — بديل wmic (شغال على Win 10 + Win 11)
# ============================================================
def _run_ps(command):
    """يشغل أمر PowerShell ويرجع أول سطر نتيجة نظيف."""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True, text=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
        if lines:
            return lines[0]
    except Exception:
        pass
    return ""


# ============================================================
# Hardware ID — بصمة الجهاز
# ============================================================
def _get_mac_address():
    """يرجع MAC Address — ثابت للجهاز."""
    try:
        mac = uuid.getnode()
        return f"{mac:012x}"
    except Exception:
        return "unknown"


def _get_windows_serial():
    """Serial Number للهارد — PowerShell CIM (شغال على Win 10/11)."""
    if platform.system() != "Windows":
        return ""
    return _run_ps("(Get-CimInstance Win32_DiskDrive | Select-Object -First 1 -ExpandProperty SerialNumber)")


def _get_processor_id():
    """Processor ID — PowerShell CIM."""
    if platform.system() != "Windows":
        return platform.machine()
    pid = _run_ps("(Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty ProcessorId)")
    return pid or platform.machine()


def _get_motherboard_serial():
    """Serial Number للوحة الأم — PowerShell CIM."""
    if platform.system() != "Windows":
        return ""
    return _run_ps("(Get-CimInstance Win32_BaseBoard | Select-Object -First 1 -ExpandProperty SerialNumber)")


def _get_machine_guid():
    """MachineGuid من الريجستري — ثابتة لكل ويندوز مهما تغيرت القطع."""
    if platform.system() != "Windows":
        return ""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Cryptography"
        )
        value, _ = winreg.QueryValueEx(key, "MachineGuid")
        winreg.CloseKey(key)
        return value
    except Exception:
        return ""


def _get_components():
    """
    يرجع قائمة مكونات البصمة (بدون دمجهم).
    كل مكون بيتخزن لوحده عشان نقدر نقارن تسامح لاحقًا.
    """
    return [
        _get_mac_address(),
        platform.node(),
        _get_windows_serial(),
        _get_processor_id(),
        _get_motherboard_serial(),
        _get_machine_guid(),
    ]


def get_hardware_id():
    """
    يرجع بصمة الجهاز — 16 حرف hex.
    نفس البصمة القديمة بالظبط عشان التراخيص الحالية تفضل شغالة.
    """
    raw = "|".join(str(p) for p in _get_components() if p)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    hw = digest[:16].upper()
    return "-".join(hw[i:i+4] for i in range(0, 16, 4))


# ============================================================
# ✅ مقارنة متسامحة — هل ده نفس الجهاز؟
# ============================================================
def is_same_device(saved_components, current_components, min_matches=MIN_COMPONENT_MATCHES):
    """
    بيقارن المكونات المحفوظة بالمكونات الحالية.

    - لو مفيش مكونات محفوظة (ترخيص قديم) → بنقارن بالطريقة القديمة الصارمة
    - لو فيه مكونات → بنقبل لو اتطابق (min_matches) مكون أو أكتر
    """
    if not saved_components:
        return None  # مفيش بيانات — يبقى القرار للكولر

    saved = [str(c).strip().upper() for c in saved_components if c and str(c).strip()]
    current = [str(c).strip().upper() for c in current_components if c and str(c).strip()]

    if not saved or not current:
        return None

    matches = sum(1 for s in saved if s in current)
    return matches >= min_matches


# ============================================================
# توليد كود التفعيل من البصمة
# ============================================================
def generate_activation_code(hardware_id, expiry_date=None):
    """
    يولد كود التفعيل من بصمة الجهاز + تاريخ الانتهاء.

    expiry_date: string بصيغة "YYYY-MM-DD" أو None للتفعيل الدائم
    """
    hw_clean = hardware_id.replace("-", "").upper()

    if expiry_date is None:
        payload = f"{hw_clean}|PERMANENT"
    else:
        try:
            datetime.strptime(expiry_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("تاريخ الانتهاء لازم يكون بصيغة YYYY-MM-DD")
        payload = f"{hw_clean}|{expiry_date}"

    signature = hmac.new(
        SECRET_KEY.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest().upper()

    code = signature[:20]
    return "-".join(code[i:i+5] for i in range(0, 20, 5))


def verify_activation_code(hardware_id, code, expiry_date=None):
    """يتأكد إن الكود مطابق للبصمة + تاريخ الانتهاء."""
    if not hardware_id or not code:
        return False
    expected = generate_activation_code(hardware_id, expiry_date)
    return hmac.compare_digest(
        expected.replace("-", "").upper(),
        code.replace("-", "").upper(),
    )


# ============================================================
# License Manager
# ============================================================
class LicenseManager:
    """يدير حفظ وقراءة والتحقق من الترخيص مع دعم تاريخ الانتهاء."""

    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.license_path = os.path.join(base_dir, LICENSE_FILE)
        self.hardware_id = get_hardware_id()
        self.components = _get_components()

    # ----------------------------------------
    # الحالة الحالية للترخيص
    # ----------------------------------------
    def get_status(self):
        """
        يرجع dict فيه حالة الترخيص:
        {
            "activated": bool,
            "valid": bool,
            "expired": bool,
            "days_left": int or None,
            "expiry_date": str or None,
            "message": str
        }
        """
        data = self._load_license()

        if not data:
            return {
                "activated": False,
                "valid": False,
                "expired": False,
                "days_left": None,
                "expiry_date": None,
                "message": "البرنامج مش مفعّل",
            }

        saved_hw = data.get("hardware_id", "")
        saved_code = data.get("activation_code", "")
        expiry_date = data.get("expiry_date")

        # ✅ فحص الجهاز — متسامح مع التراخيص الجديدة، صارم مع القديمة
        saved_components = data.get("components")
        same_device = is_same_device(saved_components, self.components)

        if same_device is False:
            return {
                "activated": False,
                "valid": False,
                "expired": False,
                "days_left": None,
                "expiry_date": expiry_date,
                "message": "الترخيص مش بتاع الجهاز ده",
            }
        # لو same_device is None (ترخيص قديم بدون components) → نقارن بالطريقة القديمة
        if same_device is None and saved_hw != self.hardware_id:
            return {
                "activated": False,
                "valid": False,
                "expired": False,
                "days_left": None,
                "expiry_date": expiry_date,
                "message": "الترخيص مش بتاع الجهاز ده",
            }

        # الكود غلط أو اتعبث بيه
        if not verify_activation_code(saved_hw, saved_code, expiry_date):
            return {
                "activated": True,
                "valid": False,
                "expired": False,
                "days_left": None,
                "expiry_date": expiry_date,
                "message": "الترخيص اتعبث بيه أو غلط",
            }

        # ⚠️ حماية ضد التلاعب بساعة النظام
        last_check = data.get("last_check")
        now = datetime.now()
        if last_check:
            try:
                last_dt = datetime.fromisoformat(last_check)
                if now < last_dt - timedelta(days=1):
                    return {
                        "activated": True,
                        "valid": False,
                        "expired": False,
                        "days_left": None,
                        "expiry_date": expiry_date,
                        "message": "⚠️ تم اكتشاف تلاعب في ساعة الجهاز",
                    }
            except Exception:
                pass

        # حفظ وقت آخر فحص
        self._update_last_check(now)

        # لو تفعيل دائم
        if expiry_date is None:
            return {
                "activated": True,
                "valid": True,
                "expired": False,
                "days_left": None,
                "expiry_date": None,
                "message": "✅ تفعيل دائم",
            }

        # نحسب الأيام المتبقية
        try:
            expiry_dt = datetime.strptime(expiry_date, "%Y-%m-%d")
            expiry_end = expiry_dt.replace(hour=23, minute=59, second=59)
            days_left = (expiry_end - now).days

            if now > expiry_end:
                return {
                    "activated": True,
                    "valid": False,
                    "expired": True,
                    "days_left": 0,
                    "expiry_date": expiry_date,
                    "message": f"❌ انتهى الاشتراك بتاريخ {expiry_date}",
                }

            return {
                "activated": True,
                "valid": True,
                "expired": False,
                "days_left": days_left,
                "expiry_date": expiry_date,
                "message": f"✅ الترخيص ساري — باقي {days_left} يوم",
            }
        except ValueError:
            return {
                "activated": True,
                "valid": False,
                "expired": False,
                "days_left": None,
                "expiry_date": expiry_date,
                "message": "تاريخ الانتهاء المحفوظ غلط",
            }

    # ----------------------------------------
    # هل الجهاز مفعّل؟
    # ----------------------------------------
    def is_activated(self):
        return self.get_status()["valid"]

    # ----------------------------------------
    # تفعيل الجهاز (بالكود)
    # ----------------------------------------
    def activate(self, code):
        """
        يفعّل الجهاز بالكود اللي المستخدم دخله.
        البرنامج هيجرب التواريخ المحتملة لوحده.
        """
        code = code.strip().upper()

        valid_expiry = self._try_parse_expiry(code)

        if valid_expiry is False:
            return False, "كود التفعيل غلط. تأكد إنك كتبته صح."

        data = {
            "hardware_id": self.hardware_id,
            "components": self.components,  # ✅ بنخزن المكونات عشان المقارنة المتسامحة
            "activation_code": code,
            "expiry_date": valid_expiry,
            "activated_at": datetime.now().isoformat(timespec="seconds"),
            "last_check": datetime.now().isoformat(timespec="seconds"),
        }

        try:
            with open(self.license_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            if valid_expiry is None:
                return True, "✅ تم تفعيل البرنامج بنجاح (تفعيل دائم)"
            else:
                return True, f"✅ تم تفعيل البرنامج بنجاح حتى {valid_expiry}"
        except OSError as e:
            return False, f"فشل حفظ الترخيص: {e}"

    def _try_parse_expiry(self, code):
        """
        بيجرب يشوف الكود مطابق لأي تاريخ انتهاء محتمل.

        - الأول يجرب التفعيل الدائم
        - بعدين يجرب تواريخ من النهارده لـ 10 سنين قدام
        """
        # 1) تفعيل دائم
        if verify_activation_code(self.hardware_id, code, None):
            return None

        # 2) نجرب تواريخ من النهارده لـ 10 سنين قدام
        today = datetime.now().date()
        for days_offset in range(0, 365 * 10 + 1):
            test_date = (today + timedelta(days=days_offset)).strftime("%Y-%m-%d")
            if verify_activation_code(self.hardware_id, code, test_date):
                return test_date

        # 3) مفيش أي مطابقة
        return False

    # ----------------------------------------
    # قراءة / حفظ ملف الترخيص
    # ----------------------------------------
    def _load_license(self):
        if not os.path.exists(self.license_path):
            return None
        try:
            with open(self.license_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return None

    def _update_last_check(self, now):
        """يحدّث وقت آخر فحص (عشان نكتشف التلاعب بالساعة)."""
        try:
            data = self._load_license()
            if data:
                data["last_check"] = now.isoformat(timespec="seconds")
                with open(self.license_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def get_saved_hardware_id(self):
        data = self._load_license()
        return data.get("hardware_id", "") if data else ""

    def deactivate(self):
        """يمسح ملف الترخيص — عشان تنقل البرنامج لجهاز تاني."""
        try:
            if os.path.exists(self.license_path):
                os.remove(self.license_path)
            return True
        except OSError:
            return False