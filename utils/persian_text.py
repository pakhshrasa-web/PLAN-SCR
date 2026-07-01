"""
تبدیل متن فارسی به تصویر با استفاده از Pillow
✅ با پشتیبانی کامل از RTL (با bidi + reshape)
"""

from kivy.graphics.texture import Texture
from kivy.uix.image import Image
from PIL import Image as PILImage, ImageDraw, ImageFont
import os

# ========== کتابخانه‌های RTL ==========
try:
    import arabic_reshaper
    HAS_RESHAPER = True
    print("✅ arabic_reshaper بارگذاری شد")
except ImportError:
    HAS_RESHAPER = False
    print("⚠️ arabic_reshaper در دسترس نیست")

try:
    from bidi.algorithm import get_display
    HAS_BIDI = True
    print("✅ python-bidi بارگذاری شد")
except ImportError:
    HAS_BIDI = False
    print("⚠️ python-bidi در دسترس نیست")


class PersianLabel(Image):
    def __init__(self, text="", font_size=24, color=(255, 255, 255, 255), **kwargs):
        # حذف پارامترهای غیرمجاز
        kwargs.pop('bold', None)
        kwargs.pop('markup', None)
        kwargs.pop('halign', None)
        kwargs.pop('valign', None)
        kwargs.pop('text_size', None)
        kwargs.pop('font_name', None)
        kwargs.pop('size_hint_x', None)
        kwargs.pop('size_hint_y', None)
        
        super().__init__(**kwargs)
        self._text = text
        self._font_size = font_size
        
        # ✅ تبدیل رنگ به int
        if isinstance(color, (tuple, list)):
            self._color = tuple(int(c) for c in color)
        else:
            self._color = (255, 255, 255, 255)
        
        self._font_path = self._find_font()
        print(f"🔍 فونت انتخاب شده برای PersianLabel: {self._font_path}")
        self._update_texture()
    
    def _update_texture(self):
        if not self._text:
            self.texture = None
            self.size = (0, 0)
            return
        
        try:
            # ========== 1. آماده‌سازی متن ==========
            display_text = self._text
            
            if HAS_RESHAPER and self._is_rtl(self._text):
                try:
                    reshaped = arabic_reshaper.reshape(self._text)
                    print(f"✅ reshape شد: '{self._text}' -> '{reshaped}'")
                    
                    if HAS_BIDI:
                        display_text = get_display(reshaped)
                        print(f"✅ bidi اعمال شد: '{reshaped}' -> '{display_text}'")
                    else:
                        display_text = reshaped
                        print("⚠️ bidi در دسترس نیست")
                        
                except Exception as e:
                    print(f"⚠️ خطا در reshape/bidi: {e}")
                    display_text = self._text
            else:
                display_text = self._text
            
            # ========== 2. بارگذاری فونت ==========
            font = None
            if self._font_path and os.path.exists(self._font_path):
                try:
                    font = ImageFont.truetype(self._font_path, self._font_size)
                    print(f"✅ فونت بارگذاری شد: {self._font_path}")
                except Exception as e:
                    print(f"⚠️ خطا در بارگذاری فونت: {e}")
            
            if font is None:
                font = ImageFont.load_default()
                print("⚠️ استفاده از فونت پیش‌فرض")
            
            # ========== 3. اندازه‌گیری دقیق متن ==========
            try:
                bbox = font.getbbox(display_text)
                if bbox:
                    left, top, right, bottom = bbox
                    text_width = right - left
                    text_height = bottom - top
                    print(f"📏 getbbox: {text_width}x{text_height}")
                else:
                    raise Exception("getbbox failed")
            except:
                temp_img = PILImage.new('RGBA', (1, 1), (255, 255, 255, 0))
                temp_draw = ImageDraw.Draw(temp_img)
                bbox = temp_draw.textbbox((0, 0), display_text, font=font)
                left, top, right, bottom = bbox
                text_width = right - left
                text_height = bottom - top
                print(f"📏 textbbox: {text_width}x{text_height}")
            
            # ========== 4. ایجاد تصویر با اندازه مناسب ==========
            padding = 20
            width = max(text_width + (padding * 2), 50)
            height = max(text_height + (padding * 2), 30)
            
            print(f"📐 اندازه نهایی: {width}x{height}")
            
            img = PILImage.new('RGBA', (width, height), (255, 255, 255, 0))
            draw = ImageDraw.Draw(img)
            
            # ========== 5. رسم متن در موقعیت درست ==========
            offset_x = padding - min(left, 0)
            offset_y = padding - min(top, 0)
            
            # ✅ اطمینان از int بودن رنگ
            if isinstance(self._color, (tuple, list)):
                color = tuple(int(c) for c in self._color)
            else:
                color = (255, 255, 255, 255)
            
            draw.text(
                (offset_x, offset_y),
                display_text,
                font=font,
                fill=color
            )
            
            # ========== 6. تبدیل به Texture ==========
            texture = Texture.create(
                size=img.size,
                colorfmt='rgba'
            )
            
            texture.blit_buffer(
                img.tobytes(),
                colorfmt='rgba',
                bufferfmt='ubyte'
            )
            
            texture.flip_vertical()
            
            self.texture = texture
            self.size = texture.size
            
            print(f"✅ Texture ساخته شد: {self.size}")
            
        except Exception as e:
            print(f"❌ خطا در ایجاد متن: {e}")
            import traceback
            traceback.print_exc()
            self.texture = None
    
    def _is_rtl(self, text):
        """تشخیص RTL بودن متن"""
        if not text:
            return False
        text = str(text)
        rtl_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF' or '\uFB50' <= c <= '\uFDFF')
        ltr_chars = sum(1 for c in text if c.isalpha() and not ('\u0600' <= c <= '\u06FF'))
        if rtl_chars == 0 and ltr_chars == 0:
            return False
        return rtl_chars > ltr_chars
    
    def _find_font(self):
        """پیدا کردن بهترین فونت موجود"""
        font_list = [
            'fonts/Amiri-Regular.ttf',
            'fonts/Lateef-Regular.ttf',
            'fonts/NotoNasrArabic-Regular.ttf',
            'fonts/Vazirmatn-Regular.ttf',
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fonts', 'Amiri-Regular.ttf'),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fonts', 'Lateef-Regular.ttf'),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fonts', 'NotoNasrArabic-Regular.ttf'),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fonts', 'Vazirmatn-Regular.ttf'),
            '/system/fonts/NotoNaskhArabic-Regular.ttf',
            '/system/fonts/NotoSansArabic-Regular.ttf',
            '/system/fonts/DroidNaskh-Regular.ttf',
            '/system/fonts/DroidSansFallback.ttf',
        ]
        
        for path in font_list:
            if os.path.exists(path):
                print(f"🔍 فونت پیدا شد: {path}")
                return path
        
        print("⚠️ هیچ فونت فارسی پیدا نشد!")
        return None
    
    def set_text(self, text):
        self._text = text
        self._update_texture()