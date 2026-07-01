# screens/user_screen.py
# ========== صفحه کاربر (ثبت ویزیت) با اسکرول و انتخاب خودکار متن ==========

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

from utils.rtl_widgets import RTLTextInput, PersianComboBox, PersianButton, RTLLabel
from utils.file_manager import (
    get_routes, get_customers, get_settings, 
    get_daily_logs, save_daily_log,
    load_json, save_json, get_data_path
)
from utils.jalali_date import get_today_jalali, get_current_time
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
            
            # ✅ حالت pan برای مدیریت بهتر کیبورد
            Window.softinput_mode = 'pan'
            
            # ✅ متغیر برای ذخیره فیلدهای قابل فوکوس
            self.focusable_fields = []
            
            self.settings = get_settings()
            self.current_route = ''
            self.is_locked = False
            self.build_ui()
            
            # ✅ اتصال رویدادهای کیبورد
            Window.bind(on_keyboard=self._on_keyboard)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت UserScreen: {e}", error_details)
            raise
    
    def on_enter(self):
        """هر بار که صفحه UserScreen نمایش داده میشه، اجرا میشه"""
        try:
            print("🔄 ورود به UserScreen - به‌روزرسانی اطلاعات")
            
            # دریافت مجدد تنظیمات
            self.settings = get_settings()
            
            # بارگذاری مجدد داده‌ها از AgentsScreen
            self.load_data_from_agents()
            
            # آپدیت هدف ویزیت
            self.update_route_info()
            
            # بررسی قفل بودن صفحه
            self.check_if_locked()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در به‌روزرسانی UserScreen: {e}", error_details)
    
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
            self._scroll_to_field(instance)
    
    def _select_all_text(self, instance):
        """انتخاب کل متن فیلد"""
        if instance and hasattr(instance, 'select_all'):
            instance.select_all()
    
    def _scroll_to_field(self, instance):
        """اسکرول به موقعیت فیلد"""
        try:
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
            
            field_pos = instance.to_window(0, 0)
            
            if field_pos[1] < 100:
                content_height = scroll.children[0].height if scroll.children else 1
                if content_height > scroll.height:
                    scroll.scroll_y = 0.3
            
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
            
            content = BoxLayout(
                orientation='vertical',
                padding=[dp(5), dp(5), dp(5), dp(5)],
                size_hint_y=None
            )
            content.bind(minimum_height=content.setter('height'))
            
            self.form_layout = GridLayout(
                cols=3,
                spacing=dp(4),
                size_hint_y=None,
                padding=dp(5)
            )
            self.form_layout.bind(minimum_height=self.form_layout.setter('height'))
            
            routes = get_routes()
            self.route_names = [r.get('name', '') for r in routes] if routes else ['']
            
            # ========== هدرها ==========
            self.form_layout.add_widget(RTLLabel(
                text='آیتم',
                size_hint_y=None,
                height=dp(35),
                bold=True,
                color=(0.4, 0.7, 1, 1),
                font_size=sp(15)
            ))
            self.form_layout.add_widget(RTLLabel(
                text='مقدار',
                size_hint_y=None,
                height=dp(35),
                bold=True,
                color=(0.4, 0.7, 1, 1),
                font_size=sp(15)
            ))
            self.form_layout.add_widget(RTLLabel(
                text='هدف',
                size_hint_y=None,
                height=dp(35),
                bold=True,
                color=(0.4, 0.7, 1, 1),
                font_size=sp(15)
            ))
            
            self.inputs = {}
            
            # ========== 1️⃣ تاریخ ویزیت ==========
            self.form_layout.add_widget(RTLLabel(
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
                height=dp(55),
                font_size=sp(36)
            )
            visit_date.bg_color = (0.15, 0.15, 0.15, 1)
            visit_date.border_color = (0.3, 0.3, 0.3, 1)
            visit_date.border_color_focus = (0.2, 0.5, 0.9, 1)
            visit_date._hidden_input.foreground_color = (1, 1, 1, 1)
            visit_date._hidden_input.disabled = True
            self.form_layout.add_widget(visit_date)
            
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
            self.form_layout.add_widget(self.target_visit_date)
            self.inputs['visit_date'] = visit_date
            
            # ========== 2️⃣ مسیر ویزیت ==========
            self.form_layout.add_widget(RTLLabel(
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
            self.form_layout.add_widget(self.route_display)
            
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
            self.form_layout.add_widget(self.route_customers_target)
            self.inputs['route_name'] = self.route_display
            
            # ========== 3️⃣ ساعت شروع کار ==========
            self.form_layout.add_widget(RTLLabel(
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
                height=dp(55),
                font_size=sp(36)
            )
            clock_in.bg_color = (0.15, 0.15, 0.15, 1)
            clock_in.border_color = (0.3, 0.3, 0.3, 1)
            clock_in.border_color_focus = (0.2, 0.5, 0.9, 1)
            clock_in._hidden_input.foreground_color = (1, 1, 1, 1)
            clock_in._hidden_input.disabled = True
            self.form_layout.add_widget(clock_in)
            
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
            self.form_layout.add_widget(self.target_clock_in)
            self.inputs['clock_in'] = clock_in
            
            # ========== 4️⃣ ساعت اولین ویزیت ==========
            self.form_layout.add_widget(RTLLabel(
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
                height=dp(55),
                font_size=sp(36)
            )
            first_visit_time.bg_color = (0.15, 0.15, 0.15, 1)
            first_visit_time.border_color = (0.3, 0.3, 0.3, 1)
            first_visit_time.border_color_focus = (0.2, 0.5, 0.9, 1)
            first_visit_time._hidden_input.foreground_color = (1, 1, 1, 1)
            first_visit_time._hidden_input.disabled = True
            self.form_layout.add_widget(first_visit_time)
            
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
            self.form_layout.add_widget(self.target_first_visit)
            self.inputs['first_visit_time'] = first_visit_time
            
            # ========== 5️⃣ تعداد مشتری ویزیت شده ==========
            self.form_layout.add_widget(RTLLabel(
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
                height=dp(55),
                input_filter='int',
                font_size=sp(36)
            )
            visited_count.bg_color = (0.15, 0.15, 0.15, 1)
            visited_count.border_color = (0.3, 0.3, 0.3, 1)
            visited_count.border_color_focus = (0.2, 0.5, 0.9, 1)
            visited_count._hidden_input.foreground_color = (1, 1, 1, 1)
            visited_count._hidden_input.disabled = True
            self.form_layout.add_widget(visited_count)
            
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
            self.form_layout.add_widget(self.visited_customers_target)
            self.inputs['visited_customers_count'] = visited_count
            
            # ========== 6️⃣ تعداد فاکتور موفق ==========
            self.form_layout.add_widget(RTLLabel(
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
                height=dp(55),
                input_filter='int',
                font_size=sp(36)
            )
            invoices_count.bg_color = (0.15, 0.15, 0.15, 1)
            invoices_count.border_color = (0.3, 0.3, 0.3, 1)
            invoices_count.border_color_focus = (0.2, 0.5, 0.9, 1)
            invoices_count._hidden_input.foreground_color = (1, 1, 1, 1)
            invoices_count._hidden_input.disabled = True
            self.form_layout.add_widget(invoices_count)
            
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
            self.form_layout.add_widget(self.target_invoices)
            self.inputs['successful_invoices_count'] = invoices_count
            
            # ========== 7️⃣ تعداد واحد فروش موفق ==========
            self.form_layout.add_widget(RTLLabel(
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
                height=dp(55),
                input_filter='int',
                font_size=sp(36)
            )
            units_count.bg_color = (0.15, 0.15, 0.15, 1)
            units_count.border_color = (0.3, 0.3, 0.3, 1)
            units_count.border_color_focus = (0.2, 0.5, 0.9, 1)
            units_count._hidden_input.foreground_color = (1, 1, 1, 1)
            units_count._hidden_input.disabled = True
            self.form_layout.add_widget(units_count)
            
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
            self.form_layout.add_widget(self.target_units)
            self.inputs['successful_units_count'] = units_count
            
            # ========== 8️⃣ مبلغ فروش موفق ==========
            self.form_layout.add_widget(RTLLabel(
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
                height=dp(55),
                input_filter='int',
                font_size=sp(36)
            )
            sales_amount.bg_color = (0.15, 0.15, 0.15, 1)
            sales_amount.border_color = (0.3, 0.3, 0.3, 1)
            sales_amount.border_color_focus = (0.2, 0.5, 0.9, 1)
            sales_amount._hidden_input.foreground_color = (1, 1, 1, 1)
            sales_amount._hidden_input.disabled = True
            self.form_layout.add_widget(sales_amount)
            
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
            self.form_layout.add_widget(self.target_sales)
            self.inputs['successful_sales_amount'] = sales_amount
            
            # ========== 9️⃣ ساعت آخرین ویزیت ==========
            self.form_layout.add_widget(RTLLabel(
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
                height=dp(55),
                font_size=sp(36)
            )
            last_visit_time.bg_color = (0.15, 0.15, 0.15, 1)
            last_visit_time.border_color = (0.3, 0.3, 0.3, 1)
            last_visit_time.border_color_focus = (0.2, 0.5, 0.9, 1)
            last_visit_time._hidden_input.foreground_color = (1, 1, 1, 1)
            last_visit_time._hidden_input.disabled = True
            self.form_layout.add_widget(last_visit_time)
            
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
            self.form_layout.add_widget(self.target_last_visit)
            self.inputs['last_visit_time'] = last_visit_time
            
            # ========== 🔟 ساعت پایان کار ==========
            self.form_layout.add_widget(RTLLabel(
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
                height=dp(55),
                font_size=sp(36)
            )
            clock_out.bg_color = (0.15, 0.15, 0.15, 1)
            clock_out.border_color = (0.3, 0.3, 0.3, 1)
            clock_out.border_color_focus = (0.2, 0.5, 0.9, 1)
            clock_out._hidden_input.foreground_color = (1, 1, 1, 1)
            clock_out._hidden_input.disabled = True
            self.form_layout.add_widget(clock_out)
            
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
            self.form_layout.add_widget(self.target_clock_out)
            self.inputs['clock_out'] = clock_out
            
            # ========== اضافه کردن فرم به محتوا ==========
            content.add_widget(self.form_layout)
            
            # ========== دکمه‌ها ==========
            btn_layout = BoxLayout(
                size_hint_y=None,
                height=dp(50),
                spacing=dp(5),
                padding=dp(5)
            )
            
            self.visit_btn = PersianButton(
                text='📋 ویزیت',
                background_color=(0.8, 0.5, 0.2, 1),
                size_hint_y=None,
                height=dp(42),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            self.visit_btn.bind(on_press=self.go_to_agents)
            btn_layout.add_widget(self.visit_btn)
            
            self.save_btn = PersianButton(
                text='💾 ذخیره',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(42),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            self.save_btn.bind(on_press=self.save_log)
            btn_layout.add_widget(self.save_btn)
            
            report_btn = PersianButton(
                text='📊 گزارش',
                background_color=(0.2, 0.6, 1, 1),
                size_hint_y=None,
                height=dp(42),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            report_btn.bind(on_press=self.go_to_report)
            btn_layout.add_widget(report_btn)
            
            logout_btn = PersianButton(
                text='🚪 خروج',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(42),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            logout_btn.bind(on_press=self.logout)
            btn_layout.add_widget(logout_btn)
            
            scroll.add_widget(content)
            main_layout.add_widget(scroll)
            main_layout.add_widget(btn_layout)
            
            self.add_widget(main_layout)
            
            # بارگذاری داده‌ها از AgentsScreen
            Clock.schedule_once(lambda dt: self.load_data_from_agents(), 0.5)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت UI UserScreen: {e}", error_details)
            raise
    
    def check_if_locked(self):
        """بررسی اینکه آیا امروز قبلاً ذخیره شده یا نه"""
        try:
            today = get_today_jalali()
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
            print(f"⚠️ خطا در بررسی قفل: {e}")
    
    def lock_page(self):
        """قفل کردن صفحه (غیرفعال کردن دکمه‌ها و فیلدها)"""
        try:
            # غیرفعال کردن دکمه ذخیره
            if hasattr(self, 'save_btn'):
                self.save_btn.disabled = True
                self.save_btn.background_color = (0.3, 0.3, 0.3, 1)
                self.save_btn.color = (0.5, 0.5, 0.5, 1)
            
            # غیرفعال کردن دکمه ویزیت
            if hasattr(self, 'visit_btn'):
                self.visit_btn.disabled = True
                self.visit_btn.background_color = (0.3, 0.3, 0.3, 1)
                self.visit_btn.color = (0.5, 0.5, 0.5, 1)
            
            # غیرفعال کردن همه فیلدها
            for key, input_field in self.inputs.items():
                if hasattr(input_field, 'disabled') and hasattr(input_field, '_hidden_input'):
                    input_field._hidden_input.disabled = True
            
        except Exception as e:
            print(f"⚠️ خطا در قفل کردن صفحه: {e}")
    
    def unlock_page(self):
        """باز کردن صفحه (فعال کردن دکمه‌ها و فیلدها)"""
        try:
            # فعال کردن دکمه ذخیره
            if hasattr(self, 'save_btn'):
                self.save_btn.disabled = False
                self.save_btn.background_color = (0.2, 0.7, 0.2, 1)
                self.save_btn.color = (1, 1, 1, 1)
            
            # فعال کردن دکمه ویزیت
            if hasattr(self, 'visit_btn'):
                self.visit_btn.disabled = False
                self.visit_btn.background_color = (0.8, 0.5, 0.2, 1)
                self.visit_btn.color = (1, 1, 1, 1)
            
            # فعال کردن فیلدهای غیرضروری (فقط فیلدهایی که باید قابل تغییر باشن)
            for key, input_field in self.inputs.items():
                if hasattr(input_field, 'disabled') and hasattr(input_field, '_hidden_input'):
                    # فقط فیلد route_name رو غیرفعال نگه دار
                    if key != 'route_name':
                        input_field._hidden_input.disabled = False
            
        except Exception as e:
            print(f"⚠️ خطا در باز کردن صفحه: {e}")
    
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
                log_time = log.get('time', '')
                route = log.get('route', '')
                
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
                    
                    sales_status = log.get('sales_status', '')
                    if sales_status == 'موفق':
                        total_invoices += 1
                        total_units += log.get('units_sold', 0)
                        total_sales += log.get('sales_amount', 0)
            
            # ذخیره مسیر
            if selected_route:
                self.current_route = selected_route
                self.route_display.set_text(selected_route)
            else:
                self.current_route = ''
                self.route_display.set_text('⚠️ مسیری ثبت نشده است')
            
            # ========== به‌روزرسانی فیلدهای مقدار ==========
            
            # ساعت شروع کار (از اولین لاگ یا تنظیمات)
            if start_time:
                self.inputs['clock_in'].text = start_time
            else:
                self.inputs['clock_in'].text = work_start
            
            # ساعت اولین ویزیت (از اولین ویزیت موفق یا تنظیمات)
            if first_visit_time:
                self.inputs['first_visit_time'].text = first_visit_time
            else:
                self.inputs['first_visit_time'].text = first_visit_setting
            
            # تعداد مشتری ویزیت شده (فقط ویزیت‌های موفق)
            self.inputs['visited_customers_count'].text = str(total_successful_visits)
            self.inputs['successful_invoices_count'].text = str(total_invoices)
            self.inputs['successful_units_count'].text = str(total_units)
            self.inputs['successful_sales_amount'].text = f"{total_sales:,}"
            
            if last_visit_time:
                self.inputs['last_visit_time'].text = last_visit_time
            else:
                self.inputs['last_visit_time'].text = ''
            
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
            
            if current_route and current_route not in ['', '⚠️ مسیری ثبت نشده است']:
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
                
                print(f"✅ هدف ویزیت: {total_customers} × {supervision_rate} = {target_visits}")
                
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
                text='انجام عملیات ذخیره‌سازی به منزلهٔ پایان کار می‌باشد.\nآیا از انجام این کار اطمینان دارید؟',
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
                color=(1, 1, 1, 1)
            )
            no_btn = PersianButton(
                text='خیر، انصراف',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1)
            )
            btn_layout.add_widget(yes_btn)
            btn_layout.add_widget(no_btn)
            content.add_widget(btn_layout)
            
            popup = Popup(
                title='تأیید پایان کار',
                content=content,
                size_hint=(0.85, 0.4),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )
            popup.title_color = (1, 1, 1, 1)
            
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
        """اجرای واقعی ذخیره‌سازی - ذخیره در فایل خلاصه روزانه"""
        try:
            log_data = {}
            
            for key, input_field in self.inputs.items():
                if key == 'route_name':
                    log_data[key] = self.current_route
                elif key == 'successful_sales_amount':
                    value = input_field.text.replace(',', '')
                    log_data[key] = value
                else:
                    log_data[key] = input_field.text
            
            if not log_data.get('visit_date'):
                self.show_message('خطا', 'تاریخ ویزیت الزامی است')
                return
            
            current_time = get_current_time()
            self.inputs['clock_out'].text = current_time
            log_data['clock_out'] = current_time
            
            if not log_data.get('last_visit_time') or log_data.get('last_visit_time') == '':
                log_data['last_visit_time'] = current_time
            
            # ذخیره در فایل خلاصه روزانه (جدا از لاگ‌های ویزیت)
            summary_file = 'daily_summary.json'
            summary_path = os.path.join(get_data_path(), summary_file)
            
            if os.path.exists(summary_path):
                all_summaries = load_json(summary_file)
            else:
                all_summaries = {}
            
            visit_date = log_data.get('visit_date')
            all_summaries[visit_date] = log_data
            
            save_json(summary_file, all_summaries)
            
            # قفل کردن صفحه بعد از ذخیره
            self.is_locked = True
            self.lock_page()
            
            self.show_message('موفق', 'اطلاعات با موفقیت ذخیره شد\nصفحه تا پایان روز قفل شد')
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ذخیره‌سازی: {e}", error_details)
    
    def go_to_agents(self, instance):
        self.manager.current = 'agents'
    
    def go_to_report(self, instance):
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
                font_size=sp(22),
                color=(1, 1, 1, 1),
                background_color=(0.2, 0.6, 1, 1)
            )
            content.add_widget(btn)
            popup = Popup(
                title=title,
                content=content,
                size_hint=(0.85, 0.4),
                background_color=(0.08, 0.08, 0.08, 1)
            )
            popup.title_color = (1, 1, 1, 1)
            popup.title_size = sp(24)
            btn.bind(on_press=popup.dismiss)
            popup.open()
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش پیام: {e}", error_details)