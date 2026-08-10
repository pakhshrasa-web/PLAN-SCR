"""
مدیریت یادآوری‌ها و امتیازات کاربران
"""

import json
import os
from datetime import datetime
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.checkbox import CheckBox
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock

from utils.storage import get_data_path
from utils.jalali_date import get_today_jalali
from utils.score_calculator import calculate_all_scores


def get_greeting_by_time(username):
    """
    دریافت پیام خوش‌آمدگویی بر اساس ساعت گوشی کاربر
    """
    try:
        now = datetime.now()
        hour = now.hour
        minute = now.minute
        time_value = hour + (minute / 60)
        
        if 0 <= time_value < 5:  # 00:00 تا 04:59
            line1 = f"نیمه شب بخیر {username} عزیز"
            line2 = "در آرامش باشی دوست من"
        elif 5 <= time_value < 10.5:  # 05:00 تا 10:29
            line1 = f"صبح بخیر {username} عزیز"
            line2 = "پر انرژی باش دوست من اول صبحه"
        elif 10.5 <= time_value < 12:  # 10:30 تا 11:59
            line1 = f"وقت بخیر {username} عزیز"
            line2 = "خدا قوت دوست من هنوز وقت داری"
        elif 12 <= time_value < 14.5:  # 12:00 تا 14:29
            line1 = f"ظهر بخیر {username} عزیز"
            line2 = "ادامه بده دوست من تازه نیمه ی روزه"
        elif 14.5 <= time_value < 16.5:  # 14:30 تا 16:29
            line1 = f"بعدازظهر بخیر {username} عزیز"
            line2 = "تا موفقیت راهی نیست دوست من خسته نشی"
        elif 16.5 <= time_value < 19:  # 16:30 تا 18:59
            line1 = f"عصر بخیر {username} عزیز"
            line2 = "تلاشت ستودنیه دوست من خسته نباشی"
        else:  # 19:00 تا 23:59
            line1 = f"شب بخیر {username} عزیز"
            line2 = "دیگه موقع استراحته نخسته دوست من"
        
        return line1, line2
        
    except Exception as e:
        print(f"خطا در دریافت ساعت: {e}")
        return f"سلام {username} عزیز", "روز خوبی داشته باشی"


def get_reminder_status(username):
    """دریافت وضعیت یادآوری برای کاربر"""
    try:
        file_path = os.path.join(get_data_path(), 'reminder_status.json')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                all_status = json.load(f)
                return all_status.get(username, {})
        return {}
    except Exception as e:
        print(f"خطا در خواندن وضعیت یادآوری: {e}")
        return {}


def save_reminder_status(username, status_data):
    """ذخیره وضعیت یادآوری برای کاربر"""
    try:
        file_path = os.path.join(get_data_path(), 'reminder_status.json')
        all_status = {}
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                all_status = json.load(f)
        
        all_status[username] = status_data
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(all_status, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"خطا در ذخیره وضعیت یادآوری: {e}")
        return False


def should_show_reminder(username):
    """بررسی اینکه آیا امروز باید یادآوری نمایش داده شود"""
    if not username:
        return False
    
    today = get_today_jalali()
    status = get_reminder_status(username)
    
    if not status:
        return True
    
    last_date = status.get('last_reminder_date', '')
    completed = status.get('reminder_completed', False)
    
    if last_date != today or not completed:
        return True
    
    return False


def mark_reminder_shown(username):
    """ثبت اینکه یادآوری امروز نمایش داده شده"""
    if not username:
        return False
    
    today = get_today_jalali()
    status = get_reminder_status(username)
    
    status['last_reminder_date'] = today
    status['reminder_shown'] = True
    status['reminder_completed'] = False
    
    return save_reminder_status(username, status)


def mark_reminder_completed(username, score_data):
    """ثبت اینکه کاربر عملیات یادآوری را انجام داده"""
    if not username:
        return False
    
    today = get_today_jalali()
    status = get_reminder_status(username)
    
    status['last_reminder_date'] = today
    status['reminder_completed'] = True
    status['points_earned'] = status.get('points_earned', 0) + score_data.get('total_points', 0)
    status['total_reminders_completed'] = status.get('total_reminders_completed', 0) + 1
    status['last_score'] = score_data
    
    return save_reminder_status(username, status)


