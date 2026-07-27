"""
مدیریت ریزتارگت‌ها
"""

import os
import json
import random
import string
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from kivy.logger import Logger as logger
from utils.storage import get_data_path
from utils.jalali_date import (
    get_today_jalali,
    get_current_time,
    convert_to_gregorian,
    validate_jalali_date,
    to_jalali
)

DETAILED_TARGETS_FILE = 'detailed_targets.json'


def _get_path() -> str:
    """دریافت مسیر فایل ریزتارگت‌ها"""
    return os.path.join(get_data_path(), DETAILED_TARGETS_FILE)


def _load() -> List[Dict]:
    """بارگذاری همه ریزتارگت‌ها"""
    try:
        path = _get_path()
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"خطا در بارگذاری ریزتارگت‌ها: {e}")
        return []


def _save(data: List[Dict]) -> bool:
    """ذخیره ریزتارگت‌ها"""
    try:
        path = _get_path()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"خطا در ذخیره ریزتارگت‌ها: {e}")
        return False


def _generate_id() -> str:
    """تولید آیدی یکتا"""
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(random.choices(chars, k=4))
    return f"DTG{random_part}"


def _calculate_end_date(start_date: str, period: str, duration: int) -> str:
    """
    محاسبه تاریخ پایان بر اساس تقویم شمسی واقعی
    
    Args:
        start_date: تاریخ شروع (مثال: 1405/05/01)
        period: روزانه / ماهانه / فصلی / سالیانه
        duration: تعداد دوره
    
    Returns:
        تاریخ پایان شمسی - همیشه آخرین روز ماه/دوره
    """
    try:
        parts = start_date.split('/')
        if len(parts) != 3:
            return start_date
        
        jy = int(parts[0])
        jm = int(parts[1])
        jd = int(parts[2])
        
        def get_month_days(year, month):
            """تعداد روزهای واقعی هر ماه شمسی"""
            if 1 <= month <= 6:
                return 31
            elif 7 <= month <= 11:
                return 30
            else:  # اسفند
                leap_years = {1, 5, 9, 13, 17, 22, 26, 30}
                year_mod = year % 33
                return 30 if year_mod in leap_years else 29
        
        if period == 'روزانه':
            # هر روز = ۱ روز اضافه
            total_days = jd
            current_year, current_month = jy, jm
            
            for _ in range(duration - 1):  # -۱ چون روز شروع رو حساب کردیم
                total_days += 1
                if total_days > get_month_days(current_year, current_month):
                    total_days = 1
                    current_month += 1
                    if current_month > 12:
                        current_month = 1
                        current_year += 1
            
            return f"{current_year:04d}/{current_month:02d}/{total_days:02d}"
            
        elif period == 'ماهانه':
            # ✅ محاسبه ماه آخر دوره
            total_months = jm + duration - 1  # -۱ چون ماه جاری رو حساب می‌کنیم
            current_year = jy
            
            while total_months > 12:
                total_months -= 12
                current_year += 1
            
            # ✅ آخرین روز ماه مقصد (نه min با روز شروع)
            last_day = get_month_days(current_year, total_months)
            
            return f"{current_year:04d}/{total_months:02d}/{last_day:02d}"
            
        elif period == 'فصلی':
            # هر فصل = ۳ ماه
            total_months = jm + (duration * 3) - 1
            current_year = jy
            
            while total_months > 12:
                total_months -= 12
                current_year += 1
            
            last_day = get_month_days(current_year, total_months)
            
            return f"{current_year:04d}/{total_months:02d}/{last_day:02d}"
            
        elif period == 'سالیانه':
            current_year = jy + duration
            last_day = get_month_days(current_year, jm)
            
            return f"{current_year:04d}/{jm:02d}/{last_day:02d}"
            
        else:
            return start_date
        
    except Exception as e:
        logger.error(f"خطا در محاسبه تاریخ پایان: {e}")
        return start_date


