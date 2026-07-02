"""
وارد کردن اطلاعات از فایل Excel - نسخه بهینه برای اندروید
"""

import os
import openpyxl
from kivy.clock import Clock
from utils.file_manager import add_route, add_customer, get_routes, get_customers
from utils.storage import ensure_public_dirs, get_import_path


def import_routes_from_excel(filepath):
    """
    وارد کردن مسیرها از فایل Excel
    فرمت فایل: ستون اول = name
    """
    print(f"🔍 import_routes_from_excel: filepath={filepath}")
    
    if not filepath:
        return False, "مسیر فایل نامعتبر است"
    
    if not os.path.exists(filepath):
        return False, f"فایل وجود ندارد: {filepath}"
    
    try:
        # ✅ لاگ حجم فایل
        file_size = os.path.getsize(filepath)
        print(f"📏 حجم فایل: {file_size} bytes")
        
        if file_size == 0:
            return False, "فایل خالی است"
        
        # ✅ بارگذاری فایل
        print("📂 در حال بارگذاری فایل اکسل...")
        wb = openpyxl.load_workbook(filepath, data_only=True)
        ws = wb.active
        print(f"✅ فایل بارگذاری شد، {ws.max_row} سطر")
        
        imported_count = 0
        duplicate_count = 0
        error_count = 0
        
        # ✅ دریافت مسیرهای موجود
        existing_routes = [r.get('name', '') for r in get_routes()]
        print(f"📋 {len(existing_routes)} مسیر موجود در سیستم")
        
        # ✅ خواندن سطرها
        for idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            try:
                if not row or not row[0]:
                    error_count += 1
                    continue
                    
                name = str(row[0]).strip()
                if not name:
                    error_count += 1
                    continue
                
                print(f"📝 سطر {idx}: نام مسیر = '{name}'")
                
                if name not in existing_routes:
                    add_route({'name': name})
                    imported_count += 1
                    existing_routes.append(name)
                    print(f"✅ مسیر '{name}' اضافه شد")
                else:
                    duplicate_count += 1
                    print(f"⚠️ مسیر '{name}' تکراری است")
                    
            except Exception as e:
                error_count += 1
                print(f"❌ خطا در سطر {idx}: {e}")
        
        wb.close()
        print(f"📊 نتیجه: {imported_count} جدید، {duplicate_count} تکراری، {error_count} خطا")
        
        msg = f"{imported_count} مسیر جدید وارد شد."
        if duplicate_count > 0:
            msg += f" {duplicate_count} مسیر تکراری نادیده گرفته شد."
        if error_count > 0:
            msg += f" {error_count} سطر خطا داشت."
        
        return True, msg
    
    except Exception as e:
        print(f"❌ خطا در import_routes_from_excel: {e}")
        import traceback
        traceback.print_exc()
        return False, f"خطا در خواندن فایل: {str(e)}"


