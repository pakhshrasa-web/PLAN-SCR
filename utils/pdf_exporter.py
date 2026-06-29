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

from utils.file_manager import get_daily_logs, get_data_path

# تلاش برای ایمپورت کتابخانه‌های RTL
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    RTL_AVAILABLE = True
except ImportError:
    RTL_AVAILABLE = False
    print("⚠️ کتابخانه‌های RTL (arabic-reshaper, python-bidi) نصب نیستند.")

def fix_text(text):
    """
    اصلاح متن فارسی برای نمایش درست در PDF
    """
    if not text:
        return ""
    if not isinstance(text, str):
        return str(text)
    
    if RTL_AVAILABLE:
        try:
            reshaped = arabic_reshaper.reshape(text)
            return get_display(reshaped)
        except:
            return text
    return text

def get_font_path():
    """
    پیدا کردن فایل فونت برای PDF
    """
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fonts', 'Vazirmatn-Regular.ttf'),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fonts', 'Vazirmatn.ttf'),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Vazirmatn-Regular.ttf'),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Vazirmatn.ttf'),
        '/system/fonts/Vazirmatn-Regular.ttf',
        '/system/fonts/Vazirmatn.ttf',
        '/system/fonts/Vazir.ttf',
        '/usr/share/fonts/truetype/vazirmatn/Vazirmatn-Regular.ttf',
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

# ثبت فونت فارسی در reportlab
FONT_PATH = get_font_path()
FONT_REGISTERED = False

if FONT_PATH:
    try:
        pdfmetrics.registerFont(TTFont('Vazirmatn', FONT_PATH))
        FONT_REGISTERED = True
        print(f"✅ فونت فارسی برای PDF از مسیر {FONT_PATH} ثبت شد")
    except Exception as e:
        print(f"⚠️ خطا در ثبت فونت PDF: {e}")
else:
    print("⚠️ فونت فارسی برای PDF یافت نشد، از فونت پیش‌فرض استفاده میشود")

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
    
    styles = getSampleStyleSheet()
    font_name = 'Vazirmatn' if FONT_REGISTERED else 'Helvetica'
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=18,
        alignment=1,
        spaceAfter=20,
        textColor=reportlab_colors.HexColor('#2E86C1')
    )
    
    story.append(Paragraph(fix_text("گزارش ویزیت‌های فروش"), title_style))
    story.append(Spacer(1, 5*mm))
    
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
    
    headers = ["تاریخ", "ساعت شروع", "ویزیت", "فاکتور", "واحد", "فروش (تومان)"]
    data = [[fix_text(h) for h in headers]]
    
    sorted_logs = sorted(logs.items(), key=lambda x: x[0], reverse=True)
    
    if max_records and len(sorted_logs) > max_records:
        sorted_logs = sorted_logs[:max_records]
    
    for date, log in sorted_logs:
        sales_num = safe_int(log.get('successful_sales_amount', 0))
        data.append([
            fix_text(date),
            fix_text(log.get('clock_in', '')),
            fix_text(str(safe_int(log.get('visited_customers_count', 0)))),
            fix_text(str(safe_int(log.get('successful_invoices_count', 0)))),
            fix_text(str(safe_int(log.get('successful_units_count', 0)))),
            fix_text(f"{sales_num:,}")
        ])
    
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