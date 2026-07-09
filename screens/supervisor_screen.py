# screens/supervisor_screen.py
# ========== صفحه سوپروایزر ==========

import traceback
import os
from datetime import datetime
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox

from utils.rtl_widgets import (
    RTLTextInput, PersianComboBox, PersianButton,
    RTLLabel, PersianPopup, RTLMessageLabel
)
from utils.file_manager import get_agents, get_routes, get_customers, get_settings
from utils.jalali_date import get_today_jalali, get_current_time, validate_jalali_date
from utils.target_manager import (
    create_target,
    get_all_targets,
    get_targets_filtered,
    get_target_statistics,
    update_target,
    delete_target,
    can_edit_target,
    export_targets_to_excel,
    get_active_targets_by_agent,
    finalize_targets,
    read_excel_summary
)
from constants import TARGET_TYPES, TARGET_STATUSES, TARGET_EXCEL_MAPPING, PERIOD_DISPLAY, PERIOD_MAPPING
from error_handler import ErrorPopup


class SupervisorScreen(Screen):
    """صفحه سوپروایزر - ترکیبی از امکانات ایجنت و ادمین"""

    def __init__(self, **kwargs):
        try:
            super().__init__(**kwargs)
            with self.canvas.before:
                Color(0.08, 0.08, 0.08, 1)
                self.bg_rect = Rectangle(pos=self.pos, size=self.size)
                self.bind(pos=self._update_bg, size=self._update_bg)

            Window.softinput_mode = 'resize'
            self.focusable_fields = []
            self.tab_buttons = []
            self.current_tab = 0
            self.fulfillment_selected = {}

            self.build_ui()

        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت SupervisorScreen: {e}", error_details)
            raise

    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def _on_field_focus(self, instance, value):
        if value:
            Clock.schedule_once(lambda dt: self._select_all_text(instance), 0.1)
            Clock.schedule_once(lambda dt: self._scroll_to_field(instance), 0.3)

    def _select_all_text(self, instance):
        if instance and hasattr(instance, 'select_all'):
            instance.select_all()

    def _scroll_to_field(self, instance):
        try:
            scroll = None
            for child in self.content_area.children:
                if isinstance(child, ScrollView):
                    scroll = child
                    break

            if not scroll:
                return

            field_pos = instance.to_window(0, 0)
            field_y = field_pos[1]
            keyboard_height = 250
            window_height = Window.height
            target_y = window_height - keyboard_height - dp(80)

            content_height = scroll.children[0].height if scroll.children else 1
            scroll_height = scroll.height

            if content_height > scroll_height:
                if field_y > target_y:
                    field_ratio = (content_height - field_y) / content_height
                    scroll_value = min(0.95, max(0.05, field_ratio + 0.1))
                    scroll.scroll_y = scroll_value
                elif field_y < dp(50):
                    scroll.scroll_y = 0.9

        except Exception as e:
            print(f"خطا در اسکرول: {e}")

    def build_ui(self):
        try:
            layout = BoxLayout(orientation='vertical', padding=[dp(5), dp(5), dp(5), dp(5)])

            # ========== تب‌ها ==========
            tabs_layout = BoxLayout(
                size_hint_y=None,
                height=dp(40),
                spacing=dp(2)
            )

            tab_names = [
                ('هدفگذاری', 0),
                ('تحقق تارگت', 1),
                ('بررسی بازار', 2),
                ('گزارشات', 3)
            ]

            for name, tab_id in tab_names:
                btn = PersianButton(
                    text=name,
                    background_color=(0.3, 0.5, 0.8, 0.6),
                    size_hint_y=None,
                    height=dp(36),
                    color=(1, 1, 1, 1),
                    font_size=sp(16)
                )
                btn.bind(on_press=lambda x, tid=tab_id: self.switch_tab(tid))
                tabs_layout.add_widget(btn)
                self.tab_buttons.append(btn)

            layout.add_widget(tabs_layout)

            self.content_area = BoxLayout(orientation='vertical')
            layout.add_widget(self.content_area)

            # ========== دکمه بازگشت ==========
            back_btn = PersianButton(
                text='بازگشت',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(36),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            back_btn.bind(on_press=self.go_back)
            layout.add_widget(back_btn)

            self.add_widget(layout)

            # نمایش تب پیش‌فرض
            Clock.schedule_once(lambda dt: self.switch_tab(0), 0.1)

        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ساخت UI SupervisorScreen: {e}", error_details)
            raise

    def switch_tab(self, tab_id):
        try:
            self.current_tab = tab_id

            for i, btn in enumerate(self.tab_buttons):
                btn.background_color = (0.3, 0.5, 0.8, 1) if i == tab_id else (0.3, 0.5, 0.8, 0.6)

            self.content_area.clear_widgets()
            self.focusable_fields = []

            if tab_id == 0:
                self.show_targeting_tab()
            elif tab_id == 1:
                self.show_fulfillment_tab()
            elif tab_id == 2:
                self.show_market_check_tab()
            elif tab_id == 3:
                self.show_reports_tab()

        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در تغییر تب: {e}", error_details)

    # ============================================================
    # تب ۱: هدفگذاری
    # ============================================================

    def show_targeting_tab(self):
        try:
            scroll = ScrollView(
                do_scroll_x=False,
                do_scroll_y=True,
                size_hint=(1, 1),
                scroll_type=['bars', 'content'],
                bar_width=dp(8)
            )

            content = GridLayout(
                cols=1,
                spacing=dp(10),
                size_hint_y=None,
                padding=dp(12)
            )
            content.bind(minimum_height=content.setter('height'))

            # عنوان
            content.add_widget(RTLLabel(
                text='ثبت تارگت جدید',
                size_hint_y=None,
                height=dp(50),
                font_size=sp(22),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))

            # ========== ۱- کامبوباکس عاملین ==========
            content.add_widget(RTLLabel(
                text='انتخاب عامل:',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(18),
                color=(1, 1, 1, 1)
            ))

            agents = get_agents()
            agent_names = [a.get('name', '') for a in agents] if agents else ['']

            self.agent_spinner = PersianComboBox(
                text=agent_names[0] if agent_names else '',
                values=agent_names,
                height=dp(75)
            )
            self.agent_spinner.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.agent_spinner.main_btn.color = (1, 1, 1, 1)
            self.agent_spinner.main_btn.font_size = sp(22)
            content.add_widget(self.agent_spinner)

            # ========== ۲- کامبوباکس نوع تارگت ==========
            content.add_widget(RTLLabel(
                text='نوع تارگت:',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(18),
                color=(1, 1, 1, 1)
            ))

            self.target_type_spinner = PersianComboBox(
                text=TARGET_TYPES[0],
                values=TARGET_TYPES,
                height=dp(75)
            )
            self.target_type_spinner.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.target_type_spinner.main_btn.color = (1, 1, 1, 1)
            self.target_type_spinner.main_btn.font_size = sp(22)
            content.add_widget(self.target_type_spinner)

            # ========== ۳- میزان هدف ==========
            content.add_widget(RTLLabel(
                text='میزان هدف:',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(18),
                color=(1, 1, 1, 1)
            ))

            self.target_value_input = RTLTextInput(
                hint_text='مقدار عددی را وارد کنید',
                multiline=False,
                size_hint_y=None,
                height=dp(80),
                input_filter='int',
                font_size=sp(28)
            )
            self.target_value_input.bg_color = (0.15, 0.15, 0.15, 1)
            self.target_value_input.border_color = (0.3, 0.3, 0.3, 1)
            self.target_value_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.target_value_input._hidden_input.foreground_color = (1, 1, 1, 1)
            self.target_value_input._hidden_input.bind(focus=self._on_field_focus)
            self.focusable_fields.append(self.target_value_input._hidden_input)
            content.add_widget(self.target_value_input)

            # ========== ۴- کامبوباکس دوره ==========
            content.add_widget(RTLLabel(
                text='دوره:',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(18),
                color=(1, 1, 1, 1)
            ))

            self.period_spinner = PersianComboBox(
                text=PERIOD_DISPLAY[0],
                values=PERIOD_DISPLAY,
                height=dp(75)
            )
            self.period_spinner.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.period_spinner.main_btn.color = (1, 1, 1, 1)
            self.period_spinner.main_btn.font_size = sp(22)
            content.add_widget(self.period_spinner)

            # ========== ۵- مدت تارگت ==========
            content.add_widget(RTLLabel(
                text='مدت تارگت:',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(18),
                color=(1, 1, 1, 1)
            ))

            self.duration_input = RTLTextInput(
                text='1',
                multiline=False,
                size_hint_y=None,
                height=dp(80),
                input_filter='int',
                font_size=sp(28)
            )
            self.duration_input.bg_color = (0.15, 0.15, 0.15, 1)
            self.duration_input.border_color = (0.3, 0.3, 0.3, 1)
            self.duration_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.duration_input._hidden_input.foreground_color = (1, 1, 1, 1)
            self.duration_input._hidden_input.bind(focus=self._on_field_focus)
            self.focusable_fields.append(self.duration_input._hidden_input)
            content.add_widget(self.duration_input)

            # ========== ۶- تاریخ شروع ==========
            content.add_widget(RTLLabel(
                text='تاریخ شروع (سال/ماه/روز):',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(18),
                color=(1, 1, 1, 1)
            ))

            self.start_date_input = RTLTextInput(
                text=get_today_jalali(),
                multiline=False,
                size_hint_y=None,
                height=dp(80),
                font_size=sp(28)
            )
            self.start_date_input.bg_color = (0.15, 0.15, 0.15, 1)
            self.start_date_input.border_color = (0.3, 0.3, 0.3, 1)
            self.start_date_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.start_date_input._hidden_input.foreground_color = (1, 1, 1, 1)
            self.start_date_input._hidden_input.bind(focus=self._on_field_focus)
            self.focusable_fields.append(self.start_date_input._hidden_input)
            content.add_widget(self.start_date_input)

            # ========== ۷- توضیحات ==========
            content.add_widget(RTLLabel(
                text='توضیحات:',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(18),
                color=(1, 1, 1, 1)
            ))

            self.description_input = RTLTextInput(
                hint_text='توضیحات (اختیاری)',
                multiline=False,
                size_hint_y=None,
                height=dp(80),
                font_size=sp(24)
            )
            self.description_input.bg_color = (0.15, 0.15, 0.15, 1)
            self.description_input.border_color = (0.3, 0.3, 0.3, 1)
            self.description_input.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.description_input._hidden_input.foreground_color = (1, 1, 1, 1)
            self.description_input._hidden_input.bind(focus=self._on_field_focus)
            self.focusable_fields.append(self.description_input._hidden_input)
            content.add_widget(self.description_input)

            # ========== ۸- دکمه ثبت تارگت ==========
            btn_layout = BoxLayout(size_hint_y=None, height=dp(65), spacing=dp(10))

            submit_btn = PersianButton(
                text='ثبت تارگت',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(58),
                color=(1, 1, 1, 1),
                font_size=sp(20)
            )
            submit_btn.bind(on_press=self.submit_target)
            btn_layout.add_widget(submit_btn)

            # ========== دکمه نمایش لیست تارگت‌ها ==========
            list_btn = PersianButton(
                text='نمایش لیست تارگت‌ها',
                background_color=(0.2, 0.5, 0.8, 1),
                size_hint_y=None,
                height=dp(58),
                color=(1, 1, 1, 1),
                font_size=sp(20)
            )
            list_btn.bind(on_press=self.show_targets_list)
            btn_layout.add_widget(list_btn)

            content.add_widget(btn_layout)

            scroll.add_widget(content)
            self.content_area.add_widget(scroll)

        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش تب هدفگذاری: {e}", error_details)

    def submit_target(self, instance):
        """ثبت تارگت جدید"""
        try:
            agent_name = self.agent_spinner.text
            target_type = self.target_type_spinner.text
            target_value = self.target_value_input.text.strip()
            period_display = self.period_spinner.text
            duration = self.duration_input.text.strip()
            start_date = self.start_date_input.text.strip()
            description = self.description_input.text.strip()

            # اعتبارسنجی
            if not agent_name or agent_name == '':
                self.show_message('خطا', 'لطفاً یک عامل را انتخاب کنید')
                return

            if not target_value:
                self.show_message('خطا', 'لطفاً میزان هدف را وارد کنید')
                return

            try:
                target_value_int = int(target_value)
                if target_value_int <= 0:
                    self.show_message('خطا', 'میزان هدف باید بزرگتر از صفر باشد')
                    return
            except ValueError:
                self.show_message('خطا', 'میزان هدف باید عددی باشد')
                return

            if not duration:
                self.show_message('خطا', 'لطفاً مدت تارگت را وارد کنید')
                return

            try:
                duration_int = int(duration)
                if duration_int <= 0:
                    self.show_message('خطا', 'مدت تارگت باید بزرگتر از صفر باشد')
                    return
            except ValueError:
                self.show_message('خطا', 'مدت تارگت باید عددی باشد')
                return

            if not start_date:
                self.show_message('خطا', 'لطفاً تاریخ شروع را وارد کنید')
                return

            # اعتبارسنجی تاریخ با فرمت سال/ماه/روز
            if not validate_jalali_date(start_date):
                self.show_message('خطا', 'فرمت تاریخ باید سال/ماه/روز باشد (مثال: 1405/01/31)')
                return

            # دریافت مقدار period_type از نگاشت
            period_type = PERIOD_MAPPING.get(period_display, 'daily')

            # ایجاد تارگت
            success, message, target = create_target(
                agent_name=agent_name,
                target_type=target_type,
                target_value=target_value_int,
                period_type=period_type,
                duration=duration_int,
                start_date=start_date,
                description=description,
                created_by='supervisor'
            )

            if success:
                self.target_value_input.text = ''
                self.duration_input.text = '1'
                self.start_date_input.text = get_today_jalali()
                self.description_input.text = ''
                self.show_message('موفق', message)
            else:
                self.show_message('خطا', message)

        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ثبت تارگت: {e}", error_details)

    # ============================================================
    # دیالوگ نمایش لیست تارگت‌ها با فیلتر
    # ============================================================

    def show_targets_list(self, instance):
        """نمایش لیست تارگت‌ها با دیالوگ فیلتردار"""
        try:
            content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
            with content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                           size=lambda i, v: setattr(content_rect, 'size', v))


            # ========== فیلترها ==========
            filter_layout = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(200))
            filter_layout.bind(minimum_height=filter_layout.setter('height'))

            # فیلتر عامل
            filter_layout.add_widget(RTLLabel(
                text='عامل:',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))

            agents = get_agents()
            agent_names = ['همه'] + [a.get('name', '') for a in agents] if agents else ['همه']
            self.filter_agent = PersianComboBox(
                text='همه',
                values=agent_names,
                height=dp(65)
            )
            self.filter_agent.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.filter_agent.main_btn.color = (1, 1, 1, 1)
            self.filter_agent.main_btn.font_size = sp(18)
            filter_layout.add_widget(self.filter_agent)

            # فیلتر نوع تارگت
            filter_layout.add_widget(RTLLabel(
                text='نوع تارگت:',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))

            self.filter_type = PersianComboBox(
                text='همه',
                values=['همه'] + TARGET_TYPES,
                height=dp(65)
            )
            self.filter_type.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.filter_type.main_btn.color = (1, 1, 1, 1)
            self.filter_type.main_btn.font_size = sp(18)
            filter_layout.add_widget(self.filter_type)

            # فیلتر وضعیت
            filter_layout.add_widget(RTLLabel(
                text='وضعیت:',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))

            self.filter_status = PersianComboBox(
                text='همه',
                values=['همه'] + TARGET_STATUSES,
                height=dp(65)
            )
            self.filter_status.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.filter_status.main_btn.color = (1, 1, 1, 1)
            self.filter_status.main_btn.font_size = sp(18)
            filter_layout.add_widget(self.filter_status)

            content.add_widget(filter_layout)

            # ========== دکمه‌های فیلتر و خروجی ==========
            btn_filter_layout = BoxLayout(size_hint_y=None, height=dp(55), spacing=dp(10))

            apply_btn = PersianButton(
                text='اعمال فیلتر',
                background_color=(0.2, 0.6, 1, 1),
                size_hint_x=0.5,
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            apply_btn.bind(on_press=self.apply_filter)
            btn_filter_layout.add_widget(apply_btn)

            export_btn = PersianButton(
                text='خروجی اکسل',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_x=0.5,
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            export_btn.bind(on_press=self.export_filtered_targets)
            btn_filter_layout.add_widget(export_btn)

            content.add_widget(btn_filter_layout)

            # ========== لیست تارگت‌ها ==========
            scroll = ScrollView(
                do_scroll_x=False,
                do_scroll_y=True,
                size_hint_y=0.5
            )

            self.list_content = GridLayout(
                cols=1,
                spacing=dp(6),
                size_hint_y=None,
                padding=dp(5)
            )
            self.list_content.bind(minimum_height=self.list_content.setter('height'))

            # بارگذاری اولیه
            targets = get_all_targets()
            self._populate_targets_list(self.list_content, targets)

            scroll.add_widget(self.list_content)
            content.add_widget(scroll)

            # ========== دکمه بستن ==========
            close_btn = PersianButton(
                text='بستن',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            content.add_widget(close_btn)

            self.targets_popup = PersianPopup(
                title='لیست تارگت‌ها',
                content=content,
                size_hint=(0.92, 0.88),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )

            close_btn.bind(on_press=self.targets_popup.dismiss)
            self.targets_popup.open()

        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش لیست تارگت‌ها: {e}", error_details)

    def apply_filter(self, instance):
        """اعمال فیلتر روی لیست تارگت‌ها"""
        try:
            agent = self.filter_agent.text
            target_type = self.filter_type.text
            status = self.filter_status.text

            filtered = get_targets_filtered(
                agent_name=agent if agent != 'همه' else None,
                target_type=target_type if target_type != 'همه' else None,
                status=status if status != 'همه' else None
            )

            self.list_content.clear_widgets()
            self._populate_targets_list(self.list_content, filtered)

        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در اعمال فیلتر: {e}", error_details)

    def export_filtered_targets(self, instance):
        """خروجی گرفتن از تارگت‌های فیلتر شده"""
        try:
            agent = self.filter_agent.text
            target_type = self.filter_type.text
            status = self.filter_status.text

            filtered = get_targets_filtered(
                agent_name=agent if agent != 'همه' else None,
                target_type=target_type if target_type != 'همه' else None,
                status=status if status != 'همه' else None
            )

            if not filtered:
                self.show_message('خطا', 'هیچ تارگتی برای خروجی وجود ندارد')
                return

            success, message, filepath = export_targets_to_excel(filtered)

            if success:
                self.show_message('موفق', message)
            else:
                self.show_message('خطا', message)

        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در خروجی اکسل: {e}", error_details)

    def _populate_targets_list(self, list_content, targets):
        """پر کردن لیست تارگت‌ها با دکمه‌های ویرایش و حذف"""
        try:
            if not targets:
                list_content.add_widget(RTLLabel(
                    text='هیچ تارگتی یافت نشد',
                    size_hint_y=None,
                    height=dp(45),
                    font_size=sp(18),
                    color=(0.5, 0.5, 0.5, 1)
                ))
                return

            for target in targets:
                # رنگ‌بندی بر اساس وضعیت
                status = target.get('status', '')
                if status == 'تکمیل شده':
                    bg_color = (0.2, 0.6, 0.2, 0.3)
                elif status == 'فعال':
                    bg_color = (0.2, 0.5, 0.8, 0.3)
                elif status == 'لغو شده':
                    bg_color = (0.8, 0.2, 0.2, 0.3)
                else:  # در انتظار
                    bg_color = (0.8, 0.6, 0.2, 0.3)

                box = BoxLayout(
                    orientation='vertical',
                    size_hint_y=None,
                    height=dp(130),
                    spacing=dp(3),
                    padding=[dp(8), dp(6), dp(8), dp(6)]
                )

                with box.canvas.before:
                    Color(*bg_color)
                    rect = Rectangle(pos=box.pos, size=box.size)
                    box.bind(pos=lambda i, v: setattr(rect, 'pos', v),
                           size=lambda i, v: setattr(rect, 'size', v))

                # ردیف اول: شناسه و وضعیت
                row1 = BoxLayout(size_hint_y=None, height=dp(30))
                row1.add_widget(RTLLabel(
                    text=f"{target.get('target_id', '')} | {target.get('agent_name', '')}",
                    size_hint_x=0.6,
                    font_size=sp(16),
                    color=(1, 1, 1, 1)
                ))
                row1.add_widget(RTLLabel(
                    text=status,
                    size_hint_x=0.4,
                    font_size=sp(16),
                    color=(1, 1, 1, 1),
                    halign='right'
                ))
                box.add_widget(row1)

                # ردیف دوم: جزئیات
                row2 = BoxLayout(size_hint_y=None, height=dp(30))
                row2.add_widget(RTLLabel(
                    text=f"{target.get('target_type', '')}: {target.get('target_value', 0):,}",
                    size_hint_x=0.5,
                    font_size=sp(15),
                    color=(0.8, 0.8, 0.8, 1)
                ))
                row2.add_widget(RTLLabel(
                    text=f"{target.get('start_date', '')} -> {target.get('end_date', '')}",
                    size_hint_x=0.5,
                    font_size=sp(15),
                    color=(0.8, 0.8, 0.8, 1),
                    halign='right'
                ))
                box.add_widget(row2)

                # ردیف سوم: مقدار محقق شده
                row3 = BoxLayout(size_hint_y=None, height=dp(25))
                achieved = target.get('achieved_value', 0)
                if achieved > 0:
                    row3.add_widget(RTLLabel(
                        text=f"محقق شده: {achieved:,}",
                        size_hint_x=1,
                        font_size=sp(14),
                        color=(0.2, 0.8, 0.2, 1)
                    ))
                else:
                    row3.add_widget(RTLLabel(
                        text="محقق شده: ۰",
                        size_hint_x=1,
                        font_size=sp(14),
                        color=(0.5, 0.5, 0.5, 1)
                    ))
                box.add_widget(row3)

                # ردیف چهارم: دکمه‌ها
                row4 = BoxLayout(size_hint_y=None, height=dp(35), spacing=dp(5))

                # دکمه ویرایش (فقط اگر قابل ویرایش باشد)
                if can_edit_target(target):
                    edit_btn = PersianButton(
                        text='ویرایش',
                        size_hint_x=0.33,
                        size_hint_y=None,
                        height=dp(30),
                        background_color=(0.8, 0.6, 0.2, 1),
                        color=(1, 1, 1, 1),
                        font_size=sp(13)
                    )
                    edit_btn.bind(on_press=lambda x, t=target: self._edit_target(t))
                    row4.add_widget(edit_btn)
                else:
                    edit_btn = PersianButton(
                        text='ویرایش',
                        size_hint_x=0.33,
                        size_hint_y=None,
                        height=dp(30),
                        background_color=(0.3, 0.3, 0.3, 1),
                        color=(0.5, 0.5, 0.5, 1),
                        font_size=sp(13),
                        disabled=True
                    )
                    row4.add_widget(edit_btn)

                # دکمه حذف (فقط اگر نهایی نشده باشد)
                if status != 'تکمیل شده':
                    delete_btn = PersianButton(
                        text='حذف',
                        size_hint_x=0.33,
                        size_hint_y=None,
                        height=dp(30),
                        background_color=(0.8, 0.2, 0.2, 1),
                        color=(1, 1, 1, 1),
                        font_size=sp(13)
                    )
                    delete_btn.bind(on_press=lambda x, t=target: self._delete_target(t))
                    row4.add_widget(delete_btn)
                else:
                    delete_btn = PersianButton(
                        text='حذف',
                        size_hint_x=0.33,
                        size_hint_y=None,
                        height=dp(30),
                        background_color=(0.3, 0.3, 0.3, 1),
                        color=(0.5, 0.5, 0.5, 1),
                        font_size=sp(13),
                        disabled=True
                    )
                    row4.add_widget(delete_btn)

                # دکمه خالی برای تعادل
                row4.add_widget(Label(size_hint_x=0.34))

                box.add_widget(row4)

                list_content.add_widget(box)

        except Exception as e:
            print(f"خطا در پر کردن لیست تارگت‌ها: {e}")

    def _edit_target(self, target):
        """نمایش دیالوگ ویرایش تارگت"""
        try:
            from constants import TARGET_TYPES, TARGET_STATUSES

            if not can_edit_target(target):
                self.show_message('خطا', 'این تارگت قابل ویرایش نیست')
                return

            content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(8))
            with content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                           size=lambda i, v: setattr(content_rect, 'size', v))

            content.add_widget(RTLLabel(
                text=f'ویرایش تارگت - {target.get("target_id", "")}',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(18),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))

            # نوع تارگت
            content.add_widget(RTLLabel(
                text='نوع تارگت:',
                size_hint_y=None,
                height=dp(25),
                font_size=sp(24),
                color=(1, 1, 1, 1)
            ))
            edit_type = PersianComboBox(
                text=target.get('target_type', ''),
                values=TARGET_TYPES,
                height=dp(55)
            )
            edit_type.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            edit_type.main_btn.color = (1, 1, 1, 1)
            edit_type.main_btn.font_size = sp(22)
            content.add_widget(edit_type)

            # میزان هدف
            content.add_widget(RTLLabel(
                text='میزان هدف:',
                size_hint_y=None,
                height=dp(25),
                font_size=sp(24),
                color=(1, 1, 1, 1)
            ))
            edit_value = RTLTextInput(
                text=str(target.get('target_value', 0)),
                multiline=False,
                size_hint_y=None,
                height=dp(55),
                input_filter='int',
                font_size=sp(32)
            )
            edit_value.bg_color = (0.15, 0.15, 0.15, 1)
            edit_value.border_color = (0.3, 0.3, 0.3, 1)
            edit_value.border_color_focus = (0.2, 0.5, 0.9, 1)
            edit_value._hidden_input.foreground_color = (1, 1, 1, 1)
            content.add_widget(edit_value)

            # مدت
            content.add_widget(RTLLabel(
                text='مدت (روز):',
                size_hint_y=None,
                height=dp(25),
                font_size=sp(24),
                color=(1, 1, 1, 1)
            ))
            edit_duration = RTLTextInput(
                text=str(target.get('duration', 0)),
                multiline=False,
                size_hint_y=None,
                height=dp(55),
                input_filter='int',
                font_size=sp(32)
            )
            edit_duration.bg_color = (0.15, 0.15, 0.15, 1)
            edit_duration.border_color = (0.3, 0.3, 0.3, 1)
            edit_duration.border_color_focus = (0.2, 0.5, 0.9, 1)
            edit_duration._hidden_input.foreground_color = (1, 1, 1, 1)
            content.add_widget(edit_duration)

            # تاریخ شروع
            content.add_widget(RTLLabel(
                text='تاریخ شروع:',
                size_hint_y=None,
                height=dp(25),
                font_size=sp(24),
                color=(1, 1, 1, 1)
            ))
            edit_start_date = RTLTextInput(
                text=target.get('start_date', ''),
                multiline=False,
                size_hint_y=None,
                height=dp(55),
                font_size=sp(32)
            )
            edit_start_date.bg_color = (0.15, 0.15, 0.15, 1)
            edit_start_date.border_color = (0.3, 0.3, 0.3, 1)
            edit_start_date.border_color_focus = (0.2, 0.5, 0.9, 1)
            edit_start_date._hidden_input.foreground_color = (1, 1, 1, 1)
            content.add_widget(edit_start_date)

            # وضعیت
            content.add_widget(RTLLabel(
                text='وضعیت:',
                size_hint_y=None,
                height=dp(25),
                font_size=sp(24),
                color=(1, 1, 1, 1)
            ))
            edit_status = PersianComboBox(
                text=target.get('status', ''),
                values=TARGET_STATUSES,
                height=dp(55)
            )
            edit_status.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            edit_status.main_btn.color = (1, 1, 1, 1)
            edit_status.main_btn.font_size = sp(16)
            content.add_widget(edit_status)

            # توضیحات
            content.add_widget(RTLLabel(
                text='توضیحات:',
                size_hint_y=None,
                height=dp(25),
                font_size=sp(20),
                color=(1, 1, 1, 1)
            ))
            edit_description = RTLTextInput(
                text=target.get('description', ''),
                multiline=True,
                size_hint_y=None,
                height=dp(60),
                font_size=sp(32)
            )
            edit_description.bg_color = (0.15, 0.15, 0.15, 1)
            edit_description.border_color = (0.3, 0.3, 0.3, 1)
            edit_description.border_color_focus = (0.2, 0.5, 0.9, 1)
            edit_description._hidden_input.foreground_color = (1, 1, 1, 1)
            content.add_widget(edit_description)

            btn_layout = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(8))

            save_btn = PersianButton(
                text='ذخیره تغییرات',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_x=0.5,
                size_hint_y=None,
                height=dp(40),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            cancel_btn = PersianButton(
                text='انصراف',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_x=0.5,
                size_hint_y=None,
                height=dp(40),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )

            btn_layout.add_widget(save_btn)
            btn_layout.add_widget(cancel_btn)
            content.add_widget(btn_layout)

            popup = PersianPopup(
                title='ویرایش تارگت',
                content=content,
                size_hint=(0.92, 0.85),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )

            def do_save(instance):
                try:
                    from utils.jalali_date import validate_jalali_date

                    target_id = target.get('target_id')
                    updates = {
                        'target_type': edit_type.text,
                        'target_value': int(edit_value.text) if edit_value.text else 0,
                        'duration': int(edit_duration.text) if edit_duration.text else 0,
                        'start_date': edit_start_date.text,
                        'status': edit_status.text,
                        'description': edit_description.text
                    }

                    if updates['target_value'] <= 0:
                        self.show_message('خطا', 'میزان هدف باید بزرگتر از صفر باشد')
                        return

                    if updates['duration'] <= 0:
                        self.show_message('خطا', 'مدت باید بزرگتر از صفر باشد')
                        return

                    if not validate_jalali_date(updates['start_date']):
                        self.show_message('خطا', 'تاریخ شروع نامعتبر است')
                        return

                    success, message = update_target(target_id, updates)
                    popup.dismiss()

                    if success:
                        self.show_message('موفق', message)
                        self.show_targets_list(None)
                    else:
                        self.show_message('خطا', message)

                except Exception as e:
                    error_details = traceback.format_exc()
                    ErrorPopup.show_error(f"خطا در ذخیره تغییرات: {e}", error_details)

            save_btn.bind(on_press=do_save)
            cancel_btn.bind(on_press=popup.dismiss)
            popup.open()

        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ویرایش تارگت: {e}", error_details)

    def _delete_target(self, target):
        """حذف تارگت با دیالوگ تأیید"""
        try:
            from utils.target_manager import delete_target

            status = target.get('status', '')
            if status == 'تکمیل شده':
                self.show_message('خطا', 'تارگت‌های نهایی شده قابل حذف نیستند')
                return

            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            with content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                           size=lambda i, v: setattr(content_rect, 'size', v))

            content.add_widget(RTLLabel(
                text=f'آیا از حذف تارگت "{target.get("target_id", "")}" اطمینان دارید؟',
                size_hint_y=None,
                height=dp(45),
                font_size=sp(18),
                color=(1, 0.8, 0.2, 1)
            ))

            content.add_widget(RTLLabel(
                text=f'عامل: {target.get("agent_name", "")}\nنوع: {target.get("target_type", "")}\nمیزان: {target.get("target_value", 0):,}',
                size_hint_y=None,
                height=dp(50),
                font_size=sp(14),
                color=(0.8, 0.8, 0.8, 1)
            ))

            btn_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(50))

            confirm_btn = PersianButton(
                text='بله، حذف شود',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            cancel_btn = PersianButton(
                text='انصراف',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )

            btn_layout.add_widget(confirm_btn)
            btn_layout.add_widget(cancel_btn)
            content.add_widget(btn_layout)

            popup = PersianPopup(
                title='تأیید حذف',
                content=content,
                size_hint=(0.85, 0.45),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )

            def do_delete(instance):
                popup.dismiss()
                target_id = target.get('target_id')
                success, message = delete_target(target_id)
                if success:
                    self.show_message('موفق', message)
                    self.show_targets_list(None)
                else:
                    self.show_message('خطا', message)

            def cancel_delete(instance):
                popup.dismiss()

            confirm_btn.bind(on_press=do_delete)
            cancel_btn.bind(on_press=cancel_delete)
            popup.open()

        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در حذف تارگت: {e}", error_details)

    # ============================================================
    # تب ۲: تحقق تارگت
    # ============================================================

    def show_fulfillment_tab(self):
        """نمایش تب تحقق تارگت"""
        try:
            from utils.file_picker_import import ImportFilePicker

            scroll = ScrollView(
                do_scroll_x=False,
                do_scroll_y=True,
                size_hint=(1, 1),
                scroll_type=['bars', 'content'],
                bar_width=dp(8)
            )

            content = GridLayout(
                cols=1,
                spacing=dp(10),
                size_hint_y=None,
                padding=dp(12)
            )
            content.bind(minimum_height=content.setter('height'))

            # عنوان
            content.add_widget(RTLLabel(
                text='تحقق تارگت',
                size_hint_y=None,
                height=dp(50),
                font_size=sp(22),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))

            # ========== فیلترها ==========
            filter_layout = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(250))
            filter_layout.bind(minimum_height=filter_layout.setter('height'))

            # فیلتر بازه از تاریخ
            filter_layout.add_widget(RTLLabel(
                text='از تاریخ:',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))

            self.fulfillment_start_date = RTLTextInput(
                text=get_today_jalali(),
                multiline=False,
                size_hint_y=None,
                height=dp(65),
                font_size=sp(24)
            )
            self.fulfillment_start_date.bg_color = (0.15, 0.15, 0.15, 1)
            self.fulfillment_start_date.border_color = (0.3, 0.3, 0.3, 1)
            self.fulfillment_start_date.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.fulfillment_start_date._hidden_input.foreground_color = (1, 1, 1, 1)
            filter_layout.add_widget(self.fulfillment_start_date)

            # فیلتر بازه تا تاریخ
            filter_layout.add_widget(RTLLabel(
                text='تا تاریخ:',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))

            self.fulfillment_end_date = RTLTextInput(
                text=get_today_jalali(),
                multiline=False,
                size_hint_y=None,
                height=dp(65),
                font_size=sp(24)
            )
            self.fulfillment_end_date.bg_color = (0.15, 0.15, 0.15, 1)
            self.fulfillment_end_date.border_color = (0.3, 0.3, 0.3, 1)
            self.fulfillment_end_date.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.fulfillment_end_date._hidden_input.foreground_color = (1, 1, 1, 1)
            filter_layout.add_widget(self.fulfillment_end_date)

            # فیلتر عامل (بدون گزینه همه)
            filter_layout.add_widget(RTLLabel(
                text='انتخاب عامل:',
                size_hint_y=None,
                height=dp(35),
                font_size=sp(16),
                color=(1, 1, 1, 1)
            ))

            agents = get_agents()
            agent_names = [a.get('name', '') for a in agents] if agents else ['']

            self.fulfillment_agent = PersianComboBox(
                text=agent_names[0] if agent_names else '',
                values=agent_names,
                height=dp(65)
            )
            self.fulfillment_agent.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.fulfillment_agent.main_btn.color = (1, 1, 1, 1)
            self.fulfillment_agent.main_btn.font_size = sp(18)
            filter_layout.add_widget(self.fulfillment_agent)

            content.add_widget(filter_layout)

            # دکمه نمایش تارگت‌ها
            show_btn = PersianButton(
                text='نمایش تارگت‌ها',
                background_color=(0.2, 0.6, 1, 1),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(18)
            )
            show_btn.bind(on_press=self.show_fulfillment_targets)
            content.add_widget(show_btn)

            # ========== لیست تارگت‌ها ==========
            self.fulfillment_list_scroll = ScrollView(
                do_scroll_x=False,
                do_scroll_y=True,
                size_hint_y=0.45,
                scroll_type=['bars', 'content'],
                bar_width=dp(6)
            )

            self.fulfillment_list = GridLayout(
                cols=1,
                spacing=dp(6),
                size_hint_y=None,
                padding=dp(5)
            )
            self.fulfillment_list.bind(minimum_height=self.fulfillment_list.setter('height'))

            self.fulfillment_list_scroll.add_widget(self.fulfillment_list)
            content.add_widget(self.fulfillment_list_scroll)

            # ========== دکمه انتخاب فایل ==========
            self.fulfillment_file_picker = ImportFilePicker(
                on_select=self.on_fulfillment_file_selected,
                size_hint_y=None,
                height=dp(60)
            )
            content.add_widget(self.fulfillment_file_picker)

            scroll.add_widget(content)
            self.content_area.add_widget(scroll)

        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش تب تحقق تارگت: {e}", error_details)

    def show_fulfillment_targets(self, instance):
        """نمایش تارگت‌ها در یک دیالوگ جداگانه"""
        try:
            agent = self.fulfillment_agent.text
            start_date = self.fulfillment_start_date.text.strip()
            end_date = self.fulfillment_end_date.text.strip()

            if not agent or agent == '':
                self.show_message('خطا', 'لطفاً یک عامل را انتخاب کنید')
                return

            if start_date and not validate_jalali_date(start_date):
                self.show_message('خطا', 'تاریخ شروع نامعتبر است')
                return

            if end_date and not validate_jalali_date(end_date):
                self.show_message('خطا', 'تاریخ پایان نامعتبر است')
                return

            targets = get_active_targets_by_agent(agent, start_date, end_date)

            # ========== ساخت دیالوگ ==========
            dialog_content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
            with dialog_content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                content_rect = Rectangle(pos=dialog_content.pos, size=dialog_content.size)
                dialog_content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                                size=lambda i, v: setattr(content_rect, 'size', v))

            if not targets:
                dialog_content.add_widget(RTLLabel(
                    text='هیچ تارگت فعالی در بازه انتخابی یافت نشد',
                    size_hint_y=None,
                    height=dp(45),
                    font_size=sp(16),
                    color=(0.5, 0.5, 0.5, 1)
                ))
            else:
                list_scroll = ScrollView(
                    do_scroll_x=False,
                    do_scroll_y=True,
                    size_hint_y=0.6
                )

                list_content = GridLayout(
                    cols=1,
                    spacing=dp(4),
                    size_hint_y=None,
                    padding=dp(5)
                )
                list_content.bind(minimum_height=list_content.setter('height'))

                self.fulfillment_selected = {}

                for target in targets:
                    box = BoxLayout(
                        size_hint_y=None,
                        height=dp(50),
                        spacing=dp(5),
                        padding=[dp(5), dp(2), dp(5), dp(2)]
                    )

                    check = CheckBox(
                        size_hint_x=0.1,
                        size_hint_y=None,
                        height=dp(40),
                        color=(0.4, 0.7, 1, 1)
                    )
                    check.active = False
                    target_id = target.get('target_id')
                    check.bind(active=lambda cb, value, tid=target_id: self._toggle_fulfillment_selection(tid, value))
                    box.add_widget(check)

                    self.fulfillment_selected[target_id] = False

                    info = RTLLabel(
                        text=f"{target.get('target_id', '')} | {target.get('target_type', '')} | "
                            f"{target.get('target_value', 0):,}",
                        size_hint_x=0.9,
                        size_hint_y=None,
                        height=dp(40),
                        font_size=sp(13),
                        color=(1, 1, 1, 1)
                    )
                    box.add_widget(info)

                    list_content.add_widget(box)

                list_scroll.add_widget(list_content)
                dialog_content.add_widget(list_scroll)

                select_all_btn = PersianButton(
                    text='انتخاب همه',
                    background_color=(0.2, 0.5, 0.8, 1),
                    size_hint_y=None,
                    height=dp(35),
                    color=(1, 1, 1, 1),
                    font_size=sp(14)
                )
                select_all_btn.bind(on_press=self._select_all_fulfillment_targets)
                dialog_content.add_widget(select_all_btn)

            btn_row = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(8))

            confirm_btn = PersianButton(
                text='تأیید و اعمال تحقق',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_x=0.5,
                size_hint_y=None,
                height=dp(40),
                color=(1, 1, 1, 1),
                font_size=sp(14)
            )
            confirm_btn.bind(on_press=lambda x: self._apply_fulfillment_from_dialog(dialog_popup))
            btn_row.add_widget(confirm_btn)

            close_btn = PersianButton(
                text='بستن',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_x=0.5,
                size_hint_y=None,
                height=dp(40),
                color=(1, 1, 1, 1),
                font_size=sp(14)
            )
            btn_row.add_widget(close_btn)

            dialog_content.add_widget(btn_row)

            dialog_popup = PersianPopup(
                title='انتخاب تارگت برای تحقق',
                content=dialog_content,
                size_hint=(0.92, 0.8),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )

            close_btn.bind(on_press=dialog_popup.dismiss)
            dialog_popup.open()

        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش تارگت‌ها: {e}", error_details)

    def _select_all_fulfillment_targets(self, instance):
        """انتخاب همه تارگت‌ها در دیالوگ تحقق"""
        try:
            if hasattr(self, 'fulfillment_selected'):
                count = 0
                for key in self.fulfillment_selected:
                    self.fulfillment_selected[key] = True
                    count += 1
                self.show_message('اطلاع', f'{count} تارگت انتخاب شد، برای نهایی سازی فایل اکسل را انتخاب نمایید')
        except Exception as e:
            print(f"خطا در انتخاب همه: {e}")

    def _apply_fulfillment_from_dialog(self, popup):
        """اعمال تحقق از دیالوگ"""
        try:
            selected_targets = [tid for tid, selected in self.fulfillment_selected.items() if selected]

            if not selected_targets:
                self.show_message('خطا', 'هیچ تارگتی انتخاب نشده است')
                return

            agent_name = self.fulfillment_agent.text
            self.show_message('اطلاع', f'{len(selected_targets)} تارگت انتخاب شد، برای نهایی سازی فایل اکسل را انتخاب نمایید')
            
            popup.dismiss()

        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در اعمال تحقق: {e}", error_details)

    def _toggle_fulfillment_selection(self, target_id, value):
        """تغییر وضعیت انتخاب تارگت برای تحقق"""
        if hasattr(self, 'fulfillment_selected'):
            self.fulfillment_selected[target_id] = value

    def on_fulfillment_file_selected(self, filepath):
        """پس از انتخاب فایل اکسل برای تحقق"""
        try:
            if not filepath:
                self.show_message('خطا', 'فایلی انتخاب نشده است')
                return

            summary_data = read_excel_summary(filepath)

            if not summary_data:
                self.show_message('خطا', 'داده‌های خلاصه در فایل اکسل یافت نشد')
                return

            selected_targets = [tid for tid, selected in self.fulfillment_selected.items() if selected]

            if not selected_targets:
                self.show_message('خطا', 'هیچ تارگتی انتخاب نشده است')
                return

            all_targets = get_all_targets()

            achieved_values = {}
            target_details = []
            agent_name = self.fulfillment_agent.text

            for target in all_targets:
                target_id = target.get('target_id')
                if target_id in selected_targets:
                    target_type = target.get('target_type', '')
                    excel_key = TARGET_EXCEL_MAPPING.get(target_type)

                    if excel_key and excel_key in summary_data:
                        achieved_values[target_id] = summary_data[excel_key]
                        target_details.append({
                            'id': target_id,
                            'type': target_type,
                            'achieved': summary_data[excel_key],
                            'target': target.get('target_value', 0)
                        })
                    else:
                        self.show_message('خطا', f'نوع تارگت "{target_type}" در فایل اکسل یافت نشد')
                        return

            if not achieved_values:
                self.show_message('خطا', 'هیچ داده‌ای برای تطبیق با تارگت‌ها یافت نشد')
                return

            self._show_fulfillment_confirm_dialog(selected_targets, achieved_values, target_details, agent_name)

        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در اعمال تحقق: {e}", error_details)

    def _show_fulfillment_confirm_dialog(self, target_ids, achieved_values, target_details, agent_name):
        """نمایش دیالوگ تأیید نهایی‌سازی"""
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            with content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                        size=lambda i, v: setattr(content_rect, 'size', v))

            content.add_widget(RTLLabel(
                text=f'کاربر گرامی از انتخاب این فایل اکسل برای {agent_name} مطمئن هستید؟',
                size_hint_y=None,
                height=dp(50),
                font_size=sp(18),
                color=(1, 0.8, 0.2, 1)
            ))

            list_scroll = ScrollView(size_hint_y=0.5, do_scroll_x=False)
            list_content = GridLayout(cols=1, spacing=dp(4), size_hint_y=None)
            list_content.bind(minimum_height=list_content.setter('height'))

            for detail in target_details:
                list_content.add_widget(RTLLabel(
                    text=f"{detail['id']} | {detail['type']} | "
                        f"هدف: {detail['target']:,} | تحقق: {detail['achieved']:,}",
                    size_hint_y=None,
                    height=dp(30),
                    font_size=sp(14),
                    color=(1, 1, 1, 1)
                ))

            list_scroll.add_widget(list_content)
            content.add_widget(list_scroll)

            btn_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(55))

            confirm_btn = PersianButton(
                text='بله',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )
            cancel_btn = PersianButton(
                text='خیر',
                background_color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(50),
                color=(1, 1, 1, 1),
                font_size=sp(16)
            )

            btn_layout.add_widget(confirm_btn)
            btn_layout.add_widget(cancel_btn)
            content.add_widget(btn_layout)

            popup = PersianPopup(
                title='تأیید نهایی‌سازی',
                content=content,
                size_hint=(0.9, 0.6),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )

            def do_finalize(instance):
                popup.dismiss()
                self._perform_fulfillment(target_ids, achieved_values)

            def cancel_finalize(instance):
                popup.dismiss()

            confirm_btn.bind(on_press=do_finalize)
            cancel_btn.bind(on_press=cancel_finalize)
            popup.open()

        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش دیالوگ تأیید: {e}", error_details)

    def _perform_fulfillment(self, target_ids, achieved_values):
        """اجرای نهایی‌سازی تارگت‌ها"""
        try:
            success, message = finalize_targets(target_ids, achieved_values)

            if success:
                self.show_message('موفق', 'عملیات نهایی سازی با موفقیت انجام شد')
                self.show_fulfillment_targets(None)
            else:
                self.show_message('خطا', message)

        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نهایی‌سازی تارگت‌ها: {e}", error_details)

    # ============================================================
    # تب ۳: بررسی بازار
    # ============================================================

    def show_market_check_tab(self):
        """نمایش تب بررسی بازار"""
        try:
            from utils.supervisor_visits_manager import create_supervisor_visit
            from constants import (
                VISIT_TYPES, VISIT_REASONS, CUSTOMER_STATUSES,
                SHELF_STATUSES, MONTHLY_VISITS, VISIT_SUFFICIENT,
                EXPECTED_PURCHASE, INVENTORY_STATUSES, BEHAVIOR_RATINGS,
                SATISFACTION_RATINGS, TARGET_ACHIEVEMENTS, YES_NO_OPTIONS
            )

            scroll = ScrollView(
                do_scroll_x=False,
                do_scroll_y=True,
                size_hint=(1, 1),
                scroll_type=['bars', 'content'],
                bar_width=dp(8)
            )

            content = GridLayout(
                cols=2,
                spacing=dp(8),
                size_hint_y=None,
                padding=dp(12)
            )
            content.bind(minimum_height=content.setter('height'))

            # ========== عنوان ==========
            title_box = BoxLayout(size_hint_y=None, height=dp(40))
            title_box.add_widget(RTLLabel(
                text='بررسی بازار',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(20),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))
            content.add_widget(title_box)
            content.add_widget(Label())

            # ========== ۱- مسیر ==========
            content.add_widget(RTLLabel(
                text='مسیر:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(15),
                color=(1, 1, 1, 1)
            ))

            routes = get_routes()
            route_names = [r.get('name', '') for r in routes] if routes else ['']

            self.market_route_spinner = PersianComboBox(
                text=route_names[0] if route_names else '',
                values=route_names,
                height=dp(55)
            )
            self.market_route_spinner.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.market_route_spinner.main_btn.color = (1, 1, 1, 1)
            self.market_route_spinner.main_btn.font_size = sp(17)
            
            self._last_market_route_text = self.market_route_spinner.text
            Clock.schedule_interval(self._check_market_route_change, 0.3)
            
            content.add_widget(self.market_route_spinner)

            # ========== ۲- مشتری ==========
            content.add_widget(RTLLabel(
                text='مشتری:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(15),
                color=(1, 1, 1, 1)
            ))

            self.market_customer_spinner = PersianComboBox(
                text='',
                values=[''],
                height=dp(55)
            )
            self.market_customer_spinner.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.market_customer_spinner.main_btn.color = (1, 1, 1, 1)
            self.market_customer_spinner.main_btn.font_size = sp(17)
            content.add_widget(self.market_customer_spinner)

            # ========== ۳- نحوه سرکشی ==========
            content.add_widget(RTLLabel(
                text='نحوه سرکشی:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(15),
                color=(1, 1, 1, 1)
            ))

            self.market_visit_type = PersianComboBox(
                text=VISIT_TYPES[0],
                values=VISIT_TYPES,
                height=dp(55)
            )
            self.market_visit_type.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.market_visit_type.main_btn.color = (1, 1, 1, 1)
            self.market_visit_type.main_btn.font_size = sp(17)
            content.add_widget(self.market_visit_type)

            # ========== ۴- علت سرکشی ==========
            content.add_widget(RTLLabel(
                text='علت سرکشی:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(15),
                color=(1, 1, 1, 1)
            ))

            self.market_visit_reason = PersianComboBox(
                text=VISIT_REASONS[0],
                values=VISIT_REASONS,
                height=dp(55)
            )
            self.market_visit_reason.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.market_visit_reason.main_btn.color = (1, 1, 1, 1)
            self.market_visit_reason.main_btn.font_size = sp(17)
            content.add_widget(self.market_visit_reason)

            # ========== ۵- توضیحات سوپروایزر ==========
            content.add_widget(RTLLabel(
                text='توضیحات سوپروایزر:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(15),
                color=(1, 1, 1, 1)
            ))

            self.market_supervisor_note = RTLTextInput(
                hint_text='توضیحات را وارد کنید...',
                multiline=True,
                size_hint_y=None,
                height=dp(70),
                font_size=sp(17)
            )
            self.market_supervisor_note.bg_color = (0.15, 0.15, 0.15, 1)
            self.market_supervisor_note.border_color = (0.3, 0.3, 0.3, 1)
            self.market_supervisor_note.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.market_supervisor_note._hidden_input.foreground_color = (1, 1, 1, 1)
            content.add_widget(self.market_supervisor_note)

            # ========== ۶- وضعیت مشتری ==========
            content.add_widget(RTLLabel(
                text='وضعیت مشتری:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(15),
                color=(1, 1, 1, 1)
            ))

            self.market_customer_status = PersianComboBox(
                text=CUSTOMER_STATUSES[0],
                values=CUSTOMER_STATUSES,
                height=dp(55)
            )
            self.market_customer_status.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.market_customer_status.main_btn.color = (1, 1, 1, 1)
            self.market_customer_status.main_btn.font_size = sp(17)
            content.add_widget(self.market_customer_status)

            # ========== ۷- وضعیت حضور در شلف ==========
            content.add_widget(RTLLabel(
                text='وضعیت حضور در شلف:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(15),
                color=(1, 1, 1, 1)
            ))

            self.market_shelf_status = PersianComboBox(
                text=SHELF_STATUSES[0],
                values=SHELF_STATUSES,
                height=dp(55)
            )
            self.market_shelf_status.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.market_shelf_status.main_btn.color = (1, 1, 1, 1)
            self.market_shelf_status.main_btn.font_size = sp(17)
            content.add_widget(self.market_shelf_status)

            # ========== ۸- تعداد سرکشی بازاریابان ==========
            content.add_widget(RTLLabel(
                text='تعداد سرکشی بازاریابان در ماه:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(15),
                color=(1, 1, 1, 1)
            ))

            self.market_monthly_visits = PersianComboBox(
                text=MONTHLY_VISITS[0],
                values=MONTHLY_VISITS,
                height=dp(55)
            )
            self.market_monthly_visits.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.market_monthly_visits.main_btn.color = (1, 1, 1, 1)
            self.market_monthly_visits.main_btn.font_size = sp(17)
            content.add_widget(self.market_monthly_visits)

            # ========== ۹- آیا میزان سرکشی کافیست؟ ==========
            content.add_widget(RTLLabel(
                text='آیا میزان سرکشی کافیست؟:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(15),
                color=(1, 1, 1, 1)
            ))

            self.market_visit_sufficient = PersianComboBox(
                text=VISIT_SUFFICIENT[0],
                values=VISIT_SUFFICIENT,
                height=dp(55)
            )
            self.market_visit_sufficient.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.market_visit_sufficient.main_btn.color = (1, 1, 1, 1)
            self.market_visit_sufficient.main_btn.font_size = sp(17)
            content.add_widget(self.market_visit_sufficient)

            # ========== ۱۰- میزان خرید مورد انتظار ==========
            content.add_widget(RTLLabel(
                text='میزان خرید مورد انتظار:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(15),
                color=(1, 1, 1, 1)
            ))

            self.market_expected_purchase = PersianComboBox(
                text=EXPECTED_PURCHASE[0],
                values=EXPECTED_PURCHASE,
                height=dp(55)
            )
            self.market_expected_purchase.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.market_expected_purchase.main_btn.color = (1, 1, 1, 1)
            self.market_expected_purchase.main_btn.font_size = sp(17)
            content.add_widget(self.market_expected_purchase)

            # ========== ۱۱- وضعیت موجودی ==========
            content.add_widget(RTLLabel(
                text='وضعیت موجودی مشتری:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(15),
                color=(1, 1, 1, 1)
            ))

            self.market_inventory_status = PersianComboBox(
                text=INVENTORY_STATUSES[0],
                values=INVENTORY_STATUSES,
                height=dp(55)
            )
            self.market_inventory_status.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.market_inventory_status.main_btn.color = (1, 1, 1, 1)
            self.market_inventory_status.main_btn.font_size = sp(17)
            content.add_widget(self.market_inventory_status)

            # ========== ۱۲- نحوه برخورد بازاریابان ==========
            content.add_widget(RTLLabel(
                text='نحوه برخورد بازاریابان:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(15),
                color=(1, 1, 1, 1)
            ))

            self.market_agent_behavior = PersianComboBox(
                text=BEHAVIOR_RATINGS[0],
                values=BEHAVIOR_RATINGS,
                height=dp(55)
            )
            self.market_agent_behavior.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.market_agent_behavior.main_btn.color = (1, 1, 1, 1)
            self.market_agent_behavior.main_btn.font_size = sp(17)
            content.add_widget(self.market_agent_behavior)

            # ========== ۱۳- نحوه برخورد موزعین ==========
            content.add_widget(RTLLabel(
                text='نحوه برخورد موزعین:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(15),
                color=(1, 1, 1, 1)
            ))

            self.market_distributor_behavior = PersianComboBox(
                text=BEHAVIOR_RATINGS[0],
                values=BEHAVIOR_RATINGS,
                height=dp(55)
            )
            self.market_distributor_behavior.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.market_distributor_behavior.main_btn.color = (1, 1, 1, 1)
            self.market_distributor_behavior.main_btn.font_size = sp(17)
            content.add_widget(self.market_distributor_behavior)

            # ========== ۱۴- میزان رضایتمندی مشتری ==========
            content.add_widget(RTLLabel(
                text='میزان رضایتمندی مشتری:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(15),
                color=(1, 1, 1, 1)
            ))

            self.market_customer_satisfaction = PersianComboBox(
                text=SATISFACTION_RATINGS[0],
                values=SATISFACTION_RATINGS,
                height=dp(55)
            )
            self.market_customer_satisfaction.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.market_customer_satisfaction.main_btn.color = (1, 1, 1, 1)
            self.market_customer_satisfaction.main_btn.font_size = sp(17)
            content.add_widget(self.market_customer_satisfaction)

            # ========== ۱۵- نظرات مشتری ==========
            content.add_widget(RTLLabel(
                text='نظرات مشتری:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(15),
                color=(1, 1, 1, 1)
            ))

            self.market_customer_feedback = RTLTextInput(
                hint_text='حداکثر ۱۰۰۰ کاراکتر...',
                multiline=True,
                size_hint_y=None,
                height=dp(70),
                font_size=sp(17)
            )
            self.market_customer_feedback.bg_color = (0.15, 0.15, 0.15, 1)
            self.market_customer_feedback.border_color = (0.3, 0.3, 0.3, 1)
            self.market_customer_feedback.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.market_customer_feedback._hidden_input.foreground_color = (1, 1, 1, 1)
            content.add_widget(self.market_customer_feedback)

            # ========== ۱۶- میزان تحقق هدف سرکشی ==========
            content.add_widget(RTLLabel(
                text='میزان تحقق هدف سرکشی:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(15),
                color=(1, 1, 1, 1)
            ))

            self.market_target_achievement = PersianComboBox(
                text=TARGET_ACHIEVEMENTS[0],
                values=TARGET_ACHIEVEMENTS,
                height=dp(55)
            )
            self.market_target_achievement.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.market_target_achievement.main_btn.color = (1, 1, 1, 1)
            self.market_target_achievement.main_btn.font_size = sp(17)
            content.add_widget(self.market_target_achievement)

            # ========== ۱۷- نظریه سوپروایزر ==========
            content.add_widget(RTLLabel(
                text='نظریه سوپروایزر:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(15),
                color=(1, 1, 1, 1)
            ))

            self.market_supervisor_opinion = RTLTextInput(
                hint_text='حداکثر ۱۵۰۰ کاراکتر...',
                multiline=True,
                size_hint_y=None,
                height=dp(70),
                font_size=sp(17)
            )
            self.market_supervisor_opinion.bg_color = (0.15, 0.15, 0.15, 1)
            self.market_supervisor_opinion.border_color = (0.3, 0.3, 0.3, 1)
            self.market_supervisor_opinion.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.market_supervisor_opinion._hidden_input.foreground_color = (1, 1, 1, 1)
            content.add_widget(self.market_supervisor_opinion)

            # ========== ۱۸- آیا پیگیری مجدد نیاز است؟ ==========
            content.add_widget(RTLLabel(
                text='آیا پیگیری مجدد نیاز است؟:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(15),
                color=(1, 1, 1, 1)
            ))

            self.market_need_followup = PersianComboBox(
                text=YES_NO_OPTIONS[0],
                values=YES_NO_OPTIONS,
                height=dp(55)
            )
            self.market_need_followup.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            self.market_need_followup.main_btn.color = (1, 1, 1, 1)
            self.market_need_followup.main_btn.font_size = sp(17)
            
            self._last_followup_text = self.market_need_followup.text
            Clock.schedule_interval(self._check_followup_change, 0.3)
            
            content.add_widget(self.market_need_followup)

            # ========== ۱۹- تاریخ مراجعه بعدی ==========
            content.add_widget(RTLLabel(
                text='تاریخ مراجعه بعدی:',
                size_hint_y=None,
                height=dp(28),
                font_size=sp(15),
                color=(1, 1, 1, 1)
            ))

            self.market_next_visit_date = RTLTextInput(
                text='',
                hint_text='سال/ماه/روز',
                multiline=False,
                size_hint_y=None,
                height=dp(55),
                font_size=sp(20)
            )
            self.market_next_visit_date.bg_color = (0.15, 0.15, 0.15, 1)
            self.market_next_visit_date.border_color = (0.3, 0.3, 0.3, 1)
            self.market_next_visit_date.border_color_focus = (0.2, 0.5, 0.9, 1)
            self.market_next_visit_date._hidden_input.foreground_color = (1, 1, 1, 1)
            content.add_widget(self.market_next_visit_date)

            # ========== دکمه ثبت ==========
            btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))

            submit_btn = PersianButton(
                text='ثبت سرکشی',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(17)
            )
            submit_btn.bind(on_press=self.submit_market_check)
            btn_layout.add_widget(submit_btn)

            report_btn = PersianButton(
                text='گزارشات',
                background_color=(0.2, 0.5, 0.8, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(17)
            )
            report_btn.bind(on_press=self.show_market_reports)
            btn_layout.add_widget(report_btn)

            content.add_widget(btn_layout)

            scroll.add_widget(content)
            self.content_area.add_widget(scroll)

            Clock.schedule_once(lambda dt: self.update_market_customers(), 0.1)

        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش تب بررسی بازار: {e}", error_details)

    def _check_market_route_change(self, dt):
        """بررسی تغییر مسیر در تب بررسی بازار با Clock"""
        if hasattr(self, 'market_route_spinner'):
            current_text = self.market_route_spinner.text
            if current_text != self._last_market_route_text:
                self._last_market_route_text = current_text
                self.update_market_customers()

    def _check_followup_change(self, dt):
        """بررسی تغییر گزینه نیاز به پیگیری"""
        try:
            if not hasattr(self, 'market_need_followup'):
                return
                
            current_text = self.market_need_followup.text
            
            if current_text != self._last_followup_text:
                self._last_followup_text = current_text
                
                if current_text == 'بله' and not self.market_next_visit_date.text:
                    self.market_next_visit_date.text = get_today_jalali()
        except Exception as e:
            print(f"خطا در بررسی تغییرات: {e}")

    def update_market_customers(self):
        """به‌روزرسانی لیست مشتریان بر اساس مسیر انتخاب شده"""
        try:
            if not hasattr(self, 'market_route_spinner') or not hasattr(self, 'market_customer_spinner'):
                return

            selected_route = self.market_route_spinner.text
            all_customers = get_customers()

            filtered = []
            for c in all_customers:
                if c.get('route_name', '').strip() == selected_route.strip():
                    filtered.append(c.get('name', ''))

            if filtered:
                self.market_customer_spinner.values = filtered
                self.market_customer_spinner.text = filtered[0] if filtered else ''
            else:
                self.market_customer_spinner.values = ['مشتری‌ای یافت نشد']
                self.market_customer_spinner.text = 'مشتری‌ای یافت نشد'

        except Exception as e:
            print(f"خطا در به‌روزرسانی مشتریان: {e}")

    def submit_market_check(self, instance):
        """ثبت سرکشی بررسی بازار"""
        try:
            from utils.supervisor_visits_manager import create_supervisor_visit
            from utils.jalali_date import validate_jalali_date

            data = {
                'route': self.market_route_spinner.text,
                'customer': self.market_customer_spinner.text,
                'visit_type': self.market_visit_type.text,
                'visit_reason': self.market_visit_reason.text,
                'supervisor_note': self.market_supervisor_note.text.strip(),
                'customer_status': self.market_customer_status.text,
                'shelf_status': self.market_shelf_status.text,
                'monthly_visits': self.market_monthly_visits.text,
                'visit_sufficient': self.market_visit_sufficient.text,
                'expected_purchase': self.market_expected_purchase.text,
                'inventory_status': self.market_inventory_status.text,
                'agent_behavior': self.market_agent_behavior.text,
                'distributor_behavior': self.market_distributor_behavior.text,
                'customer_satisfaction': self.market_customer_satisfaction.text,
                'customer_feedback': self.market_customer_feedback.text.strip(),
                'target_achievement': self.market_target_achievement.text,
                'supervisor_opinion': self.market_supervisor_opinion.text.strip(),
                'need_followup': self.market_need_followup.text,
                'next_visit_date': self.market_next_visit_date.text.strip()
            }

            if not data['route'] or data['route'] == '':
                self.show_message('خطا', 'لطفاً یک مسیر را انتخاب کنید')
                return

            if not data['customer'] or data['customer'] in ['', 'مشتری‌ای یافت نشد']:
                self.show_message('خطا', 'لطفاً یک مشتری را انتخاب کنید')
                return

            if data['need_followup'] == 'بله':
                if not data['next_visit_date']:
                    self.show_message('خطا', 'در صورت نیاز به پیگیری، تاریخ مراجعه بعدی را وارد کنید')
                    return
                if not validate_jalali_date(data['next_visit_date']):
                    self.show_message('خطا', 'فرمت تاریخ مراجعه بعدی نامعتبر است (مثال: 1405/01/31)')
                    return

            success, message, visit = create_supervisor_visit(data)

            if success:
                self.market_supervisor_note.text = ''
                self.market_customer_feedback.text = ''
                self.market_supervisor_opinion.text = ''
                self.market_next_visit_date.text = ''
                self.show_message('موفق', message)
            else:
                self.show_message('خطا', message)

        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در ثبت سرکشی: {e}", error_details)

    def show_market_reports(self, instance):
        """نمایش دیالوگ گزارشات بررسی بازار"""
        try:
            from utils.supervisor_visits_manager import get_all_visits, get_visits_filtered, export_visits_to_excel

            content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(6))
            with content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                        size=lambda i, v: setattr(content_rect, 'size', v))

            filter_layout = GridLayout(cols=2, spacing=dp(4), size_hint_y=None, height=dp(140))
            filter_layout.bind(minimum_height=filter_layout.setter('height'))

            filter_layout.add_widget(RTLLabel(
                text='مشتری:',
                size_hint_y=None,
                height=dp(22),
                font_size=sp(12),
                color=(1, 1, 1, 1)
            ))

            all_customers = get_customers()
            customer_names = ['همه'] + [c.get('name', '') for c in all_customers] if all_customers else ['همه']
            filter_customer = PersianComboBox(
                text='همه',
                values=customer_names,
                height=dp(45)
            )
            filter_customer.main_btn.background_color = (0.2, 0.2, 0.2, 1)
            filter_customer.main_btn.color = (1, 1, 1, 1)
            filter_customer.main_btn.font_size = sp(14)
            filter_layout.add_widget(filter_customer)

            filter_layout.add_widget(RTLLabel(
                text='از تاریخ:',
                size_hint_y=None,
                height=dp(22),
                font_size=sp(12),
                color=(1, 1, 1, 1)
            ))

            filter_start_date = RTLTextInput(
                text='',
                hint_text='سال/ماه/روز',
                multiline=False,
                size_hint_y=None,
                height=dp(45),
                font_size=sp(16)
            )
            filter_start_date.bg_color = (0.15, 0.15, 0.15, 1)
            filter_start_date.border_color = (0.3, 0.3, 0.3, 1)
            filter_start_date.border_color_focus = (0.2, 0.5, 0.9, 1)
            filter_start_date._hidden_input.foreground_color = (1, 1, 1, 1)
            filter_layout.add_widget(filter_start_date)

            filter_layout.add_widget(RTLLabel(
                text='تا تاریخ:',
                size_hint_y=None,
                height=dp(22),
                font_size=sp(12),
                color=(1, 1, 1, 1)
            ))

            filter_end_date = RTLTextInput(
                text='',
                hint_text='سال/ماه/روز',
                multiline=False,
                size_hint_y=None,
                height=dp(45),
                font_size=sp(16)
            )
            filter_end_date.bg_color = (0.15, 0.15, 0.15, 1)
            filter_end_date.border_color = (0.3, 0.3, 0.3, 1)
            filter_end_date.border_color_focus = (0.2, 0.5, 0.9, 1)
            filter_end_date._hidden_input.foreground_color = (1, 1, 1, 1)
            filter_layout.add_widget(filter_end_date)

            content.add_widget(filter_layout)

            btn_filter_layout = BoxLayout(size_hint_y=None, height=dp(35), spacing=dp(4))

            apply_btn = PersianButton(
                text='اعمال فیلتر',
                background_color=(0.2, 0.6, 1, 1),
                size_hint_x=0.5,
                size_hint_y=None,
                height=dp(30),
                color=(1, 1, 1, 1),
                font_size=sp(12)
            )
            btn_filter_layout.add_widget(apply_btn)

            export_btn = PersianButton(
                text='خروجی اکسل',
                background_color=(0.2, 0.7, 0.2, 1),
                size_hint_x=0.5,
                size_hint_y=None,
                height=dp(30),
                color=(1, 1, 1, 1),
                font_size=sp(12)
            )
            btn_filter_layout.add_widget(export_btn)

            content.add_widget(btn_filter_layout)

            list_scroll = ScrollView(
                do_scroll_x=False,
                do_scroll_y=True,
                size_hint_y=0.5
            )

            list_content = GridLayout(
                cols=1,
                spacing=dp(3),
                size_hint_y=None,
                padding=dp(3)
            )
            list_content.bind(minimum_height=list_content.setter('height'))

            visits = get_all_visits()

            if not visits:
                list_content.add_widget(RTLLabel(
                    text='هیچ سرکشی ثبت نشده است',
                    size_hint_y=None,
                    height=dp(30),
                    font_size=sp(13),
                    color=(0.5, 0.5, 0.5, 1)
                ))
            else:
                for visit in visits[:20]:
                    box = BoxLayout(
                        size_hint_y=None,
                        height=dp(35),
                        spacing=dp(4),
                        padding=[dp(3), dp(2), dp(3), dp(2)]
                    )

                    info = RTLLabel(
                        text=f"{visit.get('date', '')} | {visit.get('customer', '')} | {visit.get('route', '')}",
                        size_hint_x=0.7,
                        size_hint_y=None,
                        height=dp(30),
                        font_size=sp(12),
                        color=(1, 1, 1, 1)
                    )
                    box.add_widget(info)

                    detail_btn = PersianButton(
                        text='جزئیات',
                        size_hint_x=0.3,
                        size_hint_y=None,
                        height=dp(28),
                        background_color=(0.2, 0.5, 0.8, 1),
                        color=(1, 1, 1, 1),
                        font_size=sp(11)
                    )
                    visit_copy = visit.copy() if isinstance(visit, dict) else visit
                    detail_btn.bind(on_press=lambda x, v=visit_copy: self._show_visit_detail(v))
                    box.add_widget(detail_btn)

                    list_content.add_widget(box)

            list_scroll.add_widget(list_content)
            content.add_widget(list_scroll)

            close_btn = PersianButton(
                text='بستن',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(35),
                color=(1, 1, 1, 1),
                font_size=sp(14)
            )
            content.add_widget(close_btn)

            popup = PersianPopup(
                title='گزارشات بررسی بازار',
                content=content,
                size_hint=(0.92, 0.8),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )

            def apply_filter(instance):
                customer = filter_customer.text
                start_date = filter_start_date.text.strip()
                end_date = filter_end_date.text.strip()

                filtered = get_visits_filtered(
                    customer=customer if customer != 'همه' else None,
                    start_date=start_date if start_date else None,
                    end_date=end_date if end_date else None
                )

                list_content.clear_widgets()
                if not filtered:
                    list_content.add_widget(RTLLabel(
                        text='هیچ سرکشی یافت نشد',
                        size_hint_y=None,
                        height=dp(30),
                        font_size=sp(13),
                        color=(0.5, 0.5, 0.5, 1)
                    ))
                else:
                    for visit in filtered:
                        box = BoxLayout(
                            size_hint_y=None,
                            height=dp(35),
                            spacing=dp(4),
                            padding=[dp(3), dp(2), dp(3), dp(2)]
                        )
                        info = RTLLabel(
                            text=f"{visit.get('date', '')} | {visit.get('customer', '')} | {visit.get('route', '')}",
                            size_hint_x=0.7,
                            size_hint_y=None,
                            height=dp(30),
                            font_size=sp(12),
                            color=(1, 1, 1, 1)
                        )
                        box.add_widget(info)
                        detail_btn = PersianButton(
                            text='جزئیات',
                            size_hint_x=0.3,
                            size_hint_y=None,
                            height=dp(28),
                            background_color=(0.2, 0.5, 0.8, 1),
                            color=(1, 1, 1, 1),
                            font_size=sp(11)
                        )
                        visit_copy = visit.copy() if isinstance(visit, dict) else visit
                        detail_btn.bind(on_press=lambda x, v=visit_copy: self._show_visit_detail(v))
                        box.add_widget(detail_btn)
                        list_content.add_widget(box)

            def export_excel(instance):
                customer = filter_customer.text
                start_date = filter_start_date.text.strip()
                end_date = filter_end_date.text.strip()

                filtered = get_visits_filtered(
                    customer=customer if customer != 'همه' else None,
                    start_date=start_date if start_date else None,
                    end_date=end_date if end_date else None
                )

                if not filtered:
                    self.show_message('خطا', 'هیچ سرکشی برای خروجی وجود ندارد')
                    return

                success, message, filepath = export_visits_to_excel(filtered)
                if success:
                    self.show_message('موفق', message)
                else:
                    self.show_message('خطا', message)

            apply_btn.bind(on_press=apply_filter)
            export_btn.bind(on_press=export_excel)
            close_btn.bind(on_press=popup.dismiss)
            popup.open()

        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش گزارشات: {e}", error_details)

    def _show_visit_detail(self, visit):
        """نمایش جزئیات کامل یک سرکشی"""
        try:
            if not visit or not isinstance(visit, dict):
                self.show_message('خطا', 'اطلاعات سرکشی موجود نیست')
                return

            content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(8))
            with content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                        size=lambda i, v: setattr(content_rect, 'size', v))

            main_box = BoxLayout(orientation='vertical', size_hint_y=None)
            main_box.bind(minimum_height=main_box.setter('height'))

            visit_id = visit.get('id', 'نامشخص')
            main_box.add_widget(RTLLabel(
                text=f'جزئیات سرکشی - {visit_id}',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(22),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))

            table_container = BoxLayout(
                orientation='vertical',
                size_hint_y=None,
                spacing=dp(4),
                padding=dp(5)
            )
            table_container.bind(minimum_height=table_container.setter('height'))

            header_box = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(4))
            header_box.add_widget(RTLLabel(
                text='آیتم',
                size_hint_x=0.4,
                size_hint_y=None,
                height=dp(32),
                font_size=sp(20),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))
            header_box.add_widget(RTLLabel(
                text='مقدار',
                size_hint_x=0.6,
                size_hint_y=None,
                height=dp(32),
                font_size=sp(20),
                bold=True,
                color=(0.4, 0.7, 1, 1)
            ))
            table_container.add_widget(header_box)

            fields = [
                ('تاریخ', 'date'),
                ('ساعت', 'time'),
                ('مسیر', 'route'),
                ('مشتری', 'customer'),
                ('نحوه سرکشی', 'visit_type'),
                ('علت سرکشی', 'visit_reason'),
                ('وضعیت مشتری', 'customer_status'),
                ('وضعیت حضور در شلف', 'shelf_status'),
                ('تعداد سرکشی در ماه', 'monthly_visits'),
                ('آیا سرکشی کافیست؟', 'visit_sufficient'),
                ('خرید مورد انتظار', 'expected_purchase'),
                ('وضعیت موجودی', 'inventory_status'),
                ('برخورد بازاریاب', 'agent_behavior'),
                ('برخورد موزع', 'distributor_behavior'),
                ('رضایتمندی مشتری', 'customer_satisfaction'),
                ('تحقق هدف سرکشی', 'target_achievement'),
                ('نیاز به پیگیری', 'need_followup'),
                ('تاریخ مراجعه بعدی', 'next_visit_date')
            ]

            for label, key in fields:
                value = visit.get(key, '')
                row = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(4))
                row.add_widget(RTLLabel(
                    text=f'{label}:',
                    size_hint_x=0.4,
                    size_hint_y=None,
                    height=dp(30),
                    font_size=sp(20),
                    color=(1, 1, 1, 1)
                ))
                row.add_widget(RTLLabel(
                    text=str(value) if value else '---',
                    size_hint_x=0.6,
                    size_hint_y=None,
                    height=dp(30),
                    font_size=sp(20),
                    color=(0.8, 0.8, 0.8, 1)
                ))
                table_container.add_widget(row)

            text_fields = [
                ('توضیحات سوپروایزر', 'supervisor_note'),
                ('نظرات مشتری', 'customer_feedback'),
                ('نظریه سوپروایزر', 'supervisor_opinion')
            ]

            for label, key in text_fields:
                value = visit.get(key, '')
                if value:
                    row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))
                    row.add_widget(RTLLabel(
                        text=f'{label}:',
                        size_hint_x=0.4,
                        size_hint_y=None,
                        height=dp(40),
                        font_size=sp(20),
                        color=(1, 1, 1, 1)
                    ))
                    row.add_widget(RTLLabel(
                        text=value,
                        size_hint_x=0.6,
                        size_hint_y=None,
                        height=dp(40),
                        font_size=sp(20),
                        color=(0.8, 0.8, 0.8, 1)
                    ))
                    table_container.add_widget(row)

            total_height = 32
            total_height += len(fields) * 30
            for label, key in text_fields:
                if visit.get(key, ''):
                    total_height += 40
            total_height += 20

            table_container.height = total_height
            main_box.add_widget(table_container)

            scroll = ScrollView(
                do_scroll_x=False,
                do_scroll_y=True,
                size_hint_y=0.8
            )
            scroll.add_widget(main_box)
            content.add_widget(scroll)

            close_btn = PersianButton(
                text='بستن',
                background_color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(45),
                color=(1, 1, 1, 1),
                font_size=sp(22)
            )
            content.add_widget(close_btn)

            popup = PersianPopup(
                title='جزئیات سرکشی',
                content=content,
                size_hint=(0.92, 0.8),
                background_color=(0.08, 0.08, 0.08, 1),
                auto_dismiss=False
            )

            close_btn.bind(on_press=popup.dismiss)
            popup.open()

        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش جزئیات: {e}", error_details)

    # ============================================================
    # تب ۴: گزارشات
    # ============================================================

    def show_reports_tab(self):
        """تب گزارشات - مشابه ReportScreen"""
        try:
            content = BoxLayout(orientation='vertical', padding=dp(15))
            content.add_widget(RTLLabel(
                text='تب گزارشات',
                size_hint_y=None,
                height=dp(50),
                font_size=sp(22),
                color=(0.4, 0.7, 1, 1)
            ))
            content.add_widget(RTLLabel(
                text='(در حال توسعه)',
                size_hint_y=None,
                height=dp(40),
                font_size=sp(18),
                color=(0.5, 0.5, 0.5, 1)
            ))
            self.content_area.add_widget(content)

        except Exception as e:
            error_details = traceback.format_exc()
            ErrorPopup.show_error(f"خطا در نمایش تب گزارشات: {e}", error_details)

    # ============================================================
    # توابع عمومی
    # ============================================================

    def go_back(self, instance):
        self.manager.current = 'login'

    def show_message(self, title, message):
        try:
            content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            with content.canvas.before:
                Color(0.12, 0.12, 0.12, 1)
                content_rect = Rectangle(pos=content.pos, size=content.size)
                content.bind(pos=lambda i, v: setattr(content_rect, 'pos', v),
                           size=lambda i, v: setattr(content_rect, 'size', v))

            msg_label = RTLMessageLabel(
                text=message,
                font_size=sp(22) if len(message) < 100 else sp(18),
                color=(1, 1, 1, 1),
                height=dp(250)
            )
            content.add_widget(msg_label)

            btn = PersianButton(
                text='باشه',
                size_hint_y=None,
                height=dp(55),
                font_size=sp(22),
                color=(1, 1, 1, 1),
                background_color=(0.2, 0.6, 1, 1)
            )
            content.add_widget(btn)

            popup = PersianPopup(
                title=title,
                content=content,
                size_hint=(0.9, 0.6),
                background_color=(0.08, 0.08, 0.08, 1)
            )
            btn.bind(on_press=popup.dismiss)
            popup.open()

        except Exception as e:
            print(f"خطا در نمایش پیام: {e}")