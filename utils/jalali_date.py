"""
توابع کمکی برای کار با تاریخ شمسی - نسخه بدون وابستگی به jdatetime
"""

import datetime
import re


def to_jalali(gy, gm, gd):
    """تبدیل تاریخ میلادی به شمسی"""
    g_days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    j_days_in_month = [31, 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 29]

    gy = gy - 1600
    gm = gm - 1
    gd = gd - 1

    g_day_no = 365 * gy + (gy + 3) // 4 - (gy + 99) // 100 + (gy + 399) // 400

    for i in range(gm):
        g_day_no += g_days_in_month[i]
    if gm > 1 and ((gy % 4 == 0 and gy % 100 != 0) or (gy % 400 == 0)):
        g_day_no += 1
    g_day_no += gd

    j_day_no = g_day_no - 79

    j_np = j_day_no // 12053
    j_day_no %= 12053

    jy = 979 + 33 * j_np + 4 * (j_day_no // 1461)
    j_day_no %= 1461

    if j_day_no >= 366:
        jy += (j_day_no - 1) // 365
        j_day_no = (j_day_no - 1) % 365

    for i in range(11):
        if j_day_no >= j_days_in_month[i]:
            j_day_no -= j_days_in_month[i]
        else:
            break

    jm = i + 1
    jd = j_day_no + 1

    return f"{jy:04d}/{jm:02d}/{jd:02d}"


def get_today_jalali():
    """تاریخ امروز به شمسی (فرمت: 1402/01/15)"""
    now = datetime.datetime.now()
    return to_jalali(now.year, now.month, now.day)


def get_current_jalali_date():
    """دریافت تاریخ شمسی جاری (همان get_today_jalali)"""
    return get_today_jalali()


def get_current_time():
    """ساعت الان (فرمت: 14:30)"""
    return datetime.datetime.now().strftime('%H:%M')


def convert_to_jalali(date_str):
    """تبدیل تاریخ میلادی به شمسی"""
    if not date_str:
        return ""
    try:
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        return to_jalali(date_obj.year, date_obj.month, date_obj.day)
    except:
        return date_str


def convert_to_gregorian(jalali_str):
    """تبدیل تاریخ شمسی به میلادی"""
    if not jalali_str:
        return ""
    
    j_days_in_month = [31, 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 29]
    
    try:
        parts = jalali_str.split('/')
        if len(parts) != 3:
            return jalali_str
        
        jy = int(parts[0])
        jm = int(parts[1])
        jd = int(parts[2])
        
        jy = jy - 979
        jm = jm - 1
        jd = jd - 1
        
        j_day_no = 365 * jy + (jy // 33) * 8 + ((jy % 33) + 3) // 4
        
        for i in range(jm):
            j_day_no += j_days_in_month[i]
        
        j_day_no += jd
        
        g_day_no = j_day_no + 79
        
        gy = 1600 + 400 * (g_day_no // 146097)
        g_day_no = g_day_no % 146097
        
        leap = True
        if g_day_no >= 36525:
            g_day_no -= 36525
            gy += 100
            leap = False
        
        if g_day_no >= 365:
            g_day_no -= 365
            gy += 1
        
        if leap:
            g_days_in_month = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        else:
            g_days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        
        gm = 0
        for i in range(12):
            if g_day_no < g_days_in_month[i]:
                gm = i + 1
                gd = g_day_no + 1
                break
            g_day_no -= g_days_in_month[i]
        
        return f"{gy:04d}-{gm:02d}-{gd:02d}"
    except:
        return jalali_str


def validate_jalali_date(date_str):
    """اعتبارسنجی تاریخ شمسی"""
    pattern = r'^(\d{4})/(\d{2})/(\d{2})$'
    match = re.match(pattern, date_str)
    if not match:
        return False
    
    jy = int(match.group(1))
    jm = int(match.group(2))
    jd = int(match.group(3))
    
    if jy < 1 or jm < 1 or jm > 12 or jd < 1:
        return False
    
    j_days_in_month = [31, 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 29]
    if jd > j_days_in_month[jm - 1]:
        return False
    
    return True


def get_jalali_month_days(year, month):
    """تعداد روزهای یک ماه شمسی"""
    if 1 <= month <= 6:
        return 31
    elif 7 <= month <= 11:
        return 30
    else:
        leap_years = {1, 5, 9, 13, 17, 22, 26, 30}
        year_mod = year % 33
        if year_mod in leap_years:
            return 30
        return 29


def get_weekday_jalali(date_str):
    """دریافت نام روز هفته به فارسی"""
    days = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه']
    try:
        parts = date_str.split('/')
        if len(parts) != 3:
            return ""
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        
        greg = convert_to_gregorian(date_str)
        if greg:
            dt = datetime.datetime.strptime(greg, '%Y-%m-%d')
            return days[(dt.weekday() + 2) % 7]
        return ""
    except:
        return ""


def get_jalali_months():
    """دریافت لیست ماه‌های شمسی"""
    return ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
            'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']


def format_jalali_date(year, month, day):
    """فرمت کردن تاریخ شمسی"""
    try:
        return f"{year:04d}/{month:02d}/{day:02d}"
    except:
        return ""
    
def _add_jalali_days(date_str: str, days: int) -> str:
    """افزودن تعداد روز به تاریخ شمسی"""
    try:
        gregorian_date = convert_to_gregorian(date_str)
        if not gregorian_date or gregorian_date == date_str:
            return date_str
        
        date_obj = datetime.strptime(gregorian_date, '%Y-%m-%d')
        end_date_obj = date_obj + timedelta(days=days)
        end_date_str = to_jalali(end_date_obj.year, end_date_obj.month, end_date_obj.day)
        return end_date_str
        
    except Exception as e:
        logger.error(f"خطا در add_jalali_days: {e}")
        return date_str


def _add_jalali_months(date_str: str, months: int) -> str:
    """افزودن تعداد ماه به تاریخ شمسی"""
    try:
        parts = date_str.split('/')
        if len(parts) != 3:
            return date_str
        
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        
        new_month = month + months
        new_year = year
        
        while new_month > 12:
            new_month -= 12
            new_year += 1
        
        while new_month < 1:
            new_month += 12
            new_year -= 1
        
        # تنظیم روز (اگر روز بیشتر از روزهای ماه باشد)
        import jdatetime
        max_day = jdatetime.date(new_year, new_month, 1).days_in_month
        if day > max_day:
            day = max_day
        
        return f"{new_year:04d}/{new_month:02d}/{day:02d}"
        
    except Exception as e:
        logger.error(f"خطا در add_jalali_months: {e}")
        return date_str


def _add_jalali_years(date_str: str, years: int) -> str:
    """افزودن تعداد سال به تاریخ شمسی"""
    try:
        parts = date_str.split('/')
        if len(parts) != 3:
            return date_str
        
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        new_year = year + years
        
        # تنظیم روز (اگر روز بیشتر از روزهای ماه باشد)
        import jdatetime
        max_day = jdatetime.date(new_year, month, 1).days_in_month
        if day > max_day:
            day = max_day
        
        return f"{new_year:04d}/{month:02d}/{day:02d}"
        
    except Exception as e:
        logger.error(f"خطا در add_jalali_years: {e}")
        return date_str