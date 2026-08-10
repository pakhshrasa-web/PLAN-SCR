"""
محاسبه امتیازات کاربران بر اساس نقش و تنظیمات
"""

import os
import json
from utils.storage import get_data_path
from utils.jalali_date import get_today_jalali


def load_score_settings():
    """بارگذاری تنظیمات امتیازدهی"""
    try:
        file_path = os.path.join(get_data_path(), 'score_settings.json')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return get_default_score_settings()
    except Exception as e:
        print(f"خطا در بارگذاری تنظیمات امتیازدهی: {e}")
        return get_default_score_settings()


def get_default_score_settings():
    """مقادیر پیش‌فرض تنظیمات امتیازدهی"""
    return {
        'attendance': {
            'morning': {'active': True, 'score': 30},
            'noon': {'active': True, 'score': 20},
            'afternoon': {'active': True, 'score': 10},
            'evening': {'active': True, 'score': 5},
            'night': {'active': True, 'score': 5},
            'late_night': {'active': False, 'score': 0}
        },
        'visit': {
            'first_visit': {'active': True, 'score': 5},
            'success_visit': {'active': True, 'score': 5},
            'fail_visit': {'active': True, 'score': 1},
            'success_sale': {'active': True, 'score': 10}
        },
        'collection': {
            'success': {'active': True, 'score': 30},
            'amount_per_10m': {'active': True, 'score': 1}
        },
        'target': {
            'setting': {'active': True, 'score': 100},
            'achieve': {'active': True, 'score': 25},
            'detail': {'active': True, 'score': 25}
        },
        'other': {
            'market_visit': {'active': True, 'score': 15},
            'delivery': {'active': True, 'score': 10},
            'delivery_amount_per_10m': {'active': True, 'score': 1},
            'report': {'active': True, 'score': 100}
        },
        'bonus': {
            'active': True,
            'percent': 5000
        }
    }


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


def get_attendance_points(user_name, date, settings=None):
    """
    محاسبه امتیاز حضور بر اساس اولین ورود روز و تنظیمات
    """
    try:
        if settings is None:
            settings = load_score_settings()
        
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
        
        # محاسبه امتیاز بر اساس ساعت و تنظیمات
        hour = int(first_check_in.split(':')[0])
        minute = int(first_check_in.split(':')[1])
        time_value = hour + (minute / 60)
        
        att_settings = settings.get('attendance', {})
        
        if 5 <= time_value < 10.5:  # 05:00 تا 10:29 - صبح
            config = att_settings.get('morning', {})
            if config.get('active', True):
                return config.get('score', 30), f"صبح بخیر ({first_check_in})"
            return 0, f"صبح بخیر ({first_check_in}) - غیرفعال"
            
        elif 10.5 <= time_value < 12:  # 10:30 تا 11:59 - پیش از ظهر
            config = att_settings.get('noon', {})
            if config.get('active', True):
                return config.get('score', 20), f"وقت بخیر ({first_check_in})"
            return 0, f"وقت بخیر ({first_check_in}) - غیرفعال"
            
        elif 12 <= time_value < 14.5:  # 12:00 تا 14:29 - ظهر
            config = att_settings.get('afternoon', {})
            if config.get('active', True):
                return config.get('score', 10), f"ظهر بخیر ({first_check_in})"
            return 0, f"ظهر بخیر ({first_check_in}) - غیرفعال"
            
        elif 14.5 <= time_value < 16.5:  # 14:30 تا 16:29 - بعدازظهر
            config = att_settings.get('evening', {})
            if config.get('active', True):
                return config.get('score', 5), f"بعدازظهر بخیر ({first_check_in})"
            return 0, f"بعدازظهر بخیر ({first_check_in}) - غیرفعال"
            
        elif 16.5 <= time_value < 19:  # 16:30 تا 18:59 - عصر
            config = att_settings.get('night', {})
            if config.get('active', True):
                return config.get('score', 5), f"عصر بخیر ({first_check_in})"
            return 0, f"عصر بخیر ({first_check_in}) - غیرفعال"
            
        else:  # 19:00 تا 04:59 - شب
            config = att_settings.get('late_night', {})
            if config.get('active', False):
                return config.get('score', 0), f"شب بخیر ({first_check_in})"
            return 0, f"شب بخیر ({first_check_in}) - غیرفعال"
            
    except Exception as e:
        print(f"خطا در محاسبه امتیاز حضور: {e}")
        return 0, str(e)


