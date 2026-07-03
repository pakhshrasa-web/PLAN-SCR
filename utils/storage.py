"""
مدیریت ذخیره‌سازی داده‌ها - نسخه بازنویسی شده با معماری تمیز
"""

import os
import json
from kivy.utils import platform
from kivy.logger import Logger as logger

# ============================================================
# ✅ کش مسیرها (برای جلوگیری از تکرار os.makedirs)
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
# ✅ مسیر ذخیره‌سازی داخلی اپ (دیتابیس و JSON)
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
                _cache['data_path'] = os.path.join(path, app_name)
                logger.info(f"✅ مسیر اندروید: {_cache['data_path']}")
            else:
                raise Exception("app_storage_path returned None")
        except Exception as e:
            logger.warning(f"⚠️ خطا در دریافت مسیر اندروید: {e}")
            _cache['data_path'] = os.path.join('/data/data/org.pakhshrasa.planandroid/files', app_name)
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
    """بازگرداندن مسیر ذخیره‌سازی داخلی اپ (برای دیتابیس و JSON)"""
    if _cache['data_path'] is None:
        init_data_path()
    return _cache['data_path']

# ============================================================
# ✅ توابع مسیردهی پوشه شخصی برنامه (دسترسی کامل در اندروید)
# ============================================================

def get_app_import_path():
    """مسیر پوشه import در پوشه شخصی برنامه"""
    if _cache['app_import'] is None:
        path = os.path.join(get_data_path(), 'import')
        os.makedirs(path, exist_ok=True)
        _cache['app_import'] = path
        logger.info(f"✅ مسیر import (شخصی): {path}")
    return _cache['app_import']

def get_app_export_path():
    """مسیر پوشه export در پوشه شخصی برنامه"""
    if _cache['app_export'] is None:
        path = os.path.join(get_data_path(), 'export')
        os.makedirs(path, exist_ok=True)
        _cache['app_export'] = path
        logger.info(f"✅ مسیر export (شخصی): {path}")
    return _cache['app_export']

def get_app_backup_path():
    """مسیر پوشه backup در پوشه شخصی برنامه"""
    if _cache['app_backup'] is None:
        path = os.path.join(get_data_path(), 'backup')
        os.makedirs(path, exist_ok=True)
        _cache['app_backup'] = path
        logger.info(f"✅ مسیر backup (شخصی): {path}")
    return _cache['app_backup']

# ============================================================
# ✅ توابع مسیردهی عمومی (برای نمایش به کاربر)
# ============================================================

def _get_public_base_path():
    """دریافت مسیر پایه فضای عمومی"""
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
    """مسیر عمومی import (فقط برای نمایش به کاربر)"""
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
    """مسیر عمومی export (فقط برای نمایش به کاربر)"""
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
    """مسیر عمومی backup (فقط برای نمایش به کاربر)"""
    if _cache['public_backup'] is None:
        path = os.path.join(_get_public_base_path(), 'plan_android_data', 'backup')
        try:
            os.makedirs(path, exist_ok=True)
        except Exception as e:
            logger.warning(f"⚠️ خطا در ایجاد مسیر عمومی backup: {e}")
        _cache['public_backup'] = path
        logger.info(f"✅ مسیر عمومی backup: {path}")
    return _cache['public_backup']

# ============================================================
# ✅ توابع اصلی (با اولویت پوشه شخصی در اندروید)
# ============================================================

def get_import_path():
    """دریافت مسیر import - در اندروید از پوشه شخصی استفاده می‌کند"""
    if platform == 'android':
        return get_app_import_path()
    else:
        return get_public_import_path()

def get_export_path():
    """دریافت مسیر export - در اندروید از پوشه شخصی استفاده می‌کند"""
    if platform == 'android':
        return get_app_export_path()
    else:
        return get_public_export_path()

def get_backup_path():
    """دریافت مسیر backup - در اندروید از پوشه شخصی استفاده می‌کند"""
    if platform == 'android':
        return get_app_backup_path()
    else:
        return get_public_backup_path()

