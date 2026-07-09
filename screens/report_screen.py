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
from utils.file_manager import get_daily_logs, load_json, save_json, get_data_path, get_settings
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
            self.selected_files = {}  # برای ذخیره وضعیت انتخاب فایل‌ها
            self.history_popup = None  # برای دسترسی به popup تاریخچه
            self.build_ui()
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت ReportScreen: {e}", error_details)
            raise
    
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def _on_field_focus(self, instance, value):
        """وقتی فیلد فوکوس میشه"""
        if value:
            Clock.schedule_once(lambda dt: self._select_all_text(instance), 0.1)

    def _select_all_text(self, instance):
        """انتخاب کل متن فیلد"""
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
    # تب عملکرد کلی
    # ============================================================
    
    def show_performance_tab(self):
        try:
            summary_file = 'daily_summary.json'
            summary_path = os.path.join(get_data_path(), summary_file)
            
            if os.path.exists(summary_path):
                all_summaries = load_json(summary_file)
            else:
                all_summaries = {}
            
            # محاسبه فروش نقدی و چکی از daily_log
            all_logs = get_daily_logs()
            total_cash = 0
            total_check = 0
            total_new_customers = 0
            
            for date, logs in all_logs.items():
                if not isinstance(logs, list):
                    continue
                for log in logs:
                    if not isinstance(log, dict):
                        continue
                    sales_status = log.get('sales_status', '')
                    payment_method = log.get('payment_method', '')
                    sales_amount = log.get('sales_amount', 0)
                    if sales_status == 'موفق' and sales_amount > 0:
                        if payment_method == 'نقد':
                            total_cash += sales_amount
                        elif payment_method == 'چک':
                            total_check += sales_amount
                    if log.get('is_new_customer', False):
                        total_new_customers += 1
            
            layout = ScrollView()
            content = GridLayout(cols=1, spacing=dp(8), size_hint_y=None, padding=dp(8))
            content.bind(minimum_height=content.setter('height'))
            
            if not all_summaries:
                content.add_widget(RTLLabel(
                    text='هیچ خلاصه عملکردی ثبت نشده است',
                    size_hint_y=None,
                    height=dp(45),
                    font_size=sp(18),
                    color=(0.5, 0.5, 0.5, 1)
                ))
                layout.add_widget(content)
                self.content_area.add_widget(layout)
                return
            
            total_days = len(all_summaries)
            total_visits = 0
            total_invoices = 0
            total_units = 0
            total_sales = 0
            
            for date, summary in all_summaries.items():
                try:
                    total_visits += int(summary.get('visited_customers_count', 0))
                    total_invoices += int(summary.get('successful_invoices_count', 0))
                    total_units += int(summary.get('successful_units_count', 0))
                    total_sales += int(summary.get('successful_sales_amount', 0))
                except:
                    pass
            
            content.add_widget(RTLLabel(
                text='خلاصه عملکرد کلی',
                size_hint_y=None,
                height=dp(45),
                font_size=sp(20),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))
            
            row1 = BoxLayout(size_hint_y=None, height=dp(75), spacing=dp(7))
            row1.add_widget(self._make_card('روزهای کاری', f"{total_days:,}", (0.3, 0.6, 0.6, 1)))
            row1.add_widget(self._make_card('کل ویزیت‌ها', f"{total_visits:,}", (0.6, 0.4, 0.8, 1)))
            content.add_widget(row1)
            
            row2 = BoxLayout(size_hint_y=None, height=dp(75), spacing=dp(7))
            row2.add_widget(self._make_card('فاکتورها', f"{total_invoices:,}", (0.3, 0.5, 0.7, 1)))
            row2.add_widget(self._make_card('واحد فروش', f"{total_units:,}", (0.5, 0.3, 0.7, 1)))
            content.add_widget(row2)
            
            row3 = BoxLayout(size_hint_y=None, height=dp(75), spacing=dp(7))
            row3.add_widget(self._make_card('کل مبلغ فروش', f"{total_sales:,}", (0.2, 0.6, 0.3, 1)))
            row3.add_widget(self._make_card('فروش نقدی', f"{total_cash:,}", (0.2, 0.5, 0.8, 1)))
            content.add_widget(row3)
            
            row4 = BoxLayout(size_hint_y=None, height=dp(75), spacing=dp(7))
            row4.add_widget(self._make_card('فروش چکی', f"{total_check:,}", (0.6, 0.3, 0.6, 1)))
            row4.add_widget(self._make_card('مشتری جدید', f"{total_new_customers:,}", (0.2, 0.8, 0.4, 1)))
            content.add_widget(row4)
            
            row5 = BoxLayout(size_hint_y=None, height=dp(75), spacing=dp(7))
            avg_sale = total_sales // total_visits if total_visits > 0 else 0
            row5.add_widget(self._make_card('میانگین هر ویزیت', f"{avg_sale:,}", (0.7, 0.4, 0.4, 1)))
            row5.add_widget(Label())
            content.add_widget(row5)
            
            content.add_widget(RTLLabel(
                text='خلاصه روزانه',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(20),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))
            
            header_box = BoxLayout(size_hint_y=None, height=dp(37), spacing=dp(2))
            headers = ['تاریخ', 'ویزیت', 'فاکتور', 'واحد', 'فروش', 'نقدی', 'چکی', 'مشتری جدید']
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
            content.add_widget(header_box)
            
            for date, summary in sorted(all_summaries.items(), reverse=True):
                day_cash = 0
                day_check = 0
                day_new_customers = 0
                
                if date in all_logs and isinstance(all_logs[date], list):
                    for log in all_logs[date]:
                        if not isinstance(log, dict):
                            continue
                        sales_status = log.get('sales_status', '')
                        payment_method = log.get('payment_method', '')
                        sales_amount = log.get('sales_amount', 0)
                        if sales_status == 'موفق' and sales_amount > 0:
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
                    text=f"{int(summary.get('visited_customers_count', 0)):,}",
                    size_hint_x=1/len(headers),
                    font_size=sp(14),
                    color=(1, 1, 1, 1)
                ))
                row.add_widget(RTLLabel(
                    text=f"{int(summary.get('successful_invoices_count', 0)):,}",
                    size_hint_x=1/len(headers),
                    font_size=sp(14),
                    color=(1, 1, 1, 1)
                ))
                row.add_widget(RTLLabel(
                    text=f"{int(summary.get('successful_units_count', 0)):,}",
                    size_hint_x=1/len(headers),
                    font_size=sp(14),
                    color=(1, 1, 1, 1)
                ))
                row.add_widget(RTLLabel(
                    text="{:,}".format(int(summary.get('successful_sales_amount', '0'))),
                    size_hint_x=1/len(headers),
                    font_size=sp(14),
                    color=(1, 0.8, 0.2, 1)
                ))
                row.add_widget(RTLLabel(
                    text="{:,}".format(day_cash),
                    size_hint_x=1/len(headers),
                    font_size=sp(14),
                    color=(0.2, 0.5, 0.8, 1)
                ))
                row.add_widget(RTLLabel(
                    text="{:,}".format(day_check),
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
                
                content.add_widget(row)
            
            layout.add_widget(content)
            self.content_area.add_widget(layout)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش عملکرد کلی: {e}", error_details)
    
    # ============================================================
    # تب ریز عملکرد
    # ============================================================
    
    def show_detail_tab(self):
        try:
            all_logs = get_daily_logs()
            
            layout = ScrollView()
            content = GridLayout(cols=1, spacing=dp(4), size_hint_y=None, padding=dp(8))
            content.bind(minimum_height=content.setter('height'))
            
            if not all_logs:
                content.add_widget(RTLLabel(
                    text='هیچ ریز عملکردی ثبت نشده است',
                    size_hint_y=None,
                    height=dp(45),
                    font_size=sp(18),
                    color=(0.5, 0.5, 0.5, 1)
                ))
                layout.add_widget(content)
                self.content_area.add_widget(layout)
                return
            
            visit_list = []
            for date, logs in all_logs.items():
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
            
            content.add_widget(RTLLabel(
                text='ریز عملکرد (همه ویزیت‌ها)',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(22),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))
            
            if not visit_list:
                content.add_widget(RTLLabel(
                    text='هیچ ویزیتی ثبت نشده است',
                    size_hint_y=None,
                    height=dp(35),
                    font_size=sp(16),
                    color=(0.5, 0.5, 0.5, 1)
                ))
                layout.add_widget(content)
                self.content_area.add_widget(layout)
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
            content.add_widget(header_box)
            
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
                
                content.add_widget(row)
            
            layout.add_widget(content)
            self.content_area.add_widget(layout)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش ریز عملکرد: {e}", error_details)
    
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
                text='✓ انتخاب همه',
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
                text='🗑 حذف انتخابی',
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
                text='🧹 حذف قدیمی‌ها',
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
                text='📁 باز کردن',
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
                title='تاریخچه',
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
        """تغییر وضعیت انتخاب فایل"""
        if hasattr(self, 'selected_files'):
            self.selected_files[file_path] = value
    
    def _select_all_files(self, instance):
        """انتخاب همه فایل‌ها"""
        if not hasattr(self, 'selected_files') or not self.selected_files:
            self.show_message('توجه', 'هیچ فایلی برای انتخاب وجود ندارد')
            return
        
        for path in self.selected_files.keys():
            self.selected_files[path] = True
        
        self._update_checkboxes(True)
        
        self.show_message('توجه', f'{len(self.selected_files)} فایل انتخاب شد')
    
    def _update_checkboxes(self, value):
        """به‌روزرسانی وضعیت چک‌باکس‌ها"""
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
        """حذف فایل‌های انتخاب شده"""
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
                title='تایید حذف',
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
        """پس از اتمام حذف فایل‌ها"""
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
        """پاکسازی فایل‌های قدیمی‌تر از ۳۰ روز"""
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
                title='پاکسازی فایل‌های قدیمی',
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
        """پس از اتمام پاکسازی"""
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
        """باز کردن پوشه بکاپ"""
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
                    
                    intent = Intent()
                    intent.setAction(Intent.ACTION_VIEW)
                    uri = Uri.fromFile(File(backup_path))
                    intent.setDataAndType(uri, 'resource/folder')
                    mActivity.startActivity(intent)
                except Exception as e:
                    self.show_message('خطا', f'امکان باز کردن پوشه وجود ندارد:\n{e}')
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
        """ارسال فایل با استفاده از Intent در اندروید"""
        try:
            from kivy.utils import platform
            
            if platform == 'android':
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
                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                
                mActivity.startActivity(intent)
                
            else:
                # ✅ برای دسکتاپ - باز کردن پوشه حاوی فایل
                import os
                import subprocess
                folder_path = os.path.dirname(file_path)
                
                if platform == 'win':
                    os.startfile(folder_path)
                elif platform == 'linux':
                    subprocess.Popen(['xdg-open', folder_path])
                elif platform == 'macosx':
                    subprocess.Popen(['open', folder_path])
                else:
                    # fallback: نمایش مسیر
                    self.show_message('مسیر فایل', f'فایل در مسیر زیر ذخیره شده است:\n{file_path}')
                    
        except Exception as e:
            print(f"خطا در ارسال فایل: {e}")
            import traceback
            traceback.print_exc()
            ErrorPopup.show_error(f"خطا در ارسال فایل: {e}")
    
    # ============================================================
    # دیالوگ ارزیابی روز جاری
    # ============================================================
    
    def show_daily_evaluation(self, instance):
        try:
            today = get_today_jalali()
            self._show_evaluation_dialog(today, today)
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش ارزیابی روز: {e}", error_details)
    
    # ============================================================
    # دیالوگ ارزیابی دوره
    # ============================================================
    
    def show_period_evaluation(self, instance):
        try:
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
            
            popup = PersianPopup(
                title='ارزیابی دوره',
                content=content,
                size_hint=(0.9, 0.5),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )
            
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
        try:
            all_logs = get_daily_logs()
            all_summaries = load_json('daily_summary.json') if os.path.exists(os.path.join(get_data_path(), 'daily_summary.json')) else {}
            settings = get_settings()
            
            total_visits = 0
            total_invoices = 0
            total_units = 0
            total_sales = 0
            total_cash = 0
            total_check = 0
            total_credit = 0
            total_new_customers = 0
            
            day_count = 0
            
            date_list = []
            for date in all_logs.keys():
                if from_date <= date <= to_date:
                    date_list.append(date)
                    day_count += 1
            
            if day_count == 0:
                self.show_message('اطلاع', 'هیچ داده‌ای در بازه انتخابی وجود ندارد')
                return
            
            target_visits_per_day = settings.get('target_customer_count', 50)
            target_invoices_per_day = settings.get('target_invoice_count', 20)
            target_units_per_day = settings.get('target_count', 100)
            target_sales_per_day = settings.get('target_amount', 50000000)
            target_cash_per_day = settings.get('target_cash_sales', 30000000)
            target_credit_per_day = settings.get('target_credit_sales', 20000000)
            
            target_visits = target_visits_per_day * day_count
            target_invoices = target_invoices_per_day * day_count
            target_units = target_units_per_day * day_count
            target_sales = target_sales_per_day * day_count
            target_cash = target_cash_per_day * day_count
            target_credit = target_credit_per_day * day_count
            
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
                {'name': 'تعداد ویزیت', 'target': target_visits, 'actual': total_visits},
                {'name': 'تعداد فاکتور', 'target': target_invoices, 'actual': total_invoices},
                {'name': 'واحد فروش', 'target': target_units, 'actual': total_units},
                {'name': 'مبلغ فروش', 'target': target_sales, 'actual': total_sales},
                {'name': 'فروش نقدی', 'target': target_cash, 'actual': total_cash},
                {'name': 'فروش چکی', 'target': target_credit, 'actual': total_check},
                {'name': 'فروش اعتباری', 'target': target_credit, 'actual': total_credit},
                {'name': 'مشتری جدید', 'target': 0, 'actual': total_new_customers},
            ]
            
            content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
            with content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                        size=lambda i, v: setattr(content_rect, 'size', v))
            
            table_container = BoxLayout(
                orientation='vertical',
                size_hint_y=0.9,
                spacing=dp(2),
                padding=dp(3)
            )
            
            header_box = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(2))
            headers = ['آیتم', 'هدف', 'عملکرد', 'نتیجه']
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
                text='ارزیابی',
                background_color=(0.2, 0.6, 1, 1),
                size_hint_y=None,
                height=dp(40),
                color=(1, 1, 1, 1),
                font_size=sp(15)
            )
            content.add_widget(eval_btn)
            
            result_box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(1))
            content.add_widget(result_box)
            
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
            
            popup = PersianPopup(
                title='ارزیابی',
                content=content,
                size_hint=(0.92, 0.82),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )
            
            eval_btn.bind(on_press=lambda x: self._show_evaluation_result(result_box, items, date_list, all_logs))
            close_btn.bind(on_press=lambda x: popup.dismiss())
            
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش ارزیابی: {e}", error_details)
    
    # ============================================================
    # نمایش نتیجه ارزیابی
    # ============================================================
    
    def _show_evaluation_result(self, result_box, items, date_list, all_logs):
        try:
            total_target = 0
            total_actual = 0
            sale_items = ['مبلغ فروش', 'تعداد فاکتور', 'واحد فروش']
            for item in items:
                if item['name'] in sale_items:
                    total_target += item['target']
                    total_actual += item['actual']
            
            percent = (total_actual / total_target * 100) if total_target > 0 else 0
            
            if percent < 65:
                sales_msg = 'به اندازه کافی تلاش نکردم'
                sales_color = (0.5, 0.5, 0.5, 1)
            elif percent < 75:
                sales_msg = 'باید بیشتر تلاش کنم'
                sales_color = (1, 0.5, 0, 1)
            elif percent < 85:
                sales_msg = 'تلاشم داره نتیجه میده'
                sales_color = (1, 0.8, 0, 1)
            elif percent < 100:
                sales_msg = 'تا موفقیت راهی نیست'
                sales_color = (0.2, 0.5, 1, 1)
            else:
                sales_msg = 'به خودم افتخار میکنم'
                sales_color = (0.2, 0.7, 0.2, 1)
            
            first_visit_target = '09:00'
            work_start_target = '08:00'
            min_hours = 6
            
            all_times = []
            for date in date_list:
                if date in all_logs and isinstance(all_logs[date], list):
                    for log in all_logs[date]:
                        if not isinstance(log, dict):
                            continue
                        visit_status = log.get('visit_status', '')
                        log_time = log.get('time', '')
                        if visit_status == 'موفق' and log_time:
                            all_times.append(log_time)
            
            first_actual = all_times[0] if all_times else '--:--'
            last_actual = all_times[-1] if all_times else '--:--'
            
            def time_diff(t1, t2):
                try:
                    h1, m1 = map(int, t1.split(':'))
                    h2, m2 = map(int, t2.split(':'))
                    diff_minutes = (h2 * 60 + m2) - (h1 * 60 + m1)
                    return diff_minutes
                except:
                    return 0
            
            work_hours = 0
            work_minutes = 0
            if first_actual != '--:--' and last_actual != '--:--':
                diff_min = time_diff(first_actual, last_actual)
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
            
            result_box.clear_widgets()
            result_box.height = dp(1)
            
            result_content = BoxLayout(orientation='vertical', spacing=dp(5), size_hint_y=None)
            
            result_content.add_widget(RTLLabel(
                text='نتیجه ارزیابی',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(24),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))
            
            result_content.add_widget(RTLLabel(
                text=f'عملکرد فروش: {percent:.1f}% - {sales_msg}',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(22),
                color=sales_color
            ))
            
            result_content.add_widget(RTLLabel(
                text='ارزیابی زمان:',
                size_hint_y=None,
                height=dp(25),
                font_size=sp(22),
                bold=True,
                color=(1, 1, 1, 1)
            ))
            
            if first_actual != '--:--':
                diff = time_diff(work_start_target, first_actual)
                if diff > 0:
                    result_content.add_widget(RTLLabel(
                        text=f'{diff} دقیقه دیر کردم',
                        size_hint_y=None,
                        height=dp(25),
                        font_size=sp(20),
                        color=(1, 0.5, 0, 1)
                    ))
                else:
                    result_content.add_widget(RTLLabel(
                        text='در شروع کار تاخیر نداشتم',
                        size_hint_y=None,
                        height=dp(25),
                        font_size=sp(20),
                        color=(0.2, 0.7, 0.2, 1)
                    ))
            
            result_content.add_widget(RTLLabel(
                text=f'کارکرد مفید: {work_hours} ساعت و {work_minutes} دقیقه',
                size_hint_y=None,
                height=dp(25),
                font_size=sp(22),
                color=(1, 1, 1, 1)
            ))
            
            result_content.add_widget(RTLLabel(
                text=work_msg,
                size_hint_y=None,
                height=dp(30),
                font_size=sp(22),
                color=work_color
            ))
            
            result_content.height = dp(200)
            result_box.add_widget(result_content)
            result_box.height = dp(200)
            
        except Exception as e:
            print(f"خطا در نمایش نتیجه ارزیابی: {e}")
            import traceback
            traceback.print_exc()
    
    # ============================================================
    # توابع کمکی
    # ============================================================
    
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
            
            def do_export():
                success, result = export_to_excel()
                
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
            btn.bind(on_press=popup.dismiss)
            
            Clock.schedule_once(lambda dt: popup.open(), 0.1)
            
            return popup
            
        except Exception as e:
            print(f"خطا در نمایش پیام: {e}")
            import traceback
            traceback.print_exc()
            return None