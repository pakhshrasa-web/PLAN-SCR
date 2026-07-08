"""
مدیریت تارگت‌ها (هدف‌های فروش)
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
from constants import TARGET_TYPES, TARGET_STATUSES

TARGETS_FILE = 'targets.json'


def _get_targets_path() -> str:
    """دریافت مسیر فایل تارگت‌ها"""
    return os.path.join(get_data_path(), TARGETS_FILE)


def _load_targets() -> List[Dict]:
    """بارگذاری همه تارگت‌ها"""
    try:
        path = _get_targets_path()
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"خطا در بارگذاری تارگت‌ها: {e}")
        return []


def _save_targets(targets: List[Dict]) -> bool:
    """ذخیره تارگت‌ها"""
    try:
        path = _get_targets_path()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(targets, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"خطا در ذخیره تارگت‌ها: {e}")
        return False


def _generate_target_id() -> str:
    """تولید آیدی یکتا برای تارگت"""
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(random.choices(chars, k=4))
    return f"TG{random_part}"


def _calculate_end_date(start_date: str, duration: int) -> str:
    """
    محاسبه تاریخ پایان از تاریخ شروع و مدت
    start_date: فرمت سال/ماه/روز (مثال: 1405/01/31)
    """
    try:
        # تبدیل تاریخ شمسی به میلادی
        gregorian_date = convert_to_gregorian(start_date)
        if not gregorian_date or gregorian_date == start_date:
            logger.error(f"خطا در تبدیل تاریخ: {start_date}")
            return start_date
        
        # تبدیل به datetime
        date_obj = datetime.strptime(gregorian_date, '%Y-%m-%d')
        
        # اضافه کردن مدت به روز
        end_date_obj = date_obj + timedelta(days=duration)
        
        # تبدیل به شمسی
        end_date_str = to_jalali(
            end_date_obj.year,
            end_date_obj.month,
            end_date_obj.day
        )
        
        return end_date_str
        
    except Exception as e:
        logger.error(f"خطا در محاسبه تاریخ پایان: {e}")
        return start_date


def create_target(
    agent_name: str,
    target_type: str,
    target_value: int,
    period_type: str,
    duration: int,
    start_date: str,
    description: str = '',
    created_by: str = 'supervisor'
) -> Tuple[bool, str, Optional[Dict]]:
    """
    ایجاد تارگت جدید
    
    Args:
        agent_name: نام عامل
        target_type: نوع تارگت
        target_value: میزان هدف
        period_type: نوع دوره (daily, weekly, monthly, quarterly, yearly)
        duration: مدت به روز
        start_date: تاریخ شروع
        description: توضیحات
        created_by: ایجادکننده
    
    Returns:
        Tuple[bool, str, Optional[Dict]]: (موفقیت, پیام, دیتای تارگت)
    """
    try:
        # اعتبارسنجی
        if not agent_name:
            return False, 'نام عامل الزامی است', None

        if not target_type:
            return False, 'نوع تارگت الزامی است', None

        if target_value <= 0:
            return False, 'میزان هدف باید بزرگتر از صفر باشد', None

        if not period_type:
            return False, 'نوع دوره الزامی است', None

        if duration <= 0:
            return False, 'مدت تارگت باید بزرگتر از صفر باشد', None

        if not start_date:
            return False, 'تاریخ شروع الزامی است', None

        # اعتبارسنجی تاریخ
        if not validate_jalali_date(start_date):
            return False, 'فرمت تاریخ نامعتبر است (مثال: 1405/01/31)', None

        # محاسبه تاریخ پایان
        end_date = _calculate_end_date(start_date, duration)

        # تولید آیدی
        target_id = _generate_target_id()

        # ایجاد تارگت
        target = {
            'target_id': target_id,
            'agent_name': agent_name,
            'target_type': target_type,
            'target_value': target_value,
            'period_type': period_type,
            'duration': duration,
            'description': description,
            'start_date': start_date,
            'end_date': end_date,
            'status': 'در انتظار',
            'is_active': True,
            'is_locked': False,
            'achieved_value': 0,
            'created_at': datetime.now().isoformat(),
            'created_by': created_by,
            'finalized_at': ''
        }

        # بارگذاری تارگت‌های موجود
        targets = _load_targets()
        targets.append(target)

        # ذخیره
        if _save_targets(targets):
            logger.info(f"تارگت جدید ایجاد شد: {target_id}")
            return True, f'تارگت با شناسه {target_id} ثبت شد', target
        else:
            return False, 'خطا در ذخیره تارگت', None

    except Exception as e:
        logger.error(f"خطا در ایجاد تارگت: {e}")
        return False, f'خطا: {str(e)}', None


def get_all_targets() -> List[Dict]:
    """دریافت همه تارگت‌ها"""
    return _load_targets()


def get_targets_by_agent(agent_name: str) -> List[Dict]:
    """دریافت تارگت‌های یک عامل"""
    targets = _load_targets()
    return [t for t in targets if t.get('agent_name') == agent_name]


def get_targets_by_status(status: str) -> List[Dict]:
    """دریافت تارگت‌ها بر اساس وضعیت"""
    targets = _load_targets()
    return [t for t in targets if t.get('status') == status]


def get_targets_by_type(target_type: str) -> List[Dict]:
    """دریافت تارگت‌ها بر اساس نوع"""
    targets = _load_targets()
    return [t for t in targets if t.get('target_type') == target_type]


def get_targets_filtered(
    agent_name: str = None,
    target_type: str = None,
    status: str = None,
    period_type: str = None
) -> List[Dict]:
    """دریافت تارگت‌ها با فیلترهای دلخواه"""
    targets = _load_targets()
    result = targets

    if agent_name:
        result = [t for t in result if t.get('agent_name') == agent_name]

    if target_type:
        result = [t for t in result if t.get('target_type') == target_type]

    if status:
        result = [t for t in result if t.get('status') == status]

    if period_type:
        result = [t for t in result if t.get('period_type') == period_type]

    # مرتب‌سازی بر اساس تاریخ ایجاد (جدیدترین اول)
    result.sort(key=lambda x: x.get('created_at', ''), reverse=True)

    return result


# ============================================================
# توابع برای تب تحقق تارگت
# ============================================================

def get_active_targets_by_agent(agent_name: str, start_date: str = None, end_date: str = None) -> List[Dict]:
    """
    دریافت تارگت‌های فعال یا در انتظار یک عامل در بازه زمانی مشخص
    
    Args:
        agent_name: نام عامل
        start_date: تاریخ شروع بازه (اختیاری)
        end_date: تاریخ پایان بازه (اختیاری)
    
    Returns:
        List[Dict]: لیست تارگت‌های قابل تحقق
    """
    try:
        if not agent_name:
            logger.warning("نام عامل خالی است")
            return []
        
        targets = _load_targets()
        result = []
        
        logger.info(f"جستجوی تارگت‌ها برای عامل: {agent_name}")
        logger.info(f"تعداد کل تارگت‌ها: {len(targets)}")
        
        for target in targets:
            # فیلتر بر اساس عامل
            target_agent = target.get('agent_name', '')
            if target_agent != agent_name:
                continue
            
            # فقط تارگت‌های با وضعیت 'فعال' یا 'در انتظار' (قابل تحقق)
            status = target.get('status', '')
            if status not in ['فعال', 'در انتظار']:
                continue
            
            # فیلتر بر اساس بازه زمانی (تاریخ شروع تارگت)
            target_start = target.get('start_date', '')
            if start_date and target_start < start_date:
                continue
            if end_date and target_start > end_date:
                continue
            
            result.append(target)
            logger.info(f"تارگت پیدا شد: {target.get('target_id')} - {target.get('status')}")
        
        # مرتب‌سازی بر اساس تاریخ شروع
        result.sort(key=lambda x: x.get('start_date', ''))
        
        logger.info(f"تعداد تارگت‌های یافت شده: {len(result)}")
        return result
        
    except Exception as e:
        logger.error(f"خطا در دریافت تارگت‌ها: {e}")
        import traceback
        traceback.print_exc()
        return []


def finalize_targets(target_ids: List[str], achieved_values: Dict[str, int]) -> Tuple[bool, str]:
    """
    نهایی‌سازی تارگت‌های انتخاب شده
    
    Args:
        target_ids: لیست شناسه‌های تارگت
        achieved_values: دیکشنری {target_id: achieved_value}
    
    Returns:
        Tuple[bool, str]: (موفقیت, پیام)
    """
    try:
        targets = _load_targets()
        updated = 0
        
        for i, target in enumerate(targets):
            target_id = target.get('target_id')
            if target_id in target_ids:
                # بررسی اینکه تارگت قابل نهایی‌سازی باشد (فعال یا در انتظار)
                status = target.get('status', '')
                if status not in ['فعال', 'در انتظار']:
                    continue
                
                # به‌روزرسانی مقدار محقق شده
                achieved = achieved_values.get(target_id, 0)
                targets[i]['achieved_value'] = achieved
                targets[i]['status'] = 'تکمیل شده'
                targets[i]['finalized_at'] = datetime.now().isoformat()
                updated += 1
        
        if updated == 0:
            return False, 'هیچ تارگت قابل نهایی‌سازی یافت نشد'
        
        if _save_targets(targets):
            logger.info(f"{updated} تارگت نهایی‌سازی شد")
            return True, f'{updated} تارگت با موفقیت نهایی‌سازی شد'
        else:
            return False, 'خطا در ذخیره تارگت‌ها'
        
    except Exception as e:
        logger.error(f"خطا در نهایی‌سازی تارگت‌ها: {e}")
        return False, f'خطا: {str(e)}'


def read_excel_summary(filepath: str) -> Dict[str, int]:
    """
    خواندن داده‌های خلاصه از فایل اکسل
    
    Args:
        filepath: مسیر فایل اکسل
    
    Returns:
        Dict[str, int]: دیکشنری شامل مقادیر خلاصه
    """
    try:
        import openpyxl
        
        wb = openpyxl.load_workbook(filepath, data_only=True)
        
        # بررسی وجود شیت خلاصه آمار
        if 'خلاصه آمار' not in wb.sheetnames:
            logger.warning(f"شیت 'خلاصه آمار' در فایل {filepath} یافت نشد")
            return {}
        
        ws = wb['خلاصه آمار']
        
        # خواندن داده‌ها از شیت خلاصه آمار
        summary_data = {}
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=True):
            if row and len(row) >= 2:
                key = str(row[0]).strip()
                value = row[1]
                if value is not None:
                    try:
                        # حذف کاما و تبدیل به عدد
                        if isinstance(value, str):
                            value = value.replace(',', '').replace(' ', '')
                        summary_data[key] = int(value)
                    except (ValueError, TypeError):
                        summary_data[key] = 0
        
        wb.close()
        logger.info(f"داده‌های خلاصه خوانده شد: {len(summary_data)} آیتم")
        return summary_data
        
    except Exception as e:
        logger.error(f"خطا در خواندن فایل اکسل: {e}")
        import traceback
        traceback.print_exc()
        return {}


def can_edit_target(target: Dict) -> bool:
    """
    بررسی اینکه آیا تارگت قابل ویرایش است یا نه
    
    شرایط:
    - اگر وضعیت 'تکمیل شده' باشد، تا ۵ روز بعد از نهایی‌سازی قابل ویرایش است
    - وضعیت‌های دیگر ('در انتظار' و 'فعال') همیشه قابل ویرایش هستند
    """
    try:
        # بررسی وضعیت
        status = target.get('status', '')
        
        # تارگت‌های غیرتکمیل شده همیشه قابل ویرایش هستند
        if status != 'تکمیل شده':
            return True

        # تارگت‌های تکمیل شده: فقط تا ۵ روز بعد از نهایی‌سازی قابل ویرایش هستند
        finalized_at = target.get('finalized_at', '')
        if not finalized_at:
            return True

        finalized_date = datetime.fromisoformat(finalized_at)
        now = datetime.now()
        days_diff = (now - finalized_date).days

        # فقط تا ۵ روز بعد از نهایی‌سازی قابل ویرایش است
        return days_diff <= 5

    except Exception as e:
        logger.error(f"خطا در بررسی ویرایش تارگت: {e}")
        return False


def update_target(target_id: str, updates: Dict) -> Tuple[bool, str]:
    """
    به‌روزرسانی تارگت
    
    Args:
        target_id: شناسه تارگت
        updates: دیکشنری شامل فیلدهای قابل تغییر
    
    Returns:
        Tuple[bool, str]: (موفقیت, پیام)
    """
    try:
        targets = _load_targets()

        for i, target in enumerate(targets):
            if target.get('target_id') == target_id:
                # بررسی قابلیت ویرایش
                if not can_edit_target(target):
                    return False, 'این تارگت قابل ویرایش نیست (زمان ویرایش گذشته یا تکمیل شده)'

                # اعمال تغییرات
                allowed_fields = [
                    'target_type', 'target_value', 'duration',
                    'start_date', 'description', 'is_active', 'status'
                ]

                for field, value in updates.items():
                    if field in allowed_fields:
                        # اگر تاریخ شروع تغییر کرد، تاریخ پایان هم محاسبه بشه
                        if field == 'start_date':
                            if validate_jalali_date(value):
                                duration_val = updates.get('duration', target.get('duration', 0))
                                target['end_date'] = _calculate_end_date(value, duration_val)
                            else:
                                return False, 'تاریخ شروع نامعتبر است'

                        target[field] = value

                # اگر مدت تغییر کرد، تاریخ پایان مجدداً محاسبه بشه
                if 'duration' in updates and 'start_date' in target:
                    target['end_date'] = _calculate_end_date(
                        target['start_date'],
                        updates['duration']
                    )

                # ذخیره
                if _save_targets(targets):
                    logger.info(f"تارگت {target_id} به‌روزرسانی شد")
                    return True, 'تارگت با موفقیت به‌روزرسانی شد'
                else:
                    return False, 'خطا در ذخیره تارگت'

        return False, 'تارگت یافت نشد'

    except Exception as e:
        logger.error(f"خطا در به‌روزرسانی تارگت: {e}")
        return False, f'خطا: {str(e)}'


def delete_target(target_id: str) -> Tuple[bool, str]:
    """
    حذف تارگت (فقط در صورت عدم قفل بودن و قابل ویرایش بودن)
    """
    try:
        targets = _load_targets()

        for i, target in enumerate(targets):
            if target.get('target_id') == target_id:
                if not can_edit_target(target):
                    return False, 'این تارگت قابل حذف نیست (زمان ویرایش گذشته یا تکمیل شده)'

                targets.pop(i)

                if _save_targets(targets):
                    logger.info(f"تارگت {target_id} حذف شد")
                    return True, 'تارگت با موفقیت حذف شد'
                else:
                    return False, 'خطا در ذخیره تارگت'

        return False, 'تارگت یافت نشد'

    except Exception as e:
        logger.error(f"خطا در حذف تارگت: {e}")
        return False, f'خطا: {str(e)}'


def get_target_statistics() -> Dict:
    """
    دریافت آمار کلی تارگت‌ها
    """
    try:
        targets = _load_targets()

        total = len(targets)
        pending = len([t for t in targets if t.get('status') == 'در انتظار'])
        active = len([t for t in targets if t.get('status') == 'فعال'])
        completed = len([t for t in targets if t.get('status') == 'تکمیل شده'])
        cancelled = len([t for t in targets if t.get('status') == 'لغو شده'])

        return {
            'total': total,
            'pending': pending,
            'active': active,
            'completed': completed,
            'cancelled': cancelled
        }

    except Exception as e:
        logger.error(f"خطا در دریافت آمار تارگت‌ها: {e}")
        return {
            'total': 0,
            'pending': 0,
            'active': 0,
            'completed': 0,
            'cancelled': 0
        }


def export_targets_to_excel(targets: List[Dict], filename: str = None) -> Tuple[bool, str, str]:
    """
    خروجی گرفتن از تارگت‌ها به صورت فایل Excel
    """
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        from openpyxl.utils import get_column_letter
        from utils.storage import get_backup_path
        from utils.jalali_date import get_today_jalali
        
        if not targets:
            return False, 'هیچ تارگتی برای خروجی وجود ندارد', ''
        
        wb = openpyxl.Workbook()
        ws1 = wb.active
        ws1.title = "تارگت‌ها"
        
        header_font = Font(bold=True, size=11, color="FFFFFF")
        header_fill = PatternFill(start_color="2E86C1", end_color="2E86C1", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        headers = ['شناسه', 'عامل', 'نوع تارگت', 'میزان هدف', 'دوره', 'مدت (روز)',
                   'تاریخ شروع', 'تاریخ پایان', 'وضعیت', 'مقدار محقق شده', 'توضیحات']
        
        for col, header in enumerate(headers, 1):
            cell = ws1.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border
        
        period_display_map = {
            'daily': 'روزانه',
            'weekly': 'هفتگی',
            'monthly': 'ماهانه',
            'quarterly': 'فصلی',
            'yearly': 'سالانه'
        }
        
        for row, target in enumerate(targets, 2):
            period_type = target.get('period_type', '')
            period_display = period_display_map.get(period_type, period_type)
            
            ws1.cell(row=row, column=1, value=target.get('target_id', ''))
            ws1.cell(row=row, column=2, value=target.get('agent_name', ''))
            ws1.cell(row=row, column=3, value=target.get('target_type', ''))
            ws1.cell(row=row, column=4, value=target.get('target_value', 0))
            ws1.cell(row=row, column=5, value=period_display)
            ws1.cell(row=row, column=6, value=target.get('duration', 0))
            ws1.cell(row=row, column=7, value=target.get('start_date', ''))
            ws1.cell(row=row, column=8, value=target.get('end_date', ''))
            ws1.cell(row=row, column=9, value=target.get('status', ''))
            ws1.cell(row=row, column=10, value=target.get('achieved_value', 0))
            ws1.cell(row=row, column=11, value=target.get('description', ''))
        
        column_widths = [12, 18, 14, 16, 12, 12, 14, 14, 14, 18, 30]
        for i, width in enumerate(column_widths, 1):
            ws1.column_dimensions[get_column_letter(i)].width = width
        
        for row in ws1.iter_rows(min_row=2, max_row=len(targets) + 1):
            for cell in row:
                cell.alignment = Alignment(horizontal='center', vertical='center')
                cell.border = thin_border
        
        if not filename:
            today = get_today_jalali().replace('/', '-')
            timestamp = datetime.now().strftime('%H%M%S')
            filename = f'گزارش_تارگت_{today}_{timestamp}.xlsx'
        
        export_dir = get_backup_path()
        os.makedirs(export_dir, exist_ok=True)
        filepath = os.path.join(export_dir, filename)
        
        wb.save(filepath)
        
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"فایل اکسل تارگت‌ها ذخیره شد: {filepath} ({size} bytes)")
            return True, f'فایل با موفقیت ذخیره شد:\n{filename}', filepath
        else:
            return False, 'فایل ساخته نشد', ''
        
    except ImportError:
        return False, 'ماژول openpyxl نصب نیست.\nلطفاً با دستور زیر نصب کنید:\npip install openpyxl', ''
    except Exception as e:
        print(f"خطا در خروجی اکسل تارگت‌ها: {e}")
        import traceback
        traceback.print_exc()
        return False, f'خطا در ایجاد فایل اکسل:\n{str(e)}', ''


# ============================================================
# تابع تست
# ============================================================

def test_target_manager():
    """تست توابع مدیریت تارگت"""
    print("\n" + "=" * 50)
    print("تست مدیریت تارگت‌ها")
    print("=" * 50)

    # ایجاد تارگت تست با period_type
    success, msg, target = create_target(
        agent_name='حیدری ناصر',
        target_type='ریالی',
        target_value=30000000000,
        period_type='monthly',  # ← پارامتر اضافه شد
        duration=30,
        start_date='1405/01/31',
        description='کف تارگت فروش ریالی',
        created_by='supervisor'
    )

    if success:
        print(f"موفق: {msg}")
        print(f"تارگت: {target['target_id']}")
        print(f"   تاریخ پایان: {target['end_date']}")
        print(f"   نوع دوره: {target['period_type']}")
    else:
        print(f"خطا: {msg}")

    # آمار
    stats = get_target_statistics()
    print(f"\nآمار تارگت‌ها:")
    print(f"   کل: {stats['total']}")
    print(f"   در انتظار: {stats['pending']}")
    print(f"   فعال: {stats['active']}")
    print(f"   تکمیل شده: {stats['completed']}")
    print(f"   لغو شده: {stats['cancelled']}")

    print("=" * 50)


if __name__ == '__main__':
    test_target_manager()