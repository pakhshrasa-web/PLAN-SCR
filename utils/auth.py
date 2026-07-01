"""
احراز هویت برای تنظیمات سیستم - نسخه امن با Salt
"""

import hashlib
import os
from utils.file_manager import load_json, save_json

def hash_password(password):
    """
    هش کردن رمز عبور با SHA-256 و Salt تصادفی
    برگرداندن: salt$hash
    """
    salt = os.urandom(32).hex()
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${hashed}"

def verify_password(password, hashed_password):
    """
    بررسی رمز عبور با هش ذخیره‌شده
    """
    if not hashed_password or '$' not in hashed_password:
        return False
    
    try:
        salt, stored_hash = hashed_password.split('$')
        new_hash = hashlib.sha256((salt + password).encode()).hexdigest()
        return new_hash == stored_hash
    except Exception:
        return False

def get_admin_password():
    """
    دریافت رمز مدیر از فایل
    """
    data = load_json('admin_password.json')
    return data.get('hashed_password', None)

def set_admin_password(password):
    """
    تنظیم رمز جدید مدیر (با هش)
    """
    hashed = hash_password(password)
    save_json('admin_password.json', {'hashed_password': hashed})

def check_default_password():
    """
    بررسی و تنظیم رمز پیشفرض (در صورت عدم وجود)
    رمز پیشفرض: admin123
    """
    if get_admin_password() is None:
        set_admin_password('admin123')
        return True
    return False

def is_admin_password_set():
    """
    بررسی اینکه آیا رمز مدیر تنظیم شده است
    """
    return get_admin_password() is not None