# utils/delivery_manager.py
# ========== مدیریت توزع‌ها ==========

import os
import json
import uuid
from datetime import datetime
from utils.file_manager import get_data_path, load_json, save_json
from utils.jalali_date import get_today_jalali, get_current_time
from kivy.logger import Logger as logger

DELIVERY_FILE = 'delivery_sale.json'


def get_all_deliveries():
    """
    دریافت تمام توزیع‌ها از فایل delivery_sale.json
    
    Returns:
        dict: دیکشنری با کلید تاریخ و مقدار لیست توزیع‌های آن روز
    """
    try:
        data = load_json(DELIVERY_FILE)
        if data is None:
            return {}
        return data
    except Exception as e:
        logger.error(f"خطا در دریافت تمام توزیع‌ها: {e}")
        return {}


def get_deliveries():
    """دریافت تمام توزع‌ها (همان get_all_deliveries برای سازگاری)"""
    return get_all_deliveries()


def save_delivery(delivery_data):
    """
    ذخیره یک توزع جدید
    
    Args:
        delivery_data: دیکشنری شامل اطلاعات توزع
    
    Returns:
        (success, message, delivery_id)
    """
    try:
        deliveries = get_all_deliveries()
        
        delivery_id = f"DEL-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
        delivery_data['id'] = delivery_id
        delivery_data['timestamp'] = f"{get_today_jalali()} {get_current_time()}"
        delivery_data['is_closed'] = False
        
        today = get_today_jalali()
        if today not in deliveries:
            deliveries[today] = []
        
        deliveries[today].append(delivery_data)
        
        if save_json(DELIVERY_FILE, deliveries):
            logger.info(f"توزع ثبت شد: {delivery_id}")
            return True, "توزع با موفقیت ثبت شد", delivery_id
        else:
            return False, "خطا در ذخیره توزع", None
            
    except Exception as e:
        logger.error(f"خطا در ذخیره توزع: {e}")
        return False, f"خطا: {str(e)}", None


def get_deliveries_by_date(date=None):
    """دریافت توزع‌های یک تاریخ مشخص"""
    try:
        deliveries = get_all_deliveries()
        if not date:
            date = get_today_jalali()
        return deliveries.get(date, [])
    except Exception as e:
        logger.error(f"خطا در دریافت توزع‌های تاریخ {date}: {e}")
        return []


def get_deliveries_by_agent(agent_name, date=None):
    """دریافت توزع‌های یک فروشنده در تاریخ مشخص"""
    try:
        date_deliveries = get_deliveries_by_date(date)
        return [d for d in date_deliveries if d.get('agent_name') == agent_name]
    except Exception as e:
        logger.error(f"خطا در دریافت توزع‌های فروشنده: {e}")
        return []


def get_delivery_by_id(delivery_id):
    """دریافت یک توزع بر اساس ID"""
    try:
        deliveries = get_all_deliveries()
        for date, items in deliveries.items():
            for item in items:
                if item.get('id') == delivery_id:
                    return item
        return None
    except Exception as e:
        logger.error(f"خطا در دریافت توزع با ID {delivery_id}: {e}")
        return None


def update_delivery(delivery_id, updated_data):
    """به‌روزرسانی یک توزع"""
    try:
        deliveries = get_all_deliveries()
        for date, items in deliveries.items():
            for i, item in enumerate(items):
                if item.get('id') == delivery_id:
                    for key, value in updated_data.items():
                        item[key] = value
                    deliveries[date][i] = item
                    
                    if save_json(DELIVERY_FILE, deliveries):
                        logger.info(f"توزع به‌روزرسانی شد: {delivery_id}")
                        return True, "توزع با موفقیت به‌روزرسانی شد"
                    else:
                        return False, "خطا در ذخیره تغییرات"
        return False, "توزع پیدا نشد"
    except Exception as e:
        logger.error(f"خطا در به‌روزرسانی توزع: {e}")
        return False, f"خطا: {str(e)}"


