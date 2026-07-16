# main.py
# ========== فایل اصلی برنامه ==========

import os
import json
import sys
import traceback
from kivy.config import Config
from kivy.core.text import LabelBase
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager
from kivy.utils import platform
from kivy.clock import Clock
from kivy.metrics import dp, sp

# ========== ایمپورت ماژول‌های جدید ==========
from constants import ROLES, ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD
from error_handler import ErrorPopup, exception_handler

# ========== ایمپورت صفحات ==========
from screens import (
    LoginScreen,
    RegisterScreen,
    AdminScreen,
    AdminSettingsScreen,
    UserScreen,
    ReportScreen,
    SettingsLoginScreen,
    DebugScreen,
    AgentsScreen,
    SupervisorScreen,
    DistributorScreen 

)

# ========== تنظیم فونت ==========
def setup_font():
    """تنظیم فونت فارسی + دیباگ کامل"""
    print("\n" + "=" * 60)
    print("شروع بررسی فونت")
    print("=" * 60)

    print("Current Working Directory:")
    print(os.getcwd())

    print("\nRoot files:")
    try:
        print(os.listdir("."))
    except Exception as e:
        print("خطا:", e)

    print("\nFonts directory:")
    try:
        print(os.listdir("fonts"))
    except Exception as e:
        print("خطا:", e)

    print("=" * 60)

    font_paths = [
        "fonts/Amiri-Regular.ttf",
        "fonts/Lateef-Regular.ttf",
        "fonts/NotoNasrArabic-Regular.ttf",
        "fonts/Vazirmatn-Regular.ttf",
        os.path.join(os.path.dirname(__file__), "fonts", "Amiri-Regular.ttf"),
        os.path.join(os.path.dirname(__file__), "fonts", "Lateef-Regular.ttf"),
        os.path.join(os.path.dirname(__file__), "fonts", "NotoNasrArabic-Regular.ttf"),
        os.path.join(os.path.dirname(__file__), "fonts", "Vazirmatn-Regular.ttf"),
    ]

    font_path = None

    print("\nبررسی مسیرهای فونت:\n")

    for path in font_paths:
        exists = os.path.exists(path)
        print(f"{path}   --->   {exists}")

        if exists:
            font_path = path
            break

    if font_path:
        print("\nفونت انتخاب شد:")
        print(font_path)

        try:
            LabelBase.register(
                name="PersianFont",
                fn_regular=font_path
            )
            print("فونت با نام 'PersianFont' ثبت شد.")

            Config.set('kivy', 'default_font', ['PersianFont', 'Roboto'])
            print("فونت پیش‌فرض تنظیم شد.")

            return True

        except Exception as e:
            print("خطا در ثبت فونت:")
            print(e)
            Config.set('kivy', 'default_font', ['Roboto'])
            return False

    else:
        print("\nهیچ فونتی پیدا نشد.")
        Config.set('kivy', 'default_font', ['Roboto'])
        return False

# ========== تنظیمات پنجره ==========
if platform != 'android':
    Window.size = (400, 650)

# ========== تنظیم فونت ==========
setup_font()

# ========== ایمپورت ماژول‌های برنامه ==========
try:
    from utils.rtl_widgets import RTLTextInput, RTLSpinner, PersianComboBox, PersianButton, RTLLabel
    from utils.persian_text import PersianLabel
    from utils.text_helper import f
    from utils.storage import get_data_path, init_data_path
    from utils.file_manager import (
        get_agents, add_agent, delete_agent,
        get_routes, add_route, delete_route,
        get_customers, add_customer, delete_customer,
        get_settings, update_settings,
        get_daily_logs, save_daily_log
    )
    from utils.jalali_date import get_today_jalali, get_current_time
    from utils.user_manager import login, register_user, get_users, delete_user_by_id, get_codes, create_code
    from utils.auth import get_admin_password, set_admin_password, verify_password
    from utils.excel_importer import import_routes_from_excel, import_customers_from_excel
    from utils.excel_exporter import export_to_excel

    RTLLabel = PersianLabel
    
except Exception as e:
    error_details = traceback.format_exc()
    ErrorPopup.show_error(f"خطا در بارگذاری ماژول‌ها: {e}", error_details)


# ========== کلاس اصلی برنامه ==========
class ScreenManagement(ScreenManager):
    pass


