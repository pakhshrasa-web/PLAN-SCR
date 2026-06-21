"""
توابع کمکی برای کار با تاریخ شمسی - نسخه کامل و بهینه
"""

import jdatetime
from datetime import datetime

def get_today_jalali():
    """تاریخ امروز به شمسی (فرمت: 1402/01/15)"""
    return jdatetime.date.today().strftime('%Y/%m/%d')

def get_current_time():
    """ساعت الان (فرمت: 14:30)"""
    return datetime.now().strftime('%H:%M')

def convert_to_jalali(date_str):
    """تبدیل تاریخ میلادی به شمسی"""
    if not date_str:
        return ""
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        jdate = jdatetime.datetime.fromgregorian(datetime=date_obj)
        return jdate.strftime('%Y/%m/%d')
    except:
        return date_str

def convert_to_gregorian(jalali_str):
    """تبدیل تاریخ شمسی به میلادی"""
    if not jalali_str:
        return ""
    try:
        parts = jalali_str.split('/')
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        jd = jdatetime.date(year, month, day)
        gregorian = jd.togregorian()
        return gregorian.strftime('%Y-%m-%d')
    except:
        return jalali_str

def validate_jalali_date(date_str):
    """اعتبارسنجی تاریخ شمسی"""
    try:
        parts = date_str.split('/')
        if len(parts) != 3:
            return False
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        jdatetime.date(year, month, day)
        return True
    except:
        return False

def get_jalali_month_days(year, month):
    """تعداد روزهای یک ماه شمسی"""
    if 1 <= month <= 6:
        return 31
    elif 7 <= month <= 11:
        return 30
    else:
        try:
            jd = jdatetime.date(year, 12, 30)
            return 30 if jd.month == 12 else 29
        except:
            return 29

def get_weekday_jalali(date_str):
    """دریافت نام روز هفته به فارسی"""
    days = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه']
    try:
        parts = date_str.split('/')
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        jd = jdatetime.date(year, month, day)
        return days[jd.weekday()]
    except:
        return ""

def get_jalali_months():
    """دریافت لیست ماه‌های شمسی"""
    return ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
            'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']

def format_jalali_date(year, month, day):
    """فرمت کردن تاریخ شمسی"""
    try:
        return jdatetime.date(year, month, day).strftime('%Y/%m/%d')
    except:
        return ""