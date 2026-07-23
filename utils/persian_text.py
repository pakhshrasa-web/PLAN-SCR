"""
تبدیل متن فارسی به تصویر با استفاده از Pillow
با پشتیبانی کامل از RTL (با bidi + reshape)
"""

from kivy.graphics.texture import Texture
from kivy.uix.image import Image
from PIL import Image as PILImage, ImageDraw, ImageFont
import os

# ========== کتابخانه‌های RTL ==========
try:
    import arabic_reshaper
    HAS_RESHAPER = True
    print("arabic_reshaper بارگذاری شد")
except ImportError:
    HAS_RESHAPER = False
    print("arabic_reshaper در دسترس نیست")

try:
    from bidi.algorithm import get_display
    HAS_BIDI = True
    print("python-bidi بارگذاری شد")
except ImportError:
    HAS_BIDI = False
    print("python-bidi در دسترس نیست")


# ============================================================
# تابع تبدیل عدد به حروف - خارج از کلاس
# ============================================================

def number_to_words(n):
    """تبدیل عدد به حروف فارسی"""
    if n is None:
        return ""
    
    try:
        n = int(n)
    except:
        return ""
    
    if n == 0:
        return "صفر ریال"
    
    ones = ['', 'یک', 'دو', 'سه', 'چهار', 'پنج', 'شش', 'هفت', 'هشت', 'نه']
    tens = ['', 'ده', 'بیست', 'سی', 'چهل', 'پنجاه', 'شصت', 'هفتاد', 'هشتاد', 'نود']
    hundreds = ['', 'یکصد', 'دویست', 'سیصد', 'چهارصد', 'پانصد', 'ششصد', 'هفتصد', 'هشتصد', 'نهصد']
    groups = ['', 'هزار', 'میلیون', 'میلیارد']
    
    def convert_three_digits(num):
        if num == 0:
            return ''
        h = num // 100
        t = (num % 100) // 10
        o = num % 10
        result = []
        if h > 0:
            result.append(hundreds[h])
        if t == 1:
            if o == 0:
                result.append('ده')
            elif o == 1:
                result.append('یازده')
            elif o == 2:
                result.append('دوازده')
            elif o == 3:
                result.append('سیزده')
            elif o == 4:
                result.append('چهارده')
            elif o == 5:
                result.append('پانزده')
            elif o == 6:
                result.append('شانزده')
            elif o == 7:
                result.append('هفده')
            elif o == 8:
                result.append('هجده')
            elif o == 9:
                result.append('نوزده')
        else:
            if t > 0:
                result.append(tens[t])
            if o > 0:
                result.append(ones[o])
        return ' و '.join(result)
    
    num_str = str(n)
    group_list = []
    for i in range(len(num_str), 0, -3):
        start = max(0, i - 3)
        group = int(num_str[start:i])
        group_list.insert(0, group)
    
    result_parts = []
    for i, group in enumerate(group_list):
        if group == 0:
            continue
        group_words = convert_three_digits(group)
        if group_words:
            group_name = groups[len(group_list) - 1 - i]
            if group_name:
                result_parts.append(f"{group_words} {group_name}")
            else:
                result_parts.append(group_words)
    
    return " و ".join(result_parts) + " ریال"


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
        
        # تبدیل رنگ به int
        if isinstance(color, (tuple, list)):
            self._color = tuple(int(c) for c in color)
        else:
            self._color = (255, 255, 255, 255)
        
        self._font_path = self._find_font()
        print(f"فونت انتخاب شده برای PersianLabel: {self._font_path}")
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
                    print(f"reshape شد: '{self._text}' -> '{reshaped}'")
                    
                    if HAS_BIDI:
                        display_text = get_display(reshaped)
                        print(f"bidi اعمال شد: '{reshaped}' -> '{display_text}'")
                    else:
                        display_text = reshaped
                        print("bidi در دسترس نیست")
                        
                except Exception as e:
                    print(f"خطا در reshape/bidi: {e}")
                    display_text = self._text
            else:
                display_text = self._text
            
            # ========== 2. بارگذاری فونت ==========
            font = None
            
            # ============================================================
            # اصلاح: چک کردن اینکه _font_path None نباشه
            # ============================================================
            if self._font_path and os.path.exists(self._font_path):
                try:
                    font = ImageFont.truetype(self._font_path, self._font_size)
                    print(f"فونت بارگذاری شد: {self._font_path}")
                except Exception as e:
                    print(f"خطا در بارگذاری فونت: {e}")
            
            # ============================================================
            # اگر فونت پیدا نشد، از فونت پیش‌فرض استفاده کن
            # ============================================================
            if font is None:
                # سعی کن از فونت سیستمی استفاده کنی
                system_fonts = [
                    '/system/fonts/NotoNaskhArabic-Regular.ttf',
                    '/system/fonts/NotoSansArabic-Regular.ttf',
                    '/system/fonts/DroidNaskh-Regular.ttf',
                    '/system/fonts/DroidSansFallback.ttf',
                    'C:/Windows/Fonts/arial.ttf',
                    'C:/Windows/Fonts/tahoma.ttf',
                    '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
                ]
                for sys_font in system_fonts:
                    if os.path.exists(sys_font):
                        try:
                            font = ImageFont.truetype(sys_font, self._font_size)
                            print(f"فونت سیستمی بارگذاری شد: {sys_font}")
                            break
                        except:
                            continue
                
                # اگر هیچ فونتی پیدا نشد، از فونت پیش‌فرض Pillow استفاده کن
                if font is None:
                    font = ImageFont.load_default()
                    print("استفاده از فونت پیش‌فرض Pillow")
            
            # ========== 3. اندازه‌گیری دقیق متن ==========
            try:
                bbox = font.getbbox(display_text)
                if bbox:
                    left, top, right, bottom = bbox
                    text_width = right - left
                    text_height = bottom - top
                    print(f"getbbox: {text_width}x{text_height}")
                else:
                    raise Exception("getbbox failed")
            except:
                temp_img = PILImage.new('RGBA', (1, 1), (255, 255, 255, 0))
                temp_draw = ImageDraw.Draw(temp_img)
                bbox = temp_draw.textbbox((0, 0), display_text, font=font)
                left, top, right, bottom = bbox
                text_width = right - left
                text_height = bottom - top
                print(f"textbbox: {text_width}x{text_height}")
            
            # ========== 4. ایجاد تصویر با اندازه مناسب ==========
            padding = 20
            width = max(text_width + (padding * 2), 50)
            height = max(text_height + (padding * 2), 30)
            
            print(f"اندازه نهایی: {width}x{height}")
            
            img = PILImage.new('RGBA', (width, height), (255, 255, 255, 0))
            draw = ImageDraw.Draw(img)
            
            # ========== 5. رسم متن در موقعیت درست ==========
            offset_x = padding - min(left, 0)
            offset_y = padding - min(top, 0)
            
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
            
            print(f"Texture ساخته شد: {self.size}")
            
        except Exception as e:
            print(f"خطا در ایجاد متن: {e}")
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
        ]
        
        for path in font_list:
            if os.path.exists(path):
                print(f"فونت پیدا شد: {path}")
                return path
        
        print("هیچ فونت فارسی پیدا نشد!")
        return None
    
    def set_text(self, text):
        self._text = text
        self._update_texture()