def get_end_day_points(user_name, date, settings=None):
    """
    محاسبه امتیاز پایان کار بر اساس تنظیمات حضور
    """
    try:
        if settings is None:
            settings = load_score_settings()
        
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
        
        # بررسی پایان کار
        is_day_ended = False
        for r in user_records:
            if r.get('is_day_ended', False):
                is_day_ended = True
                break
        
        if not is_day_ended:
            return 0, "پایان کار ثبت نشده"
        
        # پیدا کردن اولین ورود برای امتیاز
        first_check_in = None
        for r in user_records:
            check_in = r.get('check_in')
            if check_in:
                if not first_check_in or check_in < first_check_in:
                    first_check_in = check_in
        
        if not first_check_in:
            return 0, "ساعت ورود ثبت نشده"
        
        # محاسبه امتیاز بر اساس ساعت و تنظیمات (همانند حضور)
        hour = int(first_check_in.split(':')[0])
        minute = int(first_check_in.split(':')[1])
        time_value = hour + (minute / 60)
        
        att_settings = settings.get('attendance', {})
        
        if 5 <= time_value < 10.5:  # 05:00 تا 10:29 - صبح
            config = att_settings.get('morning', {})
            if config.get('active', True):
                return config.get('score', 30), f"پایان کار - صبح بخیر ({first_check_in})"
            return 0, f"پایان کار - صبح بخیر (غیرفعال)"
            
        elif 10.5 <= time_value < 12:  # 10:30 تا 11:59 - پیش از ظهر
            config = att_settings.get('noon', {})
            if config.get('active', True):
                return config.get('score', 20), f"پایان کار - وقت بخیر ({first_check_in})"
            return 0, f"پایان کار - وقت بخیر (غیرفعال)"
            
        elif 12 <= time_value < 14.5:  # 12:00 تا 14:29 - ظهر
            config = att_settings.get('afternoon', {})
            if config.get('active', True):
                return config.get('score', 10), f"پایان کار - ظهر بخیر ({first_check_in})"
            return 0, f"پایان کار - ظهر بخیر (غیرفعال)"
            
        elif 14.5 <= time_value < 16.5:  # 14:30 تا 16:29 - بعدازظهر
            config = att_settings.get('evening', {})
            if config.get('active', True):
                return config.get('score', 5), f"پایان کار - بعدازظهر بخیر ({first_check_in})"
            return 0, f"پایان کار - بعدازظهر بخیر (غیرفعال)"
            
        elif 16.5 <= time_value < 19:  # 16:30 تا 18:59 - عصر
            config = att_settings.get('night', {})
            if config.get('active', True):
                return config.get('score', 5), f"پایان کار - عصر بخیر ({first_check_in})"
            return 0, f"پایان کار - عصر بخیر (غیرفعال)"
            
        else:  # 19:00 تا 04:59 - شب
            config = att_settings.get('late_night', {})
            if config.get('active', False):
                return config.get('score', 0), f"پایان کار - شب بخیر ({first_check_in})"
            return 0, f"پایان کار - شب بخیر (غیرفعال)"
            
    except Exception as e:
        print(f"خطا در محاسبه امتیاز پایان کار: {e}")
        return 0, str(e)


def get_mission_points(agent_name, date=None):
    """
    محاسبه امتیاز ماموریت‌های انجام شده
    """
    try:
        from utils.name_matcher import normalize_persian_text
        
        missions_data = load_json_file('do_missions.json')
        if not missions_data:
            return 0, 0, "هیچ ماموریتی یافت نشد"
        
        # تبدیل به لیست اگر دیکشنری باشد
        missions = []
        if isinstance(missions_data, dict):
            for date_key, items in missions_data.items():
                if isinstance(items, list):
                    for m in items:
                        if isinstance(m, dict):
                            m['_date'] = date_key
                            missions.append(m)
        elif isinstance(missions_data, list):
            missions = missions_data
        else:
            return 0, 0, "ساختار فایل ماموریت‌ها نامعتبر است"
        
        # نرمال‌سازی نام عامل
        agent_norm = normalize_persian_text(agent_name)
        
        total_score = 0
        completed_count = 0
        success_count = 0
        fail_count = 0
        
        for m in missions:
            if not isinstance(m, dict):
                continue
            
            m_agent = m.get('agent_name', '')
            m_agent_norm = normalize_persian_text(m_agent)
            
            if m_agent_norm != agent_norm:
                continue
            
            if m.get('active') == False:
                status = m.get('status', '')
                completed_at = m.get('completed_at', '')
                
                if date is not None and completed_at != date:
                    continue
                
                if 'موفق' in status:
                    total_score += m.get('score', 0)
                    success_count += 1
                    completed_count += 1
                elif 'ناموفق' in status:
                    fail_count += 1
                    completed_count += 1
        
        detail = f"{completed_count} ماموریت انجام شده (موفق: {success_count}، ناموفق: {fail_count})"
        return total_score, completed_count, detail
        
    except Exception as e:
        print(f"خطا در محاسبه امتیاز ماموریت: {e}")
        import traceback
        traceback.print_exc()
        return 0, 0, str(e)


