# screens/collection_dialog.py
# ========== دیالوگ وصول مطالبات برای ایجنت ==========

import os
import traceback
from datetime import datetime
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.window import Window

from utils.rtl_widgets import PersianButton, RTLLabel, PersianPopup, RTLTextInput, PersianComboBox
from utils.persian_text import PersianLabel, number_to_words
from utils.file_manager import get_customers, get_routes, get_data_path
from utils.jalali_date import get_today_jalali, get_current_time
from utils.signature_widget import SignatureWidget
from utils.bank_manager import get_bank_names, add_bank, update_bank, delete_bank
from utils.collection_manager import (
    save_collection, check_duplicate_sayadi, check_duplicate_check_number
)
from error_handler import ErrorPopup


class CollectionDialog:
    """کلاس مدیریت دیالوگ های وصول مطالبات"""
    
    def __init__(self, agent_name, route, on_save_callback=None):
        self.agent_name = agent_name
        self.current_route = route
        self.on_save_callback = on_save_callback
        
        self.selected_customer = None
        self.temp_checks = []
        self.payment_methods = {
            'نقد': False,
            'چک': False
        }
        self._is_user_editing_cash = False
        self._current_check_index = 0
        self._total_checks = 0
        
        self._collection_widgets = {}
        self._signature_widget = None
        self._current_popup = None
        
        self.show_customer_selection()
    

    def show_customer_selection(self):
        """نمایش دیالوگ انتخاب مشتری با انتخاب مسیر و جستجو"""
        try:
            routes = get_routes()
            route_names = [r.get('name', '') for r in routes if r.get('name')]
            
            if not route_names:
                self.show_message('خطا', 'هیچ مسیری تعریف نشده است')
                return
            
            all_customers = get_customers()
            
            content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
            with content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(rect, 'pos', v),
                           size=lambda i, v: setattr(rect, 'size', v))
            
            
            if self.current_route and self.current_route in route_names:
                default_route = self.current_route
            else:
                default_route = route_names[0]
            
            self.route_combo = PersianComboBox(
                text=default_route,
                values=route_names,
                height=dp(55)
            )
            self.route_combo.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.route_combo.main_btn.color = (1, 1, 1, 1)
            self.route_combo.main_btn.font_size = sp(18)
            content.add_widget(self.route_combo)
            
            content.add_widget(Label(size_hint_y=None, height=dp(5)))
            
            search_input = RTLTextInput(
                hint_text='جستجوی مشتری...',
                multiline=False,
                size_hint_y=None,
                height=dp(55),
                font_size=sp(20)
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
            
            def filter_customers(text, route_name):
                customers_grid.clear_widgets()
                search_text = text.strip()
                
                route_customers = []
                for c in all_customers:
                    if c.get('route_name', '').strip() == route_name.strip():
                        route_customers.append(c.get('name', ''))
                
                for customer in route_customers:
                    if search_text and search_text not in customer:
                        continue
                    
                    customer_btn = PersianButton(
                        text=customer,
                        size_hint_y=None,
                        height=dp(50),
                        background_color=(0.2, 0.5, 0.9, 1),
                        color=(1, 1, 1, 1),
                        font_size=sp(18)
                    )
                    customer_btn.bind(
                        on_press=lambda x, name=customer, route=route_name: self._on_customer_selected_with_route(name, route)
                    )
                    customers_grid.add_widget(customer_btn)
                
                if not customers_grid.children:
                    customers_grid.add_widget(RTLLabel(
                        text='هیچ مشتری ای یافت نشد',
                        size_hint_y=None,
                        height=dp(40),
                        font_size=sp(16),
                        color=(0.5, 0.5, 0.5, 1)
                    ))
            
            def on_search_change(instance, value):
                filter_customers(value, self.route_combo.text)
            
            def on_route_change(instance, value):
                filter_customers(search_input.text, value)
            
            search_input._hidden_input.bind(text=on_search_change)
            self.route_combo.bind(text=on_route_change)
            
            filter_customers('', self.route_combo.text)
            
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
                size_hint=(0.9, 0.8),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=True
            )
            
            self.customer_selection_popup = popup
            close_btn.bind(on_press=popup.dismiss)
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش دیالوگ انتخاب مشتری: {e}", error_details)


    def _on_customer_selected_with_route(self, customer_name, route_name):
        try:
            if hasattr(self, 'customer_selection_popup'):
                self.customer_selection_popup.dismiss()
            self.selected_customer = customer_name
            self.current_route = route_name
            self.show_intent_dialog()
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در انتخاب مشتری: {e}", error_details)
    

    def show_intent_dialog(self):
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            
            content.add_widget(RTLLabel(
                text=f'آیا برای مشتری "{self.selected_customer}" قصد ثبت پیگیری وصول دارید؟',
                size_hint_y=None,
                height=dp(70),
                font_size=sp(20),
                color=(1, 1, 1, 1),
                halign='right'
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
                title='پیگیری وصول',
                content=content,
                size_hint=(0.85, 0.35),
                auto_dismiss=False
            )
            
            yes_btn.bind(on_press=lambda x: self._on_intent_yes(popup))
            no_btn.bind(on_press=lambda x: self._on_intent_no(popup))
            
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    
    def _on_intent_yes(self, popup):
        popup.dismiss()
        self.show_success_dialog()
    
    def _on_intent_no(self, popup):
        popup.dismiss()
        self.selected_customer = None
        self.show_customer_selection()
    

    def show_success_dialog(self):
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            
            content.add_widget(RTLLabel(
                text='آیا پیگیری وصول موفقیت آمیز بود؟',
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
                title='نتیجه پیگیری',
                content=content,
                size_hint=(0.85, 0.35),
                auto_dismiss=False
            )
            
            yes_btn.bind(on_press=lambda x: self._on_success_yes(popup))
            no_btn.bind(on_press=lambda x: self._on_success_no(popup))
            
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    
    def _on_success_yes(self, popup):
        popup.dismiss()
        self.show_main_collection_dialog()
    
    def _on_success_no(self, popup):
        popup.dismiss()
        self.show_fail_reason_dialog()
    

    def show_fail_reason_dialog(self):
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(12))
            
            content.add_widget(RTLLabel(
                text='علت عدم وصول',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(22),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))
            
            fail_reasons = [
                'عدم حضور مشتری',
                'عدم موجودی نقد',
                'چک برگشتی',
                'اختلاف حساب',
                'عدم تطابق چک',
                'درخواست تعویق مشتری',
                'سایر'
            ]
            
            content.add_widget(RTLLabel(
                text='علت:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))
            
            fail_reason_combo = PersianComboBox(
                values=fail_reasons,
                text=fail_reasons[0],
                height=dp(50)
            )
            fail_reason_combo.main_btn.background_color = (0.15, 0.15, 0.15, 1)
            fail_reason_combo.main_btn.color = (1, 1, 1, 1)
            fail_reason_combo.main_btn.font_size = sp(18)
            content.add_widget(fail_reason_combo)
            
            content.add_widget(RTLLabel(
                text='توضیحات:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))
            fail_description = RTLTextInput(
                multiline=True,
                size_hint_y=None,
                height=dp(80),
                font_size=sp(18),
                hint_text='توضیحات اضافی (الزامی برای "سایر")'
            )
            fail_description.bg_color = (0.15, 0.15, 0.15, 1)
            content.add_widget(fail_description)
            
            content.add_widget(RTLLabel(
                text='تاریخ پیگیری بعدی:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))
            
            next_date_input = RTLTextInput(
                text=get_today_jalali(),
                multiline=False,
                size_hint_y=None,
                height=dp(55),
                font_size=sp(22)
            )
            next_date_input.bg_color = (0.15, 0.15, 0.15, 1)
            content.add_widget(next_date_input)
            
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
                title='عدم وصول',
                content=content,
                size_hint=(0.85, 0.65),
                auto_dismiss=False
            )
            
            save_btn.bind(on_press=lambda x: self._save_fail_collection(
                popup, fail_reason_combo.text, fail_description.text, next_date_input.text
            ))
            cancel_btn.bind(on_press=popup.dismiss)
            
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    
    def _save_fail_collection(self, popup, reason, description, next_date):
        try:
            if reason == 'سایر' and not description.strip():
                self.show_message('خطا', 'برای گزینه "سایر"، توضیحات الزامی است')
                return
            
            if not next_date or not next_date.strip():
                self.show_message('خطا', 'تاریخ پیگیری بعدی الزامی است')
                return
            
            popup.dismiss()
            
            data = {
                'agent_name': self.agent_name,
                'customer': self.selected_customer,
                'route': self.current_route,
                'date': get_today_jalali(),
                'status': 'ناموفق',
                'fail_reason': reason,
                'fail_description': description.strip(),
                'next_follow_up_date': next_date.strip()
            }
            
            success, collection_id, message = save_collection(data)
            
            if success:
                self.show_message('موفق', f'وصول ناموفق با شناسه {collection_id} ثبت شد')
                if self.on_save_callback:
                    self.on_save_callback(collection_id, 'ناموفق')
            else:
                self.show_message('خطا', message)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ذخیره وصول ناموفق: {e}", error_details)
    

    def show_main_collection_dialog(self):
        """دیالوگ اصلی ثبت وصول موفق"""
        try:
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
                spacing=dp(8),
                size_hint_y=None
            )
            content.bind(minimum_height=content.setter('height'))
            
            # عنوان
            content.add_widget(RTLLabel(
                text=f'وصول مطالبات - {self.selected_customer}',
                size_hint_y=None,
                height=dp(45),
                font_size=sp(22),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))
            
            # نحوه وصول
            content.add_widget(RTLLabel(
                text='نحوه وصول:',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(18),
                color=(1, 1, 1, 1)
            ))
            
            payment_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
            
            self.cash_btn = PersianButton(
                text='نقد',
                size_hint_x=0.5,
                size_hint_y=None,
                height=dp(45),
                background_color=(0.3, 0.3, 0.3, 1),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            self.cash_btn.halign = 'center'
            self.cash_btn.valign = 'middle'
            self.cash_btn.bind(on_press=lambda x: self._toggle_payment_btn('نقد'))
            payment_layout.add_widget(self.cash_btn)
            
            self.check_btn = PersianButton(
                text='چک',
                size_hint_x=0.5,
                size_hint_y=None,
                height=dp(45),
                background_color=(0.3, 0.3, 0.3, 1),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            self.check_btn.halign = 'center'
            self.check_btn.valign = 'middle'
            self.check_btn.bind(on_press=lambda x: self._toggle_payment_btn('چک'))
            payment_layout.add_widget(self.check_btn)
            
            content.add_widget(payment_layout)
            content.add_widget(Label(size_hint_y=None, height=dp(8)))
            
            # ========== بخش نقد ==========
            self.cash_type_label = RTLLabel(
                text='نوع وصول نقدی:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            )
            content.add_widget(self.cash_type_label)
            
            self.cash_type_combo = PersianComboBox(
                values=['وجه نقد', 'کارتخوان', 'واریز به حساب'],
                text='وجه نقد',
                height=dp(50)
            )
            self.cash_type_combo.main_btn.background_color = (0.15, 0.15, 0.15, 1)
            self.cash_type_combo.main_btn.color = (1, 1, 1, 1)
            self.cash_type_combo.main_btn.font_size = sp(18)
            self.cash_type_combo.bind(text=lambda instance, value: self._update_ui_state())
            content.add_widget(self.cash_type_combo)
            
            # مبلغ دریافتی
            amount_label = RTLLabel(
                text='مبلغ دریافتی (ریال):',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            )
            content.add_widget(amount_label)
            
            self.cash_amount_input = RTLTextInput(
                text='0',
                multiline=False,
                size_hint_y=None,
                height=dp(55),
                font_size=sp(22)
            )
            self.cash_amount_input.bg_color = (0.15, 0.15, 0.15, 1)
            self.cash_amount_input._hidden_input.bind(focus=lambda i, v: self._select_all_text(i) if v else None)
            content.add_widget(self.cash_amount_input)
            
            # مبلغ به حروف
            self.cash_amount_words = RTLTextInput(
                text='صفر ریال',
                multiline=False,
                size_hint_y=None,
                height=dp(50),
                font_size=sp(22),
                disabled=True
            )
            self.cash_amount_words.bg_color = (0.08, 0.12, 0.08, 1)
            self.cash_amount_words.border_color = (0.2, 0.4, 0.2, 1)
            content.add_widget(self.cash_amount_words)
            
            def update_cash_words(instance, value):
                try:
                    amount = value.strip()
                    if not amount or amount == '0':
                        self.cash_amount_words.text = 'صفر ریال'
                        return
                    clean_amount = amount.replace(',', '').strip()
                    if clean_amount:
                        number = float(clean_amount)
                        words = number_to_words(int(number))
                        self.cash_amount_words.text = words if words else 'صفر ریال'
                except:
                    self.cash_amount_words.text = 'خطا در تبدیل'
            
            self.cash_amount_input._hidden_input.bind(text=update_cash_words)
            
            # کسورات
            deduction_label = RTLLabel(
                text='کسورات (ریال):',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            )
            content.add_widget(deduction_label)
            
            self.cash_deduction_input = RTLTextInput(
                text='0',
                multiline=False,
                size_hint_y=None,
                height=dp(55),
                font_size=sp(22)
            )
            self.cash_deduction_input.bg_color = (0.15, 0.15, 0.15, 1)
            content.add_widget(self.cash_deduction_input)
            
            # کسورات به حروف
            self.deduction_words = RTLTextInput(
                text='صفر ریال',
                multiline=False,
                size_hint_y=None,
                height=dp(50),
                font_size=sp(22),
                disabled=True
            )
            self.deduction_words.bg_color = (0.08, 0.12, 0.08, 1)
            self.deduction_words.border_color = (0.2, 0.4, 0.2, 1)
            content.add_widget(self.deduction_words)
            
            def update_deduction_words(instance, value):
                try:
                    amount = value.strip()
                    if not amount or amount == '0':
                        self.deduction_words.text = 'صفر ریال'
                        return
                    clean_amount = amount.replace(',', '').strip()
                    if clean_amount:
                        number = float(clean_amount)
                        words = number_to_words(int(number))
                        self.deduction_words.text = words if words else 'صفر ریال'
                except:
                    self.deduction_words.text = 'خطا در تبدیل'
            
            self.cash_deduction_input._hidden_input.bind(text=update_deduction_words)
            
            # محل وصول (بانک)
            self.bank_label = RTLLabel(
                text='محل وصول (بانک):',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            )
            content.add_widget(self.bank_label)
            
            bank_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))
            
            bank_names = get_bank_names()
            self.bank_combo = PersianComboBox(
                values=bank_names if bank_names else [''],
                text=bank_names[0] if bank_names else '',
                size_hint_x=0.7,
                height=dp(50)
            )
            self.bank_combo.main_btn.background_color = (0.15, 0.15, 0.15, 1)
            self.bank_combo.main_btn.color = (1, 1, 1, 1)
            self.bank_combo.main_btn.font_size = sp(16)
            bank_row.add_widget(self.bank_combo)
            
            bank_btn_layout = BoxLayout(size_hint_x=0.3, spacing=dp(3))
            
            add_bank_btn = PersianButton(
                text='+', size_hint_x=0.33,
                background_color=(0.2, 0.6, 0.2, 1), color=(1, 1, 1, 1), font_size=sp(18)
            )
            add_bank_btn.bind(on_press=lambda x: self._add_bank_dialog())
            bank_btn_layout.add_widget(add_bank_btn)
            
            edit_bank_btn = PersianButton(
                text='ویرایش', size_hint_x=0.33,
                background_color=(0.2, 0.5, 0.9, 1), color=(1, 1, 1, 1), font_size=sp(14)
            )
            edit_bank_btn.bind(on_press=lambda x: self._edit_bank_dialog())
            bank_btn_layout.add_widget(edit_bank_btn)
            
            delete_bank_btn = PersianButton(
                text='حذف', size_hint_x=0.34,
                background_color=(0.8, 0.2, 0.2, 1), color=(1, 1, 1, 1), font_size=sp(14)
            )
            delete_bank_btn.bind(on_press=lambda x: self._delete_bank_dialog())
            bank_btn_layout.add_widget(delete_bank_btn)
            
            bank_row.add_widget(bank_btn_layout)
            content.add_widget(bank_row)
            
            # شماره پیگیری
            self.tracking_label = RTLLabel(
                text='شماره پیگیری:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            )
            content.add_widget(self.tracking_label)
            
            self.tracking_input = RTLTextInput(
                text='',
                multiline=False,
                size_hint_y=None,
                height=dp(55),
                font_size=sp(18),
                hint_text='شماره پیگیری'
            )
            self.tracking_input.bg_color = (0.15, 0.15, 0.15, 1)
            self.tracking_input.border_color = (0.3, 0.3, 0.3, 1)
            self.tracking_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.tracking_input._hidden_input.foreground_color = (1, 1, 1, 1)
            content.add_widget(self.tracking_input)
            
            # ========== بخش چک ==========
            self.check_section_label = RTLLabel(
                text='ثبت چک:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            )
            content.add_widget(self.check_section_label)
            
            self.register_check_btn = PersianButton(
                text='ثبت چک',
                size_hint_y=None,
                height=dp(50),
                background_color=(0.2, 0.5, 0.9, 1),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            self.register_check_btn.bind(on_press=lambda x: self.show_check_count_dialog())
            content.add_widget(self.register_check_btn)
            
            self.checks_summary_label = RTLLabel(
                text='',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(16),
                color=(0.6, 0.6, 0.6, 1)
            )
            content.add_widget(self.checks_summary_label)
            
            # امضای مشتری
            content.add_widget(Label(size_hint_y=None, height=dp(10)))
            content.add_widget(RTLLabel(
                text='امضای مشتری:',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(18),
                color=(1, 1, 1, 1),
                bold=True
            ))
            
            self._signature_widget = SignatureWidget(
                size_hint_y=None,
                height=dp(150)
            )
            content.add_widget(self._signature_widget)
            
            clear_sign_btn = PersianButton(
                text='پاک کردن امضا',
                size_hint_y=None,
                height=dp(40),
                background_color=(0.6, 0.4, 0.2, 1),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            clear_sign_btn.bind(on_press=lambda x: self._signature_widget.clear_canvas())
            content.add_widget(clear_sign_btn)
            
            # توضیحات
            content.add_widget(RTLLabel(
                text='توضیحات:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))
            self.description_input = RTLTextInput(
                multiline=True,
                size_hint_y=None,
                height=dp(70),
                font_size=sp(18),
                hint_text='توضیحات اضافی (اختیاری)'
            )
            self.description_input.bg_color = (0.15, 0.15, 0.15, 1)
            content.add_widget(self.description_input)
            
            # جمع کل
            content.add_widget(Label(size_hint_y=None, height=dp(8)))
            
            self.total_display = RTLLabel(
                text='جمع کل وصول: 0 ریال',
                size_hint_y=None,
                height=dp(45),
                font_size=sp(22),
                bold=True,
                color=(0.2, 0.8, 0.2, 1)
            )
            content.add_widget(self.total_display)
            
            # دکمه ها
            btn_layout = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(10))
            
            save_btn = PersianButton(
                text='ثبت نهایی',
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
                font_size=sp(20)
            )
            
            btn_layout.add_widget(save_btn)
            btn_layout.add_widget(cancel_btn)
            content.add_widget(btn_layout)
            
            scroll.add_widget(content)
            main_container.add_widget(scroll)
            
            self._current_popup = PersianPopup(
                title='ثبت وصول',
                content=main_container,
                size_hint=(0.92, 0.9),
                auto_dismiss=False
            )
            
            save_btn.bind(on_press=lambda x: self._validate_and_save())
            cancel_btn.bind(on_press=lambda x: self._cancel_collection())
            
            # ذخیره ویجت ها برای disabled/enabled
            self._cash_widgets = [
                self.cash_type_label, self.cash_type_combo,
                amount_label, self.cash_amount_input, self.cash_amount_words,
                deduction_label, self.cash_deduction_input, self.deduction_words,
                self.bank_label, self.bank_combo,
                self.tracking_label, self.tracking_input
            ]
            
            self._check_widgets = [
                self.check_section_label, self.register_check_btn, self.checks_summary_label
            ]
            
            self._update_ui_state()
            self._update_total_display()
            
            self._current_popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش دیالوگ وصول: {e}", error_details)
    

    def _toggle_payment_btn(self, method):
        try:
            self.payment_methods[method] = not self.payment_methods[method]
            
            if method == 'نقد':
                if self.payment_methods[method]:
                    self.cash_btn.background_color = (0.2, 0.6, 0.2, 1)
                else:
                    self.cash_btn.background_color = (0.3, 0.3, 0.3, 1)
            elif method == 'چک':
                if self.payment_methods[method]:
                    self.check_btn.background_color = (0.2, 0.6, 0.2, 1)
                else:
                    self.check_btn.background_color = (0.3, 0.3, 0.3, 1)
                    self.temp_checks = []
                    self.checks_summary_label.text = ''
            
            self._update_ui_state()
            self._update_total_display()
            
        except Exception as e:
            print(f"خطا در تغییر وضعیت روش پرداخت: {e}")
    

    def _update_ui_state(self):
        """بروزرسانی وضعیت فعال/غیرفعال فیلدها"""
        try:
            is_cash = self.payment_methods.get('نقد', False)
            is_check = self.payment_methods.get('چک', False)
            
            # فعال/غیرفعال کردن فیلدهای نقد
            for widget in self._cash_widgets:
                widget.disabled = not is_cash
            
            # فعال/غیرفعال کردن فیلدهای چک
            for widget in self._check_widgets:
                widget.disabled = not is_check
            
            if not is_check:
                self.temp_checks = []
                self.checks_summary_label.text = ''
            
            # نمایش/مخفی کردن بانک و پیگیری بر اساس نوع وصول
            if is_cash:
                cash_type = self.cash_type_combo.text
                show_bank = cash_type in ['کارتخوان', 'واریز به حساب']
                self.bank_label.disabled = not show_bank
                self.bank_combo.disabled = not show_bank
                self.tracking_label.disabled = not show_bank
                self.tracking_input.disabled = not show_bank
            else:
                self.bank_label.disabled = True
                self.bank_combo.disabled = True
                self.tracking_label.disabled = True
                self.tracking_input.disabled = True
            
        except Exception as e:
            print(f"خطا در بروزرسانی UI: {e}")
    

    def _update_total_display(self):
        try:
            total = 0
            
            if self.payment_methods.get('نقد', False):
                try:
                    cash = float(self.cash_amount_input.text.replace(',', '')) if self.cash_amount_input.text else 0
                    deductions = float(self.cash_deduction_input.text.replace(',', '')) if self.cash_deduction_input.text else 0
                    total += (cash - deductions)
                except:
                    pass
            
            if self.payment_methods.get('چک', False):
                total += sum([c.get('amount', 0) for c in self.temp_checks])
            
            self.total_display.text = f'جمع کل وصول: {total:,.0f} ریال'
            
        except Exception as e:
            print(f"خطا در محاسبه جمع کل: {e}")
    

    def _select_all_text(self, instance):
        if instance and hasattr(instance, 'select_all'):
            instance.select_all()
    

    def _add_bank_dialog(self):
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
            
            content.add_widget(RTLLabel(
                text='افزودن بانک جدید',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(20),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))
            
            name_input = RTLTextInput(
                hint_text='نام بانک',
                multiline=False,
                size_hint_y=None,
                height=dp(50),
                font_size=sp(18)
            )
            name_input.bg_color = (0.15, 0.15, 0.15, 1)
            content.add_widget(name_input)
            
            btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
            
            save_btn = PersianButton(
                text='افزودن',
                background_color=(0.2, 0.7, 0.2, 1),
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
            
            btn_layout.add_widget(save_btn)
            btn_layout.add_widget(cancel_btn)
            content.add_widget(btn_layout)
            
            popup = PersianPopup(
                title='افزودن بانک',
                content=content,
                size_hint=(0.8, 0.35),
                auto_dismiss=False
            )
            
            def do_add(instance):
                name = name_input.text.strip()
                if not name:
                    self.show_message('خطا', 'نام بانک الزامی است')
                    return
                
                success, message = add_bank(name)
                if success:
                    popup.dismiss()
                    self._refresh_bank_list()
                    self.show_message('موفق', message)
                else:
                    self.show_message('خطا', message)
            
            save_btn.bind(on_press=do_add)
            cancel_btn.bind(on_press=popup.dismiss)
            popup.open()
            
        except Exception as e:
            print(f"خطا در دیالوگ افزودن بانک: {e}")
    

    def _edit_bank_dialog(self):
        try:
            if not self.bank_combo or not self.bank_combo.text:
                self.show_message('خطا', 'بانکی برای ویرایش انتخاب نشده')
                return
            
            current_bank = self.bank_combo.text
            
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
            
            content.add_widget(RTLLabel(
                text=f'ویرایش بانک: {current_bank}',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(20),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))
            
            name_input = RTLTextInput(
                text=current_bank,
                multiline=False,
                size_hint_y=None,
                height=dp(50),
                font_size=sp(18)
            )
            name_input.bg_color = (0.15, 0.15, 0.15, 1)
            content.add_widget(name_input)
            
            btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
            
            save_btn = PersianButton(
                text='ویرایش',
                background_color=(0.2, 0.5, 0.9, 1),
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
            
            btn_layout.add_widget(save_btn)
            btn_layout.add_widget(cancel_btn)
            content.add_widget(btn_layout)
            
            popup = PersianPopup(
                title='ویرایش بانک',
                content=content,
                size_hint=(0.8, 0.35),
                auto_dismiss=False
            )
            
            def do_edit(instance):
                new_name = name_input.text.strip()
                if not new_name:
                    self.show_message('خطا', 'نام بانک الزامی است')
                    return
                
                success, message = update_bank(current_bank, new_name)
                if success:
                    popup.dismiss()
                    self._refresh_bank_list()
                    self.show_message('موفق', message)
                else:
                    self.show_message('خطا', message)
            
            save_btn.bind(on_press=do_edit)
            cancel_btn.bind(on_press=popup.dismiss)
            popup.open()
            
        except Exception as e:
            print(f"خطا در دیالوگ ویرایش بانک: {e}")
    

    def _delete_bank_dialog(self):
        try:
            if not self.bank_combo or not self.bank_combo.text:
                self.show_message('خطا', 'بانکی برای حذف انتخاب نشده')
                return
            
            current_bank = self.bank_combo.text
            
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            
            content.add_widget(RTLLabel(
                text=f'آیا از حذف بانک "{current_bank}" اطمینان دارید؟',
                size_hint_y=None,
                height=dp(55),
                font_size=sp(18),
                color=(1, 1, 1, 1)
            ))
            
            btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
            
            yes_btn = PersianButton(
                text='بله',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            no_btn = PersianButton(
                text='خیر',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            
            btn_layout.add_widget(yes_btn)
            btn_layout.add_widget(no_btn)
            content.add_widget(btn_layout)
            
            popup = PersianPopup(
                title='حذف بانک',
                content=content,
                size_hint=(0.8, 0.3),
                auto_dismiss=False
            )
            
            def do_delete(instance):
                success, message = delete_bank(current_bank)
                if success:
                    popup.dismiss()
                    self._refresh_bank_list()
                    self.show_message('موفق', message)
                else:
                    self.show_message('خطا', message)
            
            yes_btn.bind(on_press=do_delete)
            no_btn.bind(on_press=popup.dismiss)
            popup.open()
            
        except Exception as e:
            print(f"خطا در دیالوگ حذف بانک: {e}")
    

    def _refresh_bank_list(self):
        try:
            bank_names = get_bank_names()
            if self.bank_combo:
                self.bank_combo.values = bank_names if bank_names else ['']
                if bank_names:
                    self.bank_combo.text = bank_names[0]
                else:
                    self.bank_combo.text = ''
        except Exception as e:
            print(f"خطا در بروزرسانی لیست بانک: {e}")
    

    def show_check_count_dialog(self):
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            
            content.add_widget(RTLLabel(
                text='تعداد چک دریافتی:',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(18),
                color=(1, 1, 1, 1)
            ))
            
            check_count_input = RTLTextInput(
                text='1',
                multiline=False,
                size_hint_y=None,
                height=dp(55),
                font_size=sp(22),
                input_filter='int'
            )
            check_count_input.bg_color = (0.15, 0.15, 0.15, 1)
            content.add_widget(check_count_input)
            
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
                popup, check_count_input.text
            ))
            cancel_btn.bind(on_press=popup.dismiss)
            
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    

    def _start_check_registration(self, popup, count_str):
        try:
            try:
                count = int(count_str)
                if count < 1:
                    self.show_message('خطا', 'تعداد چک باید حداقل 1 باشد')
                    return
            except:
                self.show_message('خطا', 'تعداد چک معتبر نیست')
                return
            
            popup.dismiss()
            
            self.temp_checks = []
            self._current_check_index = 0
            self._total_checks = count
            
            self._show_check_form()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    

    def _show_check_form(self):
        try:
            if self._current_check_index >= self._total_checks:
                self._show_checks_summary()
                return
            
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
            
            content.add_widget(RTLLabel(
                text=f'چک {self._current_check_index + 1} از {self._total_checks}',
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
            check_amount_input = RTLTextInput(
                multiline=False,
                size_hint_y=None,
                height=dp(55),
                font_size=sp(22),
                hint_text='مبلغ'
            )
            check_amount_input.bg_color = (0.15, 0.15, 0.15, 1)
            content.add_widget(check_amount_input)
            
            check_amount_words = RTLTextInput(
                text='صفر ریال',
                multiline=False,
                size_hint_y=None,
                height=dp(50),
                font_size=sp(18),
                disabled=True
            )
            check_amount_words.bg_color = (0.08, 0.12, 0.08, 1)
            content.add_widget(check_amount_words)
            
            def update_check_words(instance, value):
                try:
                    amount = value.strip()
                    if not amount or amount == '0':
                        check_amount_words.text = 'صفر ریال'
                        return
                    clean = amount.replace(',', '').strip()
                    if clean:
                        words = number_to_words(int(float(clean)))
                        check_amount_words.text = words if words else 'صفر ریال'
                except:
                    check_amount_words.text = 'خطا'
            
            check_amount_input._hidden_input.bind(text=update_check_words)
            
            content.add_widget(RTLLabel(
                text='تاریخ سررسید:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))
            check_date_input = RTLTextInput(
                text=get_today_jalali(),
                multiline=False,
                size_hint_y=None,
                height=dp(55),
                font_size=sp(22)
            )
            check_date_input.bg_color = (0.15, 0.15, 0.15, 1)
            content.add_widget(check_date_input)
            
            content.add_widget(RTLLabel(
                text='شماره چک:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))
            check_number_input = RTLTextInput(
                multiline=False,
                size_hint_y=None,
                height=dp(55),
                font_size=sp(22),
                hint_text='شماره چک',
                input_filter='int'
            )
            check_number_input.bg_color = (0.15, 0.15, 0.15, 1)
            content.add_widget(check_number_input)
            
            content.add_widget(RTLLabel(
                text='شناسه صیادی (16 رقم):',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))
            
            sayadi_input = RTLTextInput(
                multiline=False,
                size_hint_y=None,
                height=dp(55),
                font_size=sp(22),
                hint_text='16 رقمی',
                input_filter='int'
            )
            sayadi_input.bg_color = (0.15, 0.15, 0.15, 1)
            sayadi_input._hidden_input.max_length = 16
            content.add_widget(sayadi_input)
            
            content.add_widget(RTLLabel(
                text='وضعیت ثبت صیادی:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))
            sayadi_status_combo = PersianComboBox(
                values=['ثبت شده', 'ثبت نشده'],
                text='ثبت شده',
                height=dp(50)
            )
            sayadi_status_combo.main_btn.background_color = (0.15, 0.15, 0.15, 1)
            sayadi_status_combo.main_btn.color = (1, 1, 1, 1)
            sayadi_status_combo.main_btn.font_size = sp(18)
            content.add_widget(sayadi_status_combo)
            
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
                size_hint=(0.9, 0.8),
                auto_dismiss=False
            )
            
            save_btn.bind(on_press=lambda x: self._save_check(
                popup,
                check_amount_input.text,
                check_date_input.text,
                check_number_input.text,
                sayadi_input.text,
                sayadi_status_combo.text
            ))
            cancel_btn.bind(on_press=lambda x: self._cancel_check_registration(popup))
            
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش فرم چک: {e}", error_details)
    

    def _save_check(self, popup, amount_str, date, check_number, sayadi_id, sayadi_status):
        try:
            try:
                amount = float(amount_str.replace(',', '')) if amount_str else 0
                if amount <= 0:
                    self.show_message('خطا', 'مبلغ چک باید بیشتر از صفر باشد')
                    return
            except:
                self.show_message('خطا', 'مبلغ چک معتبر نیست')
                return
            
            if not check_number:
                self.show_message('خطا', 'شماره چک الزامی است')
                return
            
            if check_duplicate_check_number(self.selected_customer, check_number):
                self.show_message('خطا', f'شماره چک "{check_number}" قبلا برای این مشتری ثبت شده است')
                return
            
            if not sayadi_id or len(sayadi_id) != 16:
                self.show_message('خطا', 'شناسه صیادی باید دقیقا 16 رقم باشد')
                return
            
            if not sayadi_id.isdigit():
                self.show_message('خطا', 'شناسه صیادی باید فقط شامل عدد باشد')
                return
            
            if check_duplicate_sayadi(sayadi_id):
                self.show_message('خطا', 'این شناسه صیادی قبلا در سیستم ثبت شده است')
                return
            
            if sayadi_status == 'ثبت نشده':
                confirm_content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
                confirm_content.add_widget(RTLLabel(
                    text='گرفتن چک ثبت نشده مجاز نبوده و شامل جریمه میگردد.\nآیا ادامه میدهید؟',
                    size_hint_y=None,
                    height=dp(70),
                    font_size=sp(18),
                    color=(1, 0.8, 0.2, 1)
                ))
                
                c_btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
                c_yes = PersianButton(text='بله', background_color=(0.2, 0.7, 0.2, 1), size_hint_y=None, height=dp(45), color=(1,1,1,1), font_size=sp(16))
                c_no = PersianButton(text='خیر', background_color=(0.8, 0.2, 0.2, 1), size_hint_y=None, height=dp(45), color=(1,1,1,1), font_size=sp(16))
                c_btn_layout.add_widget(c_yes)
                c_btn_layout.add_widget(c_no)
                confirm_content.add_widget(c_btn_layout)
                
                confirm_popup = PersianPopup(
                    title='تایید',
                    content=confirm_content,
                    size_hint=(0.8, 0.4),
                    auto_dismiss=False
                )
                
                def on_yes(instance):
                    confirm_popup.dismiss()
                    self._add_check_and_continue(popup, amount, date, check_number, sayadi_id, sayadi_status)
                
                def on_no(instance):
                    confirm_popup.dismiss()
                
                c_yes.bind(on_press=on_yes)
                c_no.bind(on_press=on_no)
                confirm_popup.open()
                return
            
            self._add_check_and_continue(popup, amount, date, check_number, sayadi_id, sayadi_status)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ذخیره چک: {e}", error_details)
    

    def _add_check_and_continue(self, popup, amount, date, check_number, sayadi_id, sayadi_status):
        popup.dismiss()
        
        self.temp_checks.append({
            'amount': amount,
            'due_date': date,
            'check_number': check_number,
            'sayadi_id': sayadi_id,
            'sayadi_status': sayadi_status
        })
        
        self._current_check_index += 1
        self._update_checks_summary()
        self._update_total_display()
        
        self._show_check_form()
    

    def _cancel_check_registration(self, popup):
        popup.dismiss()
        self.temp_checks = []
        self.checks_summary_label.text = ''
        self._update_total_display()
    

    def _update_checks_summary(self):
        if not self.temp_checks:
            self.checks_summary_label.text = ''
            return
        
        total = sum([c['amount'] for c in self.temp_checks])
        self.checks_summary_label.text = f'{len(self.temp_checks)} چک ثبت شده - جمع: {total:,.0f} ریال'
    

    def _show_checks_summary(self):
        try:
            total = sum([c['amount'] for c in self.temp_checks])
            
            content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(8))
            
            content.add_widget(RTLLabel(
                text='خلاصه چک ها',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(20),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))
            
            for i, check in enumerate(self.temp_checks):
                content.add_widget(RTLLabel(
                    text=f'{i+1}. مبلغ: {check["amount"]:,.0f} | تاریخ: {check["due_date"]} | '
                         f'شماره: {check["check_number"]} | صیادی: {check["sayadi_id"]}',
                    size_hint_y=None,
                    height=dp(28),
                    font_size=sp(14),
                    color=(1, 1, 1, 1)
                ))
            
            content.add_widget(RTLLabel(
                text=f'جمع کل چک ها: {total:,.0f} ریال',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(18),
                bold=True,
                color=(0.2, 0.8, 0.2, 1)
            ))
            
            close_btn = PersianButton(
                text='تایید',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            content.add_widget(close_btn)
            
            popup = PersianPopup(
                title='خلاصه چک ها',
                content=content,
                size_hint=(0.85, 0.5),
                auto_dismiss=True
            )
            
            close_btn.bind(on_press=popup.dismiss)
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    

    def _validate_and_save(self):
        try:
            is_cash = self.payment_methods.get('نقد', False)
            is_check = self.payment_methods.get('چک', False)
            
            if not is_cash and not is_check:
                self.show_message('خطا', 'حداقل یک روش وصول را انتخاب کنید')
                return
            
            if not self._signature_widget or not self._signature_widget.has_signature:
                self.show_message('خطا', 'امضای مشتری الزامی است')
                return
            
            if is_cash:
                try:
                    cash_amount = float(self.cash_amount_input.text.replace(',', '')) if self.cash_amount_input.text else 0
                    if cash_amount <= 0:
                        self.show_message('خطا', 'مبلغ نقد باید بیشتر از صفر باشد')
                        return
                    
                    deductions = float(self.cash_deduction_input.text.replace(',', '')) if self.cash_deduction_input.text else 0
                    if deductions > cash_amount:
                        self.show_message('خطا', 'کسورات نمی تواند از مبلغ دریافتی بیشتر باشد')
                        return
                    
                    cash_type = self.cash_type_combo.text
                    if cash_type in ['کارتخوان', 'واریز به حساب']:
                        if not self.bank_combo or not self.bank_combo.text:
                            self.show_message('خطا', 'انتخاب بانک (محل وصول) الزامی است')
                            return
                        
                        if not self.tracking_input or not self.tracking_input.text.strip():
                            self.show_message('خطا', 'شماره پیگیری الزامی است')
                            return
                        
                except Exception as e:
                    self.show_message('خطا', f'مقادیر نقد معتبر نیستند: {e}')
                    return
            
            if is_check and not self.temp_checks:
                self.show_message('خطا', 'حداقل یک چک باید ثبت شود')
                return
            
            self._show_final_confirmation()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در اعتبارسنجی: {e}", error_details)
    

    def _show_final_confirmation(self):
        try:
            is_cash = self.payment_methods.get('نقد', False)
            is_check = self.payment_methods.get('چک', False)
            
            content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(6))
            
            content.add_widget(RTLLabel(
                text='خلاصه وصول',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(22),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))
            
            content.add_widget(RTLLabel(
                text=f'مشتری: {self.selected_customer}',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(18),
                color=(1, 1, 1, 1)
            ))
            
            total = 0
            
            if is_cash:
                cash_amount = float(self.cash_amount_input.text.replace(',', '')) if self.cash_amount_input.text else 0
                deductions = float(self.cash_deduction_input.text.replace(',', '')) if self.cash_deduction_input.text else 0
                net_cash = cash_amount - deductions
                total += net_cash
                
                content.add_widget(RTLLabel(
                    text=f'نوع وصول نقدی: {self.cash_type_combo.text}',
                    size_hint_y=None,
                    height=dp(25),
                    font_size=sp(16),
                    color=(1, 1, 1, 1)
                ))
                content.add_widget(RTLLabel(
                    text=f'مبلغ نقد: {cash_amount:,.0f} | کسورات: {deductions:,.0f} | خالص: {net_cash:,.0f} ریال',
                    size_hint_y=None,
                    height=dp(25),
                    font_size=sp(16),
                    color=(0.2, 0.8, 0.2, 1)
                ))
                
                if self.cash_type_combo.text in ['کارتخوان', 'واریز به حساب']:
                    bank_name = self.bank_combo.text if self.bank_combo else ''
                    tracking_number = self.tracking_input.text if self.tracking_input else ''
                    
                    content.add_widget(RTLLabel(
                        text=f'بانک: {bank_name}',
                        size_hint_y=None,
                        height=dp(25),
                        font_size=sp(16),
                        color=(1, 1, 1, 1)
                    ))
                    content.add_widget(RTLLabel(
                        text=f'شماره پیگیری: {tracking_number}',
                        size_hint_y=None,
                        height=dp(25),
                        font_size=sp(16),
                        color=(1, 1, 1, 1)
                    ))
            
            if is_check:
                check_total = sum([c['amount'] for c in self.temp_checks])
                total += check_total
                
                content.add_widget(RTLLabel(
                    text=f'تعداد چک: {len(self.temp_checks)} | جمع چک ها: {check_total:,.0f} ریال',
                    size_hint_y=None,
                    height=dp(25),
                    font_size=sp(16),
                    color=(0.6, 0.3, 0.6, 1)
                ))
            
            content.add_widget(RTLLabel(
                text=f'جمع کل وصول: {total:,.0f} ریال',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(20),
                bold=True,
                color=(0.2, 0.8, 0.2, 1)
            ))
            
            btn_layout = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(10))
            
            yes_btn = PersianButton(
                text='ثبت نهایی',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            no_btn = PersianButton(
                text='انصراف',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            
            btn_layout.add_widget(yes_btn)
            btn_layout.add_widget(no_btn)
            content.add_widget(btn_layout)
            
            confirm_popup = PersianPopup(
                title='تایید نهایی',
                content=content,
                size_hint=(0.9, 0.6),
                auto_dismiss=False
            )
            
            yes_btn.bind(on_press=lambda x: self._save_collection(confirm_popup))
            no_btn.bind(on_press=confirm_popup.dismiss)
            
            confirm_popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    

    def _save_collection(self, confirm_popup):
        try:
            confirm_popup.dismiss()
            
            is_cash = self.payment_methods.get('نقد', False)
            is_check = self.payment_methods.get('چک', False)
            
            data = {
                'agent_name': self.agent_name,
                'customer': self.selected_customer,
                'route': self.current_route,
                'date': get_today_jalali(),
                'status': 'موفق',
                'has_cash': is_cash,
                'has_check': is_check,
                'description': self.description_input.text.strip()
            }
            
            if is_cash:
                cash_amount = float(self.cash_amount_input.text.replace(',', '')) if self.cash_amount_input.text else 0
                deductions = float(self.cash_deduction_input.text.replace(',', '')) if self.cash_deduction_input.text else 0
                
                data['cash_type'] = self.cash_type_combo.text
                data['cash_amount'] = cash_amount
                data['cash_deductions'] = deductions
                data['net_cash'] = cash_amount - deductions
                
                if self.cash_type_combo.text in ['کارتخوان', 'واریز به حساب']:
                    data['bank'] = self.bank_combo.text if self.bank_combo else ''
                    data['tracking_number'] = self.tracking_input.text.strip() if self.tracking_input else ''
            
            if is_check:
                data['checks'] = self.temp_checks
                data['total_check_amount'] = sum([c['amount'] for c in self.temp_checks])
            
            total = 0
            if is_cash:
                total += data['net_cash']
            if is_check:
                total += data['total_check_amount']
            data['total_collection'] = total
            
            if self._signature_widget and self._signature_widget.has_signature:
                signatures_dir = os.path.join(get_data_path(), 'signatures')
                os.makedirs(signatures_dir, exist_ok=True)
                
                temp_id = f"TEMP_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                signature_path = os.path.join(signatures_dir, f'{temp_id}.png')
                
                self._signature_widget.save_signature(signature_path)
                data['signature_path'] = signature_path
            
            success, collection_id, message = save_collection(data)
            
            if success:
                if 'signature_path' in data and data['signature_path']:
                    old_path = data['signature_path']
                    new_path = os.path.join(signatures_dir, f'{collection_id}.png')
                    try:
                        if os.path.exists(old_path):
                            os.rename(old_path, new_path)
                            data['signature_path'] = new_path
                    except Exception as e:
                        print(f"خطا در تغییر نام فایل امضا: {e}")
                
                if self._current_popup:
                    self._current_popup.dismiss()
                
                self.show_message('موفق', f'وصول با شناسه {collection_id} ثبت شد')
                
                if self.on_save_callback:
                    self.on_save_callback(collection_id, 'موفق')
            else:
                self.show_message('خطا', message)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ذخیره وصول: {e}", error_details)
    

    def _cancel_collection(self):
        if self._current_popup:
            self._current_popup.dismiss()
        
        self.temp_checks = []
        self.payment_methods = {'نقد': False, 'چک': False}
        self.selected_customer = None
    

    def show_message(self, title, message):
        """نمایش پیام با پشتیبانی از متن طولانی"""
        try:
            from kivy.uix.boxlayout import BoxLayout
            from kivy.uix.scrollview import ScrollView
            from kivy.uix.label import Label
            from kivy.metrics import dp, sp
            from kivy.graphics import Color, Rectangle
            from utils.rtl_widgets import PersianPopup, PersianButton
            
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            with content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(rect, 'pos', v),
                        size=lambda i, v: setattr(rect, 'size', v))
            
            try:
                import arabic_reshaper
                from bidi.algorithm import get_display
                reshaped = arabic_reshaper.reshape(message)
                display_text = get_display(reshaped)
            except:
                display_text = message
            
            msg_label = Label(
                text=display_text,
                font_size=sp(15),
                color=(1, 1, 1, 1),
                size_hint_y=None,
                halign='center',
                valign='top',
                text_size=(dp(550), None),
                font_name='fonts/Amiri-Regular.ttf',
                padding=(dp(20), 0, dp(0), 0)
            )
            
            lines = message.count('\n') + 1
            if len(message) > 50 and lines == 1:
                approx_chars_per_line = 35
                lines = (len(message) // approx_chars_per_line) + 1
            
            line_height = sp(15) + dp(6)
            label_height = max(lines * line_height + dp(25), dp(50))
            label_height = min(label_height, dp(490))
            
            msg_label.height = label_height
            msg_label.text_size = (dp(550), label_height)
            
            scroll = ScrollView(
                do_scroll_x=False,
                do_scroll_y=True,
                size_hint_y=None,
                height=label_height + dp(10),
                bar_width=dp(6),
                bar_color=(0.3, 0.5, 0.8, 0.8),
                bar_inactive_color=(0.2, 0.2, 0.2, 0.5)
            )
            scroll.add_widget(msg_label)
            content.add_widget(scroll)
            
            btn = PersianButton(
                text='باشه',
                size_hint_y=None,
                height=dp(45),
                font_size=sp(16),
                color=(1, 1, 1, 1),
                background_color=(0.2, 0.6, 1, 1)
            )
            content.add_widget(btn)
            
            popup = PersianPopup(
                title=title,
                content=content,
                size_hint=(0.9, None),
                height=label_height + dp(250),
                background_color=(0.08, 0.08, 0.08, 1)
            )
            btn.bind(on_press=popup.dismiss)
            popup.open()
            
        except Exception as e:
            print(f"خطا در نمایش پیام: {e}")
            import traceback
            traceback.print_exc()