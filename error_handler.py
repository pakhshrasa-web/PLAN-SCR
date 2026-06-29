# error_handler.py
# ========== سیستم نمایش خطا ==========

import os
import sys
import traceback
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView


class ErrorPopup:
    """نمایش خطا به صورت پنجره بازشو با قابلیت کپی متن"""
    
    @staticmethod
    def show_error(error_message, error_details=""):
        try:
            from utils.rtl_widgets import RTLLabel, PersianButton
            
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            
            title_label = RTLLabel(
                text="[b][color=ff3333]⚠️ خطا در برنامه[/color][/b]",
                markup=True,
                size_hint_y=None,
                height=dp(50),
                font_size=sp(18)
            )
            content.add_widget(title_label)
            
            msg_label = RTLLabel(
                text=f"[b]خطا:[/b] {error_message}",
                markup=True,
                size_hint_y=None,
                height=dp(60),
                text_size=(dp(400), None),
                halign='left'
            )
            content.add_widget(msg_label)
            
            if error_details:
                detail_label = RTLLabel(
                    text=f"[b]جزئیات:[/b]\n{error_details}",
                    markup=True,
                    size_hint_y=None,
                    height=dp(300),
                    text_size=(dp(400), None),
                    halign='left',
                    font_size=sp(12)
                )
                scroll = ScrollView(size_hint_y=None, height=dp(300))
                scroll.add_widget(detail_label)
                content.add_widget(scroll)
            else:
                content.add_widget(RTLLabel(
                    text="",
                    size_hint_y=None,
                    height=dp(20)
                ))
            
            btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
            copy_btn = PersianButton(text='📋 کپی متن خطا', background_color=(0.2, 0.4, 0.8, 1), size_hint_y=None, height=dp(45))
            close_btn = PersianButton(text='✖ بستن', background_color=(0.8, 0.2, 0.2, 1), size_hint_y=None, height=dp(45))
            
            btn_layout.add_widget(copy_btn)
            btn_layout.add_widget(close_btn)
            content.add_widget(btn_layout)
            
            popup = Popup(title='⚠️ گزارش خطا', 
                          content=content, 
                          size_hint=(0.92, 0.75),
                          auto_dismiss=False)
            
            def copy_error(instance):
                full_text = f"خطا: {error_message}\n\nجزئیات:\n{error_details}"
                try:
                    from kivy.core.clipboard import Clipboard
                    Clipboard.copy(full_text)
                    copy_btn.text = '✅ کپی شد!'
                    Clock.schedule_once(lambda dt: setattr(copy_btn, 'text', '📋 کپی متن خطا'), 2)
                except:
                    copy_btn.text = '⚠️ دستی کپی کن'
            
            def close_popup(instance):
                popup.dismiss()
            
            copy_btn.bind(on_press=copy_error)
            close_btn.bind(on_press=close_popup)
            
            popup.open()
            
            print("="*60)
            print(f"❌ خطا: {error_message}")
            print(f"📋 جزئیات:\n{error_details}")
            print("="*60)
            
            try:
                from utils.storage import get_data_path
                data_path = get_data_path()
                log_dir = os.path.join(data_path, 'logs')
                os.makedirs(log_dir, exist_ok=True)
                log_file = os.path.join(log_dir, 'crash_report.txt')
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write(f"خطا: {error_message}\n\n")
                    f.write(f"جزئیات:\n{error_details}\n")
                    f.write("="*60 + "\n")
            except:
                try:
                    with open('/sdcard/planandroid_error.txt', 'w', encoding='utf-8') as f:
                        f.write(f"خطا: {error_message}\n\n")
                        f.write(f"جزئیات:\n{error_details}\n")
                except:
                    pass
                    
        except Exception as e:
            print(f"❌ خطا در نمایش پاپ‌آپ: {e}")


def global_exception_handler(exc_type, exc_value, exc_tb):
    error_msg = str(exc_value)
    error_details = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    ErrorPopup.show_error(error_msg, error_details)


sys.excepthook = global_exception_handler


def exception_handler(exc_type, exc_value, exc_tb):
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    
    paths = [
        '/storage/emulated/0/planandroid_crash.txt',
        '/sdcard/planandroid_crash.txt',
        '/data/data/org.pakhshrasa.planandroid/files/crash.txt',
    ]
    
    for path in paths:
        try:
            dir_path = os.path.dirname(path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write("="*60 + "\n")
                f.write("❌ CRASH ERROR:\n")
                f.write("="*60 + "\n")
                f.write(error_msg)
                f.write("="*60 + "\n")
            print(f"✅ Crash log saved to: {path}")
            break
        except Exception as e:
            print(f"Could not write to {path}: {e}")
            continue
    
    print("="*60)
    print("❌ CRASH ERROR:")
    print(error_msg)
    print("="*60)