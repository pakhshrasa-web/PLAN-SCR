# screens/attendance_screen.py
# ========== صفحه حضور و غیاب ==========

import traceback
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.scrollview import ScrollView

from utils.rtl_widgets import PersianButton, RTLLabel, PersianPopup, RTLTextInput, PersianComboBox
from utils.attendance_manager import AttendanceManager
from utils.jalali_date import get_today_jalali
from error_handler import ErrorPopup


class AttendanceScreen(Screen):
    """صفحه اصلی حضور و غیاب"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        with self.canvas.before:
            Color(0.08, 0.08, 0.08, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            self.bind(pos=self._update_bg, size=self._update_bg)
        
        self.current_user = None
        self.today = get_today_jalali()
        self.build_ui()
    
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def set_user(self, user):
        """تنظیم کاربر جاری"""
        self.current_user = user
        self.load_today_attendance()
    
    def build_ui(self):
        """ساخت رابط کاربری"""
        self.clear_widgets()
        
        layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(8))
        
        # عنوان
        title_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        title_layout.add_widget(RTLLabel(
            text=f'حضور و غیاب',
            font_size=sp(22),
            bold=True,
            color=(0.4, 0.8, 1, 1),
            size_hint_x=0.6
        ))
        
        title_layout.add_widget(RTLLabel(
            text=self.today,
            font_size=sp(16),
            color=(0.6, 0.6, 0.6, 1),
            size_hint_x=0.4,
            halign='left'
        ))
        
        layout.add_widget(title_layout)
        
        # اطلاعات کاربر
        if self.current_user:
            info_layout = BoxLayout(size_hint_y=None, height=dp(35), spacing=dp(10))
            info_layout.add_widget(RTLLabel(
                text=f'کاربر: {self.current_user.get("name", "")}',
                font_size=sp(16),
                color=(1, 1, 1, 1),
                size_hint_x=0.5
            ))
            info_layout.add_widget(RTLLabel(
                text=f'نقش: {self.current_user.get("role", "")}',
                font_size=sp(16),
                color=(0.6, 0.8, 1, 1),
                size_hint_x=0.5,
                halign='left'
            ))
            layout.add_widget(info_layout)
        
        layout.add_widget(BoxLayout(size_hint_y=None, height=dp(10)))
        
        # دکمه‌های عملیاتی
        action_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        
        self.check_in_btn = PersianButton(
            text='ثبت ورود',
            size_hint_x=0.25,
            background_color=(0.2, 0.6, 0.2, 1),
            color=(1, 1, 1, 1),
            font_size=sp(14),
            bold=True
        )
        self.check_in_btn.bind(on_press=lambda x: self.check_in())
        action_layout.add_widget(self.check_in_btn)
        
        self.check_out_btn = PersianButton(
            text='ثبت خروج',
            size_hint_x=0.25,
            background_color=(0.6, 0.4, 0.2, 1),
            color=(1, 1, 1, 1),
            font_size=sp(14),
            bold=True
        )
        self.check_out_btn.bind(on_press=lambda x: self.check_out())
        action_layout.add_widget(self.check_out_btn)
        
        leave_btn = PersianButton(
            text='مرخصی',
            size_hint_x=0.25,
            background_color=(0.4, 0.2, 0.6, 1),
            color=(1, 1, 1, 1),
            font_size=sp(14)
        )
        leave_btn.bind(on_press=lambda x: self.show_leave_dialog())
        action_layout.add_widget(leave_btn)
        
        mission_btn = PersianButton(
            text='ماموریت',
            size_hint_x=0.25,
            background_color=(0.2, 0.4, 0.6, 1),
            color=(1, 1, 1, 1),
            font_size=sp(14)
        )
        mission_btn.bind(on_press=lambda x: self.show_mission_dialog())
        action_layout.add_widget(mission_btn)
        
        layout.add_widget(action_layout)
        
        layout.add_widget(BoxLayout(size_hint_y=None, height=dp(10)))
        
        # لیست حضور و غیاب امروز
        list_label = RTLLabel(
            text='وضعیت امروز:',
            size_hint_y=None,
            height=dp(30),
            font_size=sp(14),
            bold=True,
            color=(0.6, 0.8, 1, 1)
        )
        layout.add_widget(list_label)
        
        # اسکرول ویو
        scroll = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True,
            size_hint_y=1
        )
        
        self.list_grid = BoxLayout(
            orientation='vertical',
            spacing=dp(4),
            size_hint_y=None,
            padding=dp(5)
        )
        self.list_grid.bind(minimum_height=self.list_grid.setter('height'))
        
        scroll.add_widget(self.list_grid)
        layout.add_widget(scroll)
        
        # دکمه بازگشت
        back_btn = PersianButton(
            text='بازگشت',
            size_hint_y=None,
            height=dp(42),
            background_color=(0.3, 0.3, 0.3, 1),
            color=(1, 1, 1, 1),
            font_size=sp(14)
        )
        back_btn.bind(on_press=self.go_back)
        layout.add_widget(back_btn)
        
        self.add_widget(layout)
    
    def load_today_attendance(self):
        """بارگذاری حضور و غیاب امروز"""
        self.list_grid.clear_widgets()
        
        if not self.current_user:
            return
        
        user_id = self.current_user.get('id')
        records = AttendanceManager.get_daily_report(user_id=user_id)
        
        if not records:
            self.list_grid.add_widget(RTLLabel(
                text='هیچ رکوردی برای امروز ثبت نشده است',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(14),
                color=(0.5, 0.5, 0.5, 1)
            ))
            return
        
        for record in records:
            row = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(5))
            with row.canvas.before:
                Color(0.15, 0.15, 0.2, 1)
                rect = Rectangle(pos=row.pos, size=row.size)
                row.bind(pos=lambda i, v: setattr(rect, 'pos', v),
                        size=lambda i, v: setattr(rect, 'size', v))
            
            status = record.get('status', '')
            check_in = record.get('check_in', '')
            check_out = record.get('check_out', '')
            
            status_colors = {
                'حضور': (0.2, 0.8, 0.2, 1),
                'غیبت': (0.8, 0.2, 0.2, 1),
                'مرخصی': (0.8, 0.6, 0.2, 1),
                'ماموریت': (0.2, 0.6, 0.8, 1),
                'تاخیر': (0.8, 0.4, 0.2, 1),
                'خروج زودتر': (0.6, 0.2, 0.4, 1)
            }
            status_color = status_colors.get(status, (0.5, 0.5, 0.5, 1))
            
            row.add_widget(RTLLabel(
                text=f'ورود: {check_in or "-"}',
                size_hint_x=0.3,
                font_size=sp(13),
                color=(1, 1, 1, 1)
            ))
            row.add_widget(RTLLabel(
                text=f'خروج: {check_out or "-"}',
                size_hint_x=0.3,
                font_size=sp(13),
                color=(1, 1, 1, 1)
            ))
            row.add_widget(RTLLabel(
                text=status,
                size_hint_x=0.4,
                font_size=sp(13),
                bold=True,
                color=status_color
            ))
            
            self.list_grid.add_widget(row)
    
    def check_in(self):
        """ثبت ورود"""
        if not self.current_user:
            ErrorPopup.show_error('کاربری انتخاب نشده است')
            return
        
        user_id = self.current_user.get('id')
        success, message = AttendanceManager.check_in(user_id)
        if success:
            self.show_message('موفق', message)
            self.load_today_attendance()
        else:
            ErrorPopup.show_error(message)
    
    def check_out(self):
        """ثبت خروج"""
        if not self.current_user:
            ErrorPopup.show_error('کاربری انتخاب نشده است')
            return
        
        user_id = self.current_user.get('id')
        success, message = AttendanceManager.check_out(user_id)
        if success:
            self.show_message('موفق', message)
            self.load_today_attendance()
        else:
            ErrorPopup.show_error(message)
    
    def show_leave_dialog(self):
        """نمایش دیالوگ ثبت مرخصی"""
        try:
            content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(8))
            with content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(rect, 'pos', v),
                           size=lambda i, v: setattr(rect, 'size', v))
            
            content.add_widget(RTLLabel(
                text='ثبت مرخصی',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(18),
                bold=True,
                color=(0.4, 0.8, 1, 1)
            ))
            
            # تاریخ
            date_layout = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(8))
            date_layout.add_widget(RTLLabel(
                text='تاریخ:',
                size_hint_x=0.15,
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            leave_date = RTLTextInput(
                text=get_today_jalali(),
                multiline=False,
                size_hint_x=0.85,
                size_hint_y=None,
                height=dp(38),
                font_size=sp(16)
            )
            leave_date.bg_color = (0.15, 0.15, 0.15, 1)
            leave_date.border_color = (0.3, 0.3, 0.3, 1)
            leave_date._hidden_input.foreground_color = (1, 1, 1, 1)
            date_layout.add_widget(leave_date)
            content.add_widget(date_layout)
            
            # نوع مرخصی
            config = AttendanceManager.load_config()
            leave_types = config.get('leave_types', ['ساعتی', 'استحقاقی', 'استعلاجی', 'اضطراری', 'بدون حقوق'])
            leave_type_combo = PersianComboBox(
                text=leave_types[0] if leave_types else 'ساعتی',
                values=leave_types,
                height=dp(40)
            )
            leave_type_combo.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            leave_type_combo.main_btn.color = (1, 1, 1, 1)
            leave_type_combo.main_btn.font_size = sp(16)
            content.add_widget(leave_type_combo)
            
            # مدت
            duration_layout = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(8))
            duration_layout.add_widget(RTLLabel(
                text='مدت:',
                size_hint_x=0.15,
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            leave_duration = RTLTextInput(
                text='',
                multiline=False,
                size_hint_x=0.85,
                size_hint_y=None,
                height=dp(38),
                font_size=sp(16),
                hint_text='مثال: 8 (ساعت) یا 1 (روز)'
            )
            leave_duration.bg_color = (0.15, 0.15, 0.15, 1)
            leave_duration.border_color = (0.3, 0.3, 0.3, 1)
            leave_duration._hidden_input.foreground_color = (1, 1, 1, 1)
            duration_layout.add_widget(leave_duration)
            content.add_widget(duration_layout)
            
            # توضیحات
            note_input = RTLTextInput(
                text='',
                multiline=True,
                size_hint_y=None,
                height=dp(60),
                font_size=sp(14),
                hint_text='توضیحات (اختیاری)'
            )
            note_input.bg_color = (0.15, 0.15, 0.15, 1)
            note_input.border_color = (0.3, 0.3, 0.3, 1)
            note_input._hidden_input.foreground_color = (1, 1, 1, 1)
            content.add_widget(note_input)
            
            # دکمه‌ها
            btn_layout = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(8))
            
            save_btn = PersianButton(
                text='ثبت',
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
            
            btn_layout.add_widget(save_btn)
            btn_layout.add_widget(cancel_btn)
            content.add_widget(btn_layout)
            
            popup = PersianPopup(
                title='ثبت مرخصی',
                content=content,
                size_hint=(0.9, 0.65),
                background_color=(0.08, 0.08, 0.08, 1)
            )
            
            def do_save(instance):
                user_id = self.current_user.get('id')
                date = leave_date.text.strip()
                if not date:
                    ErrorPopup.show_error('لطفاً تاریخ را وارد کنید')
                    return
                
                leave_type = leave_type_combo.text
                duration = leave_duration.text.strip()
                if not duration:
                    ErrorPopup.show_error('لطفاً مدت مرخصی را وارد کنید')
                    return
                
                try:
                    duration_float = float(duration)
                    if duration_float <= 0:
                        ErrorPopup.show_error('مدت مرخصی باید بیشتر از صفر باشد')
                        return
                except ValueError:
                    ErrorPopup.show_error('مدت مرخصی باید عدد باشد')
                    return
                
                note = note_input.text.strip()
                success, message = AttendanceManager.register_leave(
                    user_id, date, leave_type, duration_float, note
                )
                
                if success:
                    popup.dismiss()
                    self.show_message('موفق', message)
                    self.load_today_attendance()
                else:
                    ErrorPopup.show_error(message)
            
            def on_cancel(instance):
                popup.dismiss()
            
            save_btn.bind(on_press=do_save)
            cancel_btn.bind(on_press=on_cancel)
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    
    def show_mission_dialog(self):
        """نمایش دیالوگ ثبت ماموریت"""
        try:
            content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(8))
            with content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(rect, 'pos', v),
                           size=lambda i, v: setattr(rect, 'size', v))
            
            content.add_widget(RTLLabel(
                text='ثبت ماموریت',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(18),
                bold=True,
                color=(0.4, 0.8, 1, 1)
            ))
            
            # تاریخ
            date_layout = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(8))
            date_layout.add_widget(RTLLabel(
                text='تاریخ:',
                size_hint_x=0.15,
                font_size=sp(14),
                color=(1, 1, 1, 1)
            ))
            mission_date = RTLTextInput(
                text=get_today_jalali(),
                multiline=False,
                size_hint_x=0.85,
                size_hint_y=None,
                height=dp(38),
                font_size=sp(16)
            )
            mission_date.bg_color = (0.15, 0.15, 0.15, 1)
            mission_date.border_color = (0.3, 0.3, 0.3, 1)
            mission_date._hidden_input.foreground_color = (1, 1, 1, 1)
            date_layout.add_widget(mission_date)
            content.add_widget(date_layout)
            
            # توضیحات
            note_input = RTLTextInput(
                text='',
                multiline=True,
                size_hint_y=None,
                height=dp(80),
                font_size=sp(14),
                hint_text='توضیحات ماموریت (مقصد، دلیل، و...)'
            )
            note_input.bg_color = (0.15, 0.15, 0.15, 1)
            note_input.border_color = (0.3, 0.3, 0.3, 1)
            note_input._hidden_input.foreground_color = (1, 1, 1, 1)
            content.add_widget(note_input)
            
            # دکمه‌ها
            btn_layout = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(8))
            
            save_btn = PersianButton(
                text='ثبت',
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
            
            btn_layout.add_widget(save_btn)
            btn_layout.add_widget(cancel_btn)
            content.add_widget(btn_layout)
            
            popup = PersianPopup(
                title='ثبت ماموریت',
                content=content,
                size_hint=(0.9, 0.55),
                background_color=(0.08, 0.08, 0.08, 1)
            )
            
            def do_save(instance):
                user_id = self.current_user.get('id')
                date = mission_date.text.strip()
                if not date:
                    ErrorPopup.show_error('لطفاً تاریخ را وارد کنید')
                    return
                
                note = note_input.text.strip()
                if not note:
                    ErrorPopup.show_error('لطفاً توضیحات ماموریت را وارد کنید')
                    return
                
                success, message = AttendanceManager.register_mission(user_id, date, note)
                
                if success:
                    popup.dismiss()
                    self.show_message('موفق', message)
                    self.load_today_attendance()
                else:
                    ErrorPopup.show_error(message)
            
            def on_cancel(instance):
                popup.dismiss()
            
            save_btn.bind(on_press=do_save)
            cancel_btn.bind(on_press=on_cancel)
            popup.open()
            
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا: {e}", error_details)
    
    def show_message(self, title, message):
        """نمایش پیام"""
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            with content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(rect, 'pos', v),
                           size=lambda i, v: setattr(rect, 'size', v))
            
            content.add_widget(RTLLabel(
                text=message,
                size_hint_y=None,
                height=dp(60),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))
            
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
                size_hint=(0.8, 0.35),
                background_color=(0.08, 0.08, 0.08, 1)
            )
            btn.bind(on_press=popup.dismiss)
            popup.open()
            
        except Exception as e:
            print(f"خطا در نمایش پیام: {e}")
    
    def go_back(self, instance):
        """بازگشت به صفحه ورود"""
        self.manager.current = 'login'