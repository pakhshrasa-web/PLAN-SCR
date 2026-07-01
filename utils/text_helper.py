"""
کمک‌کننده برای نمایش صحیح متن فارسی
"""

import arabic_reshaper
from bidi.algorithm import get_display

# کش برای بهبود عملکرد
_reshape_cache = {}
_CACHE_MAX_SIZE = 200

def f(text):
    """
    تبدیل متن فارسی به شکل صحیح برای نمایش در Kivy
    
    Args:
        text: متن ورودی (می‌تواند str, int, float, None)
    
    Returns:
        str: متن اصلاح‌شده برای نمایش RTL
    """
    if not text:
        return text
    
    if not isinstance(text, str):
        text = str(text)
    
    if text in _reshape_cache:
        return _reshape_cache[text]
    
    try:
        result = get_display(arabic_reshaper.reshape(text))
        if len(_reshape_cache) < _CACHE_MAX_SIZE:
            _reshape_cache[text] = result
        return result
    except Exception:
        return text

def is_persian_text(text):
    """
    تشخیص فارسی بودن متن
    
    Args:
        text: متن ورودی
    
    Returns:
        bool: True اگر متن فارسی باشد
    """
    if not text:
        return False
    
    text = str(text)
    persian_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    total_chars = sum(1 for c in text if c.isalpha())
    
    if total_chars == 0:
        return False
    
    return persian_chars / total_chars > 0.3

def fix_english_numbers(text):
    """
    تبدیل اعداد انگلیسی به فارسی
    
    Args:
        text: متن ورودی
    
    Returns:
        str: متن با اعداد فارسی
    """
    if not text:
        return text
    
    text = str(text)
    
    english_to_persian = {
        '0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
        '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'
    }
    
    result = ''
    for char in text:
        result += english_to_persian.get(char, char)
    
    return result

def fix_persian_numbers(text):
    """
    تبدیل اعداد فارسی به انگلیسی
    """
    if not text:
        return text
    
    text = str(text)
    
    persian_to_english = {
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
    }
    
    result = ''
    for char in text:
        result += persian_to_english.get(char, char)
    
    return result

def clear_cache():
    """پاک کردن کش"""
    global _reshape_cache
    _reshape_cache = {}

def get_cache_size():
    """دریافت اندازه کش"""
    return len(_reshape_cache)

# Alias برای استفاده راحت‌تر
def _(text):
    """Alias برای تابع f"""
    return f(text)

# تابع fix_text برای سازگاری با pdf_exporter.py
def fix_text(text):
    """Alias برای تابع f"""
    return f(text)