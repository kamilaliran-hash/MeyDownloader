[app]
title = MeyDownloader
package.name = meydownloader
package.domain = com.meydownloader
source.dir = app
source.include_exts = py,png,jpg,kv
version = 1.2.1

requirements = python3,kivy==2.3.1,yt-dlp,yt-dlp-ejs,certifi,pyjnius,android,openssl

icon.filename = assets/icon512.png
presplash.filename = assets/presplash.png
android.presplash_color = #110C1E

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,(name=android.permission.WRITE_EXTERNAL_STORAGE;maxSdkVersion=28),(name=android.permission.READ_EXTERNAL_STORAGE;maxSdkVersion=32)
android.api = 34
android.minapi = 24
android.archs = arm64-v8a
android.accept_sdk_license = True
android.allow_backup = True

# Lets you "Share" a link from YouTube/Facebook/X/Instagram/TikTok straight into MeyDownloader
android.manifest.intent_filters = android_intent_filters.xml

# Static ffmpeg + QuickJS binaries packaged as "native libs" so Android lets us execute them
android.add_libs_arm64_v8a = android_libs/arm64-v8a/*.so

p4a.branch = v2024.01.21

[buildozer]
log_level = 2
warn_on_root = 0