def delete_delivery(delivery_id):
    """حذف یک توزع (فقط در صورتی که بسته نشده باشد)"""
    try:
        deliveries = get_all_deliveries()
        for date, items in deliveries.items():
            for i, item in enumerate(items):
                if item.get('id') == delivery_id:
                    if item.get('is_closed', False):
                        return False, "توزع بسته شده و قابل حذف نیست"
                    
                    del deliveries[date][i]
                    if not deliveries[date]:
                        del deliveries[date]
                    
                    if save_json(DELIVERY_FILE, deliveries):
                        logger.info(f"توزع حذف شد: {delivery_id}")
                        return True, "توزع با موفقیت حذف شد"
                    else:
                        return False, "خطا در ذخیره تغییرات"
        return False, "توزع پیدا نشد"
    except Exception as e:
        logger.error(f"خطا در حذف توزع: {e}")
        return False, f"خطا: {str(e)}"


def get_delivery_stats(agent_name=None, date=None):
    """دریافت آمار توزع‌ها"""
    try:
        deliveries = get_deliveries_by_date(date)
        
        if agent_name:
            deliveries = [d for d in deliveries if d.get('agent_name') == agent_name]
        
        total_deliveries = len(deliveries)
        successful = len([d for d in deliveries if d.get('delivery_status') == 'موفق'])
        failed = len([d for d in deliveries if d.get('delivery_status') == 'ناموفق'])
        total_amount = sum([d.get('invoice_amount', 0) for d in deliveries])
        total_received = sum([d.get('total_received', 0) for d in deliveries])
        total_remaining = sum([d.get('remaining_amount', 0) for d in deliveries])
        
        return {
            'total': total_deliveries,
            'successful': successful,
            'failed': failed,
            'total_amount': total_amount,
            'total_received': total_received,
            'total_remaining': total_remaining,
            'deliveries': deliveries
        }
    except Exception as e:
        logger.error(f"خطا در دریافت آمار توزع: {e}")
        return {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'total_amount': 0,
            'total_received': 0,
            'total_remaining': 0,
            'deliveries': []
        }


def get_delivery_summary(date=None):
    """دریافت خلاصه توزیع‌های یک تاریخ (برای نمایش در UserScreen)"""
    try:
        deliveries = get_deliveries_by_date(date)
        
        if not deliveries:
            return {
                'total_customers': 0,
                'total_deliveries': 0,
                'total_amount': 0,
                'total_cash': 0,
                'total_check': 0,
                'total_credit': 0,
                'total_return_qty': 0,
                'total_return_amount': 0,
                'first_time': None,
                'last_time': None,
                'start_time': None,
                'routes': []
            }
        
        total_customers = 0
        total_deliveries = 0
        total_amount = 0
        total_cash = 0
        total_check = 0
        total_credit = 0
        total_return_qty = 0
        total_return_amount = 0
        first_time = None
        last_time = None
        start_time = None
        routes = set()
        
        for delivery in deliveries:
            if not isinstance(delivery, dict):
                continue
            
            route = delivery.get('route', '')
            if route:
                routes.add(route)
            
            delivery_time = delivery.get('timestamp', '')
            if delivery_time and ' ' in delivery_time:
                time_part = delivery_time.split(' ')[1]
                if start_time is None:
                    start_time = time_part
                if first_time is None:
                    first_time = time_part
                last_time = time_part
            
            delivery_status = delivery.get('delivery_status', '')
            
            if delivery_status == 'موفق':
                total_customers += 1
                total_deliveries += 1
                total_amount += delivery.get('invoice_amount', 0)
                total_cash += delivery.get('cash_amount', 0)
                total_check += delivery.get('check_amount', 0)
                total_credit += delivery.get('remaining_amount', 0)
                total_return_qty += delivery.get('returned_quantity', 0)
                total_return_amount += delivery.get('returned_amount', 0)
        
        return {
            'total_customers': total_customers,
            'total_deliveries': total_deliveries,
            'total_amount': total_amount,
            'total_cash': total_cash,
            'total_check': total_check,
            'total_credit': total_credit,
            'total_return_qty': total_return_qty,
            'total_return_amount': total_return_amount,
            'first_time': first_time,
            'last_time': last_time,
            'start_time': start_time,
            'routes': list(routes)
        }
        
    except Exception as e:
        logger.error(f"خطا در دریافت خلاصه توزیع: {e}")
        return {
            'total_customers': 0,
            'total_deliveries': 0,
            'total_amount': 0,
            'total_cash': 0,
            'total_check': 0,
            'total_credit': 0,
            'total_return_qty': 0,
            'total_return_amount': 0,
            'first_time': None,
            'last_time': None,
            'start_time': None,
            'routes': []
        }