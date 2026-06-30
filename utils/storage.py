"""
مدیریت ذخیره‌سازی داده‌ها در سیستم‌عامل‌های مختلف
"""

import os
import json
from kivy.utils import platform

_data_path = None

def init_data_path():
    """مقداردهی اولیه مسیر ذخیره‌سازی"""
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
        os.makedirs(os.path.join(_data_path, 'reports'), exist_ok=True)
        print(f"✅ پوشه‌ها در {_data_path} ایجاد شدند")
    except Exception as e:
        print(f"❌ خطا در ایجاد پوشه: {e}")
        _data_path = os.path.join(os.getcwd(), app_name)
        os.makedirs(_data_path, exist_ok=True)
    
    return _data_path

def get_data_path():
    """بازگرداندن مسیر ذخیره‌سازی"""
    global _data_path
    if _data_path is None:
        init_data_path()
    return _data_path

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

def get_reports_path():
    """دریافت مسیر پوشه گزارشات"""
    reports_path = os.path.join(get_data_path(), 'reports')
    os.makedirs(reports_path, exist_ok=True)
    return reports_path