def _calculate_daily_target(target_count: int, period: str, duration: int) -> int:
    """
    محاسبه تارگت روزانه
    
    روزانه: / duration
    ماهانه: / (duration × 26)
    فصلی:   / (duration × 78)  (3 ماه × 26)
    سالیانه: / (duration × 312) (12 ماه × 26)
    """
    if period == 'روزانه':
        divisor = duration
    elif period == 'ماهانه':
        divisor = duration * 26
    elif period == 'فصلی':
        divisor = duration * 78  # 3 × 26
    elif period == 'سالیانه':
        divisor = duration * 312  # 12 × 26
    else:
        divisor = duration
    
    if divisor <= 0:
        return target_count
    
    return max(1, round(target_count / divisor))


def create_detailed_target(
    agent_name: str,
    product_group: str,
    target_count: int,
    unit: str,
    period: str,
    duration: int,
    linked_target_id: str,
    start_date: str = '',
    created_by: str = 'supervisor'
) -> Tuple[bool, str, Optional[Dict]]:
    """ایجاد ریزتارگت جدید"""
    try:
        if not agent_name:
            return False, 'نام عامل الزامی است', None
        
        if not product_group:
            return False, 'گروه کالا الزامی است', None
        
        if target_count <= 0:
            return False, 'تعداد هدف باید بزرگتر از صفر باشد', None
        
        if not unit:
            return False, 'واحد تارگت الزامی است', None
        
        if not period:
            return False, 'دوره تارگت الزامی است', None
        
        if duration <= 0:
            return False, 'مدت باید بزرگتر از صفر باشد', None
        
        if not linked_target_id:
            return False, 'پیوند به تارگت اصلی الزامی است', None
        
        if not start_date:
            start_date = get_today_jalali()
        
        if not validate_jalali_date(start_date):
            return False, 'تاریخ شروع نامعتبر است', None
        
        # محاسبه تاریخ پایان با تقویم واقعی شمسی
        end_date = _calculate_end_date(start_date, period, duration)
        
        # محاسبه تارگت روزانه
        daily_target = _calculate_daily_target(target_count, period, duration)
        
        # تولید آیدی
        target_id = _generate_id()
        
        target = {
            'id': target_id,
            'agent_name': agent_name,
            'product_group': product_group,
            'target_count': target_count,
            'unit': unit,
            'period': period,
            'duration': duration,
            'linked_target_id': linked_target_id,
            'start_date': start_date,
            'end_date': end_date,
            'daily_target': daily_target,
            'status': 'در انتظار',
            'achieved_value': 0,
            'created_at': datetime.now().isoformat(),
            'created_by': created_by
        }
        
        data = _load()
        data.append(target)
        
        if _save(data):
            logger.info(f"ریزتارگت جدید: {target_id}")
            return True, f'ریزتارگت با شناسه {target_id} ثبت شد', target
        else:
            return False, 'خطا در ذخیره', None
        
    except Exception as e:
        logger.error(f"خطا: {e}")
        return False, f'خطا: {str(e)}', None


def get_all_detailed_targets() -> List[Dict]:
    """دریافت همه ریزتارگت‌ها"""
    return _load()


def get_targets_by_agent(agent_name: str) -> List[Dict]:
    """دریافت ریزتارگت‌های یک عامل"""
    data = _load()
    return [t for t in data if t.get('agent_name') == agent_name]


def get_targets_by_status(status: str) -> List[Dict]:
    """دریافت ریزتارگت‌ها بر اساس وضعیت"""
    data = _load()
    return [t for t in data if t.get('status') == status]


def can_edit_target(target: Dict) -> bool:
    """بررسی قابلیت ویرایش (تحقق نیافته + حداکثر ۱۰ روز از ایجاد)"""
    try:
        status = target.get('status', '')
        if status in ['تکمیل شده', 'لغو شده']:
            return False
        
        created_at = target.get('created_at', '')
        if not created_at:
            return True
        
        created_date = datetime.fromisoformat(created_at)
        now = datetime.now()
        days_diff = (now - created_date).days
        
        return days_diff <= 10
        
    except Exception as e:
        logger.error(f"خطا: {e}")
        return False


