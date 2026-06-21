"""
ویجت‌های RTL برای پشتیبانی از متن فارسی
"""

from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.label import Label
import os

# بررسی وجود فونت
def is_font_available(font_name):
    """بررسی وجود فونت در سیستم"""
    try:
        from kivy.core.text import LabelBase
        # بررسی اینکه فونت ثبت شده یا نه
        if font_name in LabelBase._fonts:
            return True
    except:
        pass
    return False

# نام فونت با fallback
FONT_NAME = 'Vazirmatn' if is_font_available('Vazirmatn') else 'Arial'


class RTLTextInput(TextInput):
    """
    TextInput با پشتیبانی از RTL و فونت فارسی
    """
    def __init__(self, **kwargs):
        # تنظیمات پیش‌فرض
        kwargs.setdefault('font_name', FONT_NAME)
        kwargs.setdefault('halign', 'right')
        kwargs.setdefault('padding', (10, 10, 10, 10))
        kwargs.setdefault('write_tab', False)
        
        super().__init__(**kwargs)
        
        # تنظیمات اضافی برای بهبود RTL
        self.bind(text=self._on_text_change)
    
    def _on_text_change(self, instance, value):
        """هنگام تغییر متن، اطمینان از RTL"""
        if value and value.strip():
            # اگر متن فارسی بود، راست‌چین کن
            if any('\u0600' <= c <= '\u06FF' for c in value):
                self.halign = 'right'
            else:
                self.halign = 'left'
    
    def insert_text(self, substring, from_undo=False):
        """درج متن با پشتیبانی از RTL"""
        # اگر کاراکتر فارسی است، در انتها اضافه کن
        if substring and any('\u0600' <= c <= '\u06FF' for c in substring):
            # اگر متن خالی است یا آخرین کاراکتر فارسی است
            if not self.text or self.cursor[0] == len(self.text):
                self.halign = 'right'
            else:
                self.halign = 'left'
        
        return super().insert_text(substring, from_undo=from_undo)


class RTLSpinner(Spinner):
    """
    Spinner با پشتیبانی از RTL و فونت فارسی
    """
    def __init__(self, **kwargs):
        kwargs.setdefault('font_name', FONT_NAME)
        kwargs.setdefault('halign', 'right')
        kwargs.setdefault('text_autoupdate', True)
        
        super().__init__(**kwargs)
        
        # اطمینان از نمایش صحیح متن در Spinner
        self.bind(text=self._on_text_change)
        
        # تنظیم dropdown برای RTL بعد از ساخت
        self.bind(on_press=self._setup_dropdown_rtl)
    
    def _on_text_change(self, instance, value):
        """هنگام تغییر متن، RTL را اعمال کن"""
        if value and any('\u0600' <= c <= '\u06FF' for c in value):
            self.halign = 'right'
        else:
            self.halign = 'left'
    
    def _setup_dropdown_rtl(self, instance):
        """تنظیم جهت dropdown برای RTL"""
        if hasattr(self, '_dropdown') and self._dropdown:
            try:
                if hasattr(self._dropdown, 'container'):
                    self._dropdown.container.halign = 'right'
            except:
                pass


class RTLLabel(Label):
    """
    Label با پشتیبانی از RTL و فونت فارسی
    """
    def __init__(self, **kwargs):
        kwargs.setdefault('font_name', FONT_NAME)
        kwargs.setdefault('halign', 'right')
        kwargs.setdefault('valign', 'middle')
        
        super().__init__(**kwargs)
        self.bind(text=self._on_text_change)
    
    def _on_text_change(self, instance, value):
        """هنگام تغییر متن، RTL را اعمال کن"""
        if value and any('\u0600' <= c <= '\u06FF' for c in value):
            self.halign = 'right'
        else:
            self.halign = 'left'


def is_rtl_text(text):
    """بررسی RTL بودن متن"""
    if not text:
        return False
    
    text = str(text)
    rtl_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    ltr_chars = sum(1 for c in text if c.isalpha() and not ('\u0600' <= c <= '\u06FF'))
    
    if rtl_chars == 0 and ltr_chars == 0:
        return False
    
    return rtl_chars > ltr_chars


def auto_align_textinput(textinput):
    """تنظیم خودکار alignment بر اساس متن"""
    if textinput.text and is_rtl_text(textinput.text):
        textinput.halign = 'right'
        textinput.padding = (10, 10, 10, 10)
    else:
        textinput.halign = 'left'
        textinput.padding = (10, 10, 10, 10)