def get_visit_points(agent_name, date=None, settings=None):
    """
    محاسبه امتیاز ویزیت‌ها و فروش‌ها برای بازاریاب
    """
    try:
        if settings is None:
            settings = load_score_settings()
        
        daily_log = load_json_file('daily_log.json')
        if not daily_log:
            return {}, "هیچ داده‌ای یافت نشد"
        
        visit_settings = settings.get('visit', {})
        
        result = {
            'successful_visits': 0,
            'failed_visits': 0,
            'total_visits': 0,
            'successful_sales': 0,
            'new_customers': 0,
            'cash_sales': 0,
            'check_sales': 0,
            'visit_points': 0,
            'sales_points': 0,
            'new_customer_points': 0,
            'first_visit_points': 0,
            'cash_points': 0,
            'check_points': 0,
            'total_points': 0,
            'has_first_visit': False,
            'first_visit_time': None
        }
        
        # جمع‌آوری همه ویزیت‌های کاربر در تاریخ مورد نظر
        user_visits = []
        
        for log_date, logs in daily_log.items():
            if not isinstance(logs, list):
                continue
            
            if date is not None and log_date != date:
                continue
                
            for log in logs:
                log_agent = log.get('agent_name', '')
                if log_agent != agent_name:
                    continue
                
                visit_status = log.get('visit_status', '')
                if visit_status not in ['موفق', 'ناموفق']:
                    continue
                
                user_visits.append({
                    'log': log,
                    'time': log.get('time', ''),
                    'visit_status': visit_status,
                    'sales_status': log.get('sales_status', ''),
                    'is_new_customer': log.get('is_new_customer', False),
                    'payment_method': log.get('payment_method', ''),
                    'sales_amount': log.get('sales_amount', 0)
                })
        
        if not user_visits:
            detail = "هیچ ویزیتی ثبت نشده"
            result['detail'] = detail
            return result, detail
        
        # پیدا کردن اولین ویزیت بر اساس زمان
        user_visits.sort(key=lambda x: x['time'])
        first_visit = user_visits[0]
        first_visit_time = first_visit['time']
        result['first_visit_time'] = first_visit_time
        
        print(f"🔍 اولین ویزیت: ساعت {first_visit_time} - وضعیت: {first_visit['visit_status']}")
        
        # محاسبه امتیازات
        for visit in user_visits:
            log = visit['log']
            visit_status = visit['visit_status']
            visit_time = visit['time']
            
            result['total_visits'] += 1
            
            if not result['has_first_visit'] and visit_time == first_visit_time:
                result['has_first_visit'] = True
                config = visit_settings.get('first_visit', {})
                if config.get('active', True):
                    result['first_visit_points'] = config.get('score', 5)
                    print(f"   ✅ اولین ویزیت: {visit_time} - {result['first_visit_points']} امتیاز")
            
            if visit_status == 'موفق':
                result['successful_visits'] += 1
                config = visit_settings.get('success_visit', {})
                if config.get('active', True):
                    result['visit_points'] += config.get('score', 5)
            elif visit_status == 'ناموفق':
                result['failed_visits'] += 1
                config = visit_settings.get('fail_visit', {})
                if config.get('active', True):
                    result['visit_points'] += config.get('score', 1)
            
            sales_status = visit.get('sales_status', '')
            if sales_status == 'موفق':
                result['successful_sales'] += 1
                config = visit_settings.get('success_sale', {})
                if config.get('active', True):
                    result['sales_points'] += config.get('score', 10)
            
            if visit.get('is_new_customer', False):
                result['new_customers'] += 1
                config = visit_settings.get('first_visit', {})
                if config.get('active', True):
                    result['new_customer_points'] += config.get('score', 5)
            
            payment_method = visit.get('payment_method', '')
            sales_amount = visit.get('sales_amount', 0)
            if payment_method == 'نقد':
                result['cash_sales'] += sales_amount
                result['cash_points'] += int(sales_amount / 100000000) * 10
            elif payment_method == 'چک':
                result['check_sales'] += sales_amount
                result['check_points'] += int(sales_amount / 100000000) * 5
        
        result['total_points'] = (
            result['first_visit_points'] +
            result['visit_points'] +
            result['sales_points'] +
            result['new_customer_points'] +
            result['cash_points'] +
            result['check_points']
        )
        
        detail = f"کل ویزیت‌ها: {result['total_visits']} (موفق: {result['successful_visits']}، ناموفق: {result['failed_visits']})"
        if result['has_first_visit']:
            detail += f" | اولین ویزیت: {first_visit_time}"
        result['detail'] = detail
        
        print(f"\n📊 تفکیک امتیازات ویزیت برای {agent_name}:")
        print(f"   ویزیت موفق: {result['successful_visits']} × ۵ = {result['successful_visits'] * 5}")
        print(f"   ویزیت ناموفق: {result['failed_visits']} × ۱ = {result['failed_visits'] * 1}")
        print(f"   اولین ویزیت: {result['first_visit_points']}")
        print(f"   فروش موفق: {result['successful_sales']} × ۱۰ = {result['successful_sales'] * 10}")
        print(f"   مشتری جدید: {result['new_customers']} × ۵ = {result['new_customer_points']}")
        print(f"   فروش نقدی: {result['cash_points']}")
        print(f"   فروش چکی: {result['check_points']}")
        print(f"   جمع کل: {result['total_points']}")
        
        return result, "محاسبه شد"
        
    except Exception as e:
        print(f"خطا در محاسبه امتیاز ویزیت: {e}")
        import traceback
        traceback.print_exc()
        return {}, str(e)


def get_collection_points(agent_name, date=None, settings=None):
    """
    محاسبه امتیاز وصول‌ها بر اساس تنظیمات
    """
    try:
        if settings is None:
            settings = load_score_settings()
        
        collections = load_json_file('collections.json')
        if not collections:
            return {}, "هیچ داده‌ای یافت نشد"
        
        collection_settings = settings.get('collection', {})
        
        result = {
            'success_count': 0,
            'fail_count': 0,
            'total_points': 0,
            'total_amount': 0,
            'success_points': 0,
            'amount_points': 0
        }
        
        for c in collections:
            if c.get('agent_name') != agent_name:
                continue
            
            collection_date = c.get('date', '')
            if date is not None and collection_date != date:
                continue
            
            status = c.get('status', '')
            if status == 'موفق':
                result['success_count'] += 1
                config = collection_settings.get('success', {})
                if config.get('active', True):
                    points = config.get('score', 30)
                    result['success_points'] += points
                
                total_collection = c.get('total_collection', 0)
                if total_collection > 0:
                    config_amount = collection_settings.get('amount_per_10m', {})
                    if config_amount.get('active', True):
                        amount_score = config_amount.get('score', 1)
                        result['amount_points'] += int(total_collection / 10000000) * amount_score
                        result['total_amount'] += total_collection
                        
            elif status == 'ناموفق':
                result['fail_count'] += 1
        
        result['total_points'] = result['success_points'] + result['amount_points']
        return result, "محاسبه شد"
        
    except Exception as e:
        print(f"خطا در محاسبه امتیاز وصول: {e}")
        return {}, str(e)


