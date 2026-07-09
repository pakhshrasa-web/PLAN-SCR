# screens/agents_screen.py
# ========== صفحه ثبت ویزیت بازاریابان با اسکرول دقیق ==========

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
            # پس‌زمینه تیره
            with self.canvas.before:
                Color(0.08, 0.08, 0.08, 1)
                self.bg_rect = Rectangle(pos=self.pos, size=self.size)
                self.bind(pos=self._update_bg, size=self._update_bg)
            
            # تغییر به resize برای اسکرول دقیق
            Window.softinput_mode = 'resize'
            
            # متغیر برای ذخیره فیلدهای قابل فوکوس
            self.focusable_fields = []
            
            # تعریف متغیرهای کلاس
            self.amount_words_label = None
            self._last_reason_text = ''
            self._last_search_text = ''
            self._last_route_text = ''
            self._last_customer_text = ''
            self.locked_route = None  # مسیر قفل‌شده
            self.route_confirmed = False  # آیا مسیر تأیید شده؟
            self.session_new_customers = []  # ✅ لیست مشتریان جدید در این جلسه
            
            self.settings = get_settings()
            self.selected_customer = None
            self.selected_route = None
            
            self.build_ui()
            
            # اتصال رویدادهای کیبورد
            Window.bind(on_keyboard=self._on_keyboard)
            
            # بررسی اینکه آیا امروز ویزیتی ثبت شده یا نه
            Clock.schedule_once(self._check_today_visits, 0.5)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت AgentsScreen: {e}", error_details)
            raise

    def number_to_persian_words(self, number):
        """تبدیل عدد به حروف فارسی + ریال"""
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
    
    def _check_today_visits(self, dt):
        """بررسی اینکه آیا امروز ویزیتی ثبت شده یا نه"""
        try:
            today = get_today_jalali()
            logs = get_daily_logs()
            
            # اگر امروز در لاگ‌ها هست و لیست خالی نیست
            if today in logs and logs[today] and len(logs[today]) > 0:
                # مسیر قفل بشه
                if hasattr(self, 'route_spinner'):
                    # ✅ مسیر قفل‌شده را از آخرین لاگ بگیر
                    last_visit = logs[today][-1]
                    locked_route = last_visit.get('route', '')
                    
                    if locked_route:
                        self.locked_route = locked_route
                        self.route_spinner.text = locked_route
                        self.route_spinner.main_btn.disabled = True
                        self.route_spinner.main_btn.background_color = (0.15, 0.15, 0.15, 1)
                        self.route_spinner.main_btn.color = (0.6, 0.6, 0.6, 1)
                        self.route_confirmed = True
                        # ✅ به‌روزرسانی لیست مشتریان بر اساس مسیر قفل‌شده
                        Clock.schedule_once(lambda dt: self.update_customers_list(), 0.3)
                
                # نمایش پیام به کاربر
                self.show_message('اطلاع', 'امروز قبلاً ویزیت ثبت شده است.مسیر قفل شد.')
        except Exception as e:
            print(f"خطا در بررسی ویزیت‌های امروز: {e}")
    
    def build_ui(self):
        try:
            main_layout = BoxLayout(orientation='vertical')
            
            # ========== ScrollView برای محتوا ==========
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
            
            # ========== عنوان صفحه ==========
            content.add_widget(RTLLabel(
                text='ثبت ویزیت بازاریابان',
                font_size=sp(22),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                bold=True
            ))
            
            content.add_widget(Label(size_hint_y=None, height=dp(5)))
            
            # ========== تاریخ (غیر قابل تغییر) ==========
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
            
            # ========== ساعت (غیر قابل تغییر) ==========
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
            
            # ========== مسیر (کمبوباکس - همیشه خالی شروع میشود) ==========
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
                text='',  # ✅ خالی شروع میشود
                values=route_names,
                height=dp(70)
            )
            self.route_spinner.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.route_spinner.main_btn.color = (1, 1, 1, 1)
            self.route_spinner.main_btn.font_size = sp(18)
            
            # ✅ اگر مسیر قفل‌شده وجود دارد و امروز ویزیت ثبت شده، مسیر را تنظیم و قفل کن
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
            # ✅ تغییر Clock: وقتی مسیر تغییر کرد، دیالوگ تأیید نمایش داده شود
            Clock.schedule_interval(self._check_route_change_with_confirm, 0.3)
            content.add_widget(self.route_spinner)
            
            content.add_widget(Label(size_hint_y=None, height=dp(5)))
            
            # ========== مشتری (کمبوباکس) ==========
            content.add_widget(RTLLabel(
                text='انتخاب مشتری:',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(16),
                color=(0.4, 0.7, 1, 1),
                bold=True
            ))
            
            self.customer_spinner = PersianComboBox(
                text='',
                values=[''],
                height=dp(70)
            )
            self.customer_spinner.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.customer_spinner.main_btn.color = (1, 1, 1, 1)
            self.customer_spinner.main_btn.font_size = sp(18)
            self._last_customer_text = self.customer_spinner.text
            Clock.schedule_interval(self._check_customer_change, 0.3)
            content.add_widget(self.customer_spinner)
            
            content.add_widget(Label(size_hint_y=None, height=dp(10)))

            # ========== جستجوی مشتری ==========
            content.add_widget(RTLLabel(
                text='جستجوی مشتری:',
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
                height=dp(75),
                font_size=sp(32)
            )
            self.search_input.bg_color = (0.15, 0.15, 0.15, 1)
            self.search_input.border_color = (0.3, 0.3, 0.3, 1)
            self.search_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.search_input._hidden_input.foreground_color = (1, 1, 1, 1)
            self.search_input._hidden_input.bind(focus=self._on_field_focus)
            self.focusable_fields.append(self.search_input._hidden_input)
            content.add_widget(self.search_input)
            
            # ========== دکمه افزودن مشتری جدید ==========
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
            
            # بررسی تغییرات جستجو با Clock
            self._last_search_text = ''
            Clock.schedule_interval(self._check_search_change, 0.3)
            
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
                self.customer_spinner.values = ['مشتری‌ای یافت نشد']
                self.customer_spinner.text = 'مشتری‌ای یافت نشد'
                
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در جستجوی مشتری: {e}", error_details)

    def _check_route_change_with_confirm(self, dt):
        """بررسی تغییر مسیر و نمایش دیالوگ تأیید"""
        if hasattr(self, 'route_spinner') and not self.route_spinner.main_btn.disabled:
            current_text = self.route_spinner.text
            if current_text != self._last_route_text and current_text and current_text != '':
                self._last_route_text = current_text
                # ✅ نمایش دیالوگ تأیید مسیر
                self.show_route_confirm_dialog(current_text)
    
    def _check_customer_change(self, dt):
        """بررسی تغییر مشتری با Clock"""
        if hasattr(self, 'customer_spinner'):
            current_text = self.customer_spinner.text
            if current_text != self._last_customer_text:
                self._last_customer_text = current_text
                if current_text and current_text not in ['', 'مشتری‌ای یافت نشد']:
                    self.on_customer_selected(current_text)
    
    def update_time(self, dt):
        """بروزرسانی ساعت"""
        self.time_label.text = get_current_time()
    
    def on_route_selected(self, value):
        """زمانی که مسیر انتخاب می‌شود"""
        self.selected_route = value
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
                self.customer_spinner.values = ['مشتری‌ای یافت نشد']
                self.customer_spinner.text = 'مشتری‌ای یافت نشد'
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در بروزرسانی لیست مشتریان: {e}", error_details)
    
    def on_customer_selected(self, value):
        """زمانی که مشتری انتخاب می‌شود - نمایش دیالوگ تأیید"""
        if value and value not in ['', 'مشتری‌ای یافت نشد']:
            self.selected_customer = value
            self.show_confirm_dialog(value)
    
    # ============================================================
    # دیالوگ افزودن مشتری جدید
    # ============================================================
    
    def show_add_customer_dialog(self, instance):
        """نمایش دیالوگ افزودن مشتری جدید (مشابه AdminScreen)"""
        try:
            from utils.file_manager import get_routes, get_customers, add_customer
            from utils.jalali_date import get_today_jalali

            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
            with content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                           size=lambda i, v: setattr(content_rect, 'size', v))

            # عنوان
            content.add_widget(RTLLabel(
                text='افزودن مشتری جدید',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(18),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))

            # انتخاب مسیر
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

            # مسیر پیش‌فرض = مسیر انتخاب شده در صفحه
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

            # نام مشتری (اجباری)
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

            # نام فروشگاه (اختیاری)
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

            # موبایل (اجباری)
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

            # آدرس (اختیاری)
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

            # دکمه‌ها
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

                    # اعتبارسنجی نام مشتری
                    name = customer_name_input.text.strip()
                    if not name:
                        self.show_message('خطا', 'نام مشتری الزامی است')
                        customer_name_input._hidden_input.focus = True
                        return

                    # اعتبارسنجی شماره موبایل
                    mobile = customer_mobile_input.text.strip()
                    if not mobile:
                        self.show_message('خطا', 'شماره موبایل الزامی است')
                        customer_mobile_input._hidden_input.focus = True
                        return

                    # اعتبارسنجی فرمت موبایل
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

                    # بررسی تکراری بودن نام مشتری
                    all_customers = get_customers()
                    for c in all_customers:
                        if c.get('name', '').strip() == name:
                            self.show_message('خطا', f'مشتری با نام "{name}" قبلاً ثبت شده است')
                            customer_name_input._hidden_input.focus = True
                            return
                        
                        # بررسی تکراری بودن شماره موبایل
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
                    
                    # ✅ اضافه کردن نام مشتری به لیست مشتریان جدید جلسه
                    self.session_new_customers.append(name)
                    
                    popup.dismiss()
                    
                    # به‌روزرسانی لیست مشتریان
                    self.update_customers_list()
                    self.show_message('موفق', f'مشتری "{name}" با موفقیت اضافه شد')
                    
                    # اگر مسیر انتخاب شده در دیالوگ با مسیر فعلی یکی بود، مشتری در لیست نمایش داده میشه
                    if route_name == self.route_spinner.text:
                        self.filter_customers('')
                    
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

    # ============================================================
    # دیالوگ‌های ویزیت
    # ============================================================
    
    def show_route_confirm_dialog(self, route_name):
        """نمایش دیالوگ تأیید مسیر انتخاب شده"""
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
                # ✅ قفل کردن مسیر و ذخیره در locked_route
                self.locked_route = route_name
                self.route_confirmed = True
                self.route_spinner.main_btn.disabled = True
                self.route_spinner.main_btn.background_color = (0.15, 0.15, 0.15, 1)
                self.route_spinner.main_btn.color = (0.6, 0.6, 0.6, 1)
                # ✅ به‌روزرسانی لیست مشتریان بر اساس مسیر انتخاب شده
                self.update_customers_list()
                self.show_message('موفق', f'مسیر "{route_name}" با موفقیت انتخاب و قفل شد.')
            
            def on_no(instance):
                popup.dismiss()
                # ✅ برگرداندن کامبوباکس به حالت خالی
                self.route_spinner.text = ''
                self._last_route_text = ''
                self.route_confirmed = False
                # غیرفعال کردن مشتریان
                self.customer_spinner.values = ['']
                self.customer_spinner.text = ''
            
            yes_btn.bind(on_press=on_yes)
            no_btn.bind(on_press=on_no)
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش دیالوگ تأیید مسیر: {e}", error_details)

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
        """دیالوگ علت ویزیت ناموفق"""
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
                height=dp(65)
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
        """به‌روزرسانی برچسب نمایش مبلغ به حروف"""
        try:
            # اگر لیبل وجود ندارد، کاری نکن
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
                text=f'فروش موفق برای "{customer_name}"',
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
            
            # مبلغ فاکتور
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

            # برچسب نمایش عدد به حروف
            self.amount_words_label = RTLLabel(
                text='صفر ریال',
                size_hint_y=None,
                height=dp(50),
                font_size=sp(72),
                color=(0.8, 1, 0.8, 1),
                halign='right'
            )
            content.add_widget(self.amount_words_label)
            
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
            
            customer_name = kwargs.get('customer_name')
            
            # ✅ بررسی اینکه آیا مشتری در همین جلسه اضافه شده
            is_new_customer = customer_name in self.session_new_customers
            
            log_data = {
                'date': today,
                'route': self.route_spinner.text,
                'customer': customer_name,
                'visit_status': kwargs.get('visit_status'),
                'time': get_current_time(),
                'is_new_customer': is_new_customer  # ✅ ذخیره میشود
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
            
            # ذخیره مسیر قفل‌شده
            self.locked_route = self.route_spinner.text
            
            # قفل کردن مسیر فقط بعد از ثبت موفق ویزیت
            if hasattr(self, 'route_spinner'):
                self.route_spinner.main_btn.disabled = True
                self.route_spinner.main_btn.background_color = (0.15, 0.15, 0.15, 1)
                self.route_spinner.main_btn.color = (0.6, 0.6, 0.6, 1)
            
            # قفل کردن مشتری هم بعد از ثبت ویزیت
            if hasattr(self, 'customer_spinner'):
                self.customer_spinner.main_btn.disabled = True
                self.customer_spinner.main_btn.background_color = (0.15, 0.15, 0.15, 1)
                self.customer_spinner.main_btn.color = (0.6, 0.6, 0.6, 1)
            
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
            # ویزیت ثبت شده، مسیر را ذخیره کن
            if hasattr(self, 'route_spinner'):
                self.locked_route = self.route_spinner.text
        else:
            # ویزیت ثبت نشده، قفل را باز کن
            self.locked_route = None
            self.route_confirmed = False
            if hasattr(self, 'route_spinner'):
                self.route_spinner.main_btn.disabled = False
                self.route_spinner.main_btn.background_color = (0.2, 0.2, 0.2, 1)
                self.route_spinner.main_btn.color = (1, 1, 1, 1)
                self.route_spinner.text = ''
                self._last_route_text = ''
            
            if hasattr(self, 'customer_spinner'):
                self.customer_spinner.main_btn.disabled = False
                self.customer_spinner.main_btn.background_color = (0.2, 0.2, 0.2, 1)
                self.customer_spinner.main_btn.color = (1, 1, 1, 1)
        
        self.manager.current = 'user'