def import_customers_from_excel(filepath):
    """
    وارد کردن مشتریان از فایل Excel
    فرمت فایل: name, store_name, route_name, mobile, address
    """
    print(f"🔍 import_customers_from_excel: filepath={filepath}")
    
    if not filepath:
        return False, "مسیر فایل نامعتبر است"
    
    if not os.path.exists(filepath):
        return False, f"فایل وجود ندارد: {filepath}"
    
    try:
        # ✅ لاگ حجم فایل
        file_size = os.path.getsize(filepath)
        print(f"📏 حجم فایل: {file_size} bytes")
        
        if file_size == 0:
            return False, "فایل خالی است"
        
        # ✅ بارگذاری فایل
        print("📂 در حال بارگذاری فایل اکسل...")
        wb = openpyxl.load_workbook(filepath, data_only=True)
        ws = wb.active
        print(f"✅ فایل بارگذاری شد، {ws.max_row} سطر")
        
        imported_count = 0
        duplicate_count = 0
        error_count = 0
        
        # ✅ دریافت مسیرهای موجود
        routes = get_routes()
        route_names = [r.get('name', '') for r in routes]
        print(f"📋 {len(route_names)} مسیر موجود در سیستم")
        
        # ✅ خواندن سطرها
        for idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            try:
                if not row:
                    error_count += 1
                    continue
                
                # خواندن مقادیر با مدیریت None
                name = str(row[0]).strip() if row[0] else ''
                store_name = str(row[1]).strip() if len(row) > 1 and row[1] else ''
                route_name = str(row[2]).strip() if len(row) > 2 and row[2] else ''
                mobile = str(row[3]).strip() if len(row) > 3 and row[3] else ''
                address = str(row[4]).strip() if len(row) > 4 and row[4] else ''
                
                if not name:
                    error_count += 1
                    print(f"⚠️ سطر {idx}: نام مشتری خالی است")
                    continue
                
                print(f"📝 سطر {idx}: نام='{name}', مسیر='{route_name}', موبایل='{mobile}'")
                
                # بررسی تکراری نبودن
                existing = get_customers()
                is_duplicate = any(c.get('name') == name for c in existing)
                
                if not is_duplicate:
                    # بررسی وجود مسیر
                    if route_name and route_name not in route_names:
                        route_names.append(route_name)
                        add_route({'name': route_name})
                        print(f"✅ مسیر جدید '{route_name}' اضافه شد")
                    
                    customer = {
                        'name': name,
                        'store_name': store_name,
                        'route_name': route_name,
                        'mobile': mobile,
                        'address': address
                    }
                    add_customer(customer)
                    imported_count += 1
                    print(f"✅ مشتری '{name}' اضافه شد")
                else:
                    duplicate_count += 1
                    print(f"⚠️ مشتری '{name}' تکراری است")
                    
            except Exception as e:
                error_count += 1
                print(f"❌ خطا در سطر {idx}: {e}")
        
        wb.close()
        print(f"📊 نتیجه: {imported_count} جدید، {duplicate_count} تکراری، {error_count} خطا")
        
        msg = f"{imported_count} مشتری جدید وارد شد."
        if duplicate_count > 0:
            msg += f" {duplicate_count} مشتری تکراری نادیده گرفته شد."
        if error_count > 0:
            msg += f" {error_count} سطر خطا داشت."
        
        return True, msg
    
    except Exception as e:
        print(f"❌ خطا در import_customers_from_excel: {e}")
        import traceback
        traceback.print_exc()
        return False, f"خطا در خواندن فایل: {str(e)}"


def get_excel_template_routes():
    """ایجاد فایل نمونه برای مسیرها"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Routes"
    ws['A1'] = "name"
    ws['A2'] = "نمونه: مسیر شمال"
    ws['A3'] = "نمونه: مسیر جنوب"
    ws['A4'] = "نمونه: مسیر شرق"
    return wb


def get_excel_template_customers():
    """ایجاد فایل نمونه برای مشتریان"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Customers"
    ws['A1'] = "name"
    ws['B1'] = "store_name"
    ws['C1'] = "route_name"
    ws['D1'] = "mobile"
    ws['E1'] = "address"
    
    ws['A2'] = "علی محمدی"
    ws['B2'] = "فروشگاه رضا"
    ws['C2'] = "مسیر شمال"
    ws['D2'] = "09121234567"
    ws['E2'] = "خیابان ولیعصر"
    
    ws['A3'] = "محمد کریمی"
    ws['B3'] = "فروشگاه سینا"
    ws['C3'] = "مسیر جنوب"
    ws['D3'] = "09129876543"
    ws['E3'] = "خیابان انقلاب"
    
    return wb


def save_excel_template(data_type='customers'):
    """
    ذخیره فایل نمونه در پوشه import
    data_type: 'customers' یا 'routes'
    """
    try:
        # ✅ اطمینان از وجود پوشه
        ensure_public_dirs()
        import_path = get_import_path()
        
        if data_type == 'routes':
            wb = get_excel_template_routes()
            filename = 'template_routes.xlsx'
        else:
            wb = get_excel_template_customers()
            filename = 'template_customers.xlsx'
        
        filepath = os.path.join(import_path, filename)
        wb.save(filepath)
        
        print(f"✅ فایل نمونه ذخیره شد: {filepath}")
        return True, filepath
        
    except Exception as e:
        print(f"❌ خطا در ذخیره فایل نمونه: {e}")
        return False, str(e)


def import_from_excel(filepath, data_type='customers'):
    """
    تابع عمومی برای وارد کردن از اکسل
    data_type: 'customers' یا 'routes'
    """
    print(f"🔍 import_from_excel: filepath={filepath}, data_type={data_type}")
    
    if data_type == 'routes':
        return import_routes_from_excel(filepath)
    elif data_type == 'customers':
        return import_customers_from_excel(filepath)
    else:
        return False, "نوع داده نامعتبر است"