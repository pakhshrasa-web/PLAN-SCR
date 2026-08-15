"""
مدیریت ذخیره‌سازی داده‌ها - نسخه یکپارچه نهایی
هماهنگ‌سازی مسیرها در ویندوز و اندروید
"""

import os
import json
import time
import hashlib
import urllib.parse
from kivy.utils import platform
from kivy.logger import Logger as logger

# ============================================================
# کش مسیرها
# ============================================================

_cache = {
    'data_path': None,
    'app_import': None,
    'app_export': None,
    'app_backup': None,
    'public_import': None,
    'public_export': None,
    'public_backup': None,
}

# ============================================================
# مسیر ذخیره‌سازی داخلی اپ (یکسان در ویندوز و اندروید)
# ============================================================

def init_data_path():
    """مقداردهی اولیه مسیر ذخیره‌سازی داخلی اپ"""
    if _cache['data_path'] is not None:
        return _cache['data_path']
    
    app_name = 'planandroid'
    
    if platform == 'android':
        try:
            from android.storage import app_storage_path
            path = app_storage_path()
            if path and path.strip():
                _cache['data_path'] = path
                logger.info(f"مسیر اندروید: {_cache['data_path']}")
            else:
                raise Exception("app_storage_path returned empty")
        except Exception as e:
            logger.warning(f"خطا در دریافت مسیر اندروید: {e}")
            _cache['data_path'] = '/data/data/org.pakhshrasa.planandroid/files'
    elif platform == 'win':
        _cache['data_path'] = os.path.join(os.environ.get('APPDATA', os.getcwd()), app_name)
        logger.info(f"مسیر ویندوز: {_cache['data_path']}")
    elif platform in ('linux', 'macosx'):
        _cache['data_path'] = os.path.join(os.path.expanduser('~'), f'.{app_name}')
        logger.info(f"مسیر لینوکس/مک: {_cache['data_path']}")
    else:
        _cache['data_path'] = os.path.join(os.getcwd(), app_name)
        logger.info(f"مسیر پیش‌فرض: {_cache['data_path']}")
    
    try:
        os.makedirs(_cache['data_path'], exist_ok=True)
        logger.info(f"پوشه داده ایجاد شد: {_cache['data_path']}")
    except Exception as e:
        logger.error(f"خطا در ایجاد پوشه داده: {e}")
        _cache['data_path'] = os.path.join(os.getcwd(), app_name)
        os.makedirs(_cache['data_path'], exist_ok=True)
    
    return _cache['data_path']

def get_data_path():
    """بازگرداندن مسیر ذخیره‌سازی داخلی اپ"""
    if _cache['data_path'] is None:
        init_data_path()
    return _cache['data_path']

# ============================================================
# توابع مسیردهی پوشه شخصی برنامه
# ============================================================

def get_app_import_path():
    """دریافت مسیر پوشه import در داده‌های برنامه"""
    if _cache['app_import'] is None:
        path = os.path.join(get_data_path(), 'import')
        os.makedirs(path, exist_ok=True)
        _cache['app_import'] = path
        logger.info(f"مسیر import (شخصی): {path}")
    return _cache['app_import']

def get_app_export_path():
    """دریافت مسیر پوشه export در داده‌های برنامه"""
    if _cache['app_export'] is None:
        path = os.path.join(get_data_path(), 'export')
        os.makedirs(path, exist_ok=True)
        _cache['app_export'] = path
        logger.info(f"مسیر export (شخصی): {path}")
    return _cache['app_export']

def get_app_backup_path():
    """دریافت مسیر پوشه backup در داده‌های برنامه"""
    if _cache['app_backup'] is None:
        path = os.path.join(get_data_path(), 'backup')
        os.makedirs(path, exist_ok=True)
        _cache['app_backup'] = path
        logger.info(f"مسیر backup (شخصی): {path}")
    return _cache['app_backup']

# ============================================================
# توابع مسیردهی عمومی
# ============================================================

def _get_public_base_path():
    """دریافت مسیر پایه عمومی (Download)"""
    if platform == 'android':
        try:
            from android.storage import primary_external_storage_path
            base = primary_external_storage_path()
            if base:
                return os.path.join(base, 'Download')
        except Exception as e:
            logger.warning(f"خطا در دریافت مسیر عمومی: {e}")
        return '/storage/emulated/0/Download/'
    else:
        return os.path.join(os.path.expanduser('~'), 'Downloads')

