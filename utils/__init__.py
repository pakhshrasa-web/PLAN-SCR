"""
پکیج ابزارهای کمکی برای برنامه Plan Android
"""

# ایمپورت‌های اصلی برای دسترسی راحت
from .auth import hash_password, verify_password, get_admin_password, set_admin_password
from .storage import (
    get_data_path, init_data_path, load_json, save_json, get_reports_path,
    get_agents, add_agent, update_agent, delete_agent,
    get_routes, add_route, update_route, delete_route,
    get_customers, add_customer, update_customer, delete_customer, get_customers_by_route,
    get_settings, update_settings,
    get_daily_logs, get_daily_log, save_daily_log, delete_daily_log, get_all_logs_sorted
)
from .jalali_date import (
    get_today_jalali, get_current_time, convert_to_jalali, convert_to_gregorian,
    validate_jalali_date, get_jalali_month_days, get_weekday_jalali,
    get_jalali_months, format_jalali_date
)
from .text_helper import f, fix_text, is_persian_text, fix_english_numbers, fix_persian_numbers, _
from .rtl import RTLTextInput, RTLSpinner, RTLLabel, is_rtl_text, auto_align_textinput
from .user_manager import (
    generate_code, get_users, save_users, get_codes, save_codes,
    create_code, verify_code, register_user, login,
    delete_user_by_id, delete_user, get_user_by_username
)
from .excel_exporter import export_to_excel
from .excel_importer import import_routes_from_excel, import_customers_from_excel, import_from_excel
from .pdf_exporter import export_to_pdf, export_pdf_with_limit
from .file_picker import FilePicker

__version__ = '1.0.0'
__author__ = 'Plan Android Team'

__all__ = [
    'hash_password', 'verify_password', 'get_admin_password', 'set_admin_password',
    'get_data_path', 'init_data_path', 'load_json', 'save_json', 'get_reports_path',
    'get_agents', 'add_agent', 'update_agent', 'delete_agent',
    'get_routes', 'add_route', 'update_route', 'delete_route',
    'get_customers', 'add_customer', 'update_customer', 'delete_customer', 'get_customers_by_route',
    'get_settings', 'update_settings',
    'get_daily_logs', 'get_daily_log', 'save_daily_log', 'delete_daily_log', 'get_all_logs_sorted',
    'get_today_jalali', 'get_current_time', 'convert_to_jalali', 'convert_to_gregorian',
    'validate_jalali_date', 'get_jalali_month_days', 'get_weekday_jalali',
    'get_jalali_months', 'format_jalali_date',
    'f', 'fix_text', 'is_persian_text', 'fix_english_numbers', 'fix_persian_numbers', '_',
    'RTLTextInput', 'RTLSpinner', 'RTLLabel', 'is_rtl_text', 'auto_align_textinput',
    'generate_code', 'get_users', 'save_users', 'get_codes', 'save_codes',
    'create_code', 'verify_code', 'register_user', 'login',
    'delete_user_by_id', 'delete_user', 'get_user_by_username',
    'export_to_excel',
    'import_routes_from_excel', 'import_customers_from_excel', 'import_from_excel',
    'export_to_pdf', 'export_pdf_with_limit',
    'FilePicker',
]