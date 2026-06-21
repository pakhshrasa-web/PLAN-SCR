[app]

title = Plan Android
package.name = planandroid
package.domain = org.pakhshrasa

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json
source.exclude_exts = spec,log,pyc,pyo
source.exclude_dirs = tests, bin, buildozer, .git, .github

version = 1.0.0

# ====== نسخه پایدار و تست شده برای بیلد اندروید ======
requirements = python3==3.9.10,kivy==2.1.0,kivymd==1.1.1,pyjnius==1.5.0,android,openpyxl,jdatetime,arabic-reshaper,python-bidi,requests,plyer,reportlab

orientation = portrait
fullscreen = 0
logcat = True

# ====== تنظیمات اندروید - نسخه پایدار ======
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE
android.api = 31
android.minapi = 21
android.sdk = 31
android.ndk = 23b
android.archs = armeabi-v7a, arm64-v8a
android.accept_sdk_license = True
android.logcat_filters = *:S python:D
android.gradle_plugin_version = 7.4.0

# ====== غیرفعال کردن دیباگ و فعال کردن ریلیز ======
android.debug = False
android.release = True

android.manifest_extra = <application android:enableOnBackInvokedCallback="true" />
android.gradle = True

# ====== قفل کردن نسخه p4a برای جلوگیری از خطا ======
p4a.url = https://github.com/kivy/python-for-android/archive/refs/tags/2022.7.1.tar.gz
