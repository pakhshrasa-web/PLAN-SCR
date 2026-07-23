# screens/admin_settings_screen.py
# ========== صفحه تنظیمات مدیریت با اسکرول دقیق ==========

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
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.checkbox import CheckBox
from utils.rtl_widgets import RTLTextInput, PersianComboBox, PersianButton, RTLLabel, PersianPopup
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
            
            # تغییر به resize برای اسکرول دقیق
            Window.softinput_mode = 'resize'
            
            # متغیر برای ذخیره فیلدهای قابل فوکوس
            self.focusable_fields = []
            
            self.build_ui()
            
            # اتصال رویدادهای کیبورد
            Window.bind(on_keyboard=self._on_keyboard)
            
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
                color=(1, 1, 1, 1),
                font_size=sp(14)
            )
            btn_password.bind(on_press=lambda x: self.switch_tab(3))
            tabs_layout.add_widget(btn_password)
            
            btn_codes = PersianButton(
                text='کدهای ثبت نام',
                background_color=(0.3, 0.5, 0.8, 0.6),
                size_hint_y=None,
                height=dp(34),
                color=(1, 1, 1, 1),
                font_size=sp(14)
            )
            btn_codes.bind(on_press=lambda x: self.switch_tab(1))
            tabs_layout.add_widget(btn_codes)
            
            btn_users = PersianButton(
                text='مدیریت کاربران',
                background_color=(0.3, 0.5, 0.8, 1),
                size_hint_y=None,
                height=dp(34),
                color=(1, 1, 1, 1),
                font_size=sp(14)
            )
            btn_users.bind(on_press=lambda x: self.switch_tab(0))
            tabs_layout.add_widget(btn_users)
            
            # تب خام سازی
            btn_clean = PersianButton(
                text='خام سازی',
                background_color=(0.8, 0.2, 0.2, 0.8),
                size_hint_y=None,
                height=dp(34),
                color=(1, 1, 1, 1),
                font_size=sp(14)
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
                color=(1, 1, 1, 1),
                font_size=sp(14)
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
            # ریست کردن لیست فیلدها برای هر تب جدید
            self.focusable_fields = []
            
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
    
    # ============================================================
    # مدیریت فوکوس و انتخاب خودکار متن
    # ============================================================
    
    def _on_field_focus(self, instance, value):
        """وقتی فیلد فوکوس میشه یا فوکوس رو از دست میده"""
        if value:
            Clock.schedule_once(lambda dt: self._select_all_text(instance), 0.1)
            # اسکرول با تأخیر برای اطمینان از نمایش کیبورد
            Clock.schedule_once(lambda dt: self._scroll_to_field(instance), 0.3)
    
    def _select_all_text(self, instance):
        """انتخاب کل متن فیلد"""
        if instance and hasattr(instance, 'select_all'):
            instance.select_all()
    
    def _scroll_to_field(self, instance):
        """اسکرول دقیق به موقعیت فیلد بالای کیبورد"""
        try:
            # پیدا کردن ScrollView در صفحه
            scroll = None
            for child in self.content_area.children:
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
            
            # ارتفاع قابل مشاهده صفحه
            window_height = Window.height
            
            # موقعیت هدف: بالای کیبورد با فاصله
            target_y = window_height - keyboard_height - dp(80)
            
            # محتوای ScrollView
            content_height = scroll.children[0].height if scroll.children else 1
            scroll_height = scroll.height
            
            if content_height > scroll_height:
                # اگر فیلد پایین‌تر از هدف بود، اسکرول کن
                if field_y > target_y:
                    # محاسبه نسبت اسکرول
                    field_ratio = (content_height - field_y) / content_height
                    scroll_value = min(0.95, max(0.05, field_ratio + 0.1))
                    scroll.scroll_y = scroll_value
                elif field_y < dp(50):
                    # فیلد خیلی بالاست، اسکرول به پایین
                    scroll.scroll_y = 0.9
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
    
    # ========== تب خام سازی ==========

    def show_clean_tab(self):
        """نمایش تب خام سازی داده‌ها با انتخاب نوع داده"""
        try:
            scroll = ScrollView(
                do_scroll_x=False,
                do_scroll_y=True,
                size_hint=(1, 1),
                scroll_type=['bars', 'content'],
                bar_width=dp(8)
            )
            
            layout = BoxLayout(
                orientation='vertical',
                padding=dp(15),
                spacing=dp(12),
                size_hint_y=None
            )
            layout.bind(minimum_height=layout.setter('height'))
            
            layout.add_widget(RTLLabel(
                text='خام سازی داده‌ها',
                size_hint_y=None,
                height=dp(45),
                font_size=sp(22),
                bold=True,
                color=(0.8, 0.2, 0.2, 1)
            ))
            
            layout.add_widget(RTLLabel(
                text='توجه: این عملیات غیرقابل بازگشت است. لطفاً با دقت انتخاب کنید.',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(14),
                color=(1, 0.8, 0.2, 1)
            ))
            
            layout.add_widget(RTLLabel(
                text='انتخاب دسته‌های داده برای خام سازی:',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(16),
                color=(0.4, 0.7, 1, 1),
                bold=True
            ))
            
            # ========== کامبوباکس انتخاب دسته‌ها ==========
            clean_options = [
                'ویزیت‌های روزانه بازاریاب (daily_log.json)',
                'خلاصه پایان کار بازاریاب (daily_summary.json)',
                'توزیع‌های روزانه موزع (delivery_sale.json)',
                'خلاصه پایان کار موزع (distributor_summary.json)',
                'تارگت‌ها (targets.json)',
                'سرکشی‌های سوپروایزر (supervisor_visits.json)',
                'عامل‌ها (agents)',
                'مسیرها (routes)',
                'مشتریان (customers)'
            ]
            
            # نگاشت نام نمایشی به کلید فایل
            self.clean_options_map = {
                'ویزیت‌های روزانه بازاریاب (daily_log.json)': 'daily_log',
                'خلاصه پایان کار بازاریاب (daily_summary.json)': 'daily_summary',
                'توزیع‌های روزانه موزع (delivery_sale.json)': 'delivery_sale',
                'خلاصه پایان کار موزع (distributor_summary.json)': 'distributor_summary',
                'تارگت‌ها (targets.json)': 'targets',
                'سرکشی‌های سوپروایزر (supervisor_visits.json)': 'supervisor_visits',
                'عامل‌ها (agents)': 'def_agents',
                'مسیرها (routes)': 'def_routes',
                'مشتریان (customers)': 'def_customers'
            }
            
            self.clean_selected = []
            
            self.clean_combo = PersianComboBox(
                text='انتخاب کنید...',
                values=clean_options,
                height=dp(70)
            )
            self.clean_combo.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.clean_combo.main_btn.color = (1, 1, 1, 1)
            self.clean_combo.main_btn.font_size = sp(18)
            layout.add_widget(self.clean_combo)
            
            # دکمه افزودن به لیست انتخاب
            add_btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
            
            add_btn = PersianButton(
                text='افزودن به لیست حذف',
                background_color=(0.2, 0.5, 0.9, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            add_btn.bind(on_press=self._add_to_clean_list)
            add_btn_layout.add_widget(add_btn)
            
            remove_btn = PersianButton(
                text='حذف از لیست',
                background_color=(0.8, 0.5, 0.2, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            remove_btn.bind(on_press=self._remove_from_clean_list)
            add_btn_layout.add_widget(remove_btn)
            
            layout.add_widget(add_btn_layout)
            
            # ========== لیست آیتم‌های انتخاب شده ==========
            layout.add_widget(RTLLabel(
                text='آیتم‌های انتخاب شده برای خام سازی:',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(16),
                color=(0.4, 0.7, 1, 1),
                bold=True
            ))
            
            self.selected_list_scroll = ScrollView(
                do_scroll_x=False,
                do_scroll_y=True,
                size_hint_y=0.35,
                scroll_type=['bars', 'content'],
                bar_width=dp(6)
            )
            
            self.selected_list = GridLayout(
                cols=1,
                spacing=dp(4),
                size_hint_y=None,
                padding=dp(5)
            )
            self.selected_list.bind(minimum_height=self.selected_list.setter('height'))
            
            self.selected_list_scroll.add_widget(self.selected_list)
            layout.add_widget(self.selected_list_scroll)
            
            # ========== دکمه‌های انتخاب همه و لغو همه ==========
            btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
            
            select_all_btn = PersianButton(
                text='انتخاب همه',
                background_color=(0.3, 0.3, 0.5, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            select_all_btn.bind(on_press=self._select_all_clean_items)
            btn_layout.add_widget(select_all_btn)
            
            clear_all_btn = PersianButton(
                text='پاک کردن لیست',
                background_color=(0.5, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            clear_all_btn.bind(on_press=self._clear_clean_list)
            btn_layout.add_widget(clear_all_btn)
            
            layout.add_widget(btn_layout)
            
            # ========== دکمه اصلی خام سازی ==========
            clean_btn = PersianButton(
                text='خام سازی انتخاب‌ها',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            clean_btn.bind(on_press=self.show_clean_confirm)
            layout.add_widget(clean_btn)
            
            scroll.add_widget(layout)
            self.content_area.add_widget(scroll)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش تب خام سازی: {e}", error_details)

    def _add_to_clean_list(self, instance):
        """افزودن آیتم انتخاب شده به لیست خام سازی"""
        try:
            selected_text = self.clean_combo.text
            if not selected_text or selected_text == 'انتخاب کنید...':
                self.show_message('خطا', 'لطفاً یک آیتم را انتخاب کنید')
                return
            
            if selected_text in self.clean_selected:
                self.show_message('توجه', 'این آیتم قبلاً انتخاب شده است')
                return
            
            self.clean_selected.append(selected_text)
            self._update_selected_list()
            
        except Exception as e:
            print(f"خطا در افزودن به لیست: {e}")

    def _remove_from_clean_list(self, instance):
        """حذف آیتم انتخاب شده از لیست خام سازی"""
        try:
            if not self.clean_selected:
                self.show_message('توجه', 'لیست خالی است')
                return
            
            # حذف آخرین آیتم
            removed = self.clean_selected.pop()
            self._update_selected_list()
            
        except Exception as e:
            print(f"خطا در حذف از لیست: {e}")

    def _update_selected_list(self):
        """به‌روزرسانی لیست نمایشی آیتم‌های انتخاب شده"""
        try:
            self.selected_list.clear_widgets()
            
            if not self.clean_selected:
                self.selected_list.add_widget(RTLLabel(
                    text='هیچ آیتمی انتخاب نشده است',
                    size_hint_y=None,
                    height=dp(35),
                    font_size=sp(14),
                    color=(0.5, 0.5, 0.5, 1)
                ))
                return
            
            for item in self.clean_selected:
                box = BoxLayout(size_hint_y=None, height=dp(35), spacing=dp(5))
                
                box.add_widget(RTLLabel(
                    text=f'• {item}',
                    size_hint_x=0.85,
                    size_hint_y=None,
                    height=dp(30),
                    font_size=sp(14),
                    color=(0.2, 0.8, 0.2, 1)
                ))
                
                remove_btn = PersianButton(
                    text='حذف',
                    size_hint_x=0.15,
                    size_hint_y=None,
                    height=dp(28),
                    background_color=(0.8, 0.2, 0.2, 1),
                    color=(1, 1, 1, 1),
                    font_size=sp(12)
                )
                remove_btn.bind(on_press=lambda x, i=item: self._remove_single_from_list(i))
                box.add_widget(remove_btn)
                
                self.selected_list.add_widget(box)
            
        except Exception as e:
            print(f"خطا در به‌روزرسانی لیست: {e}")

    def _remove_single_from_list(self, item):
        """حذف یک آیتم خاص از لیست"""
        try:
            if item in self.clean_selected:
                self.clean_selected.remove(item)
                self._update_selected_list()
        except Exception as e:
            print(f"خطا در حذف آیتم: {e}")

    def _select_all_clean_items(self, instance):
        """انتخاب همه آیتم‌ها"""
        try:
            all_items = [
                'ویزیت‌های روزانه بازاریاب (daily_log.json)',
                'خلاصه پایان کار بازاریاب (daily_summary.json)',
                'توزیع‌های روزانه موزع (delivery_sale.json)',
                'خلاصه پایان کار موزع (distributor_summary.json)',
                'تارگت‌ها (targets.json)',
                'سرکشی‌های سوپروایزر (supervisor_visits.json)',
                'عامل‌ها (agents)',
                'مسیرها (routes)',
                'مشتریان (customers)'
            ]
            self.clean_selected = all_items.copy()
            self._update_selected_list()
            self.show_message('توجه', f'{len(all_items)} آیتم انتخاب شد')
            
        except Exception as e:
            print(f"خطا در انتخاب همه: {e}")

    def _clear_clean_list(self, instance):
        """پاک کردن لیست انتخاب‌ها"""
        try:
            if not self.clean_selected:
                return
            self.clean_selected = []
            self._update_selected_list()
            self.show_message('توجه', 'لیست انتخاب‌ها پاک شد')
            
        except Exception as e:
            print(f"خطا در پاک کردن لیست: {e}")

    def show_clean_confirm(self, instance):
        """نمایش دیالوگ تأیید خام سازی با لیست انتخاب‌ها"""
        try:
            if not self.clean_selected:
                self.show_message('خطا', 'هیچ آیتمی برای خام سازی انتخاب نشده است')
                return
            
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            with content.canvas.before:
                Color(0.15, 0.15, 0.15, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                        size=lambda i, v: setattr(content_rect, 'size', v))
            
            content.add_widget(RTLLabel(
                text='هشدار: این عملیات غیرقابل بازگشت است!',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(18),
                color=(0.8, 0.2, 0.2, 1)
            ))
            
            content.add_widget(RTLLabel(
                text='آیتم‌های انتخاب شده برای حذف:',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))
            
            list_scroll = ScrollView(
                do_scroll_x=False,
                do_scroll_y=True,
                size_hint_y=0.3
            )
            list_content = GridLayout(
                cols=1,
                spacing=dp(3),
                size_hint_y=None,
                padding=dp(5)
            )
            list_content.bind(minimum_height=list_content.setter('height'))
            
            for item in self.clean_selected:
                list_content.add_widget(RTLLabel(
                    text=f'• {item}',
                    size_hint_y=None,
                    height=dp(25),
                    font_size=sp(14),
                    color=(1, 0.8, 0.2, 1)
                ))
            
            list_scroll.add_widget(list_content)
            content.add_widget(list_scroll)
            
            content.add_widget(RTLLabel(
                text='برای تأیید، عبارت "حذف" را وارد کنید:',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            
            self.confirm_clean_input = RTLTextInput(
                hint_text='عبارت تأیید',
                multiline=False,
                size_hint_y=None,
                height=dp(70),
                font_size=sp(32)
            )
            self.confirm_clean_input.bg_color = (0.15, 0.15, 0.15, 1)
            self.confirm_clean_input.border_color = (0.3, 0.3, 0.3, 1)
            self.confirm_clean_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.confirm_clean_input._hidden_input.foreground_color = (1, 1, 1, 1)
            
            self.confirm_clean_input._hidden_input.bind(focus=self._on_field_focus)
            self.focusable_fields.append(self.confirm_clean_input._hidden_input)
            
            content.add_widget(self.confirm_clean_input)
            
            btn_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(50))
            
            clean_btn = PersianButton(
                text='حذف انتخاب‌ها',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            cancel_btn = PersianButton(
                text='انصراف',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            
            btn_layout.add_widget(clean_btn)
            btn_layout.add_widget(cancel_btn)
            content.add_widget(btn_layout)
            
            popup = PersianPopup(
                title='تأیید خام سازی',
                content=content,
                size_hint=(0.85, 0.6),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )
            
            def do_clean(instance):
                if self.confirm_clean_input.text.strip() != 'حذف':
                    self.show_message('خطا', 'عبارت تأیید اشتباه است')
                    return
                popup.dismiss()
                self._perform_clean_selected()
            
            def on_cancel(instance):
                popup.dismiss()
            
            clean_btn.bind(on_press=do_clean)
            cancel_btn.bind(on_press=on_cancel)
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش دیالوگ تأیید: {e}", error_details)

    def _perform_clean_selected(self):
        """اجرای خام سازی بر اساس آیتم‌های انتخاب شده"""
        try:
            from utils.file_manager import load_json, save_json
            
            data_path = get_data_path()
            cleaned = []
            errors = []
            
            item_keys = {
                'ویزیت‌های روزانه بازاریاب (daily_log.json)': 'daily_log',
                'خلاصه پایان کار بازاریاب (daily_summary.json)': 'daily_summary',
                'توزیع‌های روزانه موزع (delivery_sale.json)': 'delivery_sale',
                'خلاصه پایان کار موزع (distributor_summary.json)': 'distributor_summary',
                'تارگت‌ها (targets.json)': 'targets',
                'سرکشی‌های سوپروایزر (supervisor_visits.json)': 'supervisor_visits',
                'عامل‌ها (agents)': 'def_agents',
                'مسیرها (routes)': 'def_routes',
                'مشتریان (customers)': 'def_customers'
            }
            
            for item in self.clean_selected:
                key = item_keys.get(item)
                if not key:
                    continue
                    
                try:
                    if key == 'daily_log':
                        save_json('daily_log.json', {})
                        cleaned.append(item)
                        
                    elif key == 'daily_summary':
                        save_json('daily_summary.json', {})
                        cleaned.append(item)
                        
                    elif key == 'delivery_sale':
                        save_json('delivery_sale.json', {})
                        cleaned.append(item)
                        
                    elif key == 'distributor_summary':
                        save_json('distributor_summary.json', {})
                        cleaned.append(item)
                        
                    elif key == 'targets':
                        save_json('targets.json', {'targets': []})
                        cleaned.append(item)
                        
                    elif key == 'supervisor_visits':
                        save_json('supervisor_visits.json', {'visits': []})
                        cleaned.append(item)
                        
                    elif key == 'def_agents':
                        data = load_json('definitions.json')
                        if data:
                            data['agents'] = []
                            save_json('definitions.json', data)
                            cleaned.append(item)
                        else:
                            errors.append(f'{item}: فایل definitions.json یافت نشد')
                            
                    elif key == 'def_routes':
                        data = load_json('definitions.json')
                        if data:
                            data['routes'] = []
                            save_json('definitions.json', data)
                            cleaned.append(item)
                        else:
                            errors.append(f'{item}: فایل definitions.json یافت نشد')
                            
                    elif key == 'def_customers':
                        data = load_json('definitions.json')
                        if data:
                            data['customers'] = []
                            save_json('definitions.json', data)
                            cleaned.append(item)
                        else:
                            errors.append(f'{item}: فایل definitions.json یافت نشد')
                            
                except Exception as e:
                    errors.append(f"{item}: {str(e)}")
            
            # پاک کردن لیست انتخاب‌ها
            self.clean_selected = []
            self._update_selected_list()
            
            if cleaned:
                message = 'آیتم‌های زیر با موفقیت خام سازی شدند:\n' + '\n'.join(f'• {c}' for c in cleaned)
                if errors:
                    message += '\n\nخطاها:\n' + '\n'.join(f'• {e}' for e in errors)
                self.show_message('نتیجه خام سازی', message)
            else:
                self.show_message('خطا', 'هیچ آیتمی خام سازی نشد.\n' + '\n'.join(errors))
            
            self.switch_tab(4)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در خام سازی: {e}", error_details)
    
    # ========== تب تغییر رمز ==========
    
    def show_change_password_tab(self):
        try:
            # استفاده از ScrollView برای نمایش کامل محتوا
            scroll = ScrollView(
                do_scroll_x=False,
                do_scroll_y=True,
                size_hint=(1, 1),
                scroll_type=['bars', 'content'],
                bar_width=dp(8)
            )
            
            layout = BoxLayout(
                orientation='vertical',
                padding=dp(15),
                spacing=dp(8),
                size_hint_y=None
            )
            layout.bind(minimum_height=layout.setter('height'))
            
            layout.add_widget(RTLLabel(
                text='تغییر رمز عبور مدیر',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(18),
                bold=True,
                color=(1, 1, 1, 1)
            ))
            
            layout.add_widget(Label(size_hint_y=None, height=dp(2)))
            
            layout.add_widget(RTLLabel(
                text='رمز عبور فعلی:',
                size_hint_y=None,
                height=dp(25),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            self.old_password = RTLTextInput(
                password=True,
                multiline=False,
                size_hint_y=None,
                height=dp(80),
                font_size=sp(32),
                hint_text='رمز عبور فعلی را وارد کنید'
            )
            self.old_password.bg_color = (0.15, 0.15, 0.15, 1)
            self.old_password.border_color = (0.3, 0.3, 0.3, 1)
            self.old_password.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.old_password._hidden_input.foreground_color = (1, 1, 1, 1)
            
            # اتصال رویداد فوکوس
            self.old_password._hidden_input.bind(focus=self._on_field_focus)
            self.focusable_fields.append(self.old_password._hidden_input)
            
            layout.add_widget(self.old_password)
            
            layout.add_widget(Label(size_hint_y=None, height=dp(2)))
            
            layout.add_widget(RTLLabel(
                text='رمز عبور جدید:',
                size_hint_y=None,
                height=dp(25),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            self.new_password = RTLTextInput(
                password=True,
                multiline=False,
                size_hint_y=None,
                height=dp(80),
                font_size=sp(32),
                hint_text='رمز عبور جدید را وارد کنید'
            )
            self.new_password.bg_color = (0.15, 0.15, 0.15, 1)
            self.new_password.border_color = (0.3, 0.3, 0.3, 1)
            self.new_password.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.new_password._hidden_input.foreground_color = (1, 1, 1, 1)
            
            # اتصال رویداد فوکوس
            self.new_password._hidden_input.bind(focus=self._on_field_focus)
            self.focusable_fields.append(self.new_password._hidden_input)
            
            layout.add_widget(self.new_password)
            
            layout.add_widget(Label(size_hint_y=None, height=dp(2)))
            
            layout.add_widget(RTLLabel(
                text='تکرار رمز عبور جدید:',
                size_hint_y=None,
                height=dp(25),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            self.confirm_password = RTLTextInput(
                password=True,
                multiline=False,
                size_hint_y=None,
                height=dp(80),
                font_size=sp(32),
                hint_text='تکرار رمز عبور جدید'
            )
            self.confirm_password.bg_color = (0.15, 0.15, 0.15, 1)
            self.confirm_password.border_color = (0.3, 0.3, 0.3, 1)
            self.confirm_password.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.confirm_password._hidden_input.foreground_color = (1, 1, 1, 1)
            
            # اتصال رویداد فوکوس
            self.confirm_password._hidden_input.bind(focus=self._on_field_focus)
            self.focusable_fields.append(self.confirm_password._hidden_input)
            
            layout.add_widget(self.confirm_password)
            
            layout.add_widget(Label(size_hint_y=None, height=dp(5)))
            
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
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            save_btn.bind(on_press=self.change_password)
            btn_layout.add_widget(save_btn)
            
            clear_btn = PersianButton(
                text='پاک کردن',
                background_color=(0.8, 0.5, 0.2, 1),
                size_hint_y=None,
                height=dp(42),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            clear_btn.bind(on_press=self.clear_password_fields)
            btn_layout.add_widget(clear_btn)
            
            layout.add_widget(btn_layout)
            
            scroll.add_widget(layout)
            self.content_area.add_widget(scroll)
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
    
    # ========== تب کاربران ==========
    
    def show_users_tab(self):
        try:
            users = get_users()
            
            # ScrollView با تنظیمات بهتر
            scroll = ScrollView(
                do_scroll_x=False,
                do_scroll_y=True,
                size_hint=(1, 1),
                scroll_type=['bars', 'content'],
                bar_width=dp(8)
            )
            
            content = GridLayout(
                cols=1,
                spacing=dp(5),
                size_hint_y=None,
                padding=dp(5)
            )
            content.bind(minimum_height=content.setter('height'))
            
            content.add_widget(Label(size_hint_y=None, height=dp(5)))
            
            content.add_widget(RTLLabel(
                text='لیست کاربران',
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
                    height=dp(55),
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
                    height=dp(38),
                    color=(1, 1, 1, 1),
                    font_size=sp(14)
                )
                del_btn.bind(on_press=lambda x, uid=user.get('id'): self.delete_user(uid))
                user_box.add_widget(del_btn)
                content.add_widget(user_box)
            
            scroll.add_widget(content)
            self.content_area.add_widget(scroll)
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
                background_color=(0.8, 0.2, 0.2, 1),
                font_size=sp(14)
            )
            no_btn = PersianButton(
                text='خیر، انصراف',
                size_hint_y=None,
                height=dp(40),
                color=(1, 1, 1, 1),
                background_color=(0.3, 0.3, 0.3, 1),
                font_size=sp(14)
            )
            btn_layout.add_widget(yes_btn)
            btn_layout.add_widget(no_btn)
            content.add_widget(btn_layout)
            
            popup = PersianPopup(
                title='تایید حذف',
                content=content,
                size_hint=(0.8, 0.35),
                background_color=(0.08, 0.08, 0.08, 1)
            )
            
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
    
    # ========== تب کدها ==========
    
    def show_codes_tab(self):
        try:
            roles = ['مدیر', 'ادمین', 'سوپروایزر', 'بازاریاب', 'حسابدار', 'موزع', 'راننده', 'انباردار', 'سایر']
            
            # ScrollView با تنظیمات بهتر
            scroll = ScrollView(
                do_scroll_x=False,
                do_scroll_y=True,
                size_hint=(1, 1),
                scroll_type=['bars', 'content'],
                bar_width=dp(8)
            )
            
            content = GridLayout(
                cols=1,
                spacing=dp(4),
                size_hint_y=None,
                padding=dp(5)
            )
            content.bind(minimum_height=content.setter('height'))
            
            content.add_widget(Label(size_hint_y=None, height=dp(5)))
            
            content.add_widget(RTLLabel(
                text='ساخت کد ثبت نام جدید',
                size_hint_y=None,
                height=dp(32),
                font_size=sp(16),
                bold=True,
                color=(1, 1, 1, 1)
            ))
            
            self.role_spinner = PersianComboBox(
                text='مدیر',
                values=roles,
                height=dp(65)
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
                height=dp(80),
                font_size=sp(32)
            )
            self.code_name_input.bg_color = (0.15, 0.15, 0.15, 1)
            self.code_name_input.border_color = (0.3, 0.3, 0.3, 1)
            self.code_name_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.code_name_input._hidden_input.foreground_color = (1, 1, 1, 1)
            
            # اتصال رویداد فوکوس
            self.code_name_input._hidden_input.bind(focus=self._on_field_focus)
            self.focusable_fields.append(self.code_name_input._hidden_input)
            
            content.add_widget(self.code_name_input)
            
            create_btn = PersianButton(
                text='ساخت کد',
                size_hint_y=None,
                height=dp(45),
                background_color=(0.2, 0.7, 0.2, 1),
                color=(1, 1, 1, 1),
                font_size=sp(16)
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
          
            content.add_widget(Label(size_hint_y=None, height=dp(8)))
            
            content.add_widget(RTLLabel(
                text='کدهای فعال',
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
                        height=dp(40),
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
            
            scroll.add_widget(content)
            self.content_area.add_widget(scroll)
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش کدها: {e}", error_details)
    
    def show_general_settings_tab(self):
        pass
    
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
                font_size=sp(20),
                color=(1, 1, 1, 1)
            ))
            btn = PersianButton(
                text='باشه',
                size_hint_y=None,
                height=dp(55),
                font_size=sp(20),
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
    
    def go_back(self, instance):
        self.manager.current = 'login'