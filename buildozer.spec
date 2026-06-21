[app]

# (str) Title of your application
title = Plan Android

# (str) Package name
package.name = planandroid

# (str) Package domain (needed for android/ios packaging)
package.domain = org.pakhshrasa

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,ttf,json

# (list) List of inclusions using pattern matching
# source.include_patterns = assets/*, images/*.png

# (list) Source files to exclude (let empty to not exclude anything)
source.exclude_exts = spec,log,pyc,pyo

# (list) List of directory names to not include at all
source.exclude_dirs = tests, bin, buildozer, .git, .github

# (str) Application versioning (method 1)
version = 1.0.0

# (list) Application requirements
requirements = python3==3.10.9,kivy==2.2.1,kivymd==1.1.1,pyjnius==1.6.0,android,openpyxl,jdatetime,arabic-reshaper,python-bidi,requests,plyer,reportlab

# (str) Python version
android.python_version = 3.10.9

# (str) Supported orientation (one of landscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (bool) Run with logcat module (android only)
logcat = True

# ------ Android specific ------

# (list) Permissions
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# (int) Android API to use
android.api = 33

# (int) Minimum API required
android.minapi = 21

# (int) Android SDK version
android.sdk = 33

# (str) Android NDK version to use
android.ndk = 25b

# (list) Android architectures to build for
android.archs = armeabi-v7a, arm64-v8a

# (bool) If True, then automatically accept SDK license
android.accept_sdk_license = True

# (str) Android entry point, default is ok for Kivy-based app
# android.entrypoint = org.kivy.android.PythonActivity

# (str) Android app theme, default is ok for Kivy-based app
# android.apptheme = "@android:style/Theme.NoTitleBar"

# (list) Android additional Java code to include (optional)
# android.add_src =

# (str) Android logcat filters to use
android.logcat_filters = *:S python:D

# (bool) Copy library instead of making a libpymodules.so
# android.copy_libs = 1

# (str) Android Gradle dependencies (optional)
# android.gradle_dependencies =

# (str) Android Gradle repository (optional)
# android.gradle_repositories =

# (str) Android Gradle plugin version (optional)
android.gradle_plugin_version = 8.4.0

# (bool) Enable/disable Android Java debugger
android.debug = False

# (bool) Enable/disable Android release mode (sign the APK)
android.release = True

# (str) Android permission to add to the manifest (optional)
# android.permission_extra =

# (str) Android manifest extra (optional)
android.manifest_extra = <application android:enableOnBackInvokedCallback="true" />

# (bool) Use Android packaging with Gradle (recommended)
android.gradle = True

# (bool) Enable/disable RTL support
# android.enable_rtl = True
