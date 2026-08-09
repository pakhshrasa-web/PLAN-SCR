# screens/login_screen.py
# ========== صفحه ورود ==========

import traceback
import os
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.utils import platform
from kivy.logger import Logger as logger
from screens.attendance_screen import AttendanceScreen

from utils.rtl_widgets import RTLTextInput, PersianButton, RTLLabel, PersianPopup, PersianComboBox
from utils.user_manager import login, get_users, save_current_user
from utils.backup_manager import create_backup, restore_backup, validate_backup_file
from utils.file_picker_backup import BackupFilePicker
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
    
    def _get_user_names(self):
        """دریافت لیست نام کاربران برای کامبوباکس"""
        try:
            users = get_users()
            if not users:
                return []
            names = []
            for u in users:
                if u.get('name'):
                    names.append(u.get('name'))
                elif u.get('username'):
                    names.append(u.get('username'))
            return names
        except Exception as e:
            print(f"خطا در دریافت کاربران: {e}")
            return []
    
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
                size_hint_x=0.25,
                background_color=(1, 0.8, 0.1, 1),
                size_hint_y=None,
                height=dp(40),
                color=(0, 0, 0, 1),
                font_size=sp(14)
            )
            settings_btn.bind(on_press=self.open_settings)
            header_layout.add_widget(settings_btn)
            
            backup_btn = PersianButton(
                text='بکاپ',
                size_hint_x=0.25,
                background_color=(0.2, 0.5, 0.8, 1),
                size_hint_y=None,
                height=dp(40),
                color=(1, 1, 1, 1),
                font_size=sp(14)
            )
            backup_btn.bind(on_press=self.do_backup)
            header_layout.add_widget(backup_btn)
            
            restore_btn = PersianButton(
                text='بازیابی',
                size_hint_x=0.25,
                background_color=(0.8, 0.5, 0.2, 1),
                size_hint_y=None,
                height=dp(40),
                color=(1, 1, 1, 1),
                font_size=sp(14)
            )
            restore_btn.bind(on_press=self.do_restore)
            header_layout.add_widget(restore_btn)
            
            header_layout.add_widget(Label(text='', size_hint_x=0.25))
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
            
            # ========== کامبوباکس نام کاربری ==========
            content.add_widget(RTLLabel(
                text='انتخاب کاربر:',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))
            
            user_names = self._get_user_names()
            if not user_names:
                user_names = ['هیچ کاربری ثبت نشده']
            
            self.username_combo = PersianComboBox(
                text=user_names[0] if user_names else '',
                values=user_names,
                height=dp(70)
            )
            self.username_combo.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.username_combo.main_btn.color = (1, 1, 1, 1)
            self.username_combo.main_btn.font_size = sp(20)
            content.add_widget(self.username_combo)
            
            content.add_widget(Label(size_hint_y=None, height=dp(5)))
            
            # ========== فیلد رمز عبور ==========
            content.add_widget(RTLLabel(
                text='رمز عبور:',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))
            
            self.password = TextInput(
                hint_text='Enter Password',
                password=True,
                multiline=False,
                size_hint_y=None,
                height=dp(80),
                font_size=sp(24),
                halign='right',
                font_name='PersianFont',
                background_color=(0.15, 0.15, 0.15, 1),
                foreground_color=(1, 1, 1, 1),
                cursor_color=(0.2, 0.5, 0.9, 1),
                padding=[dp(14), dp(14), dp(14), dp(14)]
            )
            
            self.password.bind(focus=self._on_field_focus)
            self.focusable_fields.append(self.password)
            
            content.add_widget(self.password)
            
            # ========== دکمه ورود ==========
            btn = PersianButton(
                text='ورود به برنامه',
                size_hint_y=None,
                height=dp(50),
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
                height=dp(50),
                background_color=(0.2, 0.7, 0.2, 1),
                color=(1, 1, 1, 1)
            )
            register_btn.bind(on_press=self.open_register)
            content.add_widget(register_btn)
            
            # ========== دکمه حضور و غیاب ==========
            attendance_btn = PersianButton(
                text='حضور و غیاب',
                size_hint_y=None,
                height=dp(50),
                background_color=(0.4, 0.2, 0.6, 1),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            attendance_btn.bind(on_press=self.show_attendance_login_dialog)
            content.add_widget(attendance_btn)
            
            # ========== ✅ دکمه گزارش عملکرد روزانه (زیر حضور و غیاب) ==========
            report_btn = PersianButton(
                text='گزارش عملکرد روزانه',
                size_hint_y=None,
                height=dp(50),
                background_color=(0.2, 0.6, 0.8, 1),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            report_btn.bind(on_press=self.show_report_login_dialog)
            content.add_widget(report_btn)
            
            content.add_widget(Label(size_hint_y=None, height=dp(5)))

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
    # مدیریت فوکوس
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
            logger.warning(f"خطا در اسکرول: {e}")
    
    # ============================================================
    # مدیریت کیبورد
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
    # بکاپ و بازیابی
    # ============================================================
    
    def do_backup(self, instance):
        success, message, backup_path = create_backup()
        self.show_message('موفق' if success else 'خطا', message)
    
    def do_restore(self, instance):
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            with content.canvas.before:
                Color(0.15, 0.15, 0.15, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                           size=lambda i, v: setattr(content_rect, 'size', v))
            
            content.add_widget(RTLLabel(
                text='لطفاً فایل بکاپ را انتخاب کنید:',
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
            
            self.restore_file_picker = BackupFilePicker(
                on_select=self._on_backup_file_selected,
                size_hint_y=None,
                height=dp(120)
            )
            content.add_widget(self.restore_file_picker)
            
            btn_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(55))
            cancel_btn = PersianButton(
                text='انصراف',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                font_size=sp(18),
                color=(1, 1, 1, 1)
            )
            cancel_btn.bind(on_press=lambda x: self._dismiss_restore_popup())
            btn_layout.add_widget(cancel_btn)
            content.add_widget(btn_layout)
            
            self.restore_popup = PersianPopup(
                title='بازیابی اطلاعات',
                content=content,
                size_hint=(0.9, 0.6),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )
            self.restore_popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در بازیابی: {e}", error_details)
    
    def _on_backup_file_selected(self, file_path):
        try:
            logger.info(f"فایل بکاپ انتخاب شد: {file_path}")
            
            if hasattr(self, 'restore_popup') and self.restore_popup:
                self.restore_popup.dismiss()
            
            is_valid, msg, _ = validate_backup_file(file_path)
            if not is_valid:
                self.show_message('خطا', msg)
                return
            
            self._confirm_restore(file_path)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در انتخاب فایل بکاپ: {e}", error_details)
    
    def _confirm_restore(self, backup_path):
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            with content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                           size=lambda i, v: setattr(content_rect, 'size', v))
            
            content.add_widget(RTLLabel(
                text=f'آیا از بازیابی اطلاعات از فایل زیر مطمئن هستید؟\n\n{os.path.basename(backup_path)}\n\nتمام داده‌های فعلی با داده‌های بکاپ جایگزین خواهند شد.',
                size_hint_y=None,
                height=dp(100),
                font_size=sp(16),
                color=(1, 0.8, 0.2, 1)
            ))
            
            btn_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(55))
            
            restore_btn = PersianButton(
                text='بازیابی',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                font_size=sp(18),
                color=(1, 1, 1, 1)
            )
            restore_btn.bind(on_press=lambda x: self._perform_restore(backup_path))
            
            cancel_btn = PersianButton(
                text='انصراف',
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
            
            self.confirm_popup = PersianPopup(
                title='تأیید بازیابی',
                content=content,
                size_hint=(0.85, 0.45),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )
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
        self._dismiss_confirm_popup()
        success, message = restore_backup(backup_path)
        self.show_message('موفق' if success else 'خطا', message)
        
        if success:
            Clock.schedule_once(lambda dt: self._restart_app(), 2.5)
    
    def _restart_app(self):
        from kivy.app import App
        App.get_running_app().stop()
    
    # ============================================================
    # توابع اصلی
    # ============================================================
    
    def open_settings(self, instance):
        self.manager.current = 'settings_login'
    
    def open_register(self, instance):
        self.manager.current = 'register'
    
    def open_report(self, instance):
        """باز کردن صفحه گزارش عملکرد روزانه"""
        if not self.manager.has_screen('total_report'):
            from screens.total_report_screen import TotalReportScreen
            self.manager.add_widget(TotalReportScreen(name='total_report'))
        self.manager.current = 'total_report'
    
    def check_login(self, instance):
        try:
            selected_name = self.username_combo.text
            
            users = get_users()
            user = None
            for u in users:
                if u.get('name') == selected_name or u.get('username') == selected_name:
                    user = u
                    break
            
            if not user:
                self.show_message('خطا', 'کاربر انتخاب شده یافت نشد')
                return
            
            username = user.get('username', '')
            password = self.password.text
            
            logged_in_user = login(username, password)
            
            if logged_in_user:
                # ✅ ذخیره کاربر جاری برای لاگین خودکار
                save_current_user(logged_in_user)
                
                role = logged_in_user.get('role', '')
                username = logged_in_user.get('username', '')
                
                from kivy.app import App
                app = App.get_running_app()
                if app:
                    app.current_user_role = role
                    app.current_username = username
                    print(f"نقش کاربر در App ذخیره شد: {role} - {username}")
                
                self.current_user_role = role
                
                if role == 'مدیر' or role == 'سرپرست':
                    self.manager.current = 'admin'
                elif role == 'سوپروایزر':
                    self.manager.current = 'supervisor'
                else:
                    self.manager.current = 'user'
            else:
                self.show_message('خطا', 'رمز عبور اشتباه است')
                self.password.text = ''
                Clock.schedule_once(lambda dt: setattr(self.password, 'focus', True), 0.1)
                
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ورود: {e}", error_details)

    def show_attendance_login_dialog(self, instance):
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(12))
            with content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(rect, 'pos', v),
                        size=lambda i, v: setattr(rect, 'size', v))
            
            content.add_widget(RTLLabel(
                text='ورود به حضور و غیاب',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(20),
                bold=True,
                color=(0.4, 0.8, 1, 1)
            ))
            
            content.add_widget(BoxLayout(size_hint_y=None, height=dp(5)))
            
            content.add_widget(RTLLabel(
                text='انتخاب کاربر:',
                size_hint_y=None,
                height=dp(22),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            
            user_names = self._get_user_names()
            if not user_names:
                user_names = ['هیچ کاربری ثبت نشده']
            
            username_combo = PersianComboBox(
                text=user_names[0] if user_names else '',
                values=user_names,
                height=dp(55)
            )
            username_combo.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            username_combo.main_btn.color = (1, 1, 1, 1)
            username_combo.main_btn.font_size = sp(16)
            content.add_widget(username_combo)
            
            content.add_widget(BoxLayout(size_hint_y=None, height=dp(5)))
            
            content.add_widget(RTLLabel(
                text='رمز عبور:',
                size_hint_y=None,
                height=dp(22),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            
            password_input = TextInput(
                hint_text='Enter Password',
                password=True,
                multiline=False,
                size_hint_y=None,
                height=dp(55),
                font_size=sp(18),
                halign='right',
                font_name='PersianFont',
                background_color=(0.15, 0.15, 0.15, 1),
                foreground_color=(1, 1, 1, 1),
                cursor_color=(0.2, 0.5, 0.9, 1),
                padding=[dp(14), dp(14), dp(14), dp(14)]
            )
            content.add_widget(password_input)
            
            content.add_widget(BoxLayout(size_hint_y=None, height=dp(10)))
            
            btn_layout = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
            
            login_btn = PersianButton(
                text='ورود',
                background_color=(0.4, 0.2, 0.6, 1),
                size_hint_y=None,
                height=dp(42),
                color=(1, 1, 1, 1),
                font_size=sp(16),
                bold=True
            )
            
            cancel_btn = PersianButton(
                text='انصراف',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(42),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            
            btn_layout.add_widget(login_btn)
            btn_layout.add_widget(cancel_btn)
            content.add_widget(btn_layout)
            
            popup = PersianPopup(
                title='حضور و غیاب',
                content=content,
                size_hint=(0.85, 0.55),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )
            
            def do_login(instance):
                selected_name = username_combo.text
                
                users = get_users()
                user = None
                for u in users:
                    if u.get('name') == selected_name or u.get('username') == selected_name:
                        user = u
                        break
                
                if not user:
                    self.show_message('خطا', 'کاربر انتخاب شده یافت نشد')
                    return
                
                username = user.get('username', '')
                password = password_input.text.strip()
                
                if not username or not password:
                    self.show_message('خطا', 'لطفاً نام کاربری و رمز عبور را وارد کنید')
                    return
                
                logged_in_user = login(username, password)
                
                if logged_in_user:
                    # ✅ ذخیره کاربر جاری
                    save_current_user(logged_in_user)
                    
                    popup.dismiss()
                    if not self.manager.has_screen('attendance'):
                        from screens.attendance_screen import AttendanceScreen
                        self.manager.add_widget(AttendanceScreen(name='attendance'))
                    
                    attendance_screen = self.manager.get_screen('attendance')
                    attendance_screen.set_user(logged_in_user)
                    self.manager.current = 'attendance'
                else:
                    self.show_message('خطا', 'نام کاربری یا رمز عبور اشتباه است')
                    password_input.text = ''
                    Clock.schedule_once(lambda dt: setattr(password_input, 'focus', True), 0.1)
            
            def on_cancel(instance):
                popup.dismiss()
            
            login_btn.bind(on_press=do_login)
            cancel_btn.bind(on_press=on_cancel)
            password_input.bind(on_text_validate=do_login)
            
            popup.open()
            
            Clock.schedule_once(lambda dt: setattr(username_combo.main_btn, 'focus', True), 0.2)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)

    def show_report_login_dialog(self, instance):
        """نمایش دیالوگ لاگین گزارش عملکرد روزانه"""
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(12))
            with content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(rect, 'pos', v),
                        size=lambda i, v: setattr(rect, 'size', v))
            
            # عنوان
            content.add_widget(RTLLabel(
                text='ورود به گزارش عملکرد روزانه',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(20),
                bold=True,
                color=(0.4, 0.8, 1, 1)
            ))
            
            content.add_widget(BoxLayout(size_hint_y=None, height=dp(5)))
            
            # کامبوباکس کاربران
            content.add_widget(RTLLabel(
                text='انتخاب کاربر:',
                size_hint_y=None,
                height=dp(25),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            
            users = get_users()
            user_names = []
            for u in users:
                name = u.get('name', '') or u.get('username', '')
                if name:
                    user_names.append(name)
            
            if not user_names:
                user_names = ['هیچ کاربری ثبت نشده']
            
            username_combo = PersianComboBox(
                text=user_names[0] if user_names else '',
                values=user_names,
                height=dp(60)
            )
            username_combo.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            username_combo.main_btn.color = (1, 1, 1, 1)
            username_combo.main_btn.font_size = sp(18)
            content.add_widget(username_combo)
            
            content.add_widget(BoxLayout(size_hint_y=None, height=dp(5)))
            
            # رمز عبور
            content.add_widget(RTLLabel(
                text='رمز عبور:',
                size_hint_y=None,
                height=dp(25),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            
            password_input = TextInput(
                hint_text='Enter Password',
                password=True,
                multiline=False,
                size_hint_y=None,
                height=dp(55),
                font_size=sp(18),
                halign='right',
                font_name='PersianFont',
                background_color=(0.15, 0.15, 0.15, 1),
                foreground_color=(1, 1, 1, 1),
                cursor_color=(0.2, 0.5, 0.9, 1),
                padding=[dp(14), dp(14), dp(14), dp(14)]
            )
            content.add_widget(password_input)
            
            content.add_widget(BoxLayout(size_hint_y=None, height=dp(10)))
            
            # دکمه‌ها
            btn_layout = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
            
            login_btn = PersianButton(
                text='ورود',
                background_color=(0.2, 0.6, 0.2, 1),
                size_hint_y=None,
                height=dp(42),
                color=(1, 1, 1, 1),
                font_size=sp(16),
                bold=True
            )
            
            cancel_btn = PersianButton(
                text='انصراف',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(42),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            
            btn_layout.add_widget(login_btn)
            btn_layout.add_widget(cancel_btn)
            content.add_widget(btn_layout)
            
            popup = PersianPopup(
                title='ورود',
                content=content,
                size_hint=(0.85, 0.55),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )
            
            def do_login(instance):
                selected_name = username_combo.text
                
                users = get_users()
                user = None
                for u in users:
                    name = u.get('name', '') or u.get('username', '')
                    if name == selected_name:
                        user = u
                        break
                
                if not user:
                    self.show_message('خطا', 'کاربر انتخاب شده یافت نشد')
                    return
                
                username = user.get('username', '')
                password = password_input.text.strip()
                
                if not username or not password:
                    self.show_message('خطا', 'لطفاً نام کاربری و رمز عبور را وارد کنید')
                    return
                
                logged_in_user = login(username, password)
                
                if logged_in_user:
                    # ✅ ذخیره کاربر جاری
                    save_current_user(logged_in_user)
                    
                    popup.dismiss()
                    if not self.manager.has_screen('total_report'):
                        from screens.total_report_screen import TotalReportScreen
                        self.manager.add_widget(TotalReportScreen(name='total_report'))
                    
                    report_screen = self.manager.get_screen('total_report')
                    report_screen.current_user = logged_in_user
                    report_screen.show_report_tab()
                    self.manager.current = 'total_report'
                else:
                    self.show_message('خطا', 'نام کاربری یا رمز عبور اشتباه است')
                    password_input.text = ''
                    Clock.schedule_once(lambda dt: setattr(password_input, 'focus', True), 0.1)
            
            def on_cancel(instance):
                popup.dismiss()
            
            login_btn.bind(on_press=do_login)
            cancel_btn.bind(on_press=on_cancel)
            password_input.bind(on_text_validate=do_login)
            
            popup.open()
            
            Clock.schedule_once(lambda dt: setattr(username_combo.main_btn, 'focus', True), 0.2)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)

    # ============================================================
    # نمایش پیام
    # ============================================================
    
    def show_message(self, title, message):
        """نمایش پیام با پشتیبانی از متن طولانی"""
        try:
            from kivy.uix.scrollview import ScrollView
            from kivy.uix.label import Label
            from kivy.uix.boxlayout import BoxLayout
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