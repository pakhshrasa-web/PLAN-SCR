"""
ویجت انتخاب فایل - نسخه حرفه‌ای برای اندروید با پشتیبانی از SAF
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
    """ویجت انتخاب فایل - پشتیبانی از اندروید ۱۰ تا ۱۴"""
    
    def __init__(self, on_select=None, file_type='excel', **kwargs):
        super().__init__(orientation='vertical', spacing=10, **kwargs)
        self.on_select = on_select
        self.selected_file = None
        self.file_type = file_type
        self.size_hint_y = None
        self.height = dp(120)
        self._pending_uri = None  # برای مدیریت غیرهمزمان
        
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
    
    # ============================================================
    # ✅ اندروید - استفاده از plyer با SAF
    # ============================================================
    
    def _pick_file_android(self):
        """انتخاب فایل در اندروید با plyer و SAF"""
        if not PLYER_AVAILABLE:
            self._show_error("خطا: plyer در دسترس نیست!")
            return
        
        try:
            # تنظیم فیلتر (فقط برای نمایش، اعتبارسنجی نهایی دستی انجام میشه)
            if self.file_type == 'excel':
                filters = [('Excel files', '*.xlsx', '*.xls')]
                title = 'انتخاب فایل اکسل'
            else:
                filters = [('Zip files', '*.zip')]
                title = 'انتخاب فایل بکاپ'
            
            print(f"📂 باز کردن انتخابگر با plyer")
            
            filechooser.open_file(
                on_selection=self._on_plyer_selection,
                filters=filters,
                title=title
            )
            
        except Exception as e:
            print(f"❌ خطا در plyer: {e}")
            import traceback
            traceback.print_exc()
            self._show_error(f"خطا: {str(e)}")
    
    def _on_plyer_selection(self, selection):
        """پردازش نتیجه انتخاب از plyer"""
        print(f"🔍 _on_plyer_selection: {selection}")
        
        if not selection or len(selection) == 0:
            self._update_label('⚠️ انتخاب لغو شد', (200, 150, 50, 255))
            return
        
        file_uri = selection[0]
        print(f"📂 فایل انتخاب شد: {file_uri}")
        
        if not file_uri:
            self._update_label('⚠️ مسیر نامعتبر', (200, 50, 50, 255))
            return
        
        # ✅ ذخیره URI برای پردازش بعد از دریافت permission
        self._pending_uri = file_uri
        
        # ✅ دریافت نام واقعی فایل
        real_filename = self._get_filename_from_uri(file_uri)
        print(f"📄 نام واقعی فایل: {real_filename}")
        
        # ✅ اعتبارسنجی پسوند (حتی اگر فیلتر درست کار نکرده باشه)
        if not self._validate_extension(real_filename):
            ext_text = 'اکسل (.xlsx, .xls)' if self.file_type == 'excel' else 'زیپ (.zip)'
            self._update_label(f'⚠️ فقط فایل‌های {ext_text} مجازند', (200, 50, 50, 255))
            self._show_error(f'لطفاً یک فایل {ext_text} انتخاب کنید')
            return
        
        # ✅ پردازش فایل
        self._handle_android_uri(file_uri, real_filename)
    
    # ============================================================
    # ✅ توابع کمکی برای اندروید
    # ============================================================
    
    def _get_filename_from_uri(self, uri):
        """دریافت نام واقعی فایل از URI با استفاده از ContentResolver"""
        try:
            from android import mActivity
            from android.content import ContentUris
            from android.net import Uri
            from android.provider import DocumentsContract, MediaStore
            from android.database import Cursor
            
            # روش ۱: اگر URI از نوع DocumentsContract است
            if DocumentsContract.isDocumentUri(mActivity, uri):
                doc_id = DocumentsContract.getDocumentId(uri)
                if doc_id and ':' in doc_id:
                    doc_id = doc_id.split(':')[-1]
                
                # دریافت نام فایل از MediaStore
                projection = [MediaStore.MediaColumns.DISPLAY_NAME]
                
                try:
                    cursor = mActivity.getContentResolver().query(
                        uri,
                        projection,
                        None,
                        None,
                        None
                    )
                    if cursor and cursor.moveToFirst():
                        filename = cursor.getString(0)
                        cursor.close()
                        if filename:
                            return filename
                except Exception as e:
                    print(f"⚠️ خطا در دریافت نام فایل از MediaStore: {e}")
            
            # روش ۲: استخراج از خود URI
            if '%' in str(uri):
                from urllib.parse import unquote
                return unquote(str(uri).split('/')[-1].split('?')[0])
            
            return str(uri).split('/')[-1].split('?')[0]
            
        except Exception as e:
            print(f"⚠️ خطا در دریافت نام فایل: {e}")
            # Fallback
            return uri.split('/')[-1]
    
    def _get_real_path_from_uri(self, uri):
        """دریافت مسیر واقعی فایل از URI (برای اندروید ۱۰-)
        این تابع برای اندروید ۱۱+ کار نمی‌کند، برای آن از کپی استفاده می‌کنیم
        """
        try:
            from android import mActivity
            from android.provider import MediaStore
            
            # فقط برای اندروید ۱۰ و پایین‌تر
            projection = [MediaStore.MediaColumns.DATA]
            
            cursor = mActivity.getContentResolver().query(
                uri,
                projection,
                None,
                None,
                None
            )
            
            if cursor and cursor.moveToFirst():
                path = cursor.getString(0)
                cursor.close()
                if path and os.path.exists(path):
                    return path
            
            return None
            
        except Exception as e:
            print(f"⚠️ خطا در دریافت مسیر واقعی: {e}")
            return None
    
    def _copy_uri_to_app_folder(self, uri, filename):
        """کپی فایل از URI به پوشه شخصی برنامه با استفاده از ContentResolver"""
        try:
            from android import mActivity
            from utils.storage import get_import_path
            
            # ✅ دریافت پوشه import
            import_path = get_import_path()
            os.makedirs(import_path, exist_ok=True)
            
            # ✅ مسیر مقصد
            dest_path = os.path.join(import_path, filename)
            
            print(f"📂 کپی فایل از {uri} به {dest_path}")
            
            # ✅ استفاده از ContentResolver برای خواندن URI
            content_resolver = mActivity.getContentResolver()
            
            # باز کردن InputStream از URI
            input_stream = content_resolver.openInputStream(uri)
            
            if not input_stream:
                raise Exception("نمی‌توان InputStream از URI دریافت کرد")
            
            # خواندن و نوشتن فایل
            with input_stream:
                with open(dest_path, 'wb') as output_file:
                    # بافر 8KB برای کپی سریع
                    buffer = bytearray(8192)
                    while True:
                        bytes_read = input_stream.read(buffer)
                        if bytes_read == -1:
                            break
                        output_file.write(buffer[:bytes_read])
            
            print(f"✅ فایل با موفقیت کپی شد: {dest_path}")
            return dest_path
            
        except Exception as e:
            print(f"❌ خطا در کپی فایل: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _handle_android_uri(self, uri, filename):
        """مدیریت کامل URI در اندروید"""
        try:
            from android.permissions import request_permissions, Permission
            
            # ✅ مرحله ۱: درخواست دسترسی
            print("📱 درخواست دسترسی...")
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE
            ])
            
            # ✅ مرحله ۲: تلاش برای دریافت مسیر واقعی (برای اندروید ۱۰-)
            real_path = self._get_real_path_from_uri(uri)
            if real_path and os.path.exists(real_path):
                print(f"✅ مسیر واقعی دریافت شد: {real_path}")
                self._process_selection([real_path])
                return
            
            # ✅ مرحله ۳: کپی فایل به پوشه شخصی برنامه (برای اندروید ۱۱+)
            print("📂 کپی فایل به پوشه شخصی برنامه...")
            dest_path = self._copy_uri_to_app_folder(uri, filename)
            
            if dest_path and os.path.exists(dest_path):
                print(f"✅ فایل با موفقیت کپی شد: {dest_path}")
                self._process_selection([dest_path])
            else:
                # اگر کپی موفق نشد، خطا نمایش بده
                self._show_error("خطا در کپی فایل! لطفاً فایل را به پوشه import کپی کنید.")
            
        except Exception as e:
            print(f"❌ خطا در مدیریت URI: {e}")
            import traceback
            traceback.print_exc()
            self._show_error(f"خطا: {str(e)}")
    
    def _validate_extension(self, filename):
        """اعتبارسنجی پسوند فایل"""
        if not filename:
            return False
        filename_lower = filename.lower()
        return any(filename_lower.endswith(ext) for ext in self._extensions)
    
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
    # ✅ پردازش نهایی انتخاب
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
            
            # ✅ بررسی وجود فایل (فقط برای مسیرهای معمولی)
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
        self._pending_uri = None
        self._update_label('📄 هیچ فایلی انتخاب نشده', (150, 150, 150, 255))