# ============================================================
# ✅ تابع اصلی برای تبدیل content:// به فایل واقعی
# ============================================================

def copy_uri_to_app_folder(uri, filename=None, target_folder='import'):
    """
    کپی فایل از URI به پوشه شخصی برنامه
    این تابع تنها نقطه ارتباط با ContentResolver است
    
    Args:
        uri: content:// URI
        filename: نام فایل (اگر None باشد از URI استخراج می‌شود)
        target_folder: 'import', 'export', 'backup'
    
    Returns:
        مسیر فایل کپی شده یا None در صورت خطا
    """
    try:
        from android import mActivity
        from android.permissions import request_permissions, Permission
        
        logger.info(f"📂 کپی URI به پوشه {target_folder}: {uri}")
        
        # ✅ درخواست دسترسی
        request_permissions([
            Permission.READ_EXTERNAL_STORAGE,
            Permission.WRITE_EXTERNAL_STORAGE
        ])
        
        # ✅ دریافت نام فایل
        if not filename:
            filename = _extract_filename_from_uri(uri)
        
        if not filename:
            logger.error("❌ نام فایل نامعتبر")
            return None
        
        # ✅ دریافت مسیر مقصد
        if target_folder == 'import':
            dest_folder = get_app_import_path()
        elif target_folder == 'export':
            dest_folder = get_app_export_path()
        elif target_folder == 'backup':
            dest_folder = get_app_backup_path()
        else:
            dest_folder = get_app_import_path()
        
        dest_path = os.path.join(dest_folder, filename)
        
        # ✅ کپی فایل با ContentResolver
        content_resolver = mActivity.getContentResolver()
        input_stream = content_resolver.openInputStream(uri)
        
        if not input_stream:
            logger.error("❌ نمی‌توان InputStream دریافت کرد")
            return None
        
        with input_stream:
            with open(dest_path, 'wb') as output_file:
                buffer = bytearray(8192)
                while True:
                    bytes_read = input_stream.read(buffer)
                    if bytes_read == -1:
                        break
                    output_file.write(buffer[:bytes_read])
        
        logger.info(f"✅ فایل با موفقیت کپی شد: {dest_path}")
        return dest_path
        
    except Exception as e:
        logger.error(f"❌ خطا در کپی URI: {e}")
        import traceback
        traceback.print_exc()
        return None

def _extract_filename_from_uri(uri):
    """استخراج نام فایل از URI با استفاده از ContentResolver"""
    try:
        from android import mActivity
        from android.provider import MediaStore, DocumentsContract
        
        # ✅ روش ۱: استفاده از MediaStore
        projection = [MediaStore.MediaColumns.DISPLAY_NAME]
        
        try:
            cursor = mActivity.getContentResolver().query(
                uri,
                projection,
                None,
                None,
                None
            )
            if cursor and cursor.moveToFirst():
                filename = cursor.getString(0)
                cursor.close()
                if filename:
                    return filename
        except Exception as e:
            logger.warning(f"⚠️ خطا در دریافت نام فایل: {e}")
        
        # ✅ روش ۲: استخراج از URI
        import urllib.parse
        raw = str(uri)
        if '%' in raw:
            raw = urllib.parse.unquote(raw)
        
        # گرفتن آخرین بخش
        filename = raw.split('/')[-1]
        
        # حذف پارامترها
        if '?' in filename:
            filename = filename.split('?')[0]
        
        return filename
        
    except Exception as e:
        logger.warning(f"⚠️ خطا در استخراج نام فایل: {e}")
        return str(uri).split('/')[-1]

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
        logger.warning(f"⚠️ خطا در بارگذاری {filename}: {e}")
    return {}

def save_json(filename, data):
    """ذخیره فایل JSON"""
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
    """تست مسیرها"""
    print("\n" + "="*50)
    print("🧪 تست مسیرها:")
    print("="*50)
    print(f"Data path: {get_data_path()}")
    print(f"Import path: {get_import_path()}")
    print(f"Export path: {get_export_path()}")
    print(f"Backup path: {get_backup_path()}")
    print("="*50)