def get_total_points(username):
    """دریافت مجموع امتیازات کاربر"""
    if not username:
        return 0
    status = get_reminder_status(username)
    return status.get('points_earned', 0)


def get_reminder_messages_by_role(role):
    """دریافت پیام‌های یادآوری بر اساس نقش"""
    messages = {
        'بازاریاب': """
 **یادآوری روزانه**

دوست من، لطفاً امروز این کارها رو انجام بده:
• گزارش عملکرد روزانه رو ثبت کن
• ماموریت‌های در انتظار رو بررسی کن
• ویزیت‌های روزانه رو ثبت کن

 پس از انجام، امتیاز ویژه دریافت می‌کنی!
""",
        'سوپروایزر': """
 **یادآوری روزانه**

دوست من، لطفاً امروز این کارها رو انجام بده:
• گزارشات سرکشی رو ثبت کن
• ماموریت‌های تعیین تکلیف نشده رو بررسی کن

 پس از انجام، امتیاز ویژه دریافت می‌کنی!
""",
        'موزع': """
 **یادآوری روزانه**

دوست من، لطفاً امروز این کارها رو انجام بده:
• گزارش توزیع روزانه رو ثبت کن
• وصول‌ها رو ثبت کن

 پس از انجام، امتیاز ویژه دریافت می‌کنی!
"""
    }
    return messages.get(role, messages['بازاریاب'])


def create_circle_widget(color, size=dp(12)):
    """ایجاد یک دایره رنگی به عنوان جایگزین ایموجی"""
    from kivy.uix.widget import Widget
    from kivy.graphics import Color, Ellipse
    
    circle = Widget(size_hint=(None, None), size=(size, size))
    with circle.canvas:
        Color(*color)
        Ellipse(pos=circle.pos, size=circle.size)
    
    def update_circle(instance, value):
        instance.canvas.clear()
        with instance.canvas:
            Color(*color)
            Ellipse(pos=instance.pos, size=instance.size)
    
    circle.bind(pos=update_circle, size=update_circle)
    return circle


def capture_popup_screenshot(popup, filename_prefix="گزارش_امتیازات"):
    """
    گرفتن اسکرین‌شات از پاپ‌آپ - سازگار با همه پلتفرم‌ها
    """
    try:
        from datetime import datetime
        from utils.storage import get_backup_path
        from kivy.utils import platform
        import os
        
        # ایجاد نام فایل
        today = get_today_jalali().replace('/', '-')
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"{filename_prefix}_{today}_{timestamp}.png"
        
        # مسیر ذخیره
        save_dir = os.path.join(get_backup_path(), 'screenshots')
        os.makedirs(save_dir, exist_ok=True)
        filepath = os.path.join(save_dir, filename)
        
        # ========== روش اصلی: export_to_png (در همه پلتفرم‌ها کار میکند) ==========
        if popup and hasattr(popup.content, 'export_to_png'):
            try:
                popup.content.export_to_png(filepath)
                if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                    print(f"اسکرین‌شات (export_to_png) ذخیره شد: {filepath}")
                    return filepath
            except Exception as e:
                print(f"خطا در export_to_png: {e}")
        
        # ========== روش ۲: فقط برای ویندوز (pyautogui) ==========
        if platform == 'win':
            try:
                import pyautogui
                screenshot = pyautogui.screenshot()
                screenshot.save(filepath, 'PNG')
                print(f"اسکرین‌شات (pyautogui) ذخیره شد: {filepath}")
                return filepath
            except ImportError:
                print("pyautogui نصب نیست (فقط ویندوز)")
            except Exception as e:
                print(f"خطا در pyautogui: {e}")
        
        # ========== روش ۳: فقط برای ویندوز (mss) ==========
        if platform == 'win':
            try:
                import mss
                from PIL import Image
                
                with mss.mss() as sct:
                    monitor = sct.monitors[1]
                    screenshot = sct.grab(monitor)
                    img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                    img.save(filepath, 'PNG')
                    print(f"اسکرین‌شات (mss) ذخیره شد: {filepath}")
                    return filepath
            except ImportError:
                print("mss نصب نیست (فقط ویندوز)")
            except Exception as e:
                print(f"خطا در mss: {e}")
        
        print("هیچ روشی برای گرفتن اسکرین‌شات موفق نبود!")
        return None
        
    except Exception as e:
        print(f"خطا در گرفتن اسکرین‌شات: {e}")
        import traceback
        traceback.print_exc()
        return None


