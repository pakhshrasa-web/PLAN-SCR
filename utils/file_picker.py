"""
ویجت انتخاب فایل - نسخه نهایی برای اندروید با Intent.ACTION_GET_CONTENT
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import dp, sp
from kivy.utils import platform
from kivy.clock import Clock
import os

from utils.persian_text import PersianLabel
from utils.rtl_widgets import PersianButton

try:
    from plyer import filechooser
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False


class FilePicker(BoxLayout):
    """ویجت انتخاب فایل - پشتیبانی از اندروید ۱۰ تا ۱۴ با Intent"""

    def __init__(self, on_select=None, file_type='excel', **kwargs):
        super().__init__(orientation='vertical', spacing=10, **kwargs)
        self.on_select = on_select
        self.selected_file = None
        self.file_type = file_type
        self.size_hint_y = None
        self.height = dp(120)
        self._pending_callback = None
        self._result_received = False
        
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
        
        # ✅ ثبت هندلر برای اندروید
        if platform == 'android':
            self._register_result_handler()
    
    def _register_result_handler(self):
        """ثبت هندلر برای نتیجه Intent در اندروید"""
        try:
            from android import mActivity
            from jnius import autoclass
            
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            
            # ذخیره callback در activity
            if not hasattr(activity, '_file_picker_callback'):
                activity._file_picker_callback = None
            
            # تنظیم callback برای این نمونه
            activity._file_picker_callback = self._on_intent_result
            
            # ثبت هندلر یکبار
            if not hasattr(activity, '_file_picker_registered'):
                from android.activity import on_activity_result
                
                @on_activity_result
                def on_activity_result(request_code, result_code, data):
                    callback = getattr(activity, '_file_picker_callback', None)
                    if callback:
                        callback(request_code, result_code, data)
                
                activity._file_picker_registered = True
                print("✅ FilePicker: هندلر Activity Result ثبت شد")
                
        except Exception as e:
            print(f"⚠️ خطا در ثبت هندلر: {e}")
    
    def pick_file(self, instance):
        """باز کردن انتخابگر فایل"""
        print(f"🔍 FilePicker.pick_file: file_type={self.file_type}, platform={platform}")
        
        if platform == 'android':
            self._pick_file_android_intent()
        else:
            self._pick_file_desktop()
    
    # ============================================================
    # ✅ اندروید - با Intent.ACTION_GET_CONTENT (بدون Permission)
    # ============================================================
    
    def _pick_file_android_intent(self):
        """انتخاب فایل در اندروید با Intent.ACTION_GET_CONTENT"""
        try:
            from android import mActivity
            from android.content import Intent
            from jnius import autoclass
            
            # تنظیم callback برای این نمونه
            activity = mActivity
            activity._file_picker_callback = self._on_intent_result
            
            # ایجاد Intent
            intent = Intent(Intent.ACTION_GET_CONTENT)
            intent.addCategory(Intent.CATEGORY_OPENABLE)
            intent.setType("*/*")
            
            # فیلتر MIME type
            if self.file_type == 'excel':
                mime_types = [
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "application/vnd.ms-excel"
                ]
            else:  # backup
                mime_types = ["application/zip"]
            
            intent.putExtra(Intent.EXTRA_MIME_TYPES, mime_types)
            
            print("📂 باز کردن انتخابگر با Intent.ACTION_GET_CONTENT")
            mActivity.startActivityForResult(intent, 1001)
            
        except Exception as e:
            print(f"❌ خطا در باز کردن انتخابگر: {e}")
            import traceback
            traceback.print_exc()
            self._show_error(f"خطا: {str(e)}")
    
    def _on_intent_result(self, request_code, result_code, data):
        """پردازش نتیجه Intent - در onActivityResult صدا زده می‌شود"""
        print(f"🔍 _on_intent_result: request={request_code}, result={result_code}")
        
        if request_code != 1001:
            return
        
        if self._result_received:
            return
        self._result_received = True
        
        from android import mActivity
        RESULT_OK = -1
        
        if result_code != RESULT_OK:
            self._update_label('⚠️ انتخاب لغو شد', (200, 150, 50, 255))
            self._result_received = False
            return
        
        if not data:
            self._update_label('⚠️ داده‌ای دریافت نشد', (200, 50, 50, 255))
            self._result_received = False
            return
        
        try:
            from android.net import Uri
            
            uri = data.getData()
            if not uri:
                self._update_label('⚠️ URI نامعتبر', (200, 50, 50, 255))
                self._result_received = False
                return
            
            print(f"📂 URI دریافت شد: {uri}")
            
            # کپی فایل از URI
            self._copy_from_saf(str(uri))
            
        except Exception as e:
            print(f"❌ خطا در پردازش نتیجه: {e}")
            import traceback
            traceback.print_exc()
            self._show_error(f"خطا: {str(e)}")
            self._result_received = False
    
    # ============================================================
    # ✅ کپی از SAF (بدون Permission)
    # ============================================================
    
    def _copy_from_saf(self, uri_str):
        """کپی فایل از SAF به پوشه برنامه (بدون نیاز به Permission)"""
        try:
            from android import mActivity
            from android.net import Uri
            from android.provider import OpenableColumns
            from utils.storage import get_app_import_path
            
            uri = Uri.parse(uri_str)
            content_resolver = mActivity.getContentResolver()
            
            # ✅ دریافت نام واقعی فایل
            filename = self._get_display_name(content_resolver, uri)
            if not filename:
                # استخراج از URI
                import urllib.parse
                raw = urllib.parse.unquote(str(uri))
                filename = raw.split('/')[-1]
                if '?' in filename:
                    filename = filename.split('?')[0]
                if not filename or '.' not in filename:
                    ext = '.xlsx' if self.file_type == 'excel' else '.zip'
                    filename = f'file_{hash(uri_str)}{ext}'
            
            # مسیر مقصد
            import_path = get_app_import_path()
            os.makedirs(import_path, exist_ok=True)
            dest_path = os.path.join(import_path, filename)
            
            print(f"📂 کپی فایل از SAF به: {dest_path}")
            
            # کپی با InputStream
            input_stream = content_resolver.openInputStream(uri)
            if not input_stream:
                raise Exception("نمی‌توان InputStream دریافت کرد")
            
            with input_stream:
                with open(dest_path, 'wb') as output_file:
                    buffer = bytearray(8192)
                    while True:
                        bytes_read = input_stream.read(buffer)
                        if bytes_read == -1:
                            break
                        output_file.write(buffer[:bytes_read])
            
            print(f"✅ فایل کپی شد: {dest_path}")
            self._result_received = False
            self._process_selection([dest_path])
            
        except Exception as e:
            print(f"❌ خطا در کپی: {e}")
            import traceback
            traceback.print_exc()
            self._result_received = False
            self._show_error(f"خطا در کپی فایل: {str(e)}")
    
    def _get_display_name(self, content_resolver, uri):
        """دریافت نام واقعی فایل از SAF با OpenableColumns"""
        try:
            from android.provider import OpenableColumns
            
            cursor = content_resolver.query(
                uri,
                [OpenableColumns.DISPLAY_NAME],
                None,
                None,
                None
            )
            
            if cursor and cursor.moveToFirst():
                name_index = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                if name_index >= 0:
                    filename = cursor.getString(name_index)
                    cursor.close()
                    return filename
            
            if cursor:
                cursor.close()
            
            return None
            
        except Exception as e:
            print(f"⚠️ خطا در دریافت نام فایل: {e}")
            return None
    
    def _validate_extension(self, file_path):
        """اعتبارسنجی پسوند فایل"""
        if not file_path:
            return False
        file_lower = file_path.lower()
        return any(file_lower.endswith(ext) for ext in self._extensions)
    
    # ============================================================
    # ✅ دسکتاپ
    # ============================================================
    
    def _pick_file_desktop(self):
        """انتخاب فایل در دسکتاپ با plyer"""
        if PLYER_AVAILABLE:
            try:
                filters = [('Excel files', '*.xlsx', '*.xls')] if self.file_type == 'excel' else [('Zip files', '*.zip')]
                filechooser.open_file(
                    on_selection=self._process_selection,
                    filters=filters
                )
                print("📂 انتخابگر دسکتاپ با plyer باز شد")
            except Exception as e:
                print(f"❌ خطا در plyer دسکتاپ: {e}")
                self._show_error(f"خطا: {str(e)}")
        else:
            self._show_error("کتابخانه انتخاب فایل در دسترس نیست")
    
    # ============================================================
    # ✅ پردازش نهایی
    # ============================================================
    
    def _process_selection(self, selection):
        """پردازش نهایی انتخاب فایل"""
        print(f"🔍 FilePicker._process_selection: {selection}")
        
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
            
            # ✅ فقط برای دسکتاپ بررسی وجود فایل
            if not file_path.startswith('content://') and not os.path.exists(file_path):
                self.selected_file = None
                self._update_label('⚠️ فایل وجود ندارد', (200, 50, 50, 255))
                self._show_error(f'فایل وجود ندارد: {os.path.basename(file_path)}')
                return
            
            # ✅ اعتبارسنجی پسوند
            if not self._validate_extension(file_path):
                self.selected_file = None
                ext_text = 'اکسل (.xlsx, .xls)' if self.file_type == 'excel' else 'زیپ (.zip)'
                self._update_label(f'❌ فقط فایل‌های {ext_text} مجازند', (200, 50, 50, 255))
                self._show_error(f'لطفاً یک فایل {ext_text} انتخاب کنید')
                return
            
            self.selected_file = file_path
            filename = os.path.basename(file_path)
            if ':' in filename:
                filename = filename.split(':')[-1]
            emoji = '📊' if self.file_type == 'excel' else '📦'
            self._update_label(f'{emoji} {filename}', (50, 200, 50, 255))
            
            print(f"🔍 FilePicker: calling on_select with {file_path}")
            if self.on_select:
                Clock.schedule_once(lambda dt: self.on_select(file_path), 0.1)
                
        except Exception as e:
            print(f"❌ FilePicker error: {e}")
            import traceback
            traceback.print_exc()
            self.selected_file = None
            self._update_label(f'⚠️ خطا', (200, 50, 50, 255))
            self._show_error(f'خطا در پردازش: {str(e)}')
    
    # ============================================================
    # ✅ توابع کمکی UI
    # ============================================================
    
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
        self._result_received = False
        self._update_label('📄 هیچ فایلی انتخاب نشده', (150, 150, 150, 255))
