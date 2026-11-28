"""MeyDownloader - download video (MP4) or audio (MP3) from YouTube, Facebook,
X/Twitter, Instagram, TikTok and 1000+ other sites. Kivy UI for Windows and Android."""
import os
import sys
import threading


from kivy.app import App
from kivy.clock import mainthread
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.base import ExceptionHandler, ExceptionManager

import core
import engine
from kivy.properties import StringProperty

HERE = os.path.dirname(os.path.abspath(__file__))

KV = """
#:import dp kivy.metrics.dp
<Lbl@Label>:
    size_hint_y: None
    height: dp(26)
    halign: "left"
    valign: "middle"
    text_size: self.size
    color: 0.78, 0.76, 0.88, 1
    font_size: "14sp"

<Btn@Button>:
    background_normal: ""
    background_down: ""
    background_color: 0.22, 0.18, 0.34, 1
    size_hint_y: None
    height: dp(46)

BoxLayout:
    orientation: "vertical"
    padding: dp(16)
    spacing: dp(9)
    canvas.before:
        Color:
            rgba: 0.067, 0.047, 0.118, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        size_hint_y: None
        height: dp(64)
        spacing: dp(12)
        Image:
            source: app.logo
            size_hint_x: None
            width: dp(56)
            fit_mode: "contain"
        BoxLayout:
            orientation: "vertical"
            Label:
                text: "[b]MeyDownloader[/b]"
                markup: True
                font_size: "24sp"
                halign: "left"
                valign: "bottom"
                text_size: self.size
            Label:
                text: "YouTube · Facebook · X · Instagram · TikTok · 1000+ sites"
                font_size: "12sp"
                color: 0.93, 0.45, 0.75, 1
                halign: "left"
                valign: "top"
                text_size: self.size
        Btn:
            text: "About"
            size_hint: None, None
            size: dp(64), dp(38)
            pos_hint: {"center_y": .5}
            on_release: app.show_about()

    BoxLayout:
        size_hint_y: None
        height: dp(26)
        Lbl:
            text: "Video / post link"
        Label:
            id: badge
            text: ""
            markup: True
            font_size: "13sp"
            halign: "right"
            valign: "middle"
            text_size: self.size
            color: 0.55, 0.85, 1, 1
    BoxLayout:
        size_hint_y: None
        height: dp(46)
        spacing: dp(8)
        TextInput:
            id: url
            hint_text: "Paste a YouTube, Facebook, X, Instagram... link"
            multiline: False
            write_tab: False
            font_size: "15sp"
            padding: dp(10), dp(12)
            on_text: app.on_url(self.text)
            on_text_validate: app.fetch()
        Btn:
            text: "Paste"
            size_hint_x: None
            width: dp(76)
            on_release: app.paste()

    BoxLayout:
        id: cookie_row
        size_hint_y: None
        height: dp(42)
        spacing: dp(8)
        Lbl:
            text: "Or use cookies from browser:"
            height: dp(42)
        Spinner:
            id: cookies
            text: "None"
            values: app.cookie_browsers
            size_hint_x: None
            width: dp(120)

    BoxLayout:
        id: android_cookie_row
        size_hint_y: None
        height: dp(42)
        spacing: dp(8)
        Btn:
            id: cookie_import
            text: "Log in"
            height: dp(42)
            background_color: 0.15, 0.45, 0.85, 1
            on_release: app.show_login_menu()
        Btn:
            text: "Import file"
            size_hint_x: None
            width: dp(100)
            height: dp(42)
            on_release: app.import_cookies()
        Btn:
            text: "Log out"
            size_hint_x: None
            width: dp(86)
            height: dp(42)
            on_release: app.clear_cookies()

    Btn:
        id: fetch_btn
        text: "Fetch info"
        background_color: 0.486, 0.227, 0.929, 1
        on_release: app.fetch()

    Label:
        id: title
        text: ""
        size_hint_y: None
        height: dp(44)
        bold: True
        text_size: self.width, None
        halign: "left"
        shorten: True
        shorten_from: "right"

    BoxLayout:
        size_hint_y: None
        height: dp(46)
        spacing: dp(8)
        ToggleButton:
            id: mp4
            text: "MP4  (video)"
            group: "mode"
            state: "down"
            allow_no_selection: False
            on_state: if self.state == "down": app.set_mode("mp4")
        ToggleButton:
            id: mp3
            text: "MP3  (audio)"
            group: "mode"
            allow_no_selection: False
            on_state: if self.state == "down": app.set_mode("mp3")

    Lbl:
        id: choice_lbl
        text: "Resolution"
    Spinner:
        id: choice
        text: "Fetch info first"
        values: []
        size_hint_y: None
        height: dp(46)

    Lbl:
        text: "Save to"
    BoxLayout:
        size_hint_y: None
        height: dp(46)
        spacing: dp(8)
        TextInput:
            id: folder
            multiline: False
            font_size: "13sp"
            padding: dp(10), dp(13)
        Btn:
            id: browse
            text: "Browse"
            size_hint_x: None
            width: dp(76)
            on_release: app.browse()

    Btn:
        id: dl_btn
        text: "Download"
        height: dp(54)
        font_size: "18sp"
        disabled: True
        background_color: 0.925, 0.282, 0.6, 1
        on_release: app.start_download()

    ProgressBar:
        id: bar
        max: 1
        value: 0
        size_hint_y: None
        height: dp(18)
    ScrollView:
        do_scroll_x: False
        Label:
            id: status
            text: "Paste a link and tap Fetch info."
            text_size: self.width, None
            size_hint_y: None
            height: max(self.texture_size[1], dp(30))
            halign: "center"
            valign: "top"
            color: 0.72, 0.7, 0.8, 1
    Label:
        text: app.footer
        size_hint_y: None
        height: dp(20)
        font_size: "11sp"
        color: 0.5, 0.47, 0.6, 1
"""

