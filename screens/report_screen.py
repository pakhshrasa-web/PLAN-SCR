# screens/report_screen.py
# ========== صفحه گزارش‌ها ==========

import traceback
import os
import threading
from datetime import datetime, timedelta
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox

from utils.rtl_widgets import PersianButton, RTLLabel, PersianPopup, RTLTextInput
from utils.persian_text import PersianLabel
from utils.file_manager import get_daily_logs, load_json, save_json, get_data_path, get_settings, get_customers
from utils.excel_exporter import export_to_excel
from utils.jalali_date import get_today_jalali
from utils.file_cleaner import (
    get_excel_files_info,
    delete_files,
    delete_old_files,
    get_total_size,
    get_file_stats
)
from error_handler import ErrorPopup


class ReportScreen(Screen):
    def __init__(self, **kwargs):
        try:
            super().__init__(**kwargs)
            with self.canvas.before:
                Color(0.08, 0.08, 0.08, 1)
                self.bg_rect = Rectangle(pos=self.pos, size=self.size)
                self.bind(pos=self._update_bg, size=self._update_bg)
            self.current_tab = 0
            self.settings = get_settings()
            self.selected_files = {}
            self.history_popup = None
            self.selected_score = None
            self.score_buttons = []
            self._self_assessment_popup = None
            self._self_assessment_confirm = None
            self.current_evaluation_date = None 

            # ✅ فلگ‌های جدید برای جلوگیری از لوپ
            self._is_processing = False
            self._self_assessment_shown = False

            # متغیرهای فیلتر
            self.performance_from_date = ''
            self.performance_to_date = ''
            self.detail_from_date = ''
            self.detail_to_date = ''

            self.build_ui()
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت ReportScreen: {e}", error_details)
            raise
    
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def _on_field_focus(self, instance, value):
        if value:
            Clock.schedule_once(lambda dt: self._select_all_text(instance), 0.1)

    def _select_all_text(self, instance):
        if instance and hasattr(instance, 'select_all'):
            instance.select_all()
    
    def build_ui(self):
        try:
            layout = BoxLayout(orientation='vertical', padding=[dp(5), dp(5), dp(5), dp(5)])
            
            tabs_layout = BoxLayout(
                size_hint_y=None,
                height=dp(40),
                spacing=dp(2)
            )
            
            btn_performance = PersianButton(
                text='عملکرد کلی',
                background_color=(0.3, 0.5, 0.8, 1),
                size_hint_y=None,
                height=dp(36),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            btn_performance.bind(on_press=lambda x: self.switch_tab(0))
            tabs_layout.add_widget(btn_performance)
            
            btn_detail = PersianButton(
                text='ریز عملکرد',
                background_color=(0.3, 0.5, 0.8, 0.6),
                size_hint_y=None,
                height=dp(36),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            btn_detail.bind(on_press=lambda x: self.switch_tab(1))
            tabs_layout.add_widget(btn_detail)
            
            btn_stats = PersianButton(
                text='آمار و ارزیابی',
                background_color=(0.3, 0.5, 0.8, 0.6),
                size_hint_y=None,
                height=dp(36),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            btn_stats.bind(on_press=lambda x: self.switch_tab(2))
            tabs_layout.add_widget(btn_stats)
            
            layout.add_widget(tabs_layout)
            
            self.content_area = BoxLayout(orientation='vertical')
            layout.add_widget(self.content_area)
            
            btn_layout = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(8), padding=dp(5))
            
            refresh_btn = PersianButton(
                text='تازه سازی',
                background_color=(0.4, 0.4, 0.8, 1),
                size_hint_y=None,
                height=dp(40),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            refresh_btn.bind(on_press=self.refresh_stats)
            btn_layout.add_widget(refresh_btn)
            
            excel_btn = PersianButton(
                text='Excel',
                background_color=(0.2, 0.6, 0.2, 1),
                size_hint_y=None,
                height=dp(40),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            excel_btn.bind(on_press=self.export_excel)
            btn_layout.add_widget(excel_btn)
            
            back_btn = PersianButton(
                text='بازگشت',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(40),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            back_btn.bind(on_press=self.go_back)
            btn_layout.add_widget(back_btn)
            
            layout.add_widget(btn_layout)
            self.add_widget(layout)
            
            self.switch_tab(0)
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت UI ReportScreen: {e}", error_details)
            raise
    
    def switch_tab(self, tab_id):
        self.current_tab = tab_id
        self.content_area.clear_widgets()
        
        if tab_id == 0:
            self.show_performance_tab()
        elif tab_id == 1:
            self.show_detail_tab()
        elif tab_id == 2:
            self.show_stats_tab()
    
    # ============================================================
    # توابع تاریخ
    # ============================================================
    
    def _get_first_day_of_month(self):
        """دریافت اولین روز ماه جاری به صورت jalali"""
        try:
            today = get_today_jalali()
            parts = today.split('/')
            if len(parts) == 3:
                return f"{parts[0]}/{parts[1]}/01"
            return today
        except:
            return get_today_jalali()
    
    def _filter_dates(self, date_list, from_date, to_date):
        """فیلتر کردن لیست تاریخ‌ها بر اساس بازه"""
        if not from_date and not to_date:
            return date_list
        
        filtered = []
        for date in date_list:
            if from_date and date < from_date:
                continue
            if to_date and date > to_date:
                continue
            filtered.append(date)
        return filtered
    
    # ============================================================
    # تب عملکرد کلی
    # ============================================================
    
    def show_performance_tab(self):
        try:
            # تنظیم پیشفرض: اول ماه تا امروز
            if not self.performance_from_date:
                self.performance_from_date = self._get_first_day_of_month()
            if not self.performance_to_date:
                self.performance_to_date = get_today_jalali()
            
            all_logs = get_daily_logs()
            
            # ✅ ساخت بخش فیلتر
            filter_layout = BoxLayout(
                orientation='vertical',
                size_hint_y=None,
                height=dp(120),
                spacing=dp(5),
                padding=dp(5)
            )
            filter_layout.add_widget(RTLLabel(
                text='فیلتر بازه زمانی:',
                size_hint_y=None,
                height=dp(25),
                font_size=sp(14),
                color=(0.4, 0.7, 1, 1),
                bold=True
            ))
            
            date_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))
            
            date_row.add_widget(RTLLabel(
                text='از:',
                size_hint_x=0.1,
                size_hint_y=None,
                height=dp(40),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            self.perf_from_input = RTLTextInput(
                text=self.performance_from_date,
                multiline=False,
                size_hint_x=0.45,
                size_hint_y=None,
                height=dp(40),
                font_size=sp(18)
            )
            self.perf_from_input.bg_color = (0.15, 0.15, 0.15, 1)
            self.perf_from_input.border_color = (0.3, 0.3, 0.3, 1)
            self.perf_from_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.perf_from_input._hidden_input.foreground_color = (1, 1, 1, 1)
            date_row.add_widget(self.perf_from_input)
            
            date_row.add_widget(RTLLabel(
                text='تا:',
                size_hint_x=0.1,
                size_hint_y=None,
                height=dp(40),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            self.perf_to_input = RTLTextInput(
                text=self.performance_to_date,
                multiline=False,
                size_hint_x=0.45,
                size_hint_y=None,
                height=dp(40),
                font_size=sp(18)
            )
            self.perf_to_input.bg_color = (0.15, 0.15, 0.15, 1)
            self.perf_to_input.border_color = (0.3, 0.3, 0.3, 1)
            self.perf_to_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.perf_to_input._hidden_input.foreground_color = (1, 1, 1, 1)
            date_row.add_widget(self.perf_to_input)
            
            filter_layout.add_widget(date_row)
            
            btn_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(5))
            
            apply_btn = PersianButton(
                text='اعمال فیلتر',
                background_color=(0.2, 0.6, 0.2, 1),
                size_hint_x=0.33,
                size_hint_y=None,
                height=dp(35),
                color=(1, 1, 1, 1),
                font_size=sp(14)
            )
            apply_btn.bind(on_press=self._apply_performance_filter)
            btn_row.add_widget(apply_btn)
            
            clear_btn = PersianButton(
                text='پاک کردن فیلتر',
                background_color=(0.8, 0.4, 0.1, 1),
                size_hint_x=0.33,
                size_hint_y=None,
                height=dp(35),
                color=(1, 1, 1, 1),
                font_size=sp(14)
            )
            clear_btn.bind(on_press=self._clear_performance_filter)
            btn_row.add_widget(clear_btn)
            
            month_btn = PersianButton(
                text='ماه جاری',
                background_color=(0.2, 0.4, 0.8, 1),
                size_hint_x=0.34,
                size_hint_y=None,
                height=dp(35),
                color=(1, 1, 1, 1),
                font_size=sp(14)
            )
            month_btn.bind(on_press=self._set_performance_current_month)
            btn_row.add_widget(month_btn)
            
            filter_layout.add_widget(btn_row)
            
            # ✅ محتوای اصلی
            content_layout = BoxLayout(orientation='vertical')
            
            # اضافه کردن فیلتر به بالا
            content_layout.add_widget(filter_layout)
            
            # ✅ نمایش داده‌ها - پاک کردن قبلی
            data_scroll = ScrollView()
            data_content = GridLayout(cols=1, spacing=dp(8), size_hint_y=None, padding=dp(8))
            data_content.bind(minimum_height=data_content.setter('height'))
            
            # فیلتر کردن تاریخ‌ها
            date_list = list(all_logs.keys())
            filtered_dates = self._filter_dates(
                date_list,
                self.performance_from_date,
                self.performance_to_date
            )
            
            # ✅ ذخیره داده‌های فیلتر شده برای استفاده در خروجی اکسل
            self._current_performance_data = filtered_dates
            
            if not filtered_dates:
                data_content.add_widget(RTLLabel(
                    text='هیچ داده‌ای در بازه انتخابی یافت نشد',
                    size_hint_y=None,
                    height=dp(45),
                    font_size=sp(18),
                    color=(0.5, 0.5, 0.5, 1)
                ))
                data_scroll.add_widget(data_content)
                content_layout.add_widget(data_scroll)
                self.content_area.add_widget(content_layout)
                return
            
            # محاسبه آمار
            total_days = len(filtered_dates)
            total_visits = 0
            total_invoices = 0
            total_units = 0
            total_sales = 0
            total_cash = 0
            total_check = 0
            total_new_customers = 0
            
            for date in filtered_dates:
                if date not in all_logs or not isinstance(all_logs[date], list):
                    continue
                for log in all_logs[date]:
                    if not isinstance(log, dict):
                        continue
                    visit_status = log.get('visit_status', '')
                    sales_status = log.get('sales_status', '')
                    payment_method = log.get('payment_method', '')
                    sales_amount = log.get('sales_amount', 0)
                    units_sold = log.get('units_sold', 0)
                    
                    if visit_status == 'موفق':
                        total_visits += 1
                    if sales_status == 'موفق':
                        total_invoices += 1
                        total_units += units_sold
                        total_sales += sales_amount
                        if payment_method == 'نقد':
                            total_cash += sales_amount
                        elif payment_method == 'چک':
                            total_check += sales_amount
                    if log.get('is_new_customer', False):
                        total_new_customers += 1
            
            data_content.add_widget(RTLLabel(
                text=f'خلاصه عملکرد ({self.performance_from_date} تا {self.performance_to_date})',
                size_hint_y=None,
                height=dp(45),
                font_size=sp(20),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))
            
            row1 = BoxLayout(size_hint_y=None, height=dp(75), spacing=dp(7))
            row1.add_widget(self._make_card('روزهای کاری', f"{total_days:,}", (0.3, 0.6, 0.6, 1)))
            row1.add_widget(self._make_card('کل ویزیت‌ها', f"{total_visits:,}", (0.6, 0.4, 0.8, 1)))
            data_content.add_widget(row1)
            
            row2 = BoxLayout(size_hint_y=None, height=dp(75), spacing=dp(7))
            row2.add_widget(self._make_card('فاکتورها', f"{total_invoices:,}", (0.3, 0.5, 0.7, 1)))
            row2.add_widget(self._make_card('واحد فروش', f"{total_units:,}", (0.5, 0.3, 0.7, 1)))
            data_content.add_widget(row2)
            
            row3 = BoxLayout(size_hint_y=None, height=dp(75), spacing=dp(7))
            row3.add_widget(self._make_card('کل مبلغ فروش', f"{total_sales:,}", (0.2, 0.6, 0.3, 1)))
            row3.add_widget(self._make_card('فروش نقدی', f"{total_cash:,}", (0.2, 0.5, 0.8, 1)))
            data_content.add_widget(row3)
            
            row4 = BoxLayout(size_hint_y=None, height=dp(75), spacing=dp(7))
            row4.add_widget(self._make_card('فروش چکی', f"{total_check:,}", (0.6, 0.3, 0.6, 1)))
            row4.add_widget(self._make_card('مشتری جدید', f"{total_new_customers:,}", (0.2, 0.8, 0.4, 1)))
            data_content.add_widget(row4)
            
            row5 = BoxLayout(size_hint_y=None, height=dp(75), spacing=dp(7))
            avg_sale = total_sales // total_visits if total_visits > 0 else 0
            row5.add_widget(self._make_card('میانگین هر ویزیت', f"{avg_sale:,}", (0.7, 0.4, 0.4, 1)))
            row5.add_widget(Label())
            data_content.add_widget(row5)
            
            data_content.add_widget(RTLLabel(
                text='خلاصه روزانه',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(20),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))
            
            header_box = BoxLayout(size_hint_y=None, height=dp(37), spacing=dp(2))
            headers = ['تاریخ', 'ویزیت', 'فاکتور', 'واحد', 'فروش', 'نقدی', 'چکی', 'مشتری جدید', 'خودآزمایی']
            for i, text in enumerate(headers):
                btn = PersianButton(
                    text=text,
                    size_hint_x=1/len(headers),
                    background_color=(0.2, 0.5, 0.8, 1),
                    color=(1, 1, 1, 1),
                    size_hint_y=None,
                    height=dp(34),
                    font_size=sp(15)
                )
                header_box.add_widget(btn)
            data_content.add_widget(header_box)
            
            # دریافت نمرات خودآزمایی
            summary_file = 'daily_summary.json'
            summary_path = os.path.join(get_data_path(), summary_file)
            self_scores = {}
            if os.path.exists(summary_path):
                all_summaries = load_json(summary_file)
                for date, data in all_summaries.items():
                    if 'self_score' in data:
                        self_scores[date] = data['self_score']
            
            for date in sorted(filtered_dates, reverse=True):
                if date not in all_logs or not isinstance(all_logs[date], list):
                    continue
                    
                day_visits = 0
                day_invoices = 0
                day_units = 0
                day_sales = 0
                day_cash = 0
                day_check = 0
                day_new_customers = 0
                
                for log in all_logs[date]:
                    if not isinstance(log, dict):
                        continue
                    visit_status = log.get('visit_status', '')
                    sales_status = log.get('sales_status', '')
                    payment_method = log.get('payment_method', '')
                    sales_amount = log.get('sales_amount', 0)
                    units_sold = log.get('units_sold', 0)
                    
                    if visit_status == 'موفق':
                        day_visits += 1
                    if sales_status == 'موفق':
                        day_invoices += 1
                        day_units += units_sold
                        day_sales += sales_amount
                        if payment_method == 'نقد':
                            day_cash += sales_amount
                        elif payment_method == 'چک':
                            day_check += sales_amount
                    if log.get('is_new_customer', False):
                        day_new_customers += 1
                
                row = BoxLayout(size_hint_y=None, height=dp(35), spacing=dp(2))
                
                row.add_widget(RTLLabel(
                    text=date,
                    size_hint_x=1/len(headers),
                    font_size=sp(14),
                    color=(1, 1, 1, 1)
                ))
                row.add_widget(RTLLabel(
                    text=f"{day_visits:,}",
                    size_hint_x=1/len(headers),
                    font_size=sp(14),
                    color=(1, 1, 1, 1)
                ))
                row.add_widget(RTLLabel(
                    text=f"{day_invoices:,}",
                    size_hint_x=1/len(headers),
                    font_size=sp(14),
                    color=(1, 1, 1, 1)
                ))
                row.add_widget(RTLLabel(
                    text=f"{day_units:,}",
                    size_hint_x=1/len(headers),
                    font_size=sp(14),
                    color=(1, 1, 1, 1)
                ))
                row.add_widget(RTLLabel(
                    text=f"{day_sales:,}",
                    size_hint_x=1/len(headers),
                    font_size=sp(14),
                    color=(1, 0.8, 0.2, 1)
                ))
                row.add_widget(RTLLabel(
                    text=f"{day_cash:,}",
                    size_hint_x=1/len(headers),
                    font_size=sp(14),
                    color=(0.2, 0.5, 0.8, 1)
                ))
                row.add_widget(RTLLabel(
                    text=f"{day_check:,}",
                    size_hint_x=1/len(headers),
                    font_size=sp(14),
                    color=(0.6, 0.3, 0.6, 1)
                ))
                row.add_widget(RTLLabel(
                    text=f"{day_new_customers:,}",
                    size_hint_x=1/len(headers),
                    font_size=sp(14),
                    color=(0.2, 0.8, 0.4, 1)
                ))
                
                # ستون خودآزمایی
                score = self_scores.get(date, '')
                score_text = str(score) if score != '' else '—'
                score_color = (0.2, 0.8, 0.4, 1) if score != '' else (0.3, 0.3, 0.3, 1)
                row.add_widget(RTLLabel(
                    text=score_text,
                    size_hint_x=1/len(headers),
                    font_size=sp(14),
                    color=score_color
                ))
                
                data_content.add_widget(row)
            
            data_scroll.add_widget(data_content)
            content_layout.add_widget(data_scroll)
            
            self.content_area.add_widget(content_layout)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش عملکرد کلی: {e}", error_details)
    
    def _apply_performance_filter(self, instance):
        try:
            from_date = self.perf_from_input.text.strip()
            to_date = self.perf_to_input.text.strip()
            
            if from_date:
                self.performance_from_date = from_date
            if to_date:
                self.performance_to_date = to_date
            
            self.refresh_stats(None)
        except Exception as e:
            ErrorPopup.show_error(f"خطا در اعمال فیلتر: {e}")

    def _clear_performance_filter(self, instance):
        try:
            self.performance_from_date = self._get_first_day_of_month()
            self.performance_to_date = get_today_jalali()
            self.perf_from_input.text = self.performance_from_date
            self.perf_to_input.text = self.performance_to_date
            
            self.refresh_stats(None)
        except Exception as e:
            ErrorPopup.show_error(f"خطا در پاک کردن فیلتر: {e}")

    def _set_performance_current_month(self, instance):
        try:
            self.performance_from_date = self._get_first_day_of_month()
            self.performance_to_date = get_today_jalali()
            self.perf_from_input.text = self.performance_from_date
            self.perf_to_input.text = self.performance_to_date
            
            self.refresh_stats(None)
        except Exception as e:
            ErrorPopup.show_error(f"خطا در تنظیم ماه جاری: {e}")
    
    # ============================================================
    # تب ریز عملکرد
    # ============================================================
    
    def show_detail_tab(self):
        try:
            all_logs = get_daily_logs()
            
            today = get_today_jalali()
            if not self.detail_from_date:
                self.detail_from_date = today
            if not self.detail_to_date:
                self.detail_to_date = today
            
            filter_layout = BoxLayout(
                orientation='vertical',
                size_hint_y=None,
                height=dp(120),
                spacing=dp(5),
                padding=dp(5)
            )
            filter_layout.add_widget(RTLLabel(
                text='فیلتر بازه زمانی:',
                size_hint_y=None,
                height=dp(25),
                font_size=sp(14),
                color=(0.4, 0.7, 1, 1),
                bold=True
            ))
            
            date_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))
            
            date_row.add_widget(RTLLabel(
                text='از:',
                size_hint_x=0.1,
                size_hint_y=None,
                height=dp(40),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            self.detail_from_input = RTLTextInput(
                text=self.detail_from_date,
                multiline=False,
                size_hint_x=0.45,
                size_hint_y=None,
                height=dp(40),
                font_size=sp(18)
            )
            self.detail_from_input.bg_color = (0.15, 0.15, 0.15, 1)
            self.detail_from_input.border_color = (0.3, 0.3, 0.3, 1)
            self.detail_from_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.detail_from_input._hidden_input.foreground_color = (1, 1, 1, 1)
            date_row.add_widget(self.detail_from_input)
            
            date_row.add_widget(RTLLabel(
                text='تا:',
                size_hint_x=0.1,
                size_hint_y=None,
                height=dp(40),
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            self.detail_to_input = RTLTextInput(
                text=self.detail_to_date,
                multiline=False,
                size_hint_x=0.45,
                size_hint_y=None,
                height=dp(40),
                font_size=sp(18)
            )
            self.detail_to_input.bg_color = (0.15, 0.15, 0.15, 1)
            self.detail_to_input.border_color = (0.3, 0.3, 0.3, 1)
            self.detail_to_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.detail_to_input._hidden_input.foreground_color = (1, 1, 1, 1)
            date_row.add_widget(self.detail_to_input)
            
            filter_layout.add_widget(date_row)
            
            btn_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(5))
            
            apply_btn = PersianButton(
                text='اعمال فیلتر',
                background_color=(0.2, 0.6, 0.2, 1),
                size_hint_x=0.33,
                size_hint_y=None,
                height=dp(35),
                color=(1, 1, 1, 1),
                font_size=sp(14)
            )
            apply_btn.bind(on_press=self._apply_detail_filter)
            btn_row.add_widget(apply_btn)
            
            today_btn = PersianButton(
                text='امروز',
                background_color=(0.2, 0.4, 0.8, 1),
                size_hint_x=0.33,
                size_hint_y=None,
                height=dp(35),
                color=(1, 1, 1, 1),
                font_size=sp(14)
            )
            today_btn.bind(on_press=self._set_detail_today)
            btn_row.add_widget(today_btn)
            
            clear_btn = PersianButton(
                text='پاک کردن',
                background_color=(0.8, 0.4, 0.1, 1),
                size_hint_x=0.34,
                size_hint_y=None,
                height=dp(35),
                color=(1, 1, 1, 1),
                font_size=sp(14)
            )
            clear_btn.bind(on_press=self._clear_detail_filter)
            btn_row.add_widget(clear_btn)
            
            filter_layout.add_widget(btn_row)
            
            content_layout = BoxLayout(orientation='vertical')
            content_layout.add_widget(filter_layout)
            
            layout = ScrollView()
            data_content = GridLayout(cols=1, spacing=dp(4), size_hint_y=None, padding=dp(8))
            data_content.bind(minimum_height=data_content.setter('height'))
            
            visit_list = []
            for date, logs in all_logs.items():
                if self.detail_from_date and date < self.detail_from_date:
                    continue
                if self.detail_to_date and date > self.detail_to_date:
                    continue
                    
                if not isinstance(logs, list):
                    continue
                for log in logs:
                    if not isinstance(log, dict):
                        continue
                    visit_list.append({
                        'date': date,
                        'route': log.get('route', ''),
                        'customer': log.get('customer', ''),
                        'visit_status': log.get('visit_status', ''),
                        'sales_status': log.get('sales_status', ''),
                        'time': log.get('time', ''),
                        'units_sold': log.get('units_sold', 0),
                        'sales_amount': log.get('sales_amount', 0),
                        'payment_method': log.get('payment_method', ''),
                        'fail_reason': log.get('fail_reason', ''),
                        'fail_sales_reason': log.get('fail_sales_reason', ''),
                        'is_new_customer': log.get('is_new_customer', False)
                    })
            
            range_text = f"از {self.detail_from_date} تا {self.detail_to_date}" if self.detail_from_date and self.detail_to_date else today
            data_content.add_widget(RTLLabel(
                text=f'ریز عملکرد ({range_text})',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(22),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))
            
            if not visit_list:
                data_content.add_widget(RTLLabel(
                    text='هیچ ویزیتی در بازه انتخابی یافت نشد',
                    size_hint_y=None,
                    height=dp(35),
                    font_size=sp(16),
                    color=(0.5, 0.5, 0.5, 1)
                ))
                layout.add_widget(data_content)
                content_layout.add_widget(layout)
                self.content_area.add_widget(content_layout)
                return
            
            header_box = BoxLayout(size_hint_y=None, height=dp(37), spacing=dp(2))
            headers = ['تاریخ', 'مسیر', 'مشتری', 'ویزیت', 'فروش', 'ساعت', 'جدید']
            for i, text in enumerate(headers):
                btn = PersianButton(
                    text=text,
                    size_hint_x=1/len(headers),
                    background_color=(0.2, 0.5, 0.8, 1),
                    color=(1, 1, 1, 1),
                    size_hint_y=None,
                    height=dp(34),
                    font_size=sp(15)
                )
                header_box.add_widget(btn)
            data_content.add_widget(header_box)
            
            for item in sorted(visit_list, key=lambda x: (x['date'], x['time']), reverse=True):
                row = BoxLayout(size_hint_y=None, height=dp(35), spacing=dp(2))
                
                row.add_widget(RTLLabel(
                    text=item['date'],
                    size_hint_x=1/len(headers),
                    font_size=sp(14),
                    color=(1, 1, 1, 1)
                ))
                row.add_widget(RTLLabel(
                    text=item['route'],
                    size_hint_x=1/len(headers),
                    font_size=sp(14),
                    color=(1, 1, 1, 1)
                ))
                row.add_widget(RTLLabel(
                    text=item['customer'],
                    size_hint_x=1/len(headers),
                    font_size=sp(14),
                    color=(1, 1, 1, 1)
                ))
                
                visit_color = (0.2, 0.7, 0.2, 1) if item['visit_status'] == 'موفق' else (0.8, 0.3, 0.3, 1)
                row.add_widget(RTLLabel(
                    text=item['visit_status'],
                    size_hint_x=1/len(headers),
                    font_size=sp(14),
                    color=visit_color
                ))
                
                if item['sales_status'] == 'موفق':
                    sales_color = (0.2, 0.7, 0.2, 1)
                    sales_text = 'موفق'
                elif item['sales_status'] == 'ناموفق':
                    sales_color = (0.8, 0.5, 0.2, 1)
                    sales_text = 'ناموفق'
                else:
                    sales_color = (0.5, 0.5, 0.5, 1)
                    sales_text = '---'
                row.add_widget(RTLLabel(
                    text=sales_text,
                    size_hint_x=1/len(headers),
                    font_size=sp(14),
                    color=sales_color
                ))
                
                row.add_widget(RTLLabel(
                    text=item['time'],
                    size_hint_x=1/len(headers),
                    font_size=sp(14),
                    color=(1, 1, 1, 1)
                ))
                
                new_customer_text = '✅' if item['is_new_customer'] else '—'
                new_customer_color = (0.2, 0.8, 0.4, 1) if item['is_new_customer'] else (0.3, 0.3, 0.3, 1)
                row.add_widget(RTLLabel(
                    text=new_customer_text,
                    size_hint_x=1/len(headers),
                    font_size=sp(14),
                    color=new_customer_color
                ))
                
                data_content.add_widget(row)
            
            layout.add_widget(data_content)
            content_layout.add_widget(layout)
            
            self.content_area.add_widget(content_layout)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش ریز عملکرد: {e}", error_details)
    
    def _apply_detail_filter(self, instance):
        try:
            from_date = self.detail_from_input.text.strip()
            to_date = self.detail_to_input.text.strip()
            
            if from_date:
                self.detail_from_date = from_date
            if to_date:
                self.detail_to_date = to_date
            
            self.refresh_stats(None)
        except Exception as e:
            ErrorPopup.show_error(f"خطا در اعمال فیلتر: {e}")

    def _set_detail_today(self, instance):
        try:
            today = get_today_jalali()
            self.detail_from_date = today
            self.detail_to_date = today
            self.detail_from_input.text = today
            self.detail_to_input.text = today
            
            self.refresh_stats(None)
        except Exception as e:
            ErrorPopup.show_error(f"خطا در تنظیم امروز: {e}")

    def _clear_detail_filter(self, instance):
        try:
            today = get_today_jalali()
            self.detail_from_date = today
            self.detail_to_date = today
            self.detail_from_input.text = today
            self.detail_to_input.text = today
            
            self.refresh_stats(None)
        except Exception as e:
            ErrorPopup.show_error(f"خطا در پاک کردن فیلتر: {e}")
    
    # ============================================================
    # تب آمار و ارزیابی
    # ============================================================
    
    def show_stats_tab(self):
        try:
            layout = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
            
            layout.add_widget(RTLLabel(
                text='آمار و ارزیابی عملکرد',
                size_hint_y=None,
                height=dp(45),
                font_size=sp(22),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))
            
            btn_layout = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(10))
            
            daily_btn = PersianButton(
                text='ارزیابی روز جاری',
                background_color=(0.2, 0.5, 0.8, 1),
                size_hint_x=0.5,
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            daily_btn.bind(on_press=self.show_daily_evaluation)
            btn_layout.add_widget(daily_btn)
            
            period_btn = PersianButton(
                text='ارزیابی دوره',
                background_color=(0.2, 0.6, 0.2, 1),
                size_hint_x=0.5,
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            period_btn.bind(on_press=self.show_period_evaluation)
            btn_layout.add_widget(period_btn)
            
            layout.add_widget(btn_layout)
            
            btn_layout2 = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(10))
            
            history_btn = PersianButton(
                text='تاریخچه گزارشات',
                background_color=(0.2, 0.5, 0.7, 1),
                size_hint_x=1,
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            history_btn.bind(on_press=self.show_history_dialog)
            btn_layout2.add_widget(history_btn)
            
            layout.add_widget(btn_layout2)
            
            self.content_area.add_widget(layout)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش آمار و ارزیابی: {e}", error_details)
    
    # ============================================================
    # دیالوگ تاریخچه گزارشات
    # ============================================================
    
    def show_history_dialog(self, instance):
        try:
            excel_files = get_excel_files_info(limit=50)
            
            content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
            with content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                           size=lambda i, v: setattr(content_rect, 'size', v))
            
            stats = get_file_stats()
            title_text = 'تاریخچه گزارشات'
            if stats['count'] > 0:
                title_text += f' ({stats["count"]} فایل - {stats["total_size_mb"]} MB)'
            
            content.add_widget(RTLLabel(
                text=title_text,
                size_hint_y=None,
                height=dp(35),
                font_size=sp(18),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))
            
            if not excel_files:
                content.add_widget(RTLLabel(
                    text='هیچ فایل گزارشی یافت نشد',
                    size_hint_y=None,
                    height=dp(40),
                    font_size=sp(16),
                    color=(0.5, 0.5, 0.5, 1)
                ))
            else:
                scroll = ScrollView(
                    do_scroll_x=False,
                    do_scroll_y=True,
                    size_hint_y=0.6
                )
                
                list_content = GridLayout(
                    cols=1,
                    spacing=dp(4),
                    size_hint_y=None,
                    padding=dp(5)
                )
                list_content.bind(minimum_height=list_content.setter('height'))
                
                self.selected_files = {}
                
                for file_info in excel_files:
                    file_box = BoxLayout(
                        size_hint_y=None,
                        height=dp(45),
                        spacing=dp(5),
                        padding=[dp(5), dp(2), dp(5), dp(2)]
                    )
                    
                    check = CheckBox(
                        size_hint_x=0.1,
                        size_hint_y=None,
                        height=dp(40),
                        color=(0.4, 0.7, 1, 1)
                    )
                    check.active = False
                    check.bind(active=lambda checkbox, value, fp=file_info['path']: self._toggle_file_selection(fp, value))
                    file_box.add_widget(check)
                    
                    self.selected_files[file_info['path']] = False
                    
                    file_label = RTLLabel(
                        text=f"{file_info['date']} ({file_info['size_kb']} KB)",
                        size_hint_x=0.6,
                        size_hint_y=None,
                        height=dp(40),
                        font_size=sp(14),
                        color=(1, 1, 1, 1),
                        halign='right'
                    )
                    file_box.add_widget(file_label)
                    
                    send_btn = PersianButton(
                        text='ارسال',
                        size_hint_x=0.3,
                        size_hint_y=None,
                        height=dp(35),
                        background_color=(0.2, 0.6, 0.2, 1),
                        color=(1, 1, 1, 1),
                        font_size=sp(14)
                    )
                    send_btn.bind(on_press=lambda x, fp=file_info['path']: self._share_file(fp))
                    file_box.add_widget(send_btn)
                    
                    list_content.add_widget(file_box)
                
                scroll.add_widget(list_content)
                content.add_widget(scroll)
            
            btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
            
            select_all_btn = PersianButton(
                text=' انتخاب همه',
                background_color=(0.2, 0.5, 0.8, 1),
                size_hint_x=0.25,
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(14)
            )
            select_all_btn.bind(on_press=self._select_all_files)
            btn_layout.add_widget(select_all_btn)
            
            delete_selected_btn = PersianButton(
                text=' حذف انتخابی',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_x=0.25,
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(14)
            )
            delete_selected_btn.bind(on_press=self._delete_selected_files)
            btn_layout.add_widget(delete_selected_btn)
            
            clean_old_btn = PersianButton(
                text=' حذف قدیمی‌ها',
                background_color=(0.7, 0.4, 0.1, 1),
                size_hint_x=0.25,
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(14)
            )
            clean_old_btn.bind(on_press=self._clean_old_files)
            btn_layout.add_widget(clean_old_btn)
            
            folder_btn = PersianButton(
                text=' باز کردن',
                background_color=(0.2, 0.5, 0.7, 1),
                size_hint_x=0.25,
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(14)
            )
            folder_btn.bind(on_press=self._open_backup_folder)
            btn_layout.add_widget(folder_btn)
            
            content.add_widget(btn_layout)
            
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
                title='',
                title_size=0,
                content=content,
                size_hint=(0.92, 0.75),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )
            
            self.history_popup = popup
            
            close_btn.bind(on_press=popup.dismiss)
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش تاریخچه: {e}", error_details)
    
    # ============================================================
    # توابع مدیریت انتخاب و حذف فایل‌ها
    # ============================================================
    
    def _toggle_file_selection(self, file_path, value):
        if hasattr(self, 'selected_files'):
            self.selected_files[file_path] = value
    
    def _select_all_files(self, instance):
        if not hasattr(self, 'selected_files') or not self.selected_files:
            self.show_message('توجه', 'هیچ فایلی برای انتخاب وجود ندارد')
            return
        
        for path in self.selected_files.keys():
            self.selected_files[path] = True
        
        self._update_checkboxes(True)
        
        self.show_message('توجه', f'{len(self.selected_files)} فایل انتخاب شد')
    
    def _update_checkboxes(self, value):
        try:
            if hasattr(self, 'history_popup') and self.history_popup:
                popup = self.history_popup
                for child in popup.content.children:
                    if hasattr(child, 'children'):
                        for box in child.children:
                            if hasattr(box, 'children'):
                                for item in box.children:
                                    if isinstance(item, CheckBox):
                                        item.active = value
        except Exception as e:
            print(f"خطا در به‌روزرسانی چک‌باکس‌ها: {e}")
    
    def _delete_selected_files(self, instance):
        try:
            selected = [path for path, selected in self.selected_files.items() if selected]
            
            if not selected:
                self.show_message('توجه', 'هیچ فایلی انتخاب نشده است')
                return
            
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            
            content.add_widget(RTLLabel(
                text=f'آیا از حذف {len(selected)} فایل انتخاب شده اطمینان دارید؟',
                size_hint_y=None,
                height=dp(50),
                font_size=sp(18),
                color=(1, 1, 1, 1)
            ))
            
            scroll = ScrollView(size_hint_y=0.4, do_scroll_x=False)
            list_content = GridLayout(cols=1, spacing=dp(2), size_hint_y=None)
            list_content.bind(minimum_height=list_content.setter('height'))
            
            for path in selected[:10]:
                list_content.add_widget(RTLLabel(
                    text=os.path.basename(path),
                    size_hint_y=None,
                    height=dp(25),
                    font_size=sp(14),
                    color=(0.5, 0.5, 0.5, 1)
                ))
            
            if len(selected) > 10:
                list_content.add_widget(RTLLabel(
                    text=f'... و {len(selected) - 10} فایل دیگر',
                    size_hint_y=None,
                    height=dp(25),
                    font_size=sp(14),
                    color=(0.5, 0.5, 0.5, 1)
                ))
            
            scroll.add_widget(list_content)
            content.add_widget(scroll)
            
            btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
            
            confirm_btn = PersianButton(
                text='حذف',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_x=0.5,
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            
            cancel_btn = PersianButton(
                text='انصراف',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_x=0.5,
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            
            btn_layout.add_widget(confirm_btn)
            btn_layout.add_widget(cancel_btn)
            content.add_widget(btn_layout)
            
            popup = PersianPopup(
                title='',
                title_size=0,
                content=content,
                size_hint=(0.85, 0.6),
                auto_dismiss=True
            )
            
            def do_delete(instance):
                popup.dismiss()
                def delete_thread():
                    deleted, failed = delete_files(selected)
                    Clock.schedule_once(lambda dt: self._on_delete_complete(deleted, failed), 0.1)
                
                thread = threading.Thread(target=delete_thread, daemon=True)
                thread.start()
            
            confirm_btn.bind(on_press=do_delete)
            cancel_btn.bind(on_press=popup.dismiss)
            
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در حذف فایل‌ها: {e}", error_details)
    
    def _on_delete_complete(self, deleted, failed):
        try:
            message = f"{deleted} فایل با موفقیت حذف شد"
            if failed > 0:
                message += f"\n{failed} فایل حذف نشد"
            
            self.show_message('نتیجه حذف', message)
            
            if hasattr(self, 'history_popup'):
                try:
                    self.history_popup.dismiss()
                except:
                    pass
            
            Clock.schedule_once(lambda dt: self.show_history_dialog(None), 0.3)
            
        except Exception as e:
            print(f"خطا در نمایش نتیجه حذف: {e}")
    
    def _clean_old_files(self, instance):
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            
            content.add_widget(RTLLabel(
                text='آیا از حذف فایل‌های قدیمی‌تر از ۳۰ روز اطمینان دارید؟',
                size_hint_y=None,
                height=dp(50),
                font_size=sp(18),
                color=(1, 1, 1, 1)
            ))
            
            stats = get_file_stats()
            if stats['count'] > 0:
                content.add_widget(RTLLabel(
                    text=f'تعداد کل: {stats["count"]} فایل\nحجم کل: {stats["total_size_mb"]} MB',
                    size_hint_y=None,
                    height=dp(50),
                    font_size=sp(14),
                    color=(0.5, 0.5, 0.5, 1)
                ))
            
            btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
            
            confirm_btn = PersianButton(
                text='بله، پاکسازی کن',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_x=0.5,
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            
            cancel_btn = PersianButton(
                text='انصراف',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_x=0.5,
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            
            btn_layout.add_widget(confirm_btn)
            btn_layout.add_widget(cancel_btn)
            content.add_widget(btn_layout)
            
            popup = PersianPopup(
                title='',
                title_size=0,
                content=content,
                size_hint=(0.85, 0.5),
                auto_dismiss=True
            )
            
            def do_clean(instance):
                popup.dismiss()
                def clean_thread():
                    deleted, failed = delete_old_files(days=30)
                    Clock.schedule_once(
                        lambda dt: self._on_clean_complete(deleted, failed), 0.1
                    )
                
                thread = threading.Thread(target=clean_thread, daemon=True)
                thread.start()
            
            confirm_btn.bind(on_press=do_clean)
            cancel_btn.bind(on_press=popup.dismiss)
            
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در پاکسازی: {e}", error_details)
    
    def _on_clean_complete(self, deleted, failed):
        try:
            if deleted > 0:
                message = f'{deleted} فایل قدیمی حذف شد'
                if failed > 0:
                    message += f'\n{failed} فایل حذف نشد'
                self.show_message('پاکسازی انجام شد', message)
            else:
                self.show_message('پاکسازی انجام شد', 'هیچ فایل قدیمی یافت نشد')
            
            if hasattr(self, 'history_popup'):
                try:
                    self.history_popup.dismiss()
                except:
                    pass
            
            Clock.schedule_once(lambda dt: self.show_history_dialog(None), 0.3)
            
        except Exception as e:
            print(f"خطا در نمایش نتیجه پاکسازی: {e}")
    
    def _open_backup_folder(self, instance):
        try:
            from utils.storage import get_backup_path
            from kivy.utils import platform
            
            backup_path = get_backup_path()
            if not os.path.exists(backup_path):
                self.show_message('خطا', 'پوشه بکاپ وجود ندارد')
                return
            
            if platform == 'android':
                try:
                    from android import mActivity
                    from jnius import autoclass
                    
                    Intent = autoclass('android.content.Intent')
                    Uri = autoclass('android.net.Uri')
                    File = autoclass('java.io.File')
                    
                    uri = Uri.fromFile(File(backup_path))
                    intent = Intent(Intent.ACTION_VIEW)
                    intent.setDataAndType(uri, 'resource/folder')
                    intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    mActivity.startActivity(intent)
                    
                except Exception as e:
                    self.show_message('مسیر پوشه', f'پوشه بکاپ:{backup_path}')
            else:
                import subprocess
                if platform == 'win':
                    os.startfile(backup_path)
                elif platform == 'linux':
                    subprocess.Popen(['xdg-open', backup_path])
                elif platform == 'macosx':
                    subprocess.Popen(['open', backup_path])
                    
        except Exception as e:
            ErrorPopup.show_error(f"خطا در باز کردن پوشه: {e}")
    
    # ============================================================
    # ارسال فایل
    # ============================================================
    
    def _share_file(self, file_path):
        try:
            from kivy.utils import platform
            import os
            
            if platform == 'android':
                try:
                    from android import mActivity
                    from jnius import autoclass
                    
                    Intent = autoclass('android.content.Intent')
                    Uri = autoclass('android.net.Uri')
                    File = autoclass('java.io.File')
                    
                    file = File(file_path)
                    if not file.exists():
                        ErrorPopup.show_error('فایل وجود ندارد')
                        return
                    
                    uri = Uri.fromFile(file)
                    intent = Intent(Intent.ACTION_VIEW)
                    intent.setDataAndType(uri, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                    intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    
                    mActivity.startActivity(intent)
                    
                except Exception as e:
                    print(f"Intent method failed: {e}")
                    self.show_message('مسیر فایل', f'مسیر ذخیره: {file_path}')
                    
            else:
                import subprocess
                folder_path = os.path.dirname(file_path)
                
                if platform == 'win':
                    os.startfile(folder_path)
                elif platform == 'linux':
                    subprocess.Popen(['xdg-open', folder_path])
                elif platform == 'macosx':
                    subprocess.Popen(['open', folder_path])
                else:
                    self.show_message('مسیر فایل', f'مسیر ذخیره:{file_path}')
                    
        except Exception as e:
            print(f"خطا در ارسال فایل: {e}")
            import traceback
            traceback.print_exc()
            self.show_message('مسیر فایل', f'مسیر ذخیره: {file_path}')

    # ============================================================
    # دیالوگ ارزیابی روز جاری
    # ============================================================
    
    def show_daily_evaluation(self, instance):
        try:
            # ✅ جلوگیری از اجرای همزمان
            if self._is_processing:
                return
            
            self._is_processing = True
            
            today = get_today_jalali()
            self.current_evaluation_date = today
            
            # ✅ بازنشانی فلگ خودآزمایی
            self._self_assessment_shown = False
            
            self._show_evaluation_dialog(today, today)
            
            # ✅ بازنشانی بعد از اتمام
            Clock.schedule_once(lambda dt: setattr(self, '_is_processing', False), 1)
            
        except Exception as e:
            self._is_processing = False
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش ارزیابی روز: {e}", error_details)
        
    # ============================================================
    # دیالوگ ارزیابی دوره
    # ============================================================
        
    def show_period_evaluation(self, instance):
        try:
            # ✅ تنظیم current_evaluation_date به None برای ارزیابی دوره
            self.current_evaluation_date = None
            
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            with content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                            size=lambda i, v: setattr(content_rect, 'size', v))
            
            content.add_widget(RTLLabel(
                text='انتخاب بازه زمانی',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(18),
                bold=True,
                color=(1, 1, 1, 1)
            ))
            
            date_layout = BoxLayout(size_hint_y=None, height=dp(80), spacing=dp(10))
            
            date_layout.add_widget(RTLLabel(
                text='از تاریخ:',
                size_hint_x=0.5,
                size_hint_y=None,
                height=dp(50),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))
            from_date_input = RTLTextInput(
                text=get_today_jalali(),
                size_hint_x=1,
                size_hint_y=None,
                height=dp(80),
                font_size=sp(28)
            )
            from_date_input.bg_color = (0.15, 0.15, 0.15, 1)
            from_date_input.border_color = (0.3, 0.3, 0.3, 1)
            from_date_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            from_date_input._hidden_input.foreground_color = (1, 1, 1, 1)
            from_date_input._hidden_input.bind(focus=self._on_field_focus)
            date_layout.add_widget(from_date_input)
            
            date_layout.add_widget(RTLLabel(
                text='تا تاریخ:',
                size_hint_x=0.5,
                size_hint_y=None,
                height=dp(50),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))
            to_date_input = RTLTextInput(
                text=get_today_jalali(),
                size_hint_x=1,
                size_hint_y=None,
                height=dp(80),
                font_size=sp(28)
            )
            to_date_input.bg_color = (0.15, 0.15, 0.15, 1)
            to_date_input.border_color = (0.3, 0.3, 0.3, 1)
            to_date_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            to_date_input._hidden_input.foreground_color = (1, 1, 1, 1)
            to_date_input._hidden_input.bind(focus=self._on_field_focus)
            date_layout.add_widget(to_date_input)
            
            content.add_widget(date_layout)
            
            btn_layout = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(10))
            
            confirm_btn = PersianButton(
                text='نمایش ارزیابی',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_x=0.5,
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            cancel_btn = PersianButton(
                text='انصراف',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_x=0.5,
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            
            btn_layout.add_widget(confirm_btn)
            btn_layout.add_widget(cancel_btn)
            content.add_widget(btn_layout)
            
            popup = Popup(
                title='',
                content=content,
                size_hint=(0.9, 0.5),
                auto_dismiss=False,
                background_color=(0.08, 0.08, 0.08, 1)
            )
            popup.title_size = 0
            popup.title_color = (0, 0, 0, 0)
            popup.separator_height = 0
            
            def on_confirm(instance):
                from_date = from_date_input.text.strip()
                to_date = to_date_input.text.strip()
                if not from_date or not to_date:
                    ErrorPopup.show_error('لطفاً هر دو تاریخ را وارد کنید')
                    return
                popup.dismiss()
                self._show_evaluation_dialog(from_date, to_date)
            
            def on_cancel(instance):
                popup.dismiss()
            
            confirm_btn.bind(on_press=on_confirm)
            cancel_btn.bind(on_press=on_cancel)
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش ارزیابی دوره: {e}", error_details)
        
    # ============================================================
    # نمایش دیالوگ ارزیابی
    # ============================================================
    
    def _show_evaluation_dialog(self, from_date, to_date):
        """نمایش دیالوگ ارزیابی با فرمول‌های جدید"""
        try:
            all_logs = get_daily_logs()
            settings = get_settings()
            
            supervision_rate = settings.get('supervision_rate', 70.0) / 100
            conversion_rate = settings.get('conversion_rate', 75.0) / 100
            min_daily_hours = settings.get('min_daily_hours', 7)
            
            target_new_customer = settings.get('target_new_customer_count', 0)
            target_units = settings.get('target_count', 100)
            target_sales = settings.get('target_amount', 50000000)
            target_cash = settings.get('target_cash_sales', 30000000)
            target_check = settings.get('target_credit_sales', 20000000)
            
            date_list = []
            for date in all_logs.keys():
                if from_date <= date <= to_date:
                    date_list.append(date)
            
            if not date_list:
                self.show_message('اطلاع', 'هیچ داده‌ای در بازه انتخابی وجود ندارد')
                return
            
            routes_in_period = set()
            for date in date_list:
                if date in all_logs and isinstance(all_logs[date], list):
                    for log in all_logs[date]:
                        route = log.get('route', '')
                        if route:
                            routes_in_period.add(route)
            
            all_customers = get_customers()
            total_customers_in_period = 0
            
            for route in routes_in_period:
                count = 0
                for c in all_customers:
                    if c.get('route_name', '').strip() == route.strip():
                        count += 1
                total_customers_in_period += count
            
            target_visits = int(total_customers_in_period * supervision_rate)
            target_invoices = int(target_visits * conversion_rate)
            target_credit = target_sales - (target_cash + target_check)
            
            day_count = len(date_list)
            target_visits_day = target_visits * day_count
            target_invoices_day = target_invoices * day_count
            target_units_day = target_units * day_count
            target_sales_day = target_sales * day_count
            target_cash_day = target_cash * day_count
            target_check_day = target_check * day_count
            target_credit_day = target_credit * day_count
            target_new_customer_day = target_new_customer * day_count
            
            total_visits = 0
            total_invoices = 0
            total_units = 0
            total_sales = 0
            total_cash = 0
            total_check = 0
            total_credit = 0
            total_new_customers = 0
            
            for date in date_list:
                if date in all_logs and isinstance(all_logs[date], list):
                    for log in all_logs[date]:
                        if not isinstance(log, dict):
                            continue
                        
                        visit_status = log.get('visit_status', '')
                        sales_status = log.get('sales_status', '')
                        payment_method = log.get('payment_method', '')
                        sales_amount = log.get('sales_amount', 0)
                        units_sold = log.get('units_sold', 0)
                        
                        if visit_status == 'موفق':
                            total_visits += 1
                        
                        if sales_status == 'موفق':
                            total_invoices += 1
                            total_units += units_sold
                            total_sales += sales_amount
                            
                            if payment_method == 'نقد':
                                total_cash += sales_amount
                            elif payment_method == 'چک':
                                total_check += sales_amount
                            elif payment_method == 'اعتباری':
                                total_credit += sales_amount
                        
                        if log.get('is_new_customer', False):
                            total_new_customers += 1
            
            items = [
                {'name': 'تعداد ویزیت', 'target': target_visits_day, 'actual': total_visits},
                {'name': 'تعداد فاکتور', 'target': target_invoices_day, 'actual': total_invoices},
                {'name': 'واحد فروش', 'target': target_units_day, 'actual': total_units},
                {'name': 'مبلغ فروش', 'target': target_sales_day, 'actual': total_sales},
                {'name': 'فروش نقدی', 'target': target_cash_day, 'actual': total_cash},
                {'name': 'فروش چکی', 'target': target_check_day, 'actual': total_check},
                {'name': 'فروش اعتباری', 'target': target_credit_day, 'actual': total_credit},
                {'name': 'مشتری جدید', 'target': target_new_customer_day, 'actual': total_new_customers},
            ]
            
            content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
            with content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                            size=lambda i, v: setattr(content_rect, 'size', v))
            
            
            table_container = BoxLayout(
                orientation='vertical',
                size_hint_y=0.75,
                spacing=dp(2),
                padding=dp(3)
            )
            
            header_box = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(2))
            headers = ['آيتم', 'هدف', 'عملكرد', 'نتیجه']
            for header in headers:
                header_box.add_widget(RTLLabel(
                    text=header,
                    size_hint_x=1/len(headers),
                    size_hint_y=None,
                    height=dp(34),
                    font_size=sp(22),
                    bold=True,
                    color=(0.4, 0.7, 1, 1),
                    halign='center'
                ))
            table_container.add_widget(header_box)
            
            table_scroll = ScrollView(
                do_scroll_x=False,
                do_scroll_y=True,
                size_hint_y=1
            )
            
            rows_content = GridLayout(
                cols=1,
                spacing=dp(2),
                size_hint_y=None,
                padding=dp(2)
            )
            rows_content.bind(minimum_height=rows_content.setter('height'))
            
            for item in items:
                row = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(2))
                
                diff = item['actual'] - item['target']
                diff_str = f"{diff:,}"
                diff_color = (1, 0.3, 0.3, 1) if diff < 0 else (0.3, 0.8, 0.3, 1)
                
                row.add_widget(RTLLabel(
                    text=item['name'],
                    size_hint_x=1/len(headers),
                    size_hint_y=None,
                    height=dp(28),
                    font_size=sp(20),
                    color=(1, 1, 1, 1),
                    halign='right'
                ))
                row.add_widget(RTLLabel(
                    text="{:,}".format(item['target']),
                    size_hint_x=1/len(headers),
                    size_hint_y=None,
                    height=dp(28),
                    font_size=sp(20),
                    color=(1, 1, 1, 1),
                    halign='center'
                ))
                row.add_widget(RTLLabel(
                    text="{:,}".format(item['actual']),
                    size_hint_x=1/len(headers),
                    size_hint_y=None,
                    height=dp(28),
                    font_size=sp(20),
                    color=(1, 1, 1, 1),
                    halign='center'
                ))
                row.add_widget(RTLLabel(
                    text=diff_str,
                    size_hint_x=1/len(headers),
                    size_hint_y=None,
                    height=dp(28),
                    font_size=sp(20),
                    color=diff_color,
                    halign='center'
                ))
                
                rows_content.add_widget(row)
            
            table_scroll.add_widget(rows_content)
            table_container.add_widget(table_scroll)
            content.add_widget(table_container)
            
            eval_btn = PersianButton(
                text='ارزيابي',
                background_color=(0.2, 0.6, 1, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(18),
                bold=True
            )
            content.add_widget(eval_btn)
            
            btn_layout = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(10))
            close_btn = PersianButton(
                text='بستن',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_x=1,
                size_hint_y=None,
                height=dp(40),
                color=(1, 1, 1, 1),
                font_size=sp(15)
            )
            btn_layout.add_widget(close_btn)
            content.add_widget(btn_layout)
            
            popup = Popup(
                title='',
                content=content,
                size_hint=(0.92, 0.85),
                auto_dismiss=False,
                background_color=(0.08, 0.08, 0.08, 1)
            )
            popup.title_size = 0
            popup.title_color = (0, 0, 0, 0)
            popup.separator_height = 0
            
            eval_btn.bind(on_press=lambda x: self._show_evaluation_result(items, date_list, all_logs, popup))
            close_btn.bind(on_press=lambda x: popup.dismiss())
            
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش ارزیابی: {e}", error_details)
    
    # ============================================================
    # نمایش نتیجه ارزیابی
    # ============================================================
    
    def _show_evaluation_result(self, items, date_list, all_logs, parent_popup=None):
        """نمایش دیالوگ جداگانه برای جزئیات ارزیابی"""
        try:
            # ✅ بستن پاپ‌آپ والد
            if parent_popup and hasattr(parent_popup, 'dismiss'):
                try:
                    parent_popup.dismiss()
                except:
                    pass

            from utils.jalali_date import get_today_jalali
            settings = get_settings()
            
            target_clock_in = settings.get('work_start_time', '08:00')
            target_first_visit = settings.get('first_visit_time', '09:00')
            min_daily_hours = settings.get('min_daily_hours', 7)
            
            actual_clock_in = None
            actual_first_visit = None
            actual_last_visit = None
            actual_clock_out = None
            
            all_times = []
            first_successful_time = None
            last_successful_time = None
            first_log_time = None
            last_log_time = None
            
            for date in date_list:
                if date in all_logs and isinstance(all_logs[date], list):
                    for log in all_logs[date]:
                        if not isinstance(log, dict):
                            continue
                        
                        log_time = log.get('time', '')
                        visit_status = log.get('visit_status', '')
                        
                        if log_time:
                            if first_log_time is None:
                                first_log_time = log_time
                            last_log_time = log_time
                            
                            if visit_status == 'موفق':
                                all_times.append(log_time)
                                if first_successful_time is None:
                                    first_successful_time = log_time
                                last_successful_time = log_time
            
            actual_clock_in = first_log_time if first_log_time else target_clock_in
            actual_first_visit = first_successful_time if first_successful_time else target_first_visit
            actual_last_visit = last_successful_time if last_successful_time else '---'
            actual_clock_out = last_log_time if last_log_time else '---'
            
            # ✅ تابع add_hours با محدودیت 23:59
            def add_hours(time_str, hours):
                """اضافه کردن ساعت به زمان با محدودیت 23:59"""
                try:
                    h, m = map(int, time_str.split(':'))
                    total_min = h * 60 + m + (hours * 60)
                    h_new = total_min // 60
                    m_new = total_min % 60
                    
                    # ✅ اگر از 23:59 بیشتر شد، به 23:59 محدود کن
                    if h_new >= 24:
                        return "23:59"
                    
                    return f"{h_new:02d}:{m_new:02d}"
                except:
                    return time_str
            
            # ✅ ===== محاسبه هدف‌ها بر اساس زمان‌های واقعی =====
            
            # ✅ هدف آخرین ویزیت: ساعت اولین ویزیت واقعی + ساعت کاری
            if actual_first_visit != '---' and actual_first_visit != target_first_visit:
                target_last_visit = add_hours(actual_first_visit, min_daily_hours)
            else:
                target_last_visit = add_hours(target_first_visit, min_daily_hours)
            
            # ✅ هدف پایان کار: ساعت شروع واقعی + (ساعت کاری + 1)
            if actual_clock_in != '---' and actual_clock_in != target_clock_in:
                target_clock_out = add_hours(actual_clock_in, min_daily_hours + 1)
            else:
                target_clock_out = add_hours(target_clock_in, min_daily_hours + 1)
            
            # ✅ محاسبه زمان کار مفید
            def time_diff(t1, t2):
                try:
                    if t1 == '---' or t2 == '---':
                        return 0
                    h1, m1 = map(int, t1.split(':'))
                    h2, m2 = map(int, t2.split(':'))
                    diff_minutes = (h2 * 60 + m2) - (h1 * 60 + m1)
                    return diff_minutes
                except:
                    return 0
            
            work_hours = 0
            work_minutes = 0
            if actual_first_visit != '---' and actual_last_visit != '---':
                diff_min = time_diff(actual_first_visit, actual_last_visit)
                work_hours = diff_min // 60
                work_minutes = diff_min % 60
            
            if work_hours < 5:
                work_msg = 'به اندازه کافی وقت نذاشتم باید جبران کنم'
                work_color = (0.5, 0.5, 0.5, 1)
            elif work_hours < 6:
                work_msg = 'میتونستم وقت بیشتری برای کارم بذارم متاسفم'
                work_color = (1, 0.8, 0, 1)
            else:
                work_msg = 'تمام تلاشم رو کردم امیدوارم نتیجه بگیرم'
                work_color = (0.2, 0.7, 0.2, 1)
            
            # ✅ ===== ارزیابی زمان با تاخیر مجاز =====
            CLOCK_IN_TOLERANCE = 15   # ۱۵ دقیقه تاخیر مجاز برای شروع کار
            FIRST_VISIT_TOLERANCE = 30  # ۳۰ دقیقه تاخیر مجاز برای اولین ویزیت
            
            # ✅ شروع کار (واقعی - هدف)
            clock_in_diff = self._time_diff(actual_clock_in, target_clock_in)
            if clock_in_diff <= CLOCK_IN_TOLERANCE:
                clock_in_status = "به موقع"
                clock_in_color = (0.2, 0.8, 0.2, 1)
                if clock_in_diff <= 0:
                    clock_in_eval = "شروع به موقع"
                else:
                    clock_in_eval = f"{clock_in_diff} دقيقه تاخير (مجاز)"
            else:
                clock_in_status = f"{clock_in_diff} دقيقه تاخير"
                clock_in_color = (0.8, 0.2, 0.2, 1)
                clock_in_eval = f"{clock_in_diff} دقيقه تاخير غيرمجاز در شروع"
            
            # ✅ اولین ویزیت (واقعی - هدف)
            first_visit_diff = self._time_diff(actual_first_visit, target_first_visit)
            if first_visit_diff <= FIRST_VISIT_TOLERANCE:
                first_visit_status = "به موقع"
                first_visit_color = (0.2, 0.8, 0.2, 1)
                if first_visit_diff <= 0:
                    first_visit_eval = "اولين ويزيت به موقع"
                else:
                    first_visit_eval = f"{first_visit_diff} دقيقه تاخير (مجاز)"
            else:
                first_visit_status = f"{first_visit_diff} دقيقه تاخير"
                first_visit_color = (0.8, 0.2, 0.2, 1)
                first_visit_eval = f"{first_visit_diff} دقيقه تاخير غيرمجاز در اولين ويزيت"
            
            # ✅ آخرین ویزیت (واقعی - هدف)
            last_visit_diff = self._time_diff(actual_last_visit, target_last_visit) if actual_last_visit != '---' else 0
            if last_visit_diff >= 0:
                last_visit_status = "كامل"
                last_visit_color = (0.2, 0.8, 0.2, 1)
                if last_visit_diff <= 30:
                    last_visit_eval = f"{work_msg} (دقیقاً به موقع)"
                else:
                    last_visit_eval = f"{work_msg} (با {last_visit_diff} دقيقه تاخير)"
            else:
                last_visit_status = f"{abs(last_visit_diff)} دقيقه زودتر"
                last_visit_color = (0.8, 0.2, 0.2, 1)
                last_visit_eval = f"{work_msg} (با {abs(last_visit_diff)} دقيقه زودتر)"
            
            # ✅ پایان کار (واقعی - هدف)
            clock_out_diff = self._time_diff(actual_clock_out, target_clock_out) if actual_clock_out != '---' else 0
            if clock_out_diff >= 0:
                clock_out_status = "كامل"
                clock_out_color = (0.2, 0.8, 0.2, 1)
                if clock_out_diff <= 30:
                    clock_out_eval = f"{work_msg} (دقیقاً به موقع)"
                else:
                    clock_out_eval = f"{work_msg} (با {clock_out_diff} دقيقه تاخير)"
            else:
                clock_out_status = f"{abs(clock_out_diff)} دقيقه زودتر"
                clock_out_color = (0.8, 0.2, 0.2, 1)
                clock_out_eval = f"{work_msg} (با {abs(clock_out_diff)} دقيقه زودتر)"
            
            work_time_display = f"{work_hours} ساعت و {work_minutes} دقيقه"
            
            # ✅ محاسبه درصد تحقق اهداف
            evaluation_items = []
            total_percent = 0
            item_count = 0
            
            for item in items:
                if item['name'] not in ['ساعت شروع کار', 'ساعت اولین ویزیت', 'ساعت آخرین ویزیت', 'ساعت پایان کار']:
                    if item['target'] > 0:
                        percent = (item['actual'] / item['target']) * 100
                    else:
                        percent = 0
                    
                    evaluation_items.append({
                        'name': item['name'],
                        'target': item['target'],
                        'actual': item['actual'],
                        'percent': percent
                    })
                    total_percent += percent
                    item_count += 1
            
            avg_percent = total_percent / item_count if item_count > 0 else 0
            
            if avg_percent < 50:
                eval_text = "نياز به تلاش بيشتر دارم"
                eval_color = (0.8, 0.2, 0.2, 1)
            elif avg_percent < 70:
                eval_text = "تلاشم كافي نيست"
                eval_color = (1, 0.5, 0, 1)
            elif avg_percent < 85:
                eval_text = "در مسير درست هستم"
                eval_color = (1, 0.8, 0, 1)
            elif avg_percent < 100:
                eval_text = "تا موفقيت راهي نيست"
                eval_color = (0.2, 0.8, 0.2, 1)
            else:
                eval_text = "به خودم افتخار ميكنم"
                eval_color = (0, 0.6, 0, 1)
            
            # ✅ ساخت دیالوگ
            dialog_content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(8))
            with dialog_content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                content_rect = Rectangle(pos=dialog_content.pos, size=dialog_content.size)
                dialog_content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                                size=lambda i, v: setattr(content_rect, 'size', v))
            
            detail_scroll = ScrollView(
                do_scroll_x=False,
                do_scroll_y=True,
                size_hint_y=1,
                scroll_type=['bars', 'content'],
                bar_width=dp(6),
                bar_color=(0.3, 0.5, 0.8, 1),
                bar_inactive_color=(0.2, 0.2, 0.2, 1)
            )
            
            detail_content = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None)
            detail_content.bind(minimum_height=detail_content.setter('height'))
            
            detail_content.add_widget(RTLLabel(
                text='نتیجه ارزیابی عملکرد',
                size_hint_y=None,
                height=dp(45),
                font_size=sp(28),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))
            
            detail_content.add_widget(RTLLabel(
                text=f'ميانگين تحقق اهداف: {avg_percent:.1f}%',
                size_hint_y=None,
                height=dp(45),
                font_size=sp(26),
                bold=True,
                color=eval_color
            ))
            
            detail_content.add_widget(RTLLabel(
                text=f'ارزيابي عملكرد: {eval_text}',
                size_hint_y=None,
                height=dp(50),
                font_size=sp(28),
                bold=True,
                color=eval_color
            ))
            
            detail_content.add_widget(RTLLabel(
                text='تفكيك عملكرد آيتم‌ها:',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(22),
                color=(0.4, 0.7, 1, 1),
                bold=True
            ))
            
            header_box = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(2))
            headers = ['آيتم', 'هدف', 'عملكرد', 'درصد']
            for header in headers:
                header_box.add_widget(RTLLabel(
                    text=header,
                    size_hint_x=1/len(headers),
                    size_hint_y=None,
                    height=dp(36),
                    font_size=sp(20),
                    bold=True,
                    color=(0.4, 0.7, 1, 1),
                    halign='center'
                ))
            detail_content.add_widget(header_box)
            
            for item in evaluation_items:
                row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(2))
                
                if item['percent'] < 50:
                    percent_color = (0.8, 0.2, 0.2, 1)
                elif item['percent'] < 70:
                    percent_color = (1, 0.5, 0, 1)
                elif item['percent'] < 85:
                    percent_color = (1, 0.8, 0, 1)
                elif item['percent'] < 100:
                    percent_color = (0.2, 0.8, 0.2, 1)
                else:
                    percent_color = (0, 0.6, 0, 1)
                
                row.add_widget(RTLLabel(
                    text=item['name'],
                    size_hint_x=1/len(headers),
                    size_hint_y=None,
                    height=dp(34),
                    font_size=sp(18),
                    color=(1, 1, 1, 1),
                    halign='right'
                ))
                row.add_widget(RTLLabel(
                    text="{:,}".format(item['target']),
                    size_hint_x=1/len(headers),
                    size_hint_y=None,
                    height=dp(34),
                    font_size=sp(18),
                    color=(1, 1, 1, 1),
                    halign='center'
                ))
                row.add_widget(RTLLabel(
                    text="{:,}".format(item['actual']),
                    size_hint_x=1/len(headers),
                    size_hint_y=None,
                    height=dp(34),
                    font_size=sp(18),
                    color=(1, 1, 1, 1),
                    halign='center'
                ))
                row.add_widget(RTLLabel(
                    text=f"{item['percent']:.1f}%",
                    size_hint_x=1/len(headers),
                    size_hint_y=None,
                    height=dp(34),
                    font_size=sp(18),
                    color=percent_color,
                    halign='center'
                ))
                
                detail_content.add_widget(row)
            
            detail_content.add_widget(RTLLabel(
                text='ارزيابي زمان:',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(22),
                color=(0.4, 0.7, 1, 1),
                bold=True
            ))
            
            detail_content.add_widget(RTLLabel(
                text=f'كاركرد مفيد: {work_time_display}',
                size_hint_y=None,
                height=dp(38),
                font_size=sp(20),
                color=work_color,
                bold=True
            ))
            
            detail_content.add_widget(RTLLabel(
                text=f'ارزيابي زمان: {work_msg}',
                size_hint_y=None,
                height=dp(38),
                font_size=sp(20),
                color=work_color,
                bold=True
            ))
            
            # ✅ جدول زمان‌ها با وضعیت جدید
            time_items = [
                {'label': 'ساعت شروع كار', 'actual': actual_clock_in, 'target': target_clock_in, 
                'status': clock_in_status, 'color': clock_in_color, 'eval': clock_in_eval},
                {'label': 'ساعت اولين ويزيت', 'actual': actual_first_visit, 'target': target_first_visit, 
                'status': first_visit_status, 'color': first_visit_color, 'eval': first_visit_eval},
                {'label': 'ساعت آخرين ويزيت (هدف)', 'actual': actual_last_visit, 'target': target_last_visit, 
                'status': last_visit_status, 'color': last_visit_color, 'eval': last_visit_eval},
                {'label': 'ساعت پايان كار (هدف)', 'actual': actual_clock_out, 'target': target_clock_out, 
                'status': clock_out_status, 'color': clock_out_color, 'eval': clock_out_eval},
            ]
            
            time_header = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(2))
            time_headers = ['آيتم', 'هدف | واقعي', 'وضعيت', 'ارزيابي']
            for header in time_headers:
                time_header.add_widget(RTLLabel(
                    text=header,
                    size_hint_x=1/len(time_headers),
                    size_hint_y=None,
                    height=dp(34),
                    font_size=sp(18),
                    bold=True,
                    color=(0.4, 0.7, 1, 1),
                    halign='center'
                ))
            detail_content.add_widget(time_header)
            
            for item in time_items:
                row = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(2))
                
                row.add_widget(RTLLabel(
                    text=item['label'],
                    size_hint_x=1/len(time_headers),
                    size_hint_y=None,
                    height=dp(32),
                    font_size=sp(17),
                    color=(1, 1, 1, 1),
                    halign='right'
                ))
                row.add_widget(RTLLabel(
                    text=f"{item['target']} | {item['actual']}",
                    size_hint_x=1/len(time_headers),
                    size_hint_y=None,
                    height=dp(32),
                    font_size=sp(17),
                    color=(1, 1, 1, 1),
                    halign='center'
                ))
                row.add_widget(RTLLabel(
                    text=item['status'],
                    size_hint_x=1/len(time_headers),
                    size_hint_y=None,
                    height=dp(32),
                    font_size=sp(17),
                    color=item['color'],
                    halign='center'
                ))
                row.add_widget(RTLLabel(
                    text=item['eval'],
                    size_hint_x=1/len(time_headers),
                    size_hint_y=None,
                    height=dp(32),
                    font_size=sp(17),
                    color=item['color'],
                    halign='center'
                ))
                
                detail_content.add_widget(row)
            
            total_height = 45 + 45 + 50 + 40 + 38 + len(evaluation_items) * 38 + 40 + 38 + 38 + 36 + len(time_items) * 36 + 20
            detail_content.height = dp(total_height)
            detail_scroll.add_widget(detail_content)
            dialog_content.add_widget(detail_scroll)
            
            # ✅ دکمه‌های پایین دیالوگ
            btn_layout = BoxLayout(
                size_hint_y=None, 
                height=dp(55), 
                spacing=dp(10),
                padding=dp(5)
            )
            
            # ✅ دکمه خودآزمایی (فقط برای روز جاری)
            today = get_today_jalali()
            is_today = self.current_evaluation_date == today
            
            if is_today:
                self_assessment_btn = PersianButton(
                    text='ثبت خودآزمایی',
                    background_color=(0.2, 0.6, 0.2, 1),
                    size_hint_x=0.5,
                    size_hint_y=None,
                    height=dp(50),
                    color=(1, 1, 1, 1),
                    font_size=sp(18),
                    bold=True
                )
                btn_layout.add_widget(self_assessment_btn)
            
            close_btn = PersianButton(
                text='بستن',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_x=0.5 if is_today else 1,
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            btn_layout.add_widget(close_btn)
            
            dialog_content.add_widget(btn_layout)
            
            detail_popup = Popup(
                title='',
                content=dialog_content,
                size_hint=(0.92, 0.88),
                auto_dismiss=False,
                background_color=(0.08, 0.08, 0.08, 1)
            )
            detail_popup.title_size = 0
            detail_popup.title_color = (0, 0, 0, 0)
            detail_popup.separator_height = 0
            
            # ✅ اتصال دکمه‌ها
            if is_today:
                self_assessment_btn.bind(
                    on_press=lambda x: self._open_self_assessment_from_evaluation(
                        detail_popup, items, date_list, all_logs
                    )
                )
            
            close_btn.bind(on_press=lambda x: detail_popup.dismiss())
            detail_popup.open()

        except Exception as e:
            print(f"خطا در نمایش جزئیات ارزیابی: {e}")
            import traceback
            traceback.print_exc()
    
    def _open_self_assessment_from_evaluation(self, popup, items=None, date_list=None, all_logs=None):
        """باز کردن دیالوگ خودآزمایی از داخل دیالوگ ارزیابی"""
        try:
            # ✅ بستن پاپ‌آپ ارزیابی
            if popup and hasattr(popup, 'dismiss'):
                try:
                    popup.dismiss()
                except:
                    pass
            
            # ✅ جلوگیری از اجرای همزمان
            if self._is_processing:
                return
            
            # ✅ جلوگیری از نمایش دوباره
            if self._self_assessment_shown:
                return
            
            # بررسی ثبت پایان کار
            today = get_today_jalali()
            summary_file = 'daily_summary.json'
            summary_path = os.path.join(get_data_path(), summary_file)
            
            if not os.path.exists(summary_path):
                self.show_message('توجه', 'برای ثبت خودآزمایی، ابتدا پایان کار را ثبت کنید.')
                return
            
            all_summaries = load_json(summary_file)
            if today not in all_summaries:
                self.show_message('توجه', 'برای ثبت خودآزمایی، ابتدا پایان کار را ثبت کنید.')
                return
            
            summary_data = all_summaries[today]
            if 'clock_out' not in summary_data or not summary_data['clock_out']:
                self.show_message('توجه', 'برای ثبت خودآزمایی، ابتدا پایان کار را ثبت کنید.')
                return
            
            # ✅ همه چیز اوکی هست، خودآزمایی رو نمایش بده
            self._self_assessment_shown = True
            self.show_self_assessment_dialog(items, date_list, all_logs)
            
        except Exception as e:
            self._self_assessment_shown = False
            print(f"خطا در باز کردن خودآزمایی: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_close_detail_dialog(self, popup, items=None, date_list=None, all_logs=None):
        """مدیریت بستن دیالوگ جزئیات"""
        try:
            # ✅ فقط بستن پاپ‌آپ
            if popup and hasattr(popup, 'dismiss'):
                try:
                    popup.dismiss()
                except:
                    pass
            
            # ✅ دیگه هیچ کاری انجام نمیده
            
        except Exception as e:
            print(f"خطا در بستن دیالوگ جزئیات: {e}")
            import traceback
            traceback.print_exc()
    
    # ============================================================
    # دیالوگ خودآزمایی
    # ============================================================
    
    def show_self_assessment_dialog(self, items=None, date_list=None, all_logs=None):
        """نمایش دیالوگ خودآزمایی اجباری با ارزیابی کلامی"""
        try:
            # ✅ جلوگیری از نمایش همزمان
            if self._self_assessment_popup and self._self_assessment_popup._window:
                return
            
            # ✅ جلوگیری از اجرای همزمان
            if self._is_processing:
                return
            
            self._is_processing = True

            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            with content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                            size=lambda i, v: setattr(content_rect, 'size', v))
            
            content.add_widget(RTLLabel(
                text='واقعا به خودم از 100 چه امتیازی میدم؟',
                size_hint_y=None,
                height=dp(50),
                font_size=sp(40),
                bold=True,
                color=(1, 1, 1, 1),
                halign='center'
            ))
            
            # دکمه‌های گرد
            score_buttons = BoxLayout(
                size_hint_y=None,
                height=dp(60),
                spacing=dp(10),
                padding=dp(10)
            )
            
            scores = [
                {'value': 0, 'color': (0.8, 0.1, 0.1, 1), 'label': '0'},
                {'value': 25, 'color': (1, 0.5, 0, 1), 'label': '25'},
                {'value': 50, 'color': (1, 0.8, 0, 1), 'label': '50'},
                {'value': 75, 'color': (0.2, 0.5, 0.9, 1), 'label': '75'},
                {'value': 100, 'color': (0.2, 0.7, 0.2, 1), 'label': '100'},
            ]
            
            self.selected_score = None
            self.score_buttons = []
            
            for score_data in scores:
                btn_layout = BoxLayout(orientation='vertical', size_hint_x=0.2, spacing=dp(2))
                
                score_btn = Button(
                    size_hint_y=None,
                    height=dp(40),
                    width=dp(40),
                    background_color=score_data['color'],
                    background_normal='',
                    border=(0, 0, 0, 0),
                    pos_hint={'center_x': 0.5}
                )
                score_btn.bind(on_press=lambda x, val=score_data['value']: self._select_score(val))
                
                self.score_buttons.append({
                    'btn': score_btn,
                    'value': score_data['value'],
                    'default_color': score_data['color']
                })
                
                btn_layout.add_widget(score_btn)
                
                btn_layout.add_widget(RTLLabel(
                    text=score_data['label'],
                    size_hint_y=None,
                    height=dp(28),
                    font_size=sp(22),
                    color=(1, 1, 1, 1),
                    halign='center'
                ))
                
                score_buttons.add_widget(btn_layout)
            
            content.add_widget(score_buttons)
            
            color_labels = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(10))
            colors_text = ['0', '25', '50', '75', '100']
            for text in colors_text:
                color_labels.add_widget(RTLLabel(
                    text=text,
                    size_hint_x=0.2,
                    size_hint_y=None,
                    height=dp(36),
                    font_size=sp(32),
                    color=(0.6, 0.6, 0.6, 1),
                    halign='center'
                ))
            content.add_widget(color_labels)
            
            # ===== ارزیابی کلامی =====
            if items and date_list and all_logs:
                # محاسبه مجدد ارزیابی کلامی
                eval_text, eval_color, work_msg, work_color, avg_percent, work_time_display = self._calculate_evaluation(items, date_list, all_logs)
                
                content.add_widget(RTLLabel(
                    text='ـــــــــــــــــــــــــــــــــــــــــ',
                    size_hint_y=None,
                    height=dp(36),
                    font_size=sp(32),
                    color=(0.3, 0.3, 0.3, 1),
                    halign='center'
                ))
                
                content.add_widget(RTLLabel(
                    text=f'ميانگين تحقق اهداف: {avg_percent:.1f}%',
                    size_hint_y=None,
                    height=dp(52),
                    font_size=sp(38),
                    bold=True,
                    color=eval_color,
                    halign='center'
                ))
                
                content.add_widget(RTLLabel(
                    text=f'ارزيابي عملكرد: {eval_text}',
                    size_hint_y=None,
                    height=dp(52),
                    font_size=sp(38),
                    bold=True,
                    color=eval_color,
                    halign='center'
                ))
                
                content.add_widget(RTLLabel(
                    text=f'كاركرد مفيد: {work_time_display}',
                    size_hint_y=None,
                    height=dp(52),
                    font_size=sp(38),
                    bold=True,
                    color=work_color,
                    halign='center'
                ))
                
                content.add_widget(RTLLabel(
                    text=f'ارزيابي زمان: {work_msg}',
                    size_hint_y=None,
                    height=dp(52),
                    font_size=sp(38),
                    bold=True,
                    color=work_color,
                    halign='center'
                ))
            
            confirm_btn = PersianButton(
                text='تأیید',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(45),
                color=(0.5, 0.5, 0.5, 1),
                font_size=sp(18),
                disabled=True
            )
            content.add_widget(confirm_btn)
            
            popup = Popup(
                title='',
                content=content,
                size_hint=(0.85, 0.6),
                auto_dismiss=False,
                background_color=(0.08, 0.08, 0.08, 1)
            )
            popup.title_size = 0
            popup.title_color = (0, 0, 0, 0)
            popup.separator_height = 0
            
            # ✅ تابع تأیید با مدیریت کامل
            def on_confirm(instance):
                if self.selected_score is not None:
                    # ✅ ذخیره نمره
                    self.save_self_score(self.selected_score)
                    
                    # ✅ بستن پاپ‌آپ
                    popup.dismiss()
                    
                    # ✅ بازنشانی فلگ‌ها
                    self._self_assessment_shown = False
                    self._is_processing = False
                    
                    # ✅ نمایش پیام موفقیت
                    self.show_message('موفق', 'نمره خودآزمایی با موفقیت ثبت شد.')
            
            confirm_btn.bind(on_press=on_confirm)
            self._self_assessment_popup = popup
            self._self_assessment_confirm = confirm_btn
            
            popup.bind(on_dismiss=self._on_self_assessment_dismiss)
            popup.open()
            
            # ✅ بازنشانی فلگ بعد از باز شدن
            Clock.schedule_once(lambda dt: setattr(self, '_is_processing', False), 1)

        except Exception as e:
            self._is_processing = False
            self._self_assessment_shown = False
            print(f"خطا در نمایش دیالوگ خودآزمایی: {e}")
            import traceback
            traceback.print_exc()

    def _on_self_assessment_dismiss(self, instance):
        """مدیریت بسته شدن دیالوگ خودآزمایی"""
        try:
            # ✅ بازنشانی فلگ‌ها
            self._self_assessment_shown = False
            self._is_processing = False
            self._self_assessment_popup = None
            
        except Exception as e:
            print(f"خطا در بستن خودآزمایی: {e}")

    def _calculate_evaluation(self, items, date_list, all_logs):
        """محاسبه ارزیابی کلامی برای نمایش در خودآزمایی"""
        try:
            settings = get_settings()
            
            target_clock_in = settings.get('work_start_time', '08:00')
            target_first_visit = settings.get('first_visit_time', '09:00')
            min_daily_hours = settings.get('min_daily_hours', 7)
            
            actual_clock_in = None
            actual_first_visit = None
            actual_last_visit = None
            actual_clock_out = None
            
            first_successful_time = None
            last_successful_time = None
            first_log_time = None
            last_log_time = None
            
            for date in date_list:
                if date in all_logs and isinstance(all_logs[date], list):
                    for log in all_logs[date]:
                        if not isinstance(log, dict):
                            continue
                        
                        log_time = log.get('time', '')
                        visit_status = log.get('visit_status', '')
                        
                        if log_time:
                            if first_log_time is None:
                                first_log_time = log_time
                            last_log_time = log_time
                            
                            if visit_status == 'موفق':
                                if first_successful_time is None:
                                    first_successful_time = log_time
                                last_successful_time = log_time
            
            actual_clock_in = first_log_time if first_log_time else target_clock_in
            actual_first_visit = first_successful_time if first_successful_time else target_first_visit
            actual_last_visit = last_successful_time if last_successful_time else '---'
            actual_clock_out = last_log_time if last_log_time else '---'
            
            # ✅ تابع add_hours با محدودیت 23:59
            def add_hours(time_str, hours):
                """اضافه کردن ساعت به زمان با محدودیت 23:59"""
                try:
                    h, m = map(int, time_str.split(':'))
                    total_min = h * 60 + m + (hours * 60)
                    h_new = total_min // 60
                    m_new = total_min % 60
                    
                    # ✅ اگر از 23:59 بیشتر شد، به 23:59 محدود کن
                    if h_new >= 24:
                        return "23:59"
                    
                    return f"{h_new:02d}:{m_new:02d}"
                except:
                    return time_str
            
            # ✅ محاسبه هدف‌ها بر اساس زمان‌های واقعی
            if actual_first_visit != '---' and actual_first_visit != target_first_visit:
                target_last_visit = add_hours(actual_first_visit, min_daily_hours)
            else:
                target_last_visit = add_hours(target_first_visit, min_daily_hours)
            
            if actual_clock_in != '---' and actual_clock_in != target_clock_in:
                target_clock_out = add_hours(actual_clock_in, min_daily_hours + 1)
            else:
                target_clock_out = add_hours(target_clock_in, min_daily_hours + 1)
            
            def time_diff(t1, t2):
                try:
                    if t1 == '---' or t2 == '---':
                        return 0
                    h1, m1 = map(int, t1.split(':'))
                    h2, m2 = map(int, t2.split(':'))
                    diff_minutes = (h2 * 60 + m2) - (h1 * 60 + m1)
                    return diff_minutes
                except:
                    return 0
            
            work_hours = 0
            work_minutes = 0
            if actual_first_visit != '---' and actual_last_visit != '---':
                diff_min = time_diff(actual_first_visit, actual_last_visit)
                work_hours = diff_min // 60
                work_minutes = diff_min % 60
            
            if work_hours < 5:
                work_msg = 'به اندازه کافی وقت نذاشتم باید جبران کنم'
                work_color = (0.5, 0.5, 0.5, 1)
            elif work_hours < 6:
                work_msg = 'میتونستم وقت بیشتری برای کارم بذارم متاسفم'
                work_color = (1, 0.8, 0, 1)
            else:
                work_msg = 'تمام تلاشم رو کردم امیدوارم نتیجه بگیرم'
                work_color = (0.2, 0.7, 0.2, 1)
            
            work_time_display = f"{work_hours} ساعت و {work_minutes} دقيقه"
            
            # محاسبه درصد
            total_percent = 0
            item_count = 0
            
            for item in items:
                if item['name'] not in ['ساعت شروع کار', 'ساعت اولین ویزیت', 'ساعت آخرین ویزیت', 'ساعت پایان کار']:
                    if item['target'] > 0:
                        percent = (item['actual'] / item['target']) * 100
                    else:
                        percent = 0
                    total_percent += percent
                    item_count += 1
            
            avg_percent = total_percent / item_count if item_count > 0 else 0
            
            if avg_percent < 50:
                eval_text = "نياز به تلاش بيشتر دارم"
                eval_color = (0.8, 0.2, 0.2, 1)
            elif avg_percent < 70:
                eval_text = "تلاشم كافي نيست"
                eval_color = (1, 0.5, 0, 1)
            elif avg_percent < 85:
                eval_text = "در مسير درست هستم"
                eval_color = (1, 0.8, 0, 1)
            elif avg_percent < 100:
                eval_text = "تا موفقيت راهي نيست"
                eval_color = (0.2, 0.8, 0.2, 1)
            else:
                eval_text = "به خودم افتخار ميكنم"
                eval_color = (0, 0.6, 0, 1)
            
            return eval_text, eval_color, work_msg, work_color, avg_percent, work_time_display
            
        except Exception as e:
            print(f"خطا در محاسبه ارزیابی: {e}")
            return "خطا در محاسبه", (0.5, 0.5, 0.5, 1), "خطا", (0.5, 0.5, 0.5, 1), 0, "۰"
    
    def _time_diff(self, time1, time2):
        """محاسبه اختلاف دو زمان به دقیقه (time1 - time2)"""
        try:
            if time1 == '---' or time2 == '---':
                return 0
            h1, m1 = map(int, time1.split(':'))
            h2, m2 = map(int, time2.split(':'))
            # ✅ time1 - time2 (درست)
            diff = (h1 * 60 + m1) - (h2 * 60 + m2)
            return diff
        except:
            return 0

    # ============================================================
    # توابع کمکی
    # ============================================================
    
    def _select_score(self, value):
        self.selected_score = value
        
        for btn_data in self.score_buttons:
            if btn_data['value'] == value:
                btn_data['btn'].background_color = (1, 1, 1, 1)
            else:
                btn_data['btn'].background_color = btn_data['default_color']
        
        if self._self_assessment_confirm:
            self._self_assessment_confirm.disabled = False
            self._self_assessment_confirm.background_color = (0.2, 0.7, 0.2, 1)
            self._self_assessment_confirm.color = (1, 1, 1, 1)
    
    def save_self_score(self, score):
        """ذخیره نمره خودآزمایی در daily_summary.json"""
        try:
            today = get_today_jalali()
            summary_file = 'daily_summary.json'
            summary_path = os.path.join(get_data_path(), summary_file)
            
            if os.path.exists(summary_path):
                all_summaries = load_json(summary_file)
            else:
                all_summaries = {}
            
            if today in all_summaries:
                all_summaries[today]['self_score'] = score
            else:
                all_summaries[today] = {'self_score': score}
            
            save_json(summary_file, all_summaries)
            
            # ✅ بازنشانی کامل فلگ‌ها
            self._self_assessment_shown = False
            self._is_processing = False
            
            return True
        except Exception as e:
            print(f"خطا در ذخیره نمره خودآزمایی: {e}")
            return False
    
    def refresh_stats(self, instance):
        self.switch_tab(self.current_tab)
    
    def _make_card(self, title, value, color):
        card = BoxLayout(
            orientation='vertical',
            size_hint_x=0.5,
            size_hint_y=None,
            height=dp(75),
            padding=dp(8),
            spacing=dp(4)
        )
        
        with card.canvas.before:
            Color(*color)
            card.bg_rect = Rectangle(pos=card.pos, size=card.size)
            card.bind(pos=self._update_card_bg, size=self._update_card_bg)
        
        card.add_widget(RTLLabel(
            text=title,
            size_hint_y=None,
            height=dp(25),
            font_size=sp(14),
            color=(1, 1, 1, 1)
        ))
        card.add_widget(RTLLabel(
            text=str(value),
            size_hint_y=None,
            height=dp(35),
            font_size=sp(22),
            bold=True,
            color=(1, 1, 1, 1)
        ))
        
        return card
    
    def _update_card_bg(self, instance, value):
        if hasattr(instance, 'bg_rect'):
            instance.bg_rect.pos = instance.pos
            instance.bg_rect.size = instance.size
    
    def export_excel(self, instance):
        try:
            self.loading_popup = self.show_message('در حال ساخت', 'لطفاً صبر کنید...')
            
            filtered_data = None
            
            if self.current_tab == 0:
                if hasattr(self, '_current_performance_data') and self._current_performance_data:
                    all_logs = get_daily_logs()
                    filtered_data = {}
                    for date in self._current_performance_data:
                        if date in all_logs:
                            filtered_data[date] = all_logs[date]
            
            elif self.current_tab == 1:
                all_logs = get_daily_logs()
                filtered_data = {}
                for date, logs in all_logs.items():
                    if self.detail_from_date and date < self.detail_from_date:
                        continue
                    if self.detail_to_date and date > self.detail_to_date:
                        continue
                    filtered_data[date] = logs
            
            if not filtered_data:
                filtered_data = None
            
            def do_export():
                success, result = export_to_excel(filtered_data)
                
                def show_result(dt):
                    if hasattr(self, 'loading_popup') and self.loading_popup:
                        try:
                            self.loading_popup.dismiss()
                        except:
                            pass
                        self.loading_popup = None
                    
                    if success:
                        self.show_message(
                            'موفق', 
                            'فایل اکسل با موفقیت ساخته شد!\n\n'
                            'فایل در پوشه Downloads ذخیره شد.'
                        )
                    else:
                        self.show_message('خطا', f'خطا در ساخت اکسل:\n{result}')
                
                Clock.schedule_once(show_result, 1)
            
            thread = threading.Thread(target=do_export, daemon=True)
            thread.start()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در خروجی اکسل: {e}", error_details)
    
    def go_back(self, instance):
        self.manager.current = 'user'
    
    def show_message(self, title, message):
        try:
            # ✅ جلوگیری از نمایش همزمان
            if self._is_processing:
                Clock.schedule_once(lambda dt: self.show_message(title, message), 1)
                return
            
            if len(message) > 200:
                message = message[:200] + "..."
            
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            
            msg_label = PersianLabel(
                text=message,
                font_size=sp(20),
                color=(255, 255, 255, 255),
                size_hint_y=None,
                halign='center',
                valign='middle',
                width=dp(280),
                text_size=(dp(280), None)
            )
            msg_label.bind(texture_size=msg_label.setter('size'))
            content.add_widget(msg_label)
            
            btn = PersianButton(
                text='باشه',
                size_hint_y=None,
                height=dp(50),
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
            
            # ✅ مدیریت بسته شدن پیام
            def on_dismiss(instance):
                self._is_processing = False
            
            popup.bind(on_dismiss=on_dismiss)
            btn.bind(on_press=popup.dismiss)
            
            Clock.schedule_once(lambda dt: popup.open(), 0.5)
            
            return popup
            
        except Exception as e:
            self._is_processing = False
            print(f"خطا در نمایش پیام: {e}")
            import traceback
            traceback.print_exc()
            return None
