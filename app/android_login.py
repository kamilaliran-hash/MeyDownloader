"""In-app login for Android (Facebook, Instagram, X, TikTok).

Opens the site's login page in an Android WebView on top of the app. When the
user taps "Done", the WebView's cookies for that site are converted to a
Netscape cookies.txt (the format yt-dlp reads) and merged into the app's
cookie file. Cookies never leave the phone.
"""
import time

from android.runnable import run_on_ui_thread
from jnius import PythonJavaClass, autoclass, java_method

SITES = {
    "Facebook": ("https://m.facebook.com/login/",
                 ["https://www.facebook.com", "https://m.facebook.com"], ".facebook.com"),
    "Instagram": ("https://www.instagram.com/accounts/login/",
                  ["https://www.instagram.com"], ".instagram.com"),
    "X / Twitter": ("https://x.com/i/flow/login", ["https://x.com", "https://twitter.com"], ".x.com"),
    "TikTok": ("https://www.tiktok.com/login", ["https://www.tiktok.com"], ".tiktok.com"),
}

_keep = []  # hold Java objects/listeners so they aren't garbage-collected


class _Click(PythonJavaClass):
    __javainterfaces__ = ["android/view/View$OnClickListener"]
    __javacontext__ = "app"

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    @java_method("(Landroid/view/View;)V")
    def onClick(self, view):
        self.callback()


def _netscape(cookie_header, domain):
    """'a=1; b=2' from CookieManager -> Netscape cookies.txt lines."""
    expiry = str(int(time.time()) + 180 * 24 * 3600)
    lines = []
    for part in (cookie_header or "").split(";"):
        if "=" not in part:
            continue
        name, value = part.strip().split("=", 1)
        lines.append("\t".join([domain, "TRUE", "/", "TRUE", expiry, name, value]))
    return lines


def collect_cookies(site):
    _, urls, domain = SITES[site]
    cm = autoclass("android.webkit.CookieManager").getInstance()
    cm.flush()
    seen, lines = set(), []
    for u in urls:
        for line in _netscape(cm.getCookie(u), domain):
            key = line.split("\t")[5]
            if key not in seen:
                seen.add(key)
                lines.append(line)
    return domain, lines


@run_on_ui_thread
def open_login(site, on_done):
    """Show the login page. on_done(site) is called (UI thread) when user taps Done."""
    url = SITES[site][0]
    act = autoclass("org.kivy.android.PythonActivity").mActivity
    WebView = autoclass("android.webkit.WebView")
    WebViewClient = autoclass("android.webkit.WebViewClient")
    LinearLayout = autoclass("android.widget.LinearLayout")
    Button = autoclass("android.widget.Button")
    LP = autoclass("android.view.ViewGroup$LayoutParams")
    LLP = autoclass("android.widget.LinearLayout$LayoutParams")
    Color = autoclass("android.graphics.Color")
    cm = autoclass("android.webkit.CookieManager").getInstance()

    layout = LinearLayout(act)
    layout.setOrientation(LinearLayout.VERTICAL)
    layout.setBackgroundColor(Color.parseColor("#110C1E"))

    bar = LinearLayout(act)
    bar.setOrientation(LinearLayout.HORIZONTAL)
    done = Button(act)
    done.setText(f"Done - I'm logged in to {site}")
    cancel = Button(act)
    cancel.setText("Cancel")
    bar.addView(done, LLP(0, LP.WRAP_CONTENT, 3.0))
    bar.addView(cancel, LLP(0, LP.WRAP_CONTENT, 1.0))

    web = WebView(act)
    s = web.getSettings()
    s.setJavaScriptEnabled(True)
    s.setDomStorageEnabled(True)
    web.setWebViewClient(WebViewClient())
    cm.setAcceptCookie(True)
    cm.setAcceptThirdPartyCookies(web, True)

    layout.addView(bar, LLP(LP.MATCH_PARENT, LP.WRAP_CONTENT))
    layout.addView(web, LLP(LP.MATCH_PARENT, 0, 1.0))

    def close(saved):
        layout.setVisibility(8)  # View.GONE
        parent = layout.getParent()
        if parent is not None:
            parent.removeView(layout)
        web.destroy()
        _keep.clear()
        on_done(site if saved else None)

    on_ok, on_cancel = _Click(lambda: close(True)), _Click(lambda: close(False))
    done.setOnClickListener(on_ok)
    cancel.setOnClickListener(on_cancel)
    _keep.extend([layout, web, on_ok, on_cancel])

    act.addContentView(layout, LP(LP.MATCH_PARENT, LP.MATCH_PARENT))
    web.loadUrl(url)


@run_on_ui_thread
def clear_webview_cookies():
    cm = autoclass("android.webkit.CookieManager").getInstance()
    cm.removeAllCookies(None)
    cm.flush()
