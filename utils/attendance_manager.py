# utils/attendance_manager.py
# ========== مدیریت حضور و غیاب پرسنل ==========

import os
import json
import shutil
from datetime import datetime
from utils.jalali_date import get_today_jalali
from utils.storage import get_data_path
from utils.file_manager import get_agents, get_settings  # ✅ اضافه شدن get_settings


class AttendanceManager:
    """کلاس مدیریت حضور و غیاب پرسنل"""
    
    @staticmethod
    def get_attendance_file():
        """دریافت مسیر فایل حضور و غیاب"""
        data_path = get_data_path()
        return os.path.join(data_path, 'attendance.json')
    
    @staticmethod
    def get_config_file():
        """دریافت مسیر فایل تنظیمات"""
        data_path = get_data_path()
        return os.path.join(data_path, 'attendance_config.json')
    
    @staticmethod
    def get_default_config():
        """دریافت تنظیمات پیش‌فرض"""
        return {
            'late_threshold': 15,
            'early_leave_threshold': 15,
            'max_attendance_days': 30,
            'weekend_days': ['پنجشنبه', 'جمعه'],
            'holidays': [],
            'leave_types': ['ساعتی', 'استحقاقی', 'استعلاجی', 'اضطراری', 'بدون حقوق'],
            'statuses': ['حضور', 'غیبت', 'مرخصی', 'ماموریت', 'تاخیر', 'خروج زودتر'],
            'annual_leave_limit': 30,
            'monthly_hourly_leave_limit': '10:00',
            'hourly_to_daily_ratio': 5
        }
    
    @staticmethod
    def get_work_hours():
        """دریافت ساعات کاری از settings.json"""
        settings = get_settings()
        return {
            'work_start_time': settings.get('work_start_time', '08:00'),
            'work_end_time': settings.get('work_end_time', '17:00'),
            'min_daily_hours': settings.get('min_daily_hours', 7)
        }
    
    @staticmethod
    def load_attendance():
        """بارگذاری داده‌های حضور و غیاب"""
        file_path = AttendanceManager.get_attendance_file()
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    @staticmethod
    def save_attendance(data):
        """ذخیره داده‌های حضور و غیاب"""
        file_path = AttendanceManager.get_attendance_file()
        
        if os.path.exists(file_path):
            backup_path = file_path + '.backup'
            shutil.copy2(file_path, backup_path)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def load_config():
        """بارگذاری تنظیمات حضور و غیاب"""
        file_path = AttendanceManager.get_config_file()
        default_config = AttendanceManager.get_default_config()
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except:
                return default_config
        return default_config
    
    @staticmethod
    def save_config(config):
        """ذخیره تنظیمات حضور و غیاب"""
        file_path = AttendanceManager.get_config_file()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    
    @staticmethod
    def check_in(user_id, date=None, time=None, note=''):
        """ثبت ورود - بدون محدودیت روزانه"""
        if date is None:
            date = get_today_jalali()
        if time is None:
            time = datetime.now().strftime('%H:%M')
        
        attendance = AttendanceManager.load_attendance()
        
        # دریافت اطلاعات پرسنل از get_agents
        personnel = get_agents()
        user_info = next((u for u in personnel if u.get('id') == user_id), {})
        
        # ✅ دریافت ساعات کاری از settings.json
        work_hours = AttendanceManager.get_work_hours()
        work_start = work_hours.get('work_start_time', '08:00')
        
        # بررسی تاخیر
        config = AttendanceManager.load_config()
        is_late = time > work_start
        late_minutes = 0
        if is_late:
            start_hour, start_min = map(int, work_start.split(':'))
            hour, minute = map(int, time.split(':'))
            late_minutes = (hour - start_hour) * 60 + (minute - start_min)
        
        record = {
            'user_id': user_id,
            'user_name': user_info.get('name', ''),
            'username': user_info.get('username', ''),
            'role': user_info.get('role', ''),
            'date': date,
            'check_in': time,
            'check_out': None,
            'status': 'تاخیر' if is_late and late_minutes > config.get('late_threshold', 15) else 'حضور',
            'late_minutes': late_minutes if is_late else 0,
            'early_minutes': 0,
            'leave_type': None,
            'leave_duration': None,
            'is_leave': False,
            'is_mission': False,
            'note': note,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'is_finalized': False
        }
        
        attendance.append(record)
        AttendanceManager.save_attendance(attendance)
        return True, 'ورود با موفقیت ثبت شد'
    
    @staticmethod
    def check_out(user_id, date=None, time=None, note=''):
        """ثبت خروج - بدون محدودیت روزانه"""
        if date is None:
            date = get_today_jalali()
        if time is None:
            time = datetime.now().strftime('%H:%M')
        
        attendance = AttendanceManager.load_attendance()
        
        # پیدا کردن آخرین رکورد امروز که خروج ندارد
        today_records = [r for r in attendance if r.get('user_id') == user_id and r.get('date') == date]
        
        record = None
        for r in reversed(today_records):
            if r.get('check_in') and not r.get('check_out'):
                record = r
                break
        
        # اگر رکوردی برای خروج پیدا نشد، یک رکورد جدید با زمان ورود و خروج همزمان ثبت کن
        if not record:
            personnel = get_agents()
            user_info = next((u for u in personnel if u.get('id') == user_id), {})
            
            # ✅ دریافت ساعات کاری از settings.json
            work_hours = AttendanceManager.get_work_hours()
            work_start = work_hours.get('work_start_time', '08:00')
            
            config = AttendanceManager.load_config()
            is_late = time > work_start
            late_minutes = 0
            if is_late:
                start_hour, start_min = map(int, work_start.split(':'))
                hour, minute = map(int, time.split(':'))
                late_minutes = (hour - start_hour) * 60 + (minute - start_min)
            
            new_record = {
                'user_id': user_id,
                'user_name': user_info.get('name', ''),
                'username': user_info.get('username', ''),
                'role': user_info.get('role', ''),
                'date': date,
                'check_in': time,
                'check_out': time,
                'status': 'تاخیر' if is_late and late_minutes > config.get('late_threshold', 15) else 'حضور',
                'late_minutes': late_minutes if is_late else 0,
                'early_minutes': 0,
                'leave_type': None,
                'leave_duration': None,
                'is_leave': False,
                'is_mission': False,
                'note': note,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'is_finalized': False
            }
            
            attendance.append(new_record)
            AttendanceManager.save_attendance(attendance)
            return True, 'خروج با موفقیت ثبت شد (ورود و خروج همزمان)'
        
        # ✅ دریافت ساعات کاری از settings.json
        work_hours = AttendanceManager.get_work_hours()
        work_end = work_hours.get('work_end_time', '17:00')
        
        # بررسی خروج زودتر
        config = AttendanceManager.load_config()
        is_early = time < work_end
        early_minutes = 0
        if is_early:
            end_hour, end_min = map(int, work_end.split(':'))
            hour, minute = map(int, time.split(':'))
            early_minutes = (end_hour - hour) * 60 + (end_min - minute)
        
        record['check_out'] = time
        if is_early and early_minutes > config.get('early_leave_threshold', 15):
            record['status'] = 'خروج زودتر'
        elif record.get('status') == 'حضور':
            record['status'] = 'حضور'
        record['early_minutes'] = early_minutes if is_early else 0
        record['updated_at'] = datetime.now().isoformat()
        record['note'] = note if note else record.get('note', '')
        
        AttendanceManager.save_attendance(attendance)
        return True, 'خروج با موفقیت ثبت شد'
    
    @staticmethod
    def register_leave(user_id, date, leave_type, duration, note=''):
        """ثبت مرخصی"""
        attendance = AttendanceManager.load_attendance()
        
        personnel = get_agents()
        user_info = next((u for u in personnel if u.get('id') == user_id), {})
        
        record = {
            'user_id': user_id,
            'user_name': user_info.get('name', ''),
            'username': user_info.get('username', ''),
            'role': user_info.get('role', ''),
            'date': date,
            'check_in': None,
            'check_out': None,
            'status': 'مرخصی',
            'late_minutes': 0,
            'early_minutes': 0,
            'leave_type': leave_type,
            'leave_duration': duration,
            'is_leave': True,
            'is_mission': False,
            'note': note,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'is_finalized': False
        }
        
        attendance.append(record)
        AttendanceManager.save_attendance(attendance)
        return True, 'مرخصی با موفقیت ثبت شد'
    
    @staticmethod
    def register_mission(user_id, date, note=''):
        """ثبت ماموریت"""
        attendance = AttendanceManager.load_attendance()
        
        personnel = get_agents()
        user_info = next((u for u in personnel if u.get('id') == user_id), {})
        
        record = {
            'user_id': user_id,
            'user_name': user_info.get('name', ''),
            'username': user_info.get('username', ''),
            'role': user_info.get('role', ''),
            'date': date,
            'check_in': None,
            'check_out': None,
            'status': 'ماموریت',
            'late_minutes': 0,
            'early_minutes': 0,
            'leave_type': None,
            'leave_duration': None,
            'is_leave': False,
            'is_mission': True,
            'note': note,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'is_finalized': False
        }
        
        attendance.append(record)
        AttendanceManager.save_attendance(attendance)
        return True, 'ماموریت با موفقیت ثبت شد'
    
    @staticmethod
    def get_daily_report(date=None, user_id=None):
        """دریافت گزارش روزانه"""
        if date is None:
            date = get_today_jalali()
        
        attendance = AttendanceManager.load_attendance()
        records = [r for r in attendance if r.get('date') == date]
        
        if user_id:
            records = [r for r in records if r.get('user_id') == user_id]
        
        return records
    
    @staticmethod
    def get_user_status(user_id, date=None):
        """دریافت وضعیت یک کاربر در تاریخ مشخص"""
        if date is None:
            date = get_today_jalali()
        
        attendance = AttendanceManager.load_attendance()
        records = [r for r in attendance if r.get('user_id') == user_id and r.get('date') == date]
        
        if records:
            return records[-1]
        return None