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
    """ویجت انتخاب فایل - پشتیبانی از اکسل در اندروید و دسکتاپ با فارسی"""
    
    def __init__(self, on_select=None, **kwargs):
        super().__init__(orientation='vertical', spacing=10, **kwargs)
        self.on_select = on_select
        self.selected_file = None
        
        # ============================================
        # ✅ دکمه انتخاب فایل با PersianButton
        # ============================================
        self.select_btn = PersianButton(
            text='📁 انتخاب فایل اکسل',
            size_hint_y=None,
            height=dp(45),
            background_color=(0.2, 0.6, 0.8, 1),  # آبی
            font_size=sp(18)
        )
        self.select_btn.bind(on_press=self.pick_file)
        self.add_widget(self.select_btn)
        
        # ============================================
        # ✅ نمایش نام فایل با PersianLabel
        # ============================================
        self.file_label = PersianLabel(
            text='📄 هیچ فایلی انتخاب نشده',
            font_size=sp(14),
            color=(150, 150, 150, 255),  # خاکستری
            size_hint_y=None,
            height=dp(35),
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
                        filters=[('Excel files', '*.xlsx', '*.xls')]
                    )
                except Exception as e:
                    self.show_error_message(f"خطا در انتخاب فایل: {str(e)}")
            else:
                self.show_error_message("کتابخانه plyer در اندروید نصب نیست")
        else:
            # در دسکتاپ از filechooser استفاده میکنیم
            if PLYER_AVAILABLE:
                try:
                    filechooser.open_file(
                        on_selection=self.file_selected,
                        filters=[('Excel files', '*.xlsx', '*.xls')]
                    )
                except Exception as e:
                    self.show_error_message(f"خطا در انتخاب فایل: {str(e)}")
            else:
                self.show_error_message("برای انتخاب فایل در ویندوز، کتابخانه plyer مورد نیاز است.")
    
    def file_selected(self, selection):
        """پس از انتخاب فایل"""
        if selection:
            file_path = selection[0]
            # بررسی پسوند فایل
            if file_path.lower().endswith(('.xlsx', '.xls')):
                self.selected_file = file_path
                filename = file_path.replace('\\', '/').split('/')[-1]
                # ✅ تنظیم متن با PersianLabel
                self.file_label.set_text(f'✅ فایل: {filename}')
                self.file_label.color = (50, 200, 50, 255)  # سبز
                if self.on_select:
                    self.on_select(self.selected_file)
            else:
                self.selected_file = None
                self.file_label.set_text('❌ فقط فایل‌های Excel (.xlsx, .xls) مجاز هستند')
                self.file_label.color = (200, 50, 50, 255)  # قرمز
                self.show_error_message("لطفاً یک فایل اکسل معتبر انتخاب کنید.")
    
    def show_error_message(self, message):
        """نمایش پیغام خطا با PersianLabel"""
        content = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # ✅ استفاده از PersianLabel برای متن خطا
        msg_label = PersianLabel(
            text=message,
            font_size=sp(16),
            color=(200, 50, 50, 255),  # قرمز
            size_hint_y=None,
            height=dp(50),
            halign='center'
        )
        content.add_widget(msg_label)
        
        # ✅ استفاده از PersianButton
        btn = PersianButton(
            text='باشه',
            size_hint_y=None,
            height=dp(40),
            background_color=(0.3, 0.3, 0.3, 1)
        )
        content.add_widget(btn)
        
        popup = Popup(
            title='⚠️ خطا',
            content=content,
            size_hint=(0.8, 0.3),
            auto_dismiss=True,
            background_color=(1, 1, 1, 1)
        )
        btn.bind(on_press=popup.dismiss)
        popup.open()
    
    def get_file(self):
        """دریافت مسیر فایل انتخاب‌شده"""
        return self.selected_file
    
    def reset(self):
        """بازنشانی ویجت"""
        self.selected_file = None
        self.file_label.set_text('📄 هیچ فایلی انتخاب نشده')
        self.file_label.color = (150, 150, 150, 255)  # خاکستری