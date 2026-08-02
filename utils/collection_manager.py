# utils/collection_manager.py
# ========== مدیریت وصول مطالبات ==========

import json
import os
import uuid
from datetime import datetime
from utils.file_manager import get_data_path


def get_collections_file_path():
    """دریافت مسیر فایل collections.json"""
    return os.path.join(get_data_path(), 'collections.json')


def _load_collections():
    """بارگذاری لیست وصول‌ها از فایل JSON"""
    file_path = get_collections_file_path()
    
    if not os.path.exists(file_path):
        _save_collections([])
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict):
            data = []
        
        return data if isinstance(data, list) else []
        
    except Exception as e:
        print(f"خطا در بارگذاری وصول‌ها: {e}")
        return []


def _save_collections(collections):
    """ذخیره لیست وصول‌ها در فایل JSON"""
    file_path = get_collections_file_path()
    
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(collections, f, ensure_ascii=False, indent=2)
        
        return True
        
    except Exception as e:
        print(f"خطا در ذخیره وصول‌ها: {e}")
        return False


def generate_collection_id():
    """تولید شناسه یکتا برای وصول"""
    now = datetime.now()
    date_part = f"{now.year}{now.month:02d}{now.day:02d}"
    random_part = str(uuid.uuid4())[:4].upper()
    return f"COL{date_part}{random_part}"


def check_duplicate_sayadi(sayadi_id):
    """بررسی تکراری نبودن شناسه صیادی در کل سیستم"""
    if not sayadi_id:
        return False
    
    collections = _load_collections()
    
    for col in collections:
        checks = col.get('checks', [])
        for check in checks:
            if check.get('sayadi_id', '') == sayadi_id:
                return True
    
    return False


def check_duplicate_check_number(customer_name, check_number):
    """بررسی تکراری نبودن شماره چک برای یک مشتری"""
    if not customer_name or not check_number:
        return False
    
    collections = _load_collections()
    
    for col in collections:
        if col.get('customer', '') == customer_name:
            checks = col.get('checks', [])
            for check in checks:
                if str(check.get('check_number', '')) == str(check_number):
                    return True
    
    return False


def save_collection(data):
    """ذخیره یک وصول جدید"""
    try:
        collections = _load_collections()
        
        # افزودن شناسه و زمان
        data['id'] = generate_collection_id()
        data['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        collections.append(data)
        
        if _save_collections(collections):
            return True, data['id'], "وصول با موفقیت ثبت شد"
        else:
            return False, None, "خطا در ذخیره وصول"
            
    except Exception as e:
        print(f"خطا در ذخیره وصول: {e}")
        return False, None, f"خطا: {str(e)}"


def get_collections(agent_name=None, date=None, status=None, customer=None):
    """دریافت وصول‌ها با فیلتر"""
    collections = _load_collections()
    
    if agent_name:
        collections = [c for c in collections if c.get('agent_name') == agent_name]
    
    if date:
        collections = [c for c in collections if c.get('date') == date]
    
    if status:
        collections = [c for c in collections if c.get('status') == status]
    
    if customer:
        collections = [c for c in collections if c.get('customer') == customer]
    
    return collections


def get_collection_stats(agent_name=None, start_date=None, end_date=None):
    """دریافت آمار وصول‌ها"""
    collections = _load_collections()
    
    if agent_name:
        collections = [c for c in collections if c.get('agent_name') == agent_name]
    
    if start_date:
        collections = [c for c in collections if c.get('date', '') >= start_date]
    
    if end_date:
        collections = [c for c in collections if c.get('date', '') <= end_date]
    
    successful = [c for c in collections if c.get('status') == 'موفق']
    failed = [c for c in collections if c.get('status') == 'ناموفق']
    
    total_cash = sum([
        c.get('net_cash', 0) 
        for c in successful 
        if c.get('has_cash', False)
    ])
    
    total_check = sum([
        c.get('total_check_amount', 0) 
        for c in successful 
        if c.get('has_check', False)
    ])
    
    return {
        'total': len(collections),
        'successful': len(successful),
        'failed': len(failed),
        'total_cash': total_cash,
        'total_check': total_check,
        'total_amount': total_cash + total_check
    }