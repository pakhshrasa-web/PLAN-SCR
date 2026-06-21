"""
ساخت خروجی PDF از ویزیت‌ها با پشتیبانی از فونت فارسی و RTL
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors as reportlab_colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from utils.storage import get_daily_logs, get_data_path
from utils.text_helper import fix_text  # استفاده از text_helper

# ========== مدیریت فونت ==========
_FONT_REGISTERED = False
_FONT_PATH = None

def get_font_path():
    """
    پیدا کردن فایل فونت برای PDF
    """
    global _FONT_PATH
    
    if _FONT_PATH:
        return _FONT_PATH
    
    # مسیرهای احتمالی
    base_dir = os.path.dirname(os.path.dirname(__file__))
    
    possible_paths = [
        os.path.join(base_dir, 'fonts', 'Vazirmatn-Regular.ttf'),
        os.path.join(base_dir, 'fonts', 'Vazirmatn.ttf'),
        os.path.join(base_dir, 'Vazirmatn-Regular.ttf'),
        os.path.join(base_dir, 'Vazirmatn.ttf'),
        '/system/fonts/Vazirmatn-Regular.ttf',
        '/system/fonts/Vazirmatn.ttf',
        '/system/fonts/Vazir.ttf',
        '/usr/share/fonts/truetype/vazirmatn/Vazirmatn-Regular.ttf',
        '/usr/local/share/fonts/vazirmatn/Vazirmatn-Regular.ttf',
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            _FONT_PATH = path
            return path
    
    return None

def register_pdf_font():
    """
    ثبت فونت برای PDF
    """
    global _FONT_REGISTERED
    
    if _FONT_REGISTERED:
        return True
    
    font_path = get_font_path()
    
    if font_path:
        try:
            pdfmetrics.registerFont(TTFont('Vazirmatn', font_path))
            _FONT_REGISTERED = True
            print(f"✅ فونت PDF از مسیر {font_path} ثبت شد")
            return True
        except Exception as e:
            print(f"⚠️ خطا در ثبت فونت PDF: {e}")
            return False
    else:
        print("⚠️ فونت فارسی برای PDF یافت نشد، از فونت پیش‌فرض استفاده میشود")
        return False

# ثبت خودکار فونت
register_pdf_font()

# ========== توابع اصلی ==========
def safe_int(value, default=0):
    """تبدیل امن به عدد صحیح"""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def export_to_pdf(max_records=None):
    """
    خروجی گرفتن از تمام ویزیت‌ها به فایل PDF
    
    Args:
        max_records: حداکثر تعداد رکورد (None = همه رکوردها)
    """
    data_path = get_data_path()
    logs = get_daily_logs()
    
    if not logs:
        return None
    
    reports_dir = os.path.join(data_path, 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    from datetime import datetime
    filename = f"sales_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(reports_dir, filename)
    
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=20*mm,
        bottomMargin=15*mm
    )
    story = []
    
    # تعریف استایل‌ها
    styles = getSampleStyleSheet()
    
    # نام فونت (با fallback)
    font_name = 'Vazirmatn' if _FONT_REGISTERED else 'Helvetica'
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=18,
        alignment=1,  # center
        spaceAfter=20,
        textColor=reportlab_colors.HexColor('#2E86C1')
    )
    
    # عنوان
    story.append(Paragraph(fix_text("گزارش ویزیت‌های فروش"), title_style))
    story.append(Spacer(1, 5*mm))
    
    # محاسبه آمار
    total_sales = 0
    total_invoices = 0
    total_visits = 0
    total_units = 0
    
    for log in logs.values():
        try:
            total_sales += safe_int(log.get('successful_sales_amount', 0))
            total_invoices += safe_int(log.get('successful_invoices_count', 0))
            total_visits += safe_int(log.get('visited_customers_count', 0))
            total_units += safe_int(log.get('successful_units_count', 0))
        except:
            pass
    
    # جدول خلاصه آمار
    summary_data = [
        [fix_text('کل فروش'), fix_text(f"{total_sales:,} تومان")],
        [fix_text('تعداد فاکتورها'), fix_text(str(total_invoices))],
        [fix_text('تعداد ویزیت‌ها'), fix_text(str(total_visits))],
        [fix_text('تعداد واحدهای فروش'), fix_text(str(total_units))],
        [fix_text('تعداد روزهای کاری'), fix_text(str(len(logs)))],
    ]
    
    summary_table = Table(summary_data, colWidths=[60*mm, 60*mm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), reportlab_colors.HexColor('#28B463')),
        ('TEXTCOLOR', (0, 0), (-1, 0), reportlab_colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), font_name),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('GRID', (0, 0), (-1, -1), 1, reportlab_colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), reportlab_colors.beige),
        ('FONTNAME', (0, 1), (-1, -1), font_name),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 10*mm))
    
    # جدول ویزیت‌ها
    headers = ["تاریخ", "ساعت شروع", "ویزیت", "فاکتور", "واحد", "فروش (تومان)"]
    data = [[fix_text(h) for h in headers]]
    
    sorted_logs = sorted(logs.items(), key=lambda x: x[0], reverse=True)
    
    # محدود کردن تعداد رکوردها
    if max_records and len(sorted_logs) > max_records:
        sorted_logs = sorted_logs[:max_records]
    
    for date, log in sorted_logs:
        sales = safe_int(log.get('successful_sales_amount', 0))
        data.append([
            fix_text(date),
            fix_text(log.get('clock_in', '')),
            fix_text(str(safe_int(log.get('visited_customers_count', 0)))),
            fix_text(str(safe_int(log.get('successful_invoices_count', 0)))),
            fix_text(str(safe_int(log.get('successful_units_count', 0)))),
            fix_text(f"{sales:,}")
        ])
    
    # تنظیم عرض ستون‌ها
    col_widths = [28*mm, 25*mm, 18*mm, 18*mm, 18*mm, 33*mm]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), reportlab_colors.HexColor('#2E86C1')),
        ('TEXTCOLOR', (0, 0), (-1, 0), reportlab_colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), font_name),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('GRID', (0, 0), (-1, -1), 1, reportlab_colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), font_name),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(table)
    
    # ساخت PDF
    try:
        doc.build(story)
        return filepath
    except Exception as e:
        print(f"❌ خطا در ساخت PDF: {e}")
        return None

def export_pdf_with_limit(max_records=50):
    """
    خروجی PDF با محدودیت تعداد رکورد
    
    Args:
        max_records: حداکثر تعداد رکورد
    """
    return export_to_pdf(max_records=max_records)