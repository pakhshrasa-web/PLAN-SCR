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

# (list) List of exclusions using pattern matching
# source.exclude_patterns = license,images/*.jpg

# (str) Application versioning (method 1)
version = 1.0.0

# (str) Application versioning (method 2)
# version.regex = __version__ = ['"](.*)['"]
# version.filename = %(source.dir)s/main.py

# (list) Application requirements
# python3==3.10.9 برای سازگاری با pyjnius
requirements = python3==3.10.9,kivy==2.2.1,kivymd==1.1.1,pyjnius==1.6.0,android,openpyxl,jdatetime,arabic-reshaper,python-bidi,requests,plyer,reportlab

# (str) Custom source folders for requirements
# requirements.source.kivy = ../../kivy

# (list) Garden requirements
# garden_requirements =

# (str) Presplash of the application
# presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
# icon.filename = %(source.dir)s/data/icon.png

# (str) Supported orientation (one of landscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (bool) Run with logcat module (android only)
logcat = True

# ------ Android specific ------

# (list) Permissions
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION

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

# (str) Android NDK directory (if empty, it will be downloaded)
# android.ndk_path =

# (str) Android SDK directory (if empty, it will be downloaded)
# android.sdk_path =

# (str) Android ANT directory (if empty, it will be downloaded)
# android.ant_path =

# (bool) If True, then skip trying to update the Android sdk
# android.skip_update = False

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

# (str) Android keystore file (for release mode)
# android.keystore = %(source.dir)s/keystore.jks
# android.keystore_password = your_password
# android.keyalias = your_alias
# android.keyalias_password = your_password

# (str) Android permission to add to the manifest (optional)
# android.permission_extra =

# (str) Android manifest extra (optional)
android.manifest_extra = <application android:enableOnBackInvokedCallback="true" />

# (bool) Use Android packaging with Gradle (recommended)
android.gradle = True

# (bool) Use Android packaging with Gradle to use the Java 8 features
# android.gradle_java_version = 8

# (bool) Enable/disable RTL support
# android.enable_rtl = True

# ------ iOS specific ------

# (str) iOS bundle identifier (com.yourcompany.myapp)
# ios.bundle = com.yourcompany.myapp

# (str) iOS bundle name (MyApp)
# ios.bundle_name = MyApp

# (list) iOS requirements
# ios.requirements = kivy, kivymd

# (str) iOS framework (kivy or kivymd)
# ios.framework = kivy

# (str) iOS deploy target version
# ios.deployment_target = 13.0

# (bool) Use iPhone X specific features
# ios.use_iphone_x_features = True

# ------ Python-for-Android (p4a) specific ------

# (str) python-for-android branch to use (default = master)
# p4a.branch = master

# (str) python-for-android git url (default = https://github.com/kivy/python-for-android)
# p4a.url = https://github.com/kivy/python-for-android

# (str) python-for-android local directory (optional)
# p4a.source_dir =

# (list) Additional p4a recipes (optional)
# p4a.recipes =

# (bool) Use a custom build directory for p4a
# p4a.local_recipes =

# ------ Buildozer specific ------

# (bool) Log the output of the build process
buildozer.log_level = 2

# (bool) Display the logcat output from the device (android only)
buildozer.logcat = True

# (str) Path to the device to use for logcat (android only)
# buildozer.logcat_device =

# (bool) Wipe the build directory before building
buildozer.wipe = False

# (bool) Use a remote buildozer server
# buildozer.remote = False

# (str) Remote buildozer server URL
# buildozer.remote_url = https://buildozer.herokuapp.com/

# (str) Remote buildozer server status URL
# buildozer.remote_status_url =

# (str) Remote buildozer server build ID
# buildozer.remote_build_id =

# (bool) Run the application on the device after build
buildozer.run = False

# (str) ADB command to use
# buildozer.adb = adb

# (bool) Try to use the Android SDK provided by the system
# buildozer.use_system_sdk = False