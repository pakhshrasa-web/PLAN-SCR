# screens/distributor_report_screen.py
# ========== صفحه گزارش موزع ==========

import traceback
import os
import threading
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup  
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock

from utils.rtl_widgets import PersianButton, RTLLabel, PersianPopup, RTLTextInput
from utils.file_manager import get_settings, load_json, save_json, get_data_path
from utils.delivery_manager import get_deliveries_by_date, get_all_deliveries
from utils.jalali_date import get_today_jalali
from error_handler import ErrorPopup
from screens.report_screen import ReportScreen
from utils.excel_exporter_distributor import export_distributor_to_excel


class DistributorReportScreen(ReportScreen):
    """صفحه گزارش موزع - ارث‌بری از ReportScreen با تغییرات مخصوص توزیع"""
    
    def __init__(self, **kwargs):
        try:
            # تنظیم فلگ مخصوص توزیع
            self.is_distributor = True
            super().__init__(**kwargs)
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت DistributorReportScreen: {e}", error_details)
            raise
    
    # ============================================================
    # بازنویسی متد تب عملکرد کلی
    # ============================================================
    
    def show_performance_tab(self):
        """نمایش تب عملکرد کلی برای موزع"""
        try:
            # تنظیم پیشفرض: اول ماه تا امروز
            if not self.performance_from_date:
                self.performance_from_date = self._get_first_day_of_month()
            if not self.performance_to_date:
                self.performance_to_date = get_today_jalali()
            
            all_deliveries = get_all_deliveries()
            
            # ساخت بخش فیلتر
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
            
            content_layout = BoxLayout(orientation='vertical')
            content_layout.add_widget(filter_layout)
            
            data_scroll = ScrollView()
            data_content = GridLayout(cols=1, spacing=dp(8), size_hint_y=None, padding=dp(8))
            data_content.bind(minimum_height=data_content.setter('height'))
            
            # فیلتر کردن تاریخ‌ها
            date_list = list(all_deliveries.keys())
            filtered_dates = self._filter_dates(
                date_list,
                self.performance_from_date,
                self.performance_to_date
            )
            
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
            
            # محاسبه آمار توزیع
            total_days = len(filtered_dates)
            total_customers = 0
            total_deliveries = 0
            total_amount = 0
            total_cash = 0
            total_check = 0
            total_credit = 0
            total_return_qty = 0
            total_return_amount = 0
            
            for date in filtered_dates:
                if date not in all_deliveries or not isinstance(all_deliveries[date], list):
                    continue
                for delivery in all_deliveries[date]:
                    if not isinstance(delivery, dict):
                        continue
                    delivery_status = delivery.get('delivery_status', '')
                    invoice_amount = delivery.get('invoice_amount', 0)
                    cash_amount = delivery.get('cash_amount', 0)
                    check_amount = delivery.get('check_amount', 0)
                    credit_amount = delivery.get('remaining_amount', 0)
                    returned_qty = delivery.get('returned_quantity', 0)
                    returned_amount = delivery.get('returned_amount', 0)
                    
                    if delivery_status == 'موفق':
                        total_customers += 1
                        total_deliveries += 1
                        total_amount += invoice_amount
                        total_cash += cash_amount
                        total_check += check_amount
                        total_credit += credit_amount
                        total_return_qty += returned_qty
                        total_return_amount += returned_amount
            
            data_content.add_widget(RTLLabel(
                text=f'خلاصه عملکرد توزیع ({self.performance_from_date} تا {self.performance_to_date})',
                size_hint_y=None,
                height=dp(45),
                font_size=sp(20),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))
            
            row1 = BoxLayout(size_hint_y=None, height=dp(75), spacing=dp(7))
            row1.add_widget(self._make_card('روزهای کاری', f"{total_days:,}", (0.3, 0.6, 0.6, 1)))
            row1.add_widget(self._make_card('مشتریان توزیع شده', f"{total_customers:,}", (0.6, 0.4, 0.8, 1)))
            data_content.add_widget(row1)
            
            row2 = BoxLayout(size_hint_y=None, height=dp(75), spacing=dp(7))
            row2.add_widget(self._make_card('توزیع موفق', f"{total_deliveries:,}", (0.3, 0.5, 0.7, 1)))
            row2.add_widget(self._make_card('مبلغ کل توزیع', f"{total_amount:,}", (0.2, 0.6, 0.3, 1)))
            data_content.add_widget(row2)
            
            row3 = BoxLayout(size_hint_y=None, height=dp(75), spacing=dp(7))
            row3.add_widget(self._make_card('مبلغ نقدی', f"{total_cash:,}", (0.2, 0.5, 0.8, 1)))
            row3.add_widget(self._make_card('مبلغ چکی', f"{total_check:,}", (0.6, 0.3, 0.6, 1)))
            data_content.add_widget(row3)
            
            row4 = BoxLayout(size_hint_y=None, height=dp(75), spacing=dp(7))
            row4.add_widget(self._make_card('مبلغ نسیه', f"{total_credit:,}", (0.8, 0.4, 0.2, 1)))
            row4.add_widget(self._make_card('تعداد برگشتی', f"{total_return_qty:,}", (0.7, 0.5, 0.1, 1)))
            data_content.add_widget(row4)
            
            row5 = BoxLayout(size_hint_y=None, height=dp(75), spacing=dp(7))
            row5.add_widget(self._make_card('مبلغ برگشتی', f"{total_return_amount:,}", (0.8, 0.2, 0.2, 1)))
            avg_delivery = total_amount // total_deliveries if total_deliveries > 0 else 0
            row5.add_widget(self._make_card('میانگین هر توزیع', f"{avg_delivery:,}", (0.7, 0.4, 0.4, 1)))
            data_content.add_widget(row5)
            
            # خلاصه روزانه
            data_content.add_widget(RTLLabel(
                text='خلاصه روزانه توزیع',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(20),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))
            
            headers = ['تاریخ', 'مشتری', 'توزیع', 'مبلغ کل', 'نقدی', 'چکی', 'نسیه', 'برگشتی']
            header_box = BoxLayout(size_hint_y=None, height=dp(37), spacing=dp(2))
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
            
            for date in sorted(filtered_dates, reverse=True):
                if date not in all_deliveries or not isinstance(all_deliveries[date], list):
                    continue
                    
                day_customers = 0
                day_deliveries = 0
                day_amount = 0
                day_cash = 0
                day_check = 0
                day_credit = 0
                day_return_qty = 0
                day_return_amount = 0
                
                for delivery in all_deliveries[date]:
                    if not isinstance(delivery, dict):
                        continue
                    delivery_status = delivery.get('delivery_status', '')
                    invoice_amount = delivery.get('invoice_amount', 0)
                    cash_amount = delivery.get('cash_amount', 0)
                    check_amount = delivery.get('check_amount', 0)
                    credit_amount = delivery.get('remaining_amount', 0)
                    returned_qty = delivery.get('returned_quantity', 0)
                    returned_amount = delivery.get('returned_amount', 0)
                    
                    if delivery_status == 'موفق':
                        day_customers += 1
                        day_deliveries += 1
                        day_amount += invoice_amount
                        day_cash += cash_amount
                        day_check += check_amount
                        day_credit += credit_amount
                        day_return_qty += returned_qty
                        day_return_amount += returned_amount
                
                row = BoxLayout(size_hint_y=None, height=dp(35), spacing=dp(2))
                
                row.add_widget(RTLLabel(
                    text=date,
                    size_hint_x=1/len(headers),
                    font_size=sp(14),
                    color=(1, 1, 1, 1)
                ))
                row.add_widget(RTLLabel(
                    text=f"{day_customers:,}",
                    size_hint_x=1/len(headers),
                    font_size=sp(14),
                    color=(1, 1, 1, 1)
                ))
                row.add_widget(RTLLabel(
                    text=f"{day_deliveries:,}",
                    size_hint_x=1/len(headers),
                    font_size=sp(14),
                    color=(1, 1, 1, 1)
                ))
                row.add_widget(RTLLabel(
                    text=f"{day_amount:,}",
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
                    text=f"{day_credit:,}",
                    size_hint_x=1/len(headers),
                    font_size=sp(14),
                    color=(0.8, 0.4, 0.2, 1)
                ))
                row.add_widget(RTLLabel(
                    text=f"{day_return_qty:,}",
                    size_hint_x=1/len(headers),
                    font_size=sp(14),
                    color=(0.8, 0.2, 0.2, 1)
                ))
                
                data_content.add_widget(row)
            
            data_scroll.add_widget(data_content)
            content_layout.add_widget(data_scroll)
            
            self.content_area.add_widget(content_layout)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش عملکرد کلی توزیع: {e}", error_details)
    
    # ============================================================
    # بازنویسی متد تب ریز عملکرد
    # ============================================================
    
    def show_detail_tab(self):
        """نمایش تب ریز عملکرد برای موزع"""
        try:
            all_deliveries = get_all_deliveries()
            
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
            
            delivery_list = []
            for date, deliveries in all_deliveries.items():
                if self.detail_from_date and date < self.detail_from_date:
                    continue
                if self.detail_to_date and date > self.detail_to_date:
                    continue
                    
                if not isinstance(deliveries, list):
                    continue
                for delivery in deliveries:
                    if not isinstance(delivery, dict):
                        continue
                    delivery_list.append({
                        'date': date,
                        'route': delivery.get('route', ''),
                        'customer': delivery.get('customer_name', ''),
                        'delivery_status': delivery.get('delivery_status', ''),
                        'invoice_amount': delivery.get('invoice_amount', 0),
                        'cash_amount': delivery.get('cash_amount', 0),
                        'check_amount': delivery.get('check_amount', 0),
                        'credit_amount': delivery.get('remaining_amount', 0),
                        'returned_qty': delivery.get('returned_quantity', 0),
                        'returned_amount': delivery.get('returned_amount', 0),
                        'time': delivery.get('timestamp', '').split(' ')[-1] if ' ' in delivery.get('timestamp', '') else '',
                        'full_delivery': delivery.get('full_delivery', True)
                    })
            
            range_text = f"از {self.detail_from_date} تا {self.detail_to_date}" if self.detail_from_date and self.detail_to_date else today
            data_content.add_widget(RTLLabel(
                text=f'ریز عملکرد توزیع ({range_text})',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(22),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))
            
            if not delivery_list:
                data_content.add_widget(RTLLabel(
                    text='هیچ توزیعی در بازه انتخابی یافت نشد',
                    size_hint_y=None,
                    height=dp(35),
                    font_size=sp(16),
                    color=(0.5, 0.5, 0.5, 1)
                ))
                layout.add_widget(data_content)
                content_layout.add_widget(layout)
                self.content_area.add_widget(content_layout)
                return
            
            headers = ['تاریخ', 'مسیر', 'مشتری', 'وضعیت', 'مبلغ', 'نقدی', 'چکی', 'نسیه', 'برگشتی', 'ساعت']
            header_box = BoxLayout(size_hint_y=None, height=dp(37), spacing=dp(2))
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
            
            for item in sorted(delivery_list, key=lambda x: (x['date'], x['time']), reverse=True):
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
                
                status_color = (0.2, 0.7, 0.2, 1) if item['delivery_status'] == 'موفق' else (0.8, 0.3, 0.3, 1)
                row.add_widget(RTLLabel(
                    text=item['delivery_status'],
                    size_hint_x=1/len(headers),
                    font_size=sp(14),
                    color=status_color
                ))
                
                row.add_widget(RTLLabel(
                    text=f"{item['invoice_amount']:,.0f}",
                    size_hint_x=1/len(headers),
                    font_size=sp(14),
                    color=(1, 0.8, 0.2, 1)
                ))
                row.add_widget(RTLLabel(
                    text=f"{item['cash_amount']:,.0f}",
                    size_hint_x=1/len(headers),
                    font_size=sp(14),
                    color=(0.2, 0.5, 0.8, 1)
                ))
                row.add_widget(RTLLabel(
                    text=f"{item['check_amount']:,.0f}",
                    size_hint_x=1/len(headers),
                    font_size=sp(14),
                    color=(0.6, 0.3, 0.6, 1)
                ))
                row.add_widget(RTLLabel(
                    text=f"{item['credit_amount']:,.0f}",
                    size_hint_x=1/len(headers),
                    font_size=sp(14),
                    color=(0.8, 0.4, 0.2, 1)
                ))
                row.add_widget(RTLLabel(
                    text=f"{item['returned_qty']}",
                    size_hint_x=1/len(headers),
                    font_size=sp(14),
                    color=(0.8, 0.2, 0.2, 1)
                ))
                row.add_widget(RTLLabel(
                    text=item['time'],
                    size_hint_x=1/len(headers),
                    font_size=sp(14),
                    color=(1, 1, 1, 1)
                ))
                
                data_content.add_widget(row)
            
            layout.add_widget(data_content)
            content_layout.add_widget(layout)
            
            self.content_area.add_widget(content_layout)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش ریز عملکرد توزیع: {e}", error_details)

    # ============================================================
    # بازنویسی متدهای ارزیابی برای توزیع
    # ============================================================

    def _show_evaluation_dialog(self, from_date, to_date):
        """نمایش دیالوگ ارزیابی برای توزیع"""
        try:
            all_deliveries = get_all_deliveries()
            settings = get_settings()
            
            min_daily_hours = settings.get('min_daily_hours', 7)
            
            target_customers = settings.get('distributor_target_customers', 30)
            target_invoices = settings.get('distributor_target_invoices', 15)
            target_amount = settings.get('distributor_target_amount', 30000000)
            target_cash = settings.get('distributor_target_cash', 15000000)
            target_check = settings.get('distributor_target_check', 10000000)
            target_credit = settings.get('distributor_target_credit', 5000000)
            
            date_list = []
            for date in all_deliveries.keys():
                if from_date <= date <= to_date:
                    date_list.append(date)
            
            if not date_list:
                self.show_message('اطلاع', 'هیچ داده‌ای در بازه انتخابی وجود ندارد')
                return
            
            day_count = len(date_list)
            target_customers_day = target_customers * day_count
            target_invoices_day = target_invoices * day_count
            target_amount_day = target_amount * day_count
            target_cash_day = target_cash * day_count
            target_check_day = target_check * day_count
            target_credit_day = target_credit * day_count
            
            total_customers = 0
            total_invoices = 0
            total_amount = 0
            total_cash = 0
            total_check = 0
            total_credit = 0
            total_return_qty = 0
            total_return_amount = 0
            
            for date in date_list:
                if date in all_deliveries and isinstance(all_deliveries[date], list):
                    for delivery in all_deliveries[date]:
                        if not isinstance(delivery, dict):
                            continue
                        
                        delivery_status = delivery.get('delivery_status', '')
                        
                        if delivery_status == 'موفق':
                            total_customers += 1
                            total_invoices += 1
                            total_amount += delivery.get('invoice_amount', 0)
                            total_cash += delivery.get('cash_amount', 0)
                            total_check += delivery.get('check_amount', 0)
                            total_credit += delivery.get('remaining_amount', 0)
                            total_return_qty += delivery.get('returned_quantity', 0)
                            total_return_amount += delivery.get('returned_amount', 0)
            
            items = [
                {'name': 'تعداد مشتری توزیع شده', 'target': target_customers_day, 'actual': total_customers},
                {'name': 'تعداد توزیع موفق', 'target': target_invoices_day, 'actual': total_invoices},
                {'name': 'مبلغ کل توزیع', 'target': target_amount_day, 'actual': total_amount},
                {'name': 'مبلغ نقدی', 'target': target_cash_day, 'actual': total_cash},
                {'name': 'مبلغ چکی', 'target': target_check_day, 'actual': total_check},
                {'name': 'مبلغ نسیه', 'target': target_credit_day, 'actual': total_credit},
                {'name': 'تعداد برگشتی', 'target': 0, 'actual': total_return_qty},
                {'name': 'مبلغ برگشتی', 'target': 0, 'actual': total_return_amount},
            ]
            
            # ============================================================
            # ساخت دیالوگ ارزیابی
            # ============================================================
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
                diff_str = f"{diff:,.0f}" if diff != 0 else "0"
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
            
            eval_btn.bind(on_press=lambda x: self._show_evaluation_result(items, date_list, all_deliveries, popup))
            close_btn.bind(on_press=lambda x: popup.dismiss())
            
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش ارزیابی توزیع: {e}", error_details)


    def _calculate_evaluation(self, items, date_list, all_deliveries):
        """محاسبه ارزیابی کلامی برای توزیع"""
        try:
            settings = get_settings()
            
            work_start = settings.get('work_start_time', '08:00')
            first_setting = settings.get('first_visit_time', '09:00')
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
                if date in all_deliveries and isinstance(all_deliveries[date], list):
                    for delivery in all_deliveries[date]:
                        if not isinstance(delivery, dict):
                            continue
                        
                        timestamp = delivery.get('timestamp', '')
                        delivery_status = delivery.get('delivery_status', '')
                        
                        if timestamp and ' ' in timestamp:
                            time_part = timestamp.split(' ')[1]
                            if first_log_time is None:
                                first_log_time = time_part
                            last_log_time = time_part
                            
                            if delivery_status == 'موفق':
                                if first_successful_time is None:
                                    first_successful_time = time_part
                                last_successful_time = time_part
            
            actual_clock_in = first_log_time if first_log_time else work_start
            actual_first_visit = first_successful_time if first_successful_time else first_setting
            actual_last_visit = last_successful_time if last_successful_time else '---'
            actual_clock_out = last_log_time if last_log_time else '---'
            
            # محاسبه زمان کار مفید
            def time_diff(t1, t2):
                try:
                    if t1 == '---' or t2 == '---':
                        return 0
                    h1, m1 = map(int, t1.split(':'))
                    h2, m2 = map(int, t2.split(':'))
                    return (h2 * 60 + m2) - (h1 * 60 + m1)
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
                if item['name'] not in ['تعداد برگشتی', 'مبلغ برگشتی']:
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
            print(f"خطا در محاسبه ارزیابی توزیع: {e}")
            return "خطا در محاسبه", (0.5, 0.5, 0.5, 1), "خطا", (0.5, 0.5, 0.5, 1), 0, "۰"  
        
    def _show_evaluation_result(self, items, date_list, all_deliveries, parent_popup=None):
        """نمایش دیالوگ جداگانه برای جزئیات ارزیابی توزیع"""
        try:
            if parent_popup and hasattr(parent_popup, 'dismiss'):
                try:
                    parent_popup.dismiss()
                except:
                    pass

            eval_text, eval_color, work_msg, work_color, avg_percent, work_time_display = self._calculate_evaluation(
                items, date_list, all_deliveries
            )
            
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
                text='نتیجه ارزیابی عملکرد توزیع',
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
            
            for item in items:
                if item['target'] > 0:
                    percent = (item['actual'] / item['target']) * 100
                else:
                    percent = 0
                
                if percent < 50:
                    percent_color = (0.8, 0.2, 0.2, 1)
                elif percent < 70:
                    percent_color = (1, 0.5, 0, 1)
                elif percent < 85:
                    percent_color = (1, 0.8, 0, 1)
                elif percent < 100:
                    percent_color = (0.2, 0.8, 0.2, 1)
                else:
                    percent_color = (0, 0.6, 0, 1)
                
                row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(2))
                
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
                    text=f"{percent:.1f}%",
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
            
            total_height = 45 + 45 + 50 + 40 + 38 + len(items) * 38 + 40 + 38 + 38 + 20
            detail_content.height = dp(total_height)
            detail_scroll.add_widget(detail_content)
            dialog_content.add_widget(detail_scroll)
            
            btn_layout = BoxLayout(
                size_hint_y=None, 
                height=dp(55), 
                spacing=dp(10),
                padding=dp(5)
            )
            
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
                self_assessment_btn.bind(
                    on_press=lambda x: self._open_self_assessment_from_evaluation(
                        detail_popup, items, date_list, all_deliveries
                    )
                )
            
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
            
            close_btn.bind(on_press=lambda x: detail_popup.dismiss())
            
            if is_today:
                self_assessment_btn.bind(
                    on_press=lambda x: self._open_self_assessment_from_evaluation(
                        detail_popup, items, date_list, all_deliveries
                    )
                )
            
            detail_popup.open()

        except Exception as e:
            print(f"خطا در نمایش جزئیات ارزیابی توزیع: {e}")
            import traceback
            traceback.print_exc()

    # ============================================================
    # متدهای خودآزمایی برای توزیع
    # ============================================================

    def show_self_assessment_dialog(self, items=None, date_list=None, all_deliveries=None):
        """نمایش دیالوگ خودآزمایی برای توزیع"""
        try:
            if self._self_assessment_popup and self._self_assessment_popup._window:
                return
            
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
            
            if items and date_list and all_deliveries:
                eval_text, eval_color, work_msg, work_color, avg_percent, work_time_display = self._calculate_evaluation(
                    items, date_list, all_deliveries
                )
                
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
            
            def on_confirm(instance):
                if self.selected_score is not None:
                    self.save_self_score(self.selected_score)
                    popup.dismiss()
                    self._self_assessment_shown = False
                    self._is_processing = False
                    self.show_message('موفق', 'نمره خودآزمایی با موفقیت ثبت شد.')
            
            confirm_btn.bind(on_press=on_confirm)
            self._self_assessment_popup = popup
            self._self_assessment_confirm = confirm_btn
            
            popup.bind(on_dismiss=self._on_self_assessment_dismiss)
            popup.open()
            
            Clock.schedule_once(lambda dt: setattr(self, '_is_processing', False), 1)

        except Exception as e:
            self._is_processing = False
            self._self_assessment_shown = False
            print(f"خطا در نمایش دیالوگ خودآزمایی توزیع: {e}")
            import traceback
            traceback.print_exc()


    def _open_self_assessment_from_evaluation(self, popup, items=None, date_list=None, all_deliveries=None):
        """باز کردن دیالوگ خودآزمایی از داخل دیالوگ ارزیابی توزیع"""
        try:
            if popup and hasattr(popup, 'dismiss'):
                try:
                    popup.dismiss()
                except:
                    pass
            
            if self._is_processing:
                return
            
            if self._self_assessment_shown:
                return
            
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
            
            self._self_assessment_shown = True
            self.show_self_assessment_dialog(items, date_list, all_deliveries)
            
        except Exception as e:
            self._self_assessment_shown = False
            print(f"خطا در باز کردن خودآزمایی توزیع: {e}")
            import traceback
            traceback.print_exc()


    def _on_self_assessment_dismiss(self, instance):
        """مدیریت بسته شدن دیالوگ خودآزمایی"""
        try:
            self._self_assessment_shown = False
            self._is_processing = False
            self._self_assessment_popup = None
            
        except Exception as e:
            print(f"خطا در بستن خودآزمایی توزیع: {e}")

    def show_stats_tab(self):
        """نمایش تب آمار و ارزیابی برای موزع"""
        try:
            layout = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
            
            layout.add_widget(RTLLabel(
                text='آمار و ارزیابی عملکرد توزیع',
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
            
            # ============================================================
            # دکمه تاریخچه گزارشات (اضافه شده)
            # ============================================================
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
            ErrorPopup.show_error(f"خطا در نمایش آمار و ارزیابی توزیع: {e}", error_details)

    # ============================================================
    # بازنویسی متد خروجی اکسل
    # ============================================================
    
    def export_excel(self, instance):
        """خروجی اکسل مخصوص توزیع"""
        try:
            self.loading_popup = self.show_message('در حال ساخت', 'لطفاً صبر کنید...')
            
            filtered_data = None
            
            if self.current_tab == 0:
                if hasattr(self, '_current_performance_data') and self._current_performance_data:
                    all_deliveries = get_all_deliveries()
                    filtered_data = {}
                    for date in self._current_performance_data:
                        if date in all_deliveries:
                            filtered_data[date] = all_deliveries[date]
            
            elif self.current_tab == 1:
                all_deliveries = get_all_deliveries()
                filtered_data = {}
                for date, deliveries in all_deliveries.items():
                    if self.detail_from_date and date < self.detail_from_date:
                        continue
                    if self.detail_to_date and date > self.detail_to_date:
                        continue
                    filtered_data[date] = deliveries
            
            if not filtered_data:
                filtered_data = None
            
            def do_export():
                success, result = export_distributor_to_excel(filtered_data)
                
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
                            'فایل اکسل توزیع با موفقیت ساخته شد!\n\n'
                            'فایل در پوشه Downloads ذخیره شد.'
                        )
                    else:
                        self.show_message('خطا', f'خطا در ساخت اکسل:\n{result}')
                
                Clock.schedule_once(show_result, 1)
            
            thread = threading.Thread(target=do_export, daemon=True)
            thread.start()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در خروجی اکسل توزیع: {e}", error_details)