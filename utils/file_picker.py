"""
ویجت انتخاب فایل - نسخه نهایی با دیباگ
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import dp, sp
from kivy.utils import platform

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
        super().__init__(orientation='vertical', spacing=10, **kwargs)
        self.on_select = on_select
        self.selected_file = None
        self.file_type = file_type
        self.size_hint_y = None
        self.height = dp(120)
        
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
        
        self.file_label = PersianLabel(
            text=label_text,
            font_size=sp(16),
            color=(150, 150, 150, 255),
            size_hint_y=None,
            height=dp(40),
            halign='center'
        )
        self.add_widget(self.file_label)
        
        self._file_filter = file_filter
        self._extensions = extensions
    
    def pick_file(self, instance):
        """باز کردن دیالوگ انتخاب فایل"""
        print(f"🔍 FilePicker.pick_file: file_type={self.file_type}")
        
        if not PLYER_AVAILABLE:
            self._show_error("کتابخانه انتخاب فایل در دسترس نیست")
            return
        
        try:
            filechooser.open_file(
                on_selection=self._on_selection,
                filters=self._file_filter
            )
        except Exception as e:
            self._show_error(f"خطا: {str(e)}")
    
    def _on_selection(self, selection):
        """پس از انتخاب فایل"""
        print(f"🔍 FilePicker._on_selection: selection={selection}")
        
        try:
            if not selection or len(selection) == 0:
                self.selected_file = None
                self._update_label('⚠️ هیچ فایلی انتخاب نشد', (200, 150, 50, 255))
                return
            
            file_path = selection[0]
            print(f"🔍 FilePicker: file_path={file_path}")
            
            if not file_path:
                self.selected_file = None
                self._update_label('⚠️ مسیر نامعتبر', (200, 50, 50, 255))
                return
            
            # ✅ بررسی پسوند
            file_lower = file_path.lower()
            is_valid = any(file_lower.endswith(ext) for ext in self._extensions)
            print(f"🔍 FilePicker: is_valid={is_valid}, extensions={self._extensions}")
            
            if is_valid:
                self.selected_file = file_path
                filename = file_path.replace('\\', '/').split('/')[-1]
                self._update_label(f'✅ {filename}', (50, 200, 50, 255))
                
                print(f"🔍 FilePicker: calling on_select with {file_path}")
                
                # ✅ فراخوانی on_select
                if self.on_select:
                    self.on_select(file_path)
                else:
                    print("⚠️ FilePicker: on_select is None!")
            else:
                self.selected_file = None
                ext_text = ' یا '.join(self._extensions)
                self._update_label(f'❌ فقط فایل‌های {ext_text} مجازند', (200, 50, 50, 255))
                self._show_error(f'لطفاً یک فایل {ext_text} انتخاب کنید')
                
        except Exception as e:
            print(f"❌ FilePicker error: {e}")
            import traceback
            traceback.print_exc()
            self.selected_file = None
            self._update_label(f'⚠️ خطا', (200, 50, 50, 255))
            self._show_error(f'خطا در پردازش: {str(e)}')
    
    def _update_label(self, text, color):
        """به‌روزرسانی لیبل"""
        self.file_label.set_text(text)
        self.file_label.color = tuple(int(c * 255) if c <= 1 else int(c) for c in color)
    
    def _show_error(self, message):
        """نمایش پیام خطا"""
        from kivy.uix.popup import Popup
        
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
            text='باشه',
            size_hint_y=None,
            height=dp(50),
            background_color=(0.3, 0.3, 0.3, 1),
            color=(1, 1, 1, 1),
            font_size=sp(18)
        )
        content.add_widget(btn)
        
        popup = Popup(
            title='⚠️ خطا',
            content=content,
            size_hint=(0.85, 0.35),
            auto_dismiss=True
        )
        popup.title_color = (1, 1, 1, 1)
        popup.title_size = sp(22)
        btn.bind(on_press=popup.dismiss)
        popup.open()
    
    def get_file(self):
        """دریافت مسیر فایل"""
        return self.selected_file
    
    def reset(self):
        """بازنشانی ویجت"""
        self.selected_file = None
        if self.file_type == 'excel':
            self.file_label.set_text('📄 هیچ فایلی انتخاب نشده')
        else:
            self.file_label.set_text('📄 No file selected')
        self.file_label.color = (150, 150, 150, 255)