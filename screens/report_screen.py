# screens/report_screen.py
# ========== صفحه گزارش‌ها ==========

import traceback
import os
import threading 
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock  

from utils.rtl_widgets import PersianButton, RTLLabel, PersianPopup
from utils.persian_text import PersianLabel  
from utils.file_manager import get_daily_logs, load_json, save_json, get_data_path
from utils.excel_exporter import export_to_excel
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
            layout = BoxLayout(orientation='vertical', padding=[dp(5), dp(5), dp(5), dp(5)])
            
            tabs_layout = BoxLayout(
                size_hint_y=None,
                height=dp(40),
                spacing=dp(2)
            )
            
            btn_performance = PersianButton(
                text=' عملکرد کلی',
                background_color=(0.3, 0.5, 0.8, 1),
                size_hint_y=None,
                height=dp(36),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            btn_performance.bind(on_press=lambda x: self.switch_tab(0))
            tabs_layout.add_widget(btn_performance)
            
            btn_detail = PersianButton(
                text=' ریز عملکرد',
                background_color=(0.3, 0.5, 0.8, 0.6),
                size_hint_y=None,
                height=dp(36),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            btn_detail.bind(on_press=lambda x: self.switch_tab(1))
            tabs_layout.add_widget(btn_detail)
            
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
        else:
            self.show_detail_tab()
    
    def show_performance_tab(self):
        try:
            summary_file = 'daily_summary.json'
            summary_path = os.path.join(get_data_path(), summary_file)
            
            if os.path.exists(summary_path):
                all_summaries = load_json(summary_file)
            else:
                all_summaries = {}
            
            layout = ScrollView()
            content = GridLayout(cols=1, spacing=dp(8), size_hint_y=None, padding=dp(8))
            content.bind(minimum_height=content.setter('height'))
            
            if not all_summaries:
                content.add_widget(RTLLabel(
                    text=' هیچ خلاصه عملکردی ثبت نشده است',
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
            
            row3 = BoxLayout(size_hint_y=None, height=dp(75), spacing=dp(6))
            row3.add_widget(self._make_card('کل مبلغ فروش', f"{total_sales:,}", (0.2, 0.6, 0.3, 1)))
            avg_sale = total_sales // total_visits if total_visits > 0 else 0
            row3.add_widget(self._make_card('میانگین هر ویزیت', f"{avg_sale:,}", (0.7, 0.4, 0.4, 1)))
            content.add_widget(row3)
            
            content.add_widget(RTLLabel(
                text='خلاصه روزانه',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(20),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))
            
            header_box = BoxLayout(size_hint_y=None, height=dp(37), spacing=dp(2))
            headers = ['تاریخ', 'ویزیت', 'فاکتور', 'واحد', 'فروش']
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
                
                content.add_widget(row)
            
            layout.add_widget(content)
            self.content_area.add_widget(layout)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش عملکرد کلی: {e}", error_details)
    
    def show_detail_tab(self):
        try:
            all_logs = get_daily_logs()
            
            layout = ScrollView()
            content = GridLayout(cols=1, spacing=dp(4), size_hint_y=None, padding=dp(8))
            content.bind(minimum_height=content.setter('height'))
            
            if not all_logs:
                content.add_widget(RTLLabel(
                    text=' هیچ ریز عملکردی ثبت نشده است',
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
                        'fail_sales_reason': log.get('fail_sales_reason', '')
                    })
            
            content.add_widget(RTLLabel(
                text=' ریز عملکرد (همه ویزیت‌ها)',
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
            headers = ['تاریخ', 'مسیر', 'مشتری', 'ویزیت', 'فروش', 'ساعت']
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
                
                content.add_widget(row)
            
            layout.add_widget(content)
            self.content_area.add_widget(layout)
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش ریز عملکرد: {e}", error_details)
    
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
        """خروجی اکسل با اجرا در ترد جداگانه"""
        try:
            # نمایش پیام در حال ساخت
            self.loading_popup = self.show_message('⏳ در حال ساخت', 'لطفاً صبر کنید...')
            
            def do_export():
                success, result = export_to_excel()
                
                def show_result(dt):
                    # بستن پیام اول
                    if hasattr(self, 'loading_popup') and self.loading_popup:
                        try:
                            self.loading_popup.dismiss()
                        except:
                            pass
                        self.loading_popup = None
                    
                    # نمایش نتیجه
                    if success:
                        self.show_message(
                            '✅ موفق', 
                            'فایل اکسل با موفقیت ساخته شد!\n\n'
                            '📁 فایل در پوشه Downloads ذخیره شد.'
                        )
                    else:
                        self.show_message('❌ خطا', f'خطا در ساخت اکسل:\n{result}')
                
                Clock.schedule_once(show_result, 1)
            
            thread = threading.Thread(target=do_export, daemon=True)
            thread.start()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در خروجی اکسل: {e}", error_details)
    
    def go_back(self, instance):
        self.manager.current = 'user'
    
    def show_message(self, title, message):
        """نمایش پیام - نسخه ساده و کوتاه"""
        try:
            # محدود کردن طول پیام
            if len(message) > 200:
                message = message[:200] + "..."
            
            # ساخت محتوای پاپ‌آپ
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            
            # پیام کوتاه و ساده
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
            
            # دکمه باشه
            btn = PersianButton(
                text='باشه',
                size_hint_y=None,
                height=dp(50),
                font_size=sp(20),
                color=(1, 1, 1, 1),
                background_color=(0.2, 0.6, 1, 1)
            )
            content.add_widget(btn)
            
            # پاپ‌آپ با عنوان فارسی
            popup = PersianPopup(
                title=title,
                content=content,
                size_hint=(0.8, 0.35),
                auto_dismiss=True
            )
            btn.bind(on_press=popup.dismiss)
            
            Clock.schedule_once(lambda dt: popup.open(), 0.1)
            
            # برگرداندن popup برای بستن خودکار
            return popup
            
        except Exception as e:
            print(f"❌ خطا در نمایش پیام: {e}")
            import traceback
            traceback.print_exc()
            return None