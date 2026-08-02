# utils/bank_manager.py
# ========== مدیریت بانک‌ها ==========

import json
import os
from utils.file_manager import get_data_path


def get_banks_file_path():
    """دریافت مسیر فایل banks.json"""
    return os.path.join(get_data_path(), 'banks.json')


def _load_banks():
    """بارگذاری لیست بانک‌ها از فایل JSON"""
    file_path = get_banks_file_path()
    
    if not os.path.exists(file_path):
        # ایجاد فایل خالی
        _save_banks([])
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # هندل کردن dict (در صورت وجود)
        if isinstance(data, dict):
            data = []
        
        return data if isinstance(data, list) else []
        
    except Exception as e:
        print(f"خطا در بارگذاری بانک‌ها: {e}")
        return []


def _save_banks(banks):
    """ذخیره لیست بانک‌ها در فایل JSON"""
    file_path = get_banks_file_path()
    
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(banks, f, ensure_ascii=False, indent=2)
        
        return True
        
    except Exception as e:
        print(f"خطا در ذخیره بانک‌ها: {e}")
        return False


def get_banks():
    """دریافت لیست بانک‌ها"""
    return _load_banks()


def get_bank_names():
    """دریافت فقط نام بانک‌ها (برای کامبوباکس)"""
    banks = _load_banks()
    return [bank.get('name', '') for bank in banks if bank.get('name')]


def add_bank(name, description=''):
    """افزودن بانک جدید"""
    if not name or not name.strip():
        return False, "نام بانک نمی‌تواند خالی باشد"
    
    banks = _load_banks()
    
    # بررسی تکراری نبودن
    for bank in banks:
        if bank.get('name', '').strip() == name.strip():
            return False, f'بانک "{name}" قبلاً ثبت شده است'
    
    new_bank = {
        'name': name.strip(),
        'description': description.strip() if description else '',
        'created_at': ''
    }
    
    banks.append(new_bank)
    
    if _save_banks(banks):
        return True, f'بانک "{name}" با موفقیت اضافه شد'
    else:
        return False, "خطا در ذخیره بانک"


def update_bank(old_name, new_name, new_description=''):
    """ویرایش بانک"""
    if not new_name or not new_name.strip():
        return False, "نام بانک نمی‌تواند خالی باشد"
    
    banks = _load_banks()
    
    # پیدا کردن بانک قدیمی
    found = False
    for bank in banks:
        if bank.get('name', '') == old_name:
            # بررسی تکراری نبودن با بقیه (غیر از خودش)
            for other in banks:
                if other.get('name', '') != old_name and other.get('name', '') == new_name.strip():
                    return False, f'بانک "{new_name}" قبلاً ثبت شده است'
            
            bank['name'] = new_name.strip()
            bank['description'] = new_description.strip() if new_description else ''
            found = True
            break
    
    if not found:
        return False, f'بانک "{old_name}" یافت نشد'
    
    if _save_banks(banks):
        return True, f'بانک "{new_name}" با موفقیت ویرایش شد'
    else:
        return False, "خطا در ذخیره بانک"


def delete_bank(name):
    """حذف بانک"""
    banks = _load_banks()
    
    # پیدا کردن بانک
    new_banks = [bank for bank in banks if bank.get('name', '') != name]
    
    if len(new_banks) == len(banks):
        return False, f'بانک "{name}" یافت نشد'
    
    if _save_banks(new_banks):
        return True, f'بانک "{name}" با موفقیت حذف شد'
    else:
        return False, "خطا در ذخیره بانک"