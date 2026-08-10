"""
مدیریت فایل‌های JSON - نسخه کامل با پشتیبانی از اندروید
"""

import os
import json
from kivy.utils import platform
# ✅ استفاده از storage به جای تعریف مجدد
from utils.storage import get_data_path, load_json, save_json


# ========== مدیریت عامل‌ها ==========
def get_agents():
    data = load_json('definitions.json')
    return data.get('agents', [])

def add_agent(agent):
    data = load_json('definitions.json')
    agents = data.get('agents', [])
    new_id = max([a.get('id', 0) for a in agents]) + 1 if agents else 1
    agent['id'] = new_id
    agents.append(agent)
    data['agents'] = agents
    save_json('definitions.json', data)
    return new_id

def update_agent(agent_id, updated_agent):
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
    data = load_json('definitions.json')
    agents = data.get('agents', [])
    agents = [a for a in agents if a.get('id') != agent_id]
    data['agents'] = agents
    save_json('definitions.json', data)


# ========== مدیریت مسیرها ==========
def get_routes():
    data = load_json('definitions.json')
    return data.get('routes', [])

def add_route(route):
    data = load_json('definitions.json')
    routes = data.get('routes', [])
    new_id = max([r.get('id', 0) for r in routes]) + 1 if routes else 1
    route['id'] = new_id
    routes.append(route)
    data['routes'] = routes
    save_json('definitions.json', data)
    return new_id

def update_route(route_id, updated_route):
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
    data = load_json('definitions.json')
    routes = data.get('routes', [])
    routes = [r for r in routes if r.get('id') != route_id]
    data['routes'] = routes
    save_json('definitions.json', data)


# ========== مدیریت مشتریان ==========
def get_customers():
    data = load_json('definitions.json')
    return data.get('customers', [])

def get_customers_by_route(route_name):
    customers = get_customers()
    return [c for c in customers if c.get('route_name') == route_name]

def add_customer(customer):
    data = load_json('definitions.json')
    customers = data.get('customers', [])
    new_id = max([c.get('id', 0) for c in customers]) + 1 if customers else 1
    customer['id'] = new_id
    customers.append(customer)
    data['customers'] = customers
    save_json('definitions.json', data)
    return new_id

def update_customer(customer_id, updated_customer):
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
    data = load_json('definitions.json')
    customers = data.get('customers', [])
    customers = [c for c in customers if c.get('id') != customer_id]
    data['customers'] = customers
    save_json('definitions.json', data)


# ========== مدیریت تنظیمات ==========
def get_settings():
    return load_json('settings.json')

def update_settings(new_settings):
    settings = get_settings()
    settings.update(new_settings)
    save_json('settings.json', settings)


# ========== مدیریت لاگ روزانه ==========
def get_daily_logs():
    return load_json('daily_log.json')

def get_daily_log(date):
    logs = get_daily_logs()
    return logs.get(date, {})

def save_daily_log(date, log_data):
    logs = get_daily_logs()
    logs[date] = log_data
    save_json('daily_log.json', logs)

def delete_daily_log(date):
    logs = get_daily_logs()
    if date in logs:
        del logs[date]
        save_json('daily_log.json', logs)

def get_all_logs_sorted():
    logs = get_daily_logs()
    return sorted(logs.items(), key=lambda x: x[0], reverse=True)


# ========== مدیریت تنظیمات تارگت ==========

def get_target_settings():
    """دریافت تنظیمات تارگت (واحدها و دوره‌ها)"""
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
    """
    دریافت لیست ماموریت‌ها از فایل do_missions.json
    """
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
        print(f"⚠️ خطا در دریافت ماموریت‌ها: {e}")
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
        print(f"❌ خطا در ذخیره ماموریت: {e}")
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
        print(f"❌ خطا در به‌روزرسانی ماموریت: {e}")
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
        print(f"❌ خطا در حذف ماموریت: {e}")
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
        print(f"⚠️ خطا در دریافت ماموریت‌های تاریخ {date}: {e}")
        return []


def get_do_missions_by_agent(agent_name, date=None):
    """دریافت ماموریت‌های یک عامل در تاریخ مشخص"""
    try:
        from utils.name_matcher import normalize_persian_text
        
        agent_norm = normalize_persian_text(agent_name)
        
        if date:
            missions = get_do_missions_by_date(date)
            return [m for m in missions if isinstance(m, dict) and normalize_persian_text(m.get('agent_name', '')) == agent_norm]
        else:
            all_missions = get_do_missions()
            return [m for m in all_missions if isinstance(m, dict) and normalize_persian_text(m.get('agent_name', '')) == agent_norm]
        
    except Exception as e:
        print(f"⚠️ خطا در دریافت ماموریت‌های عامل {agent_name}: {e}")
        return []


# ========== مدیریت اطلاعات مشتری ==========

def get_customer_by_name(customer_name):
    """دریافت اطلاعات مشتری بر اساس نام"""
    customers = get_customers()
    for c in customers:
        if c.get('name', '').strip() == customer_name.strip():
            return c
    return None


def get_customer_by_mobile(mobile):
    """دریافت اطلاعات مشتری بر اساس موبایل"""
    customers = get_customers()
    mobile_clean = mobile.replace(' ', '').replace('-', '').replace('_', '')
    for c in customers:
        c_mobile = c.get('mobile', '').strip()
        if c_mobile and c_mobile == mobile_clean:
            return c
    return None