"""
ویجت‌های RTL برای پشتیبانی از متن فارسی
"""

from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.dropdown import DropDown
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.metrics import dp, sp
from kivy.graphics import Color, RoundedRectangle
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout

try:
    from utils.persian_text import PersianLabel
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


class RTLTextInput(BoxLayout):
    """فیلد ورودی با پشتیبانی از RTL"""
    
    def __init__(self, **kwargs):
        kwargs.pop('font_name', None)
        
        self._hint_text = kwargs.pop('hint_text', '')
        self._password = kwargs.pop('password', False)
        self._multiline = kwargs.pop('multiline', False)
        self._text = kwargs.pop('text', '')
        self._font_size = kwargs.pop('font_size', sp(36))
        self._input_filter = kwargs.pop('input_filter', None)
        
        # ✅ تغییر height به 60 (حدود 2.2 سانت)
        height = kwargs.pop('height', dp(70))
        
        super().__init__(**kwargs)
        
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = height
        self.padding = dp(5)  # ✅ افزایش padding برای جا دادن متن
        
        self.bg_color = (1, 1, 1, 1)
        self.border_color = (0.7, 0.7, 0.7, 1)
        self.border_color_focus = (0.2, 0.5, 0.8, 1)
        
        with self.canvas.before:
            Color(*self.bg_color)
            self.bg_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(6)]
            )
            Color(*self.border_color)
            self.border_rect = RoundedRectangle(
                pos=(self.x + 2, self.y + 2),
                size=(self.width - 4, self.height - 4),
                radius=[dp(6)]
            )
        
        self.bind(pos=self._update_rect, size=self._update_rect)
        
        self._hidden_input = TextInput(
            text=self._text,
            password=self._password,
            multiline=self._multiline,
            font_size=self._font_size,
            size_hint=(1, 1),
            opacity=0,
            disabled=False,
            input_filter=self._input_filter,
            background_color=(0, 0, 0, 0),
            foreground_color=(0, 0, 0, 1),
            cursor_color=(0.2, 0.5, 0.8, 1),
            halign='right',
            font_name='PersianFont',
            padding=[dp(10), dp(8), dp(10), dp(8)]  # ✅ افزایش padding داخلی
        )
        self._hidden_input.bind(text=self._on_text_change)
        self._hidden_input.bind(focus=self._on_focus)
        
        display_text = self._text if self._text else self._hint_text
        is_hint = not self._text
        color = (0.5, 0.5, 0.5, 1) if is_hint else (0, 0, 0, 1)
        color_rgb = tuple(int(c * 255) for c in color)
        
        self.label = PersianLabel(
            text=display_text,
            font_size=self._font_size,
            color=color_rgb,
            size_hint=(1, 1),
            halign='right',
            valign='middle'  # ✅ وسط‌چین برای نمایش بهتر
        )
        
        self.add_widget(self.label)
        self.add_widget(self._hidden_input)
   
    def _update_rect(self, instance, value):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.border_rect.pos = (self.x + 1, self.y + 1)
        self.border_rect.size = (self.width - 2, self.height - 2)
    
    def _on_focus(self, instance, value):
        self.canvas.before.clear()
        Color(*self.bg_color)
        self.bg_rect = RoundedRectangle(
            pos=self.pos,
            size=self.size,
            radius=[dp(6)]
        )
        Color(*self.border_color_focus if value else self.border_color)
        self.border_rect = RoundedRectangle(
            pos=(self.x + 1, self.y + 1),
            size=(self.width - 2, self.height - 2),
            radius=[dp(5)]
        )
        self.canvas.before.add(self.bg_rect)
        self.canvas.before.add(self.border_rect)
    
    def _on_text_change(self, instance, value):
        self._text = value
        if value:
            color = (0, 0, 0, 1)
            color_rgb = tuple(int(c * 255) for c in color)
            self.label.set_text(value)
            self.label.color = color_rgb
            self.label._update_texture()
        else:
            color = (0.5, 0.5, 0.5, 1)
            color_rgb = tuple(int(c * 255) for c in color)
            self.label.set_text(self._hint_text)
            self.label.color = color_rgb
            self.label._update_texture()
    
    @property
    def text(self):
        return self._hidden_input.text
    
    @text.setter
    def text(self, value):
        self._hidden_input.text = value
        self._on_text_change(self._hidden_input, value)


