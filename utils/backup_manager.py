"""
مدیریت بکاپ و بازیابی - نسخه مستقل
"""

import os
import zipfile
from datetime import datetime
from kivy.logger import Logger as logger
from utils.storage import get_data_path, get_backup_path


def create_backup():
    """
    ایجاد بکاپ از تمام داده‌ها
    
    Returns:
        (success: bool, message: str, backup_path: str or None)
    """
    try:
        data_path = get_data_path()
        backup_dir = get_backup_path()
        
        # ✅ ایجاد پوشه بکاپ
        os.makedirs(backup_dir, exist_ok=True)
        
        # ✅ ایجاد نام فایل
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'backup_{timestamp}.zip')
        
        logger.info(f"📂 ایجاد بکاپ: {backup_file}")
        
        # ✅ لیست فایل‌ها
        files_to_backup = []
        
        # دیتابیس
        db_path = os.path.join(data_path, 'planandroid.db')
        if os.path.exists(db_path):
            files_to_backup.append(('planandroid.db', db_path))
            logger.info(f"✅ دیتابیس پیدا شد: {db_path}")
        
        # فایل‌های JSON
        for filename in os.listdir(data_path):
            if filename.endswith('.json'):
                filepath = os.path.join(data_path, filename)
                files_to_backup.append((filename, filepath))
                logger.info(f"✅ فایل JSON: {filename}")
        
        if not files_to_backup:
            return False, "هیچ داده‌ای برای بکاپ وجود ندارد!", None
        
        # ✅ ایجاد ZIP
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for arcname, filepath in files_to_backup:
                zipf.write(filepath, arcname)
                logger.debug(f"📦 اضافه شد: {arcname}")
        
        # ✅ بررسی فایل
        if os.path.exists(backup_file):
            file_size = os.path.getsize(backup_file)
            logger.info(f"✅ بکاپ ایجاد شد: {backup_file} ({file_size} bytes)")
            return True, f"بکاپ با موفقیت ایجاد شد!\n\n📁 {os.path.basename(backup_file)}\n📊 حجم: {file_size // 1024} KB", backup_file
        else:
            return False, "فایل بکاپ ایجاد نشد!", None
            
    except Exception as e:
        logger.error(f"❌ خطا در ایجاد بکاپ: {e}")
        import traceback
        traceback.print_exc()
        return False, f"خطا: {str(e)}", None


def validate_backup_file(backup_path):
    """
    اعتبارسنجی فایل بکاپ
    
    Returns:
        (is_valid: bool, message: str, files: list or None)
    """
    if not backup_path:
        return False, "مسیر فایل نامعتبر است", None
    
    if not os.path.exists(backup_path):
        return False, "فایل وجود ندارد", None
    
    if not backup_path.lower().endswith('.zip'):
        return False, "فایل باید با فرمت .zip باشد", None
    
    try:
        # ✅ بررسی محتوای ZIP
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            file_list = zipf.namelist()
            
            # بررسی وجود فایل‌های ضروری
            has_json = any(f.endswith('.json') for f in file_list)
            has_db = 'planandroid.db' in file_list
            
            if not has_json and not has_db:
                return False, "فایل بکاپ معتبر نیست (هیچ داده‌ای پیدا نشد)", None
            
            logger.info(f"✅ فایل بکاپ معتبر است: {len(file_list)} فایل")
            return True, f"فایل معتبر است ({len(file_list)} فایل)", file_list
            
    except zipfile.BadZipFile:
        return False, "فایل بکاپ خراب است", None
    except Exception as e:
        return False, f"خطا در بررسی فایل: {str(e)}", None


def restore_backup(backup_path):
    """
    بازیابی داده‌ها از فایل بکاپ
    
    Returns:
        (success: bool, message: str)
    """
    try:
        # ✅ اعتبارسنجی فایل
        is_valid, msg, file_list = validate_backup_file(backup_path)
        if not is_valid:
            return False, msg
        
        data_path = get_data_path()
        backup_dir = get_backup_path()
        logger.info(f"📂 بازیابی به: {data_path}")
        
        # ✅ ایجاد بکاپ از داده‌های فعلی (قبل از بازیابی) در پوشه بکاپ
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        os.makedirs(backup_dir, exist_ok=True)
        pre_restore_backup = os.path.join(backup_dir, f'pre_restore_{timestamp}.zip')
        
        files_to_backup = []
        for filename in os.listdir(data_path):
            if filename.endswith('.json') or filename == 'planandroid.db':
                filepath = os.path.join(data_path, filename)
                files_to_backup.append((filename, filepath))
        
        if files_to_backup:
            with zipfile.ZipFile(pre_restore_backup, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for arcname, filepath in files_to_backup:
                    zipf.write(filepath, arcname)
                    logger.debug(f"📦 بکاپ پیش از بازیابی: {arcname}")
            logger.info(f"✅ بکاپ از داده‌های فعلی ایجاد شد: {pre_restore_backup}")
        
        # ✅ استخراج فایل بکاپ
        logger.info(f"📂 استخراج فایل بکاپ: {backup_path}")
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            zipf.extractall(data_path)
            extracted = zipf.namelist()
            logger.info(f"📦 فایل‌های استخراج شده: {extracted}")
        
        return True, "داده‌ها با موفقیت بازیابی شدند!\n\nاپلیکیشن مجدداً راه‌اندازی خواهد شد."
        
    except Exception as e:
        logger.error(f"❌ خطا در بازیابی: {e}")
        import traceback
        traceback.print_exc()
        return False, f"خطا در بازیابی: {str(e)}"