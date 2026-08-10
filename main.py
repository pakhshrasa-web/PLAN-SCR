# main.py
# ========== فایل اصلی برنامه ==========

import os
import sys
import shutil
import json         
import traceback    

# ============================================================
# تنظیم لوگو قبل از هر چیز (با Config)
# ============================================================
from kivy.config import Config

# تنظیم لوگو برای ویندوز
Config.set('kivy', 'window_icon', 'icon/kivy-icon-64.ico')

# ============================================================
# 1. ابتدا فونت Roboto رو تنظیم کن
# ============================================================
fonts_dir = os.path.join(os.path.dirname(__file__), 'fonts')

# اطمینان از وجود فایل Roboto.ttf
roboto_path = os.path.join(fonts_dir, 'Roboto.ttf')
if not os.path.exists(roboto_path):
    amiri_path = os.path.join(fonts_dir, 'Amiri-Regular.ttf')
    if os.path.exists(amiri_path):
        shutil.copy2(amiri_path, roboto_path)
        print("Roboto.ttf از Amiri ساخته شد")

# همچنین در مسیر Kivy هم کپی کن
try:
    import kivy
    kivy_fonts_dir = os.path.join(os.path.dirname(kivy.__file__), 'data', 'fonts')
    kivy_roboto_path = os.path.join(kivy_fonts_dir, 'Roboto.ttf')
    if not os.path.exists(kivy_roboto_path) and os.path.exists(roboto_path):
        os.makedirs(kivy_fonts_dir, exist_ok=True)
        shutil.copy2(roboto_path, kivy_roboto_path)
        print(f"Roboto.ttf کپی شد به: {kivy_roboto_path}")
except:
    pass

# ============================================================
# 2. سپس Kivy رو import کن
# ============================================================
from kivy.config import Config  # قبلاً imported شده

# تنظیم فونت پیش‌فرض قبل از هر چیز
Config.set('kivy', 'default_font', [
    os.path.join(fonts_dir, 'Roboto.ttf'),
    os.path.join(fonts_dir, 'Amiri-Regular.ttf')
])

# ============================================================
# 3. حالا بقیه import‌ها
# ============================================================
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
    DistributorScreen,
    DistributorReportScreen,
    AttendanceScreen,
)
from screens.supervisor_report_screen import SupervisorReportScreen
from screens.total_report_screen import TotalReportScreen

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

    # در اندروید از فونت سیستمی استفاده کن
    if platform == 'android':
        font_paths.extend([
            '/system/fonts/NotoNaskhArabic-Regular.ttf',
            '/system/fonts/NotoSansArabic-Regular.ttf',
            '/system/fonts/DroidNaskh-Regular.ttf',
            '/system/fonts/DroidSansFallback.ttf',
        ])

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
    from utils.user_manager import login, register_user, get_users, delete_user_by_id, get_codes, create_code, get_current_user, clear_current_user
    from utils.auth import get_admin_password, set_admin_password, verify_password
    from utils.excel_importer import import_routes_from_excel, import_customers_from_excel
    from utils.excel_exporter import export_to_excel
    from utils.reminder_manager import should_show_reminder, show_complete_reminder_popup 

    RTLLabel = PersianLabel
    
except Exception as e:
    error_details = traceback.format_exc()
    ErrorPopup.show_error(f"خطا در بارگذاری ماژول‌ها: {e}", error_details)


# ========== کلاس اصلی برنامه ==========
class ScreenManagement(ScreenManager):
    pass


