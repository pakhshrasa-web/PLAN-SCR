# screens/debug_screen.py
# ========== صفحه دیباگ ==========

import os
import traceback
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivy.core.text import LabelBase
from kivy.graphics import Color, Rectangle

from utils.rtl_widgets import PersianButton, RTLLabel
from error_handler import ErrorPopup


class DebugScreen(Screen):
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
            ErrorPopup.show_error(f"خطا در ساخت DebugScreen: {e}", error_details)
            raise
    
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def build_ui(self):
        try:
            layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(8))
            
            # عنوان
            layout.add_widget(RTLLabel(
                text='بررسی فونت‌ها',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(22),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))
            
            layout.add_widget(RTLLabel(
                text='مسیرهای فونت سیستمی:',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))
            
            font_paths = [
                '/system/fonts/NotoNaskhArabic-Regular.ttf',
                '/system/fonts/NotoSansArabic-Regular.ttf',
                '/system/fonts/DroidSansFallback.ttf',
            ]
            
            for path in font_paths:
                exists = os.path.exists(path)
                status = 'موجود' if exists else 'وجود ندارد'
                color = (0.2, 0.7, 0.2, 1) if exists else (0.8, 0.2, 0.2, 1)
                layout.add_widget(RTLLabel(
                    text=f"{os.path.basename(path)}: {status}",
                    size_hint_y=None,
                    height=dp(25),
                    font_size=sp(14),
                    color=color
                ))
            
            layout.add_widget(RTLLabel(
                text='مسیرهای فونت داخلی:',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))
            
            internal_paths = [
                os.path.join(os.path.dirname(__file__), '..', 'fonts', 'Vazirmatn-Regular.ttf'),
                os.path.join(os.path.dirname(__file__), '..', 'Vazirmatn-Regular.ttf'),
            ]
            
            for path in internal_paths:
                exists = os.path.exists(path)
                status = 'موجود' if exists else 'وجود ندارد'
                color = (0.2, 0.7, 0.2, 1) if exists else (0.8, 0.2, 0.2, 1)
                layout.add_widget(RTLLabel(
                    text=f"{os.path.basename(path) if exists else path}: {status}",
                    size_hint_y=None,
                    height=dp(25),
                    font_size=sp(14),
                    color=color
                ))
            
            layout.add_widget(RTLLabel(
                text='فونت‌های ثبت شده:',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))
            
            font_names = list(LabelBase._fonts.keys())
            if font_names:
                for name in font_names:
                    layout.add_widget(RTLLabel(
                        text=f"- {name}",
                        size_hint_y=None,
                        height=dp(25),
                        font_size=sp(14),
                        color=(0.8, 0.8, 0.8, 1)
                    ))
            else:
                layout.add_widget(RTLLabel(
                    text='هیچ فونتی ثبت نشده است',
                    size_hint_y=None,
                    height=dp(25),
                    font_size=sp(14),
                    color=(0.5, 0.5, 0.5, 1)
                ))
            
            layout.add_widget(RTLLabel(
                text='نمایش متن با فونت‌های مختلف:',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))
            
            layout.add_widget(RTLLabel(
                text='تست فارسی با Roboto (فونت پیش‌فرض)',
                font_name='Roboto',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))
            
            layout.add_widget(RTLLabel(
                text='تست فارسی با PersianFont (فونت اختصاصی)',
                font_name='PersianFont',
                size_hint_y=None,
                height=dp(30),
                font_size=sp(16),
                color=(0.4, 0.7, 1, 1)
            ))
            
            # فضای خالی
            layout.add_widget(RTLLabel(
                text='',
                size_hint_y=None,
                height=dp(10)
            ))
            
            back_btn = PersianButton(
                text='بازگشت',
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                background_color=(0.3, 0.3, 0.3, 1),
                font_size=sp(18)
            )
            back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'login'))
            layout.add_widget(back_btn)
            
            self.add_widget(layout)
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت UI DebugScreen: {e}", error_details)
            raise