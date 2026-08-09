"""
محاسبه امتیازات کاربران بر اساس نقش
"""

import os
import json
from utils.storage import get_data_path
from utils.jalali_date import get_today_jalali


def load_json_file(filename):
    """بارگذاری فایل JSON"""
    try:
        file_path = os.path.join(get_data_path(), filename)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {} if filename.endswith('.json') else []
    except Exception as e:
        print(f"خطا در بارگذاری {filename}: {e}")
        return {}


def get_attendance_points(user_name, date):
    """
    محاسبه امتیاز حضور بر اساس اولین ورود روز
    """
    try:
        attendance_data = load_json_file('attendance.json')
        if not attendance_data:
            return 0, "رکورد حضوری یافت نشد"
        
        # پیدا کردن رکوردهای کاربر در تاریخ مشخص
        user_records = []
        for r in attendance_data:
            if r.get('user_name') == user_name and r.get('date') == date:
                user_records.append(r)
        
        if not user_records:
            return 0, "حضور ثبت نشده"
        
        # پیدا کردن اولین ورود
        first_check_in = None
        for r in user_records:
            check_in = r.get('check_in')
            if check_in:
                if not first_check_in or check_in < first_check_in:
                    first_check_in = check_in
        
        if not first_check_in:
            return 0, "ساعت ورود ثبت نشده"
        
        # محاسبه امتیاز بر اساس ساعت
        hour = int(first_check_in.split(':')[0])
        minute = int(first_check_in.split(':')[1])
        time_value = hour + (minute / 60)
        
        if 5 <= time_value < 10.5:  # 05:00 تا 10:29
            return 30, f"صبح بخیر ({first_check_in})"
        elif 10.5 <= time_value < 12:  # 10:30 تا 11:59
            return 20, f"وقت بخیر ({first_check_in})"
        elif 12 <= time_value < 14.5:  # 12:00 تا 14:29
            return 10, f"ظهر بخیر ({first_check_in})"
        elif 14.5 <= time_value < 19:  # 14:30 تا 18:59
            return 5, f"بعدازظهر/عصر ({first_check_in})"
        else:  # 19:00 تا 04:59
            return 0, f"شب/نیمه شب ({first_check_in})"
            
    except Exception as e:
        print(f"خطا در محاسبه امتیاز حضور: {e}")
        return 0, str(e)


def get_mission_points(agent_name):
    """
    محاسبه امتیاز ماموریت‌های انجام شده
    """
    try:
        missions = load_json_file('do_missions.json')
        if not missions:
            return 0, 0, "هیچ ماموریتی یافت نشد"
        
        total_score = 0
        completed_count = 0
        
        for m in missions:
            if m.get('agent_name') != agent_name:
                continue
            
            # فقط ماموریت‌های تعیین تکلیف شده
            if m.get('active') == False:
                status = m.get('status', '')
                if 'موفق' in status:
                    total_score += m.get('score', 0)
                    completed_count += 1
                elif 'ناموفق' in status:
                    completed_count += 1
        
        return total_score, completed_count, f"{completed_count} ماموریت انجام شده"
        
    except Exception as e:
        print(f"خطا در محاسبه امتیاز ماموریت: {e}")
        return 0, 0, str(e)


