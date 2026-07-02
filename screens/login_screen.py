# screens/login_screen.py
# ========== صفحه ورود ==========

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
from kivy.utils import platform
from kivy.logger import Logger as logger

from utils.rtl_widgets import RTLTextInput, PersianButton, RTLLabel
from utils.user_manager import login
from utils.backup_manager import create_backup, restore_backup, validate_backup_file
from utils.file_picker import FilePicker
from error_handler import ErrorPopup


class LoginScreen(Screen):
    """صفحه ورود - فقط رابط کاربری"""

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
            ErrorPopup.show_error(f"خطا در ساخت LoginScreen: {e}", error_details)
            raise
    
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def build_ui(self):
        try:
            main_layout = BoxLayout(orientation='vertical')
            
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
                font_size=sp(32)
            )
            self.password.bg_color = (0.15, 0.15, 0.15, 1)
            self.password.border_color = (0.3, 0.3, 0.3, 1)
            self.password.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.password._hidden_input.foreground_color = (1, 1, 1, 1)
            self.password._hidden_input.bind(focus=self._on_field_focus)
            self.focusable_fields.append(self.password._hidden_input)
            content.add_widget(self.password)
            
            # ========== دکمه ورود ==========
            btn = PersianButton(
                text='ورود',
                size_hint_y=None,
                height=dp(60),
                background_color=(0.2, 0.6, 1, 1),
                color=(1, 1, 1, 1)
            )
            btn.bind(on_press=self.check_login)
            content.add_widget(btn)
            content.add_widget(Label(size_hint_y=None, height=dp(5)))
            
            # ========== دکمه ثبت نام ==========
            register_btn = PersianButton(
                text='ثبت نام',
                size_hint_y=None,
                height=dp(60),
                background_color=(0.2, 0.7, 0.2, 1),
                color=(1, 1, 1, 1)
            )
            register_btn.bind(on_press=self.open_register)
            content.add_widget(register_btn)
            
            self.scroll.add_widget(content)
            main_layout.add_widget(self.scroll)
            self.add_widget(main_layout)
            
            Clock.schedule_once(self._adjust_scroll, 0.1)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت UI LoginScreen: {e}", error_details)
            raise
    
    def _adjust_scroll(self, dt):
        if hasattr(self, 'scroll'):
            self.scroll.scroll_y = 1
    
    # ============================================================
    # ✅ مدیریت فوکوس
    # ============================================================
    
    def _on_field_focus(self, instance, value):
        if value:
            Clock.schedule_once(lambda dt: self._select_all_text(instance), 0.1)
            Clock.schedule_once(lambda dt: self._scroll_to_field(instance), 0.3)
    
    def _select_all_text(self, instance):
        if instance and hasattr(instance, 'select_all'):
            instance.select_all()
    
    def _scroll_to_field(self, instance):
        try:
            if not hasattr(self, 'scroll'):
                return
            
            field_pos = instance.to_window(0, 0)
            field_y = field_pos[1]
            keyboard_height = 250
            window_height = Window.height
            target_y = window_height - keyboard_height - dp(80)
            
            content_height = self.scroll.children[0].height if self.scroll.children else 1
            scroll_height = self.scroll.height
            
            if content_height > scroll_height:
                if field_y > target_y:
                    field_ratio = (content_height - field_y) / content_height
                    scroll_value = min(0.95, max(0.05, field_ratio + 0.1))
                    self.scroll.scroll_y = scroll_value
                elif field_y < dp(50):
                    self.scroll.scroll_y = 0.9
        except Exception as e:
            logger.warning(f"⚠️ خطا در اسکرول: {e}")
    
    # ============================================================
    # ✅ مدیریت کیبورد
    # ============================================================
    
    def _on_keyboard(self, window, key, *args):
        if key == 9:  # Tab
            self._focus_next()
            return True
        elif key == 13:  # Enter
            self.check_login(None)
            return True
        return False
    
    def _focus_next(self):
        if not self.focusable_fields:
            return
        for i, field in enumerate(self.focusable_fields):
            if field.focus:
                next_i = (i + 1) % len(self.focusable_fields)
                self.focusable_fields[next_i].focus = True
                break
    
    # ============================================================
    # ✅ بکاپ و بازیابی (فقط رابط کاربری)
    # ============================================================
    
    def do_backup(self, instance):
        """ایجاد بکاپ"""
        success, message, backup_path = create_backup()
        self.show_message('✅ موفق' if success else '❌ خطا', message)
    
    def do_restore(self, instance):
        """باز کردن دیالوگ انتخاب فایل بکاپ"""
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            with content.canvas.before:
                Color(0.15, 0.15, 0.15, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                           size=lambda i, v: setattr(content_rect, 'size', v))
            
            content.add_widget(RTLLabel(
                text='📂 لطفاً فایل بکاپ را انتخاب کنید:',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(18),
                color=(1, 1, 1, 1)
            ))
            
            content.add_widget(RTLLabel(
                text='فایل‌های بکاپ معمولاً با فرمت .zip هستند',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(14),
                color=(0.6, 0.6, 0.6, 1)
            ))
            
            self.restore_file_picker = FilePicker(
                on_select=self._on_backup_file_selected,
                file_type='backup',
                size_hint_y=None,
                height=dp(120)
            )
            content.add_widget(self.restore_file_picker)
            
            btn_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(55))
            cancel_btn = PersianButton(
                text='❌ انصراف',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                font_size=sp(18),
                color=(1, 1, 1, 1)
            )
            cancel_btn.bind(on_press=lambda x: self._dismiss_restore_popup())
            btn_layout.add_widget(cancel_btn)
            content.add_widget(btn_layout)
            
            self.restore_popup = Popup(
                title='📂 بازیابی اطلاعات',
                content=content,
                size_hint=(0.9, 0.6),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )
            self.restore_popup.title_color = (1, 1, 1, 1)
            self.restore_popup.title_size = sp(20)
            self.restore_popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در بازیابی: {e}", error_details)
    
    def _on_backup_file_selected(self, file_path):
        """پس از انتخاب فایل بکاپ"""
        try:
            logger.info(f"📂 فایل بکاپ انتخاب شد: {file_path}")
            
            if hasattr(self, 'restore_popup') and self.restore_popup:
                self.restore_popup.dismiss()
            
            # ✅ اعتبارسنجی فایل
            is_valid, msg, _ = validate_backup_file(file_path)
            if not is_valid:
                self.show_message('❌ خطا', msg)
                return
            
            self._confirm_restore(file_path)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در انتخاب فایل بکاپ: {e}", error_details)
    
    def _confirm_restore(self, backup_path):
        """دیالوگ تأیید بازیابی"""
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            with content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                           size=lambda i, v: setattr(content_rect, 'size', v))
            
            content.add_widget(RTLLabel(
                text=f'⚠️ آیا از بازیابی اطلاعات از فایل زیر مطمئن هستید؟\n\n📄 {os.path.basename(backup_path)}\n\n🔴 تمام داده‌های فعلی با داده‌های بکاپ جایگزین خواهند شد.',
                size_hint_y=None,
                height=dp(100),
                font_size=sp(16),
                color=(1, 0.8, 0.2, 1)
            ))
            
            btn_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(55))
            
            restore_btn = PersianButton(
                text='✅ بازیابی',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                font_size=sp(18),
                color=(1, 1, 1, 1)
            )
            restore_btn.bind(on_press=lambda x: self._perform_restore(backup_path))
            
            cancel_btn = PersianButton(
                text='❌ انصراف',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                font_size=sp(18),
                color=(1, 1, 1, 1)
            )
            cancel_btn.bind(on_press=self._dismiss_confirm_popup)
            
            btn_layout.add_widget(restore_btn)
            btn_layout.add_widget(cancel_btn)
            content.add_widget(btn_layout)
            
            self.confirm_popup = Popup(
                title='⚠️ تأیید بازیابی',
                content=content,
                size_hint=(0.85, 0.45),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )
            self.confirm_popup.title_color = (1, 1, 1, 1)
            self.confirm_popup.title_size = sp(20)
            self.confirm_popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش دیالوگ تأیید: {e}", error_details)
    
    def _dismiss_restore_popup(self):
        if hasattr(self, 'restore_popup') and self.restore_popup:
            self.restore_popup.dismiss()
    
    def _dismiss_confirm_popup(self, instance=None):
        if hasattr(self, 'confirm_popup') and self.confirm_popup:
            self.confirm_popup.dismiss()
    
    def _perform_restore(self, backup_path):
        """اجرای بازیابی"""
        self._dismiss_confirm_popup()
        success, message = restore_backup(backup_path)
        self.show_message('✅ موفق' if success else '❌ خطا', message)
        
        if success:
            Clock.schedule_once(lambda dt: self._restart_app(), 2.5)
    
    def _restart_app(self):
        from kivy.app import App
        App.get_running_app().stop()
    
    # ============================================================
    # ✅ توابع اصلی
    # ============================================================
    
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
    
    # ============================================================
    # ✅ نمایش پیام
    # ============================================================
    
    def show_message(self, title, message):
        """نمایش پیام با PersianLabel"""
        try:
            from utils.rtl_widgets import RTLMessageLabel
            
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
            with content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                           size=lambda i, v: setattr(content_rect, 'size', v))
            
            # ✅ اسکرول برای متن‌های بلند
            scroll = ScrollView(size_hint_y=None, height=dp(300))
            msg_label = RTLMessageLabel(
                text=message,
                font_size=sp(22) if len(message) < 100 else sp(18),
                color=(1, 1, 1, 1),
                size_hint_y=None
            )
            msg_label.bind(texture_size=msg_label.setter('size'))
            scroll.add_widget(msg_label)
            content.add_widget(scroll)
            
            btn = PersianButton(
                text='باشه',
                size_hint_y=None,
                height=dp(55),
                font_size=sp(22),
                color=(1, 1, 1, 1),
                background_color=(0.2, 0.6, 1, 1)
            )
            content.add_widget(btn)
            
            popup = Popup(
                title=title,
                content=content,
                size_hint=(0.9, 0.7),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=True
            )
            popup.title_color = (1, 1, 1, 1)
            popup.title_size = sp(24)
            btn.bind(on_press=popup.dismiss)
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش پیام: {e}", error_details)
