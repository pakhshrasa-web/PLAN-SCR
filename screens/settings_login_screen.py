# screens/settings_login_screen.py
# ========== صفحه ورود به تنظیمات مدیریت با اسکرول دقیق ==========

import traceback
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
from kivy.clock import Clock

from utils.rtl_widgets import RTLTextInput, PersianButton, RTLLabel, PersianPopup
from utils.auth import get_admin_password, set_admin_password, verify_password
from error_handler import ErrorPopup
from constants import ADMIN_EMAIL


class SettingsLoginScreen(Screen):
    def __init__(self, **kwargs):
        try:
            super().__init__(**kwargs)
            # پس‌زمینه تیره
            with self.canvas.before:
                Color(0.08, 0.08, 0.08, 1)
                self.bg_rect = Rectangle(pos=self.pos, size=self.size)
                self.bind(pos=self._update_bg, size=self._update_bg)
            
            # تغییر به resize برای اسکرول دقیق
            Window.softinput_mode = 'resize'
            
            # متغیر برای ذخیره فیلدهای قابل فوکوس
            self.focusable_fields = []
            
            self.build_ui()
            
            # اتصال رویدادهای کیبورد
            Window.bind(on_keyboard=self._on_keyboard)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت SettingsLoginScreen: {e}", error_details)
            raise
    
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def build_ui(self):
        try:
            # ایجاد ScrollView برای اسکرول خودکار
            scroll = ScrollView(
                do_scroll_x=False,
                do_scroll_y=True,
                size_hint=(1, 1),
                scroll_type=['bars', 'content'],
                bar_width=dp(6)
            )
            
            content = BoxLayout(
                orientation='vertical',
                padding=dp(30),
                spacing=dp(8),
                size_hint_y=None
            )
            content.bind(minimum_height=content.setter('height'))
            
            content.add_widget(Label(size_hint_y=None, height=dp(20)))
            
            title = RTLLabel(
                text='ورود به تنظیمات سیستم',
                font_size=sp(24),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1)
            )
            content.add_widget(title)
            
            content.add_widget(Label(size_hint_y=None, height=dp(10)))
            
            self.password_input = RTLTextInput(
                hint_text='رمز عبور مدیر',
                password=True,
                multiline=False,
                size_hint_y=None,
                height=dp(100),
                font_size=sp(32)
            )
            self.password_input.bg_color = (0.15, 0.15, 0.15, 1)
            self.password_input.border_color = (0.3, 0.3, 0.3, 1)
            self.password_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.password_input._hidden_input.foreground_color = (1, 1, 1, 1)
            
            # اتصال رویداد فوکوس
            self.password_input._hidden_input.bind(focus=self._on_field_focus)
            self.focusable_fields.append(self.password_input._hidden_input)
            
            content.add_widget(self.password_input)
            
            content.add_widget(Label(size_hint_y=None, height=dp(10)))
            
            btn_layout = BoxLayout(
                spacing=dp(5),
                size_hint_y=None,
                height=dp(50)
            )
            
            login_btn = PersianButton(
                text='ورود',
                background_color=(0.2, 0.6, 1, 1),
                size_hint_y=None,
                height=dp(46),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            login_btn.bind(on_press=self.check_login)
            btn_layout.add_widget(login_btn)
            
            back_btn = PersianButton(
                text='بازگشت',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(46),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            back_btn.bind(on_press=self.go_back)
            btn_layout.add_widget(back_btn)
            
            content.add_widget(btn_layout)
            
            # اضافه کردن فضای خالی در پایین برای اسکرول
            content.add_widget(Label(size_hint_y=None, height=dp(50)))
            
            scroll.add_widget(content)
            self.add_widget(scroll)
            
            # تنظیم فوکوس روی فیلد رمز عبور
            Clock.schedule_once(lambda dt: self._focus_password(), 0.1)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت UI SettingsLoginScreen: {e}", error_details)
            raise
    
    def _focus_password(self):
        """تنظیم فوکوس روی فیلد رمز عبور"""
        if hasattr(self, 'password_input'):
            self.password_input._hidden_input.focus = True
    
    # ============================================================
    # مدیریت فوکوس و انتخاب خودکار متن
    # ============================================================
    
    def _on_field_focus(self, instance, value):
        """وقتی فیلد فوکوس میشه یا فوکوس رو از دست میده"""
        if value:
            Clock.schedule_once(lambda dt: self._select_all_text(instance), 0.1)
            Clock.schedule_once(lambda dt: self._scroll_to_field(instance), 0.3)
    
    def _select_all_text(self, instance):
        """انتخاب کل متن فیلد"""
        if instance and hasattr(instance, 'select_all'):
            instance.select_all()
    
    def _scroll_to_field(self, instance):
        """اسکرول دقیق به موقعیت فیلد بالای کیبورد"""
        try:
            # پیدا کردن ScrollView
            scroll = None
            for child in self.children:
                if isinstance(child, ScrollView):
                    scroll = child
                    break
            
            if not scroll:
                return
            
            # موقعیت فیلد در پنجره
            field_pos = instance.to_window(0, 0)
            field_y = field_pos[1]
            
            # ارتفاع کیبورد (تقریبی)
            keyboard_height = 250
            window_height = Window.height
            
            # موقعیت هدف (بالای کیبورد با فاصله)
            target_y = window_height - keyboard_height - dp(100)
            
            # محاسبه مقدار اسکرول
            content_height = scroll.children[0].height if scroll.children else 1
            scroll_height = scroll.height
            
            if content_height > scroll_height:
                if field_y > target_y:
                    # نسبت موقعیت فیلد به کل محتوا
                    field_ratio = (content_height - field_y) / content_height
                    scroll_value = min(0.95, max(0.05, field_ratio + 0.1))
                    scroll.scroll_y = scroll_value
                    
        except Exception as e:
            print(f"خطا در اسکرول به فیلد: {e}")
    
    # ============================================================
    # مدیریت کلیدهای کیبورد
    # ============================================================
    
    def _on_keyboard(self, window, key, *args):
        """مدیریت کلیدهای کیبورد"""
        if key == 13:  # Enter
            self.check_login(None)
            return True
        return False
    
    # ============================================================
    # توابع اصلی
    # ============================================================
    
    def check_login(self, instance):
        try:
            hashed = get_admin_password()
            
            if not hashed:
                from utils.auth import hash_password
                set_admin_password('admin123')
                hashed = get_admin_password()
                self.show_message('توجه', 'رمز پیش‌فرض "admin123" تنظیم شد')
            
            if verify_password(self.password_input.text, hashed):
                self.password_input.text = ''
                self.manager.current = 'admin_settings'
            else:
                self.show_message('خطا', 'رمز عبور اشتباه است')
                self.password_input.text = ''
                # دوباره فوکوس روی فیلد
                Clock.schedule_once(lambda dt: self._focus_password(), 0.1)
                
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ورود به تنظیمات: {e}", error_details)
    
    def go_back(self, instance):
        self.manager.current = 'login'
    
    def show_message(self, title, message):
        try:
            content = BoxLayout(orientation='vertical', padding=dp(25), spacing=dp(15))
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
            
            popup = PersianPopup(
                title=title,
                content=content,
                size_hint=(0.85, 0.4),
                background_color=(0.08, 0.08, 0.08, 1)
            )
            btn.bind(on_press=popup.dismiss)
            popup.open()
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش پیام: {e}", error_details)