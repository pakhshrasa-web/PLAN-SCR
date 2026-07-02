"""
ویجت انتخاب فایل - نسخه ترکیبی برای اندروید و دسکتاپ
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import dp, sp
from kivy.utils import platform
import os

from utils.persian_text import PersianLabel
from utils.rtl_widgets import PersianButton

try:
    from plyer import filechooser
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False


class FilePicker(BoxLayout):
    """ویجت انتخاب فایل - با پشتیبانی از اندروید و دسکتاپ"""
    
    def __init__(self, on_select=None, file_type='excel', **kwargs):
        super().__init__(orientation='vertical', spacing=10, **kwargs)
        self.on_select = on_select
        self.selected_file = None
        self.file_type = file_type
        self.size_hint_y = None
        self.height = dp(120)
        
        if file_type == 'excel':
            btn_text = '📁 انتخاب فایل اکسل'
            extensions = ('.xlsx', '.xls')
            label_text = '📄 هیچ فایلی انتخاب نشده'
        else:
            btn_text = '📁 انتخاب فایل بکاپ'
            extensions = ('.zip',)
            label_text = '📄 هیچ فایلی انتخاب نشده'
        
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
        
        self._extensions = extensions
    
    def pick_file(self, instance):
        """باز کردن انتخابگر فایل"""
        print(f"🔍 FilePicker.pick_file: file_type={self.file_type}, platform={platform}")
        
        if platform == 'android':
            self._pick_file_android()
        else:
            self._pick_file_desktop()
    
    def _pick_file_android(self):
        """انتخاب فایل در اندروید - تلاش با plyer اول"""
        # ✅ ابتدا try با plyer
        if PLYER_AVAILABLE:
            try:
                filters = [('Excel files', '*.xlsx', '*.xls')] if self.file_type == 'excel' else [('Zip files', '*.zip')]
                filechooser.open_file(
                    on_selection=self._process_selection,
                    filters=filters
                )
                print("📂 انتخابگر با plyer باز شد")
                return
            except Exception as e:
                print(f"⚠️ خطا در plyer: {e}")
        
        # ✅ Fallback به FileChooserListView
        self._pick_file_with_filechooser()
    
    def _pick_file_with_filechooser(self):
        """انتخاب فایل با FileChooserListView (Fallback)"""
        try:
            from kivy.uix.filechooser import FileChooserListView
            from kivy.uix.popup import Popup
            from utils.storage import get_import_path, get_backup_path
            
            content = BoxLayout(orientation='vertical', spacing=dp(5))
            
            # ✅ انتخاب مسیر شروع
            if self.file_type == 'excel':
                start_path = '/storage/emulated/0/Download/'
            else:
                start_path = '/storage/emulated/0/Download/'
            
            # ✅ اگر پوشه import وجود داره، از اون استفاده کن
            try:
                from utils.storage import get_import_path
                import_path = get_import_path()
                if os.path.exists(import_path):
                    start_path = import_path
            except:
                pass
            
            filechooser = FileChooserListView(
                path=start_path,
                filters=['*'],
                size_hint_y=0.8,
                show_hidden=False
            )
            content.add_widget(filechooser)
            
            btn_layout = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(5), padding=dp(5))
            
            select_btn = PersianButton(
                text='✅ انتخاب',
                size_hint_x=0.4,
                background_color=(0.2, 0.7, 0.2, 1),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            
            cancel_btn = PersianButton(
                text='❌ انصراف',
                size_hint_x=0.4,
                background_color=(0.8, 0.2, 0.2, 1),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            
            btn_layout.add_widget(select_btn)
            btn_layout.add_widget(cancel_btn)
            content.add_widget(btn_layout)
            
            popup = Popup(
                title='📂 انتخاب فایل',
                content=content,
                size_hint=(0.92, 0.8),
                auto_dismiss=False
            )
            popup.title_color = (1, 1, 1, 1)
            popup.title_size = sp(22)
            
            def on_select(instance):
                if filechooser.selection:
                    file_path = filechooser.selection[0]
                    if self.file_type == 'excel':
                        if file_path.lower().endswith(('.xlsx', '.xls')):
                            popup.dismiss()
                            self._process_selection([file_path])
                        else:
                            self._update_label('⚠️ فقط فایل اکسل مجاز است', (200, 50, 50, 255))
                    else:
                        if file_path.lower().endswith('.zip'):
                            popup.dismiss()
                            self._process_selection([file_path])
                        else:
                            self._update_label('⚠️ فقط فایل zip مجاز است', (200, 50, 50, 255))
                else:
                    self._update_label('⚠️ هیچ فایلی انتخاب نشد', (200, 150, 50, 255))
            
            def on_cancel(instance):
                popup.dismiss()
                self._update_label('⚠️ انتخاب لغو شد', (200, 150, 50, 255))
            
            select_btn.bind(on_press=on_select)
            cancel_btn.bind(on_press=on_cancel)
            
            popup.open()
            
        except Exception as e:
            print(f"❌ خطا در FileChooserListView: {e}")
            import traceback
            traceback.print_exc()
            self._show_error(f"خطا در انتخاب فایل: {str(e)}")
    
    def _pick_file_desktop(self):
        """انتخاب فایل در دسکتاپ با plyer"""
        if PLYER_AVAILABLE:
            try:
                filechooser.open_file(
                    on_selection=self._process_selection,
                    filters=[('Excel files', '*.xlsx', '*.xls')] if self.file_type == 'excel' else [('Zip files', '*.zip')]
                )
            except Exception as e:
                self._show_error(f"خطا: {str(e)}")
        else:
            self._show_error("کتابخانه انتخاب فایل در دسترس نیست")
    
    def _process_selection(self, selection):
        """پردازش انتخاب فایل"""
        print(f"🔍 FilePicker._process_selection: selection={selection}")
        
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
            
            file_lower = file_path.lower()
            is_valid = any(file_lower.endswith(ext) for ext in self._extensions)
            print(f"🔍 FilePicker: is_valid={is_valid}")
            
            if is_valid:
                self.selected_file = file_path
                filename = file_path.replace('\\', '/').split('/')[-1]
                self._update_label(f'✅ {filename}', (50, 200, 50, 255))
                
                print(f"🔍 FilePicker: calling on_select with {file_path}")
                if self.on_select:
                    self.on_select(file_path)
            else:
                self.selected_file = None
                ext_text = ' یا '.join(self._extensions)
                self._update_label(f'❌ فقط فایل‌های {ext_text} مجازند', (200, 50, 50, 255))
                self._show_error(f'لطفاً یک فایل {ext_text} انتخاب کنید')
                
        except Exception as e:
            print(f"❌ FilePicker error: {e}")
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
            self.file_label.set_text('📄 هیچ فایلی انتخاب نشده')
        self.file_label.color = (150, 150, 150, 255)
