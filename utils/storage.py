"""
مدیریت ذخیره‌سازی داده‌ها - نسخه نهایی با Python IO
"""

import os
import json
from kivy.utils import platform
from kivy.logger import Logger as logger

# ============================================================
# ✅ کش مسیرها
# ============================================================

_cache = {
    'data_path': None,
    'app_import': None,
    'app_export': None,
    'app_backup': None,
    'public_import': None,
    'public_export': None,
    'public_backup': None,
}

# ============================================================
# ✅ مسیر ذخیره‌سازی داخلی اپ
# ============================================================

def init_data_path():
    """مقداردهی اولیه مسیر ذخیره‌سازی داخلی اپ"""
    if _cache['data_path'] is not None:
        return _cache['data_path']
    
    app_name = 'planandroid'
    
    if platform == 'android':
        try:
            from android.storage import app_storage_path
            path = app_storage_path()
            if path:
                _cache['data_path'] = path
                logger.info(f"✅ مسیر اندروید: {_cache['data_path']}")
            else:
                raise Exception("app_storage_path returned None")
        except Exception as e:
            logger.warning(f"⚠️ خطا در دریافت مسیر اندروید: {e}")
            _cache['data_path'] = '/data/data/org.pakhshrasa.planandroid/files'
    elif platform == 'win':
        _cache['data_path'] = os.path.join(os.environ.get('APPDATA', os.getcwd()), app_name)
        logger.info(f"✅ مسیر ویندوز: {_cache['data_path']}")
    elif platform in ('linux', 'macosx'):
        _cache['data_path'] = os.path.join(os.path.expanduser('~'), f'.{app_name}')
        logger.info(f"✅ مسیر لینوکس/مک: {_cache['data_path']}")
    else:
        _cache['data_path'] = os.path.join(os.getcwd(), app_name)
        logger.info(f"✅ مسیر پیش‌فرض: {_cache['data_path']}")
    
    try:
        os.makedirs(_cache['data_path'], exist_ok=True)
        logger.info(f"✅ پوشه داده ایجاد شد: {_cache['data_path']}")
    except Exception as e:
        logger.error(f"❌ خطا در ایجاد پوشه داده: {e}")
        _cache['data_path'] = os.path.join(os.getcwd(), app_name)
        os.makedirs(_cache['data_path'], exist_ok=True)
    
    return _cache['data_path']

def get_data_path():
    """بازگرداندن مسیر ذخیره‌سازی داخلی اپ"""
    if _cache['data_path'] is None:
        init_data_path()
    return _cache['data_path']

# ============================================================
# ✅ توابع مسیردهی پوشه شخصی برنامه
# ============================================================

def get_app_import_path():
    """دریافت مسیر پوشه import در داده‌های برنامه"""
    if _cache['app_import'] is None:
        path = os.path.join(get_data_path(), 'import')
        os.makedirs(path, exist_ok=True)
        _cache['app_import'] = path
        logger.info(f"✅ مسیر import (شخصی): {path}")
    return _cache['app_import']

def get_app_export_path():
    """دریافت مسیر پوشه export در داده‌های برنامه"""
    if _cache['app_export'] is None:
        path = os.path.join(get_data_path(), 'export')
        os.makedirs(path, exist_ok=True)
        _cache['app_export'] = path
        logger.info(f"✅ مسیر export (شخصی): {path}")
    return _cache['app_export']

def get_app_backup_path():
    """دریافت مسیر پوشه backup در داده‌های برنامه"""
    if _cache['app_backup'] is None:
        path = os.path.join(get_data_path(), 'backup')
        os.makedirs(path, exist_ok=True)
        _cache['app_backup'] = path
        logger.info(f"✅ مسیر backup (شخصی): {path}")
    return _cache['app_backup']

# ============================================================
# ✅ توابع مسیردهی عمومی
# ============================================================

def _get_public_base_path():
    """دریافت مسیر پایه عمومی (Download)"""
    if platform == 'android':
        try:
            from android.storage import primary_external_storage_path
            base = primary_external_storage_path()
            if base:
                return os.path.join(base, 'Download')
        except Exception as e:
            logger.warning(f"⚠️ خطا در دریافت مسیر عمومی: {e}")
        return '/storage/emulated/0/Download/'
    else:
        return os.path.join(os.path.expanduser('~'), 'Downloads')

def get_public_import_path():
    """دریافت مسیر عمومی import"""
    if _cache['public_import'] is None:
        path = os.path.join(_get_public_base_path(), 'plan_android_data', 'import')
        try:
            os.makedirs(path, exist_ok=True)
        except Exception as e:
            logger.warning(f"⚠️ خطا در ایجاد مسیر عمومی import: {e}")
        _cache['public_import'] = path
        logger.info(f"✅ مسیر عمومی import: {path}")
    return _cache['public_import']

