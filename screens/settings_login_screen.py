# screens/settings_login_screen.py
# ========== صفحه ورود به تنظیمات مدیریت ==========

import traceback
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.graphics import Color, Rectangle

from utils.rtl_widgets import RTLTextInput, PersianButton, RTLLabel
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
            self.build_ui()
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت SettingsLoginScreen: {e}", error_details)
            raise
    
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def build_ui(self):
        try:
            layout = BoxLayout(orientation='vertical', padding=dp(30), spacing=dp(8))
            
            layout.add_widget(Label(size_hint_y=None, height=dp(20)))
            
            title = RTLLabel(
                text='ورود به تنظیمات سیستم',
                font_size=sp(24),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1)
            )
            layout.add_widget(title)
            
            layout.add_widget(Label(size_hint_y=None, height=dp(3)))
            
            self.password_input = RTLTextInput(
                hint_text='رمز عبور مدیر',
                password=True,
                multiline=False,
                size_hint_y=None,
                height=dp(50),
                font_size=sp(36)
            )
            self.password_input.foreground_color = (1, 1, 1, 1)
            self.password_input.background_color = (0.2, 0.2, 0.2, 1)
            self.password_input.hint_text_color = (0.5, 0.5, 0.5, 1)
            layout.add_widget(self.password_input)
            
            layout.add_widget(Label(size_hint_y=None, height=dp(3)))
            
            btn_layout = BoxLayout(
                spacing=dp(5),
                size_hint_y=None,
                height=dp(42)
            )
            
            login_btn = PersianButton(
                text='ورود',
                background_color=(0.2, 0.6, 1, 1),
                size_hint_y=None,
                height=dp(38),
                color=(1, 1, 1, 1)
            )
            login_btn.bind(on_press=self.check_login)
            btn_layout.add_widget(login_btn)
            
            back_btn = PersianButton(
                text='بازگشت',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(38),
                color=(1, 1, 1, 1)
            )
            back_btn.bind(on_press=self.go_back)
            btn_layout.add_widget(back_btn)
            
            layout.add_widget(btn_layout)
            
            self.add_widget(layout)
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت UI SettingsLoginScreen: {e}", error_details)
            raise
    
    def check_login(self, instance):
        try:
            hashed = get_admin_password()
            
            if not hashed:
                from utils.auth import hash_password
                set_admin_password('admin123')
                hashed = get_admin_password()
                self.show_message('توجه', 'رمز پیش‌فرض "admin123" تنظیم شد')
            
            if verify_password(self.password_input.text, hashed):
                self.manager.current = 'admin_settings'
            else:
                self.show_message('خطا', 'رمز عبور اشتباه است')
                self.password_input.text = ''
                
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ورود به تنظیمات: {e}", error_details)
    
    def go_back(self, instance):
        self.manager.current = 'login'
    
    def show_message(self, title, message):
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
            with content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                           size=lambda i, v: setattr(content_rect, 'size', v))
            
            content.add_widget(RTLLabel(
                text=message,
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1)
            ))
            btn = PersianButton(
                text='باشه',
                size_hint_y=None,
                height=dp(40),
                color=(1, 1, 1, 1),
                background_color=(0.2, 0.6, 1, 1)
            )
            content.add_widget(btn)
            popup = Popup(
                title=title,
                content=content,
                size_hint=(0.8, 0.35),
                background_color=(0.08, 0.08, 0.08, 1)
            )
            popup.title_color = (1, 1, 1, 1)
            btn.bind(on_press=popup.dismiss)
            popup.open()
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش پیام: {e}", error_details)