def get_public_import_path():
    """دریافت مسیر عمومی import"""
    if _cache['public_import'] is None:
        path = os.path.join(_get_public_base_path(), 'plan_android_data', 'import')
        try:
            os.makedirs(path, exist_ok=True)
        except Exception as e:
            logger.warning(f"خطا در ایجاد مسیر عمومی import: {e}")
        _cache['public_import'] = path
        logger.info(f"مسیر عمومی import: {path}")
    return _cache['public_import']

def get_public_export_path():
    """دریافت مسیر عمومی export"""
    if _cache['public_export'] is None:
        path = os.path.join(_get_public_base_path(), 'plan_android_data', 'export')
        try:
            os.makedirs(path, exist_ok=True)
        except Exception as e:
            logger.warning(f"خطا در ایجاد مسیر عمومی export: {e}")
        _cache['public_export'] = path
        logger.info(f"مسیر عمومی export: {path}")
    return _cache['public_export']

def get_public_backup_path():
    """دریافت مسیر عمومی backup (در Download/PlanAndroid_Backup)"""
    if _cache['public_backup'] is None:
        path = os.path.join(_get_public_base_path(), 'PlanAndroid_Backup')
        try:
            os.makedirs(path, exist_ok=True)
        except Exception as e:
            logger.warning(f"خطا در ایجاد مسیر عمومی backup: {e}")
        _cache['public_backup'] = path
        logger.info(f"مسیر عمومی backup: {path}")
    return _cache['public_backup']

# ============================================================
# توابع اصلی مسیردهی
# ============================================================

def get_import_path():
    """دریافت مسیر import (در اندروید: شخصی، در دسکتاپ: عمومی)"""
    if platform == 'android':
        return get_app_import_path()
    else:
        return get_public_import_path()

def get_export_path():
    """دریافت مسیر export (در اندروید: عمومی، در دسکتاپ: عمومی)"""
    return get_public_export_path()

def get_backup_path():
    """دریافت مسیر backup (در اندروید: عمومی، در دسکتاپ: شخصی)"""
    if platform == 'android':
        return get_public_backup_path()
    else:
        return get_app_backup_path()

# ============================================================
# تابع کپی با Python IO
# ============================================================

def copy_uri_to_app_folder(uri, filename=None, target_folder='import', file_type='excel'):
    """کپی فایل از URI به پوشه شخصی برنامه"""
    try:
        from android import mActivity
        from jnius import autoclass
        
        if isinstance(uri, str):
            Uri_class = autoclass("android.net.Uri")
            uri = Uri_class.parse(uri)
        
        if not filename:
            filename = _extract_filename_from_uri(uri, file_type)
        
        if not filename:
            logger.error("نام فایل نامعتبر")
            return None
        
        if target_folder == 'import':
            dest_folder = get_app_import_path()
        elif target_folder == 'export':
            dest_folder = get_app_export_path()
        elif target_folder == 'backup':
            dest_folder = get_app_backup_path()
        else:
            dest_folder = get_app_import_path()
        
        os.makedirs(dest_folder, exist_ok=True)
        dest_path = os.path.join(dest_folder, filename)
        
        logger.info(f"کپی فایل: {uri} → {dest_path}")
        
        content_resolver = mActivity.getContentResolver()
        input_stream = content_resolver.openInputStream(uri)
        
        if not input_stream:
            logger.error("نمی‌توان InputStream دریافت کرد")
            return None
        
        try:
            with open(dest_path, 'wb') as output_file:
                buffer = bytearray(8192)
                while True:
                    try:
                        count = input_stream.read(buffer)
                        if count <= 0:
                            break
                        output_file.write(buffer[:count])
                    except TypeError:
                        while True:
                            data = input_stream.read()
                            if data == -1:
                                break
                            output_file.write(bytes([data]))
                        break
        finally:
            try:
                input_stream.close()
            except:
                pass
        
        if os.path.exists(dest_path):
            size = os.path.getsize(dest_path)
            logger.info(f"فایل با موفقیت کپی شد: {dest_path} ({size} bytes)")
            return dest_path
        else:
            logger.error("فایل کپی نشد")
            return None
        
    except Exception as e:
        logger.error(f"خطا در کپی URI: {e}")
        import traceback
        traceback.print_exc()
        return None

# ============================================================
# استخراج نام فایل از URI
# ============================================================