def get_delivery_points(distributor_name, date=None, settings=None):
    """
    محاسبه امتیاز توزیع برای موزع بر اساس تنظیمات
    """
    try:
        if settings is None:
            settings = load_score_settings()
        
        from utils.name_matcher import normalize_persian_text
        
        deliveries = load_json_file('delivery_sale.json')
        if not deliveries:
            return {}, "هیچ داده‌ای یافت نشد"
        
        delivery_settings = settings.get('other', {})
        
        dist_norm = normalize_persian_text(distributor_name)
        
        result = {
            'successful_deliveries': 0,
            'failed_deliveries': 0,
            'full_deliveries': 0,
            'total_invoice': 0,
            'total_cash': 0,
            'total_check': 0,
            'total_points': 0,
            'delivery_points': 0,
            'amount_points': 0
        }
        
        for delivery_date, logs in deliveries.items():
            if not isinstance(logs, list):
                continue
            
            if date is not None and delivery_date != date:
                continue
                
            for log in logs:
                if not isinstance(log, dict):
                    continue
                
                agent = log.get('agent_name', '') or log.get('distributor_name', '')
                if not agent:
                    continue
                
                agent_norm = normalize_persian_text(agent)
                
                if agent_norm != dist_norm:
                    continue
                
                status = log.get('delivery_status', '')
                if status == 'موفق':
                    result['successful_deliveries'] += 1
                    config = delivery_settings.get('delivery', {})
                    if config.get('active', True):
                        points = config.get('score', 10)
                        result['delivery_points'] += points
                    
                    if log.get('full_delivery', False):
                        result['full_deliveries'] += 1
                        
                elif status == 'ناموفق':
                    result['failed_deliveries'] += 1
                
                cash_amount = log.get('cash_amount', 0)
                
                if cash_amount > 0:
                    config_amount = delivery_settings.get('delivery_amount_per_10m', {})
                    if config_amount.get('active', True):
                        amount_score = config_amount.get('score', 1)
                        result['amount_points'] += int(cash_amount / 10000000) * amount_score
                
                result['total_invoice'] += log.get('invoice_amount', 0)
                result['total_cash'] += cash_amount
                result['total_check'] += log.get('check_amount', 0)
        
        result['total_points'] = result['delivery_points'] + result['amount_points']
        
        detail = f"توزیع‌ها: {result['successful_deliveries']} موفق, {result['failed_deliveries']} ناموفق"
        result['detail'] = detail
        
        return result, "محاسبه شد"
        
    except Exception as e:
        print(f"خطا در محاسبه امتیاز توزیع: {e}")
        import traceback
        traceback.print_exc()
        return {}, str(e)


def get_market_visit_points(agent_name, date=None, settings=None):
    """
    محاسبه امتیاز سرکشی بازار برای سوپروایزر
    """
    try:
        if settings is None:
            settings = load_score_settings()
        
        from utils.name_matcher import normalize_persian_text
        
        visits = load_json_file('supervisor_visits.json')
        if not visits:
            return 0, 0, "هیچ داده‌ای یافت نشد"
        
        market_settings = settings.get('other', {}).get('market_visit', {})
        if not market_settings.get('active', True):
            return 0, 0, "امتیاز سرکشی بازار غیرفعال است"
        
        agent_norm = normalize_persian_text(agent_name)
        
        total_points = 0
        count = 0
        
        for v in visits:
            created_by = v.get('created_by', '')
            created_by_norm = normalize_persian_text(created_by)
            
            if created_by_norm != agent_norm:
                continue
            
            visit_date = v.get('date', '')
            if date is not None and visit_date != date:
                continue
            
            count += 1
            total_points += market_settings.get('score', 15)
        
        detail = f"{count} سرکشی بازار"
        return total_points, count, detail
        
    except Exception as e:
        print(f"خطا در محاسبه امتیاز سرکشی بازار: {e}")
        import traceback
        traceback.print_exc()
        return 0, 0, str(e)


