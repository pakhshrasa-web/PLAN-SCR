# screens/register_screen.py
# ========== صفحه ثبت نام با اسکرول دقیق ==========

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
            
            # تغییر به resize برای اسکرول دقیق
            Window.softinput_mode = 'resize'
            
            # متغیر برای ذخیره فیلدهای قابل فوکوس
            self.focusable_fields = []
            
            self.build_ui()
            
            # اتصال رویدادهای کیبورد
            Window.bind(on_keyboard=self._on_keyboard)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت RegisterScreen: {e}", error_details)
            raise
    
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def build_ui(self):
        try:
            main_layout = BoxLayout(orientation='vertical')
            
            # ScrollView با قابلیت اسکرول دستی
            self.scroll = ScrollView(
                do_scroll_x=False,
                do_scroll_y=True,
                size_hint=(1, 1),
                scroll_type=['bars', 'content'],
                bar_width=dp(8)
            )
            
            # محتوای داخل اسکرول
            content = BoxLayout(
                orientation='vertical',
                spacing=dp(8),
                padding=dp(20),
                size_hint_y=None
            )
            content.bind(minimum_height=content.setter('height'))
            
            # ========== عنوان ==========
            title = RTLLabel(
                text='ثبت نام کاربر جدید',
                font_size=sp(28),
                size_hint_y=None,
                height=dp(55),
                color=(1, 1, 1, 1)
            )
            content.add_widget(title)
            
            content.add_widget(Label(size_hint_y=None, height=dp(5)))
            
            # ========== فیلد کد ثبت نام ==========
            self.code_input = RTLTextInput(
                hint_text='کد ثبت نام',
                multiline=False,
                size_hint_y=None,
                height=dp(85),
                font_size=sp(32)
            )
            self.code_input.bg_color = (0.15, 0.15, 0.15, 1)
            self.code_input.border_color = (0.3, 0.3, 0.3, 1)
            self.code_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.code_input._hidden_input.foreground_color = (1, 1, 1, 1)
            
            # اتصال رویداد فوکوس
            self.code_input._hidden_input.bind(focus=self._on_field_focus)
            self.focusable_fields.append(self.code_input._hidden_input)
            
            content.add_widget(self.code_input)
            
            content.add_widget(Label(size_hint_y=None, height=dp(3)))
            
            # ========== فیلد نام کاربری ==========
            self.username = RTLTextInput(
                hint_text='نام کاربری',
                multiline=False,
                size_hint_y=None,
                height=dp(85),
                font_size=sp(32)
            )
            self.username.bg_color = (0.15, 0.15, 0.15, 1)
            self.username.border_color = (0.3, 0.3, 0.3, 1)
            self.username.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.username._hidden_input.foreground_color = (1, 1, 1, 1)
            
            # اتصال رویداد فوکوس
            self.username._hidden_input.bind(focus=self._on_field_focus)
            self.focusable_fields.append(self.username._hidden_input)
            
            content.add_widget(self.username)
            
            content.add_widget(Label(size_hint_y=None, height=dp(3)))
            
            # ========== فیلد رمز عبور ==========
            self.password = RTLTextInput(
                hint_text='رمز عبور',
                password=True,
                multiline=False,
                size_hint_y=None,
                height=dp(85),
                font_size=sp(32)
            )
            self.password.bg_color = (0.15, 0.15, 0.15, 1)
            self.password.border_color = (0.3, 0.3, 0.3, 1)
            self.password.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.password._hidden_input.foreground_color = (1, 1, 1, 1)
            
            # اتصال رویداد فوکوس
            self.password._hidden_input.bind(focus=self._on_field_focus)
            self.focusable_fields.append(self.password._hidden_input)
            
            # تنظیم با Clock برای اطمینان
            Clock.schedule_once(lambda dt: self._fix_password_color(self.password), 0.1)
            content.add_widget(self.password)
            
            content.add_widget(Label(size_hint_y=None, height=dp(3)))
            
            # ========== فیلد تکرار رمز عبور ==========
            self.confirm_password = RTLTextInput(
                hint_text='تکرار رمز عبور',
                password=True,
                multiline=False,
                size_hint_y=None,
                height=dp(85),
                font_size=sp(32)
            )
            self.confirm_password.bg_color = (0.15, 0.15, 0.15, 1)
            self.confirm_password.border_color = (0.3, 0.3, 0.3, 1)
            self.confirm_password.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.confirm_password._hidden_input.foreground_color = (1, 1, 1, 1)
            
            # اتصال رویداد فوکوس
            self.confirm_password._hidden_input.bind(focus=self._on_field_focus)
            self.focusable_fields.append(self.confirm_password._hidden_input)
            
            # تنظیم با Clock برای اطمینان
            Clock.schedule_once(lambda dt: self._fix_password_color(self.confirm_password), 0.1)
            content.add_widget(self.confirm_password)
            
            content.add_widget(Label(size_hint_y=None, height=dp(3)))
            
            # ========== فیلد شماره تلفن ==========
            self.phone = RTLTextInput(
                hint_text='شماره تلفن',
                multiline=False,
                size_hint_y=None,
                height=dp(85),
                font_size=sp(32)
            )
            self.phone.bg_color = (0.15, 0.15, 0.15, 1)
            self.phone.border_color = (0.3, 0.3, 0.3, 1)
            self.phone.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.phone._hidden_input.foreground_color = (1, 1, 1, 1)
            
            # اتصال رویداد فوکوس
            self.phone._hidden_input.bind(focus=self._on_field_focus)
            self.focusable_fields.append(self.phone._hidden_input)
            
            content.add_widget(self.phone)
            
            content.add_widget(Label(size_hint_y=None, height=dp(3)))
            
            # ========== فیلد ایمیل ==========
            self.email = RTLTextInput(
                hint_text='ایمیل',
                multiline=False,
                size_hint_y=None,
                height=dp(85),
                font_size=sp(32)
            )
            self.email.bg_color = (0.15, 0.15, 0.15, 1)
            self.email.border_color = (0.3, 0.3, 0.3, 1)
            self.email.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.email._hidden_input.foreground_color = (1, 1, 1, 1)
            
            # اتصال رویداد فوکوس
            self.email._hidden_input.bind(focus=self._on_field_focus)
            self.focusable_fields.append(self.email._hidden_input)
            
            content.add_widget(self.email)
            
            content.add_widget(Label(size_hint_y=None, height=dp(10)))
            
            # ========== دکمه‌ها ==========
            btn_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(60))
            
            register_btn = PersianButton(
                text='ثبت نام',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(55),
                color=(1, 1, 1, 1),
                font_size=sp(20)
            )
            register_btn.bind(on_press=self.do_register)
            btn_layout.add_widget(register_btn)
            
            back_btn = PersianButton(
                text='بازگشت',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(55),
                color=(1, 1, 1, 1),
                font_size=sp(20)
            )
            back_btn.bind(on_press=self.go_back)
            btn_layout.add_widget(back_btn)
            
            content.add_widget(btn_layout)
            
            # اضافه کردن محتوا به اسکرول
            self.scroll.add_widget(content)
            main_layout.add_widget(self.scroll)
            
            self.add_widget(main_layout)
            
            # تنظیم اسکرول به بالا
            Clock.schedule_once(self._adjust_scroll, 0.1)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت UI RegisterScreen: {e}", error_details)
            raise
    
    def _adjust_scroll(self, dt):
        """تنظیم اسکرول به بالا"""
        if hasattr(self, 'scroll'):
            self.scroll.scroll_y = 1
    
    # ============================================================
    # مدیریت فوکوس و انتخاب خودکار متن
    # ============================================================
    
    def _on_field_focus(self, instance, value):
        """وقتی فیلد فوکوس میشه یا فوکوس رو از دست میده"""
        if value:
            # وقتی فیلد فوکوس میشه، کل متن رو انتخاب کن
            Clock.schedule_once(lambda dt: self._select_all_text(instance), 0.1)
            
            # اسکرول به فیلد با تأخیر برای اطمینان از نمایش کیبورد
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
                    field_ratio = (content_height - field_y) / content_height
                    scroll_value = min(0.95, max(0.05, field_ratio + 0.1))
                    self.scroll.scroll_y = scroll_value
                elif field_y < dp(50):
                    # فیلد خیلی بالاست، اسکرول به پایین
                    self.scroll.scroll_y = 0.9
                else:
                    # فیلد در محدوده قابل قبول است
                    pass
                    
        except Exception as e:
            print(f"خطا در اسکرول به فیلد: {e}")
    
    # ============================================================
    # مدیریت کلیدهای کیبورد
    # ============================================================
    
    def _on_keyboard(self, window, key, *args):
        """مدیریت کلیدهای کیبورد"""
        if key == 9:  # Tab
            self._focus_next()
            return True
        elif key == 13:  # Enter
            self.do_register(None)
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
    # توابع کاربردی
    # ============================================================
    
    def _fix_password_color(self, field):
        """تنظیم مجدد رنگ فیلد رمز عبور"""
        try:
            if hasattr(field, '_hidden_input'):
                field._hidden_input.foreground_color = (1, 1, 1, 1)
                field._hidden_input.background_color = (0.15, 0.15, 0.15, 1)
                field._hidden_input.cursor_color = (1, 1, 1, 1)
                field._hidden_input.background_active = (0.15, 0.15, 0.15, 1)
                field._hidden_input.background_normal = (0.15, 0.15, 0.15, 1)
        except Exception as e:
            print(f"خطا در تنظیم رنگ فیلد رمز: {e}")
    
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
            content = BoxLayout(orientation='vertical', padding=dp(25), spacing=dp(15))
            with content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                           size=lambda i, v: setattr(content_rect, 'size', v))
            
            content.add_widget(RTLLabel(
                text=message,
                size_hint_y=None,
                height=dp(100),
                font_size=sp(22),
                color=(1, 1, 1, 1)
            ))
            btn = PersianButton(
                text='باشه',
                size_hint_y=None,
                height=dp(55),
                font_size=sp(22),
                color=(1, 1, 1, 1),
                background_color=(0.2, 0.6, 1, 1)
            )
            content.add_widget(btn)
            
            popup = PersianPopup(
                title=title,
                content=content,
                size_hint=(0.9, 0.5),
                background_color=(0.08, 0.08, 0.08, 1)
            )
            btn.bind(on_press=popup.dismiss)
            popup.open()
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش پیام: {e}", error_details)