class MainApp(App):
    def build(self):
        try:
            self.data_path = init_data_path()
            os.makedirs(os.path.join(self.data_path, 'reports'), exist_ok=True)
            
            self.init_json_files()
            
            sm = ScreenManagement()
            sm.add_widget(LoginScreen(name='login'))
            sm.add_widget(RegisterScreen(name='register'))
            sm.add_widget(AdminScreen(name='admin'))
            sm.add_widget(AdminSettingsScreen(name='admin_settings'))
            sm.add_widget(UserScreen(name='user'))
            sm.add_widget(ReportScreen(name='report'))
            sm.add_widget(SettingsLoginScreen(name='settings_login'))
            sm.add_widget(DebugScreen(name='debug'))
            sm.add_widget(AgentsScreen(name='agents'))
            sm.add_widget(SupervisorScreen(name='supervisor'))
            sm.add_widget(DistributorScreen(name='distributor')) 

            Window.bind(on_keyboard=self.on_keyboard)
            
            return sm
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در راه‌اندازی برنامه: {e}", error_details)
            return ScreenManager()
    
    def on_keyboard(self, window, key, *args):
        if key == 27:
            current_screen = self.root.current
            
            if current_screen == 'login':
                self.stop()
                return True
            elif current_screen == 'admin_settings':
                self.root.current = 'settings_login'
                return True
            elif current_screen == 'settings_login':
                self.root.current = 'login'
                return True
            elif current_screen == 'register':
                self.root.current = 'login'
                return True
            elif current_screen == 'admin':
                self.root.current = 'login'
                return True
            elif current_screen == 'supervisor':
                self.root.current = 'login'
                return True
            elif current_screen == 'user':
                self.root.current = 'login'
                return True
            elif current_screen == 'report':
                self.root.current = 'user'
                return True
            elif current_screen == 'debug':
                self.root.current = 'login'
                return True
            elif current_screen == 'agents':
                self.root.current = 'user'
                return True
        
        return False
    
    def init_json_files(self):
        try:
            from utils.auth import hash_password
            
            hashed_default = hash_password(DEFAULT_ADMIN_PASSWORD)
            
            default_data = {
                'definitions.json': {
                    'agents': [],
                    'routes': [],
                    'customers': []
                },
                'settings.json': {
                    'supervision_rate': 0.3,
                    'conversion_rate': 0.25,
                    'avg_invoice_amount': 1000000,
                    'target_amount': 50000000,
                    'target_count': 100,
                    'target_invoice_count': 20,
                    'target_customer_count': 50,
                    'target_new_customer_count': 10,
                    'target_cash_sales': 30000000,
                    'target_credit_sales': 20000000,
                    'work_start_time': '08:00',
                    'first_visit_time': '09:00',
                    'min_daily_hours': 6,
                    'first_customer_of_route': ''
                },
                'daily_log.json': {},
                'users.json': {'users': []},
                'codes.json': {'codes': []},
                'admin_password.json': {'hashed_password': hashed_default},
                'targets.json': []
            }
            
            from utils.storage import get_data_path
            data_path = get_data_path()
            
            for filename, default_content in default_data.items():
                filepath = os.path.join(data_path, filename)
                if not os.path.exists(filepath):
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(default_content, f, ensure_ascii=False, indent=2)
                    print(f"فایل {filename} ایجاد شد")
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ایجاد فایل‌های اولیه: {e}", error_details)
            raise


if __name__ == '__main__':
    try:
        MainApp().run()
    except Exception as e:
        error_details = traceback.format_exc()
        try:
            from kivy.uix.popup import Popup
            from kivy.uix.label import Label
            from kivy.uix.button import Button
            from kivy.uix.boxlayout import BoxLayout
            
            class EmergencyApp(App):
                def build(self):
                    content = BoxLayout(orientation='vertical', padding=20, spacing=15)
                    content.add_widget(Label(text=f"خطای بحرانی:\n{str(e)}", size_hint_y=None, height=200))
                    btn = Button(text='بستن', size_hint_y=None, height=50)
                    content.add_widget(btn)
                    popup = Popup(title='خطا', content=content, size_hint=(0.9, 0.6), auto_dismiss=False)
                    btn.bind(on_press=popup.dismiss)
                    popup.open()
                    return BoxLayout()
            
            EmergencyApp().run()
        except:
            print("="*60)
            print(f"خطای بحرانی: {e}")
            print(error_details)
            print("="*60)