class MainApp(App):
    # ============================================================
    # متغیر برای ذخیره نقش کاربر فعلی
    # ============================================================
    current_user_role = ''
    current_username = ''

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
            sm.add_widget(AttendanceScreen(name='attendance'))
            sm.add_widget(ReportScreen(name='report'))
            sm.add_widget(SettingsLoginScreen(name='settings_login'))
            sm.add_widget(DebugScreen(name='debug'))
            sm.add_widget(AgentsScreen(name='agents'))
            sm.add_widget(SupervisorScreen(name='supervisor'))
            sm.add_widget(SupervisorReportScreen(name='supervisor_report'))  
            sm.add_widget(DistributorScreen(name='distributor'))
            sm.add_widget(DistributorReportScreen(name='distributor_report'))
            sm.add_widget(TotalReportScreen(name='total_report')) 

            Window.bind(on_keyboard=self.on_keyboard)
            
            return sm
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در راه‌اندازی برنامه: {e}", error_details)
            return ScreenManager()
    
    def on_start(self):
        """بعد از شروع برنامه - تنظیم لوگو و چک کردن کاربر ذخیره شده"""
        try:
            # ========== تنظیم لوگو ==========
            if platform == 'win':
                icon_path = os.path.join(os.path.dirname(__file__), 'icon', 'kivy-icon-64.ico')
                if os.path.exists(icon_path):
                    try:
                        Window.icon = icon_path
                        print(f"✅ لوگو بارگذاری شد: {icon_path}")
                    except Exception as e:
                        print(f"❌ خطا در بارگذاری لوگو: {e}")
            
            # ========== چک کردن کاربر ذخیره شده ==========
            from utils.user_manager import get_current_user
            # ✅ ایمپورت‌ها قبلاً در بالا انجام شده، دیگه نیازی به تکرار نیست
            
            current_user = get_current_user()
            if current_user:
                username = current_user.get('name', '') or current_user.get('username', '')
                print(f"✅ کاربر ذخیره شده پیدا شد: {username}")
                
                # ذخیره در متغیرهای برنامه
                self.current_user_role = current_user.get('role', '')
                self.current_username = current_user.get('username', '')
                
                # ========== نمایش پاپ‌آپ یادآوری ==========
                if should_show_reminder(username):
                    # ✅ استفاده از تابع جدید
                    Clock.schedule_once(lambda dt: show_complete_reminder_popup(
                        username, 
                        current_user, 
                        self  # ارسال instance برنامه
                    ), 0.5)
                else:
                    print("ℹ️ امروز یادآوری قبلاً نمایش داده شده")
            else:
                print("ℹ️ هیچ کاربر ذخیره‌ای یافت نشد")
                
        except Exception as e:
            print(f"❌ خطا در on_start: {e}")
            import traceback
            traceback.print_exc()
    
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
            elif current_screen == 'total_report':  # ✅ اضافه شد
                self.root.current = 'login'
                return True
            elif current_screen == 'attendance':  # ✅ اضافه شد
                self.root.current = 'login'
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
                    'first_customer_of_route': '',
                    'distributor_target_customers': 30,
                    'distributor_target_invoices': 15,
                    'distributor_target_amount': 30000000,
                    'distributor_target_cash': 15000000,
                    'distributor_target_check': 10000000,
                    'distributor_target_credit': 5000000
                },
                'attendance_config.json': {
                    'late_threshold': 15,
                    'early_leave_threshold': 15,
                    'max_attendance_days': 30,
                    'weekend_days': ['پنجشنبه', 'جمعه'],
                    'holidays': [],
                    'leave_types': ['ساعتی', 'استحقاقی', 'استعلاجی', 'اضطراری', 'بدون حقوق'],
                    'statuses': ['حضور', 'غیبت', 'مرخصی', 'ماموریت', 'تاخیر', 'خروج زودتر'],
                    'annual_leave_limit': 30,
                    'monthly_hourly_leave_limit': '10:00',
                    'hourly_to_daily_ratio': 5
                },
                'daily_log.json': {},
                'users.json': {'users': []},
                'codes.json': {'codes': []},
                'admin_password.json': {'hashed_password': hashed_default},
                'targets.json': [],
                'detailed_targets.json': [],
                'supervisor_visits.json': [],
                'target_settings.json': {
                    'target_units': ["کارتن", "عدد", "شل", "بسته", "جعبه", "بانکه"],
                    'target_periods': ["روزانه", "ماهانه", "فصلی", "سالیانه"]
                },
                'products.json': {'product_groups': []}
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