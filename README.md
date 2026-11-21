# MeyDownloader

**Owner / Developer:** Kamil  ·  © 2026 Kamil. All rights reserved.

Download video as **MP4** at any available resolution, or audio as **MP3** at 128, 192 or 320 kbps, from:

**YouTube · Facebook · X/Twitter · Instagram · TikTok · Reddit · Vimeo · Threads · Dailymotion · SoundCloud · Twitch · Bilibili · Pinterest · LinkedIn**, plus 1000+ other sites supported by yt-dlp.

One Kivy codebase runs on Windows and Android.

## Features
- Paste a link and the app shows which site it's from (e.g. "Detected: Instagram")
- Lists the real resolutions each video has, with estimated file sizes, plus a "Best available" option
- Audio-only links such as SoundCloud switch to MP3 automatically
- **Private or login-only posts:**
  - Windows: under "Login cookies", pick the browser you're logged in with. Firefox is the most reliable, because Chrome and Edge lock their cookies while they're running.
  - Both platforms: put an exported `cookies.txt` (Netscape format) in `%USERPROFILE%\MeyDownloader\` on Windows, or in `Download/MeyDownloader/` on Android
- **Android:** use the Share button in YouTube, Facebook, X, Instagram or TikTok, choose MeyDownloader, and the link is fetched automatically

## Get the builds (GitHub Actions)
1. Push this folder to the `main` branch of a GitHub repo.
2. Open the **Actions** tab and wait for "Build MeyDownloader" to finish.
3. Download the artifacts:
   - `windows`: `MeyDownloader.exe` (portable, single file) and `MeyDownloader-Setup.exe` (installer, recommended because it starts faster)
   - `android`: `meydownloader-1.2.3-arm64-v8a-debug.apk`
4. To publish a GitHub Release, run `git tag v1.2.3 && git push --tags`.

## Build locally
- **Windows:** install Python 3.11 (64-bit) and Inno Setup 6, then run `windows\build_windows.bat`.
- **Android (Linux/WSL):** see the `android` job in `.github/workflows/build.yml`, then run `buildozer android debug`.

## App size
- **Slim ffmpeg** (`tools/build_ffmpeg_slim.sh`): the app only converts audio to MP3 and copies video streams into MP4 (it never re-encodes video). So ffmpeg is built with just those parts, making it about 3–6 MB instead of about 80–130 MB, with the same speed.
- **The installer uses folder mode**, so the app no longer unpacks itself to a temp folder on every launch. Startup is faster than with the single-file exe.
- **Unused Python and Kivy modules are excluded**, and the installer uses maximum LZMA compression.
- **No UPX packing.** It saves little and often triggers antivirus false alarms.
- If a site ever fails because a codec is missing, rerun the workflow from the Actions tab with **ffmpeg = full**.

## Logo
The `assets/` folder holds `icon.png` (1024 px), `icon512.png`, `icon.ico` and `presplash.png`.

## Android troubleshooting
- If something goes wrong at start-up, the app now shows the error on screen with a **Copy error** button instead of closing.
- Files are prepared in the app's private storage, then saved to **Download/MeyDownloader** through Android's MediaStore. That needs no storage permission on Android 10 and newer.
- Logs and `cookies.txt` live in `Android/data/com.meydownloader.meydownloader/files/`.

## Notes
- Sites change often. Rebuild every so often to pick up the latest yt-dlp.
- Instagram photo-only posts aren't supported (yt-dlp downloads video and audio only).
- The APK is debug-signed, so allow "Install unknown apps" to sideload it.
- Only download content you own or have permission to download.
