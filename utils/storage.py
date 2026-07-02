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
# ✅ توابع مسیردهی پوشه شخصی برنامه (دسترسی کامل در اندروید)
# ============================================================

def get_app_import_path():
    """مسیر پوشه import در پوشه شخصی برنامه"""
    path = os.path.join(get_data_path(), 'import')
    os.makedirs(path, exist_ok=True)
    print(f"✅ مسیر import (شخصی): {path}")
    return path

def get_app_export_path():
    """مسیر پوشه export در پوشه شخصی برنامه"""
    path = os.path.join(get_data_path(), 'export')
    os.makedirs(path, exist_ok=True)
    print(f"✅ مسیر export (شخصی): {path}")
    return path

def get_app_backup_path():
    """مسیر پوشه backup در پوشه شخصی برنامه"""
    path = os.path.join(get_data_path(), 'backup')
    os.makedirs(path, exist_ok=True)
    print(f"✅ مسیر backup (شخصی): {path}")
    return path

# ============================================================
# ✅ توابع مسیردهی عمومی (برای نمایش به کاربر در ویندوز)
# ============================================================

def _get_public_base_path():
    """دریافت مسیر پایه فضای عمومی"""
    if platform == 'android':
        try:
            from android.storage import primary_external_storage_path
            base = primary_external_storage_path()
            if base:
                download_path = os.path.join(base, 'Download')
                print(f"✅ مسیر پایه عمومی: {download_path}")
                return download_path
        except Exception as e:
            print(f"⚠️ خطا در دریافت مسیر عمومی: {e}")
        fallback = '/storage/emulated/0/Download/'
        print(f"⚠️ استفاده از Fallback: {fallback}")
        return fallback
    else:
        desktop_path = os.path.join(os.path.expanduser('~'), 'Downloads')
        print(f"✅ مسیر پایه دسکتاپ: {desktop_path}")
        return desktop_path

def get_public_path(folder_name):
    """دریافت مسیر پوشه در فضای عمومی"""
    base = _get_public_base_path()
    
    if not os.path.exists(base):
        print(f"⚠️ مسیر پایه وجود ندارد: {base}")
        try:
            os.makedirs(base, exist_ok=True)
            print(f"✅ مسیر پایه ایجاد شد: {base}")
        except Exception as e:
            print(f"❌ خطا در ایجاد مسیر پایه: {e}")
            fallback_path = os.path.join(get_data_path(), folder_name)
            os.makedirs(fallback_path, exist_ok=True)
            print(f"✅ Fallback مسیر {folder_name}: {fallback_path}")
            return fallback_path
    
    path = os.path.join(base, 'plan_android_data', folder_name)
    
    try:
        os.makedirs(path, exist_ok=True)
        print(f"✅ مسیر عمومی {folder_name}: {path}")
        return path
    except Exception as e:
        print(f"⚠️ خطا در ایجاد مسیر {folder_name}: {e}")
        fallback_path = os.path.join(get_data_path(), folder_name)
        try:
            os.makedirs(fallback_path, exist_ok=True)
            print(f"✅ Fallback مسیر {folder_name}: {fallback_path}")
        except Exception as e2:
            print(f"❌ خطا در Fallback: {e2}")
            import tempfile
            fallback_path = os.path.join(tempfile.gettempdir(), folder_name)
            os.makedirs(fallback_path, exist_ok=True)
            print(f"✅ Fallback نهایی {folder_name}: {fallback_path}")
        return fallback_path

# ============================================================
# ✅ توابع اصلی (با اولویت پوشه شخصی در اندروید)
# ============================================================

def get_import_path():
    """دریافت مسیر import - در اندروید از پوشه شخصی استفاده می‌کند"""
    if platform == 'android':
        return get_app_import_path()
    else:
        return get_public_path('import')

def get_export_path():
    """دریافت مسیر export - در اندروید از پوشه شخصی استفاده می‌کند"""
    if platform == 'android':
        return get_app_export_path()
    else:
        return get_public_path('export')

def get_backup_path():
    """دریافت مسیر backup - در اندروید از پوشه شخصی استفاده می‌کند"""
    if platform == 'android':
        return get_app_backup_path()
    else:
        return get_public_path('backup')

def get_public_download_path():
    """دریافت مسیر دانلود عمومی"""
    base = _get_public_base_path()
    
    if not os.path.exists(base):
        print(f"⚠️ مسیر دانلود وجود ندارد: {base}")
        try:
            os.makedirs(base, exist_ok=True)
            print(f"✅ مسیر دانلود ایجاد شد: {base}")
        except Exception as e:
            print(f"❌ خطا در ایجاد مسیر دانلود: {e}")
            fallback = get_data_path()
            print(f"✅ استفاده از Fallback: {fallback}")
            return fallback
    
    return base

def ensure_public_dirs():
    """اطمینان از وجود پوشه‌های عمومی"""
    print("🔍 بررسی پوشه‌های عمومی...")
    
    created_count = 0
    for folder in ['backup', 'export', 'import']:
        path = get_public_path(folder)
        if os.path.exists(path):
            print(f"✅ پوشه {folder} وجود دارد: {path}")
        else:
            try:
                os.makedirs(path, exist_ok=True)
                print(f"✅ پوشه {folder} ایجاد شد: {path}")
                created_count += 1
            except Exception as e:
                print(f"⚠️ خطا در ایجاد {folder}: {e}")
                fallback = os.path.join(get_data_path(), folder)
                try:
                    os.makedirs(fallback, exist_ok=True)
                    print(f"✅ Fallback {folder} ایجاد شد: {fallback}")
                except Exception as e2:
                    print(f"❌ خطا در Fallback {folder}: {e2}")
    
    print(f"✅ {created_count} پوشه جدید ایجاد شد")
    return created_count > 0

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

def test_paths():
    """تست مسیرها"""
    print("\n" + "="*50)
    print("🧪 تست مسیرها:")
    print("="*50)
    print(f"Data path: {get_data_path()}")
    print(f"Import path: {get_import_path()}")
    print(f"Export path: {get_export_path()}")
    print(f"Backup path: {get_backup_path()}")
    print("="*50)
    
    test_path = get_export_path()
    test_file = os.path.join(test_path, "test.txt")
    try:
        with open(test_file, 'w') as f:
            f.write("Test successful!")
        print(f"✅ فایل تست ایجاد شد: {test_file}")
        os.remove(test_file)
        print(f"✅ فایل تست پاک شد")
    except Exception as e:
        print(f"❌ خطا در تست: {e}")
