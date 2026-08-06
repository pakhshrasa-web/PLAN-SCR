# screens/settings_login_screen.py
# ========== صفحه ورود به تنظیمات مدیریت با اسکرول دقیق ==========

import traceback
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput  # ✅ اضافه شد
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
from kivy.clock import Clock

from utils.rtl_widgets import PersianButton, RTLLabel, PersianPopup
from utils.auth import get_admin_password, set_admin_password, verify_password
from error_handler import ErrorPopup
from constants import ADMIN_EMAIL


class SettingsLoginScreen(Screen):
    def __init__(self, **kwargs):
        try:
            super().__init__(**kwargs)
            with self.canvas.before:
                Color(0.08, 0.08, 0.08, 1)
                self.bg_rect = Rectangle(pos=self.pos, size=self.size)
                self.bind(pos=self._update_bg, size=self._update_bg)
            
            Window.softinput_mode = 'resize'
            self.focusable_fields = []
            
            self.build_ui()
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
            
            # ✅ استفاده از TextInput به جای RTLTextInput
            self.password_input = TextInput(
                hint_text='Enter manager password',
                password=True,  # ✅ ستاره‌ای می‌شود
                multiline=False,
                size_hint_y=None,
                height=dp(100),
                font_size=sp(32),
                halign='right',
                font_name='PersianFont',
                background_color=(0.15, 0.15, 0.15, 1),
                foreground_color=(1, 1, 1, 1),
                cursor_color=(0.2, 0.5, 0.9, 1),
                padding=[dp(14), dp(14), dp(14), dp(14)]
            )
            
            # اتصال رویداد فوکوس
            self.password_input.bind(focus=self._on_field_focus)
            self.focusable_fields.append(self.password_input)
            
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
                height=dp(60),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            login_btn.bind(on_press=self.check_login)
            btn_layout.add_widget(login_btn)
            
            back_btn = PersianButton(
                text='بازگشت',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(60),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            back_btn.bind(on_press=self.go_back)
            btn_layout.add_widget(back_btn)
            
            content.add_widget(btn_layout)
            content.add_widget(Label(size_hint_y=None, height=dp(50)))
            
            scroll.add_widget(content)
            self.add_widget(scroll)
            
            Clock.schedule_once(lambda dt: self._focus_password(), 0.1)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت UI SettingsLoginScreen: {e}", error_details)
            raise
    
    def _focus_password(self):
        if hasattr(self, 'password_input'):
            self.password_input.focus = True
    
    def _on_field_focus(self, instance, value):
        if value:
            Clock.schedule_once(lambda dt: self._select_all_text(instance), 0.1)
            Clock.schedule_once(lambda dt: self._scroll_to_field(instance), 0.3)
    
    def _select_all_text(self, instance):
        if instance and hasattr(instance, 'select_all'):
            instance.select_all()
    
    def _scroll_to_field(self, instance):
        try:
            scroll = None
            for child in self.children:
                if isinstance(child, ScrollView):
                    scroll = child
                    break
            
            if not scroll:
                return
            
            field_pos = instance.to_window(0, 0)
            field_y = field_pos[1]
            keyboard_height = 250
            window_height = Window.height
            target_y = window_height - keyboard_height - dp(100)
            
            content_height = scroll.children[0].height if scroll.children else 1
            scroll_height = scroll.height
            
            if content_height > scroll_height:
                if field_y > target_y:
                    field_ratio = (content_height - field_y) / content_height
                    scroll_value = min(0.95, max(0.05, field_ratio + 0.1))
                    scroll.scroll_y = scroll_value
                    
        except Exception as e:
            print(f"خطا در اسکرول به فیلد: {e}")
    
    def _on_keyboard(self, window, key, *args):
        if key == 13:  # Enter
            self.check_login(None)
            return True
        return False
    
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
                Clock.schedule_once(lambda dt: self._focus_password(), 0.1)
                
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ورود به تنظیمات: {e}", error_details)
    
    def go_back(self, instance):
        self.manager.current = 'login'
    
    def show_message(self, title, message):
        """نمایش پیام با پشتیبانی از متن طولانی"""
        try:
            from kivy.uix.boxlayout import BoxLayout
            from kivy.uix.scrollview import ScrollView
            from kivy.uix.label import Label
            from kivy.metrics import dp, sp
            from kivy.graphics import Color, Rectangle
            from utils.rtl_widgets import PersianPopup, PersianButton
            
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            with content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(rect, 'pos', v),
                           size=lambda i, v: setattr(rect, 'size', v))
            
            try:
                import arabic_reshaper
                from bidi.algorithm import get_display
                reshaped = arabic_reshaper.reshape(message)
                display_text = get_display(reshaped)
            except:
                display_text = message
            
            msg_label = Label(
                text=display_text,
                font_size=sp(15),
                color=(1, 1, 1, 1),
                size_hint_y=None,
                halign='center',
                valign='top',
                text_size=(dp(550), None),
                font_name='fonts/Amiri-Regular.ttf',
                padding=(dp(20), 0, dp(0), 0)
            )
            
            lines = message.count('\n') + 1
            if len(message) > 50 and lines == 1:
                approx_chars_per_line = 35
                lines = (len(message) // approx_chars_per_line) + 1
            
            line_height = sp(15) + dp(6)
            label_height = max(lines * line_height + dp(25), dp(50))
            label_height = min(label_height, dp(490))
            
            msg_label.height = label_height
            msg_label.text_size = (dp(550), label_height)
            
            scroll = ScrollView(
                do_scroll_x=False,
                do_scroll_y=True,
                size_hint_y=None,
                height=label_height + dp(10),
                bar_width=dp(6),
                bar_color=(0.3, 0.5, 0.8, 0.8),
                bar_inactive_color=(0.2, 0.2, 0.2, 0.5)
            )
            scroll.add_widget(msg_label)
            content.add_widget(scroll)
            
            btn = PersianButton(
                text='باشه',
                size_hint_y=None,
                height=dp(45),
                font_size=sp(16),
                color=(1, 1, 1, 1),
                background_color=(0.2, 0.6, 1, 1)
            )
            content.add_widget(btn)
            
            popup = PersianPopup(
                title=title,
                content=content,
                size_hint=(0.9, None),
                height=label_height + dp(250),
                background_color=(0.08, 0.08, 0.08, 1)
            )
            btn.bind(on_press=popup.dismiss)
            popup.open()
            
        except Exception as e:
            print(f"خطا در نمایش پیام: {e}")
            import traceback
            traceback.print_exc()
            try:
                from error_handler import ErrorPopup
                ErrorPopup.show_error(str(message))
            except:
                pass