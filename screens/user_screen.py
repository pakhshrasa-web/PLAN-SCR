# screens/user_screen.py
# ========== صفحه کاربر (ثبت ویزیت) ==========

import traceback
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

from utils.rtl_widgets import RTLTextInput, PersianComboBox, PersianButton, RTLLabel
from utils.file_manager import get_routes, get_customers, get_settings, get_daily_logs, save_daily_log
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
            self.settings = get_settings()
            self._last_route_text = ''
            self.build_ui()
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت UserScreen: {e}", error_details)
            raise
    
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def build_ui(self):
        try:
            layout = BoxLayout(orientation='vertical', padding=[dp(5), dp(5), dp(5), dp(5)])
            
            self.form_layout = GridLayout(
                cols=3,
                spacing=dp(4),
                size_hint_y=None,
                padding=dp(5)
            )
            self.form_layout.bind(minimum_height=self.form_layout.setter('height'))
            
            routes = get_routes()
            self.route_names = [r.get('name', '') for r in routes] if routes else ['']
            
            customers = get_customers()
            self.all_customer_names = [c.get('name', '') for c in customers] if customers else ['']
            
            # ========== هدرها (با رنگ روشن) ==========
            self.form_layout.add_widget(RTLLabel(
                text='آیتم',
                size_hint_y=None,
                height=dp(30),
                bold=True,
                color=(0.4, 0.7, 1, 1),
                font_size=sp(15)
            ))
            self.form_layout.add_widget(RTLLabel(
                text='مقدار',
                size_hint_y=None,
                height=dp(30),
                bold=True,
                color=(0.4, 0.7, 1, 1),
                font_size=sp(15)
            ))
            self.form_layout.add_widget(RTLLabel(
                text='هدف',
                size_hint_y=None,
                height=dp(30),
                bold=True,
                color=(0.4, 0.7, 1, 1),
                font_size=sp(15)
            ))
            
            self.inputs = {}
            
            # ========== تاریخ ویزیت ==========
            self.form_layout.add_widget(RTLLabel(
                text='تاریخ ویزیت',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            visit_date = RTLTextInput(
                text=get_today_jalali(),
                multiline=False,
                size_hint_y=None,
                height=dp(50),
                font_size=sp(36)
            )
            visit_date.foreground_color = (1, 1, 1, 1)
            visit_date.background_color = (0.2, 0.2, 0.2, 1)
            visit_date.hint_text_color = (0.5, 0.5, 0.5, 1)
            self.form_layout.add_widget(visit_date)
            self.form_layout.add_widget(RTLLabel(
                text='---',
                size_hint_y=None,
                height=dp(35),
                color=(0.5, 0.5, 0.5, 1),
                font_size=sp(14)
            ))
            self.inputs['visit_date'] = visit_date
            
            # ========== مسیر ویزیت ==========
            self.form_layout.add_widget(RTLLabel(
                text='مسیر ویزیت',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))

            self.route_spinner = PersianComboBox(
                text=self.route_names[0] if self.route_names else '',
                values=self.route_names,
                height=dp(50)
            )
            self.route_spinner.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.route_spinner.main_btn.color = (1, 1, 1, 1)
            self.route_spinner.main_btn.font_size = sp(18)
            self.form_layout.add_widget(self.route_spinner)

            # تعداد مشتریان مسیر (با رنگ طلایی)
            self.route_customers_target = Label(
                text=self.route_count,
                size_hint_y=None,
                height=dp(35),
                color=(1, 0.8, 0.2, 1),
                font_size=sp(24),
                font_name='PersianFont',
                halign='center',
                valign='middle'
            )
            self.form_layout.add_widget(self.route_customers_target)
            
            self.inputs['route_name'] = self.route_spinner
            
            self._last_route_text = self.route_spinner.text
            Clock.schedule_interval(self._check_route_change, 0.5)
            
            # ========== ساعت شروع کار ==========
            self.form_layout.add_widget(RTLLabel(
                text='ساعت شروع کار',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            clock_in = RTLTextInput(
                text=get_current_time(),
                multiline=False,
                size_hint_y=None,
                height=dp(50),
                font_size=sp(36)
            )
            clock_in.foreground_color = (1, 1, 1, 1)
            clock_in.background_color = (0.2, 0.2, 0.2, 1)
            clock_in.hint_text_color = (0.5, 0.5, 0.5, 1)
            self.form_layout.add_widget(clock_in)
            self.form_layout.add_widget(RTLLabel(
                text=self.settings.get('work_start_time', '08:00'),
                size_hint_y=None,
                height=dp(35),
                color=(1, 1, 1, 1),
                font_size=sp(14)
            ))
            self.inputs['clock_in'] = clock_in
            
            # ========== ساعت اولین ویزیت ==========
            self.form_layout.add_widget(RTLLabel(
                text='ساعت اولین ویزیت',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            first_visit_time = RTLTextInput(
                text='',
                multiline=False,
                size_hint_y=None,
                height=dp(50),
                font_size=sp(36)
            )
            first_visit_time.foreground_color = (1, 1, 1, 1)
            first_visit_time.background_color = (0.2, 0.2, 0.2, 1)
            first_visit_time.hint_text_color = (0.5, 0.5, 0.5, 1)
            self.form_layout.add_widget(first_visit_time)
            self.form_layout.add_widget(RTLLabel(
                text=self.settings.get('first_visit_time', '09:00'),
                size_hint_y=None,
                height=dp(35),
                color=(1, 1, 1, 1),
                font_size=sp(14)
            ))
            self.inputs['first_visit_time'] = first_visit_time
            
            # ========== اولین مشتری ==========
            self.form_layout.add_widget(RTLLabel(
                text='اولین مشتری',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))

            self.first_customer_spinner = PersianComboBox(
                text='',
                values=[''],
                height=dp(50)
            )
            self.first_customer_spinner.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.first_customer_spinner.main_btn.color = (1, 1, 1, 1)
            self.first_customer_spinner.main_btn.font_size = sp(18)
            self.first_customer_spinner.main_btn.halign = 'center'
            self.first_customer_spinner.main_btn.valign = 'middle'
            self.first_customer_spinner.main_btn.text_size = (None, None)
            self.form_layout.add_widget(self.first_customer_spinner)

            self.first_customer_target = RTLTextInput(
                text='',
                multiline=False,
                size_hint_y=None,
                height=dp(50),
                font_size=sp(36),
                hint_text='نام مشتری هدف'
            )
            self.first_customer_target.foreground_color = (1, 1, 1, 1)
            self.first_customer_target.background_color = (0.2, 0.2, 0.2, 1)
            self.first_customer_target.hint_text_color = (0.5, 0.5, 0.5, 1)
            self.form_layout.add_widget(self.first_customer_target)

            self.inputs['first_customer'] = self.first_customer_target
            
            # ========== تعداد مشتری ویزیت شده ==========
            self.form_layout.add_widget(RTLLabel(
                text='تعداد مشتری ویزیت شده',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            visited_count = RTLTextInput(
                text='0',
                multiline=False,
                size_hint_y=None,
                height=dp(50),
                input_filter='int',
                font_size=sp(36)
            )
            visited_count.foreground_color = (1, 1, 1, 1)
            visited_count.background_color = (0.2, 0.2, 0.2, 1)
            visited_count.hint_text_color = (0.5, 0.5, 0.5, 1)
            self.form_layout.add_widget(visited_count)
            
            self.visited_customers_target = RTLLabel(
                text='0',
                size_hint_y=None,
                height=dp(35),
                color=(1, 1, 1, 1),
                font_size=sp(14)
            )
            self.form_layout.add_widget(self.visited_customers_target)
            self.inputs['visited_customers_count'] = visited_count
            
            # ========== تعداد فاکتور موفق ==========
            self.form_layout.add_widget(RTLLabel(
                text='تعداد فاکتور موفق',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            invoices_count = RTLTextInput(
                text='0',
                multiline=False,
                size_hint_y=None,
                height=dp(50),
                input_filter='int',
                font_size=sp(36)
            )
            invoices_count.foreground_color = (1, 1, 1, 1)
            invoices_count.background_color = (0.2, 0.2, 0.2, 1)
            invoices_count.hint_text_color = (0.5, 0.5, 0.5, 1)
            self.form_layout.add_widget(invoices_count)
            self.form_layout.add_widget(RTLLabel(
                text=str(self.settings.get('target_invoice_count', '20')),
                size_hint_y=None,
                height=dp(35),
                color=(1, 1, 1, 1),
                font_size=sp(14)
            ))
            self.inputs['successful_invoices_count'] = invoices_count
            
            # ========== تعداد واحد فروش موفق ==========
            self.form_layout.add_widget(RTLLabel(
                text='تعداد واحد فروش موفق',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            units_count = RTLTextInput(
                text='0',
                multiline=False,
                size_hint_y=None,
                height=dp(50),
                input_filter='int',
                font_size=sp(36)
            )
            units_count.foreground_color = (1, 1, 1, 1)
            units_count.background_color = (0.2, 0.2, 0.2, 1)
            units_count.hint_text_color = (0.5, 0.5, 0.5, 1)
            self.form_layout.add_widget(units_count)
            self.form_layout.add_widget(RTLLabel(
                text=str(self.settings.get('target_count', '100')),
                size_hint_y=None,
                height=dp(35),
                color=(1, 1, 1, 1),
                font_size=sp(14)
            ))
            self.inputs['successful_units_count'] = units_count
            
            # ========== مبلغ فروش موفق ==========
            self.form_layout.add_widget(RTLLabel(
                text='مبلغ فروش موفق',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            sales_amount = RTLTextInput(
                text='0',
                multiline=False,
                size_hint_y=None,
                height=dp(50),
                input_filter='int',
                font_size=sp(36)
            )
            sales_amount.foreground_color = (1, 1, 1, 1)
            sales_amount.background_color = (0.2, 0.2, 0.2, 1)
            sales_amount.hint_text_color = (0.5, 0.5, 0.5, 1)
            self.form_layout.add_widget(sales_amount)
            
            target_amount = self.settings.get('target_amount', 50000000)
            try:
                target_amount = int(target_amount)
            except:
                target_amount = 0
            self.form_layout.add_widget(RTLLabel(
                text="{:,}".format(target_amount),
                size_hint_y=None,
                height=dp(35),
                color=(1, 1, 1, 1),
                font_size=sp(14)
            ))
            self.inputs['successful_sales_amount'] = sales_amount
            
            # ========== ساعت آخرین ویزیت ==========
            self.form_layout.add_widget(RTLLabel(
                text='ساعت آخرین ویزیت',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            last_visit_time = RTLTextInput(
                text='',
                multiline=False,
                size_hint_y=None,
                height=dp(50),
                font_size=sp(36)
            )
            last_visit_time.foreground_color = (1, 1, 1, 1)
            last_visit_time.background_color = (0.2, 0.2, 0.2, 1)
            last_visit_time.hint_text_color = (0.5, 0.5, 0.5, 1)
            self.form_layout.add_widget(last_visit_time)
            self.form_layout.add_widget(RTLLabel(
                text='---',
                size_hint_y=None,
                height=dp(35),
                color=(0.5, 0.5, 0.5, 1),
                font_size=sp(14)
            ))
            self.inputs['last_visit_time'] = last_visit_time
            
            # ========== ساعت پایان کار ==========
            self.form_layout.add_widget(RTLLabel(
                text='ساعت پایان کار',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            clock_out = RTLTextInput(
                text='',
                multiline=False,
                size_hint_y=None,
                height=dp(50),
                font_size=sp(36)
            )
            clock_out.foreground_color = (1, 1, 1, 1)
            clock_out.background_color = (0.2, 0.2, 0.2, 1)
            clock_out.hint_text_color = (0.5, 0.5, 0.5, 1)
            self.form_layout.add_widget(clock_out)
            self.form_layout.add_widget(RTLLabel(
                text='---',
                size_hint_y=None,
                height=dp(35),
                color=(0.5, 0.5, 0.5, 1),
                font_size=sp(14)
            ))
            self.inputs['clock_out'] = clock_out
            
            # ========== ScrollView ==========
            form_scroll = ScrollView()
            form_scroll.add_widget(self.form_layout)
            layout.add_widget(form_scroll)
            
            # ========== دکمه‌ها ==========
            btn_layout = BoxLayout(
                size_hint_y=None,
                height=dp(42),
                spacing=dp(5),
                padding=dp(5)
            )
            
            save_btn = PersianButton(
                text='💾 ذخیره',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(38),
                color=(1, 1, 1, 1)
            )
            save_btn.bind(on_press=self.save_log)
            btn_layout.add_widget(save_btn)
            
            report_btn = PersianButton(
                text='📊 گزارش',
                background_color=(0.2, 0.6, 1, 1),
                size_hint_y=None,
                height=dp(38),
                color=(1, 1, 1, 1)
            )
            report_btn.bind(on_press=self.go_to_report)
            btn_layout.add_widget(report_btn)
            
            logout_btn = PersianButton(
                text='🚪 خروج',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(38),
                color=(1, 1, 1, 1)
            )
            logout_btn.bind(on_press=self.logout)
            btn_layout.add_widget(logout_btn)
            
            layout.add_widget(btn_layout)
            self.add_widget(layout)
            
            Clock.schedule_once(lambda dt: self.update_route_info(), 0.5)
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت UI UserScreen: {e}", error_details)
            raise
    
    def _check_route_change(self, dt):
        if hasattr(self, 'route_spinner'):
            current_text = self.route_spinner.text
            if current_text != self._last_route_text:
                self._last_route_text = current_text
                self.update_route_info()
    
    def update_route_info(self):
        try:
            current_route = self.route_spinner.text
            
            if current_route and current_route not in ['', '⚠️ مسیری انتخاب نشده']:
                customers = get_customers()
                
                total_customers = 0
                filtered_customers = []
                
                for c in customers:
                    route_name = c.get('route_name', '').strip()
                    if route_name == current_route.strip():
                        total_customers += 1
                        filtered_customers.append(c.get('name', ''))
                
                self.route_count = str(total_customers)
                self.route_customers_target.text = self.route_count
                
                if filtered_customers:
                    self.first_customer_spinner.values = filtered_customers
                    self.first_customer_spinner.text = filtered_customers[0]
                else:
                    self.first_customer_spinner.values = ['⚠️ مشتری‌ای یافت نشد']
                    self.first_customer_spinner.text = '⚠️ مشتری‌ای یافت نشد'
                    
                first_customer_target = self.settings.get('first_customer_of_route', '')
                self.first_customer_target.text = first_customer_target
                
                supervision_rate = self.settings.get('supervision_rate', 0.3)
                target_visits = int(total_customers * supervision_rate)
                self.visited_customers_target.text = str(target_visits)
                
            else:
                self.route_count = '0'
                self.route_customers_target.text = '0'
                self.visited_customers_target.text = '0'
                self.first_customer_spinner.values = ['⚠️ مسیری انتخاب نشده']
                self.first_customer_spinner.text = '⚠️ مسیری انتخاب نشده'
                self.first_customer_target.text = ''
                
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در بروزرسانی اطلاعات مسیر: {e}", error_details)
    
    def save_log(self, instance):
        try:
            log_data = {}
            for key, input_field in self.inputs.items():
                log_data[key] = input_field.text
            
            if 'route_name' in self.inputs:
                log_data['route_name'] = self.inputs['route_name'].text
            if 'first_customer' in self.inputs:
                log_data['first_customer'] = self.inputs['first_customer'].text
            
            if not log_data.get('visit_date'):
                self.show_message('خطا', 'تاریخ ویزیت الزامی است')
                return
            
            for key in ['visited_customers_count', 'successful_invoices_count', 'successful_units_count', 'successful_sales_amount']:
                if key in log_data and (log_data[key] == '' or log_data[key] == '0'):
                    log_data[key] = '0'
            
            all_logs = get_daily_logs()
            
            if log_data.get('visit_date') in all_logs:
                content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
                with content.canvas.before:
                    Color(0.12, 0.12, 0.12, 1)
                    content_rect = Rectangle(pos=content.pos, size=content.size)
                    content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                               size=lambda i, v: setattr(content_rect, 'size', v))
                
                content.add_widget(RTLLabel(
                    text='ویزیتی با این تاریخ قبلاً ثبت شده است. آیا می‌خواهید جایگزین شود؟',
                    size_hint_y=None,
                    height=dp(60),
                    color=(1, 1, 1, 1)
                ))
                
                btn_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(50))
                yes_btn = PersianButton(
                    text='بله، جایگزین شود',
                    size_hint_y=None,
                    height=dp(45),
                    color=(1, 1, 1, 1),
                    background_color=(0.2, 0.7, 0.2, 1)
                )
                no_btn = PersianButton(
                    text='خیر، انصراف',
                    size_hint_y=None,
                    height=dp(45),
                    color=(1, 1, 1, 1),
                    background_color=(0.3, 0.3, 0.3, 1)
                )
                btn_layout.add_widget(yes_btn)
                btn_layout.add_widget(no_btn)
                content.add_widget(btn_layout)
                
                popup = Popup(
                    title='توجه',
                    content=content,
                    size_hint=(0.85, 0.35),
                    background_color=(0.08, 0.08, 0.08, 1)
                )
                popup.title_color = (1, 1, 1, 1)
                
                def replace(instance):
                    save_daily_log(log_data['visit_date'], log_data)
                    popup.dismiss()
                    self.show_message('موفق', 'اطلاعات ویزیت با موفقیت جایگزین شد')
                    self.clear_form()
                
                def cancel(instance):
                    popup.dismiss()
                
                yes_btn.bind(on_press=replace)
                no_btn.bind(on_press=cancel)
                popup.open()
            else:
                save_daily_log(log_data['visit_date'], log_data)
                self.show_message('موفق', 'اطلاعات ویزیت با موفقیت ذخیره شد')
                self.clear_form()
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ذخیره ویزیت: {e}", error_details)
    
    def clear_form(self):
        for key in ['first_visit_time', 'last_visit_time', 'clock_out']:
            if key in self.inputs:
                self.inputs[key].text = ''
        
        for key in ['visited_customers_count', 'successful_invoices_count', 'successful_units_count', 'successful_sales_amount']:
            if key in self.inputs:
                self.inputs[key].text = '0'
    
    def go_to_report(self, instance):
        self.manager.current = 'report'
    
    def logout(self, instance):
        self.manager.current = 'login'
    
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