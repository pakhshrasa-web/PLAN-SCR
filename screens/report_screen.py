# screens/report_screen.py
# ========== صفحه گزارش‌ها ==========

import traceback
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, Rectangle

from utils.rtl_widgets import PersianButton, RTLLabel
from utils.file_manager import get_daily_logs
from utils.excel_exporter import export_to_excel
from error_handler import ErrorPopup


class ReportScreen(Screen):
    def __init__(self, **kwargs):
        try:
            super().__init__(**kwargs)
            # پس‌زمینه تیره
            with self.canvas.before:
                Color(0.08, 0.08, 0.08, 1)
                self.bg_rect = Rectangle(pos=self.pos, size=self.size)
                self.bind(pos=self._update_bg, size=self._update_bg)
            self.build_ui()
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت ReportScreen: {e}", error_details)
            raise
    
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def build_ui(self):
        try:
            layout = BoxLayout(orientation='vertical')
            
            header = RTLLabel(
                text='📊 گزارش عملکرد',
                size_hint_y=0.07,
                font_size=sp(20),
                color=(1, 1, 1, 1)
            )
            layout.add_widget(header)
            
            stats_scroll = ScrollView(size_hint_y=0.5)
            self.stats_layout = GridLayout(cols=1, spacing=dp(8), size_hint_y=None, padding=dp(15))
            self.stats_layout.bind(minimum_height=self.stats_layout.setter('height'))
            stats_scroll.add_widget(self.stats_layout)
            layout.add_widget(stats_scroll)
            
            btn_layout = BoxLayout(size_hint_y=0.12, spacing=dp(10), padding=dp(10))
            
            refresh_btn = PersianButton(
                text='🔄 تازه سازی',
                background_color=(0.4, 0.4, 0.8, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1)
            )
            refresh_btn.bind(on_press=self.refresh_stats)
            btn_layout.add_widget(refresh_btn)
            
            excel_btn = PersianButton(
                text='📎 خروجی Excel',
                background_color=(0.2, 0.6, 0.2, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1)
            )
            excel_btn.bind(on_press=self.export_excel)
            btn_layout.add_widget(excel_btn)
            
            pdf_btn = PersianButton(
                text='📄 خروجی PDF',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1)
            )
            pdf_btn.bind(on_press=self.export_pdf)
            btn_layout.add_widget(pdf_btn)
            
            back_btn = PersianButton(
                text='🔙 بازگشت',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1)
            )
            back_btn.bind(on_press=self.go_back)
            btn_layout.add_widget(back_btn)
            
            layout.add_widget(btn_layout)
            self.add_widget(layout)
            
            self.refresh_stats(None)
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت UI ReportScreen: {e}", error_details)
            raise
    
    def refresh_stats(self, instance):
        try:
            self.stats_layout.clear_widgets()
            
            logs = get_daily_logs()
            
            if not logs:
                self.stats_layout.add_widget(RTLLabel(
                    text='📭 هیچ داده‌ای وجود ندارد',
                    size_hint_y=None,
                    height=dp(50),
                    font_size=sp(16),
                    color=(0.5, 0.5, 0.5, 1)
                ))
                return
            
            total_sales = 0
            total_invoices = 0
            total_visits = 0
            total_units = 0
            
            for date, log in logs.items():
                try:
                    sales_val = log.get('successful_sales_amount', '0')
                    total_sales += int(sales_val) if str(sales_val).isdigit() else 0
                    total_invoices += int(log.get('successful_invoices_count', '0')) if str(log.get('successful_invoices_count', '0')).isdigit() else 0
                    total_visits += int(log.get('visited_customers_count', '0')) if str(log.get('visited_customers_count', '0')).isdigit() else 0
                    total_units += int(log.get('successful_units_count', '0')) if str(log.get('successful_units_count', '0')).isdigit() else 0
                except:
                    pass
            
            self.stats_layout.add_widget(RTLLabel(
                text='📊 خلاصه آمار کل',
                size_hint_y=None,
                height=dp(45),
                font_size=sp(18),
                bold=True,
                color=(1, 1, 1, 1)
            ))
            
            stats_row1 = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(10))
            card1 = self.make_stat_card('💰 کل فروش', f"{total_sales:,}", 'Rial', (0.2, 0.6, 0.2, 1))
            card2 = self.make_stat_card('🧾 فاکتورها', str(total_invoices), '', (0.2, 0.5, 0.8, 1))
            stats_row1.add_widget(card1)
            stats_row1.add_widget(card2)
            self.stats_layout.add_widget(stats_row1)
            
            stats_row2 = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(10))
            card3 = self.make_stat_card('👥 ویزیت‌ها', str(total_visits), '', (0.8, 0.5, 0.2, 1))
            card4 = self.make_stat_card('📦 واحد فروش', str(total_units), '', (0.6, 0.3, 0.7, 1))
            stats_row2.add_widget(card3)
            stats_row2.add_widget(card4)
            self.stats_layout.add_widget(stats_row2)
            
            stats_row3 = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(10))
            card5 = self.make_stat_card('📅 روزهای کاری', str(len(logs)), '', (0.3, 0.6, 0.6, 1))
            avg_sale = total_sales // total_invoices if total_invoices > 0 else 0
            card6 = self.make_stat_card('📈 میانگین فاکتور', f"{avg_sale:,}", 'Rial', (0.7, 0.4, 0.4, 1))
            stats_row3.add_widget(card5)
            stats_row3.add_widget(card6)
            self.stats_layout.add_widget(stats_row3)
            
            if total_visits > 0:
                avg_per_visit = total_sales // total_visits
                stats_row4 = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(10))
                card7 = self.make_stat_card('🎯 فروش هر ویزیت', f"{avg_per_visit:,}", 'Rial', (0.4, 0.5, 0.3, 1))
                stats_row4.add_widget(card7)
                self.stats_layout.add_widget(stats_row4)
            
            self.stats_layout.add_widget(Label(text='', size_hint_y=None, height=dp(10)))
            self.stats_layout.add_widget(RTLLabel(
                text='📋 لیست ویزیت‌های ثبت شده',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(16),
                bold=True,
                color=(1, 1, 1, 1)
            ))
            
            header_box = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(2))
            header_date = PersianButton(
                text='تاریخ',
                size_hint_x=0.25,
                background_color=(0.2, 0.5, 0.8, 1),
                color=(1, 1, 1, 1),
                size_hint_y=None,
                height=dp(35)
            )
            header_visit = PersianButton(
                text='ویزیت',
                size_hint_x=0.25,
                background_color=(0.2, 0.5, 0.8, 1),
                color=(1, 1, 1, 1),
                size_hint_y=None,
                height=dp(35)
            )
            header_invoice = PersianButton(
                text='فاکتور',
                size_hint_x=0.25,
                background_color=(0.2, 0.5, 0.8, 1),
                color=(1, 1, 1, 1),
                size_hint_y=None,
                height=dp(35)
            )
            header_sales = PersianButton(
                text='فروش (ریال)',
                size_hint_x=0.25,
                background_color=(0.2, 0.5, 0.8, 1),
                color=(1, 1, 1, 1),
                size_hint_y=None,
                height=dp(35)
            )
            header_box.add_widget(header_date)
            header_box.add_widget(header_visit)
            header_box.add_widget(header_invoice)
            header_box.add_widget(header_sales)
            self.stats_layout.add_widget(header_box)
            
            sorted_logs = sorted(logs.items(), key=lambda x: x[0], reverse=True)
            
            for idx, (date, log) in enumerate(sorted_logs):
                row_box = BoxLayout(size_hint_y=None, height=dp(35), spacing=dp(2))
                row_box.add_widget(RTLLabel(
                    text=date,
                    size_hint_x=0.25,
                    color=(1, 1, 1, 1)
                ))
                row_box.add_widget(RTLLabel(
                    text=log.get('visited_customers_count', '0'),
                    size_hint_x=0.25,
                    color=(1, 1, 1, 1)
                ))
                row_box.add_widget(RTLLabel(
                    text=log.get('successful_invoices_count', '0'),
                    size_hint_x=0.25,
                    color=(1, 1, 1, 1)
                ))
                
                sales = log.get('successful_sales_amount', '0')
                sales_num = int(sales) if str(sales).isdigit() else 0
                row_box.add_widget(RTLLabel(
                    text=f"{sales_num:,}",
                    size_hint_x=0.25,
                    color=(1, 0.8, 0.2, 1)  # طلایی
                ))
                
                self.stats_layout.add_widget(row_box)
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در به‌روزرسانی آمار: {e}", error_details)
    
    def make_stat_card(self, title, value, unit, color):
        try:
            card = BoxLayout(
                orientation='vertical',
                size_hint_x=0.5,
                size_hint_y=None,
                height=dp(60),
                padding=dp(5),
                spacing=dp(2)
            )
            
            with card.canvas.before:
                Color(*color)
                card.bg_rect = Rectangle(pos=card.pos, size=card.size)
                card.bind(pos=self._update_card_bg, size=self._update_card_bg)
            
            title_label = RTLLabel(
                text=title,
                size_hint_y=None,
                height=dp(20),
                font_size=sp(12),
                color=(1, 1, 1, 1)
            )
            value_label = RTLLabel(
                text=f"{value} {unit}",
                size_hint_y=None,
                height=dp(30),
                font_size=sp(18),
                bold=True,
                color=(1, 1, 1, 1)
            )
            card.add_widget(title_label)
            card.add_widget(value_label)
            return card
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت کارت آماری: {e}", error_details)
            return RTLLabel(
                text=f"{title}: {value}",
                color=(1, 1, 1, 1)
            )
    
    def _update_card_bg(self, instance, value):
        if hasattr(instance, 'bg_rect'):
            instance.bg_rect.pos = instance.pos
            instance.bg_rect.size = instance.size
    
    def export_excel(self, instance):
        try:
            filepath = export_to_excel()
            if filepath:
                self.show_message('موفق', 'فایل Excel ذخیره شد')
            else:
                self.show_message('خطا', 'هیچ داده‌ای وجود ندارد')
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در خروجی Excel: {e}", error_details)
    
    def export_pdf(self, instance):
        self.show_message('توجه', 'قابلیت خروجی PDF در این نسخه موقتاً غیرفعال است')
    
    def go_back(self, instance):
        self.manager.current = 'user'
    
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