# ============================================================
# تابع نمایش پاپ‌آپ کامل (قابل استفاده در main.py)
# ============================================================

def show_complete_reminder_popup(username, user_data, app_instance):
    """
    نمایش پاپ‌آپ کامل یادآوری با امتیازات
    
    Args:
        username: نام کاربر
        user_data: دیکشنری اطلاعات کاربر
        app_instance: نمونه از MainApp (برای دسترسی به توابع)
    """
    try:
        # ========== ایمپورت bidi ==========
        try:
            import arabic_reshaper
            from bidi.algorithm import get_display
        except:
            arabic_reshaper = None
            get_display = None
        
        def fix_text(text):
            if not text:
                return text
            if arabic_reshaper and get_display:
                try:
                    reshaped = arabic_reshaper.reshape(text)
                    return get_display(reshaped)
                except:
                    return text
            return text
        
        role = user_data.get('role', 'بازاریاب')
        today = get_today_jalali()
        
        # دریافت پیام‌ها بر اساس ساعت
        line1, line2 = get_greeting_by_time(username)
        
        # محاسبه امتیازات
        score_data = calculate_all_scores(username, role, today)
        total_points = score_data.get('total_points', 0)
        
        # ========== ساخت محتوای پاپ‌آپ با اسکرول عمودی ==========
        main_scroll = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True,
            size_hint=(1, 1),
            scroll_type=['bars', 'content'],
            bar_width=dp(6),
            bar_color=(0.3, 0.5, 0.8, 0.8),
            bar_inactive_color=(0.2, 0.2, 0.2, 0.5)
        )
        
        content = BoxLayout(
            orientation='vertical',
            padding=dp(15),
            spacing=dp(6),
            size_hint_y=None
        )
        content.bind(minimum_height=content.setter('height'))
        
        with content.canvas.before:
            Color(0.08, 0.08, 0.08, 1)
            rect = Rectangle(pos=content.pos, size=content.size)
            content.bind(pos=lambda i, v: setattr(rect, 'pos', v),
                        size=lambda i, v: setattr(rect, 'size', v))
        
        # ========== خط 1: روز بخیر ==========
        label1 = Label(
            text=fix_text(line1),
            size_hint_y=None,
            height=dp(40),
            font_size=sp(22),
            bold=True,
            color=(0.4, 0.8, 1, 1),
            halign='center',
            valign='middle'
        )
        label1.bind(size=lambda s, w: setattr(s, 'text_size', (s.width, None)))
        content.add_widget(label1)
        
        # ========== خط 2: پیام انرژی ==========
        label2 = Label(
            text=fix_text(line2),
            size_hint_y=None,
            height=dp(35),
            font_size=sp(17),
            color=(0.8, 0.8, 0.8, 1),
            halign='center',
            valign='middle'
        )
        label2.bind(size=lambda s, w: setattr(s, 'text_size', (s.width, None)))
        content.add_widget(label2)
        
        # ========== خط 2.5: پاداش ==========
        bonus_points = score_data.get('bonus_points', 0)
        multiplier = score_data.get('breakdown', {}).get('multiplier', 0)

        if bonus_points > 0:
            bonus_text = f"پاداش امروز: {bonus_points:,} ریال (ضریب {multiplier})"
        else:
            bonus_text = "پاداش امروز: ۰ ریال"

        label_bonus = Label(
            text=fix_text(bonus_text),
            size_hint_y=None,
            height=dp(35),
            font_size=sp(17),
            bold=True,
            color=(1, 0.8, 0.2, 1),  # طلایی
            halign='center',
            valign='middle'
        )
        label_bonus.bind(size=lambda s, w: setattr(s, 'text_size', (s.width, None)))
        content.add_widget(label_bonus)

        # ========== خط جداکننده ==========
        content.add_widget(BoxLayout(size_hint_y=None, height=dp(3)))
        
        # ========== خط 3: عنوان یادآوری ==========
        label3 = Label(
            text=fix_text("دوست عزیز این موارد رو انجام بده:"),
            size_hint_y=None,
            height=dp(30),
            font_size=sp(15),
            bold=True,
            color=(0.4, 0.8, 1, 1),
            halign='center',
            valign='middle'
        )
        label3.bind(size=lambda s, w: setattr(s, 'text_size', (s.width, None)))
        content.add_widget(label3)
        
        # ========== لیست آیتم‌ها با اسکرول ==========
        items_scroll = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True,
            size_hint_y=None,
            height=dp(380),
            bar_width=dp(4),
            bar_color=(0.3, 0.5, 0.8, 0.6),
            bar_inactive_color=(0.2, 0.2, 0.2, 0.3)
        )
        
        items_container = BoxLayout(
            orientation='vertical',
            spacing=dp(3),
            size_hint_y=None,
            padding=dp(4)
        )
        items_container.bind(minimum_height=items_container.setter('height'))
        
        # ========== تابع ساخت ردیف با دایره رنگی ==========
        def make_row(text, points, is_done, is_good=True):
            row = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(4))
            
            # چک‌باکس
            cb = CheckBox(active=is_done, size_hint_x=0.08, size_hint_y=None, height=dp(26), color=(0.4, 0.7, 1, 1))
            row.add_widget(cb)
            
            # دایره رنگی (سبز = موفق/انجام شده، قرمز = ناموفق/انجام نشده)
            color = (0.2, 0.9, 0.2, 1) if is_done else (0.9, 0.2, 0.2, 1)
            circle = create_circle_widget(color, dp(12))
            circle.size_hint_x = 0.06
            row.add_widget(circle)
            
            # متن
            row.add_widget(Label(
                text=fix_text(text),
                size_hint_x=0.5,
                font_size=sp(13),
                color=(1, 1, 1, 1),
                halign='left',
                valign='middle'
            ))
            
            # امتیاز
            points_text = f"{points} امتیاز" if points > 0 else ""
            row.add_widget(Label(
                text=fix_text(points_text),
                size_hint_x=0.3,
                font_size=sp(13),
                color=(1, 0.8, 0.2, 1),
                halign='right',
                valign='middle'
            ))
            
            return row
        
        # ========== خط 4: وضعیت ورود ==========
        att_points = score_data.get('attendance', {}).get('points', 0)
        has_attendance = att_points > 0
        items_container.add_widget(make_row(
            "ورودت رو ثبت کن",
            att_points,
            has_attendance,
            True
        ))
        
        # ========== خط 4.5: پایان کار ==========
        end_day_points = score_data.get('end_day', {}).get('points', 0)
        has_end_day = end_day_points > 0
        items_container.add_widget(make_row(
            "پایان کارت رو ثبت کن",
            end_day_points,
            has_end_day,
            True
        ))
        
        # ========== خط 5a: ماموریت‌های انجام شده ==========
        mission_points = score_data.get('mission', {}).get('points', 0)
        mission_count = score_data.get('mission', {}).get('count', 0)
        has_mission = mission_count > 0
        items_container.add_widget(make_row(
            f"{mission_count} ماموریت انجام دادی" if mission_count > 0 else "ماموریت انجام بده",
            mission_points,
            has_mission,
            True
        ))
        
        # ========== خطوط تخصصی بر اساس نقش ==========
        if role == 'بازاریاب':
            # خط 6: اولین ویزیت
            first_visit_points = score_data.get('visit', {}).get('first_visit_points', 0)
            has_first_visit = score_data.get('visit', {}).get('has_first_visit', False)
            items_container.add_widget(make_row(
                "اولین ویزیتت رو ثبت کن",
                first_visit_points,
                has_first_visit,
                True
            ))
            
            # خط 7: ادامه ویزیت
            total_visits = score_data.get('visit', {}).get('total_visits', 0)
            visit_points = score_data.get('visit', {}).get('visit_points', 0)
            is_good_visits = total_visits >= 20
            items_container.add_widget(make_row(
                f"به ویزیت ادامه بده ({total_visits})",
                visit_points,
                is_good_visits,
                True
            ))
            
            # خط 8: فروش موفق
            sales_count = score_data.get('visit', {}).get('successful_sales', 0)
            sales_points = score_data.get('visit', {}).get('sales_points', 0)
            items_container.add_widget(make_row(
                f"فروشت رو ببر بالا ({sales_count})",
                sales_points,
                sales_count > 0,
                True
            ))
            
            # خط 9: وصول
            collection_points = score_data.get('collection', {}).get('total_points', 0)
            collection_count = score_data.get('collection', {}).get('success_count', 0)
            items_container.add_widget(make_row(
                f"وصول مطالبات ({collection_count})",
                collection_points,
                collection_count > 0,
                True
            ))
            
        elif role == 'سوپروایزر':
            # خط 6: سرکشی بازار
            market_points = score_data.get('market_visit', {}).get('points', 0)
            market_count = score_data.get('market_visit', {}).get('count', 0)
            is_good_market = market_count >= 5
            items_container.add_widget(make_row(
                f"یه سری به بازار بزن ({market_count})",
                market_points,
                is_good_market,
                True
            ))
            
            # خط 7: هدف‌گذاری
            target_points = score_data.get('target', {}).get('setting_points', 0)
            has_target = score_data.get('target', {}).get('has_setting', False)
            items_container.add_widget(make_row(
                "هدف‌گذاری رو انجام بده",
                target_points,
                has_target,
                True
            ))
            
            # خط 8: تحقق ریزتارگت
            detail_points = score_data.get('target', {}).get('detail_points', 0)
            has_detail = score_data.get('target', {}).get('has_detail', False)
            items_container.add_widget(make_row(
                "تحقق ریزتارگت‌ها",
                detail_points,
                has_detail,
                True
            ))
            
        elif role == 'موزع':
            # خط 6: اولین توزیع
            delivery_count = score_data.get('delivery', {}).get('successful_deliveries', 0)
            delivery_points = score_data.get('delivery', {}).get('delivery_points', 0)
            items_container.add_widget(make_row(
                "اولین توزیع رو ثبت کن",
                delivery_points,
                delivery_count > 0,
                True
            ))
            
            # خط 7: ادامه توزیع
            total_deliveries = score_data.get('delivery', {}).get('successful_deliveries', 0) + score_data.get('delivery', {}).get('failed_deliveries', 0)
            delivery_total_points = score_data.get('delivery', {}).get('total_points', 0)
            is_good_delivery = total_deliveries >= 12
            items_container.add_widget(make_row(
                f"به توزیع ادامه بده ({total_deliveries})",
                delivery_total_points,
                is_good_delivery,
                True
            ))
        
        # ========== خط 10: گزارش به مدیر (همه نقش‌ها) ==========
        report_points = score_data.get('report', {}).get('points', 0)
        has_report = report_points > 0
        items_container.add_widget(make_row(
            "گزارش روزانه بفرست",
            report_points,
            has_report,
            True
        ))
        
        items_scroll.add_widget(items_container)
        content.add_widget(items_scroll)
        
        # ========== خط 11: جمع امتیاز ==========
        content.add_widget(BoxLayout(size_hint_y=None, height=dp(3)))
        
        # تعیین رنگ بر اساس امتیاز
        if total_points >= 301:
            color = (0.2, 0.9, 0.2, 1)  # سبز
        elif 101 <= total_points <= 300:
            color = (1, 0.8, 0.2, 1)  # زرد
        else:
            color = (0.9, 0.5, 0.1, 1)  # نارنجی
        
        label_total = Label(
            text=fix_text(f"جمع امتیاز روز: {total_points:,}"),
            size_hint_y=None,
            height=dp(35),
            font_size=sp(18),
            bold=True,
            color=color,
            halign='center',
            valign='middle'
        )
        label_total.bind(size=lambda s, w: setattr(s, 'text_size', (s.width, None)))
        content.add_widget(label_total)
        
        # ========== دکمه‌ها ==========
        btn_layout = BoxLayout(
            size_hint_y=None,
            height=dp(48),
            spacing=dp(10)
        )
        
        ok_btn = Button(
            text=fix_text('انجامش میدم'),
            size_hint_y=None,
            height=dp(44),
            background_color=(0.2, 0.7, 0.2, 1),
            color=(1, 1, 1, 1),
            font_size=sp(16),
            bold=True
        )
        
        later_btn = Button(
            text=fix_text('بعداً'),
            size_hint_y=None,
            height=dp(44),
            background_color=(0.4, 0.3, 0.6, 1),
            color=(1, 1, 1, 1),
            font_size=sp(15)
        )
        
        btn_layout.add_widget(ok_btn)
        btn_layout.add_widget(later_btn)
        content.add_widget(btn_layout)
        
        # ========== دکمه ذخیره پاداش و گزارش تصویری (ردیف دوم) ==========
        action_layout = BoxLayout(
            size_hint_y=None,
            height=dp(40),
            spacing=dp(10)
        )
        
        # دکمه ذخیره پاداش
        save_bonus_btn = Button(
            text=fix_text('ذخیره پاداش'),
            size_hint_x=0.5,
            size_hint_y=None,
            height=dp(40),
            background_color=(0.8, 0.6, 0.1, 1),
            color=(1, 1, 1, 1),
            font_size=sp(14),
            bold=True
        )
        
        # دکمه گزارش تصویری
        screenshot_btn = Button(
            text=fix_text('گزارش تصویری'),
            size_hint_x=0.5,
            size_hint_y=None,
            height=dp(40),
            background_color=(0.2, 0.5, 0.8, 1),
            color=(1, 1, 1, 1),
            font_size=sp(14),
            bold=True
        )
        
        action_layout.add_widget(save_bonus_btn)
        action_layout.add_widget(screenshot_btn)
        content.add_widget(action_layout)

        # ========== توابع دکمه‌ها ==========
        def on_save_bonus(instance):
            from utils.score_calculator import check_day_ended, save_bonus
            
            # بررسی پایان کار
            end_check = check_day_ended(username, role, today)
            
            if not end_check['ended']:
                # نمایش پیام خطا
                error_content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
                error_content.add_widget(Label(
                    text=fix_text('⚠️ ابتدا باید پایان کار را ثبت کنید!'),
                    font_size=sp(18),
                    color=(1, 1, 1, 1),
                    halign='center'
                ))
                close_btn = Button(
                    text=fix_text('باشه'),
                    size_hint_y=None,
                    height=dp(40),
                    background_color=(0.2, 0.6, 1, 1),
                    color=(1, 1, 1, 1)
                )
                error_content.add_widget(close_btn)
                error_popup = Popup(
                    title=fix_text('⚠️ خطا'),
                    content=error_content,
                    size_hint=(0.7, 0.3),
                    background_color=(0.05, 0.05, 0.05, 1),
                    auto_dismiss=False
                )
                close_btn.bind(on_press=error_popup.dismiss)
                error_popup.open()
                return
            
            # ذخیره پاداش
            success = save_bonus(username, role, today)
            if success:
                save_bonus_btn.disabled = True
                save_bonus_btn.text = fix_text('پاداش ذخیره شد')
                save_bonus_btn.background_color = (0.2, 0.7, 0.2, 1)
                # نمایش پیام موفقیت
                success_content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
                success_content.add_widget(Label(
                    text=fix_text(f'پاداش {bonus_points:,} ریال با موفقیت ذخیره شد!'),
                    font_size=sp(18),
                    color=(0.2, 0.9, 0.2, 1),
                    halign='center'
                ))
                ok_btn_success = Button(
                    text=fix_text('باشه'),
                    size_hint_y=None,
                    height=dp(40),
                    background_color=(0.2, 0.6, 1, 1),
                    color=(1, 1, 1, 1)
                )
                success_content.add_widget(ok_btn_success)
                success_popup = Popup(
                    title=fix_text('موفق'),
                    content=success_content,
                    size_hint=(0.8, 0.3),
                    background_color=(0.05, 0.05, 0.05, 1),
                    auto_dismiss=False
                )
                ok_btn_success.bind(on_press=success_popup.dismiss)
                success_popup.open()

        def on_screenshot(instance):
            # گرفتن اسکرین‌شات با کمی تأخیر برای اطمینان از render شدن کامل
            Clock.schedule_once(lambda dt: _take_screenshot(), 0.3)

        def _take_screenshot():
            filepath = capture_popup_screenshot(popup, f"گزارش_امتیازات_{username}")
            if filepath:
                # نمایش پیام موفقیت
                success_content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
                success_content.add_widget(Label(
                    text=fix_text(f'گزارش تصویری ذخیره شد:\n{os.path.basename(filepath)}'),
                    font_size=sp(16),
                    color=(0.2, 0.9, 0.2, 1),
                    halign='center'
                ))
                ok_btn_screenshot = Button(
                    text=fix_text('باشه'),
                    size_hint_y=None,
                    height=dp(40),
                    background_color=(0.2, 0.6, 1, 1),
                    color=(1, 1, 1, 1)
                )
                success_content.add_widget(ok_btn_screenshot)
                success_popup = Popup(
                    title=fix_text('موفق'),
                    content=success_content,
                    size_hint=(0.8, 0.3),
                    background_color=(0.05, 0.05, 0.05, 1),
                    auto_dismiss=False
                )
                ok_btn_screenshot.bind(on_press=success_popup.dismiss)
                success_popup.open()
            else:
                # نمایش پیام خطا
                error_content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
                error_content.add_widget(Label(
                    text=fix_text('خطا در ذخیره گزارش تصویری'),
                    font_size=sp(18),
                    color=(0.9, 0.2, 0.2, 1),
                    halign='center'
                ))
                close_btn = Button(
                    text=fix_text('باشه'),
                    size_hint_y=None,
                    height=dp(40),
                    background_color=(0.2, 0.6, 1, 1),
                    color=(1, 1, 1, 1)
                )
                error_content.add_widget(close_btn)
                error_popup = Popup(
                    title=fix_text('⚠️ خطا'),
                    content=error_content,
                    size_hint=(0.7, 0.25),
                    background_color=(0.05, 0.05, 0.05, 1),
                    auto_dismiss=False
                )
                close_btn.bind(on_press=error_popup.dismiss)
                error_popup.open()

        save_bonus_btn.bind(on_press=on_save_bonus)
        screenshot_btn.bind(on_press=on_screenshot)

        # ========== ایجاد پاپ‌آپ ==========
        # قرار دادن content داخل اسکرول
        main_scroll.add_widget(content)
        
        popup = Popup(
            title=fix_text('چراغ راهنما'),
            content=main_scroll,
            size_hint=(0.92, 0.9),
            background_color=(0.05, 0.05, 0.05, 1),
            auto_dismiss=False
        )
        
        # ========== توابع دکمه‌ها ==========
        def on_ok(instance):
            mark_reminder_shown(username)
            popup.dismiss()
            if hasattr(app_instance, '_show_score_popup'):
                Clock.schedule_once(lambda dt: app_instance._show_score_popup(username, user_data), 0.3)
        
        def on_later(instance):
            mark_reminder_shown(username)
            popup.dismiss()
        
        ok_btn.bind(on_press=on_ok)
        later_btn.bind(on_press=on_later)
        
        popup.open()
        
    except Exception as e:
        print(f"خطا در نمایش پاپ‌آپ خوش‌آمدگویی: {e}")
        import traceback
        traceback.print_exc()