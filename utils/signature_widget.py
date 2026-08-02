# utils/signature_widget.py
# ========== ویجت امضای دیجیتال ==========

import os
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp
from kivy.utils import platform


class SignatureWidget(Widget):
    """ویجت رسم امضا با پشتیبانی از تاچ و موس"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # تنظیمات پیش‌فرض
        self.line_width = dp(3)
        self.line_color = (0, 0, 0, 1)  # مشکی
        
        # مسیر ذخیره امضا
        self.signature_path = None
        self.has_signature = False
        
        # رسم پس‌زمینه
        with self.canvas.before:
            Color(0.95, 0.95, 0.95, 1)  # خاکستری روشن
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            
            # خط نقطه‌چین راهنما
            Color(0.7, 0.7, 0.7, 0.5)
            self.guide_line = Line(
                points=[self.x + dp(20), self.center_y, 
                       self.right - dp(20), self.center_y],
                width=1,
                dash_length=dp(5),
                dash_offset=dp(3)
            )
        
        self.bind(pos=self._update_graphics, size=self._update_graphics)
        
        # فعال‌سازی تاچ و موس
        self._touches = {}
    
    def _update_graphics(self, *args):
        """بروزرسانی موقعیت پس‌زمینه"""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        
        # بروزرسانی خط راهنما
        self.guide_line.points = [
            self.x + dp(20), self.center_y,
            self.right - dp(20), self.center_y
        ]
    
    def on_touch_down(self, touch):
        """شروع رسم با تاچ یا موس"""
        if self.collide_point(*touch.pos):
            # ایجاد خط جدید
            with self.canvas:
                Color(*self.line_color)
                touch.ud['line'] = Line(
                    points=[touch.x, touch.y],
                    width=self.line_width,
                    cap='round',
                    joint='round'
                )
            
            self._touches[touch.uid] = touch
            self.has_signature = True
            return True
        
        return super().on_touch_down(touch)
    
    def on_touch_move(self, touch):
        """ادامه رسم"""
        if touch.uid in self._touches:
            # اضافه کردن نقطه جدید به خط
            line = touch.ud.get('line')
            if line:
                line.points += [touch.x, touch.y]
            return True
        
        return super().on_touch_move(touch)
    
    def on_touch_up(self, touch):
        """پایان رسم"""
        if touch.uid in self._touches:
            del self._touches[touch.uid]
            return True
        
        return super().on_touch_up(touch)
    
    def clear_canvas(self):
        """پاک کردن تمام خطوط"""
        # حذف تمام خطوط (نه پس‌زمینه)
        self.canvas.clear()
        self._touches.clear()
        self.has_signature = False
    
    def get_signature_image(self):
        """خروجی تصویر PNG از امضا"""
        if not self.has_signature:
            return None
        
        # ذخیره به صورت تصویر
        temp_path = 'temp_signature.png'
        self.export_to_png(temp_path)
        return temp_path
    
    def save_signature(self, save_path):
        """ذخیره امضا در مسیر مشخص"""
        if not self.has_signature:
            return False
        
        try:
            # ایجاد پوشه اگر وجود ندارد
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # ذخیره تصویر
            self.export_to_png(save_path)
            self.signature_path = save_path
            return True
            
        except Exception as e:
            print(f"خطا در ذخیره امضا: {e}")
            return False
    
    def set_line_color(self, r, g, b, a=1):
        """تغییر رنگ قلم"""
        self.line_color = (r, g, b, a)
    
    def set_line_width(self, width):
        """تغییر ضخامت قلم"""
        self.line_width = dp(width)