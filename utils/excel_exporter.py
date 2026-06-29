"""
ساخت خروجی Excel از ویزیت‌ها - نسخه بهینه برای اندروید
"""

import os
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

from utils.file_manager import get_daily_logs, get_data_path

def safe_int(value, default=0):
    """تبدیل امن به عدد صحیح"""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_str(value, default=''):
    """تبدیل امن به رشته"""
    if value is None:
        return default
    return str(value)

def export_to_excel():
    """خروجی گرفتن از تمام ویزیت‌ها به فایل Excel"""
    
    data_path = get_data_path()
    logs = get_daily_logs()
    
    if not logs:
        return None
    
    wb = Workbook()
    
    # صفحه اول: گزارش اصلی
    ws1 = wb.active
    ws1.title = "گزارش ویزیت‌ها"
    
    # استایل‌ها
    header_font = Font(bold=True, size=11, color="FFFFFF")
    header_fill = PatternFill(start_color="2E86C1", end_color="2E86C1", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # هدرها
    headers = ["ردیف", "تاریخ ویزیت", "ساعت شروع", "ساعت اولین ویزیت", 
               "اولین مشتری", "تعداد ویزیت", "تعداد فاکتور", 
               "تعداد واحد", "مبلغ فروش", "ساعت آخرین ویزیت", "ساعت پایان"]
    
    for col, header in enumerate(headers, 1):
        cell = ws1.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border
    
    # پر کردن داده‌ها
    row = 2
    total_sales = 0
    total_invoices = 0
    total_visits = 0
    
    sorted_logs = sorted(logs.items(), key=lambda x: x[0], reverse=True)
    
    for idx, (date, log) in enumerate(sorted_logs, 1):
        ws1.cell(row=row, column=1, value=idx)
        ws1.cell(row=row, column=2, value=safe_str(date))
        ws1.cell(row=row, column=3, value=safe_str(log.get('clock_in', '')))
        ws1.cell(row=row, column=4, value=safe_str(log.get('first_visit_time', '')))
        ws1.cell(row=row, column=5, value=safe_str(log.get('first_customer', '')))
        
        visit_val = safe_int(log.get('visited_customers_count', 0))
        ws1.cell(row=row, column=6, value=visit_val)
        
        inv_val = safe_int(log.get('successful_invoices_count', 0))
        ws1.cell(row=row, column=7, value=inv_val)
        
        units_val = safe_int(log.get('successful_units_count', 0))
        ws1.cell(row=row, column=8, value=units_val)
        
        sales_num = safe_int(log.get('successful_sales_amount', 0))
        ws1.cell(row=row, column=9, value=sales_num)
        
        ws1.cell(row=row, column=10, value=safe_str(log.get('last_visit_time', '')))
        ws1.cell(row=row, column=11, value=safe_str(log.get('clock_out', '')))
        
        total_sales += sales_num
        total_invoices += inv_val
        total_visits += visit_val
        
        row += 1
    
    # تنظیم عرض ستون‌ها
    for col in range(1, len(headers) + 1):
        ws1.column_dimensions[get_column_letter(col)].width = 15
    
    # صفحه دوم: خلاصه آمار
    ws2 = wb.create_sheet("خلاصه آمار")
    
    summary_data = [
        ["شاخص", "مقدار"],
        ["کل فروش (تومان)", f"{total_sales:,}"],
        ["تعداد کل فاکتورها", total_invoices],
        ["تعداد کل ویزیت‌ها", total_visits],
        ["تعداد روزهای کاری", len(logs)],
        ["میانگین مبلغ هر فاکتور", f"{total_sales // total_invoices:,}" if total_invoices > 0 else "۰"],
        ["میانگین فروش هر ویزیت", f"{total_sales // total_visits:,}" if total_visits > 0 else "۰"],
    ]
    
    for r, row_data in enumerate(summary_data, 1):
        for c, value in enumerate(row_data, 1):
            cell = ws2.cell(row=r, column=c, value=value)
            if r == 1:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill(start_color="28B463", end_color="28B463", fill_type="solid")
            cell.alignment = Alignment(horizontal="center")
    
    ws2.column_dimensions['A'].width = 25
    ws2.column_dimensions['B'].width = 20
    
    # ذخیره فایل
    reports_dir = os.path.join(data_path, 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    from datetime import datetime
    filename = f"sales_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = os.path.join(reports_dir, filename)
    
    wb.save(filepath)
    return filepath