"""MeyDownloader download logic (wraps yt-dlp, which supports 1000+ sites)."""
import os
import re
import sys
import shutil
import traceback

import yt_dlp

APP_NAME = "MeyDownloader"
VERSION = "1.2.0"
OWNER = "Kamil"
COPYRIGHT = "© 2026 Kamil. All rights reserved."
IS_ANDROID = "ANDROID_ARGUMENT" in os.environ or "ANDROID_PRIVATE" in os.environ
MP3_QUALITIES = ["320", "192", "128"]
BEST = "Best available"
COOKIE_BROWSERS = ["None", "firefox", "chrome", "edge", "brave", "opera"]

PLATFORMS = [
    (r"(youtube\.com|youtu\.be)", "YouTube"),
    (r"(facebook\.com|fb\.watch|fb\.com)", "Facebook"),
    (r"(twitter\.com|x\.com)", "X / Twitter"),
    (r"instagram\.com", "Instagram"),
    (r"tiktok\.com", "TikTok"),
    (r"(reddit\.com|redd\.it)", "Reddit"),
    (r"vimeo\.com", "Vimeo"),
    (r"dailymotion\.com", "Dailymotion"),
    (r"soundcloud\.com", "SoundCloud"),
    (r"twitch\.tv", "Twitch"),
    (r"(threads\.net|threads\.com)", "Threads"),
    (r"pinterest\.", "Pinterest"),
    (r"bilibili\.", "Bilibili"),
    (r"linkedin\.com", "LinkedIn"),
]


class _QuietLogger:
    """Routes all yt-dlp output here so it never touches sys.stdout/stderr
    (they don't exist in the windowed .exe, which caused "'str'/'NoneType'
    object has no attribute 'write'")."""
    def __init__(self):
        self.lines = []

    def _add(self, msg):
        self.lines = (self.lines + [str(msg)])[-200:]

    def debug(self, msg):
        self._add(msg)

    info = warning = debug

    def error(self, msg):
        self._add("ERROR: " + str(msg))


def log_dir():
    if IS_ANDROID:
        return default_download_dir()
    d = os.path.join(os.path.expanduser("~"), APP_NAME)
    os.makedirs(d, exist_ok=True)
    return d


def write_error_log(logger=None):
    """Save the full traceback + yt-dlp output; returns the log path."""
    path = os.path.join(log_dir(), "error.log")
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"{APP_NAME} {VERSION} / yt-dlp {yt_dlp.version.__version__}\n\n")
            f.write(traceback.format_exc())
            if logger and logger.lines:
                f.write("\n--- yt-dlp output ---\n" + "\n".join(logger.lines))
    except Exception:
        pass
    return path


def detect_platform(url):
    for pattern, name in PLATFORMS:
        if re.search(pattern, url, re.I):
            return name
    return "Other site" if url.startswith("http") else ""


# ---------------------------------------------------------------- helpers
def _bundle_dir():
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "windows", "bin")


def _android_native_dir():
    from jnius import autoclass
    act = autoclass("org.kivy.android.PythonActivity").mActivity
    return act.getApplicationInfo().nativeLibraryDir


def _android_files_dir():
    from jnius import autoclass
    act = autoclass("org.kivy.android.PythonActivity").mActivity
    return act.getFilesDir().getAbsolutePath()


def cookies_file_path():
    """Optional Netscape cookies.txt for private/login-only posts."""
    if IS_ANDROID:
        return os.path.join(default_download_dir(), "cookies.txt")
    return os.path.join(os.path.expanduser("~"), APP_NAME, "cookies.txt")


def base_options(cookie_browser="None"):
    """yt-dlp options: bundled ffmpeg, JS runtime and optional login cookies."""
    opts = {
        "quiet": True,
        "noplaylist": True,
        "no_warnings": True,
        "noprogress": True,          # progress comes from our hook, not the console
        "consoletitle": False,
        "no_color": True,
        "logger": _QuietLogger(),
    }
    if IS_ANDROID:
        d = _android_native_dir()
        ff, qjs = os.path.join(d, "libffmpeg.so"), os.path.join(d, "libqjs.so")
        if os.path.exists(ff):
            opts["ffmpeg_location"] = ff
        if os.path.exists(qjs):
            opts["js_runtimes"] = {"quickjs": {"path": qjs}}
        opts["cachedir"] = os.path.join(_android_files_dir(), "yt-dlp-cache")
    else:
        d = os.path.abspath(_bundle_dir())
        exe = ".exe" if os.name == "nt" else ""
        if os.path.exists(os.path.join(d, "ffmpeg" + exe)):
            opts["ffmpeg_location"] = d
        elif shutil.which("ffmpeg"):
            opts["ffmpeg_location"] = os.path.dirname(shutil.which("ffmpeg"))
        deno = os.path.join(d, "deno" + exe)
        if os.path.exists(deno):
            opts["js_runtimes"] = {"deno": {"path": deno}}
        elif shutil.which("deno") is None and shutil.which("node"):
            opts["js_runtimes"] = {"node": {}}
        if cookie_browser and cookie_browser != "None":
            opts["cookiesfrombrowser"] = (cookie_browser,)

    cf = cookies_file_path()
    if "cookiesfrombrowser" not in opts and os.path.isfile(cf):
        opts["cookiefile"] = cf
    return opts


