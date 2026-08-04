# utils/data_manager.py
# ========== مدیریت مرکزی داده‌ها ==========
"""
این ماژول مسئول مدیریت یکپارچه خواندن و نوشتن داده‌ها در فایل‌های JSON است.
با استفاده از کش، سرعت برنامه را افزایش می‌دهد و کدهای تکراری را حذف می‌کند.
"""

import os
import json
import time
from typing import Any, Dict, List, Optional, Union
from utils.storage import get_data_path
from utils.file_manager import get_app_backup_path  # فقط این رو import میکنیم


class DataManager:
    """
    کلاس مدیریت مرکزی داده‌ها با قابلیت کشینگ
    
    ویژگی‌ها:
    - خواندن/نوشتن خودکار فایل‌های JSON
    - کش هوشمند برای افزایش سرعت
    - مدیریت خطاهای رایج
    - پشتیبان‌گیری خودکار
    - امکان بی‌اعتبارسازی کش
    """
    
    _cache: Dict[str, Any] = {}
    _cache_time: Dict[str, float] = {}
    _cache_ttl: int = 300  # زمان انقضای کش به ثانیه (پیش‌فرض: ۵ دقیقه)
    _max_cache_size: int = 50  # حداکثر تعداد فایل‌های کش شده
    
    @classmethod
    def load(cls, filename: str, use_cache: bool = True, cache_ttl: Optional[int] = None) -> List[Any]:
        """
        بارگذاری داده‌ها از فایل JSON
        
        Args:
            filename: نام فایل (مثلاً 'users.json')
            use_cache: استفاده از کش (پیش‌فرض True)
            cache_ttl: زمان انقضای کش به ثانیه (اگر None باشد از مقدار پیش‌فرض استفاده می‌شود)
        
        Returns:
            List[Any]: لیست داده‌های بارگذاری شده، در صورت خطا لیست خالی برمی‌گردد
        
        Examples:
            >>> users = DataManager.load('users.json')
            >>> settings = DataManager.load('settings.json', cache_ttl=60)
        """
        try:
            # تعیین زمان انقضای کش
            ttl = cache_ttl if cache_ttl is not None else cls._cache_ttl
            
            # بررسی وجود در کش
            if use_cache and filename in cls._cache:
                # بررسی زمان انقضا
                if time.time() - cls._cache_time.get(filename, 0) < ttl:
                    return cls._cache[filename]
                else:
                    # کش منقضی شده، حذف می‌کنیم
                    del cls._cache[filename]
                    if filename in cls._cache_time:
                        del cls._cache_time[filename]
            
            # خواندن از دیسک
            path = os.path.join(get_data_path(), filename)
            
            if not os.path.exists(path):
                # فایل وجود ندارد، لیست خالی برمی‌گردانیم
                empty_data = []
                if use_cache:
                    cls._add_to_cache(filename, empty_data)
                return empty_data
            
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # اگر داده لیست نبود، به لیست تبدیل می‌کنیم
            if not isinstance(data, list):
                data = [data] if data else []
            
            # ذخیره در کش
            if use_cache:
                cls._add_to_cache(filename, data)
            
            return data
            
        except json.JSONDecodeError as e:
            # خطای فرمت JSON
            print(f"⚠️ خطا در خواندن فایل {filename}: فرمت JSON نامعتبر - {e}")
            # تلاش برای بازیابی با پشتیبان
            backup_data = cls._load_from_backup(filename)
            if backup_data is not None:
                print(f"✅ داده‌ها از پشتیبان بازیابی شدند: {filename}")
                return backup_data
            return []
            
        except PermissionError as e:
            print(f"⚠️ خطای دسترسی به فایل {filename}: {e}")
            return []
            
        except Exception as e:
            print(f"⚠️ خطای غیرمنتظره در بارگذاری {filename}: {e}")
            return []
    
    @classmethod
    def save(cls, filename: str, data: Any, create_backup: bool = True) -> bool:
        """
        ذخیره داده‌ها در فایل JSON
        
        Args:
            filename: نام فایل (مثلاً 'users.json')
            data: داده‌های مورد نظر برای ذخیره
            create_backup: ایجاد پشتیبان قبل از ذخیره (پیش‌فرض True)
        
        Returns:
            bool: موفقیت‌آمیز بودن ذخیره
        
        Examples:
            >>> users = [{'id': 1, 'name': 'علی'}]
            >>> DataManager.save('users.json', users)
            True
        """
        try:
            path = os.path.join(get_data_path(), filename)
            
            # ایجاد پشتیبان
            if create_backup and os.path.exists(path):
                cls._create_backup(filename)
            
            # ذخیره فایل
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # به‌روزرسانی کش
            cls._add_to_cache(filename, data)
            
            return True
            
        except PermissionError as e:
            print(f"⚠️ خطای دسترسی در ذخیره {filename}: {e}")
            return False
            
        except Exception as e:
            print(f"⚠️ خطا در ذخیره {filename}: {e}")
            return False
    
    @classmethod
    def update(cls, filename: str, item_id: Union[int, str], new_data: Dict[str, Any], 
               id_field: str = 'id') -> bool:
        """
        به‌روزرسانی یک آیتم خاص در فایل
        
        Args:
            filename: نام فایل
            item_id: شناسه آیتم مورد نظر
            new_data: داده‌های جدید برای به‌روزرسانی
            id_field: نام فیلد شناسه (پیش‌فرض 'id')
        
        Returns:
            bool: موفقیت‌آمیز بودن به‌روزرسانی
        
        Examples:
            >>> DataManager.update('users.json', 1, {'name': 'علی جدید'})
            True
        """
        try:
            data = cls.load(filename, use_cache=False)
            found = False
            
            for item in data:
                if item.get(id_field) == item_id:
                    item.update(new_data)
                    found = True
                    break
            
            if not found:
                print(f"⚠️ آیتم با شناسه {item_id} در {filename} یافت نشد")
                return False
            
            return cls.save(filename, data)
            
        except Exception as e:
            print(f"⚠️ خطا در به‌روزرسانی {filename}: {e}")
            return False
    
    @classmethod
    def delete(cls, filename: str, item_id: Union[int, str], id_field: str = 'id') -> bool:
        """
        حذف یک آیتم از فایل
        
        Args:
            filename: نام فایل
            item_id: شناسه آیتم مورد نظر
            id_field: نام فیلد شناسه (پیش‌فرض 'id')
        
        Returns:
            bool: موفقیت‌آمیز بودن حذف
        
        Examples:
            >>> DataManager.delete('users.json', 1)
            True
        """
        try:
            data = cls.load(filename, use_cache=False)
            original_len = len(data)
            
            data = [item for item in data if item.get(id_field) != item_id]
            
            if len(data) == original_len:
                print(f"⚠️ آیتم با شناسه {item_id} در {filename} یافت نشد")
                return False
            
            return cls.save(filename, data)
            
        except Exception as e:
            print(f"⚠️ خطا در حذف از {filename}: {e}")
            return False
    
    @classmethod
    def find(cls, filename: str, **filters) -> List[Any]:
        """
        جستجوی آیتم‌ها با فیلترهای مشخص
        
        Args:
            filename: نام فایل
            **filters: فیلترهای جستجو (مثلاً name='علی', role='admin')
        
        Returns:
            List[Any]: لیست آیتم‌های پیدا شده
        
        Examples:
            >>> admins = DataManager.find('users.json', role='admin')
            >>> ali = DataManager.find('users.json', name='علی')
        """
        try:
            data = cls.load(filename)
            result = []
            
            for item in data:
                match = True
                for key, value in filters.items():
                    if item.get(key) != value:
                        match = False
                        break
                if match:
                    result.append(item)
            
            return result
            
        except Exception as e:
            print(f"⚠️ خطا در جستجوی {filename}: {e}")
            return []
    
    @classmethod
    def find_one(cls, filename: str, **filters) -> Optional[Any]:
        """
        پیدا کردن اولین آیتم با فیلترهای مشخص
        
        Args:
            filename: نام فایل
            **filters: فیلترهای جستجو
        
        Returns:
            Optional[Any]: اولین آیتم پیدا شده یا None
        
        Examples:
            >>> user = DataManager.find_one('users.json', username='ali')
        """
        results = cls.find(filename, **filters)
        return results[0] if results else None
    
    @classmethod
    def clear_cache(cls, filename: Optional[str] = None):
        """
        پاک کردن کش
        
        Args:
            filename: اگر مشخص شود، فقط آن فایل از کش پاک می‌شود
                     اگر None باشد، تمام کش پاک می‌شود
        
        Examples:
            >>> DataManager.clear_cache()  # پاک کردن تمام کش
            >>> DataManager.clear_cache('users.json')  # پاک کردن کش یک فایل
        """
        if filename:
            if filename in cls._cache:
                del cls._cache[filename]
            if filename in cls._cache_time:
                del cls._cache_time[filename]
        else:
            cls._cache.clear()
            cls._cache_time.clear()
    
    @classmethod
    def get_cache_info(cls) -> Dict[str, Any]:
        """
        دریافت اطلاعات وضعیت کش
        
        Returns:
            Dict: اطلاعات کش شامل تعداد آیتم‌ها و لیست فایل‌ها
        
        Examples:
            >>> info = DataManager.get_cache_info()
            >>> print(f"تعداد فایل‌های کش شده: {info['size']}")
        """
        return {
            'size': len(cls._cache),
            'files': list(cls._cache.keys()),
            'max_size': cls._max_cache_size,
            'ttl': cls._cache_ttl
        }
    
    @classmethod
    def _add_to_cache(cls, filename: str, data: Any):
        """اضافه کردن داده به کش با مدیریت حجم"""
        # اگر کش پر شده، قدیمی‌ترین آیتم را حذف کن
        if len(cls._cache) >= cls._max_cache_size:
            oldest_file = min(cls._cache_time, key=cls._cache_time.get)
            del cls._cache[oldest_file]
            del cls._cache_time[oldest_file]
        
        cls._cache[filename] = data
        cls._cache_time[filename] = time.time()
    
    @classmethod
    def _create_backup(cls, filename: str):
        """ایجاد پشتیبان از فایل"""
        try:
            source_path = os.path.join(get_data_path(), filename)
            # ✅ استفاده از get_app_backup_path از file_manager
            backup_dir = get_app_backup_path()
            os.makedirs(backup_dir, exist_ok=True)
            
            # ایجاد نام فایل پشتیبان با زمان
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{filename}_{timestamp}.backup"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # کپی فایل
            import shutil
            shutil.copy2(source_path, backup_path)
            
            # حذف پشتیبان‌های قدیمی (فقط ۵ تا آخرین پشتیبان نگهداری می‌شوند)
            cls._cleanup_old_backups(filename, keep=5)
            
        except Exception as e:
            print(f"⚠️ خطا در ایجاد پشتیبان {filename}: {e}")
    
    @classmethod
    def _cleanup_old_backups(cls, filename: str, keep: int = 5):
        """حذف پشتیبان‌های قدیمی"""
        try:
            # ✅ استفاده از get_app_backup_path از file_manager
            backup_dir = get_app_backup_path()
            if not os.path.exists(backup_dir):
                return
            
            # پیدا کردن فایل‌های پشتیبان مرتبط
            pattern = f"{filename}_"
            backups = []
            
            for f in os.listdir(backup_dir):
                if f.startswith(pattern) and f.endswith('.backup'):
                    fpath = os.path.join(backup_dir, f)
                    backups.append((fpath, os.path.getmtime(fpath)))
            
            # مرتب‌سازی بر اساس زمان (جدیدترین اول)
            backups.sort(key=lambda x: x[1], reverse=True)
            
            # حذف پشتیبان‌های اضافی
            for fpath, _ in backups[keep:]:
                try:
                    os.remove(fpath)
                except:
                    pass
                    
        except Exception as e:
            print(f"⚠️ خطا در پاکسازی پشتیبان‌ها: {e}")
    
    @classmethod
    def _load_from_backup(cls, filename: str) -> Optional[List[Any]]:
        """تلاش برای بازیابی از پشتیبان"""
        try:
            # ✅ استفاده از get_app_backup_path از file_manager
            backup_dir = get_app_backup_path()
            if not os.path.exists(backup_dir):
                return None
            
            # پیدا کردن آخرین پشتیبان
            pattern = f"{filename}_"
            backups = []
            
            for f in os.listdir(backup_dir):
                if f.startswith(pattern) and f.endswith('.backup'):
                    fpath = os.path.join(backup_dir, f)
                    backups.append((fpath, os.path.getmtime(fpath)))
            
            if not backups:
                return None
            
            # جدیدترین پشتیبان
            latest_backup = max(backups, key=lambda x: x[1])[0]
            
            with open(latest_backup, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return data
            
        except Exception as e:
            print(f"⚠️ خطا در بازیابی از پشتیبان {filename}: {e}")
            return None


# ========== توابع کمکی برای استفاده راحت‌تر ==========

def load_data(filename: str) -> List[Any]:
    """بارگذاری داده (نسخه ساده شده)"""
    return DataManager.load(filename)

def save_data(filename: str, data: Any) -> bool:
    """ذخیره داده (نسخه ساده شده)"""
    return DataManager.save(filename, data)

def update_item(filename: str, item_id: Union[int, str], new_data: Dict) -> bool:
    """به‌روزرسانی آیتم (نسخه ساده شده)"""
    return DataManager.update(filename, item_id, new_data)

def delete_item(filename: str, item_id: Union[int, str]) -> bool:
    """حذف آیتم (نسخه ساده شده)"""
    return DataManager.delete(filename, item_id)

def find_items(filename: str, **filters) -> List[Any]:
    """جستجوی آیتم‌ها (نسخه ساده شده)"""
    return DataManager.find(filename, **filters)

def find_one_item(filename: str, **filters) -> Optional[Any]:
    """پیدا کردن یک آیتم (نسخه ساده شده)"""
    return DataManager.find_one(filename, **filters)