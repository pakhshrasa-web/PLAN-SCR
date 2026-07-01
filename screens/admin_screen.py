# screens/admin_screen.py
# ========== صفحه مدیریت با اسکرول دقیق ==========

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
    def __init__(self, **kwargs):
        try:
            super().__init__(**kwargs)
            # پس‌زمینه تیره
            with self.canvas.before:
                Color(0.08, 0.08, 0.08, 1)
                self.bg_rect = Rectangle(pos=self.pos, size=self.size)
                self.bind(pos=self._update_bg, size=self._update_bg)
            
            # ✅ تغییر به resize برای اسکرول دقیق
            Window.softinput_mode = 'resize'
            
            # ✅ متغیر برای ذخیره فیلدهای قابل فوکوس
            self.focusable_fields = []
            
            self.current_tab = 0
            self.build_ui()
            
            # ✅ اتصال رویدادهای کیبورد
            Window.bind(on_keyboard=self._on_keyboard)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت AdminScreen: {e}", error_details)
            raise
    
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    # ============================================================
    # ✅ مدیریت فوکوس و انتخاب خودکار متن
    # ============================================================
    
    def _on_field_focus(self, instance, value):
        """وقتی فیلد فوکوس میشه یا فوکوس رو از دست میده"""
        if value:
            Clock.schedule_once(lambda dt: self._select_all_text(instance), 0.1)
            # ✅ اسکرول با تأخیر برای اطمینان از نمایش کیبورد
            Clock.schedule_once(lambda dt: self._scroll_to_field(instance), 0.3)
    
    def _select_all_text(self, instance):
        """انتخاب کل متن فیلد"""
        if instance and hasattr(instance, 'select_all'):
            instance.select_all()
    
    def _scroll_to_field(self, instance):
        """اسکرول دقیق به موقعیت فیلد بالای کیبورد"""
        try:
            # پیدا کردن ScrollView
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
            print(f"⚠️ خطا در اسکرول به فیلد: {e}")
    
    # ============================================================
    # ✅ مدیریت کلیدهای کیبورد
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
    
    def build_ui(self):
        try:
            main_layout = BoxLayout(orientation='vertical', padding=[dp(5), dp(5), dp(5), dp(5)])
            
            # ========== تب‌ها (در بالا) ==========
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
            
            # ========== محتوای تب‌ها ==========
            self.content_area = BoxLayout(orientation='vertical')
            main_layout.add_widget(self.content_area)
            
            # ========== دکمه خروج ==========
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
            # ✅ ریست کردن لیست فیلدها برای هر تب جدید
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
    
    # ========== تب عامل‌ها ==========
    
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
                self.show_message('موفق', 'عامل با موفقیت اضافه شد')
                self.switch_tab(0)
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در افزودن عامل: {e}", error_details)
    
    def delete_agent_and_refresh(self, agent_id):
        try:
            delete_agent(agent_id)
            self.show_message('موفق', 'عامل با موفقیت حذف شد')
            self.switch_tab(0)
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در حذف عامل: {e}", error_details)
    
    # ========== تب مسیرها ==========
    
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
                self.show_message('موفق', 'مسیر با موفقیت اضافه شد')
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در افزودن مسیر: {e}", error_details)
    
    def delete_route_and_refresh(self, route_id):
        try:
            delete_route(route_id)
            self.refresh_routes_list()
            self.show_message('موفق', 'مسیر با موفقیت حذف شد')
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
                text='فرمت فایل اکسل: ستون اول نام مسیر',
                font_size=sp(14),
                color=(0.7, 0.7, 0.7, 1),
                size_hint_y=None,
                height=dp(35),
            ))
            
            self.routes_file_picker = FilePicker(
                size_hint_y=None,
                height=dp(100)
            )
            layout.add_widget(self.routes_file_picker)
            
            import_btn = PersianButton(
                text='ورود به سیستم',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1)
            )
            import_btn.bind(on_press=self.import_routes_from_excel)
            layout.add_widget(import_btn)
            
            self.routes_content.add_widget(layout)
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش ورود اکسل مسیرها: {e}", error_details)
    
    def import_routes_from_excel(self, instance):
        try:
            filepath = self.routes_file_picker.get_file()
            if not filepath:
                self.show_message('خطا', 'لطفاً ابتدا فایل را انتخاب کنید')
                return
            
            success, message = import_routes_from_excel(filepath)
            self.show_message('موفق' if success else 'خطا', message)
            
            if success:
                self.show_manual_routes()
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ورود مسیرها از اکسل: {e}", error_details)
    
    # ========== تب مشتریان ==========
    
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
                    color=(0.5, 0.5, 0.5, 1)
                ))
                return
            
            for customer in filtered:
                box = BoxLayout(
                    size_hint_y=None,
                    height=dp(50),
                    spacing=dp(5),
                    padding=[dp(5), dp(5), dp(5), dp(5)]
                )
                info = f"{customer.get('name', '')}\n{customer.get('store_name', '')}\n{customer.get('mobile', '')}"
                box.add_widget(RTLLabel(
                    text=info,
                    size_hint_x=0.7,
                    font_size=sp(12),
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
                del_btn.bind(on_press=lambda x, c=customer: self.delete_customer_and_refresh(c.get('id')))
                box.add_widget(del_btn)
                self.customers_list.add_widget(box)
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در به‌روزرسانی لیست مشتریان: {e}", error_details)
    
    def add_customer_manual(self, instance):
        try:
            route_name = self.customer_route_spinner.text
            name = self.customer_name_input.text
            store = self.customer_store_input.text
            mobile = self.customer_mobile_input.text
            address = self.customer_address_input.text
            
            if not route_name:
                self.show_message('خطا', 'لطفاً ابتدا مسیر را انتخاب کنید')
                return
            
            if not name:
                self.show_message('خطا', 'نام مشتری الزامی است')
                return
            
            customer = {
                'name': name,
                'store_name': store,
                'route_name': route_name,
                'mobile': mobile,
                'address': address
            }
            add_customer(customer)
            
            self.customer_name_input.text = ''
            self.customer_store_input.text = ''
            self.customer_mobile_input.text = ''
            self.customer_address_input.text = ''
            
            self.refresh_customers_list()
            self.show_message('موفق', 'مشتری با موفقیت اضافه شد')
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در افزودن مشتری: {e}", error_details)
    
    def delete_customer_and_refresh(self, customer_id):
        try:
            delete_customer(customer_id)
            self.refresh_customers_list()
            self.show_message('موفق', 'مشتری با موفقیت حذف شد')
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در حذف مشتری: {e}", error_details)
    
    def show_excel_customers(self):
        try:
            self.customers_content.clear_widgets()
            
            layout = BoxLayout(
                orientation='vertical',
                padding=dp(15),
                spacing=dp(12)
            )
            
            layout.add_widget(RTLLabel(
                text='📎 ورود مشتریان از فایل Excel',
                font_size=sp(18),
                color=(1, 1, 1, 1),
                size_hint_y=None,
                height=dp(40),
            ))
            
            layout.add_widget(RTLLabel(
                text='فرمت فایل اکسل: name, store_name, route_name, mobile, address',
                font_size=sp(14),
                color=(0.7, 0.7, 0.7, 1),
                size_hint_y=None,
                height=dp(35),
            ))
            
            # ✅ FilePicker با file_type='excel'
            self.customers_file_picker = FilePicker(
                on_select=self.import_customers_from_excel,
                file_type='excel',  # ✅ مشخص کردن نوع فایل
                size_hint_y=None,
                height=dp(120)
            )
            layout.add_widget(self.customers_file_picker)
            
            self.customers_content.add_widget(layout)
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش ورود اکسل مشتریان: {e}", error_details)
    
    def import_customers_from_excel(self, instance):
        try:
            filepath = self.customers_file_picker.get_file()
            if not filepath:
                self.show_message('خطا', 'لطفاً ابتدا فایل را انتخاب کنید')
                return
            
            success, message = import_customers_from_excel(filepath)
            self.show_message('موفق' if success else 'خطا', message)
            
            if success:
                self.show_manual_customers()
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ورود مشتریان از اکسل: {e}", error_details)
    
    # ========== تب تنظیمات ==========
    
    def show_settings_tab(self):
        try:
            settings = get_settings()
            
            scroll = ScrollView(
                do_scroll_x=False,
                do_scroll_y=True,
                size_hint=(1, 1),
                scroll_type=['bars', 'content'],
                bar_width=dp(8)
            )
            
            content = GridLayout(
                cols=2,
                spacing=dp(8),
                size_hint_y=None,
                padding=dp(10)
            )
            content.bind(minimum_height=content.setter('height'))
            
            fields = [
                ('supervision_rate', 'درصد سرکشی به مشتری', '0.3', 'float'),
                ('conversion_rate', 'نرخ تبدیل سرکشی به فاکتور', '0.25', 'float'),
                ('avg_invoice_amount', 'میانگین مبلغ فاکتور', '1000000', 'int'),
                ('target_amount', 'مبلغ تارگت ریالی', '50000000', 'int'),
                ('target_count', 'میزان تارگت تعدادی', '100', 'int'),
                ('target_invoice_count', 'میزان تارگت تعداد فاکتور', '20', 'int'),
                ('target_customer_count', 'میزان تارگت تعداد مشتری', '50', 'int'),
                ('target_new_customer_count', 'میزان تارگت مشتری جدید', '10', 'int'),
                ('target_cash_sales', 'تارگت فروش نقدی', '30000000', 'int'),
                ('target_credit_sales', 'تارگت فروش غیر نقدی', '20000000', 'int'),
                ('work_start_time', 'ساعت شروع به کار', '08:00', 'time'),
                ('first_visit_time', 'ساعت اولین ویزیت', '09:00', 'time'),
                ('min_daily_hours', 'حداقل ساعت کاری روزانه', '6', 'int'),
            ]
            
            inputs = {}
            for item in fields:
                key = item[0]
                label = item[1]
                default = item[2]
                field_type = item[3]
                
                content.add_widget(RTLLabel(
                    text=label + ':',
                    size_hint_y=None,
                    height=dp(60),
                    font_size=sp(14),
                    color=(1, 1, 1, 1)
                ))
                
                value = settings.get(key, default)
                if field_type == 'float':
                    input_field = RTLTextInput(
                        text=str(value),
                        multiline=False,
                        size_hint_y=None,
                        height=dp(60),
                        input_filter='float',
                        font_size=sp(36)
                    )
                elif field_type == 'int':
                    input_field = RTLTextInput(
                        text=str(value),
                        multiline=False,
                        size_hint_y=None,
                        height=dp(60),
                        input_filter='int',
                        font_size=sp(36)
                    )
                elif field_type == 'time':
                    input_field = RTLTextInput(
                        text=value,
                        multiline=False,
                        size_hint_y=None,
                        height=dp(60),
                        hint_text='HH:MM',
                        font_size=sp(36)
                    )
                else:
                    input_field = RTLTextInput(
                        text=str(value),
                        multiline=False,
                        size_hint_y=None,
                        height=dp(60),
                        font_size=sp(36)
                    )
                
                input_field.bg_color = (0.15, 0.15, 0.15, 1)
                input_field.border_color = (0.3, 0.3, 0.3, 1)
                input_field.border_color_focus = (0.2, 0.5, 0.9, 1)
                input_field._hidden_input.foreground_color = (1, 1, 1, 1)
                input_field._hidden_input.bind(focus=self._on_field_focus)
                self.focusable_fields.append(input_field._hidden_input)
                
                content.add_widget(input_field)
                inputs[key] = input_field
            
            save_btn = PersianButton(
                text='ذخیره تنظیمات',
                size_hint_y=None,
                height=dp(45),
                background_color=(0.2, 0.6, 1, 1),
                size_hint_x=0.5,
                color=(1, 1, 1, 1)
            )
            save_btn.bind(on_press=lambda x: self.save_settings(inputs))
            content.add_widget(save_btn)
            
            scroll.add_widget(content)
            self.content_area.add_widget(scroll)
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش تنظیمات: {e}", error_details)
    
    def save_settings(self, inputs):
        try:
            settings = {}
            for key, input_field in inputs.items():
                value = input_field.text
                
                if key in ['supervision_rate', 'conversion_rate']:
                    try:
                        value = float(value)
                    except:
                        value = 0.0
                elif key in ['avg_invoice_amount', 'target_amount', 'target_count', 'target_invoice_count', 
                            'target_customer_count', 'target_new_customer_count', 'target_cash_sales', 
                            'target_credit_sales', 'min_daily_hours']:
                    try:
                        value = int(value)
                    except:
                        value = 0
                elif key in ['work_start_time', 'first_visit_time']:
                    pass
                
                settings[key] = value
            
            update_settings(settings)
            self.show_message('موفق', 'تنظیمات با موفقیت ذخیره شد')
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ذخیره تنظیمات: {e}", error_details)
    
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
                font_size=sp(24),
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
            popup = Popup(
                title=title,
                content=content,
                size_hint=(0.9, 0.5),
                background_color=(0.08, 0.08, 0.08, 1)
            )
            popup.title_color = (1, 1, 1, 1)
            popup.title_size = sp(24)
            btn.bind(on_press=popup.dismiss)
            popup.open()
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش پیام: {e}", error_details)
    
    def logout(self, instance):
        self.manager.current = 'login'