def _extract_filename_from_uri(uri, file_type='excel'):
    """استخراج نام فایل از URI"""
    try:
        from android import mActivity
        from android.provider import OpenableColumns
        from jnius import autoclass
        
        if isinstance(uri, str):
            Uri_class = autoclass("android.net.Uri")
            uri = Uri_class.parse(uri)
        
        content_resolver = mActivity.getContentResolver()
        
        try:
            cursor = content_resolver.query(
                uri,
                [OpenableColumns.DISPLAY_NAME],
                None,
                None,
                None
            )
            if cursor and cursor.moveToFirst():
                name_index = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                if name_index >= 0:
                    filename = cursor.getString(name_index)
                    cursor.close()
                    if filename:
                        logger.info(f"نام فایل از cursor: {filename}")
                        return filename
            if cursor:
                cursor.close()
        except Exception as e:
            logger.warning(f"خطا در OpenableColumns: {e}")
        
        raw = str(uri)
        if '%' in raw:
            raw = urllib.parse.unquote(raw)
        
        filename = raw.split('/')[-1]
        if '?' in filename:
            filename = filename.split('?')[0]
        
        if filename and '.' in filename:
            logger.info(f"نام فایل از Uri: {filename}")
            return filename
        
        hash_val = hashlib.md5(str(uri).encode()).hexdigest()[:8]
        
        if file_type == 'excel':
            filename = f"file_{hash_val}.xlsx"
        elif file_type == 'backup':
            filename = f"file_{hash_val}.zip"
        else:
            filename = f"file_{hash_val}.dat"
        
        logger.info(f"نام فایل پیش‌فرض: {filename}")
        return filename
        
    except Exception as e:
        logger.warning(f"خطا در استخراج نام فایل: {e}")
        return None

# ============================================================
# حذف فایل‌های قدیمی
# ============================================================

def delete_old_backup_files(days=30):
    """حذف فایل‌های اکسل قدیمی‌تر از تعداد روز مشخص"""
    try:
        backup_path = get_backup_path()
        if not os.path.exists(backup_path):
            return 0
        
        now = time.time()
        deleted_count = 0
        cutoff_time = now - (days * 86400)
        
        for file in os.listdir(backup_path):
            if file.endswith('.xlsx') and file.startswith('گزارش_فروش_'):
                file_path = os.path.join(backup_path, file)
                try:
                    if os.path.getmtime(file_path) < cutoff_time:
                        os.remove(file_path)
                        deleted_count += 1
                        logger.info(f"فایل قدیمی حذف شد: {file}")
                except Exception as e:
                    logger.error(f"خطا در حذف فایل {file}: {e}")
                    continue
        
        return deleted_count
        
    except Exception as e:
        logger.error(f"خطا در حذف فایل‌های قدیمی: {e}")
        return 0

# ============================================================
# ============================================================
# ✅ توابع JSON پایه
# ============================================================
# ============================================================

def load_json(filename):
    """بارگذاری فایل JSON از پوشه داده"""
    try:
        path = os.path.join(get_data_path(), filename)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"خطا در بارگذاری {filename}: {e}")
    return {}

def save_json(filename, data):
    """ذخیره فایل JSON در پوشه داده"""
    try:
        path = os.path.join(get_data_path(), filename)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"خطا در ذخیره {filename}: {e}")
        return False

# ============================================================
# ============================================================
# ✅ توابع مدیریت داده‌ها (منتقل شده از file_manager.py)
# ============================================================
# ============================================================

# ========== مدیریت عامل‌ها ==========

def get_agents():
    """دریافت لیست عاملین"""
    data = load_json('definitions.json')
    return data.get('agents', [])

def add_agent(agent):
    """افزودن عامل جدید"""
    data = load_json('definitions.json')
    agents = data.get('agents', [])
    new_id = max([a.get('id', 0) for a in agents]) + 1 if agents else 1
    agent['id'] = new_id
    agents.append(agent)
    data['agents'] = agents
    save_json('definitions.json', data)
    return new_id

def update_agent(agent_id, updated_agent):
    """به‌روزرسانی عامل"""
    data = load_json('definitions.json')
    agents = data.get('agents', [])
    for i, agent in enumerate(agents):
        if agent.get('id') == agent_id:
            updated_agent['id'] = agent_id
            agents[i] = updated_agent
            break
    data['agents'] = agents
    save_json('definitions.json', data)

