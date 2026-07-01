"""
ویجت انتخاب فایل - نسخه بهینه برای اندروید و دسکتاپ با پشتیبانی از فارسی
"""

from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.utils import platform
from kivy.metrics import dp, sp

# ✅ ایمپورت ویجت‌های فارسی
from utils.persian_text import PersianLabel
from utils.rtl_widgets import PersianButton

# تلاش برای ایمپورت plyer در محیط اندروید
try:
    from plyer import filechooser
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False
    print("ℹ️ کتابخانه plyer در دسترس نیست. (در اندروید نصب خواهد شد)")


class FilePicker(BoxLayout):
    """ویجت انتخاب فایل - پشتیبانی از فایل‌های بکاپ در اندروید و دسکتاپ"""
    
    def __init__(self, on_select=None, **kwargs):
        super().__init__(orientation='vertical', spacing=10, **kwargs)
        self.on_select = on_select
        self.selected_file = None
        
        # ============================================
        # ✅ دکمه انتخاب فایل بکاپ - با متن انگلیسی
        # ============================================
        self.select_btn = PersianButton(
            text='📁 Select Backup File',  # ✅ تغییر به انگلیسی
            size_hint_y=None,
            height=dp(50),  # ✅ افزایش ارتفاع
            background_color=(0.2, 0.6, 0.8, 1),  # آبی
            font_size=sp(20)  # ✅ افزایش فونت
        )
        self.select_btn.bind(on_press=self.pick_file)
        self.add_widget(self.select_btn)
        
        # ============================================
        # ✅ نمایش نام فایل با PersianLabel
        # ============================================
        self.file_label = PersianLabel(
            text='📄 No file selected',
            font_size=sp(16),  # ✅ افزایش
            color=(150, 150, 150, 255),  # خاکستری
            size_hint_y=None,
            height=dp(40),  # ✅ افزایش
            halign='center'
        )
        self.add_widget(self.file_label)
    
    def pick_file(self, instance):
        """باز کردن دیالوگ انتخاب فایل"""
        if platform == 'android':
            # در اندروید از filechooser استفاده میکنیم
            if PLYER_AVAILABLE:
                try:
                    filechooser.open_file(
                        on_selection=self.file_selected,
                        filters=[('Zip files', '*.zip'), ('All files', '*')]  # ✅ فیلتر zip
                    )
                except Exception as e:
                    self.show_error_message(f"Error selecting file: {str(e)}")
            else:
                self.show_error_message("plyer library not available on Android")
        else:
            # در دسکتاپ از filechooser استفاده میکنیم
            if PLYER_AVAILABLE:
                try:
                    filechooser.open_file(
                        on_selection=self.file_selected,
                        filters=[('Zip files', '*.zip'), ('All files', '*')]
                    )
                except Exception as e:
                    self.show_error_message(f"Error selecting file: {str(e)}")
            else:
                self.show_error_message("plyer library required for file selection on Windows.")
    
    def file_selected(self, selection):
        """پس از انتخاب فایل - با بررسی کامل برای جلوگیری از خطای NoneType"""
        try:
            # ✅ بررسی اینکه selection وجود داشته باشه و خالی نباشه
            if not selection or len(selection) == 0:
                self.selected_file = None
                self.file_label.set_text('⚠️ No file selected')
                self.file_label.color = (200, 150, 50, 255)  # نارنجی
                return
            
            # ✅ گرفتن مسیر فایل
            file_path = selection[0]
            
            # ✅ بررسی اینکه مسیر خالی نباشه
            if not file_path:
                self.selected_file = None
                self.file_label.set_text('⚠️ Invalid file path')
                self.file_label.color = (200, 50, 50, 255)  # قرمز
                return
            
            # ✅ بررسی پسوند فایل (با safe check) - فقط zip برای بکاپ
            file_lower = file_path.lower() if file_path else ''
            if file_lower.endswith('.zip'):
                self.selected_file = file_path
                filename = file_path.replace('\\', '/').split('/')[-1]
                # ✅ تنظیم متن با PersianLabel
                self.file_label.set_text(f'✅ File: {filename}')
                self.file_label.color = (50, 200, 50, 255)  # سبز
                if self.on_select:
                    self.on_select(self.selected_file)
            else:
                self.selected_file = None
                self.file_label.set_text('❌ Only .zip files are allowed')
                self.file_label.color = (200, 50, 50, 255)  # قرمز
                self.show_error_message("Please select a valid .zip backup file.")
                
        except Exception as e:
            # ✅ مدیریت هرگونه خطای غیرمنتظره
            self.selected_file = None
            self.file_label.set_text(f'⚠️ Error: {str(e)[:30]}')
            self.file_label.color = (200, 50, 50, 255)  # قرمز
            self.show_error_message(f"Error processing file: {str(e)}")
    
    def show_error_message(self, message):
        """نمایش پیغام خطا با PersianLabel"""
        content = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # ✅ استفاده از PersianLabel برای متن خطا
        msg_label = PersianLabel(
            text=message,
            font_size=sp(18),  # ✅ افزایش
            color=(200, 50, 50, 255),  # قرمز
            size_hint_y=None,
            height=dp(60),  # ✅ افزایش
            halign='center'
        )
        content.add_widget(msg_label)
        
        # ✅ استفاده از PersianButton
        btn = PersianButton(
            text='OK',
            size_hint_y=None,
            height=dp(50),  # ✅ افزایش
            background_color=(0.3, 0.3, 0.3, 1),
            color=(1, 1, 1, 1),
            font_size=sp(18)  # ✅ افزایش
        )
        content.add_widget(btn)
        
        popup = Popup(
            title='⚠️ Error',
            content=content,
            size_hint=(0.85, 0.35),  # ✅ افزایش
            auto_dismiss=True
        )
        popup.title_color = (1, 1, 1, 1)
        popup.title_size = sp(22)  # ✅ افزایش
        btn.bind(on_press=popup.dismiss)
        popup.open()
    
    def get_file(self):
        """دریافت مسیر فایل انتخاب‌شده"""
        return self.selected_file
    
    def reset(self):
        """بازنشانی ویجت"""
        self.selected_file = None
        self.file_label.set_text('📄 No file selected')
        self.file_label.color = (150, 150, 150, 255)  # خاکستری