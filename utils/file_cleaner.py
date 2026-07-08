"""
مدیریت پاکسازی فایل‌ها - نسخه اختصاصی برای ReportScreen
"""

import os
import time
from typing import List, Dict, Tuple
from kivy.logger import Logger as logger
from utils.storage import get_backup_path

# ============================================================
# ✅ توابع پاکسازی
# ============================================================

def get_excel_files_info(limit: int = 50) -> List[Dict]:
    """
    دریافت اطلاعات فایل‌های اکسل موجود در پوشه بکاپ
    
    Args:
        limit (int): حداکثر تعداد فایل‌ها
        
    Returns:
        List[Dict]: لیست اطلاعات فایل‌ها
    """
    try:
        backup_path = get_backup_path()
        if not os.path.exists(backup_path):
            logger.warning(f" پوشه بکاپ وجود ندارد: {backup_path}")
            return []
        
        files_info = []
        
        for file in os.listdir(backup_path):
            # فقط فایل‌های اکسل گزارش
            if file.endswith('.xlsx') and file.startswith('گزارش_فروش_'):
                file_path = os.path.join(backup_path, file)
                try:
                    stat = os.stat(file_path)
                    
                    # استخراج تاریخ از نام فایل
                    date_part = file.replace('گزارش_فروش_', '').replace('.xlsx', '')
                    
                    files_info.append({
                        'name': file,
                        'path': file_path,
                        'size_bytes': stat.st_size,
                        'size_kb': round(stat.st_size / 1024, 1),
                        'size_mb': round(stat.st_size / (1024 * 1024), 2),
                        'modified': stat.st_mtime,
                        'date': date_part,
                        'type': 'excel'
                    })
                except Exception as e:
                    logger.error(f" خطا در خواندن اطلاعات فایل {file}: {e}")
                    continue
        
        # مرتب‌سازی بر اساس تاریخ (جدیدترین اول)
        files_info.sort(key=lambda x: x['modified'], reverse=True)
        
        # محدود کردن تعداد
        result = files_info[:limit]
        logger.info(f" {len(result)} فایل اکسل یافت شد")
        return result
        
    except Exception as e:
        logger.error(f" خطا در دریافت اطلاعات فایل‌ها: {e}")
        return []

def delete_files(file_paths: List[str]) -> Tuple[int, int]:
    """
    حذف فایل‌های مشخص شده
    
    Args:
        file_paths (List[str]): لیست مسیرهای فایل‌ها
        
    Returns:
        Tuple[int, int]: (تعداد حذف شده, تعداد خطا)
    """
    if not file_paths:
        logger.warning(" لیست فایل‌ها خالی است")
        return 0, 0
    
    deleted = 0
    failed = 0
    failed_files = []
    
    for file_path in file_paths:
        try:
            if not os.path.exists(file_path):
                logger.warning(f" فایل وجود ندارد: {file_path}")
                failed += 1
                failed_files.append(file_path)
                continue
            
            os.remove(file_path)
            deleted += 1
            logger.info(f" فایل حذف شد: {os.path.basename(file_path)}")
            
        except Exception as e:
            logger.error(f" خطا در حذف فایل {file_path}: {e}")
            failed += 1
            failed_files.append(file_path)
    
    logger.info(f" حذف کامل شد: {deleted} موفق, {failed} ناموفق")
    return deleted, failed

def delete_old_files(days: int = 30) -> Tuple[int, int]:
    """
    حذف فایل‌های قدیمی‌تر از تعداد روز مشخص
    
    Args:
        days (int): تعداد روز نگهداری فایل‌ها
        
    Returns:
        Tuple[int, int]: (تعداد حذف شده, تعداد خطا)
    """
    try:
        backup_path = get_backup_path()
        if not os.path.exists(backup_path):
            logger.warning(f" پوشه بکاپ وجود ندارد: {backup_path}")
            return 0, 0
        
        now = time.time()
        deleted = 0
        failed = 0
        cutoff_time = now - (days * 86400)  # 86400 = 24*60*60
        
        for file in os.listdir(backup_path):
            # فقط فایل‌های اکسل گزارش
            if file.endswith('.xlsx') and file.startswith('گزارش_فروش_'):
                file_path = os.path.join(backup_path, file)
                try:
                    if os.path.getmtime(file_path) < cutoff_time:
                        os.remove(file_path)
                        deleted += 1
                        logger.info(f" فایل قدیمی حذف شد: {file}")
                except Exception as e:
                    logger.error(f" خطا در حذف فایل {file}: {e}")
                    failed += 1
        
        logger.info(f"✅ پاکسازی قدیمی‌ها: {deleted} فایل حذف شد, {failed} خطا")
        return deleted, failed
        
    except Exception as e:
        logger.error(f" خطا در حذف فایل‌های قدیمی: {e}")
        return 0, 1

