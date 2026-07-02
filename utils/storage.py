"""
مدیریت ذخیره‌سازی داده‌ها در سیستم‌عامل‌های مختلف
"""

import os
import json
from kivy.utils import platform

_data_path = None

def init_data_path():
    """مقداردهی اولیه مسیر ذخیره‌سازی داخلی اپ"""
    global _data_path
    if _data_path is not None:
        return _data_path
    
    app_name = 'planandroid'
    
    if platform == 'android':
        try:
            from android.storage import app_storage_path
            path = app_storage_path()
            if path:
                _data_path = os.path.join(path, app_name)
                print(f"✅ مسیر اندروید: {_data_path}")
            else:
                raise Exception("app_storage_path returned None")
        except Exception as e:
            print(f"⚠️ خطا در دریافت مسیر اندروید: {e}")
            _data_path = os.path.join('/data/data/org.pakhshrasa.planandroid/files', app_name)
    elif platform == 'win':
        _data_path = os.path.join(os.environ.get('APPDATA', os.getcwd()), app_name)
        print(f"✅ مسیر ویندوز: {_data_path}")
    elif platform in ('linux', 'macosx'):
        _data_path = os.path.join(os.path.expanduser('~'), f'.{app_name}')
        print(f"✅ مسیر لینوکس/مک: {_data_path}")
    else:
        _data_path = os.path.join(os.getcwd(), app_name)
        print(f"✅ مسیر پیش‌فرض: {_data_path}")
    
    try:
        os.makedirs(_data_path, exist_ok=True)
        print(f"✅ پوشه‌ها در {_data_path} ایجاد شدند")
    except Exception as e:
        print(f"❌ خطا در ایجاد پوشه: {e}")
        _data_path = os.path.join(os.getcwd(), app_name)
        os.makedirs(_data_path, exist_ok=True)
    
    return _data_path

def get_data_path():
    """بازگرداندن مسیر ذخیره‌سازی داخلی اپ"""
    global _data_path
    if _data_path is None:
        init_data_path()
    return _data_path

# ============================================================
# ✅ توابع مسیردهی عمومی (برای اندروید و دسکتاپ)
# ============================================================

def _get_public_base_path():
    """دریافت مسیر پایه فضای عمومی"""
    if platform == 'android':
        try:
            from android.storage import primary_external_storage_path
            base = primary_external_storage_path()
            if base:
                return base
        except Exception as e:
            print(f"⚠️ خطا در دریافت مسیر عمومی اندروید: {e}")
        return '/storage/emulated/0/'
    else:
        return os.path.join(os.path.expanduser('~'), 'plan_android_data')

def get_public_path(folder_name):
    """
    دریافت مسیر پوشه در فضای عمومی
    folder_name: 'backup', 'export', 'import'
    """
    base = _get_public_base_path()
    
    if platform == 'android':
        path = os.path.join(base, 'plan_android_data', folder_name)
    else:
        path = os.path.join(base, folder_name)
    
    os.makedirs(path, exist_ok=True)
    return path

def get_backup_path():
    """مسیر پوشه بکاپ"""
    return get_public_path('backup')

def get_export_path():
    """مسیر پوشه خروجی اکسل"""
    return get_public_path('export')

def get_import_path():
    """مسیر پوشه ورودی اکسل"""
    return get_public_path('import')

# ============================================================
# ✅ توابع JSON
# ============================================================

def load_json(filename):
    """بارگذاری فایل JSON"""
    try:
        path = os.path.join(get_data_path(), filename)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ خطا در بارگذاری {filename}: {e}")
    return {}

def save_json(filename, data):
    """ذخیره فایل JSON"""
    try:
        path = os.path.join(get_data_path(), filename)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ خطا در ذخیره {filename}: {e}")
        return False