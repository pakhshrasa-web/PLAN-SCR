"""
ویجت انتخاب فایل - نسخه بهینه برای اندروید و دسکتاپ
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.utils import platform
from kivy.metrics import dp, sp

from utils.persian_text import PersianLabel
from utils.rtl_widgets import PersianButton

try:
    from plyer import filechooser
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False
    print("ℹ️ plyer در دسترس نیست")


class FilePicker(BoxLayout):
    """ویجت انتخاب فایل - پشتیبانی از اکسل و بکاپ"""
    
    def __init__(self, on_select=None, file_type='excel', **kwargs):
        """
        file_type: 'excel' یا 'backup'
        """
        super().__init__(orientation='vertical', spacing=10, **kwargs)
        self.on_select = on_select
        self.selected_file = None
        self.file_type = file_type
        
        # ✅ تنظیمات بر اساس نوع فایل
        if file_type == 'excel':
            btn_text = '📁 انتخاب فایل اکسل'
            file_filter = [('Excel files', '*.xlsx', '*.xls')]
            extensions = ('.xlsx', '.xls')
            label_text = '📄 هیچ فایلی انتخاب نشده'
        else:  # backup
            btn_text = '📁 Select Backup File'
            file_filter = [('Zip files', '*.zip'), ('All files', '*')]
            extensions = ('.zip',)
            label_text = '📄 No file selected'
        
        # ============================================
        # ✅ دکمه انتخاب فایل
        # ============================================
        self.select_btn = PersianButton(
            text=btn_text,
            size_hint_y=None,
            height=dp(50),
            background_color=(0.2, 0.6, 0.8, 1),
            font_size=sp(20),
            color=(1, 1, 1, 1)
        )
        self.select_btn.bind(on_press=self.pick_file)
        self.add_widget(self.select_btn)
        
        # ============================================
        # ✅ نمایش نام فایل
        # ============================================
        self.file_label = PersianLabel(
            text=label_text,
            font_size=sp(16),
            color=(150, 150, 150, 255),
            size_hint_y=None,
            height=dp(40),
            halign='center'
        )
        self.add_widget(self.file_label)
        
        # ✅ ذخیره تنظیمات
        self._file_filter = file_filter
        self._extensions = extensions
    
    def pick_file(self, instance):
        """باز کردن دیالوگ انتخاب فایل"""
        if PLYER_AVAILABLE:
            try:
                filechooser.open_file(
                    on_selection=self.file_selected,
                    filters=self._file_filter
                )
            except Exception as e:
                self.show_error_message(f"Error selecting file: {str(e)}")
        else:
            self.show_error_message("plyer library not available")
    
    def file_selected(self, selection):
        """پس از انتخاب فایل"""
        try:
            # ✅ بررسی انتخاب
            if not selection or len(selection) == 0:
                self.selected_file = None
                self.file_label.set_text('⚠️ No file selected')
                self.file_label.color = (200, 150, 50, 255)
                return
            
            # ✅ گرفتن مسیر
            file_path = selection[0]
            
            if not file_path:
                self.selected_file = None
                self.file_label.set_text('⚠️ Invalid file path')
                self.file_label.color = (200, 50, 50, 255)
                return
            
            # ✅ بررسی پسوند
            file_lower = file_path.lower()
            valid = False
            for ext in self._extensions:
                if file_lower.endswith(ext):
                    valid = True
                    break
            
            if valid:
                self.selected_file = file_path
                filename = file_path.replace('\\', '/').split('/')[-1]
                self.file_label.set_text(f'✅ {filename}')
                self.file_label.color = (50, 200, 50, 255)
                
                if self.on_select:
                    self.on_select(file_path)
            else:
                self.selected_file = None
                ext_text = ', '.join(self._extensions)
                self.file_label.set_text(f'❌ Only {ext_text} files allowed')
                self.file_label.color = (200, 50, 50, 255)
                self.show_error_message(f"Please select a valid file ({ext_text})")
                
        except Exception as e:
            self.selected_file = None
            self.file_label.set_text(f'⚠️ Error: {str(e)[:30]}')
            self.file_label.color = (200, 50, 50, 255)
            self.show_error_message(f"Error processing file: {str(e)}")
    
    def show_error_message(self, message):
        """نمایش پیغام خطا"""
        from kivy.uix.popup import Popup
        from kivy.uix.button import Button
        from kivy.uix.label import Label
        
        content = BoxLayout(orientation='vertical', padding=20, spacing=10)
        msg_label = PersianLabel(
            text=message,
            font_size=sp(18),
            color=(200, 50, 50, 255),
            size_hint_y=None,
            height=dp(60),
            halign='center'
        )
        content.add_widget(msg_label)
        
        btn = PersianButton(
            text='OK',
            size_hint_y=None,
            height=dp(50),
            background_color=(0.3, 0.3, 0.3, 1),
            color=(1, 1, 1, 1),
            font_size=sp(18)
        )
        content.add_widget(btn)
        
        popup = Popup(
            title='⚠️ Error',
            content=content,
            size_hint=(0.85, 0.35),
            auto_dismiss=True
        )
        popup.title_color = (1, 1, 1, 1)
        popup.title_size = sp(22)
        btn.bind(on_press=popup.dismiss)
        popup.open()
    
    def get_file(self):
        """دریافت مسیر فایل انتخاب‌شده"""
        return self.selected_file
    
    def reset(self):
        """بازنشانی ویجت"""
        self.selected_file = None
        if self.file_type == 'excel':
            self.file_label.set_text('📄 هیچ فایلی انتخاب نشده')
        else:
            self.file_label.set_text('📄 No file selected')
        self.file_label.color = (150, 150, 150, 255)