def delete_agent(agent_id):
    """حذف عامل"""
    data = load_json('definitions.json')
    agents = data.get('agents', [])
    agents = [a for a in agents if a.get('id') != agent_id]
    data['agents'] = agents
    save_json('definitions.json', data)

# ========== مدیریت مسیرها ==========

def get_routes():
    """دریافت لیست مسیرها"""
    data = load_json('definitions.json')
    return data.get('routes', [])

def add_route(route):
    """افزودن مسیر جدید"""
    data = load_json('definitions.json')
    routes = data.get('routes', [])
    new_id = max([r.get('id', 0) for r in routes]) + 1 if routes else 1
    route['id'] = new_id
    routes.append(route)
    data['routes'] = routes
    save_json('definitions.json', data)
    return new_id

def update_route(route_id, updated_route):
    """به‌روزرسانی مسیر"""
    data = load_json('definitions.json')
    routes = data.get('routes', [])
    for i, route in enumerate(routes):
        if route.get('id') == route_id:
            updated_route['id'] = route_id
            routes[i] = updated_route
            break
    data['routes'] = routes
    save_json('definitions.json', data)

def delete_route(route_id):
    """حذف مسیر"""
    data = load_json('definitions.json')
    routes = data.get('routes', [])
    routes = [r for r in routes if r.get('id') != route_id]
    data['routes'] = routes
    save_json('definitions.json', data)

# ========== مدیریت مشتریان ==========

def get_customers():
    """دریافت لیست مشتریان"""
    data = load_json('definitions.json')
    return data.get('customers', [])

def get_customers_by_route(route_name):
    """دریافت مشتریان یک مسیر"""
    customers = get_customers()
    return [c for c in customers if c.get('route_name') == route_name]

def add_customer(customer):
    """افزودن مشتری جدید"""
    data = load_json('definitions.json')
    customers = data.get('customers', [])
    new_id = max([c.get('id', 0) for c in customers]) + 1 if customers else 1
    customer['id'] = new_id
    customers.append(customer)
    data['customers'] = customers
    save_json('definitions.json', data)
    return new_id

def update_customer(customer_id, updated_customer):
    """به‌روزرسانی مشتری"""
    data = load_json('definitions.json')
    customers = data.get('customers', [])
    for i, customer in enumerate(customers):
        if customer.get('id') == customer_id:
            updated_customer['id'] = customer_id
            customers[i] = updated_customer
            break
    data['customers'] = customers
    save_json('definitions.json', data)

def delete_customer(customer_id):
    """حذف مشتری"""
    data = load_json('definitions.json')
    customers = data.get('customers', [])
    customers = [c for c in customers if c.get('id') != customer_id]
    data['customers'] = customers
    save_json('definitions.json', data)

# ========== مدیریت تنظیمات ==========

def get_settings():
    """دریافت تنظیمات"""
    return load_json('settings.json')

def update_settings(new_settings):
    """به‌روزرسانی تنظیمات"""
    settings = get_settings()
    settings.update(new_settings)
    save_json('settings.json', settings)

# ========== مدیریت لاگ روزانه ==========

def get_daily_logs():
    """دریافت لاگ‌های روزانه"""
    return load_json('daily_log.json')

def get_daily_log(date):
    """دریافت لاگ یک روز"""
    logs = get_daily_logs()
    return logs.get(date, {})

def save_daily_log(date, log_data):
    """ذخیره لاگ روزانه"""
    logs = get_daily_logs()
    logs[date] = log_data
    save_json('daily_log.json', logs)

def delete_daily_log(date):
    """حذف لاگ روزانه"""
    logs = get_daily_logs()
    if date in logs:
        del logs[date]
        save_json('daily_log.json', logs)

def get_all_logs_sorted():
    """دریافت همه لاگ‌ها به صورت مرتب"""
    logs = get_daily_logs()
    return sorted(logs.items(), key=lambda x: x[0], reverse=True)

# ========== مدیریت تنظیمات تارگت ==========

def get_target_settings():
    """دریافت تنظیمات تارگت"""
    data = load_json('target_settings.json')
    if not data:
        data = {
            'target_units': ["کارتن", "عدد", "شل", "بسته", "جعبه", "بانکه"],
            'target_periods': ["روزانه", "ماهانه", "فصلی", "سالیانه"]
        }
        save_json('target_settings.json', data)
    return data

