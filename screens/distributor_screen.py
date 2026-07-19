# screens/distributor_screen.py
# ========== صفحه موزع ==========

import traceback
import os
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.window import Window

from utils.rtl_widgets import PersianButton, RTLLabel, PersianPopup, RTLTextInput, PersianComboBox
from utils.persian_text import PersianLabel, number_to_words
from utils.file_manager import get_customers, get_routes, get_agents, get_settings, get_daily_logs
from utils.jalali_date import get_today_jalali, get_current_time
from utils.delivery_manager import save_delivery, get_deliveries_by_date, get_delivery_stats
from error_handler import ErrorPopup


class DistributorScreen(Screen):
    """صفحه موزع - مدیریت توزیع کالا"""
    
    def __init__(self, **kwargs):
        try:
            super().__init__(**kwargs)
            with self.canvas.before:
                Color(0.08, 0.08, 0.08, 1)
                self.bg_rect = Rectangle(pos=self.pos, size=self.size)
                self.bind(pos=self._update_bg, size=self._update_bg)
            
            Window.softinput_mode = 'resize'
            self.focusable_fields = []
            
            self.settings = get_settings()
            self.current_route = None
            self.selected_customer = None
            self._last_route_text = ''
            
            self.temp_checks = []
            self.temp_delivery_data = {}
            
            self.payment_methods = {
                'نقد': False,
                'چک': False,
                'نسیه': False
            }
            
            self._amount_warning_shown = False
            self._warning_response = None
            self.save_btn = None
            
            self.build_ui()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت DistributorScreen: {e}", error_details)
            raise
    
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
    
    def build_ui(self):
        """ساخت رابط کاربری"""
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
                text='توزیع کالا',
                font_size=sp(26),
                size_hint_y=None,
                height=dp(55),
                color=(1, 1, 1, 1),
                bold=True
            ))
            content.add_widget(Label(size_hint_y=None, height=dp(5)))
            
            # ========== تاریخ و ساعت ==========
            date_time_layout = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(10))
            
            date_time_layout.add_widget(RTLLabel(
                text=f'تاریخ: {get_today_jalali()}',
                size_hint_x=0.5,
                size_hint_y=None,
                height=dp(40),
                font_size=sp(18),
                color=(0.4, 0.7, 1, 1)
            ))
            
            self.time_label = RTLLabel(
                text=f'ساعت: {get_current_time()}',
                size_hint_x=0.5,
                size_hint_y=None,
                height=dp(40),
                font_size=sp(18),
                color=(0.4, 0.7, 1, 1)
            )
            date_time_layout.add_widget(self.time_label)
            
            content.add_widget(date_time_layout)
            content.add_widget(Label(size_hint_y=None, height=dp(5)))
            
            # ========== انتخاب مسیر ==========
            content.add_widget(RTLLabel(
                text='انتخاب مسیر:',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(18),
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
            self.route_spinner.main_btn.font_size = sp(20)
            content.add_widget(self.route_spinner)
            
            self._last_route_text = self.route_spinner.text
            Clock.schedule_interval(self._check_route_change, 0.3)
            
            content.add_widget(Label(size_hint_y=None, height=dp(5)))
            
            # ========== دکمه افزودن مشتری ==========
            add_customer_btn = PersianButton(
                text='افزودن مشتری جدید',
                background_color=(0.2, 0.6, 0.2, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            add_customer_btn.bind(on_press=self.show_add_customer_dialog)
            content.add_widget(add_customer_btn)
            content.add_widget(Label(size_hint_y=None, height=dp(5)))
            
            # ========== دکمه انتخاب مشتری ==========
            select_customer_btn = PersianButton(
                text='انتخاب مشتری',
                background_color=(0.2, 0.5, 0.9, 1),
                size_hint_y=None,
                height=dp(60),
                color=(1, 1, 1, 1),
                font_size=sp(22),
                bold=True
            )
            select_customer_btn.bind(on_press=self.show_customer_selection_dialog)
            content.add_widget(select_customer_btn)
            
            # ========== نمایش مشتری انتخاب شده ==========
            self.selected_customer_label = RTLLabel(
                text='مشتری انتخاب شده: هیچ',
                size_hint_y=None,
                height=dp(45),
                font_size=sp(20),
                color=(0.5, 0.5, 0.5, 1),
                bold=True
            )
            content.add_widget(self.selected_customer_label)
            content.add_widget(Label(size_hint_y=None, height=dp(5)))
            
            # ========== دکمه بازگشت ==========
            back_btn = PersianButton(
                text='بازگشت',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            back_btn.bind(on_press=self.go_back)
            content.add_widget(back_btn)
            
            scroll.add_widget(content)
            main_layout.add_widget(scroll)
            self.add_widget(main_layout)
            
            Clock.schedule_interval(self.update_time, 60)
            self.load_routes()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت UI DistributorScreen: {e}", error_details)
            raise
    
    def _check_route_change(self, dt):
        """بررسی تغییر مسیر با تایمر"""
        try:
            current_text = self.route_spinner.text
            if current_text != self._last_route_text and current_text and current_text != '':
                self._last_route_text = current_text
                self.on_route_selected(current_text)
        except Exception as e:
            print(f"خطا در بررسی تغییر مسیر: {e}")
    
    def update_time(self, dt):
        self.time_label.text = f'ساعت: {get_current_time()}'
    
    def load_routes(self):
        """بارگذاری لیست مسیرها"""
        try:
            routes = get_routes()
            route_names = [r.get('name', '') for r in routes if r.get('name')]
            
            if not route_names:
                route_names = ['مسیر یک', 'مسیر دو', 'مسیر سه']
            
            self.route_spinner.values = route_names
            if route_names:
                self.route_spinner.text = route_names[0]
                self.current_route = route_names[0]
                
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در بارگذاری مسیرها: {e}", error_details)
    
    def on_route_selected(self, value):
        """تغییر مسیر - بدون قفل شدن"""
        try:
            if value:
                self.current_route = value
        except Exception as e:
            print(f"خطا در انتخاب مسیر: {e}")
    
    # ============================================================
    # دیالوگ انتخاب مشتری
    # ============================================================
    
    def show_customer_selection_dialog(self, instance):
        """نمایش دیالوگ انتخاب مشتری با هایلایت مشتریان توزیع شده"""
        try:
            selected_route = self.route_spinner.text
            
            if not selected_route:
                self.show_message('خطا', 'لطفاً ابتدا یک مسیر انتخاب کنید')
                return
            
            all_customers = get_customers()
            filtered_customers = []
            for c in all_customers:
                if c.get('route_name', '').strip() == selected_route.strip():
                    filtered_customers.append(c.get('name', ''))
            
            if not filtered_customers:
                self.show_message('توجه', 'هیچ مشتری‌ای در این مسیر یافت نشد')
                return
            
            today = get_today_jalali()
            deliveries = get_deliveries_by_date(today)
            delivered_today = []
            for d in deliveries:
                if d.get('customer_name'):
                    delivered_today.append(d.get('customer_name'))
            
            content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
            with content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                            size=lambda i, v: setattr(content_rect, 'size', v))
            
            title_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(60))
            
            title_layout.add_widget(RTLLabel(
                text=f'انتخاب مشتری - {selected_route}',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(22),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))
            
            title_layout.add_widget(RTLLabel(
                text='مشتریان آبی رنگ امروز توزیع شده‌اند',
                size_hint_y=None,
                height=dp(25),
                font_size=sp(15),
                color=(0.6, 0.6, 0.6, 1)
            ))
            
            content.add_widget(title_layout)
            
            search_input = RTLTextInput(
                hint_text='جستجوی مشتری...',
                multiline=False,
                size_hint_y=None,
                height=dp(60),
                font_size=sp(36)
            )
            search_input.bg_color = (0.15, 0.15, 0.15, 1)
            search_input.border_color = (0.3, 0.3, 0.3, 1)
            search_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            search_input._hidden_input.foreground_color = (1, 1, 1, 1)
            content.add_widget(search_input)
            
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
            
            def filter_customers(text):
                customers_grid.clear_widgets()
                search_text = text.strip()
                
                for customer in filtered_customers:
                    if search_text and search_text not in customer:
                        continue
                    
                    is_delivered = customer in delivered_today
                    
                    customer_btn = PersianButton(
                        text=customer,
                        size_hint_y=None,
                        height=dp(50),
                        background_color=(0.2, 0.5, 0.9, 1) if is_delivered else (0.2, 0.2, 0.2, 1),
                        color=(1, 1, 1, 1),
                        font_size=sp(20)
                    )
                    customer_btn.bind(
                        on_press=lambda x, name=customer: self._handle_customer_selection(name)
                    )
                    customers_grid.add_widget(customer_btn)
                
                customers_grid.height = len(customers_grid.children) * dp(55) + dp(10)
            
            search_input._hidden_input.bind(text=lambda i, v: filter_customers(v))
            filter_customers('')
            
            customers_scroll.add_widget(customers_grid)
            content.add_widget(customers_scroll)
            
            close_btn = PersianButton(
                text='بستن',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            content.add_widget(close_btn)
            
            popup = PersianPopup(
                title='انتخاب مشتری',
                content=content,
                size_hint=(0.9, 0.75),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=True
            )
            
            self.customer_selection_popup = popup
            close_btn.bind(on_press=popup.dismiss)
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش دیالوگ انتخاب مشتری: {e}", error_details)
    
    def _handle_customer_selection(self, customer_name):
        """مدیریت انتخاب مشتری از دیالوگ"""
        try:
            if hasattr(self, 'customer_selection_popup'):
                self.customer_selection_popup.dismiss()
            
            today = get_today_jalali()
            deliveries = get_deliveries_by_date(today)
            delivered_today = [d.get('customer_name') for d in deliveries if d.get('customer_name')]
            
            if customer_name in delivered_today:
                self.show_delivery_change_dialog(customer_name)
            else:
                self.selected_customer = customer_name
                self.selected_customer_label.text = f'مشتری انتخاب شده: {customer_name}'
                self.selected_customer_label.color = (0.2, 0.8, 0.4, 1)
                self.show_delivery_confirmation_for_customer(customer_name)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در انتخاب مشتری: {e}", error_details)
    
    def show_delivery_change_dialog(self, customer_name):
        """دیالوگ تغییر وضعیت برای مشتری توزیع شده"""
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            
            content.add_widget(RTLLabel(
                text=f'مشتری "{customer_name}" امروز توزیع شده است.\nآیا از تغییر وضعیت اطمینان دارید؟',
                size_hint_y=None,
                height=dp(70),
                font_size=sp(20),
                color=(1, 1, 1, 1)
            ))
            
            btn_layout = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(10))
            
            yes_btn = PersianButton(
                text='بله',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            no_btn = PersianButton(
                text='خیر',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            
            btn_layout.add_widget(yes_btn)
            btn_layout.add_widget(no_btn)
            content.add_widget(btn_layout)
            
            popup = PersianPopup(
                title='تأیید تغییر وضعیت',
                content=content,
                size_hint=(0.85, 0.4),
                auto_dismiss=False
            )
            
            yes_btn.bind(on_press=lambda x: self._confirm_delivery_change(popup, customer_name))
            no_btn.bind(on_press=popup.dismiss)
            
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    
    def _confirm_delivery_change(self, popup, customer_name):
        """تأیید تغییر وضعیت و شروع فرآیند جدید"""
        try:
            popup.dismiss()
            self.selected_customer = customer_name
            self.selected_customer_label.text = f'مشتری انتخاب شده: {customer_name}'
            self.selected_customer_label.color = (0.2, 0.8, 0.4, 1)
            self.show_delivery_confirmation_for_customer(customer_name)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    
    # ============================================================
    # دیالوگ افزودن مشتری
    # ============================================================
    
    def show_add_customer_dialog(self, instance):
        try:
            from utils.file_manager import get_routes, get_customers, add_customer

            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
            with content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                           size=lambda i, v: setattr(content_rect, 'size', v))

            content.add_widget(RTLLabel(
                text='افزودن مشتری جدید',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(22),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))

            content.add_widget(RTLLabel(
                text='انتخاب مسیر:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(16),
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
                height=dp(60)
            )
            customer_route_spinner.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            customer_route_spinner.main_btn.color = (1, 1, 1, 1)
            customer_route_spinner.main_btn.font_size = sp(18)
            content.add_widget(customer_route_spinner)

            content.add_widget(RTLLabel(
                text='نام مشتری (الزامی):',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))
            customer_name_input = RTLTextInput(
                hint_text='نام مشتری را وارد کنید',
                multiline=False,
                size_hint_y=None,
                height=dp(60),
                font_size=sp(48)
            )
            customer_name_input.bg_color = (0.15, 0.15, 0.15, 1)
            customer_name_input.border_color = (0.3, 0.3, 0.3, 1)
            customer_name_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            customer_name_input._hidden_input.foreground_color = (1, 1, 1, 1)
            content.add_widget(customer_name_input)

            content.add_widget(RTLLabel(
                text='نام فروشگاه:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))
            customer_store_input = RTLTextInput(
                hint_text='نام فروشگاه را وارد کنید (اختیاری)',
                multiline=False,
                size_hint_y=None,
                height=dp(60),
                font_size=sp(48)
            )
            customer_store_input.bg_color = (0.15, 0.15, 0.15, 1)
            customer_store_input.border_color = (0.3, 0.3, 0.3, 1)
            customer_store_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            customer_store_input._hidden_input.foreground_color = (1, 1, 1, 1)
            content.add_widget(customer_store_input)

            content.add_widget(RTLLabel(
                text='موبایل (الزامی):',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))
            customer_mobile_input = RTLTextInput(
                hint_text='شماره موبایل را وارد کنید (11 رقم)',
                multiline=False,
                size_hint_y=None,
                height=dp(60),
                font_size=sp(48)
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
                height=dp(28),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))
            customer_address_input = RTLTextInput(
                hint_text='آدرس را وارد کنید (اختیاری)',
                multiline=False,
                size_hint_y=None,
                height=dp(60),
                font_size=sp(48)
            )
            customer_address_input.bg_color = (0.15, 0.15, 0.15, 1)
            customer_address_input.border_color = (0.3, 0.3, 0.3, 1)
            customer_address_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            customer_address_input._hidden_input.foreground_color = (1, 1, 1, 1)
            content.add_widget(customer_address_input)

            btn_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(50))

            submit_btn = PersianButton(
                text='افزودن مشتری',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            cancel_btn = PersianButton(
                text='انصراف',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(18)
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
                    popup.dismiss()
                    self.show_message('موفق', f'مشتری "{name}" با موفقیت اضافه شد')
                    
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
    # فرآیند توزیع
    # ============================================================
    
    def show_delivery_confirmation_for_customer(self, customer_name):
        """نمایش دیالوگ تأیید تحویل برای مشتری انتخاب شده"""
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            
            content.add_widget(RTLLabel(
                text=f'آیا قصد تحویل فاکتور برای {customer_name} را دارید؟',
                size_hint_y=None,
                height=dp(55),
                font_size=sp(20),
                color=(1, 1, 1, 1)
            ))
            
            btn_layout = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(10))
            
            yes_btn = PersianButton(
                text='بله',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            no_btn = PersianButton(
                text='خیر',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            
            btn_layout.add_widget(yes_btn)
            btn_layout.add_widget(no_btn)
            content.add_widget(btn_layout)
            
            popup = PersianPopup(
                title='تأیید تحویل',
                content=content,
                size_hint=(0.85, 0.35),
                auto_dismiss=False
            )
            
            yes_btn.bind(on_press=lambda x: self._on_delivery_confirmed(popup, customer_name))
            no_btn.bind(on_press=popup.dismiss)
            
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش دیالوگ تأیید: {e}", error_details)
    
    def _on_delivery_confirmed(self, popup, customer_name):
        """پس از تأیید تحویل - نمایش دیالوگ اطلاعات فاکتور"""
        try:
            popup.dismiss()
            self.temp_delivery_data['customer_name'] = customer_name
            self.show_invoice_dialog()
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    
    def show_invoice_dialog(self):
        """دیالوگ وارد کردن اطلاعات فاکتور با نمایش مبلغ به حروف"""
        try:
            from utils.persian_text import number_to_words
            
            main_container = BoxLayout(orientation='vertical', spacing=dp(5))
            
            scroll = ScrollView(
                do_scroll_x=False,
                do_scroll_y=True,
                size_hint=(1, 1),
                scroll_type=['bars', 'content'],
                bar_width=dp(6)
            )
            
            content = BoxLayout(
                orientation='vertical',
                padding=dp(20),
                spacing=dp(12),
                size_hint_y=None
            )
            content.bind(minimum_height=content.setter('height'))
            
            content.add_widget(RTLLabel(
                text='اطلاعات فاکتور',
                size_hint_y=None,
                height=dp(45),
                font_size=sp(24),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))
            
            content.add_widget(RTLLabel(
                text='شماره فاکتور:',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(18),
                color=(1, 1, 1, 1)
            ))
            invoice_number = RTLTextInput(
                multiline=False,
                size_hint_y=None,
                height=dp(60),
                font_size=sp(48),
                hint_text='شماره فاکتور را وارد کنید'
            )
            invoice_number.bg_color = (0.15, 0.15, 0.15, 1)
            content.add_widget(invoice_number)
            
            content.add_widget(RTLLabel(
                text='مبلغ فاکتور (ریال):',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(18),
                color=(1, 1, 1, 1)
            ))
            self.invoice_amount_input = RTLTextInput(
                text='0',
                multiline=False,
                size_hint_y=None,
                height=dp(60),
                font_size=sp(48),
                hint_text='مبلغ فاکتور را وارد کنید'
            )
            self.invoice_amount_input.bg_color = (0.15, 0.15, 0.15, 1)
            
            def on_invoice_focus(instance, value):
                if value:
                    Clock.schedule_once(lambda dt: self._select_all_text(instance), 0.1)
            
            self.invoice_amount_input._hidden_input.bind(focus=on_invoice_focus)
            content.add_widget(self.invoice_amount_input)
            
            # نمایش مبلغ به حروف
            self.invoice_amount_words_label = RTLLabel(
                text='صفر ریال',
                size_hint_y=None,
                height=dp(60),
                font_size=sp(22),
                color=(0.4, 0.9, 0.4, 1),
                halign='right',
                bold=True
            )
            content.add_widget(self.invoice_amount_words_label)
            
            def update_invoice_words(instance, value):
                try:
                    amount = value.strip()
                    if not amount or amount == '0':
                        self.invoice_amount_words_label.text = 'صفر ریال'
                        return
                    
                    clean_amount = amount.replace(',', '').strip()
                    if clean_amount:
                        number = float(clean_amount)
                        words = number_to_words(int(number))
                        if words:
                            self.invoice_amount_words_label.text = words
                        else:
                            self.invoice_amount_words_label.text = 'صفر ریال'
                except Exception as e:
                    print(f"خطا در تبدیل مبلغ به حروف: {e}")
                    self.invoice_amount_words_label.text = 'خطا در تبدیل'
            
            self.invoice_amount_input._hidden_input.bind(text=update_invoice_words)
            Clock.schedule_once(lambda dt: update_invoice_words(None, '0'), 0.1)
            
            btn_layout = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(15))
            
            confirm_btn = PersianButton(
                text='تأیید',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(55),
                color=(1, 1, 1, 1),
                font_size=sp(20),
                bold=True
            )
            cancel_btn = PersianButton(
                text='انصراف',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(55),
                color=(1, 1, 1, 1),
                font_size=sp(20),
                bold=True
            )
            
            btn_layout.add_widget(confirm_btn)
            btn_layout.add_widget(cancel_btn)
            content.add_widget(btn_layout)
            
            scroll.add_widget(content)
            main_container.add_widget(scroll)
            
            popup = PersianPopup(
                title='اطلاعات فاکتور',
                content=main_container,
                size_hint=(0.9, 0.7),
                auto_dismiss=False
            )
            
            confirm_btn.bind(on_press=lambda x: self._on_invoice_confirmed(
                popup, invoice_number.text, self.invoice_amount_input.text
            ))
            cancel_btn.bind(on_press=popup.dismiss)
            
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش دیالوگ فاکتور: {e}", error_details)
    
    def _on_invoice_confirmed(self, popup, inv_number, inv_amount):
        """پس از تأیید فاکتور - بررسی تحویل"""
        try:
            popup.dismiss()
            
            if not inv_number or not inv_amount:
                self.show_message('خطا', 'لطفاً همه فیلدها را پر کنید')
                return
            
            try:
                amount = float(inv_amount.replace(',', ''))
            except:
                self.show_message('خطا', 'مبلغ فاکتور معتبر نیست')
                return
            
            self.temp_delivery_data['invoice_number'] = inv_number
            self.temp_delivery_data['invoice_amount'] = amount
            
            self.show_delivery_check_dialog()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    
    def show_delivery_check_dialog(self):
        """دیالوگ: آیا فاکتور تحویل گردید؟"""
        try:
            customer_name = self.temp_delivery_data.get('customer_name', '')
            
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            
            content.add_widget(RTLLabel(
                text=f'آیا فاکتور به {customer_name} تحویل گردید؟',
                size_hint_y=None,
                height=dp(55),
                font_size=sp(20),
                color=(1, 1, 1, 1)
            ))
            
            btn_layout = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(10))
            
            yes_btn = PersianButton(
                text='بله',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            no_btn = PersianButton(
                text='خیر',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            
            btn_layout.add_widget(yes_btn)
            btn_layout.add_widget(no_btn)
            content.add_widget(btn_layout)
            
            popup = PersianPopup(
                title='تأیید تحویل',
                content=content,
                size_hint=(0.85, 0.35),
                auto_dismiss=False
            )
            
            yes_btn.bind(on_press=lambda x: self._on_delivered(popup))
            no_btn.bind(on_press=lambda x: self._on_not_delivered(popup))
            
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    
    def _on_delivered(self, popup):
        """فاکتور تحویل شد - بررسی کامل بودن"""
        try:
            popup.dismiss()
            self.show_full_delivery_dialog()
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    
    def _on_not_delivered(self, popup):
        """فاکتور تحویل نشد - نمایش علت"""
        try:
            popup.dismiss()
            self.show_fail_reason_dialog()
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    
    def show_fail_reason_dialog(self):
        """دیالوگ علت عدم تحویل"""
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(12))
            
            content.add_widget(RTLLabel(
                text='علت عدم تحویل فاکتور',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(22),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))
            
            reasons = [
                'بسته بودن فروشگاه',
                'عدم تطابق سفارش',
                'عدم تطابق خریدار',
                'عدم تطابق قیمت',
                'عدم تطابق نحوه تسویه',
                'عدم تحویل به موقع'
            ]
            
            fail_reason = PersianComboBox(
                values=reasons,
                text=reasons[0] if reasons else '',
                height=dp(50)
            )
            fail_reason.main_btn.background_color = (0.15, 0.15, 0.15, 1)
            fail_reason.main_btn.color = (1, 1, 1, 1)
            fail_reason.main_btn.font_size = sp(20)
            content.add_widget(fail_reason)
            
            content.add_widget(RTLLabel(
                text='توضیحات:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))
            description = RTLTextInput(
                multiline=True,
                size_hint_y=None,
                height=dp(90),
                font_size=sp(48),
                hint_text='توضیحات اضافی (اختیاری)'
            )
            description.bg_color = (0.15, 0.15, 0.15, 1)
            content.add_widget(description)
            
            btn_layout = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(10))
            
            save_btn = PersianButton(
                text='ثبت',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            cancel_btn = PersianButton(
                text='انصراف',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            
            btn_layout.add_widget(save_btn)
            btn_layout.add_widget(cancel_btn)
            content.add_widget(btn_layout)
            
            popup = PersianPopup(
                title='عدم تحویل',
                content=content,
                size_hint=(0.85, 0.6),
                auto_dismiss=False
            )
            
            save_btn.bind(on_press=lambda x: self._save_fail_delivery(
                popup, fail_reason.text, description.text
            ))
            cancel_btn.bind(on_press=popup.dismiss)
            
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    
    def _save_fail_delivery(self, popup, reason, description):
        """ذخیره توزیع ناموفق"""
        try:
            popup.dismiss()
            
            data = self.temp_delivery_data.copy()
            data.update({
                'delivery_status': 'ناموفق',
                'fail_reason': reason,
                'fail_description': description,
                'full_delivery': False,
                'route': self.current_route
            })
            
            success, message, _ = save_delivery(data)
            self.show_message('موفق' if success else 'خطا', message)
            
            if success:
                self.temp_delivery_data = {}
                self.selected_customer_label.text = 'مشتری انتخاب شده: هیچ'
                self.selected_customer_label.color = (0.5, 0.5, 0.5, 1)
                
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    
    def show_full_delivery_dialog(self):
        """دیالوگ: آیا فاکتور کامل تحویل شد؟"""
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            
            content.add_widget(RTLLabel(
                text='آیا فاکتور به صورت کامل تحویل شد؟',
                size_hint_y=None,
                height=dp(55),
                font_size=sp(20),
                color=(1, 1, 1, 1)
            ))
            
            btn_layout = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(10))
            
            yes_btn = PersianButton(
                text='بله',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            no_btn = PersianButton(
                text='خیر',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            
            btn_layout.add_widget(yes_btn)
            btn_layout.add_widget(no_btn)
            content.add_widget(btn_layout)
            
            popup = PersianPopup(
                title='کامل بودن تحویل',
                content=content,
                size_hint=(0.85, 0.35),
                auto_dismiss=False
            )
            
            yes_btn.bind(on_press=lambda x: self._on_full_delivery(popup))
            no_btn.bind(on_press=lambda x: self._on_partial_delivery(popup))
            
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    
    def _on_full_delivery(self, popup):
        """تحویل کامل - رفتن به تسویه"""
        try:
            popup.dismiss()
            self.temp_delivery_data['full_delivery'] = True
            self.temp_delivery_data['returned_quantity'] = 0
            self.temp_delivery_data['returned_amount'] = 0
            self.temp_delivery_data['return_reason'] = None
            self.show_settlement_dialog()
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    
    def _on_partial_delivery(self, popup):
        """تحویل ناقص - نمایش دیالوگ برگشتی"""
        try:
            popup.dismiss()
            self.show_return_dialog()
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    
    def show_return_dialog(self):
        """دیالوگ اطلاعات برگشتی با نمایش مبلغ به حروف"""
        try:
            from utils.persian_text import number_to_words
            
            invoice_amount = self.temp_delivery_data.get('invoice_amount', 0)
            
            main_container = BoxLayout(orientation='vertical', spacing=dp(5))
            
            scroll = ScrollView(
                do_scroll_x=False,
                do_scroll_y=True,
                size_hint=(1, 1),
                scroll_type=['bars', 'content'],
                bar_width=dp(6)
            )
            
            content = BoxLayout(
                orientation='vertical',
                padding=dp(20),
                spacing=dp(12),
                size_hint_y=None
            )
            content.bind(minimum_height=content.setter('height'))
            
            content.add_widget(RTLLabel(
                text='اطلاعات برگشتی',
                size_hint_y=None,
                height=dp(45),
                font_size=sp(24),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))
            
            content.add_widget(RTLLabel(
                text='تعداد برگشتی:',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(18),
                color=(1, 1, 1, 1)
            ))
            return_quantity = RTLTextInput(
                multiline=False,
                size_hint_y=None,
                height=dp(60),
                font_size=sp(48),
                hint_text='تعداد',
                input_filter='int'
            )
            return_quantity.bg_color = (0.15, 0.15, 0.15, 1)
            content.add_widget(return_quantity)
            
            content.add_widget(RTLLabel(
                text='مبلغ برگشتی (ریال):',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(18),
                color=(1, 1, 1, 1)
            ))
            self.return_amount_input = RTLTextInput(
                text='0',
                multiline=False,
                size_hint_y=None,
                height=dp(60),
                font_size=sp(48),
                hint_text='مبلغ'
            )
            self.return_amount_input.bg_color = (0.15, 0.15, 0.15, 1)
            
            def on_return_focus(instance, value):
                if value:
                    Clock.schedule_once(lambda dt: self._select_all_text(instance), 0.1)
            
            self.return_amount_input._hidden_input.bind(focus=on_return_focus)
            content.add_widget(self.return_amount_input)
            
            # نمایش مبلغ برگشتی به حروف
            self.return_amount_words_label = RTLLabel(
                text='صفر ریال',
                size_hint_y=None,
                height=dp(60),
                font_size=sp(22),
                color=(0.4, 0.9, 0.4, 1),
                halign='right',
                bold=True
            )
            content.add_widget(self.return_amount_words_label)
            
            def update_return_words(instance, value):
                try:
                    amount = value.strip()
                    if not amount or amount == '0':
                        self.return_amount_words_label.text = 'صفر ریال'
                        return
                    
                    clean_amount = amount.replace(',', '').strip()
                    if clean_amount:
                        number = float(clean_amount)
                        words = number_to_words(int(number))
                        if words:
                            self.return_amount_words_label.text = words
                        else:
                            self.return_amount_words_label.text = 'صفر ریال'
                except Exception as e:
                    print(f"خطا در تبدیل مبلغ برگشتی به حروف: {e}")
                    self.return_amount_words_label.text = 'خطا در تبدیل'
            
            self.return_amount_input._hidden_input.bind(text=update_return_words)
            Clock.schedule_once(lambda dt: update_return_words(None, '0'), 0.1)
            
            content.add_widget(RTLLabel(
                text=f'مبلغ مانده: {invoice_amount:,.0f} ریال',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(22),
                bold=True,
                color=(0.2, 0.8, 0.2, 1)
            ))
            
            content.add_widget(RTLLabel(
                text='علت برگشتی:',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(18),
                color=(1, 1, 1, 1)
            ))
            return_reason = RTLTextInput(
                multiline=True,
                size_hint_y=None,
                height=dp(80),
                font_size=sp(48),
                hint_text='علت برگشت کالا'
            )
            return_reason.bg_color = (0.15, 0.15, 0.15, 1)
            content.add_widget(return_reason)
            
            btn_layout = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(15))
            
            save_btn = PersianButton(
                text='ثبت',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(55),
                color=(1, 1, 1, 1),
                font_size=sp(20),
                bold=True
            )
            cancel_btn = PersianButton(
                text='بازگشت',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(55),
                color=(1, 1, 1, 1),
                font_size=sp(20),
                bold=True
            )
            
            btn_layout.add_widget(save_btn)
            btn_layout.add_widget(cancel_btn)
            content.add_widget(btn_layout)
            
            scroll.add_widget(content)
            main_container.add_widget(scroll)
            
            popup = PersianPopup(
                title='برگشتی',
                content=main_container,
                size_hint=(0.85, 0.8),
                auto_dismiss=False
            )
            
            save_btn.bind(on_press=lambda x: self._save_return_dialog(
                popup, return_quantity.text, self.return_amount_input.text, return_reason.text
            ))
            cancel_btn.bind(on_press=popup.dismiss)
            
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    
    def _save_return_dialog(self, popup, qty, amount, reason):
        """ذخیره اطلاعات برگشتی و رفتن به تسویه"""
        try:
            popup.dismiss()
            
            try:
                qty_int = int(qty) if qty else 0
                amount_float = float(amount.replace(',', '')) if amount else 0
            except:
                self.show_message('خطا', 'مقادیر وارد شده معتبر نیستند')
                return
            
            invoice_amount = self.temp_delivery_data.get('invoice_amount', 0)
            if amount_float > invoice_amount:
                self.show_message('خطا', 'مبلغ برگشتی نمی‌تواند از مبلغ فاکتور بیشتر باشد')
                return
            
            self.temp_delivery_data.update({
                'full_delivery': False,
                'returned_quantity': qty_int,
                'returned_amount': amount_float,
                'return_reason': reason
            })
            
            self.show_settlement_dialog()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    
    # ============================================================
    # دیالوگ تسویه فاکتور
    # ============================================================
    
    def show_settlement_dialog(self):
        """دیالوگ تسویه فاکتور با نمایش مبالغ به حروف"""
        try:
            from utils.persian_text import number_to_words
            
            invoice_amount = self.temp_delivery_data.get('invoice_amount', 0)
            returned_amount = self.temp_delivery_data.get('returned_amount', 0)
            base_amount = invoice_amount - returned_amount
            invoice_number = self.temp_delivery_data.get('invoice_number', '')
            customer_name = self.temp_delivery_data.get('customer_name', '')
            
            main_container = BoxLayout(orientation='vertical', spacing=dp(5))
            
            scroll = ScrollView(
                do_scroll_x=False,
                do_scroll_y=True,
                size_hint=(1, 1),
                scroll_type=['bars', 'content'],
                bar_width=dp(6)
            )
            
            content = BoxLayout(
                orientation='vertical',
                padding=dp(15),
                spacing=dp(6),
                size_hint_y=None
            )
            content.bind(minimum_height=content.setter('height'))
            
            # ============================================================
            # باکس اطلاعات فاکتور با نمایش مبالغ به حروف
            # ============================================================
            info_box = BoxLayout(
                orientation='vertical',
                size_hint_y=None,
                height=dp(240),
                padding=dp(12),
                spacing=dp(4)
            )
            with info_box.canvas.before:
                Color(0.1, 0.15, 0.2, 1)
                rect = Rectangle(pos=info_box.pos, size=info_box.size)
                info_box.bind(pos=lambda i, v: setattr(rect, 'pos', v),
                            size=lambda i, v: setattr(rect, 'size', v))
            
            info_box.add_widget(RTLLabel(
                text='اطلاعات فاکتور',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(22),
                bold=True,
                color=(1, 0.8, 0.2, 1)
            ))
            
            info_box.add_widget(RTLLabel(
                text=f'شماره فاکتور: {invoice_number}',
                size_hint_y=None,
                height=dp(25),
                font_size=sp(18),
                color=(1, 1, 1, 1),
                halign='right'
            ))
            
            info_box.add_widget(RTLLabel(
                text=f'مبلغ فاکتور: {invoice_amount:,.0f} ریال',
                size_hint_y=None,
                height=dp(25),
                font_size=sp(18),
                color=(1, 1, 1, 1),
                halign='right'
            ))
            
            invoice_words = number_to_words(invoice_amount)
            if invoice_words:
                info_box.add_widget(RTLLabel(
                    text=f'مبلغ فاکتور به حروف: {invoice_words}',
                    size_hint_y=None,
                    height=dp(25),
                    font_size=sp(14),
                    color=(0.6, 0.8, 1, 1),
                    halign='right'
                ))
            
            if returned_amount > 0:
                info_box.add_widget(RTLLabel(
                    text=f'مبلغ برگشتی: {returned_amount:,.0f} ریال',
                    size_hint_y=None,
                    height=dp(25),
                    font_size=sp(18),
                    color=(0.8, 0.2, 0.2, 1),
                    halign='right'
                ))
                return_words = number_to_words(returned_amount)
                if return_words:
                    info_box.add_widget(RTLLabel(
                        text=f'مبلغ برگشتی به حروف: {return_words}',
                        size_hint_y=None,
                        height=dp(25),
                        font_size=sp(14),
                        color=(0.8, 0.4, 0.4, 1),
                        halign='right'
                    ))
            
            info_box.add_widget(RTLLabel(
                text=f'مبلغ مانده خالص: {base_amount:,.0f} ریال',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(20),
                bold=True,
                color=(0.2, 0.8, 0.2, 1),
                halign='right'
            ))
            
            base_words = number_to_words(base_amount)
            if base_words:
                info_box.add_widget(RTLLabel(
                    text=f'مانده خالص به حروف: {base_words}',
                    size_hint_y=None,
                    height=dp(25),
                    font_size=sp(14),
                    color=(0.4, 0.9, 0.4, 1),
                    halign='right'
                ))
            
            content.add_widget(info_box)
            content.add_widget(Label(size_hint_y=None, height=dp(5)))
            
            # ============================================================
            # نحوه تسویه
            # ============================================================
            content.add_widget(RTLLabel(
                text='نحوه تسویه (چند انتخابی):',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(20),
                color=(1, 1, 1, 1)
            ))
            
            payment_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
            
            self.cash_btn = PersianButton(
                text='نقد',
                size_hint_x=0.33,
                size_hint_y=None,
                height=dp(45),
                background_color=(0.3, 0.3, 0.3, 1),
                color=(1, 1, 1, 1),
                font_size=sp(20)
            )
            self.cash_btn.bind(on_press=lambda x: self._toggle_payment_btn('نقد'))
            payment_layout.add_widget(self.cash_btn)
            
            self.check_pay_btn = PersianButton(
                text='چک',
                size_hint_x=0.33,
                size_hint_y=None,
                height=dp(45),
                background_color=(0.3, 0.3, 0.3, 1),
                color=(1, 1, 1, 1),
                font_size=sp(20)
            )
            self.check_pay_btn.bind(on_press=lambda x: self._toggle_payment_btn('چک'))
            payment_layout.add_widget(self.check_pay_btn)
            
            self.credit_btn = PersianButton(
                text='نسیه',
                size_hint_x=0.34,
                size_hint_y=None,
                height=dp(45),
                background_color=(0.3, 0.3, 0.3, 1),
                color=(1, 1, 1, 1),
                font_size=sp(20)
            )
            self.credit_btn.bind(on_press=lambda x: self._toggle_payment_btn('نسیه'))
            payment_layout.add_widget(self.credit_btn)
            
            content.add_widget(payment_layout)
            content.add_widget(Label(size_hint_y=None, height=dp(5)))
            
            # ============================================================
            # شرایط تسویه
            # ============================================================
            content.add_widget(RTLLabel(
                text='شرایط تسویه:',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(20),
                color=(1, 1, 1, 1)
            ))
            
            settlement_type = PersianComboBox(
                values=['تسویه کامل', 'تسویه بخشی از بدهی'],
                text='تسویه کامل',
                height=dp(55)
            )
            settlement_type.main_btn.background_color = (0.15, 0.15, 0.15, 1)
            settlement_type.main_btn.color = (1, 1, 1, 1)
            settlement_type.main_btn.font_size = sp(22)
            content.add_widget(settlement_type)
            content.add_widget(Label(size_hint_y=None, height=dp(5)))
            
            # ============================================================
            # فیلد 1: مانده بدهی فاکتور
            # ============================================================
            row1 = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(8))
            row1.add_widget(RTLLabel(
                text='1. مانده بدهی فاکتور:',
                size_hint_x=0.35,
                size_hint_y=None,
                height=dp(40),
                font_size=sp(18),
                color=(0.4, 0.7, 1, 1),
                halign='right'
            ))
            debt_label = RTLTextInput(
                text=f'{base_amount:,.0f} ریال',
                size_hint_x=0.65,
                size_hint_y=None,
                height=dp(40),
                font_size=sp(22),
                disabled=True
            )
            debt_label.bg_color = (0.1, 0.1, 0.1, 1)
            row1.add_widget(debt_label)
            content.add_widget(row1)
            
            # ============================================================
            # فیلد 2: درصد تخفیف نقدی
            # ============================================================
            row2 = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
            row2.add_widget(RTLLabel(
                text='2. درصد تخفیف نقدی:',
                size_hint_x=0.35,
                size_hint_y=None,
                height=dp(45),
                font_size=sp(18),
                color=(1, 1, 1, 1),
                halign='right'
            ))
            discount_percent = RTLTextInput(
                text='0',
                multiline=False,
                size_hint_x=0.65,
                size_hint_y=None,
                height=dp(45),
                font_size=sp(48),
                input_filter='float'
            )
            discount_percent.bg_color = (0.15, 0.15, 0.15, 1)
            row2.add_widget(discount_percent)
            content.add_widget(row2)
            
            # ============================================================
            # فیلد 3: سایر کسورات (درصد)
            # ============================================================
            row3 = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
            row3.add_widget(RTLLabel(
                text='3. سایر کسورات (درصد):',
                size_hint_x=0.35,
                size_hint_y=None,
                height=dp(45),
                font_size=sp(18),
                color=(1, 1, 1, 1),
                halign='right'
            ))
            other_deductions_percent = RTLTextInput(
                text='0',
                multiline=False,
                size_hint_x=0.65,
                size_hint_y=None,
                height=dp(45),
                font_size=sp(48),
                input_filter='float'
            )
            other_deductions_percent.bg_color = (0.15, 0.15, 0.15, 1)
            row3.add_widget(other_deductions_percent)
            content.add_widget(row3)
            
            # ============================================================
            # فیلد 4: سایر کسورات (ریال)
            # ============================================================
            row4 = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
            row4.add_widget(RTLLabel(
                text='4. سایر کسورات (ریال):',
                size_hint_x=0.35,
                size_hint_y=None,
                height=dp(45),
                font_size=sp(18),
                color=(1, 1, 1, 1),
                halign='right'
            ))
            other_deductions_amount = RTLTextInput(
                text='0',
                multiline=False,
                size_hint_x=0.65,
                size_hint_y=None,
                height=dp(45),
                font_size=sp(48),
                input_filter='float'
            )
            other_deductions_amount.bg_color = (0.15, 0.15, 0.15, 1)
            row4.add_widget(other_deductions_amount)
            content.add_widget(row4)
            
            # ============================================================
            # فیلد 5: توضیحات
            # ============================================================
            row5 = BoxLayout(size_hint_y=None, height=dp(70), spacing=dp(8))
            row5.add_widget(RTLLabel(
                text='5. توضیحات:',
                size_hint_x=0.35,
                size_hint_y=None,
                height=dp(65),
                font_size=sp(18),
                color=(1, 1, 1, 1),
                halign='right'
            ))
            description = RTLTextInput(
                multiline=True,
                size_hint_x=0.65,
                size_hint_y=None,
                height=dp(65),
                font_size=sp(48),
                hint_text='توضیحات اضافی (اختیاری)'
            )
            description.bg_color = (0.15, 0.15, 0.15, 1)
            row5.add_widget(description)
            content.add_widget(row5)
            
            # ============================================================
            # فیلد 6: مبلغ نقد دریافتی
            # ============================================================
            row6 = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
            row6.add_widget(RTLLabel(
                text='6. مبلغ نقد دریافتی (ریال):',
                size_hint_x=0.35,
                size_hint_y=None,
                height=dp(45),
                font_size=sp(18),
                color=(1, 1, 1, 1),
                halign='right'
            ))
            cash_amount = RTLTextInput(
                text='0',
                multiline=False,
                size_hint_x=0.65,
                size_hint_y=None,
                height=dp(45),
                font_size=sp(48),
                input_filter='float'
            )
            cash_amount.bg_color = (0.15, 0.15, 0.15, 1)
            row6.add_widget(cash_amount)
            content.add_widget(row6)
            
            # ============================================================
            # فیلد 7: مبلغ چک دریافتی
            # ============================================================
            row7 = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
            row7.add_widget(RTLLabel(
                text='7. مبلغ چک دریافتی (ریال):',
                size_hint_x=0.35,
                size_hint_y=None,
                height=dp(45),
                font_size=sp(18),
                color=(1, 1, 1, 1),
                halign='right'
            ))
            self.check_amount_display = RTLTextInput(
                text='0',
                size_hint_x=0.65,
                size_hint_y=None,
                height=dp(45),
                font_size=sp(48),
                disabled=True
            )
            self.check_amount_display.bg_color = (0.1, 0.1, 0.1, 1)
            row7.add_widget(self.check_amount_display)
            content.add_widget(row7)
            
            # ============================================================
            # فیلد 8: جمع کل مبلغ دریافتی
            # ============================================================
            row8 = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
            row8.add_widget(RTLLabel(
                text='8. جمع کل مبلغ دریافتی (ریال):',
                size_hint_x=0.35,
                size_hint_y=None,
                height=dp(45),
                font_size=sp(18),
                color=(1, 1, 1, 1),
                halign='right'
            ))
            self.total_received_display = RTLTextInput(
                text='0',
                size_hint_x=0.65,
                size_hint_y=None,
                height=dp(45),
                font_size=sp(48),
                disabled=True
            )
            self.total_received_display.bg_color = (0.1, 0.1, 0.1, 1)
            row8.add_widget(self.total_received_display)
            content.add_widget(row8)
            
            # ============================================================
            # فیلد 9: مبلغ مانده نهایی
            # ============================================================
            row9 = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
            row9.add_widget(RTLLabel(
                text='9. مبلغ مانده نهایی:',
                size_hint_x=0.35,
                size_hint_y=None,
                height=dp(45),
                font_size=sp(18),
                color=(0.4, 0.7, 1, 1),
                halign='right'
            ))
            self.remaining_label = RTLTextInput(
                text=f'{base_amount:,.0f} ریال',
                size_hint_x=0.65,
                size_hint_y=None,
                height=dp(45),
                font_size=sp(48),
                disabled=True
            )
            self.remaining_label.bg_color = (0.1, 0.1, 0.1, 1)
            row9.add_widget(self.remaining_label)
            content.add_widget(row9)
            
            # ============================================================
            # نمایش مبلغ مانده نهایی به حروف
            # ============================================================
            remaining_words_label = RTLLabel(
                text='',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(16),
                color=(0.4, 0.9, 0.4, 1),
                halign='right'
            )
            content.add_widget(remaining_words_label)
            
            content.add_widget(Label(size_hint_y=None, height=dp(5)))
            
            # ============================================================
            # دکمه‌ها
            # ============================================================
            btn_layout = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(10))
            
            self.check_register_btn = PersianButton(
                text='ثبت چک',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(55),
                color=(0.5, 0.5, 0.5, 1),
                font_size=sp(20),
                disabled=True
            )
            self.check_register_btn.bind(
                on_press=lambda x: self.show_check_dialog(
                    content, cash_amount, self.check_amount_display, 
                    self.total_received_display, self.remaining_label
                )
            )
            
            save_btn = PersianButton(
                text='ثبت',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(55),
                color=(1, 1, 1, 1),
                font_size=sp(20)
            )
            self.save_btn = save_btn
            
            cancel_btn = PersianButton(
                text='انصراف',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(55),
                color=(1, 1, 1, 1),
                font_size=sp(20)
            )
            
            btn_layout.add_widget(self.check_register_btn)
            btn_layout.add_widget(save_btn)
            btn_layout.add_widget(cancel_btn)
            content.add_widget(btn_layout)
            
            # ============================================================
            # ذخیره ویجت‌ها
            # ============================================================
            self._settlement_widgets = {
                'settlement_type': settlement_type,
                'discount_percent': discount_percent,
                'other_deductions_percent': other_deductions_percent,
                'other_deductions_amount': other_deductions_amount,
                'cash_amount': cash_amount,
                'debt_label': debt_label,
                'base_amount': base_amount,
                'invoice_amount': invoice_amount,
                'returned_amount': returned_amount,
                'invoice_number': invoice_number,
                'customer_name': customer_name,
                'remaining_words_label': remaining_words_label
            }
            
            scroll.add_widget(content)
            main_container.add_widget(scroll)
            
            self._update_field_states()
            self._settlement_type_last = settlement_type.text
            Clock.schedule_interval(self._check_settlement_type_change, 0.3)
            
            popup = PersianPopup(
                title='تسویه فاکتور',
                content=main_container,
                size_hint=(0.92, 0.88),
                auto_dismiss=False
            )
            
            save_btn.bind(on_press=lambda x: self._finalize_settlement(
                popup, settlement_type, discount_percent,
                other_deductions_percent, other_deductions_amount,
                cash_amount, self.check_amount_display, self.total_received_display,
                description, self.remaining_label
            ))
            cancel_btn.bind(on_press=popup.dismiss)
            
            popup.open()
            
            Clock.schedule_once(lambda dt: self._update_settlement_calculations(), 0.5)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    
    def _toggle_payment_btn(self, method):
        """تغییر وضعیت دکمه روش پرداخت"""
        try:
            self.payment_methods[method] = not self.payment_methods[method]
            
            if method == 'نقد':
                if self.payment_methods[method]:
                    self.cash_btn.background_color = (0.2, 0.6, 0.2, 1)
                else:
                    self.cash_btn.background_color = (0.3, 0.3, 0.3, 1)
            elif method == 'چک':
                if self.payment_methods[method]:
                    self.check_pay_btn.background_color = (0.2, 0.6, 0.2, 1)
                    self.check_register_btn.disabled = False
                    self.check_register_btn.background_color = (0.2, 0.4, 0.8, 1)
                    self.check_register_btn.color = (1, 1, 1, 1)
                else:
                    self.check_pay_btn.background_color = (0.3, 0.3, 0.3, 1)
                    self.check_register_btn.disabled = True
                    self.check_register_btn.background_color = (0.3, 0.3, 0.3, 1)
                    self.check_register_btn.color = (0.5, 0.5, 0.5, 1)
            elif method == 'نسیه':
                if self.payment_methods[method]:
                    self.credit_btn.background_color = (0.2, 0.6, 0.2, 1)
                else:
                    self.credit_btn.background_color = (0.3, 0.3, 0.3, 1)
            
            self._update_field_states()
            self._update_settlement_calculations()
            self._update_save_button_state()
            
        except Exception as e:
            print(f"خطا در تغییر وضعیت روش پرداخت: {e}")
    
    def _update_field_states(self):
        """بروزرسانی وضعیت فعال/غیرفعال فیلدها بر اساس حالت تسویه"""
        try:
            if not hasattr(self, '_settlement_widgets'):
                return
            
            settlement_type = self._settlement_widgets['settlement_type'].text
            is_cash = self.payment_methods.get('نقد', False)
            is_credit = self.payment_methods.get('نسیه', False)
            is_full = settlement_type == 'تسویه کامل'
            
            discount_input = self._settlement_widgets['discount_percent']._hidden_input
            if is_cash and is_full:
                discount_input.disabled = False
            else:
                discount_input.disabled = True
                self._settlement_widgets['discount_percent'].text = '0'
            
            other_percent_input = self._settlement_widgets['other_deductions_percent']._hidden_input
            if is_credit:
                other_percent_input.disabled = True
                self._settlement_widgets['other_deductions_percent'].text = '0'
            else:
                other_percent_input.disabled = False
            
            self._settlement_widgets['other_deductions_amount']._hidden_input.disabled = False
            
            cash_input = self._settlement_widgets['cash_amount']._hidden_input
            if is_full:
                cash_input.disabled = True
            else:
                cash_input.disabled = False
            
            if hasattr(self, 'check_register_btn'):
                if self.payment_methods.get('چک', False):
                    self.check_register_btn.disabled = False
                    self.check_register_btn.background_color = (0.2, 0.4, 0.8, 1)
                    self.check_register_btn.color = (1, 1, 1, 1)
                else:
                    self.check_register_btn.disabled = True
                    self.check_register_btn.background_color = (0.3, 0.3, 0.3, 1)
                    self.check_register_btn.color = (0.5, 0.5, 0.5, 1)
            
            self._update_save_button_state()
            
        except Exception as e:
            print(f"خطا در بروزرسانی وضعیت فیلدها: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_save_button_state(self):
        """بروزرسانی وضعیت دکمه ثبت بر اساس شرایط"""
        try:
            if not hasattr(self, 'save_btn'):
                return
            
            if not hasattr(self, '_settlement_widgets'):
                return
            
            settlement_type = self._settlement_widgets['settlement_type'].text
            is_full = settlement_type == 'تسویه کامل'
            
            if is_full:
                try:
                    cash_str = self._settlement_widgets['cash_amount'].text.replace(',', '').strip()
                    cash = float(cash_str) if cash_str else 0
                except:
                    cash = 0
                
                if cash > 0:
                    self.save_btn.disabled = False
                    self.save_btn.background_color = (0.2, 0.7, 0.2, 1)
                    self.save_btn.color = (1, 1, 1, 1)
                else:
                    self.save_btn.disabled = True
                    self.save_btn.background_color = (0.3, 0.3, 0.3, 1)
                    self.save_btn.color = (0.5, 0.5, 0.5, 1)
            else:
                self.save_btn.disabled = False
                self.save_btn.background_color = (0.2, 0.7, 0.2, 1)
                self.save_btn.color = (1, 1, 1, 1)
                
        except Exception as e:
            print(f"خطا در بروزرسانی وضعیت دکمه ثبت: {e}")
    
    def _check_settlement_type_change(self, dt):
        """بررسی تغییر شرایط تسویه با تایمر"""
        try:
            if hasattr(self, '_settlement_widgets') and 'settlement_type' in self._settlement_widgets:
                current = self._settlement_widgets['settlement_type'].text
                if current != self._settlement_type_last:
                    self._settlement_type_last = current
                    self._update_field_states()
                    self._update_settlement_calculations()
                    self._update_save_button_state()
        except Exception as e:
            print(f"خطا در بررسی تغییر شرایط تسویه: {e}")
    
    def _update_settlement_calculations(self):
        """بروزرسانی محاسبات تسویه با به‌روزرسانی مبلغ به حروف"""
        try:
            from utils.persian_text import number_to_words
            
            if not hasattr(self, '_settlement_widgets'):
                print("_settlement_widgets وجود ندارد!")
                return
            
            base_amount = self._settlement_widgets.get('base_amount', 0)
            settlement_type = self._settlement_widgets['settlement_type'].text
            is_cash = self.payment_methods.get('نقد', False)
            is_credit = self.payment_methods.get('نسیه', False)
            
            try:
                discount_str = self._settlement_widgets['discount_percent'].text.replace(',', '').strip()
                discount = float(discount_str) if discount_str else 0
            except:
                discount = 0
            
            try:
                other_percent_str = self._settlement_widgets['other_deductions_percent'].text.replace(',', '').strip()
                other_percent = float(other_percent_str) if other_percent_str else 0
            except:
                other_percent = 0
            
            try:
                other_amount_str = self._settlement_widgets['other_deductions_amount'].text.replace(',', '').strip()
                other_amount = float(other_amount_str) if other_amount_str else 0
            except:
                other_amount = 0
            
            try:
                cash_str = self._settlement_widgets['cash_amount'].text.replace(',', '').strip()
                cash = float(cash_str) if cash_str else 0
            except:
                cash = 0
            
            total_check = sum([c.get('amount', 0) for c in self.temp_checks])
            
            if discount > 7:
                self._show_discount_warning('سقف تخفیف نقدی ۷ درصد می باشد')
                self._settlement_widgets['discount_percent'].text = '7'
                discount = 7
            elif discount < 0:
                self._settlement_widgets['discount_percent'].text = '0'
                discount = 0
            
            if other_percent > 3:
                self._show_discount_warning('سقف سایر کسورات درصدی ۳ درصد می باشد')
                self._settlement_widgets['other_deductions_percent'].text = '3'
                other_percent = 3
            elif other_percent < 0:
                self._settlement_widgets['other_deductions_percent'].text = '0'
                other_percent = 0
            
            if other_amount < 0:
                self._settlement_widgets['other_deductions_amount'].text = '0'
                other_amount = 0
            
            if cash < 0:
                self._settlement_widgets['cash_amount'].text = '0'
                cash = 0
            
            if is_cash and settlement_type == 'تسویه کامل':
                discount_amount = base_amount * (discount / 100)
            else:
                discount_amount = 0
                if not (is_cash and settlement_type == 'تسویه کامل'):
                    self._settlement_widgets['discount_percent'].text = '0'
            
            if is_credit:
                other_percent_amount = 0
                self._settlement_widgets['other_deductions_percent'].text = '0'
            else:
                other_percent_amount = base_amount * (other_percent / 100)
            
            if other_amount > 0 and not self._amount_warning_shown:
                self._show_amount_warning()
                if self._warning_response is False:
                    self._settlement_widgets['other_deductions_amount'].text = '0'
                    other_amount = 0
                    self._warning_response = None
                elif self._warning_response is True:
                    self._warning_response = None
                else:
                    return
            
            total_deductions = discount_amount + other_percent_amount + other_amount
            
            if settlement_type == 'تسویه کامل':
                calculated_cash = base_amount - total_deductions - total_check
                
                if calculated_cash < 0:
                    self.show_message('هشدار', 'مبلغ چک‌ها بیشتر از مبلغ قابل پرداخت است')
                    self._settlement_widgets['cash_amount'].text = '0'
                    cash = 0
                else:
                    self._settlement_widgets['cash_amount'].text = f'{calculated_cash:,.0f}'
                    cash = calculated_cash
            else:
                try:
                    cash_str = self._settlement_widgets['cash_amount'].text.replace(',', '').strip()
                    cash = float(cash_str) if cash_str else 0
                except:
                    cash = 0
            
            total_received = cash + total_check
            final_remaining = base_amount - total_deductions - total_received
            
            if hasattr(self, 'check_amount_display'):
                self.check_amount_display.text = f'{total_check:,.0f}'
                print(f"check_amount_display.text updated to: {total_check:,.0f}")
            
            if hasattr(self, 'total_received_display'):
                self.total_received_display.text = f'{total_received:,.0f}'
                print(f"total_received_display.text updated to: {total_received:,.0f}")
            
            if hasattr(self, 'remaining_label'):
                self.remaining_label.text = f'{final_remaining:,.0f} ریال'
                print(f"remaining_label.text updated to: {final_remaining:,.0f}")
                
                if 'remaining_words_label' in self._settlement_widgets:
                    words_label = self._settlement_widgets['remaining_words_label']
                    if words_label:
                        if final_remaining != 0:
                            words = number_to_words(abs(final_remaining))
                            if final_remaining < 0:
                                words = 'منفی ' + words if words else ''
                            if words:
                                words_label.text = f'مانده نهایی به حروف: {words}'
                            else:
                                words_label.text = ''
                        else:
                            words_label.text = 'مانده نهایی به حروف: صفر'
            
            debt_widget = self._settlement_widgets.get('debt_label')
            if debt_widget:
                net_amount = base_amount - total_deductions
                debt_widget.text = f'{net_amount:,.0f} ریال'
                print(f"debt_label.text updated to: {net_amount:,.0f}")
            
            self._update_field_states()
            self._update_save_button_state()
            
        except Exception as e:
            print(f"خطا در بروزرسانی محاسبات تسویه: {e}")
            import traceback
            traceback.print_exc()
    
    def _show_discount_warning(self, message):
        """نمایش هشدار تخفیف به صورت Message Box"""
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            content.add_widget(RTLLabel(
                text=message,
                size_hint_y=None,
                height=dp(60),
                font_size=sp(20),
                color=(1, 0.8, 0.2, 1)
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
                title='هشدار',
                content=content,
                size_hint=(0.85, 0.35),
                auto_dismiss=True
            )
            btn.bind(on_press=popup.dismiss)
            popup.open()
            
        except Exception as e:
            print(f"خطا در نمایش هشدار تخفیف: {e}")
    
    def _show_amount_warning(self):
        """نمایش هشدار تخفیف مازاد به صورت Message Box با تأیید (فقط یک بار)"""
        try:
            if self._amount_warning_shown:
                return
            
            self._amount_warning_shown = True
            
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            content.add_widget(RTLLabel(
                text='در صورت اعمال تخفیف مازاد امکان عدم محاسبه توسط حسابداری وجود دارد،\nآیا ادامه میدهید؟',
                size_hint_y=None,
                height=dp(80),
                font_size=sp(20),
                color=(1, 0.8, 0.2, 1)
            ))
            
            btn_layout = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(10))
            yes_btn = PersianButton(
                text='بله',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            no_btn = PersianButton(
                text='خیر',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            btn_layout.add_widget(yes_btn)
            btn_layout.add_widget(no_btn)
            content.add_widget(btn_layout)
            
            popup = PersianPopup(
                title='هشدار',
                content=content,
                size_hint=(0.85, 0.4),
                auto_dismiss=False
            )
            
            self._warning_response = None
            
            def on_yes(instance):
                self._warning_response = True
                popup.dismiss()
                self._update_settlement_calculations()
            
            def on_no(instance):
                self._warning_response = False
                popup.dismiss()
                self._settlement_widgets['other_deductions_amount'].text = '0'
                self._update_settlement_calculations()
            
            yes_btn.bind(on_press=on_yes)
            no_btn.bind(on_press=on_no)
            popup.open()
            
        except Exception as e:
            print(f"خطا در نمایش هشدار مبلغ: {e}")
            self._amount_warning_shown = False
    
    # ============================================================
    # دیالوگ ثبت چک
    # ============================================================
    
    def show_check_dialog(self, parent_popup, cash_input, check_display, total_received_label, remaining_label):
        """دیالوگ جزئیات چک"""
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            
            content.add_widget(RTLLabel(
                text='تعداد چک دریافتی:',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(18),
                color=(1, 1, 1, 1)
            ))
            
            check_count = RTLTextInput(
                text='1',
                multiline=False,
                size_hint_y=None,
                height=dp(55),
                font_size=sp(48),
                input_filter='int'
            )
            check_count.bg_color = (0.15, 0.15, 0.15, 1)
            content.add_widget(check_count)
            
            btn_layout = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(10))
            
            next_btn = PersianButton(
                text='ادامه',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            cancel_btn = PersianButton(
                text='انصراف',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            
            btn_layout.add_widget(next_btn)
            btn_layout.add_widget(cancel_btn)
            content.add_widget(btn_layout)
            
            popup = PersianPopup(
                title='تعداد چک',
                content=content,
                size_hint=(0.8, 0.35),
                auto_dismiss=False
            )
            
            next_btn.bind(on_press=lambda x: self._start_check_registration(
                popup, check_count.text, parent_popup, cash_input, check_display, total_received_label, remaining_label
            ))
            cancel_btn.bind(on_press=popup.dismiss)
            
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    
    def _start_check_registration(self, popup, count_str, parent_popup, cash_input, check_display, total_received_label, remaining_label):
        """شروع ثبت چک‌ها"""
        try:
            popup.dismiss()
            
            try:
                count = int(count_str)
                if count < 1:
                    self.show_message('خطا', 'تعداد چک باید حداقل ۱ باشد')
                    return
            except:
                self.show_message('خطا', 'تعداد چک معتبر نیست')
                return
            
            self.temp_checks = []
            self._register_check(0, count, parent_popup, cash_input, check_display, total_received_label, remaining_label)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    
    def _register_check(self, index, total, parent_popup, cash_input, check_display, total_received_label, remaining_label):
        """ثبت یک چک"""
        try:
            if index >= total:
                self._show_check_summary(parent_popup, cash_input, check_display, total_received_label, remaining_label)
                return
            
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(12))
            
            content.add_widget(RTLLabel(
                text=f'چک {index + 1} از {total}',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(22),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))
            
            content.add_widget(RTLLabel(
                text='مبلغ چک (ریال):',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))
            check_amount = RTLTextInput(
                multiline=False,
                size_hint_y=None,
                height=dp(55),
                font_size=sp(48),
                hint_text='مبلغ',
                input_filter='float'
            )
            check_amount.bg_color = (0.15, 0.15, 0.15, 1)
            content.add_widget(check_amount)
            
            content.add_widget(RTLLabel(
                text='تاریخ چک:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))
            check_date = RTLTextInput(
                text=get_today_jalali(),
                multiline=False,
                size_hint_y=None,
                height=dp(55),
                font_size=sp(48)
            )
            check_date.bg_color = (0.15, 0.15, 0.15, 1)
            content.add_widget(check_date)
            
            content.add_widget(RTLLabel(
                text='وضعیت ثبت صیادی:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))
            sayadi_status = PersianComboBox(
                values=['ثبت شده', 'ثبت نشده'],
                text='ثبت شده',
                height=dp(50)
            )
            sayadi_status.main_btn.background_color = (0.15, 0.15, 0.15, 1)
            sayadi_status.main_btn.color = (1, 1, 1, 1)
            sayadi_status.main_btn.font_size = sp(20)
            content.add_widget(sayadi_status)
            
            btn_layout = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(10))
            
            save_btn = PersianButton(
                text='ثبت',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            cancel_btn = PersianButton(
                text='انصراف',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            
            btn_layout.add_widget(save_btn)
            btn_layout.add_widget(cancel_btn)
            content.add_widget(btn_layout)
            
            popup = PersianPopup(
                title='ثبت چک',
                content=content,
                size_hint=(0.85, 0.6),
                auto_dismiss=False
            )
            
            save_btn.bind(on_press=lambda x: self._save_check(
                popup, index, total, check_amount.text, check_date.text,
                sayadi_status.text, parent_popup, cash_input, check_display, total_received_label, remaining_label
            ))
            cancel_btn.bind(on_press=lambda x: self._cancel_check_registration(popup))
            
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    
    def _save_check(self, popup, index, total, amount, date, status, parent_popup, cash_input, check_display, total_received_label, remaining_label):
        """ذخیره یک چک و رفتن به چک بعدی"""
        try:
            popup.dismiss()
            
            try:
                amount_float = float(amount.replace(',', '')) if amount else 0
                if amount_float <= 0:
                    self.show_message('خطا', 'مبلغ چک باید بیشتر از صفر باشد')
                    return
            except:
                self.show_message('خطا', 'مبلغ چک معتبر نیست')
                return
            
            if status == 'ثبت نشده':
                confirm_content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
                confirm_content.add_widget(RTLLabel(
                    text='گرفتن چک ثبت نشده مجاز نیست و شامل جریمه خواهد بود،\nآیا ادامه می‌دهید؟',
                    size_hint_y=None,
                    height=dp(70),
                    font_size=sp(20),
                    color=(1, 0.8, 0.2, 1)
                ))
                
                btn_layout = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(10))
                yes_btn = PersianButton(text='بله', background_color=(0.2, 0.7, 0.2, 1), size_hint_y=None, height=dp(50), color=(1,1,1,1), font_size=sp(18))
                no_btn = PersianButton(text='خیر', background_color=(0.8, 0.2, 0.2, 1), size_hint_y=None, height=dp(50), color=(1,1,1,1), font_size=sp(18))
                btn_layout.add_widget(yes_btn)
                btn_layout.add_widget(no_btn)
                confirm_content.add_widget(btn_layout)
                
                confirm_popup = PersianPopup(
                    title='تأیید',
                    content=confirm_content,
                    size_hint=(0.8, 0.4),
                    auto_dismiss=False
                )
                
                yes_btn.bind(on_press=lambda x: self._continue_check_registration(
                    confirm_popup, index, total, amount_float, date, status,
                    parent_popup, cash_input, check_display, total_received_label, remaining_label
                ))
                no_btn.bind(on_press=confirm_popup.dismiss)
                
                confirm_popup.open()
                return
            
            self._continue_check_registration(None, index, total, amount_float, date, status,
                                             parent_popup, cash_input, check_display, total_received_label, remaining_label)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)

    def _continue_check_registration(self, confirm_popup, index, total, amount, date, status,
                                    parent_popup, cash_input, check_display, total_received_label, remaining_label):
        """ادامه ثبت چک بعد از تأیید"""
        try:
            if confirm_popup:
                confirm_popup.dismiss()
            
            self.temp_checks.append({
                'amount': amount,
                'date': date,
                'sayadi_status': status
            })
            
            self._update_settlement_calculations()
            
            self._register_check(index + 1, total, parent_popup, cash_input, check_display, total_received_label, remaining_label)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    
    def _cancel_check_registration(self, popup):
        """انصراف از ثبت چک"""
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            content.add_widget(RTLLabel(
                text='آیا از انصراف از ثبت چک اطمینان دارید؟',
                size_hint_y=None,
                height=dp(55),
                font_size=sp(20),
                color=(1, 1, 1, 1)
            ))
            
            btn_layout = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(10))
            yes_btn = PersianButton(text='بله', background_color=(0.8, 0.2, 0.2, 1), size_hint_y=None, height=dp(50), color=(1,1,1,1), font_size=sp(18))
            no_btn = PersianButton(text='خیر', background_color=(0.2, 0.7, 0.2, 1), size_hint_y=None, height=dp(50), color=(1,1,1,1), font_size=sp(18))
            btn_layout.add_widget(yes_btn)
            btn_layout.add_widget(no_btn)
            content.add_widget(btn_layout)
            
            confirm_popup = PersianPopup(
                title='تأیید انصراف',
                content=content,
                size_hint=(0.8, 0.35),
                auto_dismiss=False
            )
            
            yes_btn.bind(on_press=lambda x: self._confirm_cancel_check(popup, confirm_popup))
            no_btn.bind(on_press=confirm_popup.dismiss)
            
            confirm_popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)

    def _confirm_cancel_check(self, popup, confirm_popup):
        """تأیید انصراف از ثبت چک"""
        try:
            confirm_popup.dismiss()
            popup.dismiss()
            self.temp_checks = []
            self._update_settlement_calculations()
            self.show_message('اطلاع', 'ثبت چک لغو شد')
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    
    def _show_check_summary(self, parent_popup, cash_input, check_display, total_received_label, remaining_label):
        """نمایش خلاصه چک‌ها"""
        try:
            total_check_amount = sum([c['amount'] for c in self.temp_checks])
            
            invoice_amount = self.temp_delivery_data.get('invoice_amount', 0)
            returned_amount = self.temp_delivery_data.get('returned_amount', 0)
            base_amount = invoice_amount - returned_amount
            
            if total_check_amount > base_amount:
                content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
                content.add_widget(RTLLabel(
                    text=f'جمع مبالغ دریافتی ({total_check_amount:,.0f}) بیشتر از مبلغ فاکتور ({base_amount:,.0f}) است،\nادامه می‌دهید؟',
                    size_hint_y=None,
                    height=dp(70),
                    font_size=sp(20),
                    color=(1, 0.8, 0.2, 1)
                ))
                
                btn_layout = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(10))
                yes_btn = PersianButton(text='بله', background_color=(0.2, 0.7, 0.2, 1), size_hint_y=None, height=dp(50), color=(1,1,1,1), font_size=sp(18))
                no_btn = PersianButton(text='خیر', background_color=(0.8, 0.2, 0.2, 1), size_hint_y=None, height=dp(50), color=(1,1,1,1), font_size=sp(18))
                btn_layout.add_widget(yes_btn)
                btn_layout.add_widget(no_btn)
                content.add_widget(btn_layout)
                
                confirm_popup = PersianPopup(
                    title='تأیید',
                    content=content,
                    size_hint=(0.85, 0.4),
                    auto_dismiss=False
                )
                
                yes_btn.bind(on_press=lambda x: self._show_final_check_summary(
                    confirm_popup, parent_popup, cash_input, check_display, total_received_label, remaining_label
                ))
                no_btn.bind(on_press=confirm_popup.dismiss)
                
                confirm_popup.open()
                return
            
            self._show_final_check_summary(None, parent_popup, cash_input, check_display, total_received_label, remaining_label)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    
    def _show_final_check_summary(self, confirm_popup, parent_popup, cash_input, check_display, total_received_label, remaining_label):
        """نمایش نهایی چک‌ها"""
        try:
            if confirm_popup:
                confirm_popup.dismiss()
            
            total_check_amount = sum([c['amount'] for c in self.temp_checks])
            
            content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
            
            content.add_widget(RTLLabel(
                text='خلاصه چک‌ها',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(22),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))
            
            for i, check in enumerate(self.temp_checks):
                content.add_widget(RTLLabel(
                    text=f'{i+1}. مبلغ: {check["amount"]:,.0f} | تاریخ: {check["date"]} | وضعیت: {check["sayadi_status"]}',
                    size_hint_y=None,
                    height=dp(28),
                    font_size=sp(16),
                    color=(1, 1, 1, 1)
                ))
            
            content.add_widget(RTLLabel(
                text=f'جمع کل: {total_check_amount:,.0f} ریال',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(20),
                bold=True,
                color=(0.2, 0.8, 0.2, 1)
            ))
            
            btn_layout = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(10))
            
            confirm_btn = PersianButton(
                text='تأیید',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            edit_btn = PersianButton(
                text='اصلاح',
                background_color=(0.8, 0.5, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            
            btn_layout.add_widget(confirm_btn)
            btn_layout.add_widget(edit_btn)
            content.add_widget(btn_layout)
            
            popup = PersianPopup(
                title='خلاصه چک‌ها',
                content=content,
                size_hint=(0.85, 0.5),
                auto_dismiss=False
            )
            
            confirm_btn.bind(on_press=lambda x: self._finalize_checks(
                popup, parent_popup, cash_input, check_display, total_received_label, remaining_label
            ))
            edit_btn.bind(on_press=lambda x: self._edit_checks(popup, parent_popup))
            
            popup.bind(on_dismiss=lambda x: self._update_settlement_calculations())
            
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    
    def _finalize_checks(self, popup, parent_popup, cash_input, check_display, total_received_label, remaining_label):
        """نهایی کردن چک‌ها و بازگشت به تسویه"""
        try:
            popup.dismiss()
            
            total_check_amount = sum([c['amount'] for c in self.temp_checks])
            
            if check_display:
                check_display.text = f'{total_check_amount:,.0f}'
            
            self._update_settlement_calculations()
            
            self.show_message('موفق', f'{len(self.temp_checks)} چک با موفقیت ثبت شد')
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    
    def _edit_checks(self, popup, parent_popup):
        """اصلاح چک‌ها"""
        try:
            popup.dismiss()
            self.temp_checks = []
            self._update_settlement_calculations()
            self.show_message('اطلاع', 'لطفاً مجدداً چک‌ها را وارد کنید')
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    
    # ============================================================
    # ثبت نهایی
    # ============================================================
    
    def _finalize_settlement(self, popup, settlement_type, discount_percent,
                            other_deductions_percent, other_deductions_amount,
                            cash_input, check_display, total_received_label,
                            description, remaining_label):
        """نهایی‌سازی تسویه و نمایش تأیید نهایی"""
        try:
            popup.dismiss()
            
            try:
                Clock.unschedule(self._check_settlement_type_change)
            except:
                pass
            
            settle_type = settlement_type.text
            discount_str = discount_percent.text.replace(',', '').strip()
            other_percent_str = other_deductions_percent.text.replace(',', '').strip()
            other_amount_str = other_deductions_amount.text.replace(',', '').strip()
            
            try:
                discount = float(discount_str) if discount_str else 0
                other_percent = float(other_percent_str) if other_percent_str else 0
                other_amount = float(other_amount_str) if other_amount_str else 0
            except:
                self.show_message('خطا', 'مقادیر وارد شده معتبر نیستند')
                return
            
            invoice_amount = self.temp_delivery_data.get('invoice_amount', 0)
            returned_amount = self.temp_delivery_data.get('returned_amount', 0)
            base_amount = invoice_amount - returned_amount
            customer_name = self.temp_delivery_data.get('customer_name', '')
            invoice_number = self.temp_delivery_data.get('invoice_number', '')
            is_cash = self.payment_methods.get('نقد', False)
            
            if is_cash and settle_type == 'تسویه کامل':
                discount_amount = base_amount * (discount / 100)
            else:
                discount_amount = 0
            
            other_deductions_total = base_amount * (other_percent / 100) + other_amount
            net_amount = base_amount - discount_amount - other_deductions_total
            
            try:
                cash_str = cash_input.text.replace(',', '').strip()
                cash = float(cash_str) if cash_str else 0
            except:
                cash = 0
            
            try:
                check_str = check_display.text.replace(',', '').strip()
                total_check = float(check_str) if check_str else 0
            except:
                total_check = 0
            
            total_received = cash + total_check
            final_remaining = net_amount - total_received
            
            if final_remaining < 0:
                self.show_message('خطا', 'مبلغ دریافتی بیشتر از مبلغ فاکتور است')
                return
            
            confirm_content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            
            confirm_content.add_widget(RTLLabel(
                text=f'آیا از ثبت نهایی توزیع به نام {customer_name} و فاکتور {invoice_number} اطمینان دارید؟',
                size_hint_y=None,
                height=dp(60),
                font_size=sp(22),
                color=(1, 1, 1, 1)
            ))
            
            btn_layout = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(10))
            
            yes_btn = PersianButton(
                text='بله',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(20)
            )
            no_btn = PersianButton(
                text='خیر',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(20)
            )
            
            btn_layout.add_widget(yes_btn)
            btn_layout.add_widget(no_btn)
            confirm_content.add_widget(btn_layout)
            
            confirm_popup = PersianPopup(
                title='تأیید نهایی',
                content=confirm_content,
                size_hint=(0.85, 0.4),
                auto_dismiss=False
            )
            
            yes_btn.bind(on_press=lambda x: self._show_final_summary(
                confirm_popup, settle_type, discount, discount_amount,
                other_percent, other_amount, other_deductions_total,
                cash, total_check, total_received, final_remaining,
                description.text, customer_name, invoice_number,
                invoice_amount, returned_amount, base_amount
            ))
            no_btn.bind(on_press=confirm_popup.dismiss)
            
            confirm_popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    
    def _show_final_summary(self, confirm_popup, settle_type, discount, discount_amount,
                            other_percent, other_amount, other_deductions_total,
                            cash, total_check, total_received, final_remaining,
                            description, customer_name, invoice_number,
                            invoice_amount, returned_amount, base_amount):
        """نمایش خلاصه نهایی عملیات"""
        try:
            confirm_popup.dismiss()
            
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
            
            content.add_widget(RTLLabel(
                text='خلاصه عملیات توزیع',
                size_hint_y=None,
                height=dp(50),
                font_size=sp(28),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))
            
            # ============================================================
            # فقط فیلدهای لازم - حذف فیلدهای اضافی
            # ============================================================
            summary_text = f"""
مشتری: {customer_name}
شماره فاکتور: {invoice_number}
─────────────────
مبلغ فاکتور: {invoice_amount:,.0f} ریال
مبلغ برگشتی: {returned_amount:,.0f} ریال
─────────────────
درصد تخفیف نقدی: {discount}%
مبلغ تخفیف: {discount_amount:,.0f} ریال
سایر کسورات (درصد): {other_percent}%
سایر کسورات (ریال): {other_amount:,.0f} ریال
─────────────────
مبلغ نقد دریافتی: {cash:,.0f} ریال
مبلغ چک دریافتی: {total_check:,.0f} ریال
─────────────────
جمع کل دریافتی: {total_received:,.0f} ریال
مانده نهایی: {final_remaining:,.0f} ریال
            """
            
            summary_label = PersianLabel(
                text=summary_text,
                size_hint_y=None,
                height=dp(380),
                font_size=sp(24),
                color=(1, 1, 1, 255),
                halign='right',
                valign='top'
            )
            summary_label.text_size = (dp(500), None)
            content.add_widget(summary_label)
            
            close_btn = PersianButton(
                text='بستن',
                background_color=(0.2, 0.6, 1, 1),
                size_hint_y=None,
                height=dp(55),
                color=(1, 1, 1, 1),
                font_size=sp(22)
            )
            content.add_widget(close_btn)
            
            final_popup = PersianPopup(
                title='عملیات موفق',
                content=content,
                size_hint=(0.92, 0.82),
                auto_dismiss=False
            )
            
            close_btn.bind(on_press=lambda x: self._save_and_close(final_popup, 
                settle_type, discount, discount_amount, other_percent, 
                other_amount, other_deductions_total, cash, total_check, 
                total_received, final_remaining, description
            ))
            
            final_popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    
    def _save_and_close(self, popup, settle_type, discount, discount_amount,
                        other_percent, other_amount, other_deductions_total,
                        cash, total_check, total_received, final_remaining, description):
        """ذخیره نهایی و بستن"""
        try:
            data = {
                'agent_name': '',
                'distributor_name': 'موزع',
                'route': self.current_route,
                'customer_name': self.temp_delivery_data.get('customer_name', ''),
                'customer_id': '',
                'invoice_number': self.temp_delivery_data.get('invoice_number', ''),
                'invoice_amount': self.temp_delivery_data.get('invoice_amount', 0),
                'delivery_status': 'موفق',
                'full_delivery': self.temp_delivery_data.get('full_delivery', True),
                'returned_quantity': self.temp_delivery_data.get('returned_quantity', 0),
                'returned_amount': self.temp_delivery_data.get('returned_amount', 0),
                'return_reason': self.temp_delivery_data.get('return_reason', None),
                'payment_method': 'ترکیبی',
                'settlement_type': settle_type,
                'discount_percent': discount,
                'discount_amount': discount_amount,
                'other_deductions_percent': other_percent,
                'other_deductions_amount': other_amount,
                'other_deductions_total': other_deductions_total,
                'cash_amount': cash,
                'check_amount': total_check,
                'total_received': total_received,
                'remaining_amount': final_remaining,
                'checks': self.temp_checks.copy(),
                'description': description
            }
            
            success, message, _ = save_delivery(data)
            
            if success:
                popup.dismiss()
                self.show_message('موفق', 'توزیع با موفقیت ثبت شد')
                
                self.temp_delivery_data = {}
                self.temp_checks = []
                self.selected_customer_label.text = 'مشتری انتخاب شده: هیچ'
                self.selected_customer_label.color = (0.5, 0.5, 0.5, 1)
                if hasattr(self, '_settlement_widgets'):
                    self._settlement_widgets = {}
                self.payment_methods = {
                    'نقد': False,
                    'چک': False,
                    'نسیه': False
                }
                
                # ============================================================
                # رفتن به صفحه مشتریان
                # ============================================================
                Clock.schedule_once(lambda dt: setattr(self.manager, 'current', 'customers'), 0.5)
                
            else:
                self.show_message('خطا', message)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    
    # ============================================================
    # توابع کمکی
    # ============================================================
    
    def show_message(self, title, message):
        """نمایش پیام"""
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
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
                size_hint=(0.8, 0.35),
                auto_dismiss=True
            )
            btn.bind(on_press=popup.dismiss)
            popup.open()
            
        except Exception as e:
            print(f"خطا در نمایش پیام: {e}")
    
    def go_back(self, instance):
        """بازگشت به صفحه ورود"""
        self.manager.current = 'login'
