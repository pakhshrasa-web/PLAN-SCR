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
            layout = BoxLayout(orientation='vertical', padding=dp(20))
            
            font_paths = [
                '/system/fonts/NotoNaskhArabic-Regular.ttf',
                '/system/fonts/NotoSansArabic-Regular.ttf',
                '/system/fonts/DroidSansFallback.ttf',
            ]
            
            for path in font_paths:
                exists = os.path.exists(path)
                layout.add_widget(RTLLabel(
                    text=f"{path}: {'✅' if exists else '❌'}",
                    color=(1, 1, 1, 1)
                ))
            
            internal_paths = [
                os.path.join(os.path.dirname(__file__), '..', 'fonts', 'Vazirmatn-Regular.ttf'),
                os.path.join(os.path.dirname(__file__), '..', 'Vazirmatn-Regular.ttf'),
            ]
            
            for path in internal_paths:
                exists = os.path.exists(path)
                layout.add_widget(RTLLabel(
                    text=f"{path}: {'✅' if exists else '❌'}",
                    color=(1, 1, 1, 1)
                ))
            
            layout.add_widget(RTLLabel(
                text="📋 فونت‌های ثبت شده:",
                color=(1, 1, 1, 1)
            ))
            for name in LabelBase._fonts.keys():
                layout.add_widget(RTLLabel(
                    text=f"  - {name}",
                    color=(1, 1, 1, 1)
                ))
            
            layout.add_widget(RTLLabel(
                text="تست فارسی با Roboto",
                font_name='Roboto',
                color=(1, 1, 1, 1)
            ))
            layout.add_widget(RTLLabel(
                text="تست فارسی با PersianFont",
                font_name='PersianFont',
                color=(1, 1, 1, 1)
            ))
            
            back_btn = PersianButton(
                text='بازگشت',
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                background_color=(0.3, 0.3, 0.3, 1)
            )
            back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'login'))
            layout.add_widget(back_btn)
            
            self.add_widget(layout)
        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت UI DebugScreen: {e}", error_details)
            raise