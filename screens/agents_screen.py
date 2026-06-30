# screens/agents_screen.py
# ========== صفحه ثبت ویزیت بازاریابان ==========

import traceback
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window

from utils.rtl_widgets import RTLTextInput, PersianComboBox, PersianButton, RTLLabel
from utils.file_manager import get_routes, get_customers, get_settings, save_daily_log, get_daily_logs
from utils.jalali_date import get_today_jalali, get_current_time
from error_handler import ErrorPopup


class AgentsScreen(Screen):
    def __init__(self, **kwargs):
        try:
            super().__init__(**kwargs)
            # پس‌زمینه تیره
            with self.canvas.before:
                Color(0.08, 0.08, 0.08, 1)
                self.bg_rect = Rectangle(pos=self.pos, size=self.size)
                self.bind(pos=self._update_bg, size=self._update_bg)
            
            Window.softinput_mode = 'pan'
            self.settings = get_settings()
            self.selected_customer = None
            self.selected_route = None
            self._last_search_text = ''
            self.build_ui()
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت AgentsScreen: {e}", error_details)
            raise
    
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def build_ui(self):
        try:
            main_layout = BoxLayout(orientation='vertical')
            
            # ========== ScrollView برای محتوا ==========
            scroll = ScrollView(
                do_scroll_x=False,
                do_scroll_y=True,
                size_hint=(1, 1)
            )
            
            content = BoxLayout(
                orientation='vertical',
                padding=dp(15),
                spacing=dp(8),
                size_hint_y=None
            )
            content.bind(minimum_height=content.setter('height'))
            
            # ========== عنوان صفحه ==========
            content.add_widget(RTLLabel(
                text='📋 ثبت ویزیت بازاریابان',
                font_size=sp(22),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                bold=True
            ))
            
            content.add_widget(Label(size_hint_y=None, height=dp(5)))
            
            # ========== 1️⃣ تاریخ (غیر قابل تغییر) ==========
            content.add_widget(RTLLabel(
                text='📅 تاریخ:',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(16),
                color=(0.4, 0.7, 1, 1),
                bold=True
            ))
            self.date_label = RTLLabel(
                text=get_today_jalali(),
                size_hint_y=None,
                height=dp(40),
                font_size=sp(20),
                color=(1, 1, 1, 1)
            )
            content.add_widget(self.date_label)
            
            content.add_widget(Label(size_hint_y=None, height=dp(5)))
            
            # ========== 2️⃣ ساعت (غیر قابل تغییر) ==========
            content.add_widget(RTLLabel(
                text='🕐 ساعت:',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(16),
                color=(0.4, 0.7, 1, 1),
                bold=True
            ))
            self.time_label = RTLLabel(
                text=get_current_time(),
                size_hint_y=None,
                height=dp(40),
                font_size=sp(20),
                color=(1, 1, 1, 1)
            )
            content.add_widget(self.time_label)
            
            content.add_widget(Label(size_hint_y=None, height=dp(5)))
            
            # ========== 3️⃣ مسیر (کمبوباکس) ==========
            content.add_widget(RTLLabel(
                text='🗺️ انتخاب مسیر:',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(16),
                color=(0.4, 0.7, 1, 1),
                bold=True
            ))
            
            routes = get_routes()
            route_names = [r.get('name', '') for r in routes] if routes else ['']
            
            self.route_spinner = PersianComboBox(
                text=route_names[0] if route_names else '',
                values=route_names,
                height=dp(50)
            )
            self.route_spinner.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.route_spinner.main_btn.color = (1, 1, 1, 1)
            self.route_spinner.main_btn.font_size = sp(18)
            self._last_route_text = self.route_spinner.text
            Clock.schedule_interval(self._check_route_change, 0.3)
            content.add_widget(self.route_spinner)
            
            content.add_widget(Label(size_hint_y=None, height=dp(5)))
            
            # ========== 4️⃣ مشتری (کمبوباکس) ==========
            content.add_widget(RTLLabel(
                text='👤 انتخاب مشتری:',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(16),
                color=(0.4, 0.7, 1, 1),
                bold=True
            ))
            
            self.customer_spinner = PersianComboBox(
                text='',
                values=[''],
                height=dp(50)
            )
            self.customer_spinner.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.customer_spinner.main_btn.color = (1, 1, 1, 1)
            self.customer_spinner.main_btn.font_size = sp(18)
            self.customer_spinner.main_btn.halign = 'center'
            self.customer_spinner.main_btn.valign = 'middle'
            self.customer_spinner.main_btn.text_size = (None, None)
            self._last_customer_text = self.customer_spinner.text
            Clock.schedule_interval(self._check_customer_change, 0.3)
            content.add_widget(self.customer_spinner)
            
            content.add_widget(Label(size_hint_y=None, height=dp(10)))

            # ========== جستجوی مشتری ==========
            content.add_widget(RTLLabel(
                text='🔍 جستجوی مشتری:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(14),
                color=(0.4, 0.7, 1, 1),
                bold=True
            ))

            self.search_input = RTLTextInput(
                hint_text='نام مشتری را وارد کنید...',
                multiline=False,
                size_hint_y=None,
                height=dp(45),
                font_size=sp(32)
            )
            self.search_input.foreground_color = (1, 1, 1, 1)
            self.search_input.background_color = (0.2, 0.2, 0.2, 1)
            self.search_input.hint_text_color = (0.5, 0.5, 0.5, 1)
            # ❌ self.search_input.bind(text=self.filter_customers) - حذف شد
            content.add_widget(self.search_input)
            
            # ✅ بررسی تغییرات جستجو با Clock
            self._last_search_text = ''
            Clock.schedule_interval(self._check_search_change, 0.3)
            
            # ========== دکمه بازگشت ==========
            back_btn = PersianButton(
                text='🔙 بازگشت',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1)
            )
            back_btn.bind(on_press=self.go_back)
            content.add_widget(back_btn)
            
            scroll.add_widget(content)
            main_layout.add_widget(scroll)
            self.add_widget(main_layout)
            
            # به‌روزرسانی لیست مشتریان با مسیر اولیه
            Clock.schedule_once(lambda dt: self.update_customers_list(), 0.5)
            # بروزرسانی ساعت هر دقیقه
            Clock.schedule_interval(self.update_time, 60)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت UI AgentsScreen: {e}", error_details)
            raise
    
    def _check_search_change(self, dt):
        """بررسی تغییر متن جستجو با Clock"""
        if hasattr(self, 'search_input'):
            current_text = self.search_input.text
            if current_text != self._last_search_text:
                self._last_search_text = current_text
                self.filter_customers(current_text)
    
    def filter_customers(self, search_text):
        """فیلتر مشتریان بر اساس متن جستجو"""
        try:
            search_text = search_text.strip()
            all_customers = get_customers()
            selected_route = self.route_spinner.text
            
            # فیلتر بر اساس مسیر
            route_customers = []
            for c in all_customers:
                if c.get('route_name', '').strip() == selected_route.strip():
                    route_customers.append(c.get('name', ''))
            
            # فیلتر بر اساس متن جستجو
            if search_text:
                filtered = [c for c in route_customers if search_text in c]
            else:
                filtered = route_customers
            
            if filtered:
                self.customer_spinner.values = filtered
                self.customer_spinner.text = filtered[0] if filtered else ''
            else:
                self.customer_spinner.values = ['⚠️ مشتری‌ای یافت نشد']
                self.customer_spinner.text = '⚠️ مشتری‌ای یافت نشد'
                
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در جستجوی مشتری: {e}", error_details)

    def _check_route_change(self, dt):
        """بررسی تغییر مسیر با Clock"""
        if hasattr(self, 'route_spinner'):
            current_text = self.route_spinner.text
            if current_text != self._last_route_text:
                self._last_route_text = current_text
                self.on_route_selected(current_text)
    
    def _check_customer_change(self, dt):
        """بررسی تغییر مشتری با Clock"""
        if hasattr(self, 'customer_spinner'):
            current_text = self.customer_spinner.text
            if current_text != self._last_customer_text:
                self._last_customer_text = current_text
                if current_text and current_text not in ['', '⚠️ مشتری‌ای یافت نشد']:
                    self.on_customer_selected(current_text)
    
    def update_time(self, dt):
        """بروزرسانی ساعت"""
        self.time_label.text = get_current_time()
    
    def on_route_selected(self, value):
        """زمانی که مسیر انتخاب می‌شود"""
        self.selected_route = value
        
        # قفل کردن مسیر بعد از انتخاب (فقط اگر قبلاً قفل نشده باشه)
        if not self.route_spinner.main_btn.disabled:
            self.route_spinner.main_btn.disabled = True
            self.route_spinner.main_btn.background_color = (0.15, 0.15, 0.15, 1)
            self.route_spinner.main_btn.color = (0.6, 0.6, 0.6, 1)
        
        self.update_customers_list()
    
    def update_customers_list(self):
        """به‌روزرسانی لیست مشتریان بر اساس مسیر انتخاب شده"""
        try:
            if not hasattr(self, 'customer_spinner'):
                return
                
            selected_route = self.route_spinner.text
            all_customers = get_customers()
            
            filtered = []
            for c in all_customers:
                if c.get('route_name', '').strip() == selected_route.strip():
                    filtered.append(c.get('name', ''))
            
            if filtered:
                self.customer_spinner.values = filtered
                self.customer_spinner.text = filtered[0] if filtered else ''
            else:
                self.customer_spinner.values = ['⚠️ مشتری‌ای یافت نشد']
                self.customer_spinner.text = '⚠️ مشتری‌ای یافت نشد'
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در بروزرسانی لیست مشتریان: {e}", error_details)
    
    def on_customer_selected(self, value):
        """زمانی که مشتری انتخاب می‌شود - نمایش دیالوگ تأیید"""
        if value and value not in ['', '⚠️ مشتری‌ای یافت نشد']:
            self.selected_customer = value
            self.show_confirm_dialog(value)
    
    def show_confirm_dialog(self, customer_name):
        """دیالوگ تأیید ویزیت برای مشتری"""
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            with content.canvas.before:
                Color(0.15, 0.15, 0.15, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                           size=lambda i, v: setattr(content_rect, 'size', v))
            
            content.add_widget(RTLLabel(
                text=f'آیا برای "{customer_name}" ویزیت ثبت می‌نمایید؟',
                size_hint_y=None,
                height=dp(50),
                font_size=sp(18),
                color=(1, 1, 1, 1)
            ))
            
            btn_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(50))
            
            yes_btn = PersianButton(
                text='بله',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1)
            )
            no_btn = PersianButton(
                text='خیر',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1)
            )
            
            btn_layout.add_widget(yes_btn)
            btn_layout.add_widget(no_btn)
            content.add_widget(btn_layout)
            
            popup = Popup(
                title='تأیید ویزیت',
                content=content,
                size_hint=(0.85, 0.35),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )
            popup.title_color = (1, 1, 1, 1)
            
            def on_yes(instance):
                popup.dismiss()
                self.show_visit_result_dialog(customer_name)
            
            def on_no(instance):
                popup.dismiss()
                self.customer_spinner.text = ''
                self._last_customer_text = ''
            
            yes_btn.bind(on_press=on_yes)
            no_btn.bind(on_press=on_no)
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش دیالوگ تأیید: {e}", error_details)
    
    def show_visit_result_dialog(self, customer_name):
        """دیالوگ نتیجه ویزیت (موفق/ناموفق)"""
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            with content.canvas.before:
                Color(0.15, 0.15, 0.15, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                           size=lambda i, v: setattr(content_rect, 'size', v))
            
            content.add_widget(RTLLabel(
                text=f'نتیجه ویزیت برای "{customer_name}":',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(18),
                color=(1, 1, 1, 1)
            ))
            
            btn_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(50))
            
            success_btn = PersianButton(
                text='✅ ویزیت موفق',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1)
            )
            fail_btn = PersianButton(
                text='❌ ویزیت ناموفق',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1)
            )
            
            btn_layout.add_widget(success_btn)
            btn_layout.add_widget(fail_btn)
            content.add_widget(btn_layout)
            
            back_btn = PersianButton(
                text='🔙 بازگشت',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(40),
                color=(1, 1, 1, 1)
            )
            content.add_widget(back_btn)
            
            popup = Popup(
                title='نتیجه ویزیت',
                content=content,
                size_hint=(0.85, 0.5),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )
            popup.title_color = (1, 1, 1, 1)
            
            def on_success(instance):
                popup.dismiss()
                self.show_sales_result_dialog(customer_name)
            
            def on_fail(instance):
                popup.dismiss()
                self.show_fail_reason_dialog(customer_name)
            
            def on_back(instance):
                popup.dismiss()
            
            success_btn.bind(on_press=on_success)
            fail_btn.bind(on_press=on_fail)
            back_btn.bind(on_press=on_back)
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش دیالوگ نتیجه ویزیت: {e}", error_details)
    
    def show_fail_reason_dialog(self, customer_name):
        """دیالوگ علت ویزیت ناموفق"""
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            with content.canvas.before:
                Color(0.15, 0.15, 0.15, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                           size=lambda i, v: setattr(content_rect, 'size', v))
            
            content.add_widget(RTLLabel(
                text='📝 علت ویزیت ناموفق را وارد کنید:',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))
            
            reason_input = RTLTextInput(
                hint_text='متن علت...',
                size_hint_y=None,
                height=dp(100),
                font_size=sp(36)
            )
            reason_input.foreground_color = (1, 1, 1, 1)
            reason_input.background_color = (0.2, 0.2, 0.2, 1)
            reason_input.hint_text_color = (0.5, 0.5, 0.5, 1)
            content.add_widget(reason_input)
            
            btn_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(50))
            
            submit_btn = PersianButton(
                text='✅ ثبت عملیات',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1)
            )
            back_btn = PersianButton(
                text='🔙 بازگشت',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1)
            )
            
            btn_layout.add_widget(submit_btn)
            btn_layout.add_widget(back_btn)
            content.add_widget(btn_layout)
            
            popup = Popup(
                title='علت ویزیت ناموفق',
                content=content,
                size_hint=(0.85, 0.5),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )
            popup.title_color = (1, 1, 1, 1)
            
            def on_submit(instance):
                reason = reason_input.text.strip()
                if not reason:
                    ErrorPopup.show_error('لطفاً علت را وارد کنید')
                    return
                
                self.save_visit_log(
                    customer_name=customer_name,
                    visit_status='ناموفق',
                    fail_reason=reason
                )
                popup.dismiss()
                self.show_message('موفق', f'ویزیت ناموفق برای "{customer_name}" ثبت شد')
                self.reset_form()
            
            def on_back(instance):
                popup.dismiss()
                self.show_visit_result_dialog(customer_name)
            
            submit_btn.bind(on_press=on_submit)
            back_btn.bind(on_press=on_back)
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش دیالوگ علت ناموفق: {e}", error_details)
    
    def show_sales_result_dialog(self, customer_name):
        """دیالوگ نتیجه فروش (موفق/ناموفق)"""
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            with content.canvas.before:
                Color(0.15, 0.15, 0.15, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                           size=lambda i, v: setattr(content_rect, 'size', v))
            
            content.add_widget(RTLLabel(
                text=f'نتیجه فروش برای "{customer_name}":',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(18),
                color=(1, 1, 1, 1)
            ))
            
            btn_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(50))
            
            success_btn = PersianButton(
                text='💰 فروش موفق',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1)
            )
            fail_btn = PersianButton(
                text='❌ فروش ناموفق',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1)
            )
            
            btn_layout.add_widget(success_btn)
            btn_layout.add_widget(fail_btn)
            content.add_widget(btn_layout)
            
            back_btn = PersianButton(
                text='🔙 بازگشت',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(40),
                color=(1, 1, 1, 1)
            )
            content.add_widget(back_btn)
            
            popup = Popup(
                title='نتیجه فروش',
                content=content,
                size_hint=(0.85, 0.45),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )
            popup.title_color = (1, 1, 1, 1)
            
            def on_success(instance):
                popup.dismiss()
                self.show_success_sales_dialog(customer_name)
            
            def on_fail(instance):
                popup.dismiss()
                self.show_fail_sales_reason_dialog(customer_name)
            
            def on_back(instance):
                popup.dismiss()
                self.show_visit_result_dialog(customer_name)
            
            success_btn.bind(on_press=on_success)
            fail_btn.bind(on_press=on_fail)
            back_btn.bind(on_press=on_back)
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش دیالوگ نتیجه فروش: {e}", error_details)
    
    def show_fail_sales_reason_dialog(self, customer_name):
        """دیالوگ علت فروش ناموفق با کمبوباکس"""
        try:
            fail_reasons = [
                'موکول به زمان دیگر',
                'عدم نیاز مشتری',
                'شاکی بودن مشتری',
                'وجود مغایرت',
                'عدم ایجاد ارتباط مناسب',
                'سایر علل'
            ]
            
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            with content.canvas.before:
                Color(0.15, 0.15, 0.15, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                           size=lambda i, v: setattr(content_rect, 'size', v))
            
            content.add_widget(RTLLabel(
                text='علت فروش ناموفق:',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))
            
            reason_spinner = PersianComboBox(
                text=fail_reasons[0],
                values=fail_reasons,
                height=dp(45)
            )
            reason_spinner.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            reason_spinner.main_btn.color = (1, 1, 1, 1)
            reason_spinner.main_btn.font_size = sp(18)
            content.add_widget(reason_spinner)
            
            # فیلد توضیحات (برای سایر علل)
            description_input = RTLTextInput(
                hint_text='توضیحات (در صورت انتخاب سایر علل)',
                multiline=False,
                size_hint_y=None,
                height=dp(50),
                font_size=sp(36)
            )
            description_input.foreground_color = (1, 1, 1, 1)
            description_input.background_color = (0.2, 0.2, 0.2, 1)
            description_input.hint_text_color = (0.5, 0.5, 0.5, 1)
            description_input.disabled = True
            content.add_widget(description_input)
            
            self._last_reason_text = reason_spinner.text
            
            def check_reason_change(dt):
                if hasattr(self, '_last_reason_text'):
                    current = reason_spinner.text
                    if current != self._last_reason_text:
                        self._last_reason_text = current
                        description_input.disabled = (current != 'سایر علل')
                        if description_input.disabled:
                            description_input.text = ''
            
            Clock.schedule_interval(check_reason_change, 0.3)
            
            btn_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(50))
            
            submit_btn = PersianButton(
                text='✅ ثبت عملیات',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1)
            )
            back_btn = PersianButton(
                text='🔙 بازگشت',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1)
            )
            
            btn_layout.add_widget(submit_btn)
            btn_layout.add_widget(back_btn)
            content.add_widget(btn_layout)
            
            popup = Popup(
                title='علت فروش ناموفق',
                content=content,
                size_hint=(0.85, 0.6),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )
            popup.title_color = (1, 1, 1, 1)
            
            def on_submit(instance):
                reason = reason_spinner.text
                description = description_input.text.strip()
                
                if reason == 'سایر علل' and not description:
                    ErrorPopup.show_error('لطفاً توضیحات را وارد کنید')
                    return
                
                self.save_visit_log(
                    customer_name=customer_name,
                    visit_status='موفق',
                    sales_status='ناموفق',
                    fail_sales_reason=reason,
                    sales_description=description
                )
                popup.dismiss()
                self.show_message('موفق', f'فروش ناموفق برای "{customer_name}" ثبت شد')
                self.reset_form()
            
            def on_back(instance):
                popup.dismiss()
                self.show_sales_result_dialog(customer_name)
            
            submit_btn.bind(on_press=on_submit)
            back_btn.bind(on_press=on_back)
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش دیالوگ علت فروش ناموفق: {e}", error_details)
    
    def show_success_sales_dialog(self, customer_name):
        """دیالوگ فروش موفق با فیلدهای تعداد، مبلغ و نحوه تسویه"""
        try:
            payment_methods = ['نقد', 'چک', 'اعتباری']
            
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(12))
            with content.canvas.before:
                Color(0.15, 0.15, 0.15, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                           size=lambda i, v: setattr(content_rect, 'size', v))
            
            content.add_widget(RTLLabel(
                text=f'💰 فروش موفق برای "{customer_name}"',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(18),
                color=(1, 0.8, 0.2, 1),
                bold=True
            ))
            
            # تعداد واحد فروش
            content.add_widget(RTLLabel(
                text='تعداد واحد فروش:',
                size_hint_y=None,
                height=dp(25),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            units_input = RTLTextInput(
                text='0',
                multiline=False,
                size_hint_y=None,
                height=dp(45),
                input_filter='int',
                font_size=sp(36)
            )
            units_input.foreground_color = (1, 1, 1, 1)
            units_input.background_color = (0.2, 0.2, 0.2, 1)
            units_input.hint_text_color = (0.5, 0.5, 0.5, 1)
            content.add_widget(units_input)
            
            # مبلغ فاکتور
            content.add_widget(RTLLabel(
                text='مبلغ فاکتور (ریال):',
                size_hint_y=None,
                height=dp(25),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            amount_input = RTLTextInput(
                text='0',
                multiline=False,
                size_hint_y=None,
                height=dp(45),
                input_filter='int',
                font_size=sp(36)
            )
            amount_input.foreground_color = (1, 1, 1, 1)
            amount_input.background_color = (0.2, 0.2, 0.2, 1)
            amount_input.hint_text_color = (0.5, 0.5, 0.5, 1)
            content.add_widget(amount_input)
            
            # نحوه تسویه
            content.add_widget(RTLLabel(
                text='نحوه تسویه:',
                size_hint_y=None,
                height=dp(25),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            payment_spinner = PersianComboBox(
                text=payment_methods[0],
                values=payment_methods,
                height=dp(45)
            )
            payment_spinner.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            payment_spinner.main_btn.color = (1, 1, 1, 1)
            payment_spinner.main_btn.font_size = sp(18)
            content.add_widget(payment_spinner)
            
            btn_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(50))
            
            submit_btn = PersianButton(
                text='✅ ثبت عملیات',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1)
            )
            back_btn = PersianButton(
                text='🔙 بازگشت',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1)
            )
            
            btn_layout.add_widget(submit_btn)
            btn_layout.add_widget(back_btn)
            content.add_widget(btn_layout)
            
            popup = Popup(
                title='ثبت فروش موفق',
                content=content,
                size_hint=(0.85, 0.7),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )
            popup.title_color = (1, 1, 1, 1)
            
            def on_submit(instance):
                units = units_input.text.strip()
                amount = amount_input.text.strip()
                payment = payment_spinner.text
                
                # اعتبارسنجی
                if not units or units == '0':
                    ErrorPopup.show_error('لطفاً تعداد واحد فروش را وارد کنید')
                    return
                
                if not amount or amount == '0':
                    ErrorPopup.show_error('لطفاً مبلغ فاکتور را وارد کنید')
                    return
                
                try:
                    units_int = int(units)
                    amount_int = int(amount)
                    
                    if units_int <= 0:
                        ErrorPopup.show_error('تعداد واحد فروش باید بیشتر از صفر باشد')
                        return
                    
                    if amount_int <= 0:
                        ErrorPopup.show_error('مبلغ فاکتور باید بیشتر از صفر باشد')
                        return
                except ValueError:
                    ErrorPopup.show_error('لطفاً مقادیر عددی معتبر وارد کنید')
                    return
                
                self.save_visit_log(
                    customer_name=customer_name,
                    visit_status='موفق',
                    sales_status='موفق',
                    units_sold=units_int,
                    sales_amount=amount_int,
                    payment_method=payment
                )
                popup.dismiss()
                self.show_message('موفق', f'فروش موفق برای "{customer_name}" ثبت شد')
                self.reset_form()
            
            def on_back(instance):
                popup.dismiss()
                self.show_sales_result_dialog(customer_name)
            
            submit_btn.bind(on_press=on_submit)
            back_btn.bind(on_press=on_back)
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش دیالوگ فروش موفق: {e}", error_details)
    
    def save_visit_log(self, **kwargs):
        """ذخیره لاگ ویزیت"""
        try:
            today = get_today_jalali()
            logs = get_daily_logs()
            
            # اگر امروز در لاگ‌ها نیست، یک لیست خالی بساز
            if today not in logs:
                logs[today] = []
            
            # اگر لاگ‌های امروز لیست نیستند، تبدیل به لیست کن
            if not isinstance(logs[today], list):
                logs[today] = []
            
            log_data = {
                'date': today,
                'route': self.route_spinner.text,
                'customer': kwargs.get('customer_name'),
                'visit_status': kwargs.get('visit_status'),
                'time': get_current_time()
            }
            
            # اضافه کردن فیلدهای مختلف بر اساس وضعیت
            if kwargs.get('visit_status') == 'ناموفق':
                log_data['fail_reason'] = kwargs.get('fail_reason', '')
            elif kwargs.get('visit_status') == 'موفق':
                log_data['sales_status'] = kwargs.get('sales_status', '')
                if kwargs.get('sales_status') == 'ناموفق':
                    log_data['fail_sales_reason'] = kwargs.get('fail_sales_reason', '')
                    log_data['sales_description'] = kwargs.get('sales_description', '')
                elif kwargs.get('sales_status') == 'موفق':
                    log_data['units_sold'] = kwargs.get('units_sold', 0)
                    log_data['sales_amount'] = kwargs.get('sales_amount', 0)
                    log_data['payment_method'] = kwargs.get('payment_method', '')
            
            # اضافه کردن به لیست
            logs[today].append(log_data)
            
            # ذخیره کل لاگ‌ها
            save_daily_log(today, logs[today])
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ذخیره لاگ ویزیت: {e}", error_details)
    
    def reset_form(self):
        """بازنشانی فرم بعد از ثبت"""
        self.customer_spinner.text = ''
        self._last_customer_text = ''
        self.selected_customer = None
    
    def show_message(self, title, message):
        """نمایش پیام موفقیت"""
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
                height=dp(50),
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
        self.manager.current = 'user'
