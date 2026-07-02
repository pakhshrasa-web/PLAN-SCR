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
# ✅ توابع مسیردهی عمومی (با استفاده از پوشه Download)
# ============================================================

def _get_public_base_path():
    """دریافت مسیر پایه فضای عمومی - استفاده از Download در اندروید"""
    if platform == 'android':
        try:
            from android.storage import primary_external_storage_path
            base = primary_external_storage_path()
            if base:
                # ✅ استفاده از پوشه Download
                download_path = os.path.join(base, 'Download')
                print(f"✅ مسیر پایه عمومی: {download_path}")
                return download_path
        except Exception as e:
            print(f"⚠️ خطا در دریافت مسیر عمومی اندروید: {e}")
        # Fallback
        fallback = '/storage/emulated/0/Download/'
        print(f"⚠️ استفاده از Fallback: {fallback}")
        return fallback
    else:
        # ویندوز/دسکتاپ
        desktop_path = os.path.join(os.path.expanduser('~'), 'Downloads')
        print(f"✅ مسیر پایه دسکتاپ: {desktop_path}")
        return desktop_path

def get_public_path(folder_name):
    """
    دریافت مسیر پوشه در فضای عمومی
    folder_name: 'backup', 'export', 'import'
    """
    base = _get_public_base_path()
    
    # ✅ بررسی وجود مسیر پایه
    if not os.path.exists(base):
        print(f"⚠️ مسیر پایه وجود ندارد: {base}")
        try:
            os.makedirs(base, exist_ok=True)
            print(f"✅ مسیر پایه ایجاد شد: {base}")
        except Exception as e:
            print(f"❌ خطا در ایجاد مسیر پایه: {e}")
            # Fallback به پوشه داخلی
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
        # Fallback به پوشه داخلی اپ
        fallback_path = os.path.join(get_data_path(), folder_name)
        try:
            os.makedirs(fallback_path, exist_ok=True)
            print(f"✅ Fallback مسیر {folder_name}: {fallback_path}")
        except Exception as e2:
            print(f"❌ خطا در Fallback: {e2}")
            # آخرین راه‌حل: پوشه موقت
            import tempfile
            fallback_path = os.path.join(tempfile.gettempdir(), folder_name)
            os.makedirs(fallback_path, exist_ok=True)
            print(f"✅ Fallback نهایی {folder_name}: {fallback_path}")
        return fallback_path

def get_backup_path():
    """مسیر پوشه بکاپ"""
    return get_public_path('backup')

def get_export_path():
    """مسیر پوشه خروجی اکسل"""
    return get_public_path('export')

def get_import_path():
    """مسیر پوشه ورودی اکسل"""
    return get_public_path('import')

def get_public_download_path():
    """دریافت مسیر دانلود عمومی - با fallback"""
    base = _get_public_base_path()
    
    # ✅ بررسی وجود مسیر
    if not os.path.exists(base):
        print(f"⚠️ مسیر دانلود وجود ندارد: {base}")
        try:
            os.makedirs(base, exist_ok=True)
            print(f"✅ مسیر دانلود ایجاد شد: {base}")
        except Exception as e:
            print(f"❌ خطا در ایجاد مسیر دانلود: {e}")
            # Fallback به پوشه داخلی
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
                # Fallback به پوشه داخلی
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

# ✅ تابع تست سریع
def test_paths():
    """تست مسیرها"""
    print("\n" + "="*50)
    print("🧪 تست مسیرها:")
    print("="*50)
    print(f"Data path: {get_data_path()}")
    print(f"Base public: {_get_public_base_path()}")
    print(f"Download: {get_public_download_path()}")
    print(f"Backup: {get_backup_path()}")
    print(f"Export: {get_export_path()}")
    print(f"Import: {get_import_path()}")
    print("="*50)
    
    # تست نوشتن
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