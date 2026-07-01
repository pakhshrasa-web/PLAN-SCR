"""
مدیریت فایل‌های JSON - نسخه کامل با پشتیبانی از اندروید
"""

import os
import json
from kivy.app import App
from kivy.utils import platform

def get_data_path():
    """
    دریافت مسیر پوشه دیتا
    پشتیبانی از اندروید و دسکتاپ
    """
    try:
        app = App.get_running_app()
        if app:
            if hasattr(app, 'user_data_dir'):
                path = app.user_data_dir
                os.makedirs(path, exist_ok=True)
                return path
            elif hasattr(app, 'data_path'):
                path = app.data_path
                os.makedirs(path, exist_ok=True)
                return path
    except:
        pass
    
    if platform == 'android':
        try:
            from android.storage import app_storage_path
            path = app_storage_path()
            if path:
                os.makedirs(path, exist_ok=True)
                return path
        except:
            pass
    
    path = os.path.join(os.getcwd(), 'data')
    os.makedirs(path, exist_ok=True)
    return path

def load_json(filename):
    """بارگذاری فایل JSON"""
    try:
        filepath = os.path.join(get_data_path(), filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ خطا در بارگذاری {filename}: {e}")
    return {}

def save_json(filename, data):
    """ذخیره فایل JSON"""
    try:
        filepath = os.path.join(get_data_path(), filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ خطا در ذخیره {filename}: {e}")
        return False

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