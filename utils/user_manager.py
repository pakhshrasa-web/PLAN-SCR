"""
مدیریت کاربران و کدهای ثبت نام - نسخه امن و بهینه برای اندروید
"""

import random
import string
from utils.file_manager import load_json, save_json
from utils.jalali_date import get_today_jalali
from utils.auth import hash_password, verify_password  # ✅ یک بار در بالا


def generate_code(prefix):
    """تولید کد تصادفی با پیشوند مشخص"""
    numbers = ''.join(random.choices(string.digits, k=6))
    return f"{prefix}{numbers}"


def get_users():
    """دریافت لیست کاربران"""
    data = load_json('users.json')
    return data.get('users', [])


def save_users(users):
    """ذخیره لیست کاربران"""
    data = load_json('users.json')
    data['users'] = users
    save_json('users.json', data)


def get_codes():
    """دریافت لیست کدهای فعال"""
    data = load_json('codes.json')
    return data.get('codes', [])


def save_codes(codes):
    """ذخیره لیست کدهای فعال"""
    data = load_json('codes.json')
    data['codes'] = codes
    save_json('codes.json', data)


def create_code(role, name):
    """ایجاد کد جدید برای ثبت نام"""
    prefix_map = {
        'مدیر': 'mg',
        'ادمین': 'ad',
        'سوپروایزر': 'sp',
        'بازاریاب': 'ag',
        'حسابدار': 'ac',
        'موزع': 'mo',
        'راننده': 'ra',
        'انباردار': 'an',
        'سایر': 'ot'
    }
    
    prefix = prefix_map.get(role, 'us')
    code = generate_code(prefix)
    
    codes = get_codes()
    codes.append({
        'code': code,
        'role': role,
        'name': name,
        'used': False,
        'created_at': get_today_jalali()
    })
    save_codes(codes)
    return code


def verify_code(code):
    """بررسی اعتبار کد ثبت نام"""
    codes = get_codes()
    for c in codes:
        if c.get('code') == code and not c.get('used', False):
            return c
    return None


def register_user(code, username, password, phone, email):
    """ثبت نام کاربر با کد - رمز عبور هش می‌شود"""
    code_info = verify_code(code)
    if not code_info:
        return False, "کد نامعتبر یا قبلاً استفاده شده است"
    
    users = get_users()
    
    for u in users:
        if u.get('username') == username:
            return False, "این نام کاربری قبلاً ثبت شده است"
    
    hashed_password = hash_password(password)
    
    new_user = {
        'id': len(users) + 1,
        'username': username,
        'hashed_password': hashed_password,
        'role': code_info.get('role', 'بازاریاب'),
        'name': code_info.get('name', ''),
        'phone': phone,
        'email': email,
        'registered_at': get_today_jalali()
    }
    users.append(new_user)
    save_users(users)
    
    codes = get_codes()
    for c in codes:
        if c.get('code') == code:
            c['used'] = True
            break
    save_codes(codes)
    
    return True, "ثبت نام با موفقیت انجام شد"


def login(username, password):
    """ورود به سیستم با بررسی رمز هش شده"""
    users = get_users()
    for user in users:
        if user.get('username') == username:
            # ✅ verify_password از بالا ایمپورت شده
            if verify_password(password, user.get('hashed_password', '')):
                return user
            return None
    
    # ✅ بررسی مدیر سیستم - از auth ایمپورت شده
    from utils.auth import get_admin_password
    admin_hashed = get_admin_password()
    if username == 'admin' and admin_hashed and verify_password(password, admin_hashed):
        return {'role': 'مدیر', 'name': 'مدیر سیستم', 'username': 'admin', 'id': 0}
    
    return None


def delete_user_by_id(user_id):
    """حذف کاربر بر اساس ID بدون بازنشانی ID ها"""
    users = get_users()
    users = [u for u in users if u.get('id') != user_id]
    save_users(users)
    return True


def delete_user(username):
    """حذف کاربر بر اساس نام کاربری"""
    users = get_users()
    users = [u for u in users if u.get('username') != username]
    save_users(users)
    return True


def get_user_by_username(username):
    """دریافت کاربر بر اساس نام کاربری"""
    users = get_users()
    for user in users:
        if user.get('username') == username:
            return user
    return None


def get_next_id(items):
    """تولید ID جدید"""
    if not items:
        return 1
    return max([item.get('id', 0) for item in items]) + 1


def change_password(username, old_password, new_password):
    """تغییر رمز عبور کاربر"""
    user = get_user_by_username(username)
    if not user:
        return False, "کاربر یافت نشد"
    
    if not verify_password(old_password, user.get('hashed_password', '')):
        return False, "رمز عبور فعلی اشتباه است"
    
    user['hashed_password'] = hash_password(new_password)
    
    users = get_users()
    for i, u in enumerate(users):
        if u.get('id') == user.get('id'):
            users[i] = user
            break
    save_users(users)
    return True, "رمز عبور با موفقیت تغییر کرد"


def get_users_by_role(role):
    """دریافت کاربران بر اساس نقش"""
    users = get_users()
    return [u for u in users if u.get('role') == role]