[app]
title = Plan Android
package.name = planandroid
package.domain = org.pakhshrasa
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json

# ⚠️ نسخه با GitHub Run Number به‌روز می‌شود
version = 1.0.${env:GITHUB_RUN_NUMBER}

# ⚠️ بدون requests - فقط کتابخانه‌های ضروری
requirements = python3,kivy,openpyxl,arabic-reshaper,python-bidi,Pillow,jdatetime

orientation = portrait
fullscreen = 1
icon.filename = icon/kivy-icon-512.png
presplash.filename = icon/kivy-icon-512.png

[buildozer]
log_level = 2
warn_on_root = 1

[buildozer:android]
android.api = 34
android.minapi = 21
android.ndk = 25b
android.sdk_path = /home/runner/.buildozer/android/platform/android-sdk
android.accept_sdk_license = True
android.archs = armeabi-v7a, arm64-v8a
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, MANAGE_EXTERNAL_STORAGE
android.enable_androidx = True
android.allow_backup = True
android.debug = 0
android.release = 1
android.version_code = ${env:GITHUB_RUN_NUMBER}
