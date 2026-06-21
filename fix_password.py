"""
تنظیم رمز پیشفرض برای مدیر با هش صحیح
"""

import os
import json
import hashlib

def hash_password(password):
    """هش کردن رمز عبور با SHA-256 و Salt"""
    import os
    salt = os.urandom(32).hex()
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${hashed}"

# مسیر ذخیره‌سازی
data_path = os.path.join(os.environ.get('APPDATA', os.getcwd()), 'main')
os.makedirs(data_path, exist_ok=True)

# تنظیم رمز پیشفرض با هش
password = 'admin123'
hashed_password = hash_password(password)

password_data = {
    "hashed_password": hashed_password
}

filepath = os.path.join(data_path, 'admin_password.json')
with open(filepath, 'w', encoding='utf-8') as f:
    json.dump(password_data, f, ensure_ascii=False, indent=2)

print(f"✅ فایل رمز در {filepath} ایجاد شد")
print(f"🔑 رمز پیشفرض: admin123")
print(f"📝 هش ذخیره شده: {hashed_password[:50]}...")