def get_visit_points(agent_name):
    """
    محاسبه امتیاز ویزیت‌ها و فروش‌ها برای بازاریاب
    """
    try:
        daily_log = load_json_file('daily_log.json')
        if not daily_log:
            return {}, "هیچ داده‌ای یافت نشد"
        
        result = {
            'successful_visits': 0,
            'failed_visits': 0,
            'successful_sales': 0,
            'new_customers': 0,
            'cash_sales': 0,
            'check_sales': 0,
            'visit_points': 0,
            'sales_points': 0,
            'new_customer_points': 0,
            'cash_points': 0,
            'check_points': 0,
            'total_points': 0
        }
        
        for date, logs in daily_log.items():
            if not isinstance(logs, list):
                continue
            for log in logs:
                if log.get('agent_name') != agent_name:
                    continue
                
                # ویزیت‌ها
                visit_status = log.get('visit_status', '')
                if visit_status == 'موفق':
                    result['successful_visits'] += 1
                    result['visit_points'] += 5
                elif visit_status == 'ناموفق':
                    result['failed_visits'] += 1
                    result['visit_points'] += 1
                
                # فروش‌ها
                sales_status = log.get('sales_status', '')
                if sales_status == 'موفق':
                    result['successful_sales'] += 1
                    
                    # محاسبه امتیاز فروش پلکانی
                    sales_count = result['successful_sales']
                    if sales_count <= 3:
                        result['sales_points'] += 10
                    elif sales_count <= 6:
                        result['sales_points'] += 15
                    else:
                        result['sales_points'] += 20
                
                # مشتری جدید
                if log.get('is_new_customer', False):
                    result['new_customers'] += 1
                    result['new_customer_points'] += 20
                
                # فروش نقدی و چکی
                payment_method = log.get('payment_method', '')
                sales_amount = log.get('sales_amount', 0)
                if payment_method == 'نقد':
                    result['cash_sales'] += sales_amount
                    result['cash_points'] += int(sales_amount / 100000000) * 10
                elif payment_method == 'چک':
                    result['check_sales'] += sales_amount
                    result['check_points'] += int(sales_amount / 100000000) * 5
        
        result['total_points'] = (
            result['visit_points'] +
            result['sales_points'] +
            result['new_customer_points'] +
            result['cash_points'] +
            result['check_points']
        )
        
        return result, "محاسبه شد"
        
    except Exception as e:
        print(f"خطا در محاسبه امتیاز ویزیت: {e}")
        return {}, str(e)


def get_collection_points(agent_name):
    """
    محاسبه امتیاز وصول‌ها
    """
    try:
        collections = load_json_file('collections.json')
        if not collections:
            return {}, "هیچ داده‌ای یافت نشد"
        
        result = {
            'success_count': 0,
            'fail_count': 0,
            'total_points': 0
        }
        
        for c in collections:
            if c.get('agent_name') != agent_name:
                continue
            
            status = c.get('status', '')
            if status == 'موفق':
                result['success_count'] += 1
                result['total_points'] += 30
            elif status == 'ناموفق':
                result['fail_count'] += 1
                result['total_points'] += 10
        
        return result, "محاسبه شد"
        
    except Exception as e:
        print(f"خطا در محاسبه امتیاز وصول: {e}")
        return {}, str(e)


def get_report_submission_points(agent_name):
    """
    محاسبه امتیاز ارسال گزارش به مدیر (فقط در شب)
    """
    try:
        visits = load_json_file('supervisor_visits.json')
        if not visits:
            return 0, "هیچ داده‌ای یافت نشد"
        
        total_points = 0
        count = 0
        
        for v in visits:
            if v.get('created_by') != agent_name:
                continue
            
            if v.get('reported_to_manager', False):
                created_at = v.get('created_at', '')
                if created_at:
                    try:
                        time_str = created_at.split('T')[1].split(':')
                        hour = int(time_str[0])
                        
                        # فقط در بازه شب (۱۹:۰۰ تا ۲۳:۵۹)
                        if 19 <= hour <= 23:
                            total_points += 100
                            count += 1
                    except:
                        pass
        
        return total_points, f"{count} گزارش ارسال شده در شب"
        
    except Exception as e:
        print(f"خطا در محاسبه امتیاز ارسال گزارش: {e}")
        return 0, str(e)


