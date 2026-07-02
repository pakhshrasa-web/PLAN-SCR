# screens/admin_screen.py
# ========== صفحه مدیریت ==========

import traceback
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
from kivy.logger import Logger as logger
import os

from utils.rtl_widgets import RTLTextInput, PersianComboBox, PersianButton, RTLLabel
from utils.file_manager import (
    get_agents, add_agent, delete_agent,
    get_routes, add_route, delete_route,
    get_customers, add_customer, delete_customer,
    get_settings, update_settings
)
from utils.jalali_date import get_today_jalali
from utils.excel_importer import import_routes_from_excel, import_customers_from_excel
from utils.file_picker import FilePicker
from error_handler import ErrorPopup
from constants import ROLES


class AdminScreen(Screen):
    """صفحه مدیریت - فقط رابط کاربری"""

    def __init__(self, **kwargs):
        try:
            super().__init__(**kwargs)
            with self.canvas.before:
                Color(0.08, 0.08, 0.08, 1)
                self.bg_rect = Rectangle(pos=self.pos, size=self.size)
                self.bind(pos=self._update_bg, size=self._update_bg)
            
            Window.softinput_mode = 'resize'
            self.focusable_fields = []
            self.current_tab = 0
            self.build_ui()
            Window.bind(on_keyboard=self._on_keyboard)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت AdminScreen: {e}", error_details)
            raise
    
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
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
            scroll = None
            for child in self.content_area.children:
                if isinstance(child, ScrollView):
                    scroll = child
                    break
            
            if not scroll:
                return
            
            field_pos = instance.to_window(0, 0)
            field_y = field_pos[1]
            keyboard_height = 250
            window_height = Window.height
            target_y = window_height - keyboard_height - dp(80)
            
            content_height = scroll.children[0].height if scroll.children else 1
            scroll_height = scroll.height
            
            if content_height > scroll_height:
                if field_y > target_y:
                    field_ratio = (content_height - field_y) / content_height
                    scroll_value = min(0.95, max(0.05, field_ratio + 0.1))
                    scroll.scroll_y = scroll_value
                elif field_y < dp(50):
                    scroll.scroll_y = 0.9
        except Exception as e:
            logger.warning(f"⚠️ خطا در اسکرول: {e}")
    
    # ============================================================
    # ✅ مدیریت کیبورد
    # ============================================================
    
    def _on_keyboard(self, window, key, *args):
        if key == 9:
            self._focus_next()
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
    
    def build_ui(self):
        try:
            main_layout = BoxLayout(orientation='vertical', padding=[dp(5), dp(5), dp(5), dp(5)])
            
            # ========== تب‌ها ==========
            tabs_layout = BoxLayout(
                size_hint_y=None,
                height=dp(38),
                spacing=dp(2)
            )
            
            btn_settings = PersianButton(
                text='⚙️ تنظیمات',
                background_color=(0.3, 0.5, 0.8, 0.6),
                size_hint_y=None,
                height=dp(34),
                color=(1, 1, 1, 1)
            )
            btn_settings.bind(on_press=lambda x: self.switch_tab(3))
            tabs_layout.add_widget(btn_settings)
            
            btn_customers = PersianButton(
                text='مشتریان',
                background_color=(0.3, 0.5, 0.8, 0.6),
                size_hint_y=None,
                height=dp(34),
                color=(1, 1, 1, 1)
            )
            btn_customers.bind(on_press=lambda x: self.switch_tab(2))
            tabs_layout.add_widget(btn_customers)
            
            btn_routes = PersianButton(
                text='مسیرها',
                background_color=(0.3, 0.5, 0.8, 0.6),
                size_hint_y=None,
                height=dp(34),
                color=(1, 1, 1, 1)
            )
            btn_routes.bind(on_press=lambda x: self.switch_tab(1))
            tabs_layout.add_widget(btn_routes)
            
            btn_agents = PersianButton(
                text='عامل‌ها',
                background_color=(0.3, 0.5, 0.8, 1),
                size_hint_y=None,
                height=dp(34),
                color=(1, 1, 1, 1)
            )
            btn_agents.bind(on_press=lambda x: self.switch_tab(0))
            tabs_layout.add_widget(btn_agents)
            
            main_layout.add_widget(tabs_layout)
            
            self.content_area = BoxLayout(orientation='vertical')
            main_layout.add_widget(self.content_area)
            
            logout_btn = PersianButton(
                text='خروج',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(36),
                color=(1, 1, 1, 1)
            )
            logout_btn.bind(on_press=self.logout)
            main_layout.add_widget(logout_btn)
            
            self.add_widget(main_layout)
            self.switch_tab(0)
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت UI AdminScreen: {e}", error_details)
            raise
    
    def switch_tab(self, tab_id):
        try:
            self.current_tab = tab_id
            self.content_area.clear_widgets()
            self.focusable_fields = []
            
            if tab_id == 0:
                self.show_agents_tab()
            elif tab_id == 1:
                self.show_routes_tab()
            elif tab_id == 2:
                self.show_customers_tab()
            elif tab_id == 3:
                self.show_settings_tab()
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در تغییر تب: {e}", error_details)
    
    # ============================================================
    # ✅ تب عامل‌ها (بدون تغییر)
    # ============================================================
    
    def show_agents_tab(self):
        try:
            scroll = ScrollView(
                do_scroll_x=False,
                do_scroll_y=True,
                size_hint=(1, 1),
                scroll_type=['bars', 'content'],
                bar_width=dp(8)
            )
            
            content = GridLayout(
                cols=1,
                spacing=dp(8),
                size_hint_y=None,
                padding=dp(10)
            )
            content.bind(minimum_height=content.setter('height'))
            
            content.add_widget(RTLLabel(
                text='➕ افزودن عامل جدید',
                size_hint_y=None,
                height=dp(38),
                font_size=sp(16),
                bold=True,
                color=(1, 1, 1, 1)
            ))
            
            name_input = RTLTextInput(
                hint_text='نام کامل',
                multiline=False,
                size_hint_y=None,
                height=dp(60),
                font_size=sp(36)
            )
            name_input.bg_color = (0.15, 0.15, 0.15, 1)
            name_input.border_color = (0.3, 0.3, 0.3, 1)
            name_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            name_input._hidden_input.foreground_color = (1, 1, 1, 1)
            name_input._hidden_input.bind(focus=self._on_field_focus)
            self.focusable_fields.append(name_input._hidden_input)
            content.add_widget(name_input)
            
            phone_input = RTLTextInput(
                hint_text='شماره تلفن',
                multiline=False,
                size_hint_y=None,
                height=dp(60),
                font_size=sp(36)
            )
            phone_input.bg_color = (0.15, 0.15, 0.15, 1)
            phone_input.border_color = (0.3, 0.3, 0.3, 1)
            phone_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            phone_input._hidden_input.foreground_color = (1, 1, 1, 1)
            phone_input._hidden_input.bind(focus=self._on_field_focus)
            self.focusable_fields.append(phone_input._hidden_input)
            content.add_widget(phone_input)
            
            role_spinner = PersianComboBox(
                text=ROLES[0],
                values=ROLES,
                size_hint_y=None,
                height=dp(55)
            )
            role_spinner.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            role_spinner.main_btn.color = (1, 1, 1, 1)
            role_spinner.main_btn.font_size = sp(18)
            content.add_widget(role_spinner)
            
            email_input = RTLTextInput(
                hint_text='ایمیل',
                multiline=False,
                size_hint_y=None,
                height=dp(60),
                font_size=sp(36)
            )
            email_input.bg_color = (0.15, 0.15, 0.15, 1)
            email_input.border_color = (0.3, 0.3, 0.3, 1)
            email_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            email_input._hidden_input.foreground_color = (1, 1, 1, 1)
            email_input._hidden_input.bind(focus=self._on_field_focus)
            self.focusable_fields.append(email_input._hidden_input)
            content.add_widget(email_input)
            
            add_btn = PersianButton(
                text='افزودن',
                size_hint_y=None,
                height=dp(45),
                background_color=(0.2, 0.7, 0.2, 1),
                color=(1, 1, 1, 1)
            )
            add_btn.bind(on_press=lambda x: self.add_agent_and_refresh(name_input, phone_input, role_spinner, email_input))
            content.add_widget(add_btn)
            
            content.add_widget(RTLLabel(
                text='📋 لیست عامل‌ها',
                size_hint_y=None,
                height=dp(38),
                font_size=sp(16),
                bold=True,
                color=(1, 1, 1, 1)
            ))
            
            agents = get_agents()
            if not agents:
                content.add_widget(RTLLabel(
                    text='هیچ عاملی ثبت نشده است',
                    size_hint_y=None,
                    height=dp(35),
                    font_size=sp(13),
                    color=(0.5, 0.5, 0.5, 1)
                ))
            
            for agent in agents:
                agent_box = BoxLayout(
                    size_hint_y=None,
                    height=dp(50),
                    spacing=dp(5),
                    padding=[dp(5), dp(5), dp(5), dp(5)]
                )
                agent_info = RTLLabel(
                    text=f"{agent.get('name', '')}\n{agent.get('role', '')}",
                    size_hint_x=0.7,
                    font_size=sp(13),
                    color=(1, 1, 1, 1)
                )
                agent_box.add_widget(agent_info)
                del_btn = PersianButton(
                    text='حذف',
                    size_hint_x=0.3,
                    background_color=(0.8, 0.2, 0.2, 1),
                    size_hint_y=None,
                    height=dp(35),
                    color=(1, 1, 1, 1)
                )
                del_btn.bind(on_press=lambda x, a=agent: self.delete_agent_and_refresh(a.get('id')))
                agent_box.add_widget(del_btn)
                content.add_widget(agent_box)
            
            scroll.add_widget(content)
            self.content_area.add_widget(scroll)
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش عامل‌ها: {e}", error_details)
    
    def add_agent_and_refresh(self, name_input, phone_input, role_spinner, email_input):
        try:
            if name_input.text:
                agent = {
                    'name': name_input.text,
                    'phone': phone_input.text,
                    'role': role_spinner.text,
                    'email': email_input.text,
                    'hire_date': get_today_jalali()
                }
                add_agent(agent)
                name_input.text = ''
                phone_input.text = ''
                email_input.text = ''
                self.show_message('✅ موفق', 'عامل با موفقیت اضافه شد')
                self.switch_tab(0)
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در افزودن عامل: {e}", error_details)
    
    def delete_agent_and_refresh(self, agent_id):
        try:
            delete_agent(agent_id)
            self.show_message('✅ موفق', 'عامل با موفقیت حذف شد')
            self.switch_tab(0)
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در حذف عامل: {e}", error_details)
    
    # ============================================================
    # ✅ تب مسیرها (با تغییرات)
    # ============================================================
    
    def show_routes_tab(self):
        try:
            layout = BoxLayout(orientation='vertical', padding=[dp(5), dp(5), dp(5), dp(5)])
            
            tabs = BoxLayout(
                size_hint_y=None,
                height=dp(45),
                spacing=dp(3),
                padding=[dp(5), dp(5), dp(5), dp(5)]
            )
            
            btn_manual = PersianButton(
                text='مدیریت دستی',
                background_color=(0.3, 0.5, 0.8, 1),
                size_hint_y=None,
                height=dp(40),
                color=(1, 1, 1, 1)
            )
            btn_manual.bind(on_press=lambda x: self.show_manual_routes())
            tabs.add_widget(btn_manual)
            
            btn_excel = PersianButton(
                text='ورود از اکسل',
                background_color=(0.3, 0.5, 0.8, 0.6),
                size_hint_y=None,
                height=dp(40),
                color=(1, 1, 1, 1)
            )
            btn_excel.bind(on_press=lambda x: self.show_excel_routes())
            tabs.add_widget(btn_excel)
            
            layout.add_widget(tabs)
            
            self.routes_content = BoxLayout(orientation='vertical', padding=[dp(10), dp(10), dp(10), dp(10)])
            layout.add_widget(self.routes_content)
            
            self.show_manual_routes()
            self.content_area.add_widget(layout)
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش مسیرها: {e}", error_details)
    
    def show_manual_routes(self):
        try:
            self.routes_content.clear_widgets()
            
            scroll = ScrollView(
                do_scroll_x=False,
                do_scroll_y=True,
                size_hint=(1, 1),
                scroll_type=['bars', 'content'],
                bar_width=dp(8)
            )
            
            content = GridLayout(
                cols=1,
                spacing=dp(8),
                size_hint_y=None,
                padding=dp(10)
            )
            content.bind(minimum_height=content.setter('height'))
            
            content.add_widget(RTLLabel(
                text='➕ افزودن مسیر جدید',
                size_hint_y=None,
                height=dp(38),
                font_size=sp(16),
                bold=True,
                color=(1, 1, 1, 1)
            ))
            
            self.route_name_input = RTLTextInput(
                hint_text='نام مسیر',
                multiline=False,
                size_hint_y=None,
                height=dp(60),
                font_size=sp(36)
            )
            self.route_name_input.bg_color = (0.15, 0.15, 0.15, 1)
            self.route_name_input.border_color = (0.3, 0.3, 0.3, 1)
            self.route_name_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.route_name_input._hidden_input.foreground_color = (1, 1, 1, 1)
            self.route_name_input._hidden_input.bind(focus=self._on_field_focus)
            self.focusable_fields.append(self.route_name_input._hidden_input)
            content.add_widget(self.route_name_input)
            
            add_btn = PersianButton(
                text='افزودن',
                size_hint_y=None,
                height=dp(45),
                background_color=(0.2, 0.7, 0.2, 1),
                color=(1, 1, 1, 1)
            )
            add_btn.bind(on_press=self.add_route_manual)
            content.add_widget(add_btn)
            
            content.add_widget(RTLLabel(
                text='🗺️ لیست مسیرها',
                size_hint_y=None,
                height=dp(38),
                font_size=sp(16),
                bold=True,
                color=(1, 1, 1, 1)
            ))
            
            self.routes_list = GridLayout(
                cols=1,
                spacing=dp(5),
                size_hint_y=None
            )
            self.routes_list.bind(minimum_height=self.routes_list.setter('height'))
            content.add_widget(self.routes_list)
            
            scroll.add_widget(content)
            self.routes_content.add_widget(scroll)
            
            self.refresh_routes_list()
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش مسیرهای دستی: {e}", error_details)
    
    def refresh_routes_list(self):
        try:
            self.routes_list.clear_widgets()
            routes = get_routes()
            
            if not routes:
                self.routes_list.add_widget(RTLLabel(
                    text='هیچ مسیری ثبت نشده است',
                    size_hint_y=None,
                    height=dp(35),
                    font_size=sp(13),
                    color=(0.5, 0.5, 0.5, 1)
                ))
            
            for route in routes:
                box = BoxLayout(
                    size_hint_y=None,
                    height=dp(38),
                    spacing=dp(5),
                    padding=[dp(5), dp(5), dp(5), dp(5)]
                )
                box.add_widget(RTLLabel(
                    text=route.get('name', ''),
                    size_hint_x=0.7,
                    font_size=sp(14),
                    color=(1, 1, 1, 1)
                ))
                del_btn = PersianButton(
                    text='حذف',
                    size_hint_x=0.3,
                    background_color=(0.8, 0.2, 0.2, 1),
                    size_hint_y=None,
                    height=dp(35),
                    color=(1, 1, 1, 1)
                )
                del_btn.bind(on_press=lambda x, r=route: self.delete_route_and_refresh(r.get('id')))
                box.add_widget(del_btn)
                self.routes_list.add_widget(box)
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در به‌روزرسانی لیست مسیرها: {e}", error_details)
    
    def add_route_manual(self, instance):
        try:
            if self.route_name_input.text:
                add_route({'name': self.route_name_input.text})
                self.route_name_input.text = ''
                self.refresh_routes_list()
                self.show_message('✅ موفق', 'مسیر با موفقیت اضافه شد')
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در افزودن مسیر: {e}", error_details)
    
    def delete_route_and_refresh(self, route_id):
        try:
            delete_route(route_id)
            self.refresh_routes_list()
            self.show_message('✅ موفق', 'مسیر با موفقیت حذف شد')
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در حذف مسیر: {e}", error_details)
    
    def show_excel_routes(self):
        try:
            self.routes_content.clear_widgets()
            
            layout = BoxLayout(
                orientation='vertical',
                padding=dp(15),
                spacing=dp(12)
            )
            
            layout.add_widget(RTLLabel(
                text='📎 ورود مسیرها از فایل Excel',
                font_size=sp(18),
                color=(1, 1, 1, 1),
                size_hint_y=None,
                height=dp(40),
            ))
            
            layout.add_widget(RTLLabel(
                text='فرمت فایل اکسل: فقط ستون اول (نام مسیر) خوانده می‌شود',
                font_size=sp(14),
                color=(0.7, 0.7, 0.7, 1),
                size_hint_y=None,
                height=dp(35),
            ))
            
            layout.add_widget(RTLLabel(
                text='📌 سطر اول عنوان و سطرهای بعدی نام مسیرها هستند',
                font_size=sp(13),
                color=(0.6, 0.8, 0.6, 1),
                size_hint_y=None,
                height=dp(40),
            ))
            
            self.routes_file_picker = FilePicker(
                on_select=self.import_routes_from_excel_file,
                file_type='excel',
                size_hint_y=None,
                height=dp(120)
            )
            layout.add_widget(self.routes_file_picker)
            
            self.routes_content.add_widget(layout)
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش ورود اکسل مسیرها: {e}", error_details)

    def import_routes_from_excel_file(self, filepath):
        """وارد کردن مسیرها از فایل اکسل"""
        logger.info(f"🔍 import_routes_from_excel_file: {filepath}")
        
        try:
            # ✅ بررسی انتخاب فایل
            if not filepath or not str(filepath).strip():
                self.show_message('❌ خطا', 'فایلی انتخاب نشده است.')
                return
            
            # ✅ بررسی وجود فایل
            if not os.path.exists(filepath):
                self.show_message('❌ خطا', f'فایل وجود ندارد:\n{filepath}')
                return
            
            # ✅ بررسی پسوند فایل (فقط xlsx)
            if not filepath.lower().endswith('.xlsx'):
                self.show_message('❌ خطا', 'فایل باید با فرمت .xlsx باشد')
                return
            
            # ✅ اجرای مستقیم (بدون تأخیر)
            success, message = import_routes_from_excel(filepath)
            logger.info(f"🔍 import result: success={success}, message={message}")
            
            if success:
                self.show_message('✅ اطلاعات با موفقیت در دیتابیس ذخیره شد.', message)
                Clock.schedule_once(lambda dt: self.switch_tab(1), 0.5)
            else:
                self.show_message('❌ خطا', message)
                
        except Exception as e:
            logger.error(f"❌ error: {e}")
            import traceback
            traceback.print_exc()
            ErrorPopup.show_error(f"خطا در ورود مسیرها از اکسل: {e}", traceback.format_exc())
    
    # ============================================================
    # ✅ تب مشتریان (با تغییرات)
    # ============================================================
    
    def show_customers_tab(self):
        try:
            layout = BoxLayout(orientation='vertical', padding=[dp(5), dp(5), dp(5), dp(5)])
            
            tabs = BoxLayout(
                size_hint_y=None,
                height=dp(45),
                spacing=dp(3),
                padding=[dp(5), dp(5), dp(5), dp(5)]
            )
            
            btn_manual = PersianButton(
                text='مدیریت دستی',
                background_color=(0.3, 0.5, 0.8, 1),
                size_hint_y=None,
                height=dp(40),
                color=(1, 1, 1, 1)
            )
            btn_manual.bind(on_press=lambda x: self.show_manual_customers())
            tabs.add_widget(btn_manual)
            
            btn_excel = PersianButton(
                text='ورود از اکسل',
                background_color=(0.3, 0.5, 0.8, 0.6),
                size_hint_y=None,
                height=dp(40),
                color=(1, 1, 1, 1)
            )
            btn_excel.bind(on_press=lambda x: self.show_excel_customers())
            tabs.add_widget(btn_excel)
            
            layout.add_widget(tabs)
            
            self.customers_content = BoxLayout(orientation='vertical', padding=[dp(10), dp(10), dp(10), dp(10)])
            layout.add_widget(self.customers_content)
            
            self.show_manual_customers()
            self.content_area.add_widget(layout)
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش مشتریان: {e}", error_details)
    
    def show_manual_customers(self):
        try:
            self.customers_content.clear_widgets()
            
            scroll = ScrollView(
                do_scroll_x=False,
                do_scroll_y=True,
                size_hint=(1, 1),
                scroll_type=['bars', 'content'],
                bar_width=dp(8)
            )
            
            content = GridLayout(
                cols=1,
                spacing=dp(8),
                size_hint_y=None,
                padding=dp(10)
            )
            content.bind(minimum_height=content.setter('height'))
            
            content.add_widget(RTLLabel(
                text='➕ افزودن مشتری جدید',
                size_hint_y=None,
                height=dp(38),
                font_size=sp(16),
                bold=True,
                color=(1, 1, 1, 1)
            ))
            
            content.add_widget(RTLLabel(
                text='انتخاب مسیر:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            routes = get_routes()
            route_names = [r.get('name', '') for r in routes] if routes else ['']
            self.customer_route_spinner = PersianComboBox(
                text=route_names[0] if route_names else '',
                values=route_names,
                size_hint_y=None,
                height=dp(55)
            )
            self.customer_route_spinner.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.customer_route_spinner.main_btn.color = (1, 1, 1, 1)
            self.customer_route_spinner.main_btn.font_size = sp(18)
            content.add_widget(self.customer_route_spinner)
            
            self.customer_name_input = RTLTextInput(
                hint_text='نام مشتری',
                multiline=False,
                size_hint_y=None,
                height=dp(60),
                font_size=sp(36)
            )
            self.customer_name_input.bg_color = (0.15, 0.15, 0.15, 1)
            self.customer_name_input.border_color = (0.3, 0.3, 0.3, 1)
            self.customer_name_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.customer_name_input._hidden_input.foreground_color = (1, 1, 1, 1)
            self.customer_name_input._hidden_input.bind(focus=self._on_field_focus)
            self.focusable_fields.append(self.customer_name_input._hidden_input)
            content.add_widget(self.customer_name_input)
            
            self.customer_store_input = RTLTextInput(
                hint_text='نام فروشگاه',
                multiline=False,
                size_hint_y=None,
                height=dp(60),
                font_size=sp(36)
            )
            self.customer_store_input.bg_color = (0.15, 0.15, 0.15, 1)
            self.customer_store_input.border_color = (0.3, 0.3, 0.3, 1)
            self.customer_store_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.customer_store_input._hidden_input.foreground_color = (1, 1, 1, 1)
            self.customer_store_input._hidden_input.bind(focus=self._on_field_focus)
            self.focusable_fields.append(self.customer_store_input._hidden_input)
            content.add_widget(self.customer_store_input)
            
            self.customer_mobile_input = RTLTextInput(
                hint_text='موبایل',
                multiline=False,
                size_hint_y=None,
                height=dp(60),
                font_size=sp(36)
            )
            self.customer_mobile_input.bg_color = (0.15, 0.15, 0.15, 1)
            self.customer_mobile_input.border_color = (0.3, 0.3, 0.3, 1)
            self.customer_mobile_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.customer_mobile_input._hidden_input.foreground_color = (1, 1, 1, 1)
            self.customer_mobile_input._hidden_input.bind(focus=self._on_field_focus)
            self.focusable_fields.append(self.customer_mobile_input._hidden_input)
            content.add_widget(self.customer_mobile_input)
            
            self.customer_address_input = RTLTextInput(
                hint_text='آدرس',
                multiline=False,
                size_hint_y=None,
                height=dp(60),
                font_size=sp(36)
            )
            self.customer_address_input.bg_color = (0.15, 0.15, 0.15, 1)
            self.customer_address_input.border_color = (0.3, 0.3, 0.3, 1)
            self.customer_address_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.customer_address_input._hidden_input.foreground_color = (1, 1, 1, 1)
            self.customer_address_input._hidden_input.bind(focus=self._on_field_focus)
            self.focusable_fields.append(self.customer_address_input._hidden_input)
            content.add_widget(self.customer_address_input)
            
            add_btn = PersianButton(
                text='افزودن مشتری',
                size_hint_y=None,
                height=dp(45),
                background_color=(0.2, 0.7, 0.2, 1),
                color=(1, 1, 1, 1)
            )
            add_btn.bind(on_press=self.add_customer_manual)
            content.add_widget(add_btn)
            
            content.add_widget(RTLLabel(
                text='📞 لیست مشتریان',
                size_hint_y=None,
                height=dp(38),
                font_size=sp(16),
                bold=True,
                color=(1, 1, 1, 1)
            ))
            
            self.customers_list = GridLayout(
                cols=1,
                spacing=dp(5),
                size_hint_y=None
            )
            self.customers_list.bind(minimum_height=self.customers_list.setter('height'))
            content.add_widget(self.customers_list)
            
            filter_btn = PersianButton(
                text='نمایش مشتریان این مسیر',
                size_hint_y=None,
                height=dp(40),
                background_color=(0.4, 0.5, 0.6, 1),
                color=(1, 1, 1, 1)
            )
            filter_btn.bind(on_press=self.refresh_customers_list)
            content.add_widget(filter_btn)
            
            scroll.add_widget(content)
            self.customers_content.add_widget(scroll)
            
            self.refresh_customers_list()
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش مشتریان دستی: {e}", error_details)
    
    def refresh_customers_list(self, instance=None):
        try:
            self.customers_list.clear_widgets()
            
            selected_route = self.customer_route_spinner.text
            all_customers = get_customers()
            
            filtered = [c for c in all_customers if c.get('route_name') == selected_route]
            
            if not filtered:
                self.customers_list.add_widget(RTLLabel(
                    text='هیچ مشتری در این مسیر وجود ندارد',
                    size_hint_y=None,
                    height=dp(35),
                    font_size=sp(13),
                    color=(0.5, 0.5, 0.5, 