ABOUT = """
#:import dp kivy.metrics.dp
BoxLayout:
    orientation: "vertical"
    padding: dp(16)
    spacing: dp(10)
    Image:
        source: app.logo
        size_hint_y: None
        height: dp(88)
        fit_mode: "contain"
    Label:
        text: app.about_text
        markup: True
        halign: "center"
        valign: "middle"
        text_size: self.width, None
        size_hint_y: None
        height: self.texture_size[1] + dp(8)
    Label:
        id: engine_lbl
        text: app.engine_text
        font_size: "12sp"
        color: 0.55, 0.85, 1, 1
        size_hint_y: None
        height: dp(40)
        text_size: self.width, None
        halign: "center"
    BoxLayout:
        size_hint_y: None
        height: dp(46)
        spacing: dp(8)
        Button:
            text: "Update download engine"
            on_release: app.update_engine(force=True)
        Button:
            text: "Reset"
            size_hint_x: None
            width: dp(80)
            on_release: app.reset_engine()
    Widget:
"""


class MeyDownloaderApp(App):
    title = "MeyDownloader"
    icon = os.path.join(HERE, "logo.png")
    logo = os.path.join(HERE, "logo.png")
    cookie_browsers = core.COOKIE_BROWSERS
    engine_text = StringProperty("")
    footer = f"v{core.VERSION}  ·  Owner: {core.OWNER}  ·  © 2026 {core.OWNER}"
    about_text = (
        f"[size=22sp][b]MeyDownloader[/b][/size]\nVersion {core.VERSION}\n\n"
        f"[b]Owner / Developer:[/b] {core.OWNER}\n{core.COPYRIGHT}\n\n"
        "Download video (MP4) or audio (MP3) from YouTube, Facebook,\n"
        "X/Twitter, Instagram, TikTok and 1000+ other sites.\n\n"
        "[size=12sp]Powered by yt-dlp and FFmpeg.\n"
        "Only download content you own or have permission to use.[/size]"
    )

    def build(self):
        if not core.IS_ANDROID:
            Window.size = (dp(540), dp(760))
        self.mode = "mp4"
        self.resolutions = []
        self.resolved_url = None
        self.engine_text = f"Download engine: yt-dlp {engine.current_version()}"
        root = Builder.load_string(KV)
        self.ids = root.ids
        ExceptionManager.add_handler(_KeepAlive(self))
        if core.IS_ANDROID:
            root.ids.folder.text = "Download/MeyDownloader  (phone storage)"
            root.ids.folder.readonly = True
            hide = (root.ids.browse, root.ids.cookie_row)
        else:
            root.ids.folder.text = core.default_download_dir()
            hide = ()
        self._refresh_cookie_label()
        for w in hide:
            w.opacity, w.disabled = 0, True
            if w is not root.ids.browse:
                w.height = 0
        return root

    def on_start(self):
        # Android-only work runs after the window is up, and can never crash the app
        if core.IS_ANDROID:
            self._android_permissions()
            self._read_shared_link()
        self.update_engine(force=False)   # silent daily check

    # ------------------------------------------------------------ engine
    def update_engine(self, force=True):
        if force:
            self.engine_text = "Checking for engine update..."
        def work():
            status, msg = engine.check_and_update(force=force)
            if force or status == "updated":
                self._engine_msg(msg or "No update needed.")
        threading.Thread(target=work, daemon=True).start()

    @mainthread
    def _engine_msg(self, msg):
        self.engine_text = msg
        self.status(msg)

    def reset_engine(self):
        engine.reset()
        self._engine_msg("Engine reset to built-in version. Restart the app.")

    # ------------------------------------------------------------ cookies (Android)
    def _refresh_cookie_label(self):
        sites = core.logged_in_sites()
        self.ids.cookie_import.text = ("Logged in: " + ", ".join(sites)) if sites else "Log in"

    def clear_cookies(self):
        core.clear_cookies()
        try:
            if core.IS_ANDROID:
                import android_login
                android_login.clear_webview_cookies()
            else:
                import desktop_login
                desktop_login.logout()
        except Exception:
            pass
        self._refresh_cookie_label()
        self.status("Logged out of all sites.")

    def show_login_menu(self):
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button
        from kivy.uix.label import Label
        from kivy.uix.popup import Popup
        box = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(8))
        box.add_widget(Label(text="Log in so private, group and friends-only\n"
                                  "videos can be downloaded. Your login stays\n"
                                  "on this phone only.", halign="center",
                             size_hint_y=None, height=dp(72)))
        if not core.IS_ANDROID:
            box.children[0].text = ("Log in so private, group and friends-only\n"
                                    "videos can be downloaded. Your login stays\n"
                                    "on this PC only.")
        pop = Popup(title="Log in to...", content=box, size_hint=(0.9, None), height=dp(440))
        for site in ("Facebook", "Instagram", "X / Twitter", "TikTok"):
            b = Button(text=site, size_hint_y=None, height=dp(52))
            b.bind(on_release=lambda _b, s=site: (pop.dismiss(), self.open_login(s)))
            box.add_widget(b)
        pop.open()

    def open_login(self, site):
        if not core.IS_ANDROID:
            return self._desktop_login(site)
        try:
            import android_login
            self.status(f"Log in to {site}, then tap 'Done' at the top.")
            android_login.open_login(site, self._login_closed)
        except Exception as e:
            self.status(f"Cannot open login page: {e}")

    def _desktop_login(self, site):
        import subprocess
        import tempfile
        import desktop_login
        self.status(f"A login window opened. Log in to {site} - it closes by itself when done.")

        def work():
            out = os.path.join(tempfile.gettempdir(), "meydownloader_login.json")
            try:
                if os.path.exists(out):
                    os.remove(out)
                subprocess.run(desktop_login.launch_command(site, out), timeout=1800)
                import json
                with open(out, encoding="utf-8") as f:
                    res = json.load(f)
                if not res.get("lines"):
                    return self._cookie_done(f"No {site} login found. Try again.")
                core.merge_cookie_lines(res["domain"], res["lines"])
                os.remove(out)
                msg = (f"Logged in to {site}. Tap Fetch info again." if res.get("ok") else
                       f"Login window closed - saved what {site} gave us. Tap Fetch info.")
                self._cookie_done(msg)
            except FileNotFoundError:
                self._cookie_done("Login window closed before logging in.")
            except Exception as e:
                self._cookie_done(f"Login failed: {e}")
        threading.Thread(target=work, daemon=True).start()

    def _login_closed(self, site):
        # called on Android's UI thread
        if not site:
            return self._cookie_done("Login cancelled.")
        try:
            import android_login
            domain, lines = android_login.collect_cookies(site)
            if not lines:
                return self._cookie_done(f"No {site} login found. Please log in, then tap Done.")
            core.merge_cookie_lines(domain, lines)
            self._cookie_done(f"Logged in to {site}. Tap Fetch info again.")
        except Exception as e:
            self._cookie_done(f"Saving login failed: {e}")

    def import_cookies(self):
        if not core.IS_ANDROID:
            try:
                import tkinter as tk
                from tkinter import filedialog
                r = tk.Tk(); r.withdraw()
                path = filedialog.askopenfilename(title="Choose cookies.txt",
                                                  filetypes=[("Cookies", "*.txt"), ("All", "*.*")])
                r.destroy()
                if path:
                    with open(path, encoding="utf-8", errors="replace") as f:
                        core.save_cookies_text(f.read())
                    self._cookie_done("Cookies imported.")
            except Exception as e:
                self.status(f"Cookie import failed: {e}")
            return
        try:
            from android import activity
            from jnius import autoclass
            Intent = autoclass("android.content.Intent")
            intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
            intent.addCategory(Intent.CATEGORY_OPENABLE)
            intent.setType("*/*")
            activity.bind(on_activity_result=self._on_cookie_file)
            autoclass("org.kivy.android.PythonActivity").mActivity.startActivityForResult(
                intent, 4242)
        except Exception as e:
            self.status(f"Cannot open file picker: {e}")

    def _on_cookie_file(self, request, result, data):
        if request != 4242:
            return
        try:
            from android import activity
            activity.unbind(on_activity_result=self._on_cookie_file)
        except Exception:
            pass
        if result != -1 or data is None:     # -1 = RESULT_OK
            return
        try:
            from jnius import autoclass
            act = autoclass("org.kivy.android.PythonActivity").mActivity
            pfd = act.getContentResolver().openFileDescriptor(data.getData(), "r")
            with os.fdopen(pfd.detachFd(), "r", encoding="utf-8", errors="replace") as f:
                core.save_cookies_text(f.read())
            self._cookie_done("Cookies imported. Private/login-only posts should work now.")
        except Exception as e:
            self._cookie_done(f"Cookie import failed: {e}")

    @mainthread
    def _cookie_done(self, msg):
        self._refresh_cookie_label()
        self.status(msg)

    # ------------------------------------------------------------ helpers
    def _android_permissions(self):
        # Only Android 9 and older need a storage permission; newer versions
        # save through MediaStore, which needs none.
        try:
            if core.android_sdk() < 29:
                from android.permissions import request_permissions, Permission
                request_permissions([Permission.WRITE_EXTERNAL_STORAGE,
                                     Permission.READ_EXTERNAL_STORAGE])
        except Exception:
            pass

    def _read_shared_link(self):
        """Pick up a link sent via Android's Share menu."""
        try:
            from jnius import autoclass
            Intent = autoclass("android.content.Intent")
            intent = autoclass("org.kivy.android.PythonActivity").mActivity.getIntent()
            if intent.getAction() == Intent.ACTION_SEND:
                text = intent.getStringExtra(Intent.EXTRA_TEXT) or ""
                link = next((w for w in text.split() if w.startswith("http")), "")
                if link:
                    self.ids.url.text = link
                    self.fetch()
        except Exception:
            pass

    @property
    def cookie_choice(self):
        return "None" if core.IS_ANDROID else self.ids.cookies.text

    @mainthread
    def status(self, text, frac=None):
        self.ids.status.text = text
        if frac is not None:
            self.ids.bar.value = frac

    @mainthread
    def busy(self, on):
        self.ids.fetch_btn.disabled = on
        self.ids.dl_btn.disabled = on or not self.resolutions

    def on_url(self, text):
        self.resolved_url = None
        site = core.detect_platform(text.strip())
        self.ids.badge.text = f"Detected: {site}" if site else ""
        if self.resolutions:
            self.resolutions = []
            self.ids.title.text = ""
            self.set_mode(self.mode)
            self.ids.dl_btn.disabled = True

    def paste(self):
        from kivy.core.clipboard import Clipboard
        self.ids.url.text = (Clipboard.paste() or "").strip()

    def browse(self):
        try:
            import tkinter as tk
            from tkinter import filedialog
            r = tk.Tk(); r.withdraw()
            d = filedialog.askdirectory(initialdir=self.ids.folder.text)
            r.destroy()
            if d:
                self.ids.folder.text = d
        except Exception:
            self.status("Type the folder path into the box.")

    def set_mode(self, mode):
        self.mode = mode
        if mode == "mp3":
            self.ids.choice_lbl.text = "MP3 quality (kbps)"
            self.ids.choice.values = core.MP3_QUALITIES
            self.ids.choice.text = "192"
        else:
            self.ids.choice_lbl.text = "Resolution"
            self.ids.choice.values = self.resolutions
            self.ids.choice.text = self.resolutions[0] if self.resolutions else "Fetch info first"

    def show_about(self):
        from kivy.uix.popup import Popup
        Popup(title="About", content=Builder.load_string(ABOUT),
              size_hint=(0.92, None), height=dp(580),
              separator_color=(0.925, 0.282, 0.6, 1)).open()

    # ------------------------------------------------------------ actions
    def fetch(self):
        url = self.ids.url.text.strip()
        if not url.startswith("http"):
            return self.status("Please paste a valid link (starting with http).")
        self.busy(True)
        self.status("Fetching info...", 0)
        threading.Thread(target=self._fetch, args=(url, self.cookie_choice),
                         daemon=True).start()

    def _fetch(self, url, cookies):
        try:
            info = core.fetch_info(url, cookies)
            self._fetched(info)
            self.status("Choose format and quality, then tap Download.")
        except Exception as e:
            self.status(f"Error: {e}")
        finally:
            self.busy(False)

    @mainthread
    def _fetched(self, info):
        self.resolutions = info["resolutions"]
        self.resolved_url = info.get("url")
        dur = info["duration"]
        mins = f"  ({int(dur)//60}:{int(dur)%60:02d})" if dur else ""
        self.ids.title.text = f"[{info['site']}]  {info['title']}{mins}"
        if not info["has_video"]:      # audio-only sites like SoundCloud
            self.ids.mp3.state = "down"
        self.set_mode(self.mode)

    def start_download(self):
        url = self.resolved_url or self.ids.url.text.strip()
        folder = core.work_dir() if core.IS_ANDROID else self.ids.folder.text.strip()
        try:
            os.makedirs(folder, exist_ok=True)
        except Exception as e:
            return self.status(f"Cannot use folder: {e}")
        self.busy(True)
        self.status("Starting...", 0)
        threading.Thread(target=self._download,
                         args=(url, self.mode, self.ids.choice.text, folder, self.cookie_choice),
                         daemon=True).start()

    def _download(self, url, mode, choice, folder, cookies):
        try:
            path = core.download(url, mode, choice, folder,
                                 progress_cb=lambda f, t: self.status(t, f),
                                 cookie_browser=cookies)
            if core.IS_ANDROID:
                self.status("Saving to Download/MeyDownloader...", 1)
                path = core.publish_android(path)
            self.status(f"Done! Saved to:\n{path}", 1)
        except Exception as e:
            core.write_error_log() if "details:" not in str(e) else None
            self.status(f"Error: {e}")
        finally:
            self.busy(False)



class _KeepAlive(ExceptionHandler):
    """Any error inside a button/callback is shown instead of closing the app."""
    def __init__(self, app):
        super().__init__()
        self.app = app

    def handle_exception(self, inst):
        import traceback
        try:
            core.write_error_log()
            self.app.status(f"Error: {inst}")
        except Exception:
            pass
        return ExceptionManager.PASS
