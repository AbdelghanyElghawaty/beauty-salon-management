"""
change_password.py — سكريبت داخلي لتغيير باسورد أي مستخدم.
⚠️ أداة تطوير — متبعتش للعملاء. احذفها بعد الاستخدام.

الاستخدام:
    python change_password.py <username> <new_password>
    python change_password.py              ← هيسألك تفاعليًا
"""

import os
import sys
import getpass

# نضيف مسار المشروع
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from database import Database

DB_PATH = os.path.join(BASE_DIR, "barber_shop.db")


def main():
    if len(sys.argv) == 3:
        username, new_password = sys.argv[1], sys.argv[2]
    else:
        username = input("اسم المستخدم: ").strip()
        new_password = getpass.getpass("الباسورد الجديد: ")
        confirm = getpass.getpass("أكد الباسورد الجديد: ")
        if new_password != confirm:
            print("❌ الباسوردين مش متطابقين")
            sys.exit(1)

    # تحقق من قوة الباسورد
    if len(new_password) < 6:
        print("❌ الباسورد لازم يكون 6 حروف على الأقل")
        sys.exit(1)

    if not os.path.exists(DB_PATH):
        print(f"❌ ملف قاعدة البيانات مش موجود: {DB_PATH}")
        sys.exit(1)

    db = Database(DB_PATH)

    # تأكد إن المستخدم موجود
    users = db.list_users()
    target = None
    for u in users:
        # list_users بيرجع dicts — نتأكد من الشكل
        uname = u.get("username") if isinstance(u, dict) else u[1]
        if uname == username:
            target = u
            break

    if not target:
        print(f"❌ المستخدم '{username}' مش موجود")
        print(f"المستخدمين الموجودين: {[u.get('username', u[1]) for u in users]}")
        sys.exit(1)

    user_id = target.get("id") if isinstance(target, dict) else target[0]
    db.update_user_password(user_id, new_password)

    # تأكد إن التغيير اتعمل
    ok = db.verify_login(username, new_password)
    if ok:
        print(f"✅ تم تغيير باسورد '{username}' بنجاح")
    else:
        print("❌ حصل خطأ — الباسورد الجديد مش شغال")


if __name__ == "__main__":
    main()