def save_target_settings(settings_data):
    """ذخیره تنظیمات تارگت"""
    return save_json('target_settings.json', settings_data)

# ========== مدیریت واحدهای تارگت ==========

def get_target_units():
    """دریافت لیست واحدهای تارگت"""
    settings = get_target_settings()
    return settings.get('target_units', ["کارتن", "عدد", "شل", "بسته", "جعبه", "بانکه"])

def add_target_unit(name):
    """افزودن واحد تارگت جدید"""
    settings = get_target_settings()
    units = settings.get('target_units', [])
    if name not in units:
        units.append(name)
        settings['target_units'] = units
        save_target_settings(settings)
        return True
    return False

def update_target_unit(old_name, new_name):
    """ویرایش واحد تارگت"""
    settings = get_target_settings()
    units = settings.get('target_units', [])
    if old_name in units:
        idx = units.index(old_name)
        units[idx] = new_name
        settings['target_units'] = units
        save_target_settings(settings)
        return True
    return False

def delete_target_unit(name):
    """حذف واحد تارگت"""
    settings = get_target_settings()
    units = settings.get('target_units', [])
    if len(units) <= 2:
        return False
    if name in units:
        units.remove(name)
        settings['target_units'] = units
        save_target_settings(settings)
        return True
    return False

# ========== مدیریت دوره‌های تارگت ==========

def get_target_periods():
    """دریافت لیست دوره‌های تارگت"""
    settings = get_target_settings()
    return settings.get('target_periods', ["روزانه", "ماهانه", "فصلی", "سالیانه"])

def add_target_period(name):
    """افزودن دوره تارگت جدید"""
    settings = get_target_settings()
    periods = settings.get('target_periods', [])
    if name not in periods:
        periods.append(name)
        settings['target_periods'] = periods
        save_target_settings(settings)
        return True
    return False

def update_target_period(old_name, new_name):
    """ویرایش دوره تارگت"""
    settings = get_target_settings()
    periods = settings.get('target_periods', [])
    if old_name in periods:
        idx = periods.index(old_name)
        periods[idx] = new_name
        settings['target_periods'] = periods
        save_target_settings(settings)
        return True
    return False

def delete_target_period(name):
    """حذف دوره تارگت"""
    settings = get_target_settings()
    periods = settings.get('target_periods', [])
    if len(periods) <= 2:
        return False
    if name in periods:
        periods.remove(name)
        settings['target_periods'] = periods
        save_target_settings(settings)
        return True
    return False

# ========== مدیریت محصولات (گروه کالا) ==========

def get_product_groups():
    """دریافت لیست گروه‌های کالا"""
    data = load_json('products.json')
    return data.get('product_groups', [])

def add_product_group(name):
    """افزودن گروه کالا جدید"""
    data = load_json('products.json')
    groups = data.get('product_groups', [])
    if name not in groups:
        groups.append(name)
        data['product_groups'] = groups
        save_json('products.json', data)
        return True
    return False

def update_product_group(old_name, new_name):
    """ویرایش نام گروه کالا"""
    data = load_json('products.json')
    groups = data.get('product_groups', [])
    if old_name in groups:
        idx = groups.index(old_name)
        groups[idx] = new_name
        data['product_groups'] = groups
        save_json('products.json', data)
        return True
    return False

def delete_product_group(name):
    """حذف گروه کالا"""
    data = load_json('products.json')
    groups = data.get('product_groups', [])
    if name in groups:
        groups.remove(name)
        data['product_groups'] = groups
        save_json('products.json', data)
        return True
    return False

# ========== مدیریت ماموریت‌ها ==========

def get_do_missions():
    """دریافت لیست ماموریت‌ها"""
    try:
        data = load_json('do_missions.json')
        if data is None:
            return []
        
        if isinstance(data, dict):
            missions_list = []
            for date, missions in data.items():
                if isinstance(missions, list):
                    for m in missions:
                        if isinstance(m, dict):
                            m['date'] = date
                            missions_list.append(m)
            return missions_list
        
        if isinstance(data, list):
            return data
        
        return []
        
    except Exception as e:
        logger.error(f"خطا در دریافت ماموریت‌ها: {e}")
        return []

