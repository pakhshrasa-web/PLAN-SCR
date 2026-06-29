# screens/register_screen.py
# ========== صفحه ثبت نام ==========

import traceback
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.graphics import Color, Rectangle

from utils.rtl_widgets import RTLTextInput, PersianButton, RTLLabel
from utils.user_manager import register_user
from error_handler import ErrorPopup


class RegisterScreen(Screen):
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
            ErrorPopup.show_error(f"خطا در ساخت RegisterScreen: {e}", error_details)
            raise
    
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def build_ui(self):
        try:
            layout = BoxLayout(orientation='vertical', spacing=dp(15), padding=dp(40))
            
            title = RTLLabel(
                text='ثبت نام کاربر جدید',
                font_size=sp(24),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1)
            )
            layout.add_widget(title)
            
            self.code_input = RTLTextInput(
                hint_text='کد ثبت نام',
                multiline=False,
                size_hint_y=None,
                height=dp(55),
                font_size=sp(36)
            )
            self.code_input.foreground_color = (1, 1, 1, 1)
            self.code_input.background_color = (0.2, 0.2, 0.2, 1)
            self.code_input.hint_text_color = (0.5, 0.5, 0.5, 1)
            layout.add_widget(self.code_input)
            
            self.username = RTLTextInput(
                hint_text='نام کاربری',
                multiline=False,
                size_hint_y=None,
                height=dp(55),
                font_size=sp(36)
            )
            self.username.foreground_color = (1, 1, 1, 1)
            self.username.background_color = (0.2, 0.2, 0.2, 1)
            self.username.hint_text_color = (0.5, 0.5, 0.5, 1)
            layout.add_widget(self.username)
            
            self.password = RTLTextInput(
                hint_text='رمز عبور',
                password=True,
                multiline=False,
                size_hint_y=None,
                height=dp(55),
                font_size=sp(36)
            )
            self.password.foreground_color = (1, 1, 1, 1)
            self.password.background_color = (0.2, 0.2, 0.2, 1)
            self.password.hint_text_color = (0.5, 0.5, 0.5, 1)
            layout.add_widget(self.password)
            
            self.confirm_password = RTLTextInput(
                hint_text='تکرار رمز عبور',
                password=True,
                multiline=False,
                size_hint_y=None,
                height=dp(55),
                font_size=sp(36)
            )
            self.confirm_password.foreground_color = (1, 1, 1, 1)
            self.confirm_password.background_color = (0.2, 0.2, 0.2, 1)
            self.confirm_password.hint_text_color = (0.5, 0.5, 0.5, 1)
            layout.add_widget(self.confirm_password)
            
            self.phone = RTLTextInput(
                hint_text='شماره تلفن',
                multiline=False,
                size_hint_y=None,
                height=dp(55),
                font_size=sp(36)
            )
            self.phone.foreground_color = (1, 1, 1, 1)
            self.phone.background_color = (0.2, 0.2, 0.2, 1)
            self.phone.hint_text_color = (0.5, 0.5, 0.5, 1)
            layout.add_widget(self.phone)
            
            self.email = RTLTextInput(
                hint_text='ایمیل',
                multiline=False,
                size_hint_y=None,
                height=dp(55),
                font_size=sp(36)
            )
            self.email.foreground_color = (1, 1, 1, 1)
            self.email.background_color = (0.2, 0.2, 0.2, 1)
            self.email.hint_text_color = (0.5, 0.5, 0.5, 1)
            layout.add_widget(self.email)
            
            btn_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(55))
            
            register_btn = PersianButton(
                text='ثبت نام',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1)
            )
            register_btn.bind(on_press=self.do_register)
            btn_layout.add_widget(register_btn)
            
            back_btn = PersianButton(
                text='بازگشت',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1)
            )
            back_btn.bind(on_press=self.go_back)
            btn_layout.add_widget(back_btn)
            
            layout.add_widget(btn_layout)
            self.add_widget(layout)
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت UI RegisterScreen: {e}", error_details)
            raise
    
    def do_register(self, instance):
        try:
            if self.password.text != self.confirm_password.text:
                self.show_message('خطا', 'رمز عبور و تکرار آن مطابقت ندارند')
                return
            
            success, message = register_user(
                self.code_input.text,
                self.username.text,
                self.password.text,
                self.phone.text,
                self.email.text
            )
            
            if success:
                self.show_message('موفق', message)
                self.manager.current = 'login'
            else:
                self.show_message('خطا', message)
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ثبت نام: {e}", error_details)
    
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