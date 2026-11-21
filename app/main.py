"""MeyDownloader - download video (MP4) or audio (MP3) from YouTube, Facebook,
X/Twitter, Instagram, TikTok and 1000+ other sites. Kivy UI for Windows and Android."""
import os
import threading

from kivy.app import App
from kivy.clock import mainthread
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp

import core

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
            text: "Login cookies (private posts):"
            height: dp(42)
        Spinner:
            id: cookies
            text: "None"
            values: app.cookie_browsers
            size_hint_x: None
            width: dp(120)

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
    Label:
        id: status
        text: "Paste a link and tap Fetch info."
        text_size: self.width, None
        halign: "center"
        color: 0.72, 0.7, 0.8, 1
    Widget:
"""


class MeyDownloaderApp(App):
    title = "MeyDownloader"
    icon = os.path.join(HERE, "logo.png")
    logo = os.path.join(HERE, "logo.png")
    cookie_browsers = core.COOKIE_BROWSERS

    def build(self):
        if not core.IS_ANDROID:
            Window.size = (dp(540), dp(760))
        self.mode = "mp4"
        self.resolutions = []
        root = Builder.load_string(KV)
        self.ids = root.ids
        root.ids.folder.text = core.default_download_dir()
        if core.IS_ANDROID:
            for w in (root.ids.browse, root.ids.cookie_row):
                w.opacity, w.disabled = 0, True
            root.ids.cookie_row.height = 0
            self._android_permissions()
            self._read_shared_link()
        return root

    # ------------------------------------------------------------ helpers
    def _android_permissions(self):
        try:
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
        dur = info["duration"]
        mins = f"  ({int(dur)//60}:{int(dur)%60:02d})" if dur else ""
        self.ids.title.text = f"[{info['site']}]  {info['title']}{mins}"
        if not info["has_video"]:      # audio-only sites like SoundCloud
            self.ids.mp3.state = "down"
        self.set_mode(self.mode)

    def start_download(self):
        url = self.ids.url.text.strip()
        folder = self.ids.folder.text.strip()
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
            self._media_scan(path)
            self.status(f"Done! Saved to:\n{path}", 1)
        except Exception as e:
            self.status(f"Error: {e}")
        finally:
            self.busy(False)

    def _media_scan(self, path):
        if not core.IS_ANDROID:
            return
        try:
            from jnius import autoclass
            act = autoclass("org.kivy.android.PythonActivity").mActivity
            autoclass("android.media.MediaScannerConnection").scanFile(act, [path], None, None)
        except Exception:
            pass


if __name__ == "__main__":
    MeyDownloaderApp().run()