class RTLDropdown(DropDown):
    """Dropdown سفارشی با PersianLabel"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_name = 'PersianFont'
        self.auto_width = False
        self.width = dp(250)
        self.size_hint_x = None
        self.max_height = dp(300)
        self.background_color = (1, 1, 1, 1)
    
    def add_widget(self, widget, index=0):
        if isinstance(widget, str):
            label = PersianLabel(
                text=widget,
                font_size=sp(16),
                color=(0, 0, 0, 255),
                size_hint_y=None,
                height=dp(45),
                halign='right'
            )
            widget = label
        
        super().add_widget(widget, index)


class RTLSpinner(Spinner):
    """Spinner با Dropdown سفارشی"""
    
    def __init__(self, **kwargs):
        self._values = kwargs.pop('values', [])
        self._text = kwargs.pop('text', '')
        
        kwargs['font_name'] = 'PersianFont'
        kwargs['halign'] = 'right'
        kwargs['size_hint_y'] = None
        kwargs['height'] = kwargs.get('height', dp(45))
        kwargs['font_size'] = kwargs.get('font_size', sp(18))
        kwargs['background_color'] = (1, 1, 1, 1)
        kwargs['color'] = (0, 0, 0, 1)
        
        super().__init__(**kwargs)
        
        self._dropdown = RTLDropdown()
        self._dropdown.bind(on_select=self._on_select)
        self._update_dropdown()
    
    def _update_dropdown(self):
        self._dropdown.clear_widgets()
        
        for value in self._values:
            label = PersianLabel(
                text=value,
                font_size=sp(18),
                color=(0, 0, 0, 255),
                size_hint_y=None,
                height=dp(45),
                halign='right'
            )
            
            btn = Button(
                size_hint_y=None,
                height=dp(45),
                background_normal='',
                background_color=(0.95, 0.95, 0.95, 1)
            )
            
            btn.add_widget(label)
            btn.bind(on_release=lambda b, val=value: self._dropdown.select(val))
            
            self._dropdown.add_widget(btn)
    
    def _on_select(self, instance, value):
        self.text = value
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._update_dropdown()
            self._dropdown.open(self)
            return True
        return super().on_touch_down(touch)
    
    @property
    def values(self):
        return self._values
    
    @values.setter
    def values(self, value):
        self._values = value
        self._update_dropdown()


# ============================================================
# ✅ PersianComboBox - با پشتیبانی از bind
# ============================================================

import arabic_reshaper
from bidi.algorithm import get_display
from kivy.clock import Clock

def fix_persian_text(text):
    """تبدیل متن فارسی به فرم درست برای نمایش در Kivy"""
    if not text:
        return text
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


class PersianComboBox(BoxLayout):
    """کمبوباکس فارسی - نسخه نهایی با arabic_reshaper و پشتیبانی از bind"""
    
    def __init__(self, **kwargs):
        self._values = kwargs.pop('values', [])
        self._text = kwargs.pop('text', self._values[0] if self._values else '')
        self._height = kwargs.pop('height', dp(45))
        
        super().__init__(**kwargs)
        
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = self._height
        self.spacing = dp(2)
        self.padding = [dp(2), dp(2), dp(2), dp(2)]
        
        # ✅ دکمه اصلی
        self.main_btn = Button(
            text=fix_persian_text(self._text),
            font_name='PersianFont',
            font_size=sp(18),
            halign='right',
            valign='middle',
            size_hint=(1, 1),
            background_normal='',
            background_color=(1, 1, 1, 1),
            color=(0, 0, 0, 1),
            text_size=(dp(200), None)
        )
        self.main_btn.bind(on_release=self._open_popup)
        
        # کادر
        with self.main_btn.canvas.before:
            Color(1, 1, 1, 1)
            self.bg = RoundedRectangle(
                pos=self.main_btn.pos,
                size=self.main_btn.size,
                radius=[dp(5)]
            )
            Color(0.3, 0.3, 0.3, 1)
            self.border = RoundedRectangle(
                pos=(self.main_btn.x + 2, self.main_btn.y + 2),
                size=(self.main_btn.width - 4, self.main_btn.height - 4),
                radius=[dp(4)]
            )
        
        self.main_btn.bind(pos=self._update_rect, size=self._update_rect)
        
        # فلش
        self.arrow = Label(
            text='▼',
            font_size=sp(20),
            color=(0.3, 0.3, 0.3, 1),
            size_hint_x=0.1,
            halign='center',
            valign='middle'
        )
        
        self.add_widget(self.main_btn)
        self.add_widget(self.arrow)
        
        # observerها
        self._text_observers = []
        self._last_text = self._text
        Clock.schedule_interval(self._check_text_change, 0.1)
        
        # ✅ ایجاد dropdown
        self._dropdown = None
        Clock.schedule_once(self._init_dropdown, 0.1)
    
    def _init_dropdown(self, dt):
        """ایجاد dropdown"""
        from kivy.uix.dropdown import DropDown
        self._dropdown = DropDown()
        self._dropdown.background_color = (1, 1, 1, 1)
        self._dropdown.background_normal = ''
        self._dropdown.auto_width = False
        self._dropdown.width = dp(280)
        self._dropdown.size_hint_x = None
        self._dropdown.max_height = dp(350)
        self._rebuild_dropdown(0)
    
    def _rebuild_dropdown(self, dt):
        """بازسازی dropdown با مقادیر جدید"""
        if not hasattr(self, '_dropdown') or not self._dropdown:
            return
        
        self._dropdown.clear_widgets()
        
        for val in self._values:
            btn = Button(
                text=fix_persian_text(val),
                font_name='PersianFont',
                font_size=sp(18),
                halign='right',
                valign='middle',
                size_hint_y=None,
                height=dp(45),
                background_normal='',
                background_color=(0.92, 0.92, 0.92, 1),
                color=(0, 0, 0, 1),
                text_size=(dp(230), None)
            )
            
            def on_enter(b):
                b.background_color = (0.75, 0.75, 0.75, 1)
            
            def on_leave(b):
                b.background_color = (0.92, 0.92, 0.92, 1)
            
            btn.bind(on_enter=on_enter, on_leave=on_leave)
            btn.bind(on_release=lambda b, v=val: self._select_value(v, self._dropdown))
            
            self._dropdown.add_widget(btn)
    
    def _check_text_change(self, dt):
        """بررسی تغییرات text"""
        current = self.main_btn.text
        if current != self._last_text:
            self._last_text = current
            for callback in self._text_observers:
                try:
                    callback(self, current)
                except Exception as e:
                    print(f"⚠️ خطا در callback: {e}")
    
    def _update_rect(self, *args):
        self.bg.pos = self.main_btn.pos
        self.bg.size = self.main_btn.size
        self.border.pos = (self.main_btn.x + 2, self.main_btn.y + 2)
        self.border.size = (self.main_btn.width - 4, self.main_btn.height - 4)
    
    def _open_popup(self, instance):
        if not self._dropdown:
            return
        # ✅ بازسازی dropdown قبل از باز کردن
        self._rebuild_dropdown(0)
        self._dropdown.open(self)
    
    def _select_value(self, value, popup):
        self.main_btn.text = fix_persian_text(value)
        self._text = value
        popup.dismiss()
    
    def bind(self, **kwargs):
        if 'text' in kwargs:
            self._text_observers.append(kwargs['text'])
        return super().bind(**kwargs)
    
    def unbind(self, **kwargs):
        if 'text' in kwargs:
            callback = kwargs['text']
            if callback in self._text_observers:
                self._text_observers.remove(callback)
        return super().unbind(**kwargs)
    
    @property
    def text(self):
        return self._text
    
    @text.setter
    def text(self, value):
        self._text = value
        self.main_btn.text = fix_persian_text(value)
    
    @property
    def values(self):
        return self._values
    
    @values.setter
    def values(self, value):
        self._values = value
        # ✅ بازسازی dropdown
        if hasattr(self, '_dropdown') and self._dropdown:
            Clock.schedule_once(self._rebuild_dropdown, 0.1)


# ============================================================
# کلاس‌های کمکی (دست نخورده)
# ============================================================

class RTLLabel(PersianLabel):
    """RTLLabel - با تبدیل درست رنگ"""
    def __init__(self, **kwargs):
        kwargs.pop('bold', None)
        kwargs.pop('markup', None)
        kwargs.pop('halign', None)
        kwargs.pop('valign', None)
        kwargs.pop('text_size', None)
        kwargs.pop('font_name', None)
        kwargs.pop('size_hint_x', None)
        kwargs.pop('size_hint_y', None)
        
        text = kwargs.pop('text', '')
        font_size = kwargs.pop('font_size', 24)
        color = kwargs.pop('color', (0, 0, 0, 1))
        
        if isinstance(color, (tuple, list)):
            color = tuple(int(c * 255) if c <= 1 else int(c) for c in color)
        else:
            color = (0, 0, 0, 255)
        
        super().__init__(text=text, font_size=font_size, color=color, **kwargs)


class PersianButton(Button):
    """دکمه با پشتیبانی از متن فارسی"""
    def __init__(self, **kwargs):
        text = kwargs.pop('text', '')
        font_size = kwargs.pop('font_size', sp(20))
        
        kwargs.pop('font_name', None)
        kwargs.pop('halign', None)
        kwargs.pop('valign', None)
        kwargs.pop('markup', None)
        kwargs.pop('text_size', None)
        kwargs.pop('bold', None)
        
        super().__init__(**kwargs)
        
        self.label = PersianLabel(
            text=text,
            font_size=font_size,
            color=(255, 255, 255, 255),
            size_hint=(1, 1),
            halign='center',
            valign='middle'

        )
        self.add_widget(self.label)
        self.bind(size=self._update_label, pos=self._update_label)
        self._update_label()
    
    def _update_label(self, *args):
        self.label.size = self.size
        self.label.pos = self.pos
    
    def set_text(self, text):
        self.label.set_text(text)