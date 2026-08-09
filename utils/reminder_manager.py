"""
مدیریت یادآوری‌ها و امتیازات کاربران
"""

import json
import os
from datetime import datetime
from utils.storage import get_data_path
from utils.jalali_date import get_today_jalali


def get_greeting_by_time(username):
    """
    دریافت پیام خوش‌آمدگویی بر اساس ساعت گوشی کاربر
    """
    try:
        now = datetime.now()
        hour = now.hour
        minute = now.minute
        time_value = hour + (minute / 60)
        
        if 0 <= time_value < 5:  # 00:00 تا 04:59
            line1 = f"نیمه شب بخیر {username} عزیز"
            line2 = "در آرامش باشی دوست من"
        elif 5 <= time_value < 10.5:  # 05:00 تا 10:29
            line1 = f"صبح بخیر {username} عزیز"
            line2 = "پر انرژی باش دوست من"
        elif 10.5 <= time_value < 12:  # 10:30 تا 11:59
            line1 = f"وقت بخیر {username} عزیز"
            line2 = "خدا قوت دوست من"
        elif 12 <= time_value < 14.5:  # 12:00 تا 14:29
            line1 = f"ظهر بخیر {username} عزیز"
            line2 = "ادامه بده دوست من"
        elif 14.5 <= time_value < 16.5:  # 14:30 تا 16:29
            line1 = f"بعدازظهر بخیر {username} عزیز"
            line2 = "تا موفقیت راهی نیست دوست من"
        elif 16.5 <= time_value < 19:  # 16:30 تا 18:59
            line1 = f"عصر بخیر {username} عزیز"
            line2 = "تلاشت ستودنیه دوست من"
        else:  # 19:00 تا 23:59
            line1 = f"شب بخیر {username} عزیز"
            line2 = "دیگه موقع استراحته نخسته دوست من"
        
        return line1, line2
        
    except Exception as e:
        print(f"خطا در دریافت ساعت: {e}")
        return f"سلام {username} عزیز", "روز خوبی داشته باشی"


def get_reminder_status(username):
    """دریافت وضعیت یادآوری برای کاربر"""
    try:
        file_path = os.path.join(get_data_path(), 'reminder_status.json')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                all_status = json.load(f)
                return all_status.get(username, {})
        return {}
    except Exception as e:
        print(f"خطا در خواندن وضعیت یادآوری: {e}")
        return {}


def save_reminder_status(username, status_data):
    """ذخیره وضعیت یادآوری برای کاربر"""
    try:
        file_path = os.path.join(get_data_path(), 'reminder_status.json')
        all_status = {}
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                all_status = json.load(f)
        
        all_status[username] = status_data
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(all_status, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"خطا در ذخیره وضعیت یادآوری: {e}")
        return False


def should_show_reminder(username):
    """بررسی اینکه آیا امروز باید یادآوری نمایش داده شود"""
    if not username:
        return False
    
    today = get_today_jalali()
    status = get_reminder_status(username)
    
    if not status:
        return True
    
    last_date = status.get('last_reminder_date', '')
    completed = status.get('reminder_completed', False)
    
    if last_date != today or not completed:
        return True
    
    return False


def mark_reminder_shown(username):
    """ثبت اینکه یادآوری امروز نمایش داده شده"""
    if not username:
        return False
    
    today = get_today_jalali()
    status = get_reminder_status(username)
    
    status['last_reminder_date'] = today
    status['reminder_shown'] = True
    status['reminder_completed'] = False
    
    return save_reminder_status(username, status)


def mark_reminder_completed(username, score_data):
    """ثبت اینکه کاربر عملیات یادآوری را انجام داده"""
    if not username:
        return False
    
    today = get_today_jalali()
    status = get_reminder_status(username)
    
    status['last_reminder_date'] = today
    status['reminder_completed'] = True
    status['points_earned'] = status.get('points_earned', 0) + score_data.get('total_points', 0)
    status['total_reminders_completed'] = status.get('total_reminders_completed', 0) + 1
    status['last_score'] = score_data
    
    return save_reminder_status(username, status)


def get_total_points(username):
    """دریافت مجموع امتیازات کاربر"""
    if not username:
        return 0
    status = get_reminder_status(username)
    return status.get('points_earned', 0)


def get_reminder_messages_by_role(role):
    """دریافت پیام‌های یادآوری بر اساس نقش"""
    messages = {
        'بازاریاب': """
 **یادآوری روزانه**

دوست من، لطفاً امروز این کارها رو انجام بده:
• گزارش عملکرد روزانه رو ثبت کن
• ماموریت‌های در انتظار رو بررسی کن
• ویزیت‌های روزانه رو ثبت کن

 پس از انجام، امتیاز ویژه دریافت می‌کنی!
""",
        'سوپروایزر': """
 **یادآوری روزانه**

دوست من، لطفاً امروز این کارها رو انجام بده:
• گزارشات سرکشی رو ثبت کن
• ماموریت‌های تعیین تکلیف نشده رو بررسی کن

 پس از انجام، امتیاز ویژه دریافت می‌کنی!
""",
        'موزع': """
 **یادآوری روزانه**

دوست من، لطفاً امروز این کارها رو انجام بده:
• گزارش توزیع روزانه رو ثبت کن
• وصول‌ها رو ثبت کن

 پس از انجام، امتیاز ویژه دریافت می‌کنی!
"""
    }
    return messages.get(role, messages['بازاریاب'])