def get_target_points(agent_name, date=None, settings=None):
    """
    محاسبه امتیاز هدف‌گذاری و تحقق تارگت برای سوپروایزر
    """
    try:
        if settings is None:
            settings = load_score_settings()
        
        from utils.name_matcher import normalize_persian_text
        from utils.jalali_date import convert_to_jalali
        
        targets = load_json_file('targets.json')
        if not targets:
            return {}, "هیچ داده‌ای یافت نشد"
        
        agent_norm = normalize_persian_text(agent_name)
        
        target_settings = settings.get('target', {})
        
        result = {
            'setting_points': 0,
            'achieve_points': 0,
            'detail_points': 0,
            'total_points': 0,
            'has_setting': False,
            'has_achieve': False,
            'has_detail': False
        }
        
        print(f"\n   📊 بررسی تارگت‌های اصلی ({len(targets)} مورد)...")
        
        for t in targets:
            created_by = t.get('created_by', '')
            created_by_norm = normalize_persian_text(created_by)
            
            if created_by_norm != agent_norm:
                continue
            
            if date is not None:
                created_at = t.get('created_at', '')
                if created_at:
                    if 'T' in created_at:
                        created_date = created_at.split('T')[0]
                    else:
                        created_date = created_at
                    try:
                        created_date_jalali = convert_to_jalali(created_date)
                        if created_date_jalali != date:
                            continue
                    except:
                        start_date = t.get('start_date', '')
                        if start_date and start_date != date:
                            continue
            
            status = t.get('status', '')
            if status in ['در انتظار', 'فعال', 'تکمیل شده']:
                config = target_settings.get('setting', {})
                if config.get('active', True) and not result['has_setting']:
                    result['setting_points'] = config.get('score', 100)
                    result['has_setting'] = True
                    print(f"   ✅ هدف‌گذاری: {t.get('target_id')} - {status}")
            
            achieved_value = t.get('achieved_value', 0)
            target_value = t.get('target_value', 0)
            if achieved_value > 0 and target_value > 0:
                config = target_settings.get('achieve', {})
                if config.get('active', True):
                    result['achieve_points'] += config.get('score', 25)
                    result['has_achieve'] = True
                    print(f"   ✅ تحقق تارگت: {t.get('target_id')} - {achieved_value:,}/{target_value:,}")
        
        # ریزتارگت‌ها
        detailed_targets = load_json_file('detailed_targets.json')
        if detailed_targets:
            print(f"\n   📊 بررسی ریزتارگت‌ها ({len(detailed_targets)} مورد)...")
            
            for dt in detailed_targets:
                created_by = dt.get('created_by', '')
                created_by_norm = normalize_persian_text(created_by)
                
                if created_by_norm != agent_norm:
                    continue
                
                if date is not None:
                    fulfilled_date = dt.get('fulfilled_date', '')
                    if fulfilled_date:
                        if fulfilled_date != date:
                            print(f"      ⏭ رد شد (تاریخ تحقق): {dt.get('id')} - {fulfilled_date} != {date}")
                            continue
                    else:
                        created_at = dt.get('created_at', '')
                        if created_at:
                            if 'T' in created_at:
                                created_date = created_at.split('T')[0]
                            else:
                                created_date = created_at
                            try:
                                created_date_jalali = convert_to_jalali(created_date)
                                if created_date_jalali != date:
                                    print(f"      ⏭ رد شد (تاریخ ایجاد): {dt.get('id')} - {created_date_jalali} != {date}")
                                    continue
                            except:
                                start_date = dt.get('start_date', '')
                                if start_date and start_date != date:
                                    print(f"      ⏭ رد شد (تاریخ شروع): {dt.get('id')} - {start_date} != {date}")
                                    continue
                        else:
                            start_date = dt.get('start_date', '')
                            if start_date and start_date != date:
                                print(f"      ⏭ رد شد (تاریخ شروع): {dt.get('id')} - {start_date} != {date}")
                                continue
                
                status = dt.get('status', '')
                fulfilled_date = dt.get('fulfilled_date', '')
                achieved_value = dt.get('achieved_value', 0)
                
                if status == 'تکمیل شده' or fulfilled_date or achieved_value > 0:
                    config = target_settings.get('detail', {})
                    if config.get('active', True):
                        points_per_detail = config.get('score', 25)
                        result['detail_points'] += points_per_detail
                        result['has_detail'] = True
                        print(f"   ✅ تحقق ریزتارگت: {dt.get('id')} - {dt.get('product_group', '')} - {status} - fulfilled: {fulfilled_date} - achieved: {achieved_value}")
                else:
                    print(f"      ⏭ رد شد (وضعیت): {dt.get('id')} - {status} - fulfilled: {fulfilled_date}")
        
        result['total_points'] = result['setting_points'] + result['achieve_points'] + result['detail_points']
        
        print(f"\n   📊 نتیجه تارگت‌ها:")
        print(f"      - هدف‌گذاری: {result['setting_points']}")
        print(f"      - تحقق تارگت: {result['achieve_points']}")
        print(f"      - تحقق ریزتارگت: {result['detail_points']}")
        print(f"      - جمع: {result['total_points']}")
        
        return result, "محاسبه شد"
        
    except Exception as e:
        print(f"خطا در محاسبه امتیاز تارگت: {e}")
        import traceback
        traceback.print_exc()
        return {}, str(e)