def get_delivery_points(distributor_name):
    """
    محاسبه امتیاز توزیع برای موزع
    """
    try:
        deliveries = load_json_file('delivery_sale.json')
        if not deliveries:
            return {}, "هیچ داده‌ای یافت نشد"
        
        result = {
            'successful_deliveries': 0,
            'failed_deliveries': 0,
            'full_deliveries': 0,
            'total_invoice': 0,
            'total_cash': 0,
            'total_check': 0,
            'total_points': 0
        }
        
        for date, logs in deliveries.items():
            if not isinstance(logs, list):
                continue
            for log in logs:
                agent = log.get('agent_name', '') or log.get('distributor_name', '')
                if agent != distributor_name:
                    continue
                
                # وضعیت توزیع
                status = log.get('delivery_status', '')
                if status == 'موفق':
                    result['successful_deliveries'] += 1
                    result['total_points'] += 10
                    
                    # تحویل کامل
                    if log.get('full_delivery', False):
                        result['full_deliveries'] += 1
                        result['total_points'] += 5
                elif status == 'ناموفق':
                    result['failed_deliveries'] += 1
                    result['total_points'] += 3
                
                # مبالغ
                result['total_invoice'] += log.get('invoice_amount', 0)
                result['total_cash'] += log.get('cash_amount', 0)
                result['total_check'] += log.get('check_amount', 0)
                
                # امتیاز نقدی و چکی
                cash_amount = log.get('cash_amount', 0)
                check_amount = log.get('check_amount', 0)
                result['total_points'] += int(cash_amount / 100000000) * 5
                result['total_points'] += int(check_amount / 100000000) * 3
        
        return result, "محاسبه شد"
        
    except Exception as e:
        print(f"خطا در محاسبه امتیاز توزیع: {e}")
        return {}, str(e)


def calculate_all_scores(username, role, date=None):
    """
    محاسبه تمام امتیازات کاربر بر اساس نقش
    """
    if not date:
        date = get_today_jalali()
    
    result = {
        'username': username,
        'role': role,
        'date': date,
        'attendance': {'points': 0, 'detail': ''},
        'mission': {'points': 0, 'count': 0, 'detail': ''},
        'visit': {'points': 0, 'detail': ''},
        'collection': {'points': 0, 'detail': ''},
        'report': {'points': 0, 'detail': ''},
        'delivery': {'points': 0, 'detail': ''},
        'total_points': 0,
        'breakdown': {}
    }
    
    # امتیاز حضور (همه نقش‌ها)
    att_points, att_detail = get_attendance_points(username, date)
    result['attendance']['points'] = att_points
    result['attendance']['detail'] = att_detail
    
    # امتیاز ماموریت (بازاریاب و سوپروایزر)
    if role in ['بازاریاب', 'سوپروایزر']:
        mission_points, mission_count, mission_detail = get_mission_points(username)
        result['mission']['points'] = mission_points
        result['mission']['count'] = mission_count
        result['mission']['detail'] = mission_detail
    
    # امتیاز ویزیت و فروش (بازاریاب)
    if role == 'بازاریاب':
        visit_data, visit_detail = get_visit_points(username)
        result['visit'] = visit_data
        result['visit']['detail'] = visit_detail
        
        collection_data, collection_detail = get_collection_points(username)
        result['collection'] = collection_data
        result['collection']['detail'] = collection_detail
    
    # امتیاز ارسال گزارش (سوپروایزر)
    if role == 'سوپروایزر':
        report_points, report_detail = get_report_submission_points(username)
        result['report']['points'] = report_points
        result['report']['detail'] = report_detail
    
    # امتیاز توزیع (موزع)
    if role == 'موزع':
        delivery_data, delivery_detail = get_delivery_points(username)
        result['delivery'] = delivery_data
        result['delivery']['detail'] = delivery_detail
    
    # جمع کل امتیازات
    total = (
        result['attendance']['points'] +
        result['mission']['points'] +
        result.get('visit', {}).get('total_points', 0) +
        result.get('collection', {}).get('total_points', 0) +
        result.get('report', {}).get('points', 0) +
        result.get('delivery', {}).get('total_points', 0)
    )
    result['total_points'] = total
    
    return result