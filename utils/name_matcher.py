# utils/name_matcher.py
# ============================================================
# تطابق هوشمند نام‌ها برای فراخوانی ماموریت‌ها
# ============================================================

import re


def normalize_persian_text(text):
    """
    نرمال‌سازی متن فارسی برای تطابق بهتر
    
    تبدیل‌ها:
    - ي عربی → ی فارسی
    - ك عربی → ک فارسی
    - ۀ → ه
    - حذف فاصله‌های اضافی
    - حذف کدهای عددی قبل از نام
    
    Args:
        text: متنی که باید نرمال‌سازی شود
        
    Returns:
        str: متن نرمال‌سازی شده
    """
    if not text:
        return ""
    
    text = str(text).strip()
    
    # جایگزینی حروف عربی با فارسی
    replacements = {
        'ي': 'ی',  # ی عربی → ی فارسی
        'ك': 'ک',  # ک عربی → ک فارسی
        'ة': 'ه',
        'ۀ': 'ه',
        'إ': 'ا',
        'أ': 'ا',
        'آ': 'ا',
        'ؤ': 'و',
        'ئ': 'ی',
        'ٱ': 'ا',
        'ۂ': 'ه',
        '﷼': 'ریال',
    }
    
    for arabic, persian in replacements.items():
        text = text.replace(arabic, persian)
    
    # حذف کدهای عددی قبل از نام (مثل "0004 - ")
    text = re.sub(r'^\d+\s*[-–—]\s*', '', text)
    # حذف اعداد در ابتدا (مثل "0004")
    text = re.sub(r'^\d+\s+', '', text)
    
    # حذف فاصله‌های اضافی
    text = ' '.join(text.split())
    
    return text


def is_name_match(name1, name2):
    """
    بررسی تطابق دو نام با نرمال‌سازی
    
    Args:
        name1: نام اول
        name2: نام دوم
        
    Returns:
        bool: True اگر نام‌ها مطابقت داشته باشند
    """
    if not name1 or not name2:
        return False
    
    # نرمال‌سازی هر دو نام
    norm1 = normalize_persian_text(name1)
    norm2 = normalize_persian_text(name2)
    
    # تطابق کامل
    if norm1 == norm2:
        return True
    
    # تطابق جزئی (یکی شامل دیگری باشد)
    if norm1 in norm2 or norm2 in norm1:
        return True
    
    # حذف کلمات رایج و مقایسه
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    # اگر بیش از 70% کلمات مشترک باشند
    if words1 and words2:
        common = words1.intersection(words2)
        ratio = len(common) / max(len(words1), len(words2))
        if ratio >= 0.7:
            return True
    
    return False


def extract_name_from_agent_string(agent_full):
    """
    استخراج نام از رشته عامل (با حذف کدها)
    
    مثال‌ها:
    - "0004 - قاسم جوکار" → "قاسم جوکار"
    - "0004-قاسم جوکار" → "قاسم جوکار"
    - "0004–قاسم جوکار" → "قاسم جوکار"
    - "قاسم جوکار" → "قاسم جوکار"
    
    Args:
        agent_full: رشته کامل عامل
        
    Returns:
        str: نام استخراج شده
    """
    if not agent_full:
        return ""
    
    agent_full = str(agent_full).strip()
    
    # حذف کدها با الگوهای مختلف
    if ' - ' in agent_full:
        return agent_full.split(' - ')[-1].strip()
    elif '-' in agent_full:
        return agent_full.split('-')[-1].strip()
    elif '–' in agent_full:
        return agent_full.split('–')[-1].strip()
    else:
        return agent_full


def normalize_agent_string(agent_full):
    """
    نرمال‌سازی کامل رشته عامل (استخراج نام + نرمال‌سازی)
    
    Args:
        agent_full: رشته کامل عامل
        
    Returns:
        str: نام نرمال‌سازی شده
    """
    name = extract_name_from_agent_string(agent_full)
    return normalize_persian_text(name)