def save_do_mission(mission_data):
    """ذخیره یک ماموریت جدید"""
    try:
        import uuid
        from utils.jalali_date import get_today_jalali, get_current_time
        
        missions = load_json('do_missions.json')
        if not isinstance(missions, dict):
            missions = {}
        
        mission_id = f"MSN-{uuid.uuid4().hex[:4].upper()}"
        mission_data['id'] = mission_id
        mission_data['created_at'] = f"{get_today_jalali()} {get_current_time()}"
        
        today = get_today_jalali()
        if today not in missions:
            missions[today] = []
        
        missions[today].append(mission_data)
        
        if save_json('do_missions.json', missions):
            return True, "ماموریت با موفقیت ثبت شد", mission_id
        else:
            return False, "خطا در ذخیره ماموریت", None
            
    except Exception as e:
        logger.error(f"خطا در ذخیره ماموریت: {e}")
        return False, f"خطا: {str(e)}", None

def update_do_mission(mission_id, updated_data):
    """به‌روزرسانی یک ماموریت"""
    try:
        missions = load_json('do_missions.json')
        if not isinstance(missions, dict):
            return False, "هیچ ماموریتی یافت نشد"
        
        for date, items in missions.items():
            if isinstance(items, list):
                for i, item in enumerate(items):
                    if isinstance(item, dict) and item.get('id') == mission_id:
                        for key, value in updated_data.items():
                            item[key] = value
                        missions[date][i] = item
                        
                        if save_json('do_missions.json', missions):
                            return True, "ماموریت با موفقیت به‌روزرسانی شد"
                        else:
                            return False, "خطا در ذخیره تغییرات"
        
        return False, "ماموریت یافت نشد"
        
    except Exception as e:
        logger.error(f"خطا در به‌روزرسانی ماموریت: {e}")
        return False, f"خطا: {str(e)}"

def delete_do_mission(mission_id):
    """حذف یک ماموریت"""
    try:
        missions = load_json('do_missions.json')
        if not isinstance(missions, dict):
            return False, "هیچ ماموریتی یافت نشد"
        
        for date, items in missions.items():
            if isinstance(items, list):
                for i, item in enumerate(items):
                    if isinstance(item, dict) and item.get('id') == mission_id:
                        del missions[date][i]
                        if not missions[date]:
                            del missions[date]
                        
                        if save_json('do_missions.json', missions):
                            return True, "ماموریت با موفقیت حذف شد"
                        else:
                            return False, "خطا در ذخیره تغییرات"
        
        return False, "ماموریت یافت نشد"
        
    except Exception as e:
        logger.error(f"خطا در حذف ماموریت: {e}")
        return False, f"خطا: {str(e)}"

def get_do_missions_by_date(date=None):
    """دریافت ماموریت‌های یک تاریخ مشخص"""
    try:
        from utils.jalali_date import get_today_jalali
        
        if not date:
            date = get_today_jalali()
        
        missions = load_json('do_missions.json')
        if not isinstance(missions, dict):
            return []
        
        return missions.get(date, [])
        
    except Exception as e:
        logger.error(f"خطا در دریافت ماموریت‌های تاریخ {date}: {e}")
        return []

def get_do_missions_by_agent(agent_name, date=None):
    """دریافت ماموریت‌های یک عامل در تاریخ مشخص"""
    try:
        if date:
            missions = get_do_missions_by_date(date)
            return [m for m in missions if isinstance(m, dict) and m.get('agent_name') == agent_name]
        else:
            all_missions = get_do_missions()
            return [m for m in all_missions if isinstance(m, dict) and m.get('agent_name') == agent_name]
        
    except Exception as e:
        logger.error(f"خطا در دریافت ماموریت‌های عامل {agent_name}: {e}")
        return []

# ============================================================
# تابع تست
# ============================================================

def test_paths():
    """تست تمام مسیرها"""
    print("\n" + "="*50)
    print("تست مسیرها:")
    print("="*50)
    print(f"Data path: {get_data_path()}")
    print(f"App Import: {get_app_import_path()}")
    print(f"App Export: {get_app_export_path()}")
    print(f"App Backup: {get_app_backup_path()}")
    print(f"Public Import: {get_public_import_path()}")
    print(f"Public Export: {get_public_export_path()}")
    print(f"Public Backup: {get_public_backup_path()}")
    print(f"Import (main): {get_import_path()}")
    print(f"Export (main): {get_export_path()}")
    print(f"Backup (main): {get_backup_path()}")
    print("="*50)

# ============================================================
# اجرای تست در صورت اجرای مستقیم
# ============================================================

if __name__ == '__main__':
    test_paths()