def update_detailed_target(target_id: str, updates: Dict) -> Tuple[bool, str]:
    """به‌روزرسانی ریزتارگت"""
    try:
        data = _load()
        
        for i, target in enumerate(data):
            if target.get('id') == target_id:
                if not can_edit_target(target):
                    return False, 'این ریزتارگت قابل ویرایش نیست'
                
                allowed = ['product_group', 'target_count', 'unit', 'period', 
                          'duration', 'linked_target_id', 'start_date']
                
                for field, value in updates.items():
                    if field in allowed:
                        target[field] = value
                
                # بازمحاسبه daily_target و end_date
                target['daily_target'] = _calculate_daily_target(
                    target.get('target_count', 0),
                    target.get('period', ''),
                    target.get('duration', 1)
                )
                target['end_date'] = _calculate_end_date(
                    target.get('start_date', ''),
                    target.get('period', ''),
                    target.get('duration', 1)
                )
                
                if _save(data):
                    return True, 'به‌روزرسانی موفق'
                else:
                    return False, 'خطا در ذخیره'
        
        return False, 'ریزتارگت یافت نشد'
        
    except Exception as e:
        return False, f'خطا: {str(e)}'


def delete_detailed_target(target_id: str) -> Tuple[bool, str]:
    """حذف ریزتارگت"""
    try:
        data = _load()
        
        for i, target in enumerate(data):
            if target.get('id') == target_id:
                if not can_edit_target(target):
                    return False, 'این ریزتارگت قابل حذف نیست'
                
                data.pop(i)
                
                if _save(data):
                    return True, 'حذف موفق'
                else:
                    return False, 'خطا در ذخیره'
        
        return False, 'ریزتارگت یافت نشد'
        
    except Exception as e:
        return False, f'خطا: {str(e)}'


def export_to_excel(targets: List[Dict], filename: str = None) -> Tuple[bool, str, str]:
    """خروجی اکسل ریزتارگت‌ها"""
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        from openpyxl.utils import get_column_letter
        from utils.storage import get_backup_path
        
        if not targets:
            return False, 'هیچ ریزتارگتی وجود ندارد', ''
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "ریزتارگت‌ها"
        
        header_font = Font(bold=True, size=10, color="FFFFFF")
        header_fill = PatternFill(start_color="2E86C1", end_color="2E86C1", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        thin_border = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin')
        )
        
        headers = [
            'شناسه ریزتارگت',
            'نام عامل',
            'دوره تارگت',
            'تاریخ شروع',        # ✅ همون start_date که سوپروایزر وارد کرده
            'تاریخ پایان',        # ✅ محاسبه‌شده با تقویم واقعی
            'تاریخ ایجاد',        # ✅ created_at تبدیل به شمسی
            'نام گروه کالا',
            'تعداد تارگت',
            'واحد تارگت',
            'پیوند با تارگت مادر',
            'تارگت روزانه'
        ]
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border
        
        for row, target in enumerate(targets, 2):
            # تاریخ ایجاد رو از isoformat به شمسی تبدیل کن
            created_at = target.get('created_at', '')
            created_date = ''
            if created_at:
                try:
                    dt = datetime.fromisoformat(created_at)
                    created_date = to_jalali(dt.year, dt.month, dt.day)
                except:
                    created_date = created_at[:10]
            
            values = [
                target.get('id', ''),
                target.get('agent_name', ''),
                target.get('period', ''),
                target.get('start_date', ''),       # ✅ تاریخ شروع (همونی که کاربر وارد کرده)
                target.get('end_date', ''),         # ✅ تاریخ پایان (محاسبه‌شده)
                created_date,                        # ✅ تاریخ ایجاد (تبدیل به شمسی)
                target.get('product_group', ''),
                target.get('target_count', 0),
                target.get('unit', ''),
                target.get('linked_target_id', ''),
                target.get('daily_target', 0)
            ]
            
            for col, value in enumerate(values, 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.alignment = Alignment(horizontal='center', vertical='center')
                cell.border = thin_border
        
        column_widths = [16, 18, 12, 14, 14, 14, 18, 14, 12, 20, 16]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = width
        
        if not filename:
            today = get_today_jalali().replace('/', '-')
            timestamp = datetime.now().strftime('%H%M%S')
            filename = f'ریزتارگت_{today}_{timestamp}.xlsx'
        
        export_dir = get_backup_path()
        os.makedirs(export_dir, exist_ok=True)
        filepath = os.path.join(export_dir, filename)
        
        wb.save(filepath)
        return True, f'فایل ذخیره شد:\n{filename}', filepath
        
    except ImportError:
        return False, 'ماژول openpyxl نصب نیست', ''
    except Exception as e:
        return False, f'خطا: {str(e)}', ''