def get_total_size() -> float:
    """
    محاسبه حجم کل فایل‌های اکسل
    
    Returns:
        float: حجم کل به مگابایت
    """
    try:
        backup_path = get_backup_path()
        if not os.path.exists(backup_path):
            return 0
        
        total_size = 0
        file_count = 0
        
        for file in os.listdir(backup_path):
            if file.endswith('.xlsx') and file.startswith('گزارش_فروش_'):
                file_path = os.path.join(backup_path, file)
                try:
                    total_size += os.path.getsize(file_path)
                    file_count += 1
                except Exception as e:
                    logger.error(f"❌ خطا در خواندن حجم فایل {file}: {e}")
                    continue
        
        size_mb = round(total_size / (1024 * 1024), 2)
        logger.info(f" حجم کل فایل‌ها: {size_mb} MB ({file_count} فایل)")
        return size_mb
        
    except Exception as e:
        logger.error(f" خطا در محاسبه حجم کل: {e}")
        return 0

def get_file_stats() -> Dict:
    """
    دریافت آمار کامل فایل‌ها
    
    Returns:
        Dict: آمار شامل تعداد، حجم، قدیمی‌ترین و جدیدترین فایل
    """
    try:
        backup_path = get_backup_path()
        if not os.path.exists(backup_path):
            return {
                'count': 0,
                'total_size_mb': 0,
                'oldest_date': None,
                'newest_date': None,
                'oldest_file': None,
                'newest_file': None
            }
        
        files = []
        for file in os.listdir(backup_path):
            if file.endswith('.xlsx') and file.startswith('گزارش_فروش_'):
                file_path = os.path.join(backup_path, file)
                try:
                    stat = os.stat(file_path)
                    files.append({
                        'name': file,
                        'path': file_path,
                        'size': stat.st_size,
                        'modified': stat.st_mtime
                    })
                except:
                    continue
        
        if not files:
            return {
                'count': 0,
                'total_size_mb': 0,
                'oldest_date': None,
                'newest_date': None,
                'oldest_file': None,
                'newest_file': None
            }
        
        files.sort(key=lambda x: x['modified'])
        total_size = sum(f['size'] for f in files)
        
        return {
            'count': len(files),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'oldest_date': files[0]['name'].replace('گزارش_فروش_', '').replace('.xlsx', ''),
            'newest_date': files[-1]['name'].replace('گزارش_فروش_', '').replace('.xlsx', ''),
            'oldest_file': files[0]['name'],
            'newest_file': files[-1]['name']
        }
        
    except Exception as e:
        logger.error(f" خطا در دریافت آمار: {e}")
        return {
            'count': 0,
            'total_size_mb': 0,
            'oldest_date': None,
            'newest_date': None,
            'oldest_file': None,
            'newest_file': None
        }

# ============================================================
# ✅ تابع تست
# ============================================================

def test_cleaner():
    """تست توابع پاکسازی"""
    print("\n" + "="*50)
    print(" تست توابع پاکسازی:")
    print("="*50)
    
    # آمار
    stats = get_file_stats()
    print(f" آمار فایل‌ها:")
    print(f"  - تعداد: {stats['count']}")
    print(f"  - حجم کل: {stats['total_size_mb']} MB")
    print(f"  - قدیمی‌ترین: {stats['oldest_date']}")
    print(f"  - جدیدترین: {stats['newest_date']}")
    
    # لیست فایل‌ها
    files = get_excel_files_info(limit=5)
    print(f"\n ۵ فایل آخر:")
    for f in files:
        print(f"  - {f['date']} ({f['size_kb']} KB)")
    
    print("="*50)

if __name__ == '__main__':
    test_cleaner()