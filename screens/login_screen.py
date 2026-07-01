# screens/login_screen.py
# ========== صفحه ورود با اسکرول دقیق ==========

import traceback
import os
from datetime import datetime
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.textinput import TextInput

from utils.rtl_widgets import RTLTextInput, PersianButton, RTLLabel
from utils.user_manager import login
from utils.storage import get_data_path
from error_handler import ErrorPopup


class LoginScreen(Screen):

    def __init__(self, **kwargs):
        try:
            super().__init__(**kwargs)
            with self.canvas.before:
                Color(0.08, 0.08, 0.08, 1)
                self.bg_rect = Rectangle(pos=self.pos, size=self.size)
                self.bind(pos=self._update_bg, size=self._update_bg)
            
            # ✅ تغییر به resize برای اسکرول دقیق
            Window.softinput_mode = 'resize'
            
            # ✅ متغیر برای ذخیره فیلدهای قابل فوکوس
            self.focusable_fields = []
            
            self.build_ui()
            
            # ✅ اتصال رویدادهای کیبورد
            Window.bind(on_keyboard=self._on_keyboard)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت LoginScreen: {e}", error_details)
            raise
    
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def build_ui(self):
        try:
            main_layout = BoxLayout(orientation='vertical')
            
            # ✅ ScrollView با قابلیت اسکرول دستی
            self.scroll = ScrollView(
                do_scroll_x=False,
                do_scroll_y=True,
                size_hint=(1, 1),
                scroll_type=['bars', 'content'],
                bar_width=dp(8)
            )
            
            content = BoxLayout(
                orientation='vertical',
                padding=dp(20),
                spacing=dp(5),
                size_hint_y=None
            )
            content.bind(minimum_height=content.setter('height'))
            
            # ========== دکمه‌های بالایی ==========
            header_layout = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(5))
            
            settings_btn = PersianButton(
                text='مدیریت',
                size_hint_x=0.2,
                background_color=(1, 0.8, 0.1, 1),
                size_hint_y=None,
                height=dp(40),
                color=(0, 0, 0, 1),
                font_size=sp(14)
            )
            settings_btn.bind(on_press=self.open_settings)
            header_layout.add_widget(settings_btn)
            
            backup_btn = PersianButton(
                text='💾 بکاپ',
                size_hint_x=0.2,
                background_color=(0.2, 0.5, 0.8, 1),
                size_hint_y=None,
                height=dp(40),
                color=(1, 1, 1, 1),
                font_size=sp(14)
            )
            backup_btn.bind(on_press=self.do_backup)
            header_layout.add_widget(backup_btn)
            
            restore_btn = PersianButton(
                text='📂 بازیابی',
                size_hint_x=0.2,
                background_color=(0.8, 0.5, 0.2, 1),
                size_hint_y=None,
                height=dp(40),
                color=(1, 1, 1, 1),
                font_size=sp(14)
            )
            restore_btn.bind(on_press=self.do_restore)
            header_layout.add_widget(restore_btn)
            
            header_layout.add_widget(Label(text='', size_hint_x=0.4))
            content.add_widget(header_layout)
            
            content.add_widget(Label(size_hint_y=None, height=dp(10)))
            
            # ========== عنوان ==========
            title = RTLLabel(
                text='مدیریت فروش',
                font_size=sp(32),
                size_hint_y=None,
                height=dp(60),
                color=(1, 1, 1, 1)
            )
            content.add_widget(title)
            
            content.add_widget(Label(size_hint_y=None, height=dp(10)))
            
            # ========== فیلد نام کاربری ==========
            self.username = RTLTextInput(
                hint_text='نام کاربری',
                size_hint_y=None,
                height=dp(90),
                font_size=sp(36)
            )
            self.username.bg_color = (0.15, 0.15, 0.15, 1)
            self.username.border_color = (0.3, 0.3, 0.3, 1)
            self.username.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.username._hidden_input.foreground_color = (1, 1, 1, 1)
            
            # ✅ اتصال رویداد فوکوس برای انتخاب خودکار متن
            self.username._hidden_input.bind(focus=self._on_field_focus)
            self.focusable_fields.append(self.username._hidden_input)
            
            content.add_widget(self.username)

            content.add_widget(Label(size_hint_y=None, height=dp(5)))

            # ========== فیلد رمز عبور ==========
            self.password = RTLTextInput(
                hint_text='رمز عبور',
                password=True,
                size_hint_y=None,
                height=dp(90),
                font_size=sp(42)
            )
            self.password.bg_color = (0.15, 0.15, 0.15, 1)
            self.password.border_color = (0.3, 0.3, 0.3, 1)
            self.password.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.password._hidden_input.foreground_color = (1, 1, 1, 1)
            
            # ✅ اتصال رویداد فوکوس برای انتخاب خودکار متن
            self.password._hidden_input.bind(focus=self._on_field_focus)
            self.focusable_fields.append(self.password._hidden_input)
            
            content.add_widget(self.password)
            
            # ========== دکمه ورود ==========
            btn = PersianButton(
                text='ورود',
                size_hint_y=None,
                height=dp(50),
                background_color=(0.2, 0.6, 1, 1),
                color=(1, 1, 1, 1)
            )
            btn.bind(on_press=self.check_login)
            content.add_widget(btn)
            
            content.add_widget(Label(size_hint_y=None, height=dp(3)))
            
            # ========== دکمه ثبت نام ==========
            register_btn = PersianButton(
                text='ثبت نام',
                size_hint_y=None,
                height=dp(50),
                background_color=(0.2, 0.7, 0.2, 1),
                color=(1, 1, 1, 1),
                halign='center',
                valign='middle'
            )
            register_btn.bind(on_press=self.open_register)
            content.add_widget(register_btn)
            
            self.scroll.add_widget(content)
            main_layout.add_widget(self.scroll)
            self.add_widget(main_layout)
            
            # ✅ تنظیم اسکرول به بالا
            Clock.schedule_once(self._adjust_scroll, 0.1)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت UI LoginScreen: {e}", error_details)
            raise
    
    def _adjust_scroll(self, dt):
        """تنظیم اسکرول به بالا"""
        if hasattr(self, 'scroll'):
            self.scroll.scroll_y = 1
    
    # ============================================================
    # ✅ مدیریت فوکوس و انتخاب خودکار متن
    # ============================================================
    
    def _on_field_focus(self, instance, value):
        """وقتی فیلد فوکوس میشه یا فوکوس رو از دست میده"""
        if value:
            # ✅ وقتی فیلد فوکوس میشه، کل متن رو انتخاب کن
            Clock.schedule_once(lambda dt: self._select_all_text(instance), 0.1)
            
            # ✅ اسکرول به فیلد با تأخیر برای اطمینان از نمایش کیبورد
            Clock.schedule_once(lambda dt: self._scroll_to_field(instance), 0.3)
    
    def _select_all_text(self, instance):
        """انتخاب کل متن فیلد"""
        if instance and hasattr(instance, 'select_all'):
            instance.select_all()
    
    def _scroll_to_field(self, instance):
        """اسکرول دقیق به موقعیت فیلد بالای کیبورد"""
        try:
            if not hasattr(self, 'scroll'):
                return
            
            # موقعیت فیلد در پنجره
            field_pos = instance.to_window(0, 0)
            field_y = field_pos[1]
            
            # ارتفاع کیبورد (تقریبی)
            keyboard_height = 250
            
            # ارتفاع قابل مشاهده صفحه
            window_height = Window.height
            
            # موقعیت هدف: بالای کیبورد با فاصله
            target_y = window_height - keyboard_height - dp(80)
            
            # محتوای ScrollView
            content_height = self.scroll.children[0].height if self.scroll.children else 1
            scroll_height = self.scroll.height
            
            if content_height > scroll_height:
                # اگر فیلد پایین‌تر از هدف بود، اسکرول کن
                if field_y > target_y:
                    # محاسبه نسبت اسکرول
                    # نسبت موقعیت فیلد به کل محتوا
                    field_ratio = (content_height - field_y) / content_height
                    # تنظیم اسکرول با کمی آفست
                    scroll_value = min(0.95, max(0.05, field_ratio + 0.1))
                    self.scroll.scroll_y = scroll_value
                elif field_y < dp(50):
                    # فیلد خیلی بالاست، اسکرول به پایین
                    self.scroll.scroll_y = 0.9
                else:
                    # فیلد در محدوده قابل قبول است
                    pass
                    
        except Exception as e:
            print(f"⚠️ خطا در اسکرول به فیلد: {e}")
    
    # ============================================================
    # ✅ مدیریت کلیدهای کیبورد
    # ============================================================
    
    def _on_keyboard(self, window, key, *args):
        """مدیریت کلیدهای کیبورد"""
        if key == 9:  # Tab
            self._focus_next()
            return True
        elif key == 13:  # Enter
            self.check_login(None)
            return True
        return False
    
    def _focus_next(self):
        """فوکوس به فیلد بعدی"""
        if not self.focusable_fields:
            return
        for i, field in enumerate(self.focusable_fields):
            if field.focus:
                next_i = (i + 1) % len(self.focusable_fields)
                self.focusable_fields[next_i].focus = True
                break
    
    # ============================================================
    # ✅ توابع بکاپ و بازیابی (بدون تغییر)
    # ============================================================
    
    def do_backup(self, instance):
        """انجام بکاپ از داده‌ها"""
        try:
            data_path = get_data_path()
            backup_dir = os.path.join(data_path, 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(backup_dir, f'backup_{timestamp}.zip')
            
            import zipfile
            
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for filename in os.listdir(data_path):
                    if filename.endswith('.json'):
                        filepath = os.path.join(data_path, filename)
                        zipf.write(filepath, filename)
            
            self.show_message('✅ موفق', f'بکاپ با موفقیت ایجاد شد')
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ایجاد بکاپ: {e}", error_details)
    
    def do_restore(self, instance):
        """بازیابی داده‌ها از بکاپ"""
        try:
            data_path = get_data_path()
            backup_dir = os.path.join(data_path, 'backups')
            
            if not os.path.exists(backup_dir):
                self.show_message('خطا', 'هیچ بکاپی یافت نشد')
                return
            
            backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.zip')]
            backup_files.sort(reverse=True)
            
            if not backup_files:
                self.show_message('خطا', 'هیچ فایل بکاپی یافت نشد')
                return
            
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            with content.canvas.before:
                Color(0.15, 0.15, 0.15, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                           size=lambda i, v: setattr(content_rect, 'size', v))
            
            content.add_widget(RTLLabel(
                text='انتخاب فایل بکاپ برای بازیابی:',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(18),
                color=(1, 1, 1, 1)
            ))
            
            from utils.rtl_widgets import PersianComboBox
            backup_spinner = PersianComboBox(
                text=backup_files[0],
                values=backup_files,
                height=dp(55)
            )
            backup_spinner.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            backup_spinner.main_btn.color = (1, 1, 1, 1)
            backup_spinner.main_btn.font_size = sp(18)
            content.add_widget(backup_spinner)
            
            btn_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(55))
            
            restore_btn = PersianButton(
                text='✅ بازیابی',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                font_size=sp(18),
                color=(1, 1, 1, 1)
            )
            cancel_btn = PersianButton(
                text='❌ انصراف',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                font_size=sp(18),
                color=(1, 1, 1, 1)
            )
            
            btn_layout.add_widget(restore_btn)
            btn_layout.add_widget(cancel_btn)
            content.add_widget(btn_layout)
            
            popup = Popup(
                title='📂 بازیابی اطلاعات',
                content=content,
                size_hint=(0.85, 0.55),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )
            popup.title_color = (1, 1, 1, 1)
            popup.title_size = sp(20)
            
            def do_restore_action(instance):
                selected = backup_spinner.text
                if not selected:
                    self.show_message('خطا', 'لطفاً یک فایل انتخاب کنید')
                    return
                
                popup.dismiss()
                self._perform_restore(selected)
            
            def on_cancel(instance):
                popup.dismiss()
            
            restore_btn.bind(on_press=do_restore_action)
            cancel_btn.bind(on_press=on_cancel)
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در بازیابی: {e}", error_details)
    
    def _perform_restore(self, backup_filename):
        """اجرای واقعی بازیابی"""
        try:
            import zipfile
            data_path = get_data_path()
            backup_path = os.path.join(data_path, 'backups', backup_filename)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            pre_restore_backup = os.path.join(data_path, 'backups', f'pre_restore_{timestamp}.zip')
            
            with zipfile.ZipFile(pre_restore_backup, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for filename in os.listdir(data_path):
                    if filename.endswith('.json'):
                        filepath = os.path.join(data_path, filename)
                        zipf.write(filepath, filename)
            
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(data_path)
            
            self.show_message('✅ موفق', 'داده‌ها با موفقیت بازیابی شدند')
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در اجرای بازیابی: {e}", error_details)
    
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
                self.show_message('خطا', 'نام کاربری یا رمز عبور اشتباه است')
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ورود: {e}", error_details)
    
    def show_message(self, title, message):
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            with content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                           size=lambda i, v: setattr(content_rect, 'size', v))
            
            content.add_widget(RTLLabel(
                text=message,
                size_hint_y=None,
                height=dp(80),
                font_size=sp(20),
                color=(1, 1, 1, 1)
            ))
            btn = PersianButton(
                text='باشه',
                size_hint_y=None,
                height=dp(50),
                font_size=sp(18),
                color=(1, 1, 1, 1),
                background_color=(0.2, 0.6, 1, 1)
            )
            content.add_widget(btn)
            popup = Popup(
                title=title,
                content=content,
                size_hint=(0.85, 0.4),
                background_color=(0.08, 0.08, 0.08, 1)
            )
            popup.title_color = (1, 1, 1, 1)
            popup.title_size = sp(20)
            btn.bind(on_press=popup.dismiss)
            popup.open()
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش پیام: {e}", error_details)