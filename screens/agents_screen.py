# screens/agents_screen.py
# ========== صفحه ثبت ویزیت بازاریابان با لیست مشتریان ==========

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

from utils.rtl_widgets import RTLTextInput, PersianComboBox, PersianButton, RTLLabel, PersianPopup
from utils.file_manager import get_routes, get_customers, get_settings, save_daily_log, get_daily_logs, add_customer
from utils.jalali_date import get_today_jalali, get_current_time
from error_handler import ErrorPopup


class AgentsScreen(Screen):
    def __init__(self, **kwargs):
        try:
            super().__init__(**kwargs)
            with self.canvas.before:
                Color(0.08, 0.08, 0.08, 1)
                self.bg_rect = Rectangle(pos=self.pos, size=self.size)
                self.bind(pos=self._update_bg, size=self._update_bg)
            
            Window.softinput_mode = 'resize'
            self.focusable_fields = []
            
            self.amount_words_label = None
            self._last_reason_text = ''
            self._last_route_text = ''
            self.locked_route = None
            self.route_confirmed = False
            self.session_new_customers = []
            
            # ✅ تعریف customers_list_container قبل از build_ui
            self.customers_list_container = GridLayout(
                cols=1,
                spacing=dp(6),
                size_hint_y=None,
                padding=dp(5)
            )
            self.customers_list_container.height = dp(50)  # ارتفاع اولیه
            
            self.settings = get_settings()
            self.selected_customer = None
            self.selected_route = None
            
            self.build_ui()
            
            Window.bind(on_keyboard=self._on_keyboard)
            Clock.schedule_once(self._check_today_visits, 0.5)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت AgentsScreen: {e}", error_details)
            raise

    def number_to_persian_words(self, number):
        try:
            if number == 0:
                return "صفر ریال"
            
            ones = ['', 'یک', 'دو', 'سه', 'چهار', 'پنج', 'شش', 'هفت', 'هشت', 'نه']
            tens = ['', 'ده', 'بیست', 'سی', 'چهل', 'پنجاه', 'شصت', 'هفتاد', 'هشتاد', 'نود']
            hundreds = ['', 'یکصد', 'دویست', 'سیصد', 'چهارصد', 'پانصد', 'ششصد', 'هفتصد', 'هشتصد', 'نهصد']
            groups = ['', 'هزار', 'میلیون', 'میلیارد']
            
            def convert_three_digits(num):
                if num == 0:
                    return ''
                h = num // 100
                t = (num % 100) // 10
                o = num % 10
                result = []
                if h > 0:
                    result.append(hundreds[h])
                if t == 1:
                    if o == 0:
                        result.append('ده')
                    elif o == 1:
                        result.append('یازده')
                    elif o == 2:
                        result.append('دوازده')
                    elif o == 3:
                        result.append('سیزده')
                    elif o == 4:
                        result.append('چهارده')
                    elif o == 5:
                        result.append('پانزده')
                    elif o == 6:
                        result.append('شانزده')
                    elif o == 7:
                        result.append('هفده')
                    elif o == 8:
                        result.append('هجده')
                    elif o == 9:
                        result.append('نوزده')
                else:
                    if t > 0:
                        result.append(tens[t])
                    if o > 0:
                        result.append(ones[o])
                return ' و '.join(result)
            
            num_str = str(number)
            group_list = []
            for i in range(len(num_str), 0, -3):
                start = max(0, i - 3)
                group = int(num_str[start:i])
                group_list.insert(0, group)
            
            result_parts = []
            for i, group in enumerate(group_list):
                if group == 0:
                    continue
                group_words = convert_three_digits(group)
                if group_words:
                    group_name = groups[len(group_list) - 1 - i]
                    if group_name:
                        result_parts.append(f"{group_words} {group_name}")
                    else:
                        result_parts.append(group_words)
            
            return " و ".join(result_parts) + " ریال"
        except Exception as e:
            print(f"خطا در تبدیل عدد به حروف: {e}")
            return f"{number:,} ریال"
    
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
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
            print(f"خطا در اسکرول به فیلد: {e}")
    
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
    
    def _check_today_visits(self, dt):
        try:
            today = get_today_jalali()
            logs = get_daily_logs()
            
            if today in logs and logs[today] and len(logs[today]) > 0:
                if hasattr(self, 'route_spinner'):
                    last_visit = logs[today][-1]
                    locked_route = last_visit.get('route', '')
                    
                    if locked_route:
                        self.locked_route = locked_route
                        self.route_spinner.text = locked_route
                        self.route_spinner.main_btn.disabled = True
                        self.route_spinner.main_btn.background_color = (0.15, 0.15, 0.15, 1)
                        self.route_spinner.main_btn.color = (0.6, 0.6, 0.6, 1)
                        self.route_confirmed = True
                        Clock.schedule_once(lambda dt: self.update_customers_list(), 0.3)
                
                self.show_message('اطلاع', 'برای امروز ویزیت ثبت شده و مسیر قفل است.')
        except Exception as e:
            print(f"خطا در بررسی ویزیت‌های امروز: {e}")
    
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
                padding=dp(15),
                spacing=dp(8),
                size_hint_y=None
            )
            content.bind(minimum_height=content.setter('height'))
            
            # ========== عنوان ==========
            content.add_widget(RTLLabel(
                text='ثبت ویزیت بازاریابان',
                font_size=sp(22),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                bold=True
            ))
            content.add_widget(Label(size_hint_y=None, height=dp(5)))
            
            # ========== تاریخ ==========
            content.add_widget(RTLLabel(
                text='تاریخ:',
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
            
            # ========== ساعت ==========
            content.add_widget(RTLLabel(
                text='ساعت:',
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
            
            # ========== مسیر ==========
            content.add_widget(RTLLabel(
                text='انتخاب مسیر:',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(16),
                color=(0.4, 0.7, 1, 1),
                bold=True
            ))
            
            routes = get_routes()
            route_names = [r.get('name', '') for r in routes] if routes else ['']
            
            self.route_spinner = PersianComboBox(
                text='',
                values=route_names,
                height=dp(70)
            )
            self.route_spinner.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.route_spinner.main_btn.color = (1, 1, 1, 1)
            self.route_spinner.main_btn.font_size = sp(18)
            
            today = get_today_jalali()
            logs = get_daily_logs()
            if self.locked_route and today in logs and logs[today] and len(logs[today]) > 0:
                if self.locked_route in route_names:
                    self.route_spinner.text = self.locked_route
                    self.route_spinner.main_btn.disabled = True
                    self.route_spinner.main_btn.background_color = (0.15, 0.15, 0.15, 1)
                    self.route_spinner.main_btn.color = (0.6, 0.6, 0.6, 1)
                    self.route_confirmed = True
            
            self._last_route_text = self.route_spinner.text
            # ✅ اضافه کردن تایمر برای بررسی تغییر مسیر
            Clock.schedule_interval(self._check_route_change_with_confirm, 0.3)
            content.add_widget(self.route_spinner)
            content.add_widget(Label(size_hint_y=None, height=dp(5)))
            
            # ========== دکمه افزودن مشتری ==========
            add_customer_btn = PersianButton(
                text='افزودن مشتری جدید',
                background_color=(0.2, 0.6, 0.2, 1),
                size_hint_y=None,
                height=dp(40),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            add_customer_btn.bind(on_press=self.show_add_customer_dialog)
            content.add_widget(add_customer_btn)
            
            # ========== دکمه انتخاب مشتری (جایگزین لیست قبلی) ==========
            select_customer_btn = PersianButton(
                text='انتخاب مشتری',
                background_color=(0.2, 0.5, 0.9, 1),
                size_hint_y=None,
                height=dp(55),
                color=(1, 1, 1, 1),
                font_size=sp(20),
                bold=True
            )
            select_customer_btn.bind(on_press=self.show_customer_selection_dialog)
            content.add_widget(select_customer_btn)
            
            # ========== نمایش مشتری انتخاب شده ==========
            self.selected_customer_label = RTLLabel(
                text='مشتری انتخاب شده: هیچ',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(18),
                color=(0.5, 0.5, 0.5, 1),
                bold=True
            )
            content.add_widget(self.selected_customer_label)
            
            # ========== دکمه بازگشت ==========
            back_btn = PersianButton(
                text='بازگشت',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            back_btn.bind(on_press=self.go_back)
            content.add_widget(back_btn)
            
            scroll.add_widget(content)
            main_layout.add_widget(scroll)
            self.add_widget(main_layout)
            
   
            Clock.schedule_interval(self.update_time, 60)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت UI AgentsScreen: {e}", error_details)
            raise
    
    
    def _check_route_change_with_confirm(self, dt):
        if hasattr(self, 'route_spinner') and not self.route_spinner.main_btn.disabled:
            current_text = self.route_spinner.text
            if current_text != self._last_route_text and current_text and current_text != '':
                self._last_route_text = current_text
                self.show_route_confirm_dialog(current_text)
    
    def update_time(self, dt):
        self.time_label.text = get_current_time()
    
    def update_customers_list(self):
        """به‌روزرسانی لیست مشتریان"""
        try:
            # ✅ اگر کانتینر والد ندارد، کاری نکن
            if not hasattr(self, 'customers_list_container') or not self.customers_list_container.parent:
                print("⚠️ customers_list_container والد ندارد، لیست به‌روز نمی‌شود")
                return
            
            # ✅ پاک کردن لیست قبلی
            self.customers_list_container.clear_widgets()
            
            selected_route = self.route_spinner.text
            
            # ✅ اگر مسیری انتخاب نشده
            if not selected_route:
                self.customers_list_container.add_widget(RTLLabel(
                    text='لطفاً ابتدا یک مسیر انتخاب کنید',
                    size_hint_y=None,
                    height=dp(40),
                    font_size=sp(16),
                    color=(0.5, 0.5, 0.5, 1)
                ))
                self.customers_list_container.height = dp(40)
                if hasattr(self.customers_list_container, 'parent') and self.customers_list_container.parent:
                    self.customers_list_container.parent.update_from_scroll()
                return
            
            # ✅ دریافت مشتریان
            all_customers = get_customers()
            search_text = self.search_input.text.strip()
            
            # ✅ فیلتر مشتریان
            filtered = []
            for c in all_customers:
                route_name = c.get('route_name', '').strip()
                customer_name = c.get('name', '')
                if route_name == selected_route.strip():
                    if search_text:
                        if search_text in customer_name:
                            filtered.append(customer_name)
                    else:
                        filtered.append(customer_name)
            
            # ✅ اگر مشتری‌ای وجود نداشت
            if not filtered:
                self.customers_list_container.add_widget(RTLLabel(
                    text='هیچ مشتری‌ای در این مسیر یافت نشد',
                    size_hint_y=None,
                    height=dp(40),
                    font_size=sp(16),
                    color=(0.5, 0.5, 0.5, 1)
                ))
                self.customers_list_container.height = dp(40)
                if hasattr(self.customers_list_container, 'parent') and self.customers_list_container.parent:
                    self.customers_list_container.parent.update_from_scroll()
                return
            
            # ✅ ایجاد دکمه‌های مشتریان
            for customer_name in filtered:
                customer_box = BoxLayout(
                    size_hint_y=None,
                    height=dp(50),
                    spacing=dp(5),
                    padding=[dp(8), dp(4), dp(8), dp(4)]
                )
                
                with customer_box.canvas.before:
                    Color(0.15, 0.15, 0.2, 1)
                    rect = Rectangle(pos=customer_box.pos, size=customer_box.size)
                    customer_box.bind(
                        pos=lambda i, v: setattr(rect, 'pos', v),
                        size=lambda i, v: setattr(rect, 'size', v)
                    )
                
                customer_label = RTLLabel(
                    text=customer_name,
                    size_hint_x=0.7,
                    size_hint_y=None,
                    height=dp(45),
                    font_size=sp(18),
                    color=(1, 1, 1, 1),
                    halign='right'
                )
                customer_box.add_widget(customer_label)
                
                visit_btn = PersianButton(
                    text='ویزیت',
                    size_hint_x=0.3,
                    size_hint_y=None,
                    height=dp(40),
                    background_color=(0.2, 0.6, 0.8, 1),
                    color=(1, 1, 1, 1),
                    font_size=sp(15)
                )
                visit_btn.bind(on_press=lambda x, name=customer_name: self.on_customer_selected(name))
                customer_box.add_widget(visit_btn)
                
                self.customers_list_container.add_widget(customer_box)
            
            # ✅ تنظیم ارتفاع کل کانتینر
            total_height = len(filtered) * dp(55) + dp(10)
            self.customers_list_container.height = total_height
            
            # ✅ به‌روزرسانی اسکرول فقط اگر والد وجود داشته باشه
            if hasattr(self.customers_list_container, 'parent') and self.customers_list_container.parent:
                self.customers_list_container.parent.update_from_scroll()
            
            # ✅ دیباگ
            print(f"✅ ارتفاع کانتینر تنظیم شد: {self.customers_list_container.height}")
            print(f"✅ تعداد مشتریان نمایش داده شده: {len(filtered)}")
            
        except Exception as e:
            error_details = traceback.format_exc()
            # ✅ فقط لاگ کن، خطا نشون نده چون دیگه از این قابلیت استفاده نمیشه
            print(f"⚠️ خطا در بروزرسانی لیست مشتریان (نادیده گرفته شد): {e}")
    
    # ============================================================
    # دیالوگ انتخاب مشتری (جدید)
    # ============================================================
    
    def show_customer_selection_dialog(self, instance):
        """نمایش دیالوگ انتخاب مشتری"""
        try:
            selected_route = self.route_spinner.text
            
            # ✅ اگر مسیری انتخاب نشده
            if not selected_route:
                self.show_message('خطا', 'لطفاً ابتدا یک مسیر انتخاب کنید')
                return
            
            # ✅ دریافت مشتریان مسیر
            all_customers = get_customers()
            filtered_customers = []
            for c in all_customers:
                if c.get('route_name', '').strip() == selected_route.strip():
                    filtered_customers.append(c.get('name', ''))
            
            if not filtered_customers:
                self.show_message('توجه', 'هیچ مشتری‌ای در این مسیر یافت نشد')
                return
            
            # ✅ دریافت لیست مشتریان ویزیت شده امروز
            today = get_today_jalali()
            logs = get_daily_logs()
            visited_today = []
            if today in logs and isinstance(logs[today], list):
                for log in logs[today]:
                    if isinstance(log, dict):
                        visited_today.append(log.get('customer', ''))
            
            # ✅ ساخت محتوای دیالوگ
            content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
            with content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                            size=lambda i, v: setattr(content_rect, 'size', v))
            
            # ✅ عنوان با توضیح هایلایت
            title_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(60))
            
            title_layout.add_widget(RTLLabel(
                text=f'انتخاب مشتری - {selected_route}',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(18),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))
            
            title_layout.add_widget(RTLLabel(
                text=' مشتریان آبی رنگ امروز ویزیت شده‌اند',
                size_hint_y=None,
                height=dp(25),
                font_size=sp(15),
                color=(0.6, 0.6, 0.6, 1)
            ))
            
            content.add_widget(title_layout)
            
            # ✅ جستجو
            search_input = RTLTextInput(
                hint_text='جستجوی مشتری...',
                multiline=False,
                size_hint_y=None,
                height=dp(55),
                font_size=sp(24)
            )
            search_input.bg_color = (0.15, 0.15, 0.15, 1)
            search_input.border_color = (0.3, 0.3, 0.3, 1)
            search_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            search_input._hidden_input.foreground_color = (1, 1, 1, 1)
            content.add_widget(search_input)
            
            # ✅ لیست مشتریان
            customers_scroll = ScrollView(
                do_scroll_x=False,
                do_scroll_y=True,
                size_hint_y=0.65,
                scroll_type=['bars', 'content'],
                bar_width=dp(6)
            )
            
            customers_grid = GridLayout(
                cols=1,
                spacing=dp(4),
                size_hint_y=None,
                padding=dp(5)
            )
            customers_grid.bind(minimum_height=customers_grid.setter('height'))
            
            # ✅ تابع فیلتر کردن
            def filter_customers(text):
                customers_grid.clear_widgets()
                search_text = text.strip()
                
                for customer in filtered_customers:
                    if search_text and search_text not in customer:
                        continue
                    
                    # ✅ تشخیص ویزیت شده امروز
                    is_visited = customer in visited_today
                    
                    customer_btn = PersianButton(
                        text=customer,
                        size_hint_y=None,
                        height=dp(45),
                        background_color=(0.2, 0.6, 1, 1) if is_visited else (0.2, 0.2, 0.2, 1),
                        color=(1, 1, 1, 1),
                        font_size=sp(18)
                    )
                    customer_btn.bind(
                        on_press=lambda x, name=customer: self._handle_customer_selection(name, content)
                    )
                    customers_grid.add_widget(customer_btn)
                
                customers_grid.height = len(customers_grid.children) * dp(50) + dp(10)
            
            # ✅ اصلاح: استفاده از _hidden_input.text برای bind
            search_input._hidden_input.bind(text=lambda i, v: filter_customers(v))
            filter_customers('')
            
            customers_scroll.add_widget(customers_grid)
            content.add_widget(customers_scroll)
            
            # ✅ دکمه بستن
            close_btn = PersianButton(
                text='بستن',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            content.add_widget(close_btn)
            
            popup = PersianPopup(
                title='انتخاب مشتری',
                content=content,
                size_hint=(0.9, 0.75),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=True
            )
            
            # ✅ ذخیره popup برای دسترسی بعدی
            self.customer_selection_popup = popup
            
            close_btn.bind(on_press=popup.dismiss)
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش دیالوگ انتخاب مشتری: {e}", error_details)
    
    def _handle_customer_selection(self, customer_name, dialog_content):
        """مدیریت انتخاب مشتری از دیالوگ"""
        try:
            today = get_today_jalali()
            logs = get_daily_logs()
            
            # ✅ بررسی اینکه مشتری امروز ویزیت شده؟
            is_visited_today = False
            if today in logs and isinstance(logs[today], list):
                for log in logs[today]:
                    if isinstance(log, dict) and log.get('customer') == customer_name:
                        is_visited_today = True
                        break
            
            # ✅ اگر ویزیت شده، سوال بپرس
            if is_visited_today:
                content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
                with content.canvas.before:
                    Color(0.15, 0.15, 0.15, 1)
                    content_rect = Rectangle(pos=content.pos, size=content.size)
                    content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                                size=lambda i, v: setattr(content_rect, 'size', v))
                
                content.add_widget(RTLLabel(
                    text=f'مشتری "{customer_name}" امروز ویزیت شده است.از تغییر وضعیت مطمئن هستید؟',
                    size_hint_y=None,
                    height=dp(60),
                    font_size=sp(18),
                    color=(1, 1, 1, 1)
                ))
                
                btn_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(50))
                
                yes_btn = PersianButton(
                    text='بله',
                    background_color=(0.2, 0.7, 0.2, 1),
                    size_hint_y=None,
                    height=dp(45),
                    color=(1, 1, 1, 1),
                    font_size=sp(16)
                )
                no_btn = PersianButton(
                    text='خیر',
                    background_color=(0.8, 0.2, 0.2, 1),
                    size_hint_y=None,
                    height=dp(45),
                    color=(1, 1, 1, 1),
                    font_size=sp(16)
                )
                
                btn_layout.add_widget(yes_btn)
                btn_layout.add_widget(no_btn)
                content.add_widget(btn_layout)
                
                confirm_popup = PersianPopup(
                    title='تأیید تغییر',
                    content=content,
                    size_hint=(0.85, 0.4),
                    background_color=(0.08, 0.08, 0.08, 1),
                    auto_dismiss=False
                )
                
                def on_yes(instance):
                    confirm_popup.dismiss()
                    # ✅ بستن popup انتخاب مشتری
                    if hasattr(self, 'customer_selection_popup'):
                        self.customer_selection_popup.dismiss()
                    self.selected_customer = customer_name
                    self.selected_customer_label.text = f'مشتری انتخاب شده: {customer_name}'
                    self.selected_customer_label.color = (0.2, 0.8, 0.4, 1)
                    self.show_confirm_dialog(customer_name)
                
                def on_no(instance):
                    confirm_popup.dismiss()
                
                yes_btn.bind(on_press=on_yes)
                no_btn.bind(on_press=on_no)
                confirm_popup.open()
                
            else:
                # ✅ ویزیت نشده، مستقیم برو به دیالوگ تأیید
                # ✅ بستن popup انتخاب مشتری
                if hasattr(self, 'customer_selection_popup'):
                    self.customer_selection_popup.dismiss()
                self.selected_customer = customer_name
                self.selected_customer_label.text = f'مشتری انتخاب شده: {customer_name}'
                self.selected_customer_label.color = (0.2, 0.8, 0.4, 1)
                self.show_confirm_dialog(customer_name)
                
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در انتخاب مشتری: {e}", error_details)
    
    def on_customer_selected(self, customer_name):
        if customer_name and customer_name not in ['', 'مشتری‌ای یافت نشد', 'هیچ مشتری‌ای در این مسیر یافت نشد']:
            self.selected_customer = customer_name
            self.selected_customer_label.text = f'مشتری انتخاب شده: {customer_name}'
            self.selected_customer_label.color = (0.2, 0.8, 0.4, 1)
            self.show_confirm_dialog(customer_name)
    
    # ============================================================
    # ادامه دیالوگ‌ها (همانند کد قبلی)
    # ============================================================
    
    def show_add_customer_dialog(self, instance):
        try:
            from utils.file_manager import get_routes, get_customers, add_customer
            from utils.jalali_date import get_today_jalali

            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
            with content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                           size=lambda i, v: setattr(content_rect, 'size', v))

            content.add_widget(RTLLabel(
                text='افزودن مشتری جدید',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(18),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))

            content.add_widget(RTLLabel(
                text='انتخاب مسیر:',
                size_hint_y=None,
                height=dp(25),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))

            routes = get_routes()
            if routes:
                route_names = [r.get('name', '') for r in routes]
            else:
                route_names = ['ابتدا مسیر ایجاد کنید']

            default_route = self.route_spinner.text if self.route_spinner.text else route_names[0]

            customer_route_spinner = PersianComboBox(
                text=default_route if default_route in route_names else route_names[0],
                values=route_names,
                height=dp(55)
            )
            customer_route_spinner.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            customer_route_spinner.main_btn.color = (1, 1, 1, 1)
            customer_route_spinner.main_btn.font_size = sp(16)
            content.add_widget(customer_route_spinner)

            content.add_widget(RTLLabel(
                text='نام مشتری (الزامی):',
                size_hint_y=None,
                height=dp(25),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            customer_name_input = RTLTextInput(
                hint_text='نام مشتری را وارد کنید',
                multiline=False,
                size_hint_y=None,
                height=dp(55),
                font_size=sp(24)
            )
            customer_name_input.bg_color = (0.15, 0.15, 0.15, 1)
            customer_name_input.border_color = (0.3, 0.3, 0.3, 1)
            customer_name_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            customer_name_input._hidden_input.foreground_color = (1, 1, 1, 1)
            content.add_widget(customer_name_input)

            content.add_widget(RTLLabel(
                text='نام فروشگاه:',
                size_hint_y=None,
                height=dp(25),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            customer_store_input = RTLTextInput(
                hint_text='نام فروشگاه را وارد کنید (اختیاری)',
                multiline=False,
                size_hint_y=None,
                height=dp(55),
                font_size=sp(24)
            )
            customer_store_input.bg_color = (0.15, 0.15, 0.15, 1)
            customer_store_input.border_color = (0.3, 0.3, 0.3, 1)
            customer_store_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            customer_store_input._hidden_input.foreground_color = (1, 1, 1, 1)
            content.add_widget(customer_store_input)

            content.add_widget(RTLLabel(
                text='موبایل (الزامی):',
                size_hint_y=None,
                height=dp(25),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            customer_mobile_input = RTLTextInput(
                hint_text='شماره موبایل را وارد کنید (11 رقم)',
                multiline=False,
                size_hint_y=None,
                height=dp(55),
                font_size=sp(24)
            )
            customer_mobile_input.bg_color = (0.15, 0.15, 0.15, 1)
            customer_mobile_input.border_color = (0.3, 0.3, 0.3, 1)
            customer_mobile_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            customer_mobile_input._hidden_input.foreground_color = (1, 1, 1, 1)
            customer_mobile_input._hidden_input.input_filter = 'int'
            content.add_widget(customer_mobile_input)

            content.add_widget(RTLLabel(
                text='آدرس:',
                size_hint_y=None,
                height=dp(25),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            customer_address_input = RTLTextInput(
                hint_text='آدرس را وارد کنید (اختیاری)',
                multiline=False,
                size_hint_y=None,
                height=dp(55),
                font_size=sp(24)
            )
            customer_address_input.bg_color = (0.15, 0.15, 0.15, 1)
            customer_address_input.border_color = (0.3, 0.3, 0.3, 1)
            customer_address_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            customer_address_input._hidden_input.foreground_color = (1, 1, 1, 1)
            content.add_widget(customer_address_input)

            btn_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(45))

            submit_btn = PersianButton(
                text='افزودن مشتری',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(40),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            cancel_btn = PersianButton(
                text='انصراف',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(40),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )

            btn_layout.add_widget(submit_btn)
            btn_layout.add_widget(cancel_btn)
            content.add_widget(btn_layout)

            popup = PersianPopup(
                title='افزودن مشتری',
                content=content,
                size_hint=(0.9, 0.75),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )

            def do_add_customer(instance):
                try:
                    route_name = customer_route_spinner.text
                    if route_name == 'ابتدا مسیر ایجاد کنید':
                        self.show_message('خطا', 'لطفاً ابتدا یک مسیر ایجاد کنید')
                        return

                    name = customer_name_input.text.strip()
                    if not name:
                        self.show_message('خطا', 'نام مشتری الزامی است')
                        customer_name_input._hidden_input.focus = True
                        return

                    mobile = customer_mobile_input.text.strip()
                    if not mobile:
                        self.show_message('خطا', 'شماره موبایل الزامی است')
                        customer_mobile_input._hidden_input.focus = True
                        return

                    mobile_clean = mobile.replace(' ', '').replace('-', '').replace('_', '')
                    if not mobile_clean.isdigit():
                        self.show_message('خطا', 'شماره موبایل باید فقط شامل عدد باشد')
                        customer_mobile_input._hidden_input.focus = True
                        return
                    
                    if len(mobile_clean) != 11:
                        self.show_message('خطا', 'شماره موبایل باید ۱۱ رقم باشد')
                        customer_mobile_input._hidden_input.focus = True
                        return
                    
                    if not mobile_clean.startswith('09'):
                        self.show_message('خطا', 'شماره موبایل باید با 09 شروع شود')
                        customer_mobile_input._hidden_input.focus = True
                        return

                    all_customers = get_customers()
                    for c in all_customers:
                        if c.get('name', '').strip() == name:
                            self.show_message('خطا', f'مشتری با نام "{name}" قبلاً ثبت شده است')
                            customer_name_input._hidden_input.focus = True
                            return
                        
                        existing_mobile = c.get('mobile', '').strip()
                        if existing_mobile and existing_mobile == mobile_clean:
                            self.show_message('خطا', f'شماره موبایل "{mobile_clean}" قبلاً برای مشتری "{c.get("name")}" ثبت شده است')
                            customer_mobile_input._hidden_input.focus = True
                            return

                    customer = {
                        'name': name,
                        'store_name': customer_store_input.text.strip(),
                        'route_name': route_name,
                        'mobile': mobile_clean,
                        'address': customer_address_input.text.strip()
                    }
                    
                    add_customer(customer)
                    self.session_new_customers.append(name)
                    popup.dismiss()
                    
                    self.update_customers_list()
                    self.show_message('موفق', f'مشتری "{name}" با موفقیت اضافه شد')
                    
                    if route_name == self.route_spinner.text:
                        self.update_customers_list()
                    
                except Exception as e:
                    error_details = traceback.format_exc()
                    ErrorPopup.show_error(f"خطا در افزودن مشتری: {e}", error_details)

            def cancel_add(instance):
                popup.dismiss()

            submit_btn.bind(on_press=do_add_customer)
            cancel_btn.bind(on_press=cancel_add)
            popup.open()

        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش دیالوگ افزودن مشتری: {e}", error_details)

    def show_route_confirm_dialog(self, route_name):
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            with content.canvas.before:
                Color(0.15, 0.15, 0.15, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                        size=lambda i, v: setattr(content_rect, 'size', v))
            
            content.add_widget(RTLLabel(
                text=f'آیا قصد ویزیت مسیر "{route_name}" را دارید؟',
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
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            no_btn = PersianButton(
                text='خیر',
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
                title='تأیید مسیر',
                content=content,
                size_hint=(0.85, 0.35),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )
            
            def on_yes(instance):
                popup.dismiss()
                self.locked_route = route_name
                self.route_confirmed = True
                self.route_spinner.main_btn.disabled = True
                self.route_spinner.main_btn.background_color = (0.15, 0.15, 0.15, 1)
                self.route_spinner.main_btn.color = (0.6, 0.6, 0.6, 1)
                self.update_customers_list()
                self.show_message('موفق', f'مسیر "{route_name}" با موفقیت انتخاب و قفل شد.')
            
            def on_no(instance):
                popup.dismiss()
                self.route_spinner.text = ''
                self._last_route_text = ''
                self.route_confirmed = False
                self.update_customers_list()
            
            yes_btn.bind(on_press=on_yes)
            no_btn.bind(on_press=on_no)
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش دیالوگ تأیید مسیر: {e}", error_details)

    def show_confirm_dialog(self, customer_name):
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
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            no_btn = PersianButton(
                text='خیر',
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
                title='تأیید ویزیت',
                content=content,
                size_hint=(0.85, 0.35),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )
            
            def on_yes(instance):
                popup.dismiss()
                self.show_visit_result_dialog(customer_name)
            
            def on_no(instance):
                popup.dismiss()
                self.selected_customer = None
            
            yes_btn.bind(on_press=on_yes)
            no_btn.bind(on_press=on_no)
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش دیالوگ تأیید: {e}", error_details)

    def show_visit_result_dialog(self, customer_name):
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
                text='ویزیت موفق',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            fail_btn = PersianButton(
                text='ویزیت ناموفق',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            
            btn_layout.add_widget(success_btn)
            btn_layout.add_widget(fail_btn)
            content.add_widget(btn_layout)
            
            back_btn = PersianButton(
                text='بازگشت',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(40),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            content.add_widget(back_btn)
            
            popup = PersianPopup(
                title='نتیجه ویزیت',
                content=content,
                size_hint=(0.85, 0.5),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )
            
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
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            with content.canvas.before:
                Color(0.15, 0.15, 0.15, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                           size=lambda i, v: setattr(content_rect, 'size', v))
            
            content.add_widget(RTLLabel(
                text='علت ویزیت ناموفق را وارد کنید:',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))
            
            reason_input = RTLTextInput(
                hint_text='متن علت...',
                size_hint_y=None,
                height=dp(100),
                font_size=sp(32)
            )
            reason_input.bg_color = (0.15, 0.15, 0.15, 1)
            reason_input.border_color = (0.3, 0.3, 0.3, 1)
            reason_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            reason_input._hidden_input.foreground_color = (1, 1, 1, 1)
            reason_input._hidden_input.bind(focus=self._on_field_focus)
            self.focusable_fields.append(reason_input._hidden_input)
            content.add_widget(reason_input)
            
            btn_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(50))
            
            submit_btn = PersianButton(
                text='ثبت عملیات',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            back_btn = PersianButton(
                text='بازگشت',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            
            btn_layout.add_widget(submit_btn)
            btn_layout.add_widget(back_btn)
            content.add_widget(btn_layout)
            
            popup = PersianPopup(
                title='علت ویزیت ناموفق',
                content=content,
                size_hint=(0.85, 0.5),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )
            
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
                text='فروش موفق',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            fail_btn = PersianButton(
                text='فروش ناموفق',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            
            btn_layout.add_widget(success_btn)
            btn_layout.add_widget(fail_btn)
            content.add_widget(btn_layout)
            
            back_btn = PersianButton(
                text='بازگشت',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(40),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            content.add_widget(back_btn)
            
            popup = PersianPopup(
                title='نتیجه فروش',
                content=content,
                size_hint=(0.85, 0.45),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )
            
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
                height=dp(65)
            )
            reason_spinner.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            reason_spinner.main_btn.color = (1, 1, 1, 1)
            reason_spinner.main_btn.font_size = sp(18)
            content.add_widget(reason_spinner)
            
            description_input = RTLTextInput(
                hint_text='توضیحات (در صورت انتخاب سایر علل)',
                multiline=False,
                size_hint_y=None,
                height=dp(75),
                font_size=sp(32)
            )
            description_input.bg_color = (0.15, 0.15, 0.15, 1)
            description_input.border_color = (0.3, 0.3, 0.3, 1)
            description_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            description_input._hidden_input.foreground_color = (1, 1, 1, 1)
            description_input._hidden_input.bind(focus=self._on_field_focus)
            self.focusable_fields.append(description_input._hidden_input)
            description_input._hidden_input.disabled = True
            content.add_widget(description_input)
            
            self._last_reason_text = reason_spinner.text
            
            def check_reason_change(dt):
                if hasattr(self, '_last_reason_text'):
                    current = reason_spinner.text
                    if current != self._last_reason_text:
                        self._last_reason_text = current
                        description_input._hidden_input.disabled = (current != 'سایر علل')
                        if description_input._hidden_input.disabled:
                            description_input.text = ''
            
            Clock.schedule_interval(check_reason_change, 0.3)
            
            btn_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(50))
            
            submit_btn = PersianButton(
                text='ثبت عملیات',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            back_btn = PersianButton(
                text='بازگشت',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            
            btn_layout.add_widget(submit_btn)
            btn_layout.add_widget(back_btn)
            content.add_widget(btn_layout)
            
            popup = PersianPopup(
                title='علت فروش ناموفق',
                content=content,
                size_hint=(0.85, 0.6),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )
            
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

    def _update_amount_label(self, instance, value):
        try:
            if not self.amount_words_label:
                return
                
            amount = value.strip()
            if not amount or amount == '0':
                self.amount_words_label.set_text('صفر ریال')
                return
            
            number = int(amount)
            words = self.number_to_persian_words(number)
            self.amount_words_label.set_text(words)
        except ValueError:
            if self.amount_words_label:
                self.amount_words_label.set_text('مبلغ نامعتبر')
        except Exception as e:
            print(f"خطا در تبدیل عدد به حروف: {e}")
            if self.amount_words_label:
                self.amount_words_label.set_text('خطا در تبدیل')

    def show_success_sales_dialog(self, customer_name):
        try:
            payment_methods = ['نقد', 'چک', 'اعتباری']
            
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(12))
            with content.canvas.before:
                Color(0.15, 0.15, 0.15, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                        size=lambda i, v: setattr(content_rect, 'size', v))
            
            content.add_widget(RTLLabel(
                text=f'فروش موفق برای "{customer_name}"',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(18),
                color=(1, 0.8, 0.2, 1),
                bold=True
            ))
            
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
                height=dp(70),
                input_filter='int',
                font_size=sp(22)
            )
            units_input.bg_color = (0.15, 0.15, 0.15, 1)
            units_input.border_color = (0.3, 0.3, 0.3, 1)
            units_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            units_input._hidden_input.foreground_color = (1, 1, 1, 1)
            units_input._hidden_input.bind(focus=self._on_field_focus)
            self.focusable_fields.append(units_input._hidden_input)
            content.add_widget(units_input)
            
            content.add_widget(RTLLabel(
                text='مبلغ فاکتور (ریال):',
                size_hint_y=None,
                height=dp(25),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))

            self.amount_input = RTLTextInput(
                text='0',
                multiline=False,
                size_hint_y=None,
                height=dp(70),
                input_filter='int',
                font_size=sp(22)
            )
            self.amount_input.bg_color = (0.15, 0.15, 0.15, 1)
            self.amount_input.border_color = (0.3, 0.3, 0.3, 1)
            self.amount_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.amount_input._hidden_input.foreground_color = (1, 1, 1, 1)
            self.amount_input._hidden_input.bind(focus=self._on_field_focus)
            self.amount_input._hidden_input.bind(text=self._update_amount_label)
            self.focusable_fields.append(self.amount_input._hidden_input)
            content.add_widget(self.amount_input)

            self.amount_words_label = RTLLabel(
                text='صفر ریال',
                size_hint_y=None,
                height=dp(50),
                font_size=sp(72),
                color=(0.8, 1, 0.8, 1),
                halign='right'
            )
            content.add_widget(self.amount_words_label)
            
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
                height=dp(65)
            )
            payment_spinner.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            payment_spinner.main_btn.color = (1, 1, 1, 1)
            payment_spinner.main_btn.font_size = sp(18)
            content.add_widget(payment_spinner)
            
            btn_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(50))
            
            submit_btn = PersianButton(
                text='ثبت عملیات',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            back_btn = PersianButton(
                text='بازگشت',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            
            btn_layout.add_widget(submit_btn)
            btn_layout.add_widget(back_btn)
            content.add_widget(btn_layout)
            
            popup = PersianPopup(
                title='ثبت فروش موفق',
                content=content,
                size_hint=(0.85, 0.8),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )
            
            def on_submit(instance):
                units = units_input.text.strip()
                amount = self.amount_input.text.strip()
                payment = payment_spinner.text
                
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
        try:
            today = get_today_jalali()
            logs = get_daily_logs()
            
            if today not in logs:
                logs[today] = []
            
            if not isinstance(logs[today], list):
                logs[today] = []
            
            customer_name = kwargs.get('customer_name')
            is_new_customer = customer_name in self.session_new_customers
            
            log_data = {
                'date': today,
                'route': self.route_spinner.text,
                'customer': customer_name,
                'visit_status': kwargs.get('visit_status'),
                'time': get_current_time(),
                'is_new_customer': is_new_customer
            }
            
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
            
            # ✅ حذف ویزیت قبلی این مشتری در امروز (برای جایگزینی)
            logs[today] = [log for log in logs[today] if log.get('customer') != customer_name]
            
            logs[today].append(log_data)
            save_daily_log(today, logs[today])
            
            self.locked_route = self.route_spinner.text
            
            if hasattr(self, 'route_spinner'):
                self.route_spinner.main_btn.disabled = True
                self.route_spinner.main_btn.background_color = (0.15, 0.15, 0.15, 1)
                self.route_spinner.main_btn.color = (0.6, 0.6, 0.6, 1)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ذخیره لاگ ویزیت: {e}", error_details)

    def reset_form(self):
        self.selected_customer = None
        self.selected_customer_label.text = 'مشتری انتخاب شده: هیچ'
        self.selected_customer_label.color = (0.5, 0.5, 0.5, 1)
        self.update_customers_list()

    def show_message(self, title, message):
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            with content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                           size=lambda i, v: setattr(content_rect, 'size', v))
            
            content.add_widget(RTLLabel(
                text=message,
                size_hint_y=None,
                height=dp(80),
                font_size=sp(18),
                color=(1, 1, 1, 1)
            ))
            btn = PersianButton(
                text='باشه',
                size_hint_y=None,
                height=dp(50),
                font_size=sp(18),
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

    def go_back(self, instance):
        today = get_today_jalali()
        logs = get_daily_logs()
        
        if today in logs and logs[today] and len(logs[today]) > 0:
            if hasattr(self, 'route_spinner'):
                self.locked_route = self.route_spinner.text
        else:
            self.locked_route = None
            self.route_confirmed = False
            if hasattr(self, 'route_spinner'):
                self.route_spinner.main_btn.disabled = False
                self.route_spinner.main_btn.background_color = (0.2, 0.2, 0.2, 1)
                self.route_spinner.main_btn.color = (1, 1, 1, 1)
                self.route_spinner.text = ''
                self._last_route_text = ''
        
        self.manager.current = 'user'