def default_download_dir():
    if IS_ANDROID:
        try:
            from android.storage import primary_external_storage_path
            base = os.path.join(primary_external_storage_path(), "Download")
        except Exception:
            base = "/storage/emulated/0/Download"
    else:
        base = os.path.join(os.path.expanduser("~"), "Downloads")
    path = os.path.join(base, APP_NAME)
    os.makedirs(path, exist_ok=True)
    return path


def _human(n):
    if not n:
        return "?"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def _friendly_error(e, url):
    msg = re.sub(r"\x1b\[[0-9;]*m", "", str(e)).replace("ERROR: ", "")
    low = msg.lower()
    if any(k in low for k in ("login", "log in", "sign in", "cookies", "private",
                              "rate-limit", "authentication", "not available")):
        hint = ("Pick your browser under 'Login cookies' (be logged in there)"
                if not IS_ANDROID else
                f"Put an exported cookies.txt in {default_download_dir()}")
        return f"{msg}\n\nThis post may need a login. {hint}."
    if "unsupported url" in low:
        return "This link isn't supported. Use a direct link to the video/post."
    return msg


# ---------------------------------------------------------------- API
def fetch_info(url, cookie_browser="None"):
    """Return dict: title, duration, site, resolutions[], has_video."""
    opts = {**base_options(cookie_browser), "skip_download": True}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        write_error_log(opts["logger"])
        raise RuntimeError(_friendly_error(e, url)) from None

    if info.get("_type") == "playlist" and info.get("entries"):
        # e.g. multi-video X/Instagram posts: use the first item
        info = next(iter(info["entries"]))

    formats = info.get("formats") or [info]
    audio_size = max((f.get("filesize") or f.get("filesize_approx") or 0
                      for f in formats
                      if f.get("vcodec") == "none" and f.get("acodec") != "none"), default=0)
    best, has_video = {}, False
    for f in formats:
        if f.get("vcodec") == "none":
            continue
        has_video = has_video or f.get("vcodec") is not None or bool(f.get("height"))
        h = f.get("height")
        if not h:
            continue
        size = f.get("filesize") or f.get("filesize_approx") or 0
        if f.get("acodec") == "none":
            size += audio_size
        best[h] = max(best.get(h, 0), size)

    resolutions = [BEST] + [f"{h}p  (~{_human(best[h])})" for h in sorted(best, reverse=True)]
    return {
        "title": info.get("title") or info.get("id") or "media",
        "duration": info.get("duration"),
        "site": info.get("extractor_key") or detect_platform(url),
        "resolutions": resolutions,
        "has_video": has_video or bool(best),
        "url": info.get("webpage_url") or url,
    }


def download(url, mode, choice, out_dir, progress_cb=None, cookie_browser="None"):
    """mode 'mp3' (choice = kbps) or 'mp4' (choice = 'Best available' / '1080p ...')."""
    result = {}

    def hook(d):
        if not progress_cb:
            return
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            frac = d.get("downloaded_bytes", 0) / total if total else 0
            speed = (d.get("_speed_str") or "").strip()
            progress_cb(frac, f"Downloading {frac*100:.0f}%  {speed}")
        elif d["status"] == "finished":
            progress_cb(1.0, "Processing...")

    def pp_hook(d):
        if d["status"] == "finished":
            result["path"] = d["info_dict"].get("filepath")

    opts = {
        **base_options(cookie_browser),
        "outtmpl": os.path.join(out_dir, "%(title).120B [%(id)s].%(ext)s"),
        "progress_hooks": [hook],
        "postprocessor_hooks": [pp_hook],
        "windowsfilenames": True,
        "trim_file_name": 180,
    }
    if "ffmpeg_location" not in opts:
        raise RuntimeError("ffmpeg not found - it is required for MP3 and HD MP4.")

    if mode == "mp3":
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": choice},
            {"key": "FFmpegMetadata"},
        ]
    else:
        if choice.startswith(BEST) or not choice[:1].isdigit():
            opts["format"] = "bv*[vcodec^=avc1]+ba[ext=m4a]/bv*+ba/b"
        else:
            h = int(choice.split("p")[0])
            opts["format"] = (
                f"bv*[height<={h}][vcodec^=avc1]+ba[ext=m4a]/"
                f"bv*[height<={h}][ext=mp4]+ba[ext=m4a]/"
                f"bv*[height<={h}]+ba/b[height<={h}]/bv*+ba/b"
            )
        opts["merge_output_format"] = "mp4"
        opts["remux_video"] = "mp4"
        opts["postprocessors"] = [{"key": "FFmpegMetadata"}]

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info.get("_type") == "playlist" and info.get("entries"):
                info = next(iter(info["entries"]))
            path = result.get("path") or ydl.prepare_filename(info)
    except Exception as e:
        log = write_error_log(opts["logger"])
        raise RuntimeError(f"{_friendly_error(e, url)}\n(details: {log})") from None

    if mode == "mp3":
        path = os.path.splitext(path)[0] + ".mp3"
    return path
