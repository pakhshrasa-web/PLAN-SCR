"""
ویجت انتخاب فایل - نسخه بهینه برای اندروید و دسکتاپ
"""

from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.utils import platform
from kivy.clock import Clock

# تلاش برای ایمپورت plyer در محیط اندروید
try:
    from plyer import filechooser
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False
    print("ℹ️ کتابخانه plyer در دسترس نیست. (در اندروید نصب خواهد شد)")

class FilePicker(BoxLayout):
    """ویجت انتخاب فایل - پشتیبانی از اکسل در اندروید و دسکتاپ"""
    
    def __init__(self, on_select=None, **kwargs):
        super().__init__(orientation='vertical', spacing=10, **kwargs)
        self.on_select = on_select
        self.selected_file = None
        self._selection_pending = False
        
        self.select_btn = Button(
            text='📁 انتخاب فایل اکسل',
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.6, 0.8, 1)
        )
        self.select_btn.bind(on_press=self.pick_file)
        self.add_widget(self.select_btn)
        
        self.file_label = Label(
            text='📄 هیچ فایلی انتخاب نشده',
            size_hint_y=None,
            height=40,
            color=(0.5, 0.5, 0.5, 1)
        )
        self.add_widget(self.file_label)
    
    def pick_file(self, instance):
        """باز کردن دیالوگ انتخاب فایل"""
        # جلوگیری از انتخاب همزمان
        if self._selection_pending:
            return
        
        self._selection_pending = True
        
        if platform == 'android':
            # در اندروید از filechooser استفاده میکنیم
            if PLYER_AVAILABLE:
                try:
                    filechooser.open_file(
                        on_selection=self.file_selected,
                        filters=[('Excel files', '*.xlsx', '*.xls')]
                    )
                except Exception as e:
                    self._selection_pending = False
                    self.show_error_message(f"خطا در انتخاب فایل: {str(e)}")
            else:
                self._selection_pending = False
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
                    self._selection_pending = False
                    self.show_error_message(f"خطا در انتخاب فایل: {str(e)}")
            else:
                self._selection_pending = False
                self.show_error_message("برای انتخاب فایل در ویندوز، کتابخانه plyer مورد نیاز است.")
    
    def file_selected(self, selection):
        """پس از انتخاب فایل"""
        self._selection_pending = False
        
        if selection:
            file_path = selection[0]
            # بررسی پسوند فایل
            if file_path.lower().endswith(('.xlsx', '.xls')):
                self.selected_file = file_path
                filename = file_path.replace('\\', '/').split('/')[-1]
                self.file_label.text = f'✅ فایل: {filename}'
                self.file_label.color = (0.2, 0.7, 0.2, 1)  # سبز
                if self.on_select:
                    self.on_select(self.selected_file)
            else:
                self.selected_file = None
                self.file_label.text = '❌ فقط فایل‌های Excel (.xlsx, .xls) مجاز هستند'
                self.file_label.color = (0.8, 0.2, 0.2, 1)  # قرمز
                self.show_error_message("لطفاً یک فایل اکسل معتبر انتخاب کنید.")
        else:
            # کاربر انصراف داده
            self._selection_pending = False
    
    def show_error_message(self, message):
        """نمایش پیغام خطا"""
        content = BoxLayout(orientation='vertical', padding=20, spacing=10)
        content.add_widget(Label(text=message, halign='center'))
        btn = Button(text='باشه', size_hint_y=None, height=40)
        content.add_widget(btn)
        
        popup = Popup(
            title='⚠️ خطا',
            content=content,
            size_hint=(0.8, 0.3),
            auto_dismiss=True
        )
        btn.bind(on_press=popup.dismiss)
        popup.open()
    
    def get_file(self):
        """دریافت مسیر فایل انتخاب‌شده"""
        return self.selected_file
    
    def reset(self):
        """بازنشانی ویجت"""
        self.selected_file = None
        self._selection_pending = False
        self.file_label.text = '📄 هیچ فایلی انتخاب نشده'
        self.file_label.color = (0.5, 0.5, 0.5, 1)
    
    def set_file(self, filepath):
        """تنظیم فایل به صورت دستی"""
        if filepath and os.path.exists(filepath):
            self.selected_file = filepath
            filename = os.path.basename(filepath)
            self.file_label.text = f'✅ فایل: {filename}'
            self.file_label.color = (0.2, 0.7, 0.2, 1)
            if self.on_select:
                self.on_select(self.selected_file)
            return True
        return False