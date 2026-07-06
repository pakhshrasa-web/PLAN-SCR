"""
خروجی اکسل - فقط ذخیره فایل در مسیر مشخص
"""

import os
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock

from utils.persian_text import PersianLabel
from utils.rtl_widgets import PersianButton


class ExportFilePicker(BoxLayout):
    """ویجت خروجی اکسل - فقط نمایش مسیر ذخیره"""
    
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=10, **kwargs)
        self.size_hint_y = None
        self.height = dp(80)
        
        from utils.storage import get_export_path
        export_path = get_export_path()
        
        self.file_label = PersianLabel(
            text=f'📁 مسیر خروجی:\n{export_path}',
            font_size=sp(14),
            color=(0.6, 0.8, 0.6, 255),
            size_hint_y=None,
            height=dp(60),
            halign='center'
        )
        self.add_widget(self.file_label)
    
    def get_export_path(self):
        from utils.storage import get_export_path
        return get_export_path()