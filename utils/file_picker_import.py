"""
ویجت انتخاب فایل اکسل - مخصوص ورود اطلاعات
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import dp, sp
from kivy.utils import platform
from kivy.clock import Clock
import os

from utils.persian_text import PersianLabel
from utils.rtl_widgets import PersianButton, PersianPopup


class ImportFilePicker(BoxLayout):
    """ویجت انتخاب فایل اکسل - فقط .xlsx, .xls"""
    
    def __init__(self, on_select=None, **kwargs):
        super().__init__(orientation='vertical', spacing=10, **kwargs)
        self.on_select = on_select
        self.selected_file = None
        self.size_hint_y = None
        self.height = dp(120)
        self._pending_result = False
        
        self.select_btn = PersianButton(
            text='انتخاب فایل اکسل',
            size_hint_y=None,
            height=dp(50),
            background_color=(0.2, 0.6, 0.8, 1),
            font_size=sp(20),
            color=(1, 1, 1, 1)
        )
        self.select_btn.bind(on_press=self.pick_file)
        self.add_widget(self.select_btn)
        
        self.file_label = PersianLabel(
            text='هیچ فایلی انتخاب نشده',
            font_size=sp(16),
            color=(150, 150, 150, 255),
            size_hint_y=None,
            height=dp(40),
            halign='center'
        )
        self.add_widget(self.file_label)
        
        if platform == 'android':
            self._register_intent_handler()
    
    def _register_intent_handler(self):
        """ثبت هندلر برای دریافت نتیجه انتخاب فایل"""
        try:
            from android import mActivity
            from android.activity import bind
            
            # ذخیره callback در activity
            mActivity._import_file_picker_callback = self._on_intent_result
            
            def intent_handler(request_code, result_code, data):
                callback = getattr(mActivity, '_import_file_picker_callback', None)
                if callback and request_code == 3001:
                    callback(request_code, result_code, data)
            
            bind(on_activity_result=intent_handler)
            mActivity._import_file_picker_registered = True
            print("ImportFilePicker: هندلر ثبت شد")
        except Exception as e:
            print(f"خطا در ثبت هندلر: {e}")
    
    def pick_file(self, instance):
        """باز کردن دیالوگ انتخاب فایل"""
        if platform == 'android':
            self._pick_file_intent()
        else:
            self._pick_file_desktop()
    
    def _pick_file_intent(self):
        """انتخاب فایل در اندروید با Intent"""
        try:
            from android import mActivity
            from jnius import autoclass
            
            # تنظیم callback
            mActivity._import_file_picker_callback = self._on_intent_result
            self._pending_result = True
            
            # ایجاد Intent
            Intent = autoclass('android.content.Intent')
            intent = Intent(Intent.ACTION_GET_CONTENT)
            intent.addCategory(Intent.CATEGORY_OPENABLE)
            intent.setType("*/*")
            
            # محدود کردن به فایل‌های اکسل
            mime_types = [
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/vnd.ms-excel"
            ]
            intent.putExtra(Intent.EXTRA_MIME_TYPES, mime_types)
            
            print("باز کردن انتخابگر اکسل")
            mActivity.startActivityForResult(intent, 3001)
            
        except Exception as e:
            print(f"خطا در باز کردن انتخابگر: {e}")
            self._show_error(f"خطا: {str(e)}")
    
    def _on_intent_result(self, request_code, result_code, data):
        """دریافت نتیجه انتخاب فایل"""
        print(f"_on_intent_result: request={request_code}, result={result_code}")
        
        if request_code != 3001 or not self._pending_result:
            return
        self._pending_result = False
        
        if result_code != -1:  # RESULT_OK = -1
            self._update_label('انتخاب لغو شد', (200, 150, 50, 255))
            return
        
        if not data:
            self._update_label('داده‌ای دریافت نشد', (200, 50, 50, 255))
            return
        
        try:
            # دریافت Uri
            uri = data.getData()
            if not uri:
                self._update_label('URI نامعتبر', (200, 50, 50, 255))
                return
            
            # دریافت نام فایل
            filename = self._get_filename_from_uri(uri)
            if not filename:
                import hashlib
                filename = f"excel_{hashlib.md5(str(uri).encode()).hexdigest()[:8]}.xlsx"
            
            # کپی فایل از Uri
            file_path = self._copy_from_uri(uri, filename)
            if file_path:
                self._process_file(file_path)
            else:
                self._update_label('خطا در کپی فایل', (200, 50, 50, 255))
                
        except Exception as e:
            print(f"خطا در پردازش نتیجه: {e}")
            import traceback
            traceback.print_exc()
            self._show_error(f"خطا: {str(e)}")
    
    def _copy_from_uri(self, uri, filename=None):
        """
        کپی فایل از Uri به پوشه import
        این روش اصلی و قابل اعتماد برای اندروید است
        """
        try:
            from android import mActivity
            from jnius import autoclass, cast
            import io
            
            # دریافت ContentResolver
            content_resolver = mActivity.getContentResolver()
            
            if filename is None:
                filename = self._get_filename_from_uri(uri)
                if not filename:
                    import hashlib
                    filename = f"excel_{hashlib.md5(str(uri).encode()).hexdigest()[:8]}.xlsx"
            
            # ایجاد پوشه import
            from utils.storage import get_app_import_path
            import_path = get_app_import_path()
            os.makedirs(import_path, exist_ok=True)
            dest_path = os.path.join(import_path, filename)
            
            # باز کردن InputStream از Uri
            input_stream = content_resolver.openInputStream(uri)
            if not input_stream:
                print("InputStream null")
                return None
            
            # کپی فایل
            with input_stream:
                with open(dest_path, 'wb') as output:
                    # خواندن با بافر 8KB
                    buffer = bytearray(8192)
                    while True:
                        bytes_read = input_stream.read(buffer)
                        if bytes_read == -1:
                            break
                        output.write(buffer[:bytes_read])
            
            # بررسی وجود فایل
            if os.path.exists(dest_path):
                print(f"فایل کپی شد: {dest_path} ({os.path.getsize(dest_path)} bytes)")
                return dest_path
            else:
                print("فایل کپی نشد")
                return None
            
        except Exception as e:
            print(f"خطا در کپی از Uri: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _get_filename_from_uri(self, uri):
        """
        دریافت نام فایل از Uri
        از ContentResolver برای دریافت DISPLAY_NAME استفاده میکند
        """
        try:
            from android import mActivity
            from jnius import autoclass
            from android.provider import OpenableColumns
            
            content_resolver = mActivity.getContentResolver()
            
            # Query برای دریافت نام فایل
            cursor = content_resolver.query(uri, None, None, None, None)
            
            if cursor and cursor.moveToFirst():
                # تلاش برای دریافت DISPLAY_NAME
                name_index = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                if name_index != -1:
                    filename = cursor.getString(name_index)
                    cursor.close()
                    if filename:
                        print(f"نام فایل از cursor: {filename}")
                        return filename
                cursor.close()
            
            # روش جایگزین: استخراج از Uri
            uri_str = str(uri)
            import urllib.parse
            decoded = urllib.parse.unquote(uri_str)
            
            # استخراج نام از مسیر
            if '/' in decoded:
                filename = decoded.split('/')[-1]
            else:
                filename = decoded
            
            # حذف پارامترها
            if '?' in filename:
                filename = filename.split('?')[0]
            
            # بررسی پسوند
            ext = '.xlsx' if '.xlsx' in filename.lower() else '.xls' if '.xls' in filename.lower() else None
            if ext:
                print(f"نام فایل از Uri: {filename}")
                return filename
            
            print(f"نام فایل معتبر پیدا نشد: {filename}")
            return None
            
        except Exception as e:
            print(f"خطا در دریافت نام فایل: {e}")
            return None
    
    def _pick_file_desktop(self):
        """انتخاب فایل در دسکتاپ با FileChooserListView"""
        try:
            from kivy.uix.filechooser import FileChooserListView
            from kivy.uix.popup import Popup
            from utils.storage import get_app_import_path
            
            content = BoxLayout(orientation='vertical', spacing=dp(5))
            
            start_path = get_app_import_path()
            if not os.path.exists(start_path):
                os.makedirs(start_path, exist_ok=True)
            
            filechooser = FileChooserListView(
                path=start_path,
                filters=['*.xlsx', '*.xls'],
                size_hint_y=0.8,
                show_hidden=False
            )
            content.add_widget(filechooser)
            
            btn_layout = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(5))
            select_btn = PersianButton(
                text='انتخاب',
                size_hint_x=0.4,
                background_color=(0.2, 0.7, 0.2, 1),
                color=(1,1,1,1)
            )
            cancel_btn = PersianButton(
                text='انصراف',
                size_hint_x=0.4,
                background_color=(0.8, 0.2, 0.2, 1),
                color=(1,1,1,1)
            )
            btn_layout.add_widget(select_btn)
            btn_layout.add_widget(cancel_btn)
            content.add_widget(btn_layout)
            
            popup = PersianPopup(
                title='انتخاب اکسل',
                content=content,
                size_hint=(0.92, 0.8),
                auto_dismiss=False
            )
            
            def on_select(instance):
                if filechooser.selection:
                    file_path = filechooser.selection[0]
                    ext = os.path.splitext(file_path)[1].lower()
                    if ext in ['.xlsx', '.xls']:
                        popup.dismiss()
                        self._process_file(file_path)
                    else:
                        self._update_label('فقط فایل‌های اکسل مجازند', (200, 50, 50, 255))
                else:
                    self._update_label('هیچ فایلی انتخاب نشد', (200, 150, 50, 255))
            
            select_btn.bind(on_press=on_select)
            cancel_btn.bind(on_press=popup.dismiss)
            popup.open()
            
        except Exception as e:
            print(f"خطا در انتخابگر دسکتاپ: {e}")
            self._show_error(f"خطا: {str(e)}")
    
    def _process_file(self, file_path):
        """پردازش فایل انتخاب شده"""
        if not file_path or not os.path.exists(file_path):
            self._update_label('فایل وجود ندارد', (200, 50, 50, 255))
            return
        
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in ['.xlsx', '.xls']:
            self._update_label('فقط فایل‌های اکسل مجازند', (200, 50, 50, 255))
            return
        
        self.selected_file = file_path
        self._update_label(f'{os.path.basename(file_path)}', (50, 200, 50, 255))
        
        if self.on_select:
            Clock.schedule_once(lambda dt: self.on_select(file_path), 0.1)
    
    def _update_label(self, text, color):
        """به‌روزرسانی برچسب"""
        def update():
            self.file_label.set_text(text)
            self.file_label.color = tuple(
                int(c * 255) if c <= 1 else int(c) for c in color
            )
        Clock.schedule_once(lambda dt: update(), 0)
    
    def _show_error(self, message):
        """نمایش پیام خطا"""
        from kivy.uix.popup import Popup
        
        def show():
            content = BoxLayout(orientation='vertical', padding=20, spacing=10)
            content.add_widget(
                PersianLabel(
                    text=message,
                    font_size=sp(18),
                    color=(200,50,50,255),
                    size_hint_y=None,
                    height=dp(60)
                )
            )
            btn = PersianButton(
                text='باشه',
                size_hint_y=None,
                height=dp(50),
                background_color=(0.3,0.3,0.3,1),
                color=(1,1,1,1)
            )
            content.add_widget(btn)
            popup = PersianPopup(
                title='خطا',
                content=content,
                size_hint=(0.85, 0.35),
                auto_dismiss=True
            )
            btn.bind(on_press=popup.dismiss)
            popup.open()
        Clock.schedule_once(lambda dt: show(), 0)
    
    def get_file(self):
        """دریافت مسیر فایل انتخاب شده"""
        return self.selected_file
    
    def reset(self):
        """بازنشانی ویجت"""
        self.selected_file = None
        self._pending_result = False
        self._update_label('هیچ فایلی انتخاب نشده', (150, 150, 150, 255))