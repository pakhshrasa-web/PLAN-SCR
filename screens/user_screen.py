# screens/user_screen.py
# ========== صفحه کاربر (ثبت ویزیت) با اسکرول دقیق ==========

import traceback
import os
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.properties import StringProperty
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window

from utils.rtl_widgets import RTLTextInput, PersianComboBox, PersianButton, RTLLabel, PersianPopup
from utils.file_manager import (
    get_routes, get_customers, get_settings, 
    get_daily_logs, save_daily_log,
    load_json, save_json, get_data_path
)
from utils.jalali_date import get_today_jalali, get_current_time
from utils.delivery_manager import get_deliveries_by_date
from error_handler import ErrorPopup


class UserScreen(Screen):
    route_count = StringProperty('0')
    
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
            
            self.settings = get_settings()
            self.current_route = ''
            self.is_locked = False
            self.current_tab = 'visit'  # 'visit' یا 'distributor'
            
            # ============================================================
            # اضافه شده: متغیر برای ذخیره نقش کاربر
            # ============================================================
            self.user_role = ''
            
            self.build_ui()
            
            # اتصال رویدادهای کیبورد
            Window.bind(on_keyboard=self._on_keyboard)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت UserScreen: {e}", error_details)
            raise
    
    def on_pre_enter(self):
        """قبل از نمایش صفحه - بارگذاری نقش"""
        try:
            self._load_user_role()
            print(f" on_pre_enter - نقش: {self.user_role}")
        except Exception as e:
            print(f"خطا در on_pre_enter: {e}")

    def on_enter(self):
        """هر بار که صفحه UserScreen نمایش داده میشه، اجرا میشه"""
        try:
            print("=" * 50)
            print("ورود به UserScreen")
            print("=" * 50)
            
            # بارگذاری مجدد نقش (در صورت تغییر)
            self._load_user_role()
            print(f" نقش کاربر پس از بارگذاری: {self.user_role}")
            
            # ============================================================
            # بروزرسانی دکمه‌ها با تاخیر کوتاه
            # ============================================================
            Clock.schedule_once(lambda dt: self._update_buttons(), 0.1)
            
            # دریافت مجدد تنظیمات
            self.settings = get_settings()
            
            # بارگذاری مجدد داده‌ها بر اساس تب فعلی
            if self.user_role == 'موزع':
                self.load_distributor_data()
            else:
                self.load_data_from_agents()
                self.update_route_info()
            
            # بررسی قفل بودن صفحه (بعد از تعیین نقش)
            Clock.schedule_once(lambda dt: self.check_if_locked(), 0.2)
            
            print("=" * 50)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در به‌روزرسانی UserScreen: {e}", error_details)

    def _load_user_role(self):
        """بارگذاری نقش کاربر از App"""
        try:
            from kivy.app import App
            
            # دریافت از App
            app = App.get_running_app()
            if app and hasattr(app, 'current_user_role'):
                self.user_role = app.current_user_role
                print(f" نقش کاربر از App: {self.user_role}")
                return
            
            # اگر از App دریافت نشد، از LoginScreen بگیر
            login_screen = self.manager.get_screen('login')
            if login_screen and hasattr(login_screen, 'current_user_role'):
                self.user_role = login_screen.current_user_role
                print(f" نقش کاربر از LoginScreen: {self.user_role}")
                return
            
            # اگر هیچکدام کار نکرد، مقدار پیش‌فرض
            self.user_role = 'بازاریاب'
            print(f" نقش کاربر پیدا نشد، مقدار پیش‌فرض: {self.user_role}")
            
        except Exception as e:
            print(f"خطا در بارگذاری نقش کاربر: {e}")
            self.user_role = 'بازاریاب'
    
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def _update_buttons(self):
        """بروزرسانی وضعیت دکمه‌ها بر اساس نقش کاربر"""
        try:
            if not hasattr(self, 'visit_btn') or not hasattr(self, 'distributor_btn'):
                print(" دکمه‌ها وجود ندارند")
                return
            
            print(f" بروزرسانی دکمه‌ها برای نقش: {self.user_role}")
            
            # غیرفعال کردن هر دو دکمه
            self.visit_btn.disabled = True
            self.visit_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.visit_btn.color = (0.4, 0.4, 0.4, 1)
            
            self.distributor_btn.disabled = True
            self.distributor_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.distributor_btn.color = (0.4, 0.4, 0.4, 1)
            
            if self.user_role == 'موزع':
                self.distributor_btn.disabled = False
                self.distributor_btn.background_color = (0.8, 0.5, 0.2, 1)
                self.distributor_btn.color = (1, 1, 1, 1)
                
                self.visit_btn.disabled = True
                self.visit_btn.background_color = (0.2, 0.2, 0.2, 1)
                self.visit_btn.color = (0.4, 0.4, 0.4, 1)
                
                # نمایش فرم توزیع
                if hasattr(self, 'content_area'):
                    self.show_distributor_form()
                    self.load_distributor_data()
                    
                # ============================================================
                # تنظیم دکمه گزارش برای موزع
                # ============================================================
                # پیدا کردن دکمه گزارش در btn_layout
                # اگه دکمه گزارش رو در متغیر ذخیره کردید، از اون استفاده کنید
                # در غیر این صورت، تابع go_to_report رو تنظیم کنید
                
            else:
                self.visit_btn.disabled = False
                self.visit_btn.background_color = (0.8, 0.5, 0.2, 1)
                self.visit_btn.color = (1, 1, 1, 1)
                
                self.distributor_btn.disabled = True
                self.distributor_btn.background_color = (0.2, 0.2, 0.2, 1)
                self.distributor_btn.color = (0.4, 0.4, 0.4, 1)
                
                # نمایش فرم ویزیت
                if hasattr(self, 'content_area'):
                    self.show_visit_form()
                    self.load_data_from_agents()
                    self.update_route_info()
            
            print(f"   بعد از تغییر - visit_btn.disabled: {self.visit_btn.disabled}")
            print(f"   بعد از تغییر - distributor_btn.disabled: {self.distributor_btn.disabled}")
                
        except Exception as e:
            print(f" خطا در بروزرسانی دکمه‌ها: {e}")
            import traceback
            traceback.print_exc()
    
    def go_to_distributor(self, instance):
        """رفتن به صفحه توزیع"""
        try:
            self.manager.current = 'distributor'
        except Exception as e:
            ErrorPopup.show_error(f"خطا در رفتن به صفحه توزیع: {e}")

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
            # پیدا کردن ScrollView
            scroll = None
            for child in self.children:
                if isinstance(child, ScrollView):
                    scroll = child
                    break
            
            if not scroll:
                for child in self.children:
                    if hasattr(child, 'children'):
                        for sub in child.children:
                            if isinstance(sub, ScrollView):
                                scroll = sub
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
    
    def build_ui(self):
        try:
            main_layout = BoxLayout(orientation='vertical')
            
            scroll = ScrollView(
                do_scroll_x=False,
                do_scroll_y=True,
                size_hint=(1, 1),
                scroll_type=['bars', 'content'],
                bar_width=dp(8)
            )
            
            self.content_area = BoxLayout(
                orientation='vertical',
                padding=[dp(5), dp(5), dp(5), dp(5)],
                size_hint_y=None
            )
            self.content_area.bind(minimum_height=self.content_area.setter('height'))
            
            # ============================================================
            # ابتدا layoutها رو بساز
            # ============================================================
            self.visit_form_layout = GridLayout(
                cols=3,
                spacing=dp(4),
                size_hint_y=None,
                padding=dp(5)
            )
            self.visit_form_layout.bind(minimum_height=self.visit_form_layout.setter('height'))
            
            self.distributor_form_layout = GridLayout(
                cols=3,
                spacing=dp(4),
                size_hint_y=None,
                padding=dp(5)
            )
            self.distributor_form_layout.bind(minimum_height=self.distributor_form_layout.setter('height'))
            
            # ============================================================
            # حالا فرم‌ها رو پر کن
            # ============================================================
            self._build_visit_form()
            self._build_distributor_form()
            
            # ============================================================
            # نمایش فرم پیش‌فرض (ویزیت)
            # ============================================================
            self.show_visit_form()
            
            scroll.add_widget(self.content_area)
            main_layout.add_widget(scroll)
            
            # ========== دکمه‌ها ==========
            btn_layout = BoxLayout(
                size_hint_y=None,
                height=dp(50),
                spacing=dp(5),
                padding=dp(5)
            )

            self.visit_btn = PersianButton(
                text='ویزیت',
                background_color=(0.8, 0.5, 0.2, 1),
                size_hint_x=0.5,
                size_hint_y=None,
                height=dp(42),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            self.visit_btn.bind(on_press=self.go_to_agents)
            btn_layout.add_widget(self.visit_btn)

            self.distributor_btn = PersianButton(
                text='توزیع',
                background_color=(0.8, 0.5, 0.2, 1),
                size_hint_x=0.5,
                size_hint_y=None,
                height=dp(42),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            self.distributor_btn.bind(on_press=self.go_to_distributor)
            btn_layout.add_widget(self.distributor_btn)

            self.save_btn = PersianButton(
                text='ذخیره',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_x=0.5,
                size_hint_y=None,
                height=dp(42),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            self.save_btn.bind(on_press=self.save_log)
            btn_layout.add_widget(self.save_btn)

            report_btn = PersianButton(
                text='گزارش',
                background_color=(0.2, 0.6, 1, 1),
                size_hint_x=0.5,
                size_hint_y=None,
                height=dp(42),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            report_btn.bind(on_press=self.go_to_report)
            btn_layout.add_widget(report_btn)

            logout_btn = PersianButton(
                text='خروج',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_x=0.5,
                size_hint_y=None,
                height=dp(42),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            logout_btn.bind(on_press=self.logout)
            btn_layout.add_widget(logout_btn)
            
            main_layout.add_widget(btn_layout)
            
            self.add_widget(main_layout)
            
            # ============================================================
            # بارگذاری اولیه با تاخیرهای مناسب
            # ============================================================
            Clock.schedule_once(lambda dt: self._load_user_role(), 0.1)
            Clock.schedule_once(lambda dt: self._update_buttons(), 0.2)

        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت UI UserScreen: {e}", error_details)
            raise
    
    def _build_visit_form(self):
        """ساخت فرم ویزیت"""
        # ========== هدرها ==========
        self.visit_form_layout.add_widget(RTLLabel(
            text='آیتم',
            size_hint_y=None,
            height=dp(35),
            bold=True,
            color=(0.4, 0.7, 1, 1),
            font_size=sp(15)
        ))
        self.visit_form_layout.add_widget(RTLLabel(
            text='مقدار',
            size_hint_y=None,
            height=dp(35),
            bold=True,
            color=(0.4, 0.7, 1, 1),
            font_size=sp(15)
        ))
        self.visit_form_layout.add_widget(RTLLabel(
            text='هدف',
            size_hint_y=None,
            height=dp(35),
            bold=True,
            color=(0.4, 0.7, 1, 1),
            font_size=sp(15)
        ))
        
        self.visit_inputs = {}
        
        # ========== 1️⃣ تاریخ ویزیت ==========
        self.visit_form_layout.add_widget(RTLLabel(
            text='تاریخ ویزیت',
            size_hint_y=None,
            height=dp(40),
            font_size=sp(14),
            color=(1, 1, 1, 1)
        ))
        visit_date = RTLTextInput(
            text=get_today_jalali(),
            multiline=False,
            size_hint_y=None,
            height=dp(75),
            font_size=sp(32)
        )
        visit_date.bg_color = (0.15, 0.15, 0.15, 1)
        visit_date.border_color = (0.3, 0.3, 0.3, 1)
        visit_date.border_color_focus = (0.2, 0.5, 0.9, 1)
        visit_date._hidden_input.foreground_color = (1, 1, 1, 1)
        visit_date._hidden_input.disabled = True
        self.visit_form_layout.add_widget(visit_date)
        
        self.target_visit_date = Label(
            text=get_today_jalali(),
            size_hint_y=None,
            height=dp(40),
            color=(1, 1, 1, 1),
            font_size=sp(14),
            font_name='PersianFont',
            halign='center',
            valign='middle',
            text_size=(dp(120), dp(40))
        )
        self.visit_form_layout.add_widget(self.target_visit_date)
        self.visit_inputs['visit_date'] = visit_date
        
        # ========== 2️⃣ مسیر ویزیت ==========
        self.visit_form_layout.add_widget(RTLLabel(
            text='مسیر ویزیت',
            size_hint_y=None,
            height=dp(40),
            font_size=sp(14),
            color=(1, 1, 1, 1)
        ))
        self.route_display = RTLLabel(
            text='',
            size_hint_y=None,
            height=dp(45),
            font_size=sp(20),
            color=(1, 1, 1, 1)
        )
        self.visit_form_layout.add_widget(self.route_display)
        
        self.route_customers_target = Label(
            text='0',
            size_hint_y=None,
            height=dp(40),
            color=(1, 0.8, 0.2, 1),
            font_size=sp(24),
            font_name='PersianFont',
            halign='center',
            valign='middle',
            text_size=(dp(120), dp(40))
        )
        self.visit_form_layout.add_widget(self.route_customers_target)
        self.visit_inputs['route_name'] = self.route_display
        
        # ========== 3️⃣ ساعت شروع کار ==========
        self.visit_form_layout.add_widget(RTLLabel(
            text='ساعت شروع کار',
            size_hint_y=None,
            height=dp(40),
            font_size=sp(14),
            color=(1, 1, 1, 1)
        ))
        clock_in = RTLTextInput(
            text='',
            multiline=False,
            size_hint_y=None,
            height=dp(75),
            font_size=sp(32)
        )
        clock_in.bg_color = (0.15, 0.15, 0.15, 1)
        clock_in.border_color = (0.3, 0.3, 0.3, 1)
        clock_in.border_color_focus = (0.2, 0.5, 0.9, 1)
        clock_in._hidden_input.foreground_color = (1, 1, 1, 1)
        clock_in._hidden_input.disabled = True
        self.visit_form_layout.add_widget(clock_in)
        
        self.target_clock_in = Label(
            text=self.settings.get('work_start_time', '08:00'),
            size_hint_y=None,
            height=dp(40),
            color=(1, 1, 1, 1),
            font_size=sp(14),
            font_name='PersianFont',
            halign='center',
            valign='middle',
            text_size=(dp(120), dp(40))
        )
        self.visit_form_layout.add_widget(self.target_clock_in)
        self.visit_inputs['clock_in'] = clock_in
        
        # ========== 4️⃣ ساعت اولین ویزیت ==========
        self.visit_form_layout.add_widget(RTLLabel(
            text='ساعت اولین ویزیت',
            size_hint_y=None,
            height=dp(40),
            font_size=sp(14),
            color=(1, 1, 1, 1)
        ))
        first_visit_time = RTLTextInput(
            text='',
            multiline=False,
            size_hint_y=None,
            height=dp(75),
            font_size=sp(32)
        )
        first_visit_time.bg_color = (0.15, 0.15, 0.15, 1)
        first_visit_time.border_color = (0.3, 0.3, 0.3, 1)
        first_visit_time.border_color_focus = (0.2, 0.5, 0.9, 1)
        first_visit_time._hidden_input.foreground_color = (1, 1, 1, 1)
        first_visit_time._hidden_input.disabled = True
        self.visit_form_layout.add_widget(first_visit_time)
        
        self.target_first_visit = Label(
            text=self.settings.get('first_visit_time', '09:00'),
            size_hint_y=None,
            height=dp(40),
            color=(1, 1, 1, 1),
            font_size=sp(14),
            font_name='PersianFont',
            halign='center',
            valign='middle',
            text_size=(dp(120), dp(40))
        )
        self.visit_form_layout.add_widget(self.target_first_visit)
        self.visit_inputs['first_visit_time'] = first_visit_time
        
        # ========== 5️⃣ تعداد مشتری ویزیت شده ==========
        self.visit_form_layout.add_widget(RTLLabel(
            text='تعداد مشتری ویزیت شده',
            size_hint_y=None,
            height=dp(40),
            font_size=sp(14),
            color=(1, 1, 1, 1)
        ))
        visited_count = RTLTextInput(
            text='0',
            multiline=False,
            size_hint_y=None,
            height=dp(75),
            input_filter='int',
            font_size=sp(32)
        )
        visited_count.bg_color = (0.15, 0.15, 0.15, 1)
        visited_count.border_color = (0.3, 0.3, 0.3, 1)
        visited_count.border_color_focus = (0.2, 0.5, 0.9, 1)
        visited_count._hidden_input.foreground_color = (1, 1, 1, 1)
        visited_count._hidden_input.disabled = True
        self.visit_form_layout.add_widget(visited_count)
        
        self.visited_customers_target = Label(
            text='0',
            size_hint_y=None,
            height=dp(40),
            color=(1, 1, 1, 1),
            font_size=sp(14),
            font_name='PersianFont',
            halign='center',
            valign='middle',
            text_size=(dp(120), dp(40))
        )
        self.visit_form_layout.add_widget(self.visited_customers_target)
        self.visit_inputs['visited_customers_count'] = visited_count
        
        # ========== 5️⃣-1️⃣ تعداد مشتری جدید ==========
        self.visit_form_layout.add_widget(RTLLabel(
            text='تعداد مشتری جدید',
            size_hint_y=None,
            height=dp(40),
            font_size=sp(14),
            color=(1, 1, 1, 1),
            bold=True
        ))
        new_customers_count = RTLTextInput(
            text='0',
            multiline=False,
            size_hint_y=None,
            height=dp(75),
            input_filter='int',
            font_size=sp(32)
        )
        new_customers_count.bg_color = (0.15, 0.15, 0.15, 1)
        new_customers_count.border_color = (0.3, 0.3, 0.3, 1)
        new_customers_count.border_color_focus = (0.2, 0.5, 0.9, 1)
        new_customers_count._hidden_input.foreground_color = (1, 1, 1, 1)
        new_customers_count._hidden_input.disabled = True
        self.visit_form_layout.add_widget(new_customers_count)

        self.new_customers_target = Label(
            text='0',
            size_hint_y=None,
            height=dp(40),
            color=(1, 1, 1, 1),
            font_size=sp(14),
            font_name='PersianFont',
            halign='center',
            valign='middle',
            text_size=(dp(120), dp(40))
        )
        self.visit_form_layout.add_widget(self.new_customers_target)
        self.visit_inputs['new_customers_count'] = new_customers_count
        
        # ========== 6️⃣ تعداد فاکتور موفق ==========
        self.visit_form_layout.add_widget(RTLLabel(
            text='تعداد فاکتور موفق',
            size_hint_y=None,
            height=dp(40),
            font_size=sp(14),
            color=(1, 1, 1, 1)
        ))
        invoices_count = RTLTextInput(
            text='0',
            multiline=False,
            size_hint_y=None,
            height=dp(75),
            input_filter='int',
            font_size=sp(32)
        )
        invoices_count.bg_color = (0.15, 0.15, 0.15, 1)
        invoices_count.border_color = (0.3, 0.3, 0.3, 1)
        invoices_count.border_color_focus = (0.2, 0.5, 0.9, 1)
        invoices_count._hidden_input.foreground_color = (1, 1, 1, 1)
        invoices_count._hidden_input.disabled = True
        self.visit_form_layout.add_widget(invoices_count)
        
        self.target_invoices = Label(
            text=str(self.settings.get('target_invoice_count', '20')),
            size_hint_y=None,
            height=dp(40),
            color=(1, 1, 1, 1),
            font_size=sp(14),
            font_name='PersianFont',
            halign='center',
            valign='middle',
            text_size=(dp(120), dp(40))
        )
        self.visit_form_layout.add_widget(self.target_invoices)
        self.visit_inputs['successful_invoices_count'] = invoices_count
        
        # ========== 7️⃣ تعداد واحد فروش موفق ==========
        self.visit_form_layout.add_widget(RTLLabel(
            text='تعداد واحد فروش موفق',
            size_hint_y=None,
            height=dp(40),
            font_size=sp(14),
            color=(1, 1, 1, 1)
        ))
        units_count = RTLTextInput(
            text='0',
            multiline=False,
            size_hint_y=None,
            height=dp(75),
            input_filter='int',
            font_size=sp(32)
        )
        units_count.bg_color = (0.15, 0.15, 0.15, 1)
        units_count.border_color = (0.3, 0.3, 0.3, 1)
        units_count.border_color_focus = (0.2, 0.5, 0.9, 1)
        units_count._hidden_input.foreground_color = (1, 1, 1, 1)
        units_count._hidden_input.disabled = True
        self.visit_form_layout.add_widget(units_count)
        
        self.target_units = Label(
            text=str(self.settings.get('target_count', '100')),
            size_hint_y=None,
            height=dp(40),
            color=(1, 1, 1, 1),
            font_size=sp(14),
            font_name='PersianFont',
            halign='center',
            valign='middle',
            text_size=(dp(120), dp(40))
        )
        self.visit_form_layout.add_widget(self.target_units)
        self.visit_inputs['successful_units_count'] = units_count
        
        # ========== 8️⃣ مبلغ فروش موفق ==========
        self.visit_form_layout.add_widget(RTLLabel(
            text='مبلغ فروش موفق',
            size_hint_y=None,
            height=dp(40),
            font_size=sp(14),
            color=(1, 1, 1, 1)
        ))
        sales_amount = RTLTextInput(
            text='0',
            multiline=False,
            size_hint_y=None,
            height=dp(75),
            input_filter='int',
            font_size=sp(32)
        )
        sales_amount.bg_color = (0.15, 0.15, 0.15, 1)
        sales_amount.border_color = (0.3, 0.3, 0.3, 1)
        sales_amount.border_color_focus = (0.2, 0.5, 0.9, 1)
        sales_amount._hidden_input.foreground_color = (1, 1, 1, 1)
        sales_amount._hidden_input.disabled = True
        self.visit_form_layout.add_widget(sales_amount)
        
        target_amount = self.settings.get('target_amount', 50000000)
        try:
            target_amount = int(target_amount)
        except:
            target_amount = 0
        self.target_sales = Label(
            text="{:,}".format(target_amount),
            size_hint_y=None,
            height=dp(40),
            color=(1, 1, 1, 1),
            font_size=sp(14),
            font_name='PersianFont',
            halign='center',
            valign='middle',
            text_size=(dp(120), dp(40))
        )
        self.visit_form_layout.add_widget(self.target_sales)
        self.visit_inputs['successful_sales_amount'] = sales_amount
        
        # ========== 9️⃣ فروش نقدی ==========
        self.visit_form_layout.add_widget(RTLLabel(
            text='فروش نقدی',
            size_hint_y=None,
            height=dp(40),
            font_size=sp(14),
            color=(1, 1, 1, 1)
        ))
        cash_sales = RTLTextInput(
            text='0',
            multiline=False,
            size_hint_y=None,
            height=dp(75),
            input_filter='int',
            font_size=sp(32)
        )
        cash_sales.bg_color = (0.15, 0.15, 0.15, 1)
        cash_sales.border_color = (0.3, 0.3, 0.3, 1)
        cash_sales.border_color_focus = (0.2, 0.5, 0.9, 1)
        cash_sales._hidden_input.foreground_color = (1, 1, 1, 1)
        cash_sales._hidden_input.disabled = True
        self.visit_form_layout.add_widget(cash_sales)
        
        target_cash = self.settings.get('target_cash_sales', 30000000)
        try:
            target_cash = int(target_cash)
        except:
            target_cash = 0
        self.target_cash = Label(
            text="{:,}".format(target_cash),
            size_hint_y=None,
            height=dp(40),
            color=(1, 1, 1, 1),
            font_size=sp(14),
            font_name='PersianFont',
            halign='center',
            valign='middle',
            text_size=(dp(120), dp(40))
        )
        self.visit_form_layout.add_widget(self.target_cash)
        self.visit_inputs['cash_sales'] = cash_sales
        
        # ========== 🔟 فروش چکی ==========
        self.visit_form_layout.add_widget(RTLLabel(
            text='فروش چکی',
            size_hint_y=None,
            height=dp(40),
            font_size=sp(14),
            color=(1, 1, 1, 1)
        ))
        check_sales = RTLTextInput(
            text='0',
            multiline=False,
            size_hint_y=None,
            height=dp(75),
            input_filter='int',
            font_size=sp(32)
        )
        check_sales.bg_color = (0.15, 0.15, 0.15, 1)
        check_sales.border_color = (0.3, 0.3, 0.3, 1)
        check_sales.border_color_focus = (0.2, 0.5, 0.9, 1)
        check_sales._hidden_input.foreground_color = (1, 1, 1, 1)
        check_sales._hidden_input.disabled = True
        self.visit_form_layout.add_widget(check_sales)
        
        target_check = self.settings.get('target_credit_sales', 20000000)
        try:
            target_check = int(target_check)
        except:
            target_check = 0
        self.target_check = Label(
            text="{:,}".format(target_check),
            size_hint_y=None,
            height=dp(40),
            color=(1, 1, 1, 1),
            font_size=sp(14),
            font_name='PersianFont',
            halign='center',
            valign='middle',
            text_size=(dp(120), dp(40))
        )
        self.visit_form_layout.add_widget(self.target_check)
        self.visit_inputs['check_sales'] = check_sales
        
        # ========== 1️⃣1️⃣ فروش اعتباری ==========
        self.visit_form_layout.add_widget(RTLLabel(
            text='فروش اعتباری',
            size_hint_y=None,
            height=dp(40),
            font_size=sp(14),
            color=(1, 1, 1, 1)
        ))
        credit_sales = RTLTextInput(
            text='0',
            multiline=False,
            size_hint_y=None,
            height=dp(75),
            input_filter='int',
            font_size=sp(32)
        )
        credit_sales.bg_color = (0.15, 0.15, 0.15, 1)
        credit_sales.border_color = (0.3, 0.3, 0.3, 1)
        credit_sales.border_color_focus = (0.2, 0.5, 0.9, 1)
        credit_sales._hidden_input.foreground_color = (1, 1, 1, 1)
        credit_sales._hidden_input.disabled = True
        self.visit_form_layout.add_widget(credit_sales)
        
        target_credit = self.settings.get('target_credit_sales', 20000000)
        try:
            target_credit = int(target_credit)
        except:
            target_credit = 0
        self.target_credit = Label(
            text="{:,}".format(target_credit),
            size_hint_y=None,
            height=dp(40),
            color=(1, 1, 1, 1),
            font_size=sp(14),
            font_name='PersianFont',
            halign='center',
            valign='middle',
            text_size=(dp(120), dp(40))
        )
        self.visit_form_layout.add_widget(self.target_credit)
        self.visit_inputs['credit_sales'] = credit_sales
        
        # ========== 1️⃣2️⃣ ساعت آخرین ویزیت ==========
        self.visit_form_layout.add_widget(RTLLabel(
            text='ساعت آخرین ویزیت',
            size_hint_y=None,
            height=dp(40),
            font_size=sp(14),
            color=(1, 1, 1, 1)
        ))
        last_visit_time = RTLTextInput(
            text='',
            multiline=False,
            size_hint_y=None,
            height=dp(75),
            font_size=sp(32)
        )
        last_visit_time.bg_color = (0.15, 0.15, 0.15, 1)
        last_visit_time.border_color = (0.3, 0.3, 0.3, 1)
        last_visit_time.border_color_focus = (0.2, 0.5, 0.9, 1)
        last_visit_time._hidden_input.foreground_color = (1, 1, 1, 1)
        last_visit_time._hidden_input.disabled = True
        self.visit_form_layout.add_widget(last_visit_time)
        
        self.target_last_visit = Label(
            text='---',
            size_hint_y=None,
            height=dp(40),
            color=(1, 1, 1, 1),
            font_size=sp(14),
            font_name='PersianFont',
            halign='center',
            valign='middle',
            text_size=(dp(120), dp(40))
        )
        self.visit_form_layout.add_widget(self.target_last_visit)
        self.visit_inputs['last_visit_time'] = last_visit_time
        
        # ========== 1️⃣3️⃣ ساعت پایان کار ==========
        self.visit_form_layout.add_widget(RTLLabel(
            text='ساعت پایان کار',
            size_hint_y=None,
            height=dp(40),
            font_size=sp(14),
            color=(1, 1, 1, 1)
        ))
        clock_out = RTLTextInput(
            text='',
            multiline=False,
            size_hint_y=None,
            height=dp(75),
            font_size=sp(32)
        )
        clock_out.bg_color = (0.15, 0.15, 0.15, 1)
        clock_out.border_color = (0.3, 0.3, 0.3, 1)
        clock_out.border_color_focus = (0.2, 0.5, 0.9, 1)
        clock_out._hidden_input.foreground_color = (1, 1, 1, 1)
        clock_out._hidden_input.disabled = True
        self.visit_form_layout.add_widget(clock_out)
        
        self.target_clock_out = Label(
            text='---',
            size_hint_y=None,
            height=dp(40),
            color=(1, 1, 1, 1),
            font_size=sp(14),
            font_name='PersianFont',
            halign='center',
            valign='middle',
            text_size=(dp(120), dp(40))
        )
        self.visit_form_layout.add_widget(self.target_clock_out)
        self.visit_inputs['clock_out'] = clock_out
    
    def _build_distributor_form(self):
        """ساخت فرم توزیع"""
        # ========== هدرها ==========
        self.distributor_form_layout.add_widget(RTLLabel(
            text='آیتم',
            size_hint_y=None,
            height=dp(35),
            bold=True,
            color=(0.4, 0.7, 1, 1),
            font_size=sp(15)
        ))
        self.distributor_form_layout.add_widget(RTLLabel(
            text='مقدار',
            size_hint_y=None,
            height=dp(35),
            bold=True,
            color=(0.4, 0.7, 1, 1),
            font_size=sp(15)
        ))
        self.distributor_form_layout.add_widget(RTLLabel(
            text='هدف',
            size_hint_y=None,
            height=dp(35),
            bold=True,
            color=(0.4, 0.7, 1, 1),
            font_size=sp(15)
        ))
        
        self.distributor_inputs = {}
        
        # ========== 1️⃣ تاریخ توزیع ==========
        self.distributor_form_layout.add_widget(RTLLabel(
            text='تاریخ توزیع',
            size_hint_y=None,
            height=dp(40),
            font_size=sp(14),
            color=(1, 1, 1, 1)
        ))
        dist_date = RTLTextInput(
            text=get_today_jalali(),
            multiline=False,
            size_hint_y=None,
            height=dp(75),
            font_size=sp(32)
        )
        dist_date.bg_color = (0.15, 0.15, 0.15, 1)
        dist_date.border_color = (0.3, 0.3, 0.3, 1)
        dist_date.border_color_focus = (0.2, 0.5, 0.9, 1)
        dist_date._hidden_input.foreground_color = (1, 1, 1, 1)
        dist_date._hidden_input.disabled = True
        self.distributor_form_layout.add_widget(dist_date)
        
        self.dist_target_date = Label(
            text=get_today_jalali(),
            size_hint_y=None,
            height=dp(40),
            color=(1, 1, 1, 1),
            font_size=sp(14),
            font_name='PersianFont',
            halign='center',
            valign='middle',
            text_size=(dp(120), dp(40))
        )
        self.distributor_form_layout.add_widget(self.dist_target_date)
        self.distributor_inputs['dist_date'] = dist_date
        
        # ========== 2️⃣ مسیر توزیع ==========
        self.distributor_form_layout.add_widget(RTLLabel(
            text='مسیر توزیع',
            size_hint_y=None,
            height=dp(40),
            font_size=sp(14),
            color=(1, 1, 1, 1)
        ))
        self.dist_route_display = RTLLabel(
            text='',
            size_hint_y=None,
            height=dp(45),
            font_size=sp(20),
            color=(1, 1, 1, 1)
        )
        self.distributor_form_layout.add_widget(self.dist_route_display)
        
        self.dist_route_target = Label(
            text='0',
            size_hint_y=None,
            height=dp(40),
            color=(1, 0.8, 0.2, 1),
            font_size=sp(24),
            font_name='PersianFont',
            halign='center',
            valign='middle',
            text_size=(dp(120), dp(40))
        )
        self.distributor_form_layout.add_widget(self.dist_route_target)
        self.distributor_inputs['dist_route'] = self.dist_route_display
        
        # ========== 3️⃣ ساعت شروع توزیع ==========
        self.distributor_form_layout.add_widget(RTLLabel(
            text='ساعت شروع توزیع',
            size_hint_y=None,
            height=dp(40),
            font_size=sp(14),
            color=(1, 1, 1, 1)
        ))
        dist_clock_in = RTLTextInput(
            text='',
            multiline=False,
            size_hint_y=None,
            height=dp(75),
            font_size=sp(32)
        )
        dist_clock_in.bg_color = (0.15, 0.15, 0.15, 1)
        dist_clock_in.border_color = (0.3, 0.3, 0.3, 1)
        dist_clock_in.border_color_focus = (0.2, 0.5, 0.9, 1)
        dist_clock_in._hidden_input.foreground_color = (1, 1, 1, 1)
        dist_clock_in._hidden_input.disabled = True
        self.distributor_form_layout.add_widget(dist_clock_in)
        
        self.dist_target_clock_in = Label(
            text=self.settings.get('work_start_time', '08:00'),
            size_hint_y=None,
            height=dp(40),
            color=(1, 1, 1, 1),
            font_size=sp(14),
            font_name='PersianFont',
            halign='center',
            valign='middle',
            text_size=(dp(120), dp(40))
        )
        self.distributor_form_layout.add_widget(self.dist_target_clock_in)
        self.distributor_inputs['dist_clock_in'] = dist_clock_in
        
        # ========== 4️⃣ ساعت اولین توزیع ==========
        self.distributor_form_layout.add_widget(RTLLabel(
            text='ساعت اولین توزیع',
            size_hint_y=None,
            height=dp(40),
            font_size=sp(14),
            color=(1, 1, 1, 1)
        ))
        dist_first_time = RTLTextInput(
            text='',
            multiline=False,
            size_hint_y=None,
            height=dp(75),
            font_size=sp(32)
        )
        dist_first_time.bg_color = (0.15, 0.15, 0.15, 1)
        dist_first_time.border_color = (0.3, 0.3, 0.3, 1)
        dist_first_time.border_color_focus = (0.2, 0.5, 0.9, 1)
        dist_first_time._hidden_input.foreground_color = (1, 1, 1, 1)
        dist_first_time._hidden_input.disabled = True
        self.distributor_form_layout.add_widget(dist_first_time)
        
        self.dist_target_first = Label(
            text=self.settings.get('first_visit_time', '09:00'),
            size_hint_y=None,
            height=dp(40),
            color=(1, 1, 1, 1),
            font_size=sp(14),
            font_name='PersianFont',
            halign='center',
            valign='middle',
            text_size=(dp(120), dp(40))
        )
        self.distributor_form_layout.add_widget(self.dist_target_first)
        self.distributor_inputs['dist_first_time'] = dist_first_time
        
        # ========== 5️⃣ تعداد مشتری توزیع شده ==========
        # تغییر به: تعداد فاکتور قابل توزیع
        self.distributor_form_layout.add_widget(RTLLabel(
            text='تعداد فاکتور قابل توزیع',  # ← تغییر نام
            size_hint_y=None,
            height=dp(40),
            font_size=sp(14),
            color=(1, 1, 1, 1)
        ))
        dist_customers = RTLTextInput(
            text='0',
            multiline=False,
            size_hint_y=None,
            height=dp(75),
            input_filter='int',
            font_size=sp(32)
        )
        dist_customers.bg_color = (0.15, 0.15, 0.15, 1)
        dist_customers.border_color = (0.3, 0.3, 0.3, 1)
        dist_customers.border_color_focus = (0.2, 0.5, 0.9, 1)
        dist_customers._hidden_input.foreground_color = (1, 1, 1, 1)
        dist_customers._hidden_input.disabled = True
        self.distributor_form_layout.add_widget(dist_customers)

        self.dist_target_customers = Label(
            text=str(self.settings.get('distributor_target_customers', '30')),
            size_hint_y=None,
            height=dp(40),
            color=(1, 1, 1, 1),
            font_size=sp(14),
            font_name='PersianFont',
            halign='center',
            valign='middle',
            text_size=(dp(120), dp(40))
        )
        self.distributor_form_layout.add_widget(self.dist_target_customers)
        self.distributor_inputs['dist_customers'] = dist_customers
        
        # ========== 6️⃣ تعداد توزیع موفق ==========
        self.distributor_form_layout.add_widget(RTLLabel(
            text='تعداد توزیع موفق',
            size_hint_y=None,
            height=dp(40),
            font_size=sp(14),
            color=(1, 1, 1, 1)
        ))
        dist_invoices = RTLTextInput(
            text='0',
            multiline=False,
            size_hint_y=None,
            height=dp(75),
            input_filter='int',
            font_size=sp(32)
        )
        dist_invoices.bg_color = (0.15, 0.15, 0.15, 1)
        dist_invoices.border_color = (0.3, 0.3, 0.3, 1)
        dist_invoices.border_color_focus = (0.2, 0.5, 0.9, 1)
        dist_invoices._hidden_input.foreground_color = (1, 1, 1, 1)
        dist_invoices._hidden_input.disabled = True
        self.distributor_form_layout.add_widget(dist_invoices)
        
        self.dist_target_invoices = Label(
            text=str(self.settings.get('distributor_target_invoices', '15')),
            size_hint_y=None,
            height=dp(40),
            color=(1, 1, 1, 1),
            font_size=sp(14),
            font_name='PersianFont',
            halign='center',
            valign='middle',
            text_size=(dp(120), dp(40))
        )
        self.distributor_form_layout.add_widget(self.dist_target_invoices)
        self.distributor_inputs['dist_invoices'] = dist_invoices
        
        # ========== 7️⃣ مبلغ کل توزیع ==========
        self.distributor_form_layout.add_widget(RTLLabel(
            text='مبلغ کل توزیع',
            size_hint_y=None,
            height=dp(40),
            font_size=sp(14),
            color=(1, 1, 1, 1)
        ))
        dist_amount = RTLTextInput(
            text='0',
            multiline=False,
            size_hint_y=None,
            height=dp(75),
            input_filter='int',
            font_size=sp(32)
        )
        dist_amount.bg_color = (0.15, 0.15, 0.15, 1)
        dist_amount.border_color = (0.3, 0.3, 0.3, 1)
        dist_amount.border_color_focus = (0.2, 0.5, 0.9, 1)
        dist_amount._hidden_input.foreground_color = (1, 1, 1, 1)
        dist_amount._hidden_input.disabled = True
        self.distributor_form_layout.add_widget(dist_amount)
        
        target_dist_amount = self.settings.get('distributor_target_amount', 30000000)
        try:
            target_dist_amount = int(target_dist_amount)
        except:
            target_dist_amount = 0
        self.dist_target_amount = Label(
            text="{:,}".format(target_dist_amount),
            size_hint_y=None,
            height=dp(40),
            color=(1, 1, 1, 1),
            font_size=sp(14),
            font_name='PersianFont',
            halign='center',
            valign='middle',
            text_size=(dp(120), dp(40))
        )
        self.distributor_form_layout.add_widget(self.dist_target_amount)
        self.distributor_inputs['dist_amount'] = dist_amount
        
        # ========== 8️⃣ مبلغ نقدی ==========
        self.distributor_form_layout.add_widget(RTLLabel(
            text='مبلغ نقدی',
            size_hint_y=None,
            height=dp(40),
            font_size=sp(14),
            color=(1, 1, 1, 1)
        ))
        dist_cash = RTLTextInput(
            text='0',
            multiline=False,
            size_hint_y=None,
            height=dp(75),
            input_filter='int',
            font_size=sp(32)
        )
        dist_cash.bg_color = (0.15, 0.15, 0.15, 1)
        dist_cash.border_color = (0.3, 0.3, 0.3, 1)
        dist_cash.border_color_focus = (0.2, 0.5, 0.9, 1)
        dist_cash._hidden_input.foreground_color = (1, 1, 1, 1)
        dist_cash._hidden_input.disabled = True
        self.distributor_form_layout.add_widget(dist_cash)
        
        target_dist_cash = self.settings.get('distributor_target_cash', 15000000)
        try:
            target_dist_cash = int(target_dist_cash)
        except:
            target_dist_cash = 0
        self.dist_target_cash = Label(
            text="{:,}".format(target_dist_cash),
            size_hint_y=None,
            height=dp(40),
            color=(1, 1, 1, 1),
            font_size=sp(14),
            font_name='PersianFont',
            halign='center',
            valign='middle',
            text_size=(dp(120), dp(40))
        )
        self.distributor_form_layout.add_widget(self.dist_target_cash)
        self.distributor_inputs['dist_cash'] = dist_cash
        
        # ========== 9️⃣ مبلغ چکی ==========
        self.distributor_form_layout.add_widget(RTLLabel(
            text='مبلغ چکی',
            size_hint_y=None,
            height=dp(40),
            font_size=sp(14),
            color=(1, 1, 1, 1)
        ))
        dist_check = RTLTextInput(
            text='0',
            multiline=False,
            size_hint_y=None,
            height=dp(75),
            input_filter='int',
            font_size=sp(32)
        )
        dist_check.bg_color = (0.15, 0.15, 0.15, 1)
        dist_check.border_color = (0.3, 0.3, 0.3, 1)
        dist_check.border_color_focus = (0.2, 0.5, 0.9, 1)
        dist_check._hidden_input.foreground_color = (1, 1, 1, 1)
        dist_check._hidden_input.disabled = True
        self.distributor_form_layout.add_widget(dist_check)
        
        target_dist_check = self.settings.get('distributor_target_check', 10000000)
        try:
            target_dist_check = int(target_dist_check)
        except:
            target_dist_check = 0
        self.dist_target_check = Label(
            text="{:,}".format(target_dist_check),
            size_hint_y=None,
            height=dp(40),
            color=(1, 1, 1, 1),
            font_size=sp(14),
            font_name='PersianFont',
            halign='center',
            valign='middle',
            text_size=(dp(120), dp(40))
        )
        self.distributor_form_layout.add_widget(self.dist_target_check)
        self.distributor_inputs['dist_check'] = dist_check
        
        # ========== 🔟 مبلغ نسیه ==========
        self.distributor_form_layout.add_widget(RTLLabel(
            text='مبلغ نسیه',
            size_hint_y=None,
            height=dp(40),
            font_size=sp(14),
            color=(1, 1, 1, 1)
        ))
        dist_credit = RTLTextInput(
            text='0',
            multiline=False,
            size_hint_y=None,
            height=dp(75),
            input_filter='int',
            font_size=sp(32)
        )
        dist_credit.bg_color = (0.15, 0.15, 0.15, 1)
        dist_credit.border_color = (0.3, 0.3, 0.3, 1)
        dist_credit.border_color_focus = (0.2, 0.5, 0.9, 1)
        dist_credit._hidden_input.foreground_color = (1, 1, 1, 1)
        dist_credit._hidden_input.disabled = True
        self.distributor_form_layout.add_widget(dist_credit)
        
        target_dist_credit = self.settings.get('distributor_target_credit', 5000000)
        try:
            target_dist_credit = int(target_dist_credit)
        except:
            target_dist_credit = 0
        self.dist_target_credit = Label(
            text="{:,}".format(target_dist_credit),
            size_hint_y=None,
            height=dp(40),
            color=(1, 1, 1, 1),
            font_size=sp(14),
            font_name='PersianFont',
            halign='center',
            valign='middle',
            text_size=(dp(120), dp(40))
        )
        self.distributor_form_layout.add_widget(self.dist_target_credit)
        self.distributor_inputs['dist_credit'] = dist_credit
        
        # ========== 1️⃣1️⃣ تعداد برگشتی ==========
        self.distributor_form_layout.add_widget(RTLLabel(
            text='تعداد برگشتی',
            size_hint_y=None,
            height=dp(40),
            font_size=sp(14),
            color=(1, 1, 1, 1)
        ))
        dist_return_qty = RTLTextInput(
            text='0',
            multiline=False,
            size_hint_y=None,
            height=dp(75),
            input_filter='int',
            font_size=sp(32)
        )
        dist_return_qty.bg_color = (0.15, 0.15, 0.15, 1)
        dist_return_qty.border_color = (0.3, 0.3, 0.3, 1)
        dist_return_qty.border_color_focus = (0.2, 0.5, 0.9, 1)
        dist_return_qty._hidden_input.foreground_color = (1, 1, 1, 1)
        dist_return_qty._hidden_input.disabled = True
        self.distributor_form_layout.add_widget(dist_return_qty)
        
        self.dist_target_return_qty = Label(
            text='0',
            size_hint_y=None,
            height=dp(40),
            color=(1, 1, 1, 1),
            font_size=sp(14),
            font_name='PersianFont',
            halign='center',
            valign='middle',
            text_size=(dp(120), dp(40))
        )
        self.distributor_form_layout.add_widget(self.dist_target_return_qty)
        self.distributor_inputs['dist_return_qty'] = dist_return_qty
        
        # ========== 1️⃣2️⃣ مبلغ برگشتی ==========
        self.distributor_form_layout.add_widget(RTLLabel(
            text='مبلغ برگشتی',
            size_hint_y=None,
            height=dp(40),
            font_size=sp(14),
            color=(1, 1, 1, 1)
        ))
        dist_return_amount = RTLTextInput(
            text='0',
            multiline=False,
            size_hint_y=None,
            height=dp(75),
            input_filter='int',
            font_size=sp(32)
        )
        dist_return_amount.bg_color = (0.15, 0.15, 0.15, 1)
        dist_return_amount.border_color = (0.3, 0.3, 0.3, 1)
        dist_return_amount.border_color_focus = (0.2, 0.5, 0.9, 1)
        dist_return_amount._hidden_input.foreground_color = (1, 1, 1, 1)
        dist_return_amount._hidden_input.disabled = True
        self.distributor_form_layout.add_widget(dist_return_amount)
        
        self.dist_target_return_amount = Label(
            text='0',
            size_hint_y=None,
            height=dp(40),
            color=(1, 1, 1, 1),
            font_size=sp(14),
            font_name='PersianFont',
            halign='center',
            valign='middle',
            text_size=(dp(120), dp(40))
        )
        self.distributor_form_layout.add_widget(self.dist_target_return_amount)
        self.distributor_inputs['dist_return_amount'] = dist_return_amount
        
        # ========== 1️⃣3️⃣ ساعت آخرین توزیع ==========
        self.distributor_form_layout.add_widget(RTLLabel(
            text='ساعت آخرین توزیع',
            size_hint_y=None,
            height=dp(40),
            font_size=sp(14),
            color=(1, 1, 1, 1)
        ))
        dist_last_time = RTLTextInput(
            text='',
            multiline=False,
            size_hint_y=None,
            height=dp(75),
            font_size=sp(32)
        )
        dist_last_time.bg_color = (0.15, 0.15, 0.15, 1)
        dist_last_time.border_color = (0.3, 0.3, 0.3, 1)
        dist_last_time.border_color_focus = (0.2, 0.5, 0.9, 1)
        dist_last_time._hidden_input.foreground_color = (1, 1, 1, 1)
        dist_last_time._hidden_input.disabled = True
        self.distributor_form_layout.add_widget(dist_last_time)
        
        self.dist_target_last = Label(
            text='---',
            size_hint_y=None,
            height=dp(40),
            color=(1, 1, 1, 1),
            font_size=sp(14),
            font_name='PersianFont',
            halign='center',
            valign='middle',
            text_size=(dp(120), dp(40))
        )
        self.distributor_form_layout.add_widget(self.dist_target_last)
        self.distributor_inputs['dist_last_time'] = dist_last_time
        
        # ========== 1️⃣4️⃣ ساعت پایان توزیع ==========
        self.distributor_form_layout.add_widget(RTLLabel(
            text='ساعت پایان توزیع',
            size_hint_y=None,
            height=dp(40),
            font_size=sp(14),
            color=(1, 1, 1, 1)
        ))
        dist_clock_out = RTLTextInput(
            text='',
            multiline=False,
            size_hint_y=None,
            height=dp(75),
            font_size=sp(32)
        )
        dist_clock_out.bg_color = (0.15, 0.15, 0.15, 1)
        dist_clock_out.border_color = (0.3, 0.3, 0.3, 1)
        dist_clock_out.border_color_focus = (0.2, 0.5, 0.9, 1)
        dist_clock_out._hidden_input.foreground_color = (1, 1, 1, 1)
        dist_clock_out._hidden_input.disabled = True
        self.distributor_form_layout.add_widget(dist_clock_out)
        
        self.dist_target_clock_out = Label(
            text='---',
            size_hint_y=None,
            height=dp(40),
            color=(1, 1, 1, 1),
            font_size=sp(14),
            font_name='PersianFont',
            halign='center',
            valign='middle',
            text_size=(dp(120), dp(40))
        )
        self.distributor_form_layout.add_widget(self.dist_target_clock_out)
        self.distributor_inputs['dist_clock_out'] = dist_clock_out
    
    def show_visit_form(self):
        """نمایش فرم ویزیت"""
        if hasattr(self, 'content_area'):
            self.content_area.clear_widgets()
            self.content_area.add_widget(self.visit_form_layout)
            self.current_tab = 'visit'

    def show_distributor_form(self):
        """نمایش فرم توزیع"""
        if hasattr(self, 'content_area'):
            self.content_area.clear_widgets()
            self.content_area.add_widget(self.distributor_form_layout)
            self.current_tab = 'distributor'

    def check_if_locked(self):
        """بررسی اینکه آیا امروز قبلاً ذخیره شده یا نه - بر اساس نقش"""
        try:
            today = get_today_jalali()
            
            # تعیین نام فایل بر اساس نقش
            if self.user_role == 'موزع':
                summary_file = 'distributor_summary.json'
            else:
                summary_file = 'daily_summary.json'
            
            summary_path = os.path.join(get_data_path(), summary_file)
            
            if os.path.exists(summary_path):
                all_summaries = load_json(summary_file)
                if today in all_summaries:
                    self.is_locked = True
                    self.lock_page()
                else:
                    self.is_locked = False
                    self.unlock_page()
            else:
                self.is_locked = False
                self.unlock_page()
                
        except Exception as e:
            print(f"خطا در بررسی قفل: {e}")
    
    def lock_page(self):
        """قفل کردن صفحه (غیرفعال کردن دکمه‌ها و فیلدها)"""
        try:
            # غیرفعال کردن دکمه ذخیره
            if hasattr(self, 'save_btn'):
                self.save_btn.disabled = True
                self.save_btn.background_color = (0.3, 0.3, 0.3, 1)
                self.save_btn.color = (0.5, 0.5, 0.5, 1)
            
            # ============================================================
            # غیرفعال کردن هر دو دکمه ویزیت و توزیع
            # ============================================================
            if hasattr(self, 'visit_btn'):
                self.visit_btn.disabled = True
                self.visit_btn.background_color = (0.3, 0.3, 0.3, 1)
                self.visit_btn.color = (0.5, 0.5, 0.5, 1)
            
            if hasattr(self, 'distributor_btn'):
                self.distributor_btn.disabled = True
                self.distributor_btn.background_color = (0.3, 0.3, 0.3, 1)
                self.distributor_btn.color = (0.5, 0.5, 0.5, 1)
            
            # غیرفعال کردن همه فیلدها
            for key, input_field in self.visit_inputs.items():
                if hasattr(input_field, 'disabled') and hasattr(input_field, '_hidden_input'):
                    input_field._hidden_input.disabled = True
            
            for key, input_field in self.distributor_inputs.items():
                if hasattr(input_field, 'disabled') and hasattr(input_field, '_hidden_input'):
                    input_field._hidden_input.disabled = True
            
        except Exception as e:
            print(f"خطا در قفل کردن صفحه: {e}")
    
    def unlock_page(self):
        """باز کردن صفحه (فعال کردن دکمه‌ها و فیلدها)"""
        try:
            # فعال کردن دکمه ذخیره
            if hasattr(self, 'save_btn'):
                self.save_btn.disabled = False
                self.save_btn.background_color = (0.2, 0.7, 0.2, 1)
                self.save_btn.color = (1, 1, 1, 1)
            
            # ============================================================
            # فعال کردن دکمه‌ها بر اساس نقش (با رعایت قفل)
            # ============================================================
            # فقط اگر قفل نبود، دکمه‌ها رو فعال کن
            if not self.is_locked:
                if self.user_role == 'موزع':
                    if hasattr(self, 'distributor_btn'):
                        self.distributor_btn.disabled = False
                        self.distributor_btn.background_color = (0.8, 0.5, 0.2, 1)
                        self.distributor_btn.color = (1, 1, 1, 1)
                    
                    if hasattr(self, 'visit_btn'):
                        self.visit_btn.disabled = True
                        self.visit_btn.background_color = (0.2, 0.2, 0.2, 1)
                        self.visit_btn.color = (0.4, 0.4, 0.4, 1)
                else:
                    if hasattr(self, 'visit_btn'):
                        self.visit_btn.disabled = False
                        self.visit_btn.background_color = (0.8, 0.5, 0.2, 1)
                        self.visit_btn.color = (1, 1, 1, 1)
                    
                    if hasattr(self, 'distributor_btn'):
                        self.distributor_btn.disabled = True
                        self.distributor_btn.background_color = (0.2, 0.2, 0.2, 1)
                        self.distributor_btn.color = (0.4, 0.4, 0.4, 1)
            
            # فعال کردن فیلدهای ویزیت
            for key, input_field in self.visit_inputs.items():
                if hasattr(input_field, 'disabled') and hasattr(input_field, '_hidden_input'):
                    if key != 'route_name' and key != 'visit_date':
                        input_field._hidden_input.disabled = False
            
            # فعال کردن فیلدهای توزیع
            for key, input_field in self.distributor_inputs.items():
                if hasattr(input_field, 'disabled') and hasattr(input_field, '_hidden_input'):
                    if key != 'dist_route' and key != 'dist_date':
                        input_field._hidden_input.disabled = False
            
        except Exception as e:
            print(f"خطا در باز کردن صفحه: {e}")
    
    def load_distributor_data(self):
        """بارگذاری داده‌های توزیع از delivery_sale.json"""
        try:
            today = get_today_jalali()
            deliveries = get_deliveries_by_date(today)
            
            if not deliveries:
                return
            
            total_customers = 0          # تعداد کل توزیع‌ها (موفق + ناموفق)
            total_successful = 0         # تعداد توزیع‌های موفق
            total_invoices = 0
            total_amount = 0
            total_cash = 0
            total_check = 0
            total_credit = 0
            total_return_qty = 0
            total_return_amount = 0
            first_time = None
            first_success_time = None
            last_time = None
            start_time = None
            selected_route = None
            
            work_start = self.settings.get('work_start_time', '08:00')
            first_setting = self.settings.get('first_visit_time', '09:00')
            min_hours = self.settings.get('min_daily_hours', 6)
            
            for delivery in deliveries:
                if not isinstance(delivery, dict):
                    continue
                
                route = delivery.get('route', '')
                delivery_time = delivery.get('timestamp', '')
                invoice_amount = delivery.get('invoice_amount', 0)
                returned_amount = delivery.get('returned_amount', 0)
                cash_amount = delivery.get('cash_amount', 0)
                check_amount = delivery.get('check_amount', 0)
                credit_amount = delivery.get('remaining_amount', 0)
                returned_qty = delivery.get('returned_quantity', 0)
                delivery_status = delivery.get('delivery_status', '')
                
                if delivery_time and ' ' in delivery_time:
                    time_part = delivery_time.split(' ')[1]
                else:
                    time_part = delivery_time
                
                if route and not selected_route:
                    selected_route = route
                
                # ============================================================
                # ساعت‌ها
                # ============================================================
                if time_part:
                    if start_time is None:
                        start_time = time_part
                    if first_time is None:
                        first_time = time_part
                    if delivery_status == 'موفق' and first_success_time is None:
                        first_success_time = time_part
                    last_time = time_part
                
                # ============================================================
                # محاسبات آماری
                # ============================================================
                
                # تعداد کل توزیع‌ها (موفق + ناموفق)
                total_customers += 1
                
                # فقط توزیع‌های موفق
                if delivery_status == 'موفق':
                    total_successful += 1
                    total_invoices += 1
                    total_amount += invoice_amount
                    total_cash += cash_amount
                    total_check += check_amount
                    total_credit += credit_amount
                    total_return_qty += returned_qty
                    total_return_amount += returned_amount
            
            # به‌روزرسانی مسیر
            if selected_route:
                self.dist_route_display.set_text(selected_route)
                self.current_route = selected_route
            else:
                self.dist_route_display.set_text('مسیری ثبت نشده است')
                self.current_route = ''
            
            # ========== به‌روزرسانی فیلدهای مقدار ==========
            
            # تعداد فاکتور قابل توزیع = کل توزیع‌ها (موفق + ناموفق)
            self.distributor_inputs['dist_customers'].text = str(total_customers)
            print(f"تعداد فاکتور قابل توزیع (کل): {total_customers}")
            
            # تعداد توزیع موفق = فقط توزیع‌های موفق
            self.distributor_inputs['dist_invoices'].text = str(total_successful)
            print(f"تعداد توزیع موفق: {total_successful}")
            
            # مبالغ
            self.distributor_inputs['dist_amount'].text = f"{total_amount:,.0f}"
            self.distributor_inputs['dist_cash'].text = f"{total_cash:,.0f}"
            self.distributor_inputs['dist_check'].text = f"{total_check:,.0f}"
            self.distributor_inputs['dist_credit'].text = f"{total_credit:,.0f}"
            self.distributor_inputs['dist_return_qty'].text = str(total_return_qty)
            self.distributor_inputs['dist_return_amount'].text = f"{total_return_amount:,.0f}"
            
            print(f"مبلغ کل: {total_amount:,.0f}")
            print(f"مبلغ نقدی: {total_cash:,.0f}")
            print(f"مبلغ چکی: {total_check:,.0f}")
            print(f"تعداد برگشتی: {total_return_qty}")
            print(f"مبلغ برگشتی: {total_return_amount:,.0f}")
            
            # ساعت شروع کار
            if start_time:
                self.distributor_inputs['dist_clock_in'].text = start_time
                print(f"ساعت شروع توزیع: {start_time}")
            else:
                self.distributor_inputs['dist_clock_in'].text = work_start
            
            # ساعت اولین توزیع موفق
            if first_success_time:
                self.distributor_inputs['dist_first_time'].text = first_success_time
                print(f"ساعت اولین توزیع موفق: {first_success_time}")
            else:
                self.distributor_inputs['dist_first_time'].text = first_setting
            
            # ساعت آخرین توزیع
            if last_time:
                self.distributor_inputs['dist_last_time'].text = last_time
                print(f"ساعت آخرین توزیع: {last_time}")
            else:
                self.distributor_inputs['dist_last_time'].text = ''
            
            # ========== ستون هدف ==========
            
            # هدف تعداد فاکتور قابل توزیع
            target_customers = self.settings.get('distributor_target_customers', 30)
            self.dist_target_customers.text = str(target_customers)
            
            # هدف تعداد توزیع موفق
            target_invoices = self.settings.get('distributor_target_invoices', 15)
            self.dist_target_invoices.text = str(target_invoices)
            
            # هدف مبلغ کل توزیع
            target_amount = self.settings.get('distributor_target_amount', 30000000)
            try:
                target_amount = int(target_amount)
            except:
                target_amount = 0
            self.dist_target_amount.text = "{:,}".format(target_amount)
            
            # هدف مبلغ نقدی
            target_cash = self.settings.get('distributor_target_cash', 15000000)
            try:
                target_cash = int(target_cash)
            except:
                target_cash = 0
            self.dist_target_cash.text = "{:,}".format(target_cash)
            
            # هدف مبلغ چکی
            target_check = self.settings.get('distributor_target_check', 10000000)
            try:
                target_check = int(target_check)
            except:
                target_check = 0
            self.dist_target_check.text = "{:,}".format(target_check)
            
            # هدف مبلغ نسیه
            target_credit = self.settings.get('distributor_target_credit', 5000000)
            try:
                target_credit = int(target_credit)
            except:
                target_credit = 0
            self.dist_target_credit.text = "{:,}".format(target_credit)
            
            # ============================================================
            # ساعت هدف آخرین توزیع = ساعت اولین توزیع موفق + حداقل ساعت کاری
            # ============================================================
            if first_success_time:
                try:
                    h, m = map(int, first_success_time.split(':'))
                    total_minutes = h * 60 + m + (min_hours * 60)
                    h_new = total_minutes // 60
                    m_new = total_minutes % 60
                    if h_new >= 24:
                        h_new = h_new - 24
                    last_target = f"{h_new:02d}:{m_new:02d}"
                    self.dist_target_last.text = last_target
                    print(f"هدف ساعت آخرین توزیع (بر اساس اولین توزیع موفق {first_success_time}): {last_target}")
                except:
                    self.dist_target_last.text = '---'
            else:
                # اگر توزیع موفق وجود نداشت، از تنظیمات استفاده کن
                try:
                    h, m = map(int, first_setting.split(':'))
                    total_minutes = h * 60 + m + (min_hours * 60)
                    h_new = total_minutes // 60
                    m_new = total_minutes % 60
                    if h_new >= 24:
                        h_new = h_new - 24
                    last_target = f"{h_new:02d}:{m_new:02d}"
                    self.dist_target_last.text = last_target
                    print(f"هدف ساعت آخرین توزیع (بر اساس تنظیمات {first_setting}): {last_target}")
                except:
                    self.dist_target_last.text = '---'
            
            # ============================================================
            # ساعت هدف پایان توزیع = ساعت شروع کار واقعی + حداقل ساعت کاری + 1
            # ============================================================
            if start_time:
                try:
                    h, m = map(int, start_time.split(':'))
                    total_minutes = h * 60 + m + ((min_hours + 1) * 60)
                    h_new = total_minutes // 60
                    m_new = total_minutes % 60
                    if h_new >= 24:
                        h_new = h_new - 24
                    clock_out_target = f"{h_new:02d}:{m_new:02d}"
                    self.dist_target_clock_out.text = clock_out_target
                    print(f"هدف ساعت پایان توزیع (بر اساس شروع واقعی {start_time}): {clock_out_target}")
                except:
                    # اگر خطا بود، از تنظیمات استفاده کن
                    try:
                        h, m = map(int, work_start.split(':'))
                        total_minutes = h * 60 + m + ((min_hours + 1) * 60)
                        h_new = total_minutes // 60
                        m_new = total_minutes % 60
                        if h_new >= 24:
                            h_new = h_new - 24
                        clock_out_target = f"{h_new:02d}:{m_new:02d}"
                        self.dist_target_clock_out.text = clock_out_target
                        print(f"هدف ساعت پایان توزیع (بر اساس تنظیمات {work_start}): {clock_out_target}")
                    except:
                        self.dist_target_clock_out.text = '---'
            else:
                # اگر ساعت شروع وجود نداشت، از تنظیمات استفاده کن
                try:
                    h, m = map(int, work_start.split(':'))
                    total_minutes = h * 60 + m + ((min_hours + 1) * 60)
                    h_new = total_minutes // 60
                    m_new = total_minutes % 60
                    if h_new >= 24:
                        h_new = h_new - 24
                    clock_out_target = f"{h_new:02d}:{m_new:02d}"
                    self.dist_target_clock_out.text = clock_out_target
                    print(f"هدف ساعت پایان توزیع (بر اساس تنظیمات {work_start}): {clock_out_target}")
                except:
                    self.dist_target_clock_out.text = '---'
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در بارگذاری داده‌های توزیع: {e}", error_details)
    
    def load_data_from_agents(self):
        """بارگذاری داده‌های ویزیت از AgentsScreen"""
        try:
            today = get_today_jalali()
            all_logs = get_daily_logs()
            
            if today not in all_logs:
                return
            
            agent_logs = all_logs[today]
            
            # اگر لاگ‌ها لیست نیستند، تبدیل به لیست کن
            if not isinstance(agent_logs, list):
                agent_logs = []
                all_logs[today] = agent_logs
            
            if not agent_logs:
                return
            
            total_successful_visits = 0
            total_invoices = 0
            total_units = 0
            total_sales = 0
            total_cash = 0
            total_check = 0
            total_credit = 0
            total_new_customers = 0
            first_visit_time = None
            last_visit_time = None
            start_time = None
            selected_route = None
            
            # دریافت تنظیمات
            work_start = self.settings.get('work_start_time', '08:00')
            first_visit_setting = self.settings.get('first_visit_time', '09:00')
            min_hours = self.settings.get('min_daily_hours', 6)
            
            for log in agent_logs:
                if not isinstance(log, dict):
                    continue
                    
                visit_status = log.get('visit_status', '')
                sales_status = log.get('sales_status', '')
                payment_method = log.get('payment_method', '')
                sales_amount = log.get('sales_amount', 0)
                log_time = log.get('time', '')
                route = log.get('route', '')
                
                # شمارش مشتریان جدید
                if log.get('is_new_customer', False):
                    total_new_customers += 1
                
                if route and not selected_route:
                    selected_route = route
                
                if log_time:
                    if start_time is None:
                        start_time = log_time
                    
                    if visit_status == 'موفق' and first_visit_time is None:
                        first_visit_time = log_time
                    
                    if visit_status == 'موفق':
                        last_visit_time = log_time
                
                if visit_status == 'موفق':
                    total_successful_visits += 1
                    
                    if sales_status == 'موفق':
                        total_invoices += 1
                        total_units += log.get('units_sold', 0)
                        total_sales += sales_amount
                        
                        # محاسبه فروش بر اساس نوع تسویه
                        if payment_method == 'نقد':
                            total_cash += sales_amount
                        elif payment_method == 'چک':
                            total_check += sales_amount
                        elif payment_method == 'اعتباری':
                            total_credit += sales_amount
            
            # ذخیره مسیر
            if selected_route:
                self.current_route = selected_route
                self.route_display.set_text(selected_route)
            else:
                self.current_route = ''
                self.route_display.set_text('مسیری ثبت نشده است')
            
            # ========== به‌روزرسانی فیلدهای مقدار ==========
            
            # ساعت شروع کار (از اولین لاگ یا تنظیمات)
            if start_time:
                self.visit_inputs['clock_in'].text = start_time
            else:
                self.visit_inputs['clock_in'].text = work_start
            
            # ساعت اولین ویزیت (از اولین ویزیت موفق یا تنظیمات)
            if first_visit_time:
                self.visit_inputs['first_visit_time'].text = first_visit_time
            else:
                self.visit_inputs['first_visit_time'].text = first_visit_setting
            
            # تعداد مشتری ویزیت شده (فقط ویزیت‌های موفق)
            self.visit_inputs['visited_customers_count'].text = str(total_successful_visits)
            self.visit_inputs['successful_invoices_count'].text = str(total_invoices)
            self.visit_inputs['successful_units_count'].text = str(total_units)
            self.visit_inputs['successful_sales_amount'].text = f"{total_sales:,}"
            
            # فروش نقدی، چکی و اعتباری
            self.visit_inputs['cash_sales'].text = f"{total_cash:,}"
            self.visit_inputs['check_sales'].text = f"{total_check:,}"
            self.visit_inputs['credit_sales'].text = f"{total_credit:,}"
            
            # تعداد مشتری جدید
            self.visit_inputs['new_customers_count'].text = str(total_new_customers)
            self.new_customers_target.text = str(total_new_customers)
            
            if last_visit_time:
                self.visit_inputs['last_visit_time'].text = last_visit_time
            else:
                self.visit_inputs['last_visit_time'].text = ''
            
            # ========== ستون هدف ==========
            
            # هدف تعداد مشتری ویزیت شده (در update_route_info محاسبه میشه)
            self.update_route_info()
            
            # ساعت آخرین ویزیت = ساعت اولین ویزیت + حداقل ساعت کاری
            try:
                h, m = map(int, first_visit_setting.split(':'))
                total_minutes = h * 60 + m + (min_hours * 60)
                h_new = total_minutes // 60
                m_new = total_minutes % 60
                if h_new >= 24:
                    h_new = h_new - 24
                last_visit_target = f"{h_new:02d}:{m_new:02d}"
                self.target_last_visit.text = last_visit_target
            except:
                self.target_last_visit.text = '---'
            
            # ساعت پایان کار = ساعت شروع کار + حداقل ساعت کاری + 1
            try:
                h, m = map(int, work_start.split(':'))
                total_minutes = h * 60 + m + ((min_hours + 1) * 60)
                h_new = total_minutes // 60
                m_new = total_minutes % 60
                if h_new >= 24:
                    h_new = h_new - 24
                clock_out_target = f"{h_new:02d}:{m_new:02d}"
                self.target_clock_out.text = clock_out_target
            except:
                self.target_clock_out.text = '---'
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در بارگذاری داده‌های ویزیت: {e}", error_details)
    
    def update_route_info(self):
        try:
            current_route = self.current_route
            
            if current_route and current_route not in ['', 'مسیری ثبت نشده است']:
                customers = get_customers()
                
                total_customers = 0
                for c in customers:
                    route_name = c.get('route_name', '').strip()
                    if route_name == current_route.strip():
                        total_customers += 1
                
                self.route_count = str(total_customers)
                self.route_customers_target.text = self.route_count
                
                # هدف تعداد مشتری ویزیت شده = تعداد مشتری مسیر × درصد سرکشی
                supervision_rate = self.settings.get('supervision_rate', 0.3)
                
                # اگر عدد بزرگتر از 1 بود، یعنی درصد است (مثلاً 70.0)
                if supervision_rate > 1:
                    supervision_rate = supervision_rate / 100
                
                target_visits = int(total_customers * supervision_rate)
                self.visited_customers_target.text = str(target_visits)
                
                print(f"هدف ویزیت: {total_customers} × {supervision_rate} = {target_visits}")
                
            else:
                self.route_count = '0'
                self.route_customers_target.text = '0'
                self.visited_customers_target.text = '0'
                
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در بروزرسانی اطلاعات مسیر: {e}", error_details)
    
    def save_log(self, instance):
        """ذخیره لاگ نهایی با تأیید پایان کار"""
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            with content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                           size=lambda i, v: setattr(content_rect, 'size', v))
            
            content.add_widget(RTLLabel(
                text='عملیات ذخیره‌سازی به منزلهٔ پایان کار می‌باشد، آیا ادامه می‌دهید؟',
                size_hint_y=None,
                height=dp(70),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))
            
            btn_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(50))
            yes_btn = PersianButton(
                text='بله، پایان کار',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            no_btn = PersianButton(
                text='خیر، انصراف',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            btn_layout.add_widget(yes_btn)
            btn_layout.add_widget(no_btn)
            content.add_widget(btn_layout)
            
            popup = PersianPopup(
                title='تأیید پایان کار',
                content=content,
                size_hint=(0.85, 0.4),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )
            
            def on_yes(instance):
                popup.dismiss()
                self._do_save_log()
            
            def on_no(instance):
                popup.dismiss()
            
            yes_btn.bind(on_press=on_yes)
            no_btn.bind(on_press=on_no)
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش دیالوگ تأیید: {e}", error_details)
    
    def _do_save_log(self):
        """اجرای واقعی ذخیره‌سازی - ذخیره در فایل خلاصه روزانه بر اساس نقش"""
        try:
            log_data = {}
            
            if self.current_tab == 'visit':
                inputs = self.visit_inputs
                date_key = 'visit_date'
                summary_file = 'daily_summary.json'  # برای بازاریاب
            else:
                inputs = self.distributor_inputs
                date_key = 'dist_date'
                summary_file = 'distributor_summary.json'  # برای موزع
            
            for key, input_field in inputs.items():
                if key == 'route_name' or key == 'dist_route':
                    log_data[key] = self.current_route
                elif key in ['successful_sales_amount', 'cash_sales', 'check_sales', 'credit_sales', 
                            'new_customers_count', 'dist_amount', 'dist_cash', 'dist_check', 
                            'dist_credit', 'dist_return_qty', 'dist_return_amount']:
                    value = input_field.text.replace(',', '')
                    log_data[key] = value
                else:
                    log_data[key] = input_field.text
            
            if not log_data.get(date_key):
                self.show_message('خطا', 'تاریخ الزامی است')
                return
            
            current_time = get_current_time()
            if self.current_tab == 'visit':
                inputs['clock_out'].text = current_time
                log_data['clock_out'] = current_time
                if not log_data.get('last_visit_time') or log_data.get('last_visit_time') == '':
                    log_data['last_visit_time'] = current_time
            else:
                inputs['dist_clock_out'].text = current_time
                log_data['dist_clock_out'] = current_time
                if not log_data.get('dist_last_time') or log_data.get('dist_last_time') == '':
                    log_data['dist_last_time'] = current_time
            
            # ذخیره در فایل مناسب بر اساس نقش
            summary_path = os.path.join(get_data_path(), summary_file)
            
            if os.path.exists(summary_path):
                all_summaries = load_json(summary_file)
            else:
                all_summaries = {}
            
            log_date = log_data.get(date_key)
            all_summaries[log_date] = log_data
            
            save_json(summary_file, all_summaries)
            
            # قفل کردن صفحه بعد از ذخیره
            self.is_locked = True
            self.lock_page()
            
            self.show_message('موفق', 'اطلاعات با موفقیت ذخیره شد - صفحه تا پایان روز قفل شد')
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ذخیره‌سازی: {e}", error_details)
    
    def go_to_agents(self, instance):
        self.manager.current = 'agents'
    
    def go_to_report(self, instance):
        """رفتن به صفحه گزارش مناسب بر اساس نقش کاربر"""
        try:
            from kivy.app import App
            
            # دریافت نقش کاربر از App
            app = App.get_running_app()
            if app and hasattr(app, 'current_user_role'):
                if app.current_user_role == 'موزع':
                    self.manager.current = 'distributor_report'
                else:
                    self.manager.current = 'report'
            else:
                # اگر نقش مشخص نبود، پیش‌فرض گزارش بازاریاب
                self.manager.current = 'report'
                
        except Exception as e:
            print(f"خطا در رفتن به گزارش: {e}")
            self.manager.current = 'report'
    
    def logout(self, instance):
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
                height=dp(80),
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
                size_hint=(0.85, 0.4),
                background_color=(0.08, 0.08, 0.08, 1)
            )
            btn.bind(on_press=popup.dismiss)
            popup.open()
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش پیام: {e}", error_details)