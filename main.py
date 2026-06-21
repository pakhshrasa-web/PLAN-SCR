"""
اپلیکیشن مدیریت ویزیت و فروش - نسخه کامل و بهینه‌شده برای اندروید
"""

# ========== تنظیم فونت و مسیرها ==========
import os
import sys
import json
import traceback
from kivy.config import Config
from kivy.core.text import LabelBase
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle
from kivy.utils import platform

# ========== مدیریت خطاهای سراسری ==========
def exception_handler(exc_type, exc_value, exc_traceback):
    """هندلر سراسری خطا برای نمایش و ذخیره خطاها"""
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    # ذخیره در فایل
    try:
        from utils.storage import get_data_path
        error_file = os.path.join(get_data_path(), 'error_log.txt')
        with open(error_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*50}\n{error_msg}\n{'='*50}\n")
    except:
        pass
    
    # نمایش در کنسول
    print(f"❌ ERROR: {error_msg}")
    
    # نمایش پاپ‌آپ (اگر برنامه اجرا شده باشد)
    try:
        from kivy.app import App
        app = App.get_running_app()
        if app:
            from kivy.uix.popup import Popup
            from kivy.uix.label import Label
            from kivy.uix.button import Button
            from kivy.uix.boxlayout import BoxLayout
            
            content = BoxLayout(orientation='vertical', padding=20, spacing=10)
            content.add_widget(Label(text=f"خطای برنامه:\n{str(exc_value)[:200]}", halign='center'))
            btn = Button(text='باشه', size_hint_y=None, height=40)
            content.add_widget(btn)
            
            popup = Popup(title='❌ خطا', content=content, size_hint=(0.9, 0.4))
            btn.bind(on_press=popup.dismiss)
            popup.open()
    except:
        pass

sys.excepthook = exception_handler