def get_public_export_path():
    """دریافت مسیر عمومی export"""
    if _cache['public_export'] is None:
        path = os.path.join(_get_public_base_path(), 'plan_android_data', 'export')
        try:
            os.makedirs(path, exist_ok=True)
        except Exception as e:
            logger.warning(f"⚠️ خطا در ایجاد مسیر عمومی export: {e}")
        _cache['public_export'] = path
        logger.info(f"✅ مسیر عمومی export: {path}")
    return _cache['public_export']

def get_public_backup_path():
    """دریافت مسیر عمومی backup (در Download/PlanAndroid_Backup)"""
    if _cache['public_backup'] is None:
        path = os.path.join(_get_public_base_path(), 'PlanAndroid_Backup')
        try:
            os.makedirs(path, exist_ok=True)
        except Exception as e:
            logger.warning(f"⚠️ خطا در ایجاد مسیر عمومی backup: {e}")
        _cache['public_backup'] = path
        logger.info(f"✅ مسیر عمومی backup: {path}")
    return _cache['public_backup']

# ============================================================
# ✅ توابع اصلی (با تغییر در backup)
# ============================================================

def get_import_path():
    """دریافت مسیر import (در اندروید: شخصی، در دسکتاپ: عمومی)"""
    if platform == 'android':
        return get_app_import_path()
    else:
        return get_public_import_path()

def get_export_path():
    """دریافت مسیر export (در اندروید: عمومی، در دسکتاپ: عمومی)"""
    # ✅ تغییر: در اندروید هم به مسیر عمومی برود
    if platform == 'android':
        return get_public_export_path()  # ← تغییر مهم!
    else:
        return get_public_export_path()

def get_backup_path():
    """دریافت مسیر backup (در اندروید: عمومی، در دسکتاپ: شخصی)"""
    if platform == 'android':
        return get_public_backup_path()
    else:
        return get_app_backup_path()

# ============================================================
# ✅ تابع کپی با Python IO (ساده و مطمئن)
# ============================================================

def copy_uri_to_app_folder(uri, filename=None, target_folder='import', file_type='excel'):
    """
    کپی فایل از URI به پوشه شخصی برنامه با Python IO
    
    Args:
        uri: content:// URI (string یا Uri)
        filename: نام فایل (اختیاری)
        target_folder: 'import', 'export', 'backup'
        file_type: 'excel' یا 'backup' (برای پسوند پیش‌فرض)
    
    Returns:
        مسیر فایل کپی شده یا None
    """
    try:
        from android import mActivity
        from jnius import autoclass
        
        # ✅ تبدیل به Uri
        if isinstance(uri, str):
            Uri_class = autoclass("android.net.Uri")
            uri = Uri_class.parse(uri)
        
        # ✅ دریافت نام فایل
        if not filename:
            filename = _extract_filename_from_uri(uri, file_type)
        
        if not filename:
            logger.error("❌ نام فایل نامعتبر")
            return None
        
        # ✅ انتخاب پوشه مقصد
        if target_folder == 'import':
            dest_folder = get_app_import_path()  # ← اصلاح شده
        elif target_folder == 'export':
            dest_folder = get_app_export_path()
        elif target_folder == 'backup':
            dest_folder = get_app_backup_path()
        else:
            dest_folder = get_app_import_path()  # ← اصلاح شده
        
        # اطمینان از وجود پوشه مقصد
        os.makedirs(dest_folder, exist_ok=True)
        
        dest_path = os.path.join(dest_folder, filename)
        
        # ✅ کپی فایل با Python IO (ساده و مطمئن)
        logger.info(f"📂 کپی فایل: {uri} → {dest_path}")
        
        content_resolver = mActivity.getContentResolver()
        input_stream = content_resolver.openInputStream(uri)
        
        if not input_stream:
            logger.error("❌ نمی‌توان InputStream دریافت کرد")
            return None
        
        # ✅ کپی با بافر 8192
        try:
            with open(dest_path, 'wb') as output_file:
                buffer = bytearray(8192)
                while True:
                    try:
                        count = input_stream.read(buffer)
                        if count <= 0:
                            break
                        output_file.write(buffer[:count])
                    except TypeError:
                        # روش جایگزین برای برخی دستگاه‌ها
                        while True:
                            data = input_stream.read()
                            if data == -1:
                                break
                            output_file.write(bytes([data]))
                        break
        finally:
            # بستن InputStream
            try:
                input_stream.close()
            except:
                pass
        
        # ✅ بررسی نتیجه
        if os.path.exists(dest_path):
            size = os.path.getsize(dest_path)
            logger.info(f"✅ فایل با موفقیت کپی شد: {dest_path} ({size} bytes)")
            return dest_path
        else:
            logger.error("❌ فایل کپی نشد")
            return None
        
    except Exception as e:
        logger.error(f"❌ خطا در کپی URI: {e}")
        import traceback
        traceback.print_exc()
        return None
    
