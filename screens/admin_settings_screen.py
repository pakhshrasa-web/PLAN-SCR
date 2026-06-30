# screens/admin_settings_screen.py
# ========== صفحه تنظیمات مدیریت ==========

import traceback
import os
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, Rectangle

from utils.rtl_widgets import RTLTextInput, PersianComboBox, PersianButton, RTLLabel
from utils.user_manager import get_users, delete_user_by_id, get_codes, create_code
from utils.auth import get_admin_password, set_admin_password, verify_password
from utils.file_manager import load_json, save_json, get_daily_logs, get_data_path
from error_handler import ErrorPopup
from constants import ROLES


class AdminSettingsScreen(Screen):
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
            ErrorPopup.show_error(f"خطا در ساخت AdminSettingsScreen: {e}", error_details)
            raise
    
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def build_ui(self):
        try:
            layout = BoxLayout(orientation='vertical', padding=[dp(5), dp(5), dp(5), dp(5)])
            
            # ========== تب‌ها ==========
            tabs_layout = BoxLayout(
                size_hint_y=None,
                height=dp(38),
                spacing=dp(2)
            )
            
            btn_password = PersianButton(
                text='تغییر رمز',
                background_color=(0.3, 0.5, 0.8, 0.6),
                size_hint_y=None,
                height=dp(34),
                color=(1, 1, 1, 1)
            )
            btn_password.bind(on_press=lambda x: self.switch_tab(3))
            tabs_layout.add_widget(btn_password)
            
            btn_codes = PersianButton(
                text='کدهای ثبت نام',
                background_color=(0.3, 0.5, 0.8, 0.6),
                size_hint_y=None,
                height=dp(34),
                color=(1, 1, 1, 1)
            )
            btn_codes.bind(on_press=lambda x: self.switch_tab(1))
            tabs_layout.add_widget(btn_codes)
            
            btn_users = PersianButton(
                text='مدیریت کاربران',
                background_color=(0.3, 0.5, 0.8, 1),
                size_hint_y=None,
                height=dp(34),
                color=(1, 1, 1, 1)
            )
            btn_users.bind(on_press=lambda x: self.switch_tab(0))
            tabs_layout.add_widget(btn_users)
            
            # ✅ تب خام سازی
            btn_clean = PersianButton(
                text='🧹 خام سازی',
                background_color=(0.8, 0.2, 0.2, 0.8),
                size_hint_y=None,
                height=dp(34),
                color=(1, 1, 1, 1)
            )
            btn_clean.bind(on_press=lambda x: self.switch_tab(4))
            tabs_layout.add_widget(btn_clean)
            
            layout.add_widget(tabs_layout)
            
            # ========== محتوای تب‌ها ==========
            self.content_area = BoxLayout(orientation='vertical')
            layout.add_widget(self.content_area)
            
            # ========== دکمه بازگشت ==========
            back_btn = PersianButton(
                text='بازگشت',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(36),
                color=(1, 1, 1, 1)
            )
            back_btn.bind(on_press=self.go_back)
            layout.add_widget(back_btn)
            
            self.add_widget(layout)
            self.switch_tab(0)
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت UI AdminSettingsScreen: {e}", error_details)
            raise
    
    def switch_tab(self, tab_id):
        try:
            self.content_area.clear_widgets()
            
            if tab_id == 0:
                self.show_users_tab()
            elif tab_id == 1:
                self.show_codes_tab()
            elif tab_id == 2:
                self.show_general_settings_tab()
            elif tab_id == 3:
                self.show_change_password_tab()
            elif tab_id == 4:
                self.show_clean_tab()
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در تغییر تب: {e}", error_details)
    
    # ========== تب خام سازی ==========
    
    def show_clean_tab(self):
        """نمایش تب خام سازی داده‌ها"""
        try:
            layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(15))
            
            layout.add_widget(RTLLabel(
                text='🧹 خام سازی داده‌های کاربران',
                size_hint_y=None,
                height=dp(45),
                font_size=sp(20),
                bold=True,
                color=(0.8, 0.2, 0.2, 1)
            ))
            
            layout.add_widget(RTLLabel(
                text='⚠️ توجه: این عملیات تمام داده‌های ثبت شده توسط کاربران عادی را حذف می‌کند.\nداده‌های مدیریتی (کاربران، تنظیمات، مسیرها، مشتریان و کدها) حفظ می‌شوند.',
                size_hint_y=None,
                height=dp(60),
                font_size=sp(14),
                color=(1, 0.8, 0.2, 1)
            ))
            
            # نمایش آمار داده‌ها
            stats_box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(100), spacing=dp(5))
            
            daily_logs = get_daily_logs()
            total_visits = 0
            for date, logs in daily_logs.items():
                if isinstance(logs, list):
                    total_visits += len(logs)
            
            stats_box.add_widget(RTLLabel(
                text=f'📊 تعداد روزهای دارای داده: {len(daily_logs)}',
                size_hint_y=None,
                height=dp(25),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))
            stats_box.add_widget(RTLLabel(
                text=f'📊 تعداد کل ویزیت‌ها: {total_visits}',
                size_hint_y=None,
                height=dp(25),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))
            
            # بررسی فایل خلاصه
            summary_path = os.path.join(get_data_path(), 'daily_summary.json')
            if os.path.exists(summary_path):
                stats_box.add_widget(RTLLabel(
                    text='📊 فایل خلاصه روزانه: موجود',
                    size_hint_y=None,
                    height=dp(25),
                    font_size=sp(16),
                    color=(0.2, 0.7, 0.2, 1)
                ))
            else:
                stats_box.add_widget(RTLLabel(
                    text='📊 فایل خلاصه روزانه: وجود ندارد',
                    size_hint_y=None,
                    height=dp(25),
                    font_size=sp(16),
                    color=(0.5, 0.5, 0.5, 1)
                ))
            
            layout.add_widget(stats_box)
            
            # دکمه خام سازی
            clean_btn = PersianButton(
                text='🗑️ حذف همه داده‌های کاربران',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            clean_btn.bind(on_press=self.show_clean_confirm)
            layout.add_widget(clean_btn)
            
            self.content_area.add_widget(layout)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش تب خام سازی: {e}", error_details)
    
    def show_clean_confirm(self, instance):
        """نمایش دیالوگ تأیید خام سازی"""
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            with content.canvas.before:
                Color(0.15, 0.15, 0.15, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                           size=lambda i, v: setattr(content_rect, 'size', v))
            
            content.add_widget(RTLLabel(
                text='⚠️ هشدار: این عملیات غیرقابل بازگشت است!\nآیا از حذف تمام داده‌های کاربران اطمینان دارید؟',
                size_hint_y=None,
                height=dp(60),
                font_size=sp(18),
                color=(0.8, 0.2, 0.2, 1)
            ))
            
            # فیلد تأیید
            content.add_widget(RTLLabel(
                text='برای تأیید، عبارت "حذف" را وارد کنید:',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            
            confirm_input = RTLTextInput(
                hint_text='عبارت تأیید',
                multiline=False,
                size_hint_y=None,
                height=dp(45),
                font_size=sp(36)
            )
            confirm_input.foreground_color = (1, 1, 1, 1)
            confirm_input.background_color = (0.2, 0.2, 0.2, 1)
            confirm_input.hint_text_color = (0.5, 0.5, 0.5, 1)
            content.add_widget(confirm_input)
            
            btn_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(50))
            
            clean_btn = PersianButton(
                text='🗑️ حذف همه',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1)
            )
            cancel_btn = PersianButton(
                text='❌ انصراف',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1)
            )
            
            btn_layout.add_widget(clean_btn)
            btn_layout.add_widget(cancel_btn)
            content.add_widget(btn_layout)
            
            popup = Popup(
                title='🧹 تأیید خام سازی',
                content=content,
                size_hint=(0.85, 0.55),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )
            popup.title_color = (1, 1, 1, 1)
            
            def do_clean(instance):
                if confirm_input.text.strip() != 'حذف':
                    self.show_message('خطا', 'عبارت تأیید اشتباه است')
                    return
                popup.dismiss()
                self._perform_clean()
            
            def on_cancel(instance):
                popup.dismiss()
            
            clean_btn.bind(on_press=do_clean)
            cancel_btn.bind(on_press=on_cancel)
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش دیالوگ تأیید: {e}", error_details)
    
    def _perform_clean(self):
        """اجرای واقعی خام سازی"""
        try:
            data_path = get_data_path()
            
            # فایل‌هایی که باید پاک بشن (داده‌های کاربران)
            files_to_clean = ['daily_log.json', 'daily_summary.json']
            
            for filename in files_to_clean:
                filepath = os.path.join(data_path, filename)
                if os.path.exists(filepath):
                    if filename == 'daily_log.json':
                        save_json(filename, {})
                    elif filename == 'daily_summary.json':
                        save_json(filename, {})
                    print(f"✅ {filename} خام سازی شد")
            
            self.show_message('✅ موفق', 'تمامی داده‌های کاربران با موفقیت حذف شدند')
            self.switch_tab(4)  # رفرش تب
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در خام سازی: {e}", error_details)
    
    def show_change_password_tab(self):
        try:
            layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
            
            layout.add_widget(RTLLabel(
                text='تغییر رمز عبور مدیر',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(18),
                bold=True,
                color=(1, 1, 1, 1)
            ))
            
            layout.add_widget(RTLLabel(
                text='رمز عبور فعلی:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            self.old_password = RTLTextInput(
                password=True,
                multiline=False,
                size_hint_y=None,
                height=dp(50),
                font_size=sp(36),
                hint_text='رمز عبور فعلی را وارد کنید'
            )
            self.old_password.foreground_color = (1, 1, 1, 1)
            self.old_password.background_color = (0.2, 0.2, 0.2, 1)
            self.old_password.hint_text_color = (0.5, 0.5, 0.5, 1)
            layout.add_widget(self.old_password)
            
            layout.add_widget(RTLLabel(
                text='رمز عبور جدید:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            self.new_password = RTLTextInput(
                password=True,
                multiline=False,
                size_hint_y=None,
                height=dp(50),
                font_size=sp(36),
                hint_text='رمز عبور جدید را وارد کنید'
            )
            self.new_password.foreground_color = (1, 1, 1, 1)
            self.new_password.background_color = (0.2, 0.2, 0.2, 1)
            self.new_password.hint_text_color = (0.5, 0.5, 0.5, 1)
            layout.add_widget(self.new_password)
            
            layout.add_widget(RTLLabel(
                text='تکرار رمز عبور جدید:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            self.confirm_password = RTLTextInput(
                password=True,
                multiline=False,
                size_hint_y=None,
                height=dp(50),
                font_size=sp(36),
                hint_text='تکرار رمز عبور جدید'
            )
            self.confirm_password.foreground_color = (1, 1, 1, 1)
            self.confirm_password.background_color = (0.2, 0.2, 0.2, 1)
            self.confirm_password.hint_text_color = (0.5, 0.5, 0.5, 1)
            layout.add_widget(self.confirm_password)
            
            btn_layout = BoxLayout(
                spacing=dp(10),
                size_hint_y=None,
                height=dp(48),
                padding=(0, dp(8), 0, 0)
            )
            
            save_btn = PersianButton(
                text='تغییر رمز',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(42),
                color=(1, 1, 1, 1)
            )
            save_btn.bind(on_press=self.change_password)
            btn_layout.add_widget(save_btn)
            
            clear_btn = PersianButton(
                text='پاک کردن',
                background_color=(0.8, 0.5, 0.2, 1),
                size_hint_y=None,
                height=dp(42),
                color=(1, 1, 1, 1)
            )
            clear_btn.bind(on_press=self.clear_password_fields)
            btn_layout.add_widget(clear_btn)
            
            layout.add_widget(btn_layout)
            self.content_area.add_widget(layout)
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش تب تغییر رمز: {e}", error_details)
    
    def change_password(self, instance):
        try:
            old = self.old_password.text
            new = self.new_password.text
            confirm = self.confirm_password.text
            
            hashed = get_admin_password()
            if not hashed or not verify_password(old, hashed):
                self.show_message('خطا', 'رمز عبور فعلی اشتباه است')
                return
            
            if len(new) < 6:
                self.show_message('خطا', 'رمز عبور جدید باید حداقل 6 کاراکتر باشد')
                return
            
            if new != confirm:
                self.show_message('خطا', 'رمز عبور جدید و تکرار آن مطابقت ندارند')
                return
            
            set_admin_password(new)
            self.clear_password_fields(instance)
            self.show_message('موفق', 'رمز عبور با موفقیت تغییر کرد')
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در تغییر رمز: {e}", error_details)
    
    def clear_password_fields(self, instance):
        self.old_password.text = ''
        self.new_password.text = ''
        self.confirm_password.text = ''
    
    def show_users_tab(self):
        try:
            users = get_users()
            
            layout = ScrollView()
            content = GridLayout(
                cols=1,
                spacing=dp(5),
                size_hint_y=None,
                padding=dp(5)
            )
            content.bind(minimum_height=content.setter('height'))
            
            content.add_widget(Label(size_hint_y=None, height=dp(5)))
            
            content.add_widget(RTLLabel(
                text='📋 لیست کاربران',
                size_hint_y=None,
                height=dp(32),
                font_size=sp(16),
                bold=True,
                color=(1, 1, 1, 1)
            ))
            
            if not users:
                content.add_widget(RTLLabel(
                    text='هیچ کاربری ثبت نشده است',
                    size_hint_y=None,
                    height=dp(32),
                    font_size=sp(14),
                    color=(0.5, 0.5, 0.5, 1)
                ))
            
            for user in users:
                user_box = BoxLayout(
                    size_hint_y=None,
                    height=dp(50),
                    spacing=dp(5)
                )
                
                info = f"{user.get('username', '')} | {user.get('name', '')} | {user.get('role', '')}"
                user_info = RTLLabel(
                    text=info,
                    size_hint_x=0.7,
                    font_size=sp(13),
                    color=(1, 1, 1, 1)
                )
                user_box.add_widget(user_info)
                
                del_btn = PersianButton(
                    text='حذف',
                    size_hint_x=0.3,
                    background_color=(0.8, 0.2, 0.2, 1),
                    size_hint_y=None,
                    height=dp(32),
                    color=(1, 1, 1, 1)
                )
                del_btn.bind(on_press=lambda x, uid=user.get('id'): self.delete_user(uid))
                user_box.add_widget(del_btn)
                content.add_widget(user_box)
            
            layout.add_widget(content)
            self.content_area.add_widget(layout)
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش کاربران: {e}", error_details)
    
    def delete_user(self, user_id):
        try:
            users = get_users()
            username = ""
            for user in users:
                if user.get('id') == user_id:
                    username = user.get('username', '')
                    break
            
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            with content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                           size=lambda i, v: setattr(content_rect, 'size', v))
            
            content.add_widget(RTLLabel(
                text=f'آیا از حذف کاربر "{username}" مطمئن هستید؟',
                size_hint_y=None,
                height=dp(45),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))
            
            btn_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(45))
            yes_btn = PersianButton(
                text='بله، حذف شود',
                size_hint_y=None,
                height=dp(40),
                color=(1, 1, 1, 1),
                background_color=(0.8, 0.2, 0.2, 1)
            )
            no_btn = PersianButton(
                text='خیر، انصراف',
                size_hint_y=None,
                height=dp(40),
                color=(1, 1, 1, 1),
                background_color=(0.3, 0.3, 0.3, 1)
            )
            btn_layout.add_widget(yes_btn)
            btn_layout.add_widget(no_btn)
            content.add_widget(btn_layout)
            
            popup = Popup(
                title='تایید حذف',
                content=content,
                size_hint=(0.8, 0.35),
                background_color=(0.08, 0.08, 0.08, 1)
            )
            popup.title_color = (1, 1, 1, 1)
            
            def do_delete(instance):
                delete_user_by_id(user_id)
                popup.dismiss()
                self.show_message('موفق', f'کاربر "{username}" با موفقیت حذف شد')
                self.switch_tab(0)
            
            def cancel_delete(instance):
                popup.dismiss()
            
            yes_btn.bind(on_press=do_delete)
            no_btn.bind(on_press=cancel_delete)
            popup.open()
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در حذف کاربر: {e}", error_details)
    
    def show_codes_tab(self):
        try:
            roles = ['مدیر', 'ادمین', 'سوپروایزر', 'بازاریاب', 'حسابدار', 'موزع', 'راننده', 'انباردار', 'سایر']
            
            layout = ScrollView()
            content = GridLayout(
                cols=1,
                spacing=dp(4),
                size_hint_y=None,
                padding=dp(5)
            )
            content.bind(minimum_height=content.setter('height'))
            
            content.add_widget(Label(size_hint_y=None, height=dp(5)))
            
            self.role_spinner = PersianComboBox(
                text='مدیر',
                values=roles,
                height=dp(45)
            )
            self.role_spinner.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.role_spinner.main_btn.color = (1, 1, 1, 1)
            self.role_spinner.main_btn.font_size = sp(18)
            content.add_widget(self.role_spinner)
            
            content.add_widget(Label(size_hint_y=None, height=dp(2)))
            
            self.code_name_input = RTLTextInput(
                hint_text='نام و نام خانوادگی',
                multiline=False,
                size_hint_y=None,
                height=dp(50),
                font_size=sp(36)
            )
            self.code_name_input.foreground_color = (1, 1, 1, 1)
            self.code_name_input.background_color = (0.2, 0.2, 0.2, 1)
            self.code_name_input.hint_text_color = (0.5, 0.5, 0.5, 1)
            content.add_widget(self.code_name_input)
            
            create_btn = PersianButton(
                text='ساخت کد',
                size_hint_y=None,
                height=dp(45),
                background_color=(0.2, 0.7, 0.2, 1),
                color=(1, 1, 1, 1)
            )
            content.add_widget(create_btn)
            
            def do_create(instance):
                try:
                    selected_role = self.role_spinner.text
                    name = self.code_name_input.text
                    
                    if not name:
                        self.show_message('خطا', 'لطفاً نام و نام خانوادگی را وارد کنید')
                        return
                    
                    code = create_code(selected_role, name)
                    self.show_message('موفق', f'کد ساخته شد:\n{code}')
                    self.code_name_input.text = ''
                    self.switch_tab(1)
                except Exception as e:
                    error_details = traceback.format_exc()
                    ErrorPopup.show_error(f"خطا در ساخت کد: {e}", error_details)
            
            create_btn.bind(on_press=do_create)
          
            content.add_widget(RTLLabel(
                text='📋 کدهای فعال',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(16),
                bold=True,
                color=(1, 1, 1, 1)
            ))
            
            codes = get_codes()
            has_codes = False
            for code_info in codes:
                if not code_info.get('used', False):
                    has_codes = True
                    code_box = BoxLayout(
                        size_hint_y=None,
                        height=dp(35),
                        spacing=dp(5)
                    )
                    code_text = f"{code_info['code']} - {code_info['role']} - {code_info['name']}"
                    code_label = RTLLabel(
                        text=code_text,
                        size_hint_x=1,
                        font_size=sp(14),
                        color=(1, 1, 1, 1)
                    )
                    code_box.add_widget(code_label)
                    content.add_widget(code_box)
            
            if not has_codes:
                content.add_widget(RTLLabel(
                    text='هیچ کد فعالی وجود ندارد',
                    size_hint_y=None,
                    height=dp(35),
                    font_size=sp(14),
                    color=(0.5, 0.5, 0.5, 1)
                ))
            
            layout.add_widget(content)
            self.content_area.add_widget(layout)
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش کدها: {e}", error_details)
    
    def show_general_settings_tab(self):
        pass
    
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
                height=dp(45),
                font_size=sp(16),
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
    
    def go_back(self, instance):
        self.manager.current = 'login'