# ========== مدیریت فونت ==========
def get_font_path():
    """دریافت مسیر فایل فونت - قابل استفاده در همه سیستم‌عامل‌ها"""
    possible_paths = [
        os.path.join(os.path.dirname(__file__), 'fonts', 'Vazirmatn-Regular.ttf'),
        os.path.join(os.path.dirname(__file__), 'fonts', 'Vazirmatn.ttf'),
        os.path.join(os.path.dirname(__file__), 'Vazirmatn-Regular.ttf'),
        os.path.join(os.path.dirname(__file__), 'Vazirmatn.ttf'),
        os.path.join('/system/fonts/', 'Vazirmatn-Regular.ttf'),
        os.path.join('/system/fonts/', 'Vazirmatn.ttf'),
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

# ثبت فونت
font_path = get_font_path()
if font_path:
    try:
        LabelBase.register(name='Vazirmatn', fn_regular=font_path)
        Config.set('kivy', 'default_font', ['Vazirmatn'])
        print(f"✅ فونت با موفقیت از مسیر {font_path} بارگذاری شد")
    except Exception as e:
        print(f"⚠️ خطا در بارگذاری فونت: {e}")
else:
    print("ℹ️ فونت فارسی یافت نشد، استفاده از فونت پیش‌فرض")
    Config.set('kivy', 'default_font', ['Arial'])

# تنظیم اندازه پنجره برای دسکتاپ
if platform != 'android':
    Window.size = (400, 650)

# ========== ایمپورت ماژول‌های برنامه ==========
from utils import (
    # Storage
    get_data_path, init_data_path, load_json, save_json,
    get_agents, add_agent, delete_agent,
    get_routes, add_route, delete_route,
    get_customers, add_customer, delete_customer,
    get_settings, update_settings,
    get_daily_logs, save_daily_log,
    # Jalali Date
    get_today_jalali, get_current_time,
    # User Manager
    login, register_user, get_users, delete_user_by_id, get_codes, create_code,
    # Auth
    get_admin_password, set_admin_password, verify_password,
    # Excel
    import_routes_from_excel, import_customers_from_excel,
    export_to_excel,
    # PDF
    export_to_pdf,
    # RTL
    RTLTextInput, RTLSpinner, RTLLabel,
    # Text Helper
    f, fix_text,
    # File Picker
    FilePicker
)

# ========== تعریف نقش‌ها ==========
ROLES = ['بازاریاب', 'سوپروایزر', 'سرپرست', 'مدیر', 'حسابدار', 'موزع', 'راننده', 'انباردار', 'سایر']

# ========== توابع کمکی ==========
def show_message(title, message):
    """نمایش پیغام به کاربر"""
    content = BoxLayout(orientation='vertical', padding=20, spacing=10)
    content.add_widget(Label(text=f(message), size_hint_y=None, height=50))
    btn = Button(text=f('باشه'), size_hint_y=None, height=40)
    content.add_widget(btn)
    popup = Popup(title=f(title), content=content, size_hint=(0.8, 0.35))
    btn.bind(on_press=popup.dismiss)
    popup.open()
    return popup

# ========== صفحات برنامه ==========

class LoginScreen(Screen):
    """صفحه ورود به سیستم"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()
    
    def build_ui(self):
        layout = BoxLayout(orientation='vertical', spacing=20, padding=40)
        
        # هدر با دکمه تنظیمات
        header_layout = BoxLayout(size_hint_y=0.1, spacing=10)
        settings_btn = Button(text='⚙️', size_hint_x=0.2, background_color=(0.3, 0.3, 0.3, 1))
        settings_btn.bind(on_press=self.open_settings)
        header_layout.add_widget(settings_btn)
        header_layout.add_widget(Label(text='', size_hint_x=0.6))
        header_layout.add_widget(Label(text='', size_hint_x=0.2))
        layout.add_widget(header_layout)
        
        # عنوان
        title = Label(text=f('مدیریت فروش'), font_size='28sp', size_hint_y=0.2)
        layout.add_widget(title)
        
        # فیلدهای ورود
        self.username = RTLTextInput(hint_text='نام کاربری', size_hint_y=None, height=50)
        layout.add_widget(self.username)
        
        self.password = RTLTextInput(hint_text='رمز عبور', password=True, size_hint_y=None, height=50)
        layout.add_widget(self.password)
        
        # دکمه‌ها
        btn = Button(text=f('ورود'), size_hint_y=None, height=50)
        btn.bind(on_press=self.check_login)
        layout.add_widget(btn)
        
        register_btn = Button(text=f('ثبت نام'), size_hint_y=None, height=40, background_color=(0.3, 0.6, 0.3, 1))
        register_btn.bind(on_press=self.open_register)
        layout.add_widget(register_btn)
        
        self.add_widget(layout)
    
    def open_settings(self, instance):
        self.manager.current = 'settings_login'
    
    def open_register(self, instance):
        self.manager.current = 'register'
    
    def check_login(self, instance):
        try:
            user = login(self.username.text, self.password.text)
            if user:
                if user.get('role') == 'مدیر':
                    self.manager.current = 'admin'
                else:
                    self.manager.current = 'user'
            else:
                show_message('خطا', 'نام کاربری یا رمز عبور اشتباه است')
        except Exception as e:
            show_message('خطا', f'خطا در ورود: {str(e)}')


class RegisterScreen(Screen):
    """صفحه ثبت نام کاربر جدید"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()
    
    def build_ui(self):
        layout = BoxLayout(orientation='vertical', spacing=15, padding=40)
        
        title = Label(text=f('ثبت نام کاربر جدید'), font_size='24sp', size_hint_y=0.1)
        layout.add_widget(title)
        
        self.code_input = RTLTextInput(hint_text='کد ثبت نام', multiline=False, size_hint_y=None, height=50)
        layout.add_widget(self.code_input)
        
        self.username = RTLTextInput(hint_text='نام کاربری', multiline=False, size_hint_y=None, height=50)
        layout.add_widget(self.username)
        
        self.password = RTLTextInput(hint_text='رمز عبور', password=True, multiline=False, size_hint_y=None, height=50)
        layout.add_widget(self.password)
        
        self.confirm_password = RTLTextInput(hint_text='تکرار رمز عبور', password=True, multiline=False, size_hint_y=None, height=50)
        layout.add_widget(self.confirm_password)
        
        self.phone = RTLTextInput(hint_text='شماره تلفن', multiline=False, size_hint_y=None, height=50)
        layout.add_widget(self.phone)
        
        self.email = RTLTextInput(hint_text='ایمیل', multiline=False, size_hint_y=None, height=50)
        layout.add_widget(self.email)
        
        btn_layout = BoxLayout(spacing=10, size_hint_y=None, height=50)
        register_btn = Button(text=f('ثبت نام'), background_color=(0.2, 0.7, 0.2, 1))
        register_btn.bind(on_press=self.do_register)
        btn_layout.add_widget(register_btn)
        
        back_btn = Button(text=f('بازگشت'), background_color=(0.5, 0.5, 0.5, 1))
        back_btn.bind(on_press=self.go_back)
        btn_layout.add_widget(back_btn)
        
        layout.add_widget(btn_layout)
        self.add_widget(layout)
    
    def do_register(self, instance):
        try:
            if self.password.text != self.confirm_password.text:
                show_message('خطا', 'رمز عبور و تکرار آن مطابقت ندارند')
                return
            
            success, message = register_user(
                self.code_input.text,
                self.username.text,
                self.password.text,
                self.phone.text,
                self.email.text
            )
            
            if success:
                show_message('موفق', message)
                self.manager.current = 'login'
            else:
                show_message('خطا', message)
        except Exception as e:
            show_message('خطا', f'خطا در ثبت نام: {str(e)}')
    
    def go_back(self, instance):
        self.manager.current = 'login'


class SettingsLoginScreen(Screen):
    """صفحه ورود به تنظیمات"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()
    
    def build_ui(self):
        layout = BoxLayout(orientation='vertical', spacing=20, padding=40)
        
        title = Label(text=f('ورود به تنظیمات سیستم'), font_size='24sp', size_hint_y=0.2)
        layout.add_widget(title)
        
        self.password_input = RTLTextInput(hint_text='رمز عبور مدیر', password=True, multiline=False, size_hint_y=None, height=50)
        layout.add_widget(self.password_input)
        
        btn_layout = BoxLayout(spacing=10, size_hint_y=None, height=50)
        login_btn = Button(text=f('ورود'), background_color=(0.2, 0.6, 1, 1))
        login_btn.bind(on_press=self.check_login)
        btn_layout.add_widget(login_btn)
        
        back_btn = Button(text=f('بازگشت'), background_color=(0.5, 0.5, 0.5, 1))
        back_btn.bind(on_press=self.go_back)
        btn_layout.add_widget(back_btn)
        
        layout.add_widget(btn_layout)
        self.add_widget(layout)
    
    def check_login(self, instance):
        try:
            hashed = get_admin_password()
            if hashed and verify_password(self.password_input.text, hashed):
                self.manager.current = 'admin_settings'
            else:
                show_message('خطا', 'رمز عبور اشتباه است')
                self.password_input.text = ''
        except Exception as e:
            show_message('خطا', f'خطا در ورود: {str(e)}')
    
    def go_back(self, instance):
        self.manager.current = 'login'


class AdminSettingsScreen(Screen):
    """تنظیمات مدیر"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()
    
    def build_ui(self):
        layout = BoxLayout(orientation='vertical')
        
        header = Label(text=f('تنظیمات سیستم'), size_hint_y=0.07, font_size='20sp')
        layout.add_widget(header)
        
        tabs_layout = BoxLayout(size_hint_y=0.08, spacing=2)
        
        btn_users = Button(text=f('مدیریت کاربران'), background_color=(0.3, 0.5, 0.8, 1))
        btn_users.bind(on_press=lambda x: self.switch_tab(0))
        tabs_layout.add_widget(btn_users)
        
        btn_codes = Button(text=f('کدهای ثبت نام'), background_color=(0.3, 0.5, 0.8, 0.6))
        btn_codes.bind(on_press=lambda x: self.switch_tab(1))
        tabs_layout.add_widget(btn_codes)
        
        btn_general = Button(text=f('تنظیمات عمومی'), background_color=(0.3, 0.5, 0.8, 0.6))
        btn_general.bind(on_press=lambda x: self.switch_tab(2))
        tabs_layout.add_widget(btn_general)
        
        btn_password = Button(text=f('تغییر رمز'), background_color=(0.3, 0.5, 0.8, 0.6))
        btn_password.bind(on_press=lambda x: self.switch_tab(3))
        tabs_layout.add_widget(btn_password)
        
        layout.add_widget(tabs_layout)
        
        self.content_area = BoxLayout(orientation='vertical')
        layout.add_widget(self.content_area)
        
        back_btn = Button(text=f('بازگشت'), size_hint_y=0.07, background_color=(0.5, 0.5, 0.5, 1))
        back_btn.bind(on_press=self.go_back)
        layout.add_widget(back_btn)
        
        self.add_widget(layout)
        self.switch_tab(0)
    
    def switch_tab(self, tab_id):
        self.content_area.clear_widgets()
        if tab_id == 0:
            self.show_users_tab()
        elif tab_id == 1:
            self.show_codes_tab()
        elif tab_id == 2:
            self.show_general_settings_tab()
        elif tab_id == 3:
            self.show_change_password_tab()
    
    def show_change_password_tab(self):
        layout = BoxLayout(orientation='vertical', padding=30, spacing=15)
        
        layout.add_widget(Label(text=f('تغییر رمز عبور مدیر'), size_hint_y=None, height=50, font_size='18sp', bold=True))
        layout.add_widget(Label(text=f('رمز عبور فعلی:'), size_hint_y=None, height=30))
        self.old_password = RTLTextInput(password=True, multiline=False, size_hint_y=None, height=45)
        layout.add_widget(self.old_password)
        
        layout.add_widget(Label(text=f('رمز عبور جدید:'), size_hint_y=None, height=30))
        self.new_password = RTLTextInput(password=True, multiline=False, size_hint_y=None, height=45)
        layout.add_widget(self.new_password)
        
        layout.add_widget(Label(text=f('تکرار رمز عبور جدید:'), size_hint_y=None, height=30))
        self.confirm_password = RTLTextInput(password=True, multiline=False, size_hint_y=None, height=45)
        layout.add_widget(self.confirm_password)
        
        btn_layout = BoxLayout(spacing=10, size_hint_y=None, height=50, padding=(0, 20, 0, 0))
        save_btn = Button(text=f('تغییر رمز'), background_color=(0.2, 0.7, 0.2, 1))
        save_btn.bind(on_press=self.change_password)
        btn_layout.add_widget(save_btn)
        
        clear_btn = Button(text=f('پاک کردن'), background_color=(0.8, 0.5, 0.2, 1))
        clear_btn.bind(on_press=self.clear_password_fields)
        btn_layout.add_widget(clear_btn)
        
        layout.add_widget(btn_layout)
        self.content_area.add_widget(layout)
    
    def change_password(self, instance):
        try:
            old = self.old_password.text
            new = self.new_password.text
            confirm = self.confirm_password.text
            
            hashed = get_admin_password()
            if not hashed or not verify_password(old, hashed):
                show_message('خطا', 'رمز عبور فعلی اشتباه است')
                return
            
            if len(new) < 6:
                show_message('خطا', 'رمز عبور جدید باید حداقل 6 کاراکتر باشد')
                return
            
            if new != confirm:
                show_message('خطا', 'رمز عبور جدید و تکرار آن مطابقت ندارند')
                return
            
            set_admin_password(new)
            self.clear_password_fields(instance)
            show_message('موفق', 'رمز عبور با موفقیت تغییر کرد')
        except Exception as e:
            show_message('خطا', f'خطا در تغییر رمز: {str(e)}')
    
    def clear_password_fields(self, instance):
        self.old_password.text = ''
        self.new_password.text = ''
        self.confirm_password.text = ''
    
    def show_users_tab(self):
        try:
            users = get_users()
            
            layout = ScrollView()
            content = GridLayout(cols=1, spacing=10, size_hint_y=None, padding=10)
            content.bind(minimum_height=content.setter('height'))
            
            content.add_widget(Label(text=f('📋 لیست کاربران'), size_hint_y=None, height=40, font_size='16sp', bold=True))
            
            for user in users:
                user_box = BoxLayout(size_hint_y=None, height=80, spacing=5)
                info = f"{user.get('username', '')}\n{user.get('name', '')}\n{user.get('role', '')}"
                user_info = Label(text=f(info), size_hint_x=0.7)
                user_box.add_widget(user_info)
                
                del_btn = Button(text=f('حذف'), size_hint_x=0.3, background_color=(0.8, 0.2, 0.2, 1))
                del_btn.bind(on_press=lambda x, uid=user.get('id'): self.delete_user(uid))
                user_box.add_widget(del_btn)
                content.add_widget(user_box)
            
            layout.add_widget(content)
            self.content_area.add_widget(layout)
        except Exception as e:
            show_message('خطا', f'خطا در نمایش کاربران: {str(e)}')
    
    def delete_user(self, user_id):
        try:
            users = get_users()
            username = ""
            for user in users:
                if user.get('id') == user_id:
                    username = user.get('username', '')
                    break
            
            content = BoxLayout(orientation='vertical', padding=20, spacing=15)
            content.add_widget(Label(text=f(f'آیا از حذف کاربر "{username}" مطمئن هستید؟'), size_hint_y=None, height=50))
            
            btn_layout = BoxLayout(spacing=10, size_hint_y=None, height=50)
            yes_btn = Button(text=f('بله، حذف شود'))
            no_btn = Button(text=f('خیر، انصراف'))
            btn_layout.add_widget(yes_btn)
            btn_layout.add_widget(no_btn)
            content.add_widget(btn_layout)
            
            popup = Popup(title=f('تایید حذف'), content=content, size_hint=(0.8, 0.35))
            
            def do_delete(instance):
                delete_user_by_id(user_id)
                popup.dismiss()
                show_message('موفق', f'کاربر "{username}" با موفقیت حذف شد')
                self.switch_tab(0)
            
            def cancel_delete(instance):
                popup.dismiss()
            
            yes_btn.bind(on_press=do_delete)
            no_btn.bind(on_press=cancel_delete)
            popup.open()
        except Exception as e:
            show_message('خطا', f'خطا در حذف کاربر: {str(e)}')
    
    def show_codes_tab(self):
        try:
            roles = ['مدیر', 'ادمین', 'سوپروایزر', 'بازاریاب', 'حسابدار', 'موزع', 'راننده', 'انباردار', 'سایر']
            
            layout = ScrollView()
            content = GridLayout(cols=1, spacing=10, size_hint_y=None, padding=10)
            content.bind(minimum_height=content.setter('height'))
            
            content.add_widget(Label(text=f('➕ ایجاد کد جدید'), size_hint_y=None, height=40, font_size='16sp', bold=True))
            
            role_spinner = RTLSpinner(text=roles[0], values=roles, size_hint_y=None, height=45)
            content.add_widget(role_spinner)
            
            name_input = RTLTextInput(hint_text='نام و نام خانوادگی', multiline=False, size_hint_y=None, height=45)
            content.add_widget(name_input)
            
            create_btn = Button(text=f('ساخت کد'), size_hint_y=None, height=45, background_color=(0.2, 0.7, 0.2, 1))
            content.add_widget(create_btn)
            
            content.add_widget(Label(text=f('📋 کدهای فعال'), size_hint_y=None, height=40, font_size='16sp', bold=True))
            
            codes = get_codes()
            for code_info in codes:
                if not code_info.get('used', False):
                    code_box = BoxLayout(size_hint_y=None, height=50, spacing=5)
                    code_text = f"{code_info['code']} - {code_info['role']} - {code_info['name']}"
                    code_label = Label(text=f(code_text), size_hint_x=0.8)
                    code_box.add_widget(code_label)
                    content.add_widget(code_box)
            
            def do_create(instance):
                try:
                    code = create_code(role_spinner.text, name_input.text)
                    show_message('موفق', f'کد ساخته شد:\n{code}')
                    self.switch_tab(1)
                except Exception as e:
                    show_message('خطا', f'خطا در ساخت کد: {str(e)}')
            
            create_btn.bind(on_press=do_create)
            
            layout.add_widget(content)
            self.content_area.add_widget(layout)
        except Exception as e:
            show_message('خطا', f'خطا در نمایش کدها: {str(e)}')
    
    def show_general_settings_tab(self):
        try:
            settings = get_settings()
            
            layout = ScrollView()
            content = GridLayout(cols=2, spacing=10, size_hint_y=None, padding=10)
            content.bind(minimum_height=content.setter('height'))
            
            fields = [
                ('supervision_rate', 'درصد سرکشی', '0.3'),
                ('conversion_rate', 'نرخ تبدیل', '0.25'),
                ('avg_invoice_amount', 'میانگین مبلغ فاکتور', '1000000'),
                ('target_amount', 'تارگت ریالی', '50000000'),
                ('work_start_time', 'ساعت شروع کار', '08:00'),
                ('min_daily_hours', 'حداقل ساعت کاری', '6'),
            ]
            
            inputs = {}
            for key, label, default in fields:
                content.add_widget(Label(text=f(label + ':'), size_hint_y=None, height=45))
                input_field = RTLTextInput(text=str(settings.get(key, default)), multiline=False, size_hint_y=None, height=45)
                content.add_widget(input_field)
                inputs[key] = input_field
            
            save_btn = Button(text=f('ذخیره تنظیمات'), size_hint_y=None, height=50, background_color=(0.2, 0.6, 1, 1))
            content.add_widget(save_btn)
            
            layout.add_widget(content)
            self.content_area.add_widget(layout)
            save_btn.bind(on_press=lambda x: self.save_settings(inputs))
        except Exception as e:
            show_message('خطا', f'خطا در نمایش تنظیمات: {str(e)}')
    
    def save_settings(self, inputs):
        try:
            settings = {}
            for key, input_field in inputs.items():
                value = input_field.text
                if key in ['supervision_rate', 'conversion_rate']:
                    try:
                        value = float(value)
                    except:
                        value = 0
                elif key in ['avg_invoice_amount', 'target_amount', 'min_daily_hours']:
                    try:
                        value = int(value)
                    except:
                        value = 0
                settings[key] = value
            update_settings(settings)
            show_message('موفق', 'تنظیمات ذخیره شد')
        except Exception as e:
            show_message('خطا', f'خطا در ذخیره تنظیمات: {str(e)}')
    
    def go_back(self, instance):
        self.manager.current = 'login'


class AdminScreen(Screen):
    """پنل مدیریت"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_tab = 0
        self.build_ui()
    
    def build_ui(self):
        main_layout = BoxLayout(orientation='vertical')
        
        header = Label(text=f('پنل مدیریت'), size_hint_y=0.07, font_size='20sp')
        main_layout.add_widget(header)
        
        tabs_layout = BoxLayout(size_hint_y=0.08, spacing=2)
        
        btn_agents = Button(text=f('عامل‌ها'), background_color=(0.3, 0.5, 0.8, 1))
        btn_agents.bind(on_press=lambda x: self.switch_tab(0))
        tabs_layout.add_widget(btn_agents)
        
        btn_routes = Button(text=f('مسیرها'), background_color=(0.3, 0.5, 0.8, 0.6))
        btn_routes.bind(on_press=lambda x: self.switch_tab(1))
        tabs_layout.add_widget(btn_routes)
        
        btn_customers = Button(text=f('مشتریان'), background_color=(0.3, 0.5, 0.8, 0.6))
        btn_customers.bind(on_press=lambda x: self.switch_tab(2))
        tabs_layout.add_widget(btn_customers)
        
        btn_settings = Button(text=f('⚙️ تنظیمات'), background_color=(0.3, 0.5, 0.8, 0.6))
        btn_settings.bind(on_press=lambda x: self.switch_tab(3))
        tabs_layout.add_widget(btn_settings)
        
        main_layout.add_widget(tabs_layout)
        
        self.content_area = BoxLayout(orientation='vertical')
        main_layout.add_widget(self.content_area)
        
        logout_btn = Button(text=f('خروج'), size_hint_y=0.07, background_color=(0.8, 0.2, 0.2, 1))
        logout_btn.bind(on_press=self.logout)
        main_layout.add_widget(logout_btn)
        
        self.add_widget(main_layout)
        self.switch_tab(0)
    
    def switch_tab(self, tab_id):
        self.current_tab = tab_id
        self.content_area.clear_widgets()
        
        if tab_id == 0:
            self.show_agents_tab()
        elif tab_id == 1:
            self.show_routes_tab()
        elif tab_id == 2:
            self.show_customers_tab()
        elif tab_id == 3:
            self.show_settings_tab()
    
    def show_agents_tab(self):
        try:
            layout = ScrollView()
            content = GridLayout(cols=1, spacing=10, size_hint_y=None, padding=10)
            content.bind(minimum_height=content.setter('height'))
            
            content.add_widget(Label(text=f('➕ افزودن عامل جدید'), size_hint_y=None, height=40, font_size='16sp', bold=True))
            
            name_input = RTLTextInput(hint_text='نام کامل', multiline=False, size_hint_y=None, height=45)
            content.add_widget(name_input)
            
            phone_input = RTLTextInput(hint_text='شماره تلفن', multiline=False, size_hint_y=None, height=45)
            content.add_widget(phone_input)
            
            role_spinner = RTLSpinner(text=ROLES[0], values=ROLES, size_hint_y=None, height=45)
            content.add_widget(role_spinner)
            
            email_input = RTLTextInput(hint_text='ایمیل', multiline=False, size_hint_y=None, height=45)
            content.add_widget(email_input)
            
            add_btn = Button(text=f('افزودن'), size_hint_y=None, height=45, background_color=(0.2, 0.7, 0.2, 1))
            content.add_widget(add_btn)
            
            content.add_widget(Label(text=f('📋 لیست عامل‌ها'), size_hint_y=None, height=40, font_size='16sp', bold=True))
            
            agents = get_agents()
            for agent in agents:
                agent_box = BoxLayout(size_hint_y=None, height=60, spacing=5)
                agent_info = Label(text=f("{agent.get('name', '')}\n{agent.get('role', '')}"), size_hint_x=0.7)
                agent_box.add_widget(agent_info)
                del_btn = Button(text=f('حذف'), size_hint_x=0.3, background_color=(0.8, 0.2, 0.2, 1))
                del_btn.bind(on_press=lambda x, a=agent: self.delete_agent_and_refresh(a.get('id')))
                agent_box.add_widget(del_btn)
                content.add_widget(agent_box)
            
            def do_add(instance):
                if name_input.text:
                    agent = {
                        'name': name_input.text,
                        'phone': phone_input.text,
                        'role': role_spinner.text,
                        'email': email_input.text,
                        'hire_date': get_today_jalali()
                    }
                    add_agent(agent)
                    name_input.text = ''
                    phone_input.text = ''
                    email_input.text = ''
                    show_message('موفق', 'عامل با موفقیت اضافه شد')
                    self.switch_tab(0)
            
            add_btn.bind(on_press=do_add)
            
            layout.add_widget(content)
            self.content_area.add_widget(layout)
        except Exception as e:
            show_message('خطا', f'خطا در نمایش عامل‌ها: {str(e)}')
    
    def delete_agent_and_refresh(self, agent_id):
        try:
            delete_agent(agent_id)
            show_message('موفق', 'عامل با موفقیت حذف شد')
            self.switch_tab(0)
        except Exception as e:
            show_message('خطا', f'خطا در حذف عامل: {str(e)}')
    
    def show_routes_tab(self):
        layout = BoxLayout(orientation='vertical')
        
        tabs = BoxLayout(size_hint_y=0.08, spacing=2)
        btn_manual = Button(text=f('مدیریت دستی'), background_color=(0.3, 0.5, 0.8, 1))
        btn_excel = Button(text=f('ورود از اکسل'), background_color=(0.3, 0.5, 0.8, 0.6))
        
        btn_manual.bind(on_press=lambda x: self.show_manual_routes())
        btn_excel.bind(on_press=lambda x: self.show_excel_routes())
        
        tabs.add_widget(btn_manual)
        tabs.add_widget(btn_excel)
        layout.add_widget(tabs)
        
        self.routes_content = BoxLayout(orientation='vertical')
        layout.add_widget(self.routes_content)
        
        self.show_manual_routes()
        self.content_area.add_widget(layout)
    
    def show_manual_routes(self):
        try:
            self.routes_content.clear_widgets()
            
            content = GridLayout(cols=1, spacing=10, size_hint_y=None, padding=10)
            content.bind(minimum_height=content.setter('height'))
            
            content.add_widget(Label(text=f('➕ افزودن مسیر جدید'), size_hint_y=None, height=40, font_size='16sp', bold=True))
            
            self.route_name_input = RTLTextInput(hint_text='نام مسیر', multiline=False, size_hint_y=None, height=45)
            content.add_widget(self.route_name_input)
            
            add_btn = Button(text=f('افزودن'), size_hint_y=None, height=45, background_color=(0.2, 0.7, 0.2, 1))
            add_btn.bind(on_press=self.add_route_manual)
            content.add_widget(add_btn)
            
            content.add_widget(Label(text=f('🗺️ لیست مسیرها'), size_hint_y=None, height=40, font_size='16sp', bold=True))
            
            self.routes_list = GridLayout(cols=1, spacing=5, size_hint_y=None)
            self.routes_list.bind(minimum_height=self.routes_list.setter('height'))
            content.add_widget(self.routes_list)
            
            scroll = ScrollView()
            scroll.add_widget(content)
            self.routes_content.add_widget(scroll)
            
            self.refresh_routes_list()
        except Exception as e:
            show_message('خطا', f'خطا در نمایش مسیرها: {str(e)}')
    
    def refresh_routes_list(self):
        self.routes_list.clear_widgets()
        routes = get_routes()
        for route in routes:
            box = BoxLayout(size_hint_y=None, height=50, spacing=5)
            box.add_widget(Label(text=f(route.get('name', '')), size_hint_x=0.7))
            del_btn = Button(text=f('حذف'), size_hint_x=0.3, background_color=(0.8, 0.2, 0.2, 1))
            del_btn.bind(on_press=lambda x, r=route: self.delete_route_and_refresh(r.get('id')))
            box.add_widget(del_btn)
            self.routes_list.add_widget(box)
    
    def add_route_manual(self, instance):
        try:
            if self.route_name_input.text:
                add_route({'name': self.route_name_input.text})
                self.route_name_input.text = ''
                self.refresh_routes_list()
                show_message('موفق', 'مسیر با موفقیت اضافه شد')
        except Exception as e:
            show_message('خطا', f'خطا در افزودن مسیر: {str(e)}')
    
    def delete_route_and_refresh(self, route_id):
        try:
            delete_route(route_id)
            self.refresh_routes_list()
            show_message('موفق', 'مسیر با موفقیت حذف شد')
        except Exception as e:
            show_message('خطا', f'خطا در حذف مسیر: {str(e)}')
    
    def show_excel_routes(self):
        self.routes_content.clear_widgets()
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        layout.add_widget(Label(text=f('📎 ورود مسیرها از فایل Excel'), font_size='18sp', bold=True, size_hint_y=0.08))
        
        info = Label(text=f('فرمت فایل اکسل: ستون اول نام مسیر'), size_hint_y=None, height=40)
        layout.add_widget(info)
        
        self.routes_file_picker = FilePicker(size_hint_y=None, height=100)
        layout.add_widget(self.routes_file_picker)
        
        import_btn = Button(text=f('ورود به سیستم'), size_hint_y=0.1, background_color=(0.2, 0.7, 0.2, 1))
        import_btn.bind(on_press=self.import_routes_from_excel)
        layout.add_widget(import_btn)
        
        self.routes_content.add_widget(layout)
    
    def import_routes_from_excel(self, instance):
        try:
            filepath = self.routes_file_picker.get_file()
            if not filepath:
                show_message('خطا', 'لطفاً ابتدا فایل را انتخاب کنید')
                return
            
            success, message = import_routes_from_excel(filepath)
            show_message('موفق' if success else 'خطا', message)
            
            if success:
                self.show_manual_routes()
        except Exception as e:
            show_message('خطا', f'خطا در وارد کردن مسیرها: {str(e)}')
    
    def show_customers_tab(self):
        layout = BoxLayout(orientation='vertical')
        
        tabs = BoxLayout(size_hint_y=0.08, spacing=2)
        btn_manual = Button(text=f('مدیریت دستی'), background_color=(0.3, 0.5, 0.8, 1))
        btn_excel = Button(text=f('ورود از اکسل'), background_color=(0.3, 0.5, 0.8, 0.6))
        
        btn_manual.bind(on_press=lambda x: self.show_manual_customers())
        btn_excel.bind(on_press=lambda x: self.show_excel_customers())
        
        tabs.add_widget(btn_manual)
        tabs.add_widget(btn_excel)
        layout.add_widget(tabs)
        
        self.customers_content = BoxLayout(orientation='vertical')
        layout.add_widget(self.customers_content)
        
        self.show_manual_customers()
        self.content_area.add_widget(layout)
    
    def show_manual_customers(self):
        try:
            self.customers_content.clear_widgets()
            
            content = GridLayout(cols=1, spacing=10, size_hint_y=None, padding=10)
            content.bind(minimum_height=content.setter('height'))
            
            content.add_widget(Label(text=f('➕ افزودن مشتری جدید'), size_hint_y=None, height=40, font_size='16sp', bold=True))
            
            content.add_widget(Label(text=f('انتخاب مسیر:'), size_hint_y=None, height=30))
            routes = get_routes()
            route_names = [r.get('name', '') for r in routes] if routes else ['']
            self.customer_route_spinner = RTLSpinner(text=route_names[0] if route_names else '', values=route_names, size_hint_y=None, height=45)
            content.add_widget(self.customer_route_spinner)
            
            self.customer_name_input = RTLTextInput(hint_text='نام مشتری', multiline=False, size_hint_y=None, height=45)
            content.add_widget(self.customer_name_input)
            
            self.customer_store_input = RTLTextInput(hint_text='نام فروشگاه', multiline=False, size_hint_y=None, height=45)
            content.add_widget(self.customer_store_input)
            
            self.customer_mobile_input = RTLTextInput(hint_text='موبایل', multiline=False, size_hint_y=None, height=45)
            content.add_widget(self.customer_mobile_input)
            
            self.customer_address_input = RTLTextInput(hint_text='آدرس', multiline=False, size_hint_y=None, height=45)
            content.add_widget(self.customer_address_input)
            
            add_btn = Button(text=f('افزودن مشتری'), size_hint_y=None, height=45, background_color=(0.2, 0.7, 0.2, 1))
            add_btn.bind(on_press=self.add_customer_manual)
            content.add_widget(add_btn)
            
            content.add_widget(Label(text=f('📞 لیست مشتریان'), size_hint_y=None, height=40, font_size='16sp', bold=True))
            
            self.customers_list = GridLayout(cols=1, spacing=5, size_hint_y=None)
            self.customers_list.bind(minimum_height=self.customers_list.setter('height'))
            content.add_widget(self.customers_list)
            
            filter_btn = Button(text=f('نمایش مشتریان این مسیر'), size_hint_y=None, height=40, background_color=(0.4, 0.5, 0.6, 1))
            filter_btn.bind(on_press=self.refresh_customers_list)
            content.add_widget(filter_btn)
            
            scroll = ScrollView()
            scroll.add_widget(content)
            self.customers_content.add_widget(scroll)
            
            self.refresh_customers_list()
        except Exception as e:
            show_message('خطا', f'خطا در نمایش مشتریان: {str(e)}')
    
    def refresh_customers_list(self, instance=None):
        try:
            self.customers_list.clear_widgets()
            
            selected_route = self.customer_route_spinner.text
            all_customers = get_customers()
            
            filtered = [c for c in all_customers if c.get('route_name') == selected_route]
            
            if not filtered:
                self.customers_list.add_widget(Label(text=f('هیچ مشتری در این مسیر وجود ندارد'), size_hint_y=None, height=40))
                return
            
            for customer in filtered:
                box = BoxLayout(size_hint_y=None, height=60, spacing=5)
                info = f"{customer.get('name', '')}\n{customer.get('store_name', '')}\n{customer.get('mobile', '')}"
                box.add_widget(Label(text=f(info), size_hint_x=0.7))
                del_btn = Button(text=f('حذف'), size_hint_x=0.3, background_color=(0.8, 0.2, 0.2, 1))
                del_btn.bind(on_press=lambda x, c=customer: self.delete_customer_and_refresh(c.get('id')))
                box.add_widget(del_btn)
                self.customers_list.add_widget(box)
        except Exception as e:
            show_message('خطا', f'خطا در نمایش مشتریان: {str(e)}')
    
    def add_customer_manual(self, instance):
        try:
            route_name = self.customer_route_spinner.text
            name = self.customer_name_input.text
            store = self.customer_store_input.text
            mobile = self.customer_mobile_input.text
            address = self.customer_address_input.text
            
            if not route_name:
                show_message('خطا', 'لطفاً ابتدا مسیر را انتخاب کنید')
                return
            
            if not name:
                show_message('خطا', 'نام مشتری الزامی است')
                return
            
            customer = {
                'name': name,
                'store_name': store,
                'route_name': route_name,
                'mobile': mobile,
                'address': address
            }
            add_customer(customer)
            
            self.customer_name_input.text = ''
            self.customer_store_input.text = ''
            self.customer_mobile_input.text = ''
            self.customer_address_input.text = ''
            
            self.refresh_customers_list()
            show_message('موفق', 'مشتری با موفقیت اضافه شد')
        except Exception as e:
            show_message('خطا', f'خطا در افزودن مشتری: {str(e)}')
    
    def delete_customer_and_refresh(self, customer_id):
        try:
            delete_customer(customer_id)
            self.refresh_customers_list()
            show_message('موفق', 'مشتری با موفقیت حذف شد')
        except Exception as e:
            show_message('خطا', f'خطا در حذف مشتری: {str(e)}')
    
    def show_excel_customers(self):
        self.customers_content.clear_widgets()
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        layout.add_widget(Label(text=f('📎 ورود مشتریان از فایل Excel'), font_size='18sp', bold=True, size_hint_y=0.08))
        
        info = Label(text=f('فرمت فایل اکسل: name, store_name, route_name, mobile, address'), size_hint_y=None, height=40)
        layout.add_widget(info)
        
        self.customers_file_picker = FilePicker(size_hint_y=None, height=100)
        layout.add_widget(self.customers_file_picker)
        
        import_btn = Button(text=f('ورود به سیستم'), size_hint_y=0.1, background_color=(0.2, 0.7, 0.2, 1))
        import_btn.bind(on_press=self.import_customers_from_excel)
        layout.add_widget(import_btn)
        
        self.customers_content.add_widget(layout)
    
    def import_customers_from_excel(self, instance):
        try:
            filepath = self.customers_file_picker.get_file()
            if not filepath:
                show_message('خطا', 'لطفاً ابتدا فایل را انتخاب کنید')
                return
            
            success, message = import_customers_from_excel(filepath)
            show_message('موفق' if success else 'خطا', message)
            
            if success:
                self.show_manual_customers()
        except Exception as e:
            show_message('خطا', f'خطا در وارد کردن مشتریان: {str(e)}')
    
    def show_settings_tab(self):
        try:
            settings = get_settings()
            routes = get_routes()
            customers = get_customers()
            
            route_names = [r.get('name', '') for r in routes] if routes else ['']
            customer_names = [c.get('name', '') for c in customers] if customers else ['']
            
            layout = ScrollView()
            content = GridLayout(cols=2, spacing=10, size_hint_y=None, padding=10)
            content.bind(minimum_height=content.setter('height'))
            
            fields = [
                ('supervision_rate', f('درصد سرکشی به مشتری'), '0.3', 'float'),
                ('conversion_rate', f('نرخ تبدیل سرکشی به فاکتور'), '0.25', 'float'),
                ('avg_invoice_amount', f('میانگین مبلغ فاکتور استاندارد'), '1000000', 'int'),
                ('target_amount', f('مبلغ تارگت ریالی'), '50000000', 'int'),
                ('target_count', f('میزان تارگت تعدادی'), '100', 'int'),
                ('target_invoice_count', f('میزان تارگت تعداد فاکتور'), '20', 'int'),
                ('target_customer_count', f('میزان تارگت تعداد مشتری'), '50', 'int'),
                ('target_new_customer_count', f('میزان تارگت مشتری جدید'), '10', 'int'),
                ('target_cash_sales', f('تارگت فروش و وصول نقدی'), '30000000', 'int'),
                ('target_credit_sales', f('تارگت فروش و وصول غیر نقدی'), '20000000', 'int'),
                ('first_customer_of_route', f('اولین مشتری مسیر روز'), settings.get('first_customer_of_route', ''), 'spinner_customer', customer_names),
                ('work_start_time', f('ساعت شروع به کار'), '08:00', 'time'),
                ('first_visit_time', f('ساعت اولین ویزیت'), '09:00', 'time'),
                ('min_daily_hours', f('حداقل ساعت کاری روزانه'), '6', 'int'),
            ]
            
            inputs = {}
            for item in fields:
                key = item[0]
                label = item[1]
                default = item[2]
                field_type = item[3]
                
                content.add_widget(Label(text=label + ':', size_hint_y=None, height=45))
                
                if field_type == 'float':
                    value = settings.get(key, default)
                    input_field = RTLTextInput(text=str(value), multiline=False, size_hint_y=None, height=45, input_filter='float')
                elif field_type == 'int':
                    value = settings.get(key, default)
                    input_field = RTLTextInput(text=str(value), multiline=False, size_hint_y=None, height=45, input_filter='int')
                elif field_type == 'time':
                    value = settings.get(key, default)
                    input_field = RTLTextInput(text=value, multiline=False, size_hint_y=None, height=45, hint_text='HH:MM')
                elif field_type == 'spinner_customer':
                    values = item[4] if len(item) > 4 else ['']
                    value = settings.get(key, default)
                    input_field = RTLSpinner(text=value if value else (values[0] if values else ''), 
                                            values=values, size_hint_y=None, height=45)
                else:
                    value = settings.get(key, default)
                    input_field = RTLTextInput(text=str(value), multiline=False, size_hint_y=None, height=45)
                
                content.add_widget(input_field)
                inputs[key] = input_field
            
            content.add_widget(Label(size_hint_y=None, height=10))
            
            save_btn = Button(text=f('ذخیره تنظیمات'), size_hint_y=None, height=50, background_color=(0.2, 0.6, 1, 1), size_hint_x=0.5)
            save_btn.bind(on_press=lambda x: self.save_settings(inputs))
            content.add_widget(save_btn)
            
            layout.add_widget(content)
            self.content_area.add_widget(layout)
        except Exception as e:
            show_message('خطا', f'خطا در نمایش تنظیمات: {str(e)}')
    
    def save_settings(self, inputs):
        try:
            settings = {}
            for key, input_field in inputs.items():
                value = input_field.text
                
                if key in ['supervision_rate', 'conversion_rate']:
                    try:
                        value = float(value)
                    except:
                        value = 0.0
                elif key in ['avg_invoice_amount', 'target_amount', 'target_count', 'target_invoice_count', 
                            'target_customer_count', 'target_new_customer_count', 'target_cash_sales', 
                            'target_credit_sales', 'min_daily_hours']:
                    try:
                        value = int(value)
                    except:
                        value = 0
                elif key in ['work_start_time', 'first_visit_time', 'first_customer_of_route']:
                    pass
                
                settings[key] = value
            
            update_settings(settings)
            show_message('موفق', 'تنظیمات با موفقیت ذخیره شد')
        except Exception as e:
            show_message('خطا', f'خطا در ذخیره تنظیمات: {str(e)}')
    
    def logout(self, instance):
        self.manager.current = 'login'


class UserScreen(Screen):
    """صفحه ثبت ویزیت روزانه"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings = get_settings()
        self.build_ui()
    
    def build_ui(self):
        layout = BoxLayout(orientation='vertical')
        
        header = Label(text=f('ثبت ویزیت روزانه'), size_hint_y=0.07, font_size='20sp')
        layout.add_widget(header)
        
        self.form_layout = GridLayout(cols=3, spacing=8, size_hint_y=None, padding=10)
        self.form_layout.bind(minimum_height=self.form_layout.setter('height'))
        
        routes = get_routes()
        self.route_names = [r.get('name', '') for r in routes] if routes else ['']
        
        customers = get_customers()
        self.all_customer_names = [c.get('name', '') for c in customers] if customers else ['']
        
        self.form_layout.add_widget(Label(text=f('آیتم'), size_hint_y=None, height=35, bold=True, color=(0.2, 0.5, 0.8, 1)))
        self.form_layout.add_widget(Label(text=f('مقدار'), size_hint_y=None, height=35, bold=True, color=(0.2, 0.5, 0.8, 1)))
        self.form_layout.add_widget(Label(text=f('هدف'), size_hint_y=None, height=35, bold=True, color=(0.2, 0.5, 0.8, 1)))
        
        self.inputs = {}
        
        self.form_layout.add_widget(Label(text=f('تاریخ ویزیت'), size_hint_y=None, height=40))
        visit_date = RTLTextInput(text=get_today_jalali(), multiline=False, size_hint_y=None, height=40)
        self.form_layout.add_widget(visit_date)
        self.form_layout.add_widget(Label(text='---', size_hint_y=None, height=40, color=(0.5, 0.5, 0.5, 1)))
        self.inputs['visit_date'] = visit_date
        
        self.form_layout.add_widget(Label(text=f('مسیر ویزیت'), size_hint_y=None, height=40))
        self.route_spinner = RTLSpinner(text=self.route_names[0] if self.route_names else '', values=self.route_names, size_hint_y=None, height=40)
        self.route_spinner.bind(text=self.on_route_change)
        self.form_layout.add_widget(self.route_spinner)
        self.route_customers_target = Label(text='0', size_hint_y=None, height=40, color=(0.6, 0.4, 0.2, 1))
        self.form_layout.add_widget(self.route_customers_target)
        self.inputs['route_name'] = self.route_spinner
        
        self.form_layout.add_widget(Label(text=f('ساعت شروع کار'), size_hint_y=None, height=40))
        clock_in = RTLTextInput(text=get_current_time(), multiline=False, size_hint_y=None, height=40)
        self.form_layout.add_widget(clock_in)
        self.form_layout.add_widget(Label(text=f(self.settings.get('work_start_time', '08:00')), size_hint_y=None, height=40, color=(0.6, 0.4, 0.2, 1)))
        self.inputs['clock_in'] = clock_in
        
        self.form_layout.add_widget(Label(text=f('ساعت اولین ویزیت'), size_hint_y=None, height=40))
        first_visit_time = RTLTextInput(text='', multiline=False, size_hint_y=None, height=40)
        self.form_layout.add_widget(first_visit_time)
        self.form_layout.add_widget(Label(text=f(self.settings.get('first_visit_time', '09:00')), size_hint_y=None, height=40, color=(0.6, 0.4, 0.2, 1)))
        self.inputs['first_visit_time'] = first_visit_time
        
        self.form_layout.add_widget(Label(text=f('اولین مشتری'), size_hint_y=None, height=40))
        self.first_customer_spinner = RTLSpinner(text='', values=self.all_customer_names, size_hint_y=None, height=40)
        self.form_layout.add_widget(self.first_customer_spinner)
        self.first_customer_target = Label(text=f(self.settings.get('first_customer_of_route', 'تعیین نشده')), size_hint_y=None, height=40, color=(0.6, 0.4, 0.2, 1))
        self.form_layout.add_widget(self.first_customer_target)
        self.inputs['first_customer'] = self.first_customer_spinner
        
        self.form_layout.add_widget(Label(text=f('تعداد مشتری ویزیت شده'), size_hint_y=None, height=40))
        visited_count = RTLTextInput(text='0', multiline=False, size_hint_y=None, height=40, input_filter='int')
        self.form_layout.add_widget(visited_count)
        self.visited_customers_target = Label(text='0', size_hint_y=None, height=40, color=(0.6, 0.4, 0.2, 1))
        self.form_layout.add_widget(self.visited_customers_target)
        self.inputs['visited_customers_count'] = visited_count
        
        self.form_layout.add_widget(Label(text=f('تعداد فاکتور موفق'), size_hint_y=None, height=40))
        invoices_count = RTLTextInput(text='0', multiline=False, size_hint_y=None, height=40, input_filter='int')
        self.form_layout.add_widget(invoices_count)
        self.form_layout.add_widget(Label(text=f(str(self.settings.get('target_invoice_count', '20'))), size_hint_y=None, height=40, color=(0.6, 0.4, 0.2, 1)))
        self.inputs['successful_invoices_count'] = invoices_count
        
        self.form_layout.add_widget(Label(text=f('تعداد واحد فروش موفق'), size_hint_y=None, height=40))
        units_count = RTLTextInput(text='0', multiline=False, size_hint_y=None, height=40, input_filter='int')
        self.form_layout.add_widget(units_count)
        self.form_layout.add_widget(Label(text=f(str(self.settings.get('target_count', '100'))), size_hint_y=None, height=40, color=(0.6, 0.4, 0.2, 1)))
        self.inputs['successful_units_count'] = units_count
        
        self.form_layout.add_widget(Label(text=f('مبلغ فروش موفق'), size_hint_y=None, height=40))
        sales_amount = RTLTextInput(text='0', multiline=False, size_hint_y=None, height=40, input_filter='int')
        self.form_layout.add_widget(sales_amount)
        target_amount = self.settings.get('target_amount', 50000000)
        try:
            target_amount = int(target_amount)
        except:
            target_amount = 0
        self.form_layout.add_widget(Label(text=f("{:,}".format(target_amount)), size_hint_y=None, height=40, color=(0.6, 0.4, 0.2, 1)))
        self.inputs['successful_sales_amount'] = sales_amount
        
        self.form_layout.add_widget(Label(text=f('ساعت آخرین ویزیت'), size_hint_y=None, height=40))
        last_visit_time = RTLTextInput(text='', multiline=False, size_hint_y=None, height=40)
        self.form_layout.add_widget(last_visit_time)
        self.form_layout.add_widget(Label(text='---', size_hint_y=None, height=40, color=(0.5, 0.5, 0.5, 1)))
        self.inputs['last_visit_time'] = last_visit_time
        
        self.form_layout.add_widget(Label(text=f('ساعت پایان کار'), size_hint_y=None, height=40))
        clock_out = RTLTextInput(text='', multiline=False, size_hint_y=None, height=40)
        self.form_layout.add_widget(clock_out)
        self.form_layout.add_widget(Label(text='---', size_hint_y=None, height=40, color=(0.5, 0.5, 0.5, 1)))
        self.inputs['clock_out'] = clock_out
        
        form_scroll = ScrollView()
        form_scroll.add_widget(self.form_layout)
        layout.add_widget(form_scroll)
        
        btn_layout = BoxLayout(size_hint_y=0.09, spacing=10, padding=10)
        
        save_btn = Button(text=f('💾 ذخیره'), background_color=(0.2, 0.7, 0.2, 1))
        save_btn.bind(on_press=self.save_log)
        btn_layout.add_widget(save_btn)
        
        report_btn = Button(text=f('📊 گزارش'), background_color=(0.2, 0.6, 1, 1))
        report_btn.bind(on_press=self.go_to_report)
        btn_layout.add_widget(report_btn)
        
        logout_btn = Button(text=f('🚪 خروج'), background_color=(0.8, 0.2, 0.2, 1))
        logout_btn.bind(on_press=self.logout)
        btn_layout.add_widget(logout_btn)
        
        layout.add_widget(btn_layout)
        self.add_widget(layout)
        
        self.update_route_info()
    
    def update_route_info(self):
        try:
            current_route = self.route_spinner.text
            
            if current_route:
                customers = get_customers()
                total_customers = len([c for c in customers if c.get('route_name') == current_route])
                self.route_customers_target.text = str(total_customers)
                
                supervision_rate = self.settings.get('supervision_rate', 0.3)
                target_visits = int(total_customers * supervision_rate)
                self.visited_customers_target.text = str(target_visits)
                
                first_customer_target = self.settings.get('first_customer_of_route', 'تعیین نشده')
                self.first_customer_target.text = f(first_customer_target)
                
                filtered_customers = [c.get('name', '') for c in customers if c.get('route_name') == current_route]
                self.first_customer_spinner.values = filtered_customers if filtered_customers else ['']
                if filtered_customers:
                    self.first_customer_spinner.text = filtered_customers[0]
            else:
                self.route_customers_target.text = '0'
                self.visited_customers_target.text = '0'
                self.first_customer_spinner.values = ['']
                self.first_customer_spinner.text = ''
        except Exception as e:
            print(f"⚠️ خطا در به‌روزرسانی اطلاعات مسیر: {e}")
    
    def on_route_change(self, spinner, text):
        self.update_route_info()
    
    def save_log(self, instance):
        try:
            log_data = {}
            for key, input_field in self.inputs.items():
                log_data[key] = input_field.text
            
            if not log_data['visit_date']:
                show_message('خطا', 'تاریخ ویزیت الزامی است')
                return
            
            for key in ['visited_customers_count', 'successful_invoices_count', 'successful_units_count', 'successful_sales_amount']:
                if key in log_data and (log_data[key] == '' or log_data[key] == '0'):
                    log_data[key] = '0'
            
            all_logs = get_daily_logs()
            
            if log_data['visit_date'] in all_logs:
                content = BoxLayout(orientation='vertical', padding=20, spacing=15)
                content.add_widget(Label(text=f('ویزیتی با این تاریخ قبلاً ثبت شده است. آیا می‌خواهید جایگزین شود؟'), size_hint_y=None, height=60))
                
                btn_layout = BoxLayout(spacing=10, size_hint_y=None, height=50)
                yes_btn = Button(text=f('بله، جایگزین شود'))
                no_btn = Button(text=f('خیر، انصراف'))
                btn_layout.add_widget(yes_btn)
                btn_layout.add_widget(no_btn)
                content.add_widget(btn_layout)
                
                popup = Popup(title=f('توجه'), content=content, size_hint=(0.85, 0.35))
                
                def replace(instance):
                    save_daily_log(log_data['visit_date'], log_data)
                    popup.dismiss()
                    show_message('موفق', 'اطلاعات ویزیت با موفقیت جایگزین شد')
                    self.clear_form()
                
                def cancel(instance):
                    popup.dismiss()
                
                yes_btn.bind(on_press=replace)
                no_btn.bind(on_press=cancel)
                popup.open()
            else:
                save_daily_log(log_data['visit_date'], log_data)
                show_message('موفق', 'اطلاعات ویزیت با موفقیت ذخیره شد')
                self.clear_form()
        except Exception as e:
            show_message('خطا', f'خطا در ذخیره اطلاعات: {str(e)}')
    
    def clear_form(self):
        for key in ['first_visit_time', 'last_visit_time', 'clock_out']:
            if key in self.inputs:
                self.inputs[key].text = ''
        
        for key in ['visited_customers_count', 'successful_invoices_count', 'successful_units_count', 'successful_sales_amount']:
            if key in self.inputs:
                self.inputs[key].text = '0'
    
    def go_to_report(self, instance):
        self.manager.current = 'report'
    
    def logout(self, instance):
        self.manager.current = 'login'


class ReportScreen(Screen):
    """صفحه گزارشات"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()
    
    def build_ui(self):
        layout = BoxLayout(orientation='vertical')
        
        header = Label(text=f('📊 گزارش عملکرد'), size_hint_y=0.07, font_size='20sp')
        layout.add_widget(header)
        
        stats_scroll = ScrollView(size_hint_y=0.5)
        self.stats_layout = GridLayout(cols=1, spacing=8, size_hint_y=None, padding=15)
        self.stats_layout.bind(minimum_height=self.stats_layout.setter('height'))
        stats_scroll.add_widget(self.stats_layout)
        layout.add_widget(stats_scroll)
        
        btn_layout = BoxLayout(size_hint_y=0.12, spacing=10, padding=10)
        
        refresh_btn = Button(text=f('🔄 تازه سازی'), background_color=(0.4, 0.4, 0.8, 1))
        refresh_btn.bind(on_press=self.refresh_stats)
        btn_layout.add_widget(refresh_btn)
        
        excel_btn = Button(text=f('📎 خروجی Excel'), background_color=(0.2, 0.6, 0.2, 1))
        excel_btn.bind(on_press=self.export_excel)
        btn_layout.add_widget(excel_btn)
        
        pdf_btn = Button(text=f('📄 خروجی PDF'), background_color=(0.8, 0.2, 0.2, 1))
        pdf_btn.bind(on_press=self.export_pdf)
        btn_layout.add_widget(pdf_btn)
        
        back_btn = Button(text=f('🔙 بازگشت'), background_color=(0.5, 0.5, 0.5, 1))
        back_btn.bind(on_press=self.go_back)
        btn_layout.add_widget(back_btn)
        
        layout.add_widget(btn_layout)
        self.add_widget(layout)
        
        self.refresh_stats(None)
    
    def refresh_stats(self, instance):
        try:
            self.stats_layout.clear_widgets()
            
            logs = get_daily_logs()
            
            if not logs:
                self.stats_layout.add_widget(Label(text=f('📭 هیچ داده‌ای وجود ندارد'), size_hint_y=None, height=50, font_size='16sp'))
                return
            
            total_sales = 0
            total_invoices = 0
            total_visits = 0
            total_units = 0
            
            for date, log in logs.items():
                try:
                    sales_val = log.get('successful_sales_amount', '0')
                    total_sales += int(sales_val) if str(sales_val).isdigit() else 0
                    total_invoices += int(log.get('successful_invoices_count', '0')) if str(log.get('successful_invoices_count', '0')).isdigit() else 0
                    total_visits += int(log.get('visited_customers_count', '0')) if str(log.get('visited_customers_count', '0')).isdigit() else 0
                    total_units += int(log.get('successful_units_count', '0')) if str(log.get('successful_units_count', '0')).isdigit() else 0
                except:
                    pass
            
            self.stats_layout.add_widget(Label(text=f('📊 خلاصه آمار کل'), size_hint_y=None, height=45, font_size='18sp', bold=True))
            
            stats_row1 = BoxLayout(size_hint_y=None, height=60, spacing=10)
            card1 = self.make_stat_card(f('💰 کل فروش'), f"{total_sales:,}", 'Rial', (0.2, 0.6, 0.2, 1))
            card2 = self.make_stat_card(f('🧾 فاکتورها'), str(total_invoices), '', (0.2, 0.5, 0.8, 1))
            stats_row1.add_widget(card1)
            stats_row1.add_widget(card2)
            self.stats_layout.add_widget(stats_row1)
            
            stats_row2 = BoxLayout(size_hint_y=None, height=60, spacing=10)
            card3 = self.make_stat_card(f('👥 ویزیت‌ها'), str(total_visits), '', (0.8, 0.5, 0.2, 1))
            card4 = self.make_stat_card(f('📦 واحد فروش'), str(total_units), '', (0.6, 0.3, 0.7, 1))
            stats_row2.add_widget(card3)
            stats_row2.add_widget(card4)
            self.stats_layout.add_widget(stats_row2)
            
            stats_row3 = BoxLayout(size_hint_y=None, height=60, spacing=10)
            card5 = self.make_stat_card(f('📅 روزهای کاری'), str(len(logs)), '', (0.3, 0.6, 0.6, 1))
            avg_sale = total_sales // total_invoices if total_invoices > 0 else 0
            card6 = self.make_stat_card(f('📈 میانگین فاکتور'), f"{avg_sale:,}", 'Rial', (0.7, 0.4, 0.4, 1))
            stats_row3.add_widget(card5)
            stats_row3.add_widget(card6)
            self.stats_layout.add_widget(stats_row3)
            
            if total_visits > 0:
                avg_per_visit = total_sales // total_visits
                stats_row4 = BoxLayout(size_hint_y=None, height=60, spacing=10)
                card7 = self.make_stat_card(f('🎯 فروش هر ویزیت'), f"{avg_per_visit:,}", 'Rial', (0.4, 0.5, 0.3, 1))
                stats_row4.add_widget(card7)
                self.stats_layout.add_widget(stats_row4)
            
            self.stats_layout.add_widget(Label(text=f(''), size_hint_y=None, height=10))
            self.stats_layout.add_widget(Label(text=f('📋 لیست ویزیت‌های ثبت شده'), size_hint_y=None, height=40, font_size='16sp', bold=True))
            
            header_box = BoxLayout(size_hint_y=None, height=40, spacing=2)
            header_date = Button(text=f('تاریخ'), size_hint_x=0.25, background_color=(0.2, 0.5, 0.8, 1), color=(1, 1, 1, 1))
            header_visit = Button(text=f('ویزیت'), size_hint_x=0.25, background_color=(0.2, 0.5, 0.8, 1), color=(1, 1, 1, 1))
            header_invoice = Button(text=f('فاکتور'), size_hint_x=0.25, background_color=(0.2, 0.5, 0.8, 1), color=(1, 1, 1, 1))
            header_sales = Button(text=f('فروش (ریال)'), size_hint_x=0.25, background_color=(0.2, 0.5, 0.8, 1), color=(1, 1, 1, 1))
            header_box.add_widget(header_date)
            header_box.add_widget(header_visit)
            header_box.add_widget(header_invoice)
            header_box.add_widget(header_sales)
            self.stats_layout.add_widget(header_box)
            
            sorted_logs = sorted(logs.items(), key=lambda x: x[0], reverse=True)
            
            for idx, (date, log) in enumerate(sorted_logs):
                row_box = BoxLayout(size_hint_y=None, height=35, spacing=2)
                row_box.add_widget(Label(text=date, size_hint_x=0.25))
                row_box.add_widget(Label(text=log.get('visited_customers_count', '0'), size_hint_x=0.25))
                row_box.add_widget(Label(text=log.get('successful_invoices_count', '0'), size_hint_x=0.25))
                
                sales = log.get('successful_sales_amount', '0')
                sales_num = int(sales) if str(sales).isdigit() else 0
                row_box.add_widget(Label(text=f"{sales_num:,}", size_hint_x=0.25))
                
                self.stats_layout.add_widget(row_box)
        except Exception as e:
            show_message('خطا', f'خطا در نمایش گزارش: {str(e)}')
    
    def make_stat_card(self, title, value, unit, color):
        card = BoxLayout(orientation='vertical', size_hint_x=0.5, size_hint_y=None, height=60, padding=5, spacing=2)
        title_label = Label(text=title, size_hint_y=None, height=20, font_size='12sp')
        value_label = Label(text=f"{value} {unit}", size_hint_y=None, height=30, font_size='18sp', bold=True)
        card.add_widget(title_label)
        card.add_widget(value_label)
        
        with card.canvas.before:
            Color(*color)
            self.bg_rect = Rectangle(pos=card.pos, size=card.size)
            card.bind(pos=self.update_bg, size=self.update_bg)
            card.bg_color = color
            card.bg_rect = self.bg_rect
        return card
    
    def update_bg(self, instance, value):
        instance.bg_rect.pos = instance.pos
        instance.bg_rect.size = instance.size
    
    def export_excel(self, instance):
        try:
            filepath = export_to_excel()
            if filepath:
                show_message('موفق', 'فایل Excel ذخیره شد')
            else:
                show_message('خطا', 'هیچ داده‌ای وجود ندارد')
        except Exception as e:
            show_message('خطا', f'خطا در خروجی Excel: {str(e)}')
    
    def export_pdf(self, instance):
        try:
            filepath = export_to_pdf()
            if filepath:
                show_message('موفق', 'فایل PDF ذخیره شد')
            else:
                show_message('خطا', 'هیچ داده‌ای وجود ندارد')
        except Exception as e:
            show_message('خطا', f'خطا در خروجی PDF: {str(e)}')
    
    def go_back(self, instance):
        self.manager.current = 'user'


class ScreenManagement(ScreenManager):
    """مدیریت صفحات"""
    pass


class MainApp(App):
    """کلاس اصلی برنامه"""
    def build(self):
        # مقداردهی اولیه مسیر ذخیره‌سازی
        self.data_path = init_data_path()
        os.makedirs(os.path.join(self.data_path, 'reports'), exist_ok=True)
        
        # ایجاد فایل‌های JSON اولیه
        self.init_json_files()
        
        # ایجاد مدیریت صفحات
        sm = ScreenManagement()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(AdminScreen(name='admin'))
        sm.add_widget(UserScreen(name='user'))
        sm.add_widget(ReportScreen(name='report'))
        sm.add_widget(RegisterScreen(name='register'))
        sm.add_widget(AdminSettingsScreen(name='admin_settings'))
        sm.add_widget(SettingsLoginScreen(name='settings_login'))
        
        # ✅ مدیریت دکمه Back در اندروید
        from kivy.core.window import Window
        Window.bind(on_keyboard=self.on_keyboard)
        
        # ✅ مدیریت بسته شدن پنجره در دسکتاپ
        Window.bind(on_close=self.on_close)
        
        return sm
    
    def on_keyboard(self, window, key, *args):
        """مدیریت دکمه Back در اندروید"""
        if key == 27:  # کلید Back
            current_screen = self.root.current
            
            # اگر در صفحه ورود هستیم، برنامه بسته شود
            if current_screen == 'login':
                self.stop()
                return True
            
            # اگر در صفحات دیگر هستیم، به صفحه قبلی برگردیم
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
            elif current_screen == 'user':
                self.root.current = 'login'
                return True
            elif current_screen == 'report':
                self.root.current = 'user'
                return True
        
        return False
    
    def on_close(self, *args):
        """مدیریت بسته شدن پنجره در دسکتاپ"""
        # ذخیره اطلاعات قبل از بسته شدن (اختیاری)
        print("👋 برنامه در حال بسته شدن...")
        return True  # اجازه بسته شدن بده
    
    def init_json_files(self):
        """ایجاد فایل‌های JSON اولیه در صورت نبودن"""
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
            'admin_password.json': {'hashed_password': ''}
        }
        
        data_path = get_data_path()
        
        for filename, default_content in default_data.items():
            filepath = os.path.join(data_path, filename)
            if not os.path.exists(filepath):
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(default_content, f, ensure_ascii=False, indent=2)
                    print(f"✅ فایل {filename} ایجاد شد")
                except Exception as e:
                    print(f"❌ خطا در ایجاد {filename}: {e}")


if __name__ == '__main__':
    MainApp().run()