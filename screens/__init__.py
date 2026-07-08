# screens/__init__.py
# ========== پکیج صفحات ==========

from .login_screen import LoginScreen
from .register_screen import RegisterScreen
from .admin_screen import AdminScreen
from .admin_settings_screen import AdminSettingsScreen
from .user_screen import UserScreen
from .report_screen import ReportScreen
from .settings_login_screen import SettingsLoginScreen
from .debug_screen import DebugScreen
from .agents_screen import AgentsScreen
from .supervisor_screen import SupervisorScreen

__all__ = [
    'LoginScreen',
    'RegisterScreen',
    'AdminScreen',
    'AdminSettingsScreen',
    'UserScreen',
    'ReportScreen',
    'SettingsLoginScreen',
    'DebugScreen',
    'AgentsScreen',
    'SupervisorScreen'
]