# utils/storage.py - اضافه کن

def delete_old_backup_files(days=30):
    """حذف فایل‌های اکسل قدیمی‌تر از تعداد روز مشخص"""
    try:
        backup_path = get_backup_path()
        if not os.path.exists(backup_path):
            return 0
        
        now = time.time()
        deleted_count = 0
        cutoff_time = now - (days * 86400)
        
        for file in os.listdir(backup_path):
            if file.endswith('.xlsx') and file.startswith('گزارش_فروش_'):
                file_path = os.path.join(backup_path, file)
                try:
                    if os.path.getmtime(file_path) < cutoff_time:
                        os.remove(file_path)
                        deleted_count += 1
                        logger.info(f"🗑️ فایل قدیمی حذف شد: {file}")
                except Exception as e:
                    logger.error(f"❌ خطا در حذف فایل {file}: {e}")
                    continue
        
        return deleted_count
        
    except Exception as e:
        logger.error(f"❌ خطا در حذف فایل‌های قدیمی: {e}")
        return 0

def _extract_filename_from_uri(uri, file_type='excel'):
    """
    استخراج نام فایل از URI با OpenableColumns
    
    Args:
        uri: content:// URI
        file_type: 'excel' یا 'backup' (برای پسوند پیش‌فرض)
    
    Returns:
        نام فایل یا None
    """
    try:
        from android import mActivity
        from android.provider import OpenableColumns
        from jnius import autoclass
        
        # ✅ تبدیل به Uri
        if isinstance(uri, str):
            Uri_class = autoclass("android.net.Uri")
            uri = Uri_class.parse(uri)
        
        content_resolver = mActivity.getContentResolver()
        
        # ✅ روش ۱: OpenableColumns.DISPLAY_NAME (بهترین روش)
        try:
            cursor = content_resolver.query(
                uri,
                [OpenableColumns.DISPLAY_NAME],
                None,
                None,
                None
            )
            if cursor and cursor.moveToFirst():
                name_index = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                if name_index >= 0:
                    filename = cursor.getString(name_index)
                    cursor.close()
                    if filename:
                        logger.info(f"✅ نام فایل از cursor: {filename}")
                        return filename
            if cursor:
                cursor.close()
        except Exception as e:
            logger.warning(f"⚠️ خطا در OpenableColumns: {e}")
        
        # ✅ روش ۲: استخراج از URI
        import urllib.parse
        raw = str(uri)
        if '%' in raw:
            raw = urllib.parse.unquote(raw)
        
        filename = raw.split('/')[-1]
        if '?' in filename:
            filename = filename.split('?')[0]
        
        if filename and '.' in filename:
            logger.info(f"✅ نام فایل از Uri: {filename}")
            return filename
        
        # ✅ روش ۳: نام پیش‌فرض با پسوند مناسب
        import hashlib
        hash_val = hashlib.md5(str(uri).encode()).hexdigest()[:8]
        
        if file_type == 'excel':
            filename = f"file_{hash_val}.xlsx"
        elif file_type == 'backup':
            filename = f"file_{hash_val}.zip"
        else:
            filename = f"file_{hash_val}.dat"
        
        logger.info(f"✅ نام فایل پیش‌فرض: {filename}")
        return filename
        
    except Exception as e:
        logger.warning(f"⚠️ خطا در استخراج نام فایل: {e}")
        return None

# ============================================================
# ✅ توابع JSON
# ============================================================

def load_json(filename):
    """بارگذاری فایل JSON از پوشه داده"""
    try:
        path = os.path.join(get_data_path(), filename)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"⚠️ خطا در بارگذاری {filename}: {e}")
    return {}

def save_json(filename, data):
    """ذخیره فایل JSON در پوشه داده"""
    try:
        path = os.path.join(get_data_path(), filename)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"❌ خطا در ذخیره {filename}: {e}")
        return False

# ============================================================
# ✅ تابع تست
# ============================================================

def test_paths():
    """تست تمام مسیرها"""
    print("\n" + "="*50)
    print("🧪 تست مسیرها:")
    print("="*50)
    print(f"Data path: {get_data_path()}")
    print(f"App Import: {get_app_import_path()}")
    print(f"App Export: {get_app_export_path()}")
    print(f"App Backup: {get_app_backup_path()}")
    print(f"Public Import: {get_public_import_path()}")
    print(f"Public Export: {get_public_export_path()}")
    print(f"Public Backup: {get_public_backup_path()}")
    print(f"Import (main): {get_import_path()}")
    print(f"Export (main): {get_export_path()}")
    print(f"Backup (main): {get_backup_path()}")
    print("="*50)

# ============================================================
# ✅ اجرای تست در صورت اجرای مستقیم
# ============================================================

if __name__ == '__main__':
    test_paths()