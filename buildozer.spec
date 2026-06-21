[app]

title = Plan Android
package.name = planandroid
package.domain = org.pakhshrasa

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json
source.exclude_exts = spec,log,pyc,pyo
source.exclude_dirs = tests, bin, buildozer, .git, .github

version = 1.0.0

# ====== استفاده از پایتون 3.10 با نسخه‌های سازگار ======
requirements = python3==3.10.9,kivy==2.2.1,kivymd==1.1.1,pyjnius==1.6.0,android,openpyxl,jdatetime,arabic-reshaper,python-bidi,requests,plyer,reportlab

orientation = portrait
fullscreen = 0
logcat = True

# ====== تنظیمات اندروید - به‌روز ======
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25c
android.archs = armeabi-v7a, arm64-v8a
android.accept_sdk_license = True
android.logcat_filters = *:S python:D
android.gradle_plugin_version = 8.4.0

# ====== غیرفعال کردن دیباگ و فعال کردن ریلیز ======
android.debug = False
android.release = True

android.manifest_extra = <application android:enableOnBackInvokedCallback="true" />
android.gradle = True

# ====== مهم: استفاده از شاخه master p4a ======
p4a.branch = master
