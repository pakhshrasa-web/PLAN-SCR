# screens/login_screen.py
# ========== صفحه ورود ==========

import traceback
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.graphics import Color, Rectangle

from utils.rtl_widgets import RTLTextInput, PersianButton, RTLLabel
from utils.user_manager import login
from error_handler import ErrorPopup


class LoginScreen(Screen):
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
            ErrorPopup.show_error(f"خطا در ساخت LoginScreen: {e}", error_details)
            raise
    
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def build_ui(self):
        try:
            layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(5))
            
            header_layout = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
            settings_btn = PersianButton(
                text='مدیریت',
                size_hint_x=0.2,
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(36),
                color=(1, 1, 1, 1)
            )
            settings_btn.bind(on_press=self.open_settings)
            header_layout.add_widget(settings_btn)
            header_layout.add_widget(Label(text='', size_hint_x=0.8))
            layout.add_widget(header_layout)
            
            layout.add_widget(Label(size_hint_y=None, height=dp(10)))
            
            title = RTLLabel(
                text='مدیریت فروش',
                font_size=sp(32),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1)
            )
            layout.add_widget(title)
            
            layout.add_widget(Label(size_hint_y=None, height=dp(10)))
            
            self.username = RTLTextInput(
                hint_text='نام کاربری',
                size_hint_y=None,
                height=dp(50),
                font_size=sp(36)
            )
            self.username.foreground_color = (1, 1, 1, 1)
            self.username.background_color = (0.2, 0.2, 0.2, 1)
            self.username.hint_text_color = (0.5, 0.5, 0.5, 1)
            layout.add_widget(self.username)
            
            layout.add_widget(Label(size_hint_y=None, height=dp(2)))
            
            self.password = RTLTextInput(
                hint_text='رمز عبور',
                password=True,
                size_hint_y=None,
                height=dp(50),
                font_size=sp(36)
            )
            self.password.foreground_color = (1, 1, 1, 1)
            self.password.background_color = (0.2, 0.2, 0.2, 1)
            self.password.hint_text_color = (0.5, 0.5, 0.5, 1)
            layout.add_widget(self.password)
            
            layout.add_widget(Label(size_hint_y=None, height=dp(3)))
            
            btn = PersianButton(
                text='ورود',
                size_hint_y=None,
                height=dp(45),
                background_color=(0.2, 0.6, 1, 1),
                color=(1, 1, 1, 1)
            )
            btn.bind(on_press=self.check_login)
            layout.add_widget(btn)
            
            layout.add_widget(Label(size_hint_y=None, height=dp(3)))
            
            register_btn = PersianButton(
                text='ثبت نام',
                size_hint_y=None,
                height=dp(40),
                background_color=(0.2, 0.7, 0.2, 1),
                color=(1, 1, 1, 1)
            )
            register_btn.bind(on_press=self.open_register)
            layout.add_widget(register_btn)
            
            self.add_widget(layout)
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت UI LoginScreen: {e}", error_details)
            raise
    
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