def get_report_submission_points(agent_name, date=None, settings=None):
    """
    محاسبه امتیاز ارسال گزارش روزانه (بررسی وجود فایل در پوشه reports)
    """
    try:
        if settings is None:
            settings = load_score_settings()
        
        from utils.storage import get_backup_path
        from utils.name_matcher import normalize_persian_text
        import os
        
        if date is None:
            from utils.jalali_date import get_today_jalali
            date = get_today_jalali()
        
        report_settings = settings.get('other', {}).get('report', {})
        if not report_settings.get('active', True):
            return 0, "امتیاز ارسال گزارش غیرفعال است"
        
        agent_norm = normalize_persian_text(agent_name)
        agent_name_with_underscore = agent_name.replace(' ', '_')
        agent_norm_with_underscore = agent_norm.replace(' ', '_')
        
        date_folder = date.replace('/', '-')
        reports_dir = os.path.join(get_backup_path(), 'daily_reports', date_folder)
        
        print(f"\n🔍 بررسی گزارش روزانه:")
        print(f"   مسیر: {reports_dir}")
        print(f"   نام کاربر: {agent_name}")
        print(f"   نام با زیرخط: {agent_name_with_underscore}")
        print(f"   نام نرمال‌سازی شده: {agent_norm}")
        print(f"   نام نرمال‌سازی شده با زیرخط: {agent_norm_with_underscore}")
        
        if not os.path.exists(reports_dir):
            print(f"   ❌ پوشه گزارشات وجود ندارد")
            return 0, "گزارش روزانه ارسال نشده"
        
        files = os.listdir(reports_dir)
        print(f"   📂 تعداد فایل‌ها: {len(files)}")
        
        for f in files:
            print(f"      - {f}")
        
        report_found = False
        found_files = []
        
        for filename in files:
            if not filename.endswith('.xlsx'):
                continue
            
            is_match = (
                agent_name in filename or
                agent_norm in filename or
                agent_name_with_underscore in filename or
                agent_norm_with_underscore in filename
            )
            
            if is_match:
                report_found = True
                found_files.append(filename)
                print(f"   ✅ گزارش یافت شد: {filename}")
        
        if not report_found:
            print(f"   ❌ هیچ گزارشی برای {agent_name} یافت نشد")
            return 0, "گزارش روزانه ارسال نشده"
        
        points = report_settings.get('score', 100)
        print(f"   ✅ امتیاز: {points}")
        return points, f"گزارش روزانه ارسال شده (امتیاز: {points})"
        
    except Exception as e:
        print(f"خطا در محاسبه امتیاز ارسال گزارش: {e}")
        import traceback
        traceback.print_exc()
        return 0, str(e)


def calculate_bonus(total_points, settings=None):
    """
    محاسبه پاداش بر اساس محدوده امتیاز
    
    پاداش = امتیاز روز × مبلغ پایه پاداش × ضریب
    
    محدوده‌ها:
    - کمتر از ۲۰۰: ضریب ۰ (بدون پاداش)
    - ۲۰۰ تا ۳۵۰: ضریب ۱
    - ۳۵۱ تا ۵۰۰: ضریب ۱.۵
    - ۵۰۱ به بالا: ضریب ۲
    """
    try:
        if settings is None:
            settings = load_score_settings()
        
        bonus_settings = settings.get('bonus', {})
        if not bonus_settings.get('active', False):
            return {
                'bonus_amount': 0,
                'bonus_percent': 0,
                'multiplier': 0
            }
        
        base_bonus = bonus_settings.get('percent', 0)
        
        if base_bonus <= 0:
            return {
                'bonus_amount': 0,
                'bonus_percent': 0,
                'multiplier': 0
            }
        
        if total_points < 200:
            multiplier = 0
            multiplier_display = "۰ (بدون پاداش)"
        elif 200 <= total_points <= 350:
            multiplier = 1.0
            multiplier_display = "۱"
        elif 351 <= total_points <= 500:
            multiplier = 1.5
            multiplier_display = "۱.۵"
        else:
            multiplier = 2.0
            multiplier_display = "۲"
        
        bonus_amount = int(total_points * base_bonus * multiplier)
        
        print(f"🎁 پاداش: {total_points} × {base_bonus:,} × {multiplier_display} = {bonus_amount:,} ریال")
        
        return {
            'bonus_amount': bonus_amount,
            'bonus_percent': 0,
            'multiplier': multiplier_display
        }
        
    except Exception as e:
        print(f"خطا در محاسبه پاداش: {e}")
        return {
            'bonus_amount': 0,
            'bonus_percent': 0,
            'multiplier': 0
        }


def check_day_ended_attendance(user_name, date=None):
    """
    بررسی پایان کار از طریق attendance.json (عمومی)
    """
    try:
        if date is None:
            from utils.jalali_date import get_today_jalali
            date = get_today_jalali()
        
        attendance_data = load_json_file('attendance.json')
        if not attendance_data:
            return False
        
        for record in attendance_data:
            if (record.get('user_name') == user_name and 
                record.get('date') == date and 
                record.get('is_day_ended', False)):
                return True
        
        return False
        
    except Exception as e:
        print(f"خطا در بررسی پایان کار حضوری: {e}")
        return False


def check_day_ended_marketing(agent_name, date=None):
    """
    بررسی پایان کار بازاریاب از طریق daily_summary.json
    """
    try:
        if date is None:
            from utils.jalali_date import get_today_jalali
            date = get_today_jalali()
        
        daily_summary = load_json_file('daily_summary.json')
        if not daily_summary:
            return False
        
        if date in daily_summary:
            summary = daily_summary[date]
            if isinstance(summary, dict) and summary.get('clock_out'):
                return True
        
        return False
        
    except Exception as e:
        print(f"خطا در بررسی پایان کار بازاریاب: {e}")
        return False


def check_day_ended_distributor(distributor_name, date=None):
    """
    بررسی پایان کار موزع از طریق distributor_summary.json
    """
    try:
        if date is None:
            from utils.jalali_date import get_today_jalali
            date = get_today_jalali()
        
        distributor_summary = load_json_file('distributor_summary.json')
        if not distributor_summary:
            return False
        
        if date in distributor_summary:
            summary = distributor_summary[date]
            if isinstance(summary, dict) and summary.get('dist_clock_out'):
                return True
        
        return False
        
    except Exception as e:
        print(f"خطا در بررسی پایان کار موزع: {e}")
        return False


def check_day_ended(username, role, date=None):
    """
    بررسی کامل پایان کار بر اساس نقش کاربر
    """
    try:
        if date is None:
            from utils.jalali_date import get_today_jalali
            date = get_today_jalali()
        
        result = {
            'ended': False,
            'source': 'none'
        }
        
        # 1. بررسی attendance.json (همه نقش‌ها)
        if check_day_ended_attendance(username, date):
            result['ended'] = True
            result['source'] = 'attendance'
            print(f"✅ پایان کار در attendance.json ثبت شده است")
            return result
        
        # 2. بررسی تخصصی بر اساس نقش
        if role == 'بازاریاب':
            if check_day_ended_marketing(username, date):
                result['ended'] = True
                result['source'] = 'daily_summary'
                print(f"✅ پایان کار در daily_summary.json ثبت شده است")
                return result
            else:
                print(f"⚠️ پایان کار در daily_summary.json ثبت نشده است")
        
        elif role == 'موزع':
            if check_day_ended_distributor(username, date):
                result['ended'] = True
                result['source'] = 'distributor_summary'
                print(f"✅ پایان کار در distributor_summary.json ثبت شده است")
                return result
            else:
                print(f"⚠️ پایان کار در distributor_summary.json ثبت نشده است")
        
        # سایر نقش‌ها: فقط attendance.json کافی است
        else:
            print(f"ℹ️ نقش {role} فقط نیاز به attendance.json دارد")
        
        return result
        
    except Exception as e:
        print(f"خطا در بررسی پایان کار: {e}")
        import traceback
        traceback.print_exc()
        return {'ended': False, 'source': 'none'}


def save_bonus(username, role, date=None):
    """
    ذخیره پاداش در فایل bonus_records.json
    """
    try:
        import os
        import json
        from datetime import datetime
        from utils.storage import get_data_path
        
        if date is None:
            from utils.jalali_date import get_today_jalali
            date = get_today_jalali()
        
        # محاسبه امتیازات و پاداش
        score_data = calculate_all_scores(username, role, date)
        bonus_amount = score_data.get('bonus_points', 0)
        
        if bonus_amount <= 0:
            print("⚠️ پاداشی برای ذخیره وجود ندارد")
            return False
        
        # ذخیره در فایل پاداش
        bonus_file = os.path.join(get_data_path(), 'bonus_records.json')
        
        if os.path.exists(bonus_file):
            with open(bonus_file, 'r', encoding='utf-8') as f:
                all_bonus = json.load(f)
        else:
            all_bonus = {}
        
        if username not in all_bonus:
            all_bonus[username] = {}
        
        all_bonus[username][date] = {
            'bonus_amount': bonus_amount,
            'total_points': score_data.get('total_points', 0),
            'multiplier': score_data.get('breakdown', {}).get('multiplier', 0),
            'saved_at': datetime.now().isoformat()
        }
        
        with open(bonus_file, 'w', encoding='utf-8') as f:
            json.dump(all_bonus, f, ensure_ascii=False, indent=2)
        
        print(f"✅ پاداش {bonus_amount:,} ریال برای {username} ذخیره شد")
        return True
        
    except Exception as e:
        print(f"خطا در ذخیره پاداش: {e}")
        return False


def calculate_all_scores(username, role, date=None):
    """
    محاسبه تمام امتیازات کاربر بر اساس نقش و تنظیمات
    """
    if not date:
        date = get_today_jalali()
    
    print(f"\n{'='*50}")
    print(f"🔍 محاسبه امتیازات برای: {username}")
    print(f"📅 تاریخ: {date}")
    print(f"🎭 نقش: {role}")
    print(f"{'='*50}")
    
    settings = load_score_settings()
    
    result = {
        'username': username,
        'role': role,
        'date': date,
        'attendance': {'points': 0, 'detail': ''},
        'end_day': {'points': 0, 'detail': ''},
        'mission': {'points': 0, 'count': 0, 'detail': ''},
        'visit': {'points': 0, 'detail': ''},
        'collection': {'points': 0, 'detail': ''},
        'report': {'points': 0, 'detail': ''},
        'delivery': {'points': 0, 'detail': ''},
        'market_visit': {'points': 0, 'count': 0, 'detail': ''},
        'target': {'points': 0, 'detail': ''},
        'total_points': 0,
        'bonus_points': 0,
        'breakdown': {}
    }
    
    # امتیاز حضور
    print(f"\n📌 بررسی حضور و غیاب...")
    att_points, att_detail = get_attendance_points(username, date, settings)
    result['attendance']['points'] = att_points
    result['attendance']['detail'] = att_detail
    print(f"   حضور: {att_points} امتیاز - {att_detail}")
    
    # امتیاز پایان کار
    print(f"\n📌 بررسی پایان کار...")
    end_day_points, end_day_detail = get_end_day_points(username, date, settings)
    result['end_day']['points'] = end_day_points
    result['end_day']['detail'] = end_day_detail
    print(f"   پایان کار: {end_day_points} امتیاز - {end_day_detail}")
    
    # امتیاز ماموریت (با تاریخ امروز) - برای بازاریاب، سوپروایزر و موزع
    if role in ['بازاریاب', 'سوپروایزر', 'موزع']:
        print(f"\n📌 بررسی ماموریت‌ها...")
        mission_points, mission_count, mission_detail = get_mission_points(username, date)
        result['mission']['points'] = mission_points
        result['mission']['count'] = mission_count
        result['mission']['detail'] = mission_detail
        print(f"   ماموریت‌ها: {mission_points} امتیاز - {mission_count} مورد - {mission_detail}")
    
    # امتیاز ویزیت و فروش (بازاریاب)
    if role == 'بازاریاب':
        print(f"\n📌 بررسی ویزیت‌ها...")
        visit_data, visit_detail = get_visit_points(username, date, settings)
        result['visit'] = visit_data
        result['visit']['detail'] = visit_detail
        print(f"   ویزیت‌ها: {visit_data.get('total_points', 0)} امتیاز")
        print(f"     - موفق: {visit_data.get('successful_visits', 0)}")
        print(f"     - ناموفق: {visit_data.get('failed_visits', 0)}")
        print(f"     - اولین ویزیت: {visit_data.get('has_first_visit', False)}")
        
        print(f"\n📌 بررسی وصول‌ها...")
        collection_data, collection_detail = get_collection_points(username, date, settings)
        result['collection'] = collection_data
        result['collection']['detail'] = collection_detail
        print(f"   وصول‌ها: {collection_data.get('total_points', 0)} امتیاز")
        print(f"     - موفق: {collection_data.get('success_count', 0)}")
        print(f"     - ناموفق: {collection_data.get('fail_count', 0)}")
    
    # ========== امتیازات سوپروایزر ==========
    if role == 'سوپروایزر':
        # امتیاز سرکشی بازار
        print(f"\n📌 بررسی سرکشی بازار...")
        market_points, market_count, market_detail = get_market_visit_points(username, date, settings)
        result['market_visit']['points'] = market_points
        result['market_visit']['count'] = market_count
        result['market_visit']['detail'] = market_detail
        print(f"   سرکشی بازار: {market_points} امتیاز - {market_count} مورد - {market_detail}")
        
        # امتیاز تارگت‌ها
        print(f"\n📌 بررسی تارگت‌ها...")
        target_data, target_detail = get_target_points(username, date, settings)
        result['target'] = target_data
        result['target']['detail'] = target_detail
        print(f"   تارگت‌ها: {target_data.get('total_points', 0)} امتیاز")
        print(f"     - هدف‌گذاری: {target_data.get('setting_points', 0)}")
        print(f"     - تحقق تارگت: {target_data.get('achieve_points', 0)}")
        print(f"     - تحقق ریزتارگت: {target_data.get('detail_points', 0)}")
    
    # ========== امتیازات موزع ==========
    if role == 'موزع':
        print(f"\n📌 بررسی توزیع‌ها...")
        delivery_data, delivery_detail = get_delivery_points(username, date, settings)
        result['delivery'] = delivery_data
        result['delivery']['detail'] = delivery_detail
        print(f"   توزیع‌ها: {delivery_data.get('total_points', 0)} امتیاز")
        print(f"     - موفق: {delivery_data.get('successful_deliveries', 0)}")
        print(f"     - ناموفق: {delivery_data.get('failed_deliveries', 0)}")
        print(f"     - تحویل کامل: {delivery_data.get('full_deliveries', 0)}")
        print(f"     - مبلغ کل: {delivery_data.get('total_cash', 0):,} ریال")
    
    # ========== ✅ گزارش روزانه (همه نقش‌ها) ==========
    print(f"\n📌 بررسی گزارش روزانه...")
    report_points, report_detail = get_report_submission_points(username, date, settings)
    result['report']['points'] = report_points
    result['report']['detail'] = report_detail
    print(f"   گزارش روزانه: {report_points} امتیاز - {report_detail}")
    
    # جمع کل امتیازات (بدون تغییر)
    total_points = (
        result['attendance']['points'] +
        result['end_day']['points'] +
        result['mission']['points'] +
        result.get('visit', {}).get('total_points', 0) +
        result.get('collection', {}).get('total_points', 0) +
        result.get('report', {}).get('points', 0) +
        result.get('delivery', {}).get('total_points', 0) +
        result.get('market_visit', {}).get('points', 0) +
        result.get('target', {}).get('total_points', 0)
    )
    result['total_points'] = total_points
    
    # ✅ محاسبه پاداش (به ریال)
    bonus_result = calculate_bonus(total_points, settings)
    result['bonus_points'] = bonus_result['bonus_amount']
    result['breakdown'] = {
        'base_points': total_points,
        'bonus_amount': bonus_result['bonus_amount'],
        'bonus_percent': bonus_result['bonus_percent'],
        'multiplier': bonus_result.get('multiplier', 0),
        'final_points': total_points + bonus_result['bonus_amount']
    }
    
    print(f"\n{'='*50}")
    print(f"✅ امتیاز روز: {total_points}")
    print(f"🎁 پاداش (ریال): {bonus_result['bonus_amount']:,}")
    print(f"🏆 جمع با پاداش: {total_points + bonus_result['bonus_amount']:,}")
    print(f"{'='*50}\n")
    
    return result