"""In-app login for Windows (Facebook, Instagram, X, TikTok).

Runs in its own process (MeyDownloader.exe --login <site> <out.json>) because
the browser window (pywebview + Microsoft Edge WebView2) needs the main thread,
which Kivy already uses in the main app. The window closes by itself as soon as
the login cookie appears; the cookies are written to out.json in Netscape
cookies.txt format and merged by the main app. Nothing leaves the PC.
"""
import json
import os
import sys
import time
from email.utils import parsedate_to_datetime

# site: (login page, cookie domain, cookie that proves you are logged in)
SITES = {
    "Facebook": ("https://www.facebook.com/login/", "facebook.com", "c_user"),
    "Instagram": ("https://www.instagram.com/accounts/login/", "instagram.com", "sessionid"),
    "X / Twitter": ("https://x.com/i/flow/login", "x.com", "auth_token"),
    "TikTok": ("https://www.tiktok.com/login", "tiktok.com", "sessionid"),
}


def storage_dir():
    d = os.path.join(os.path.expanduser("~"), "MeyDownloader", "webview")
    os.makedirs(d, exist_ok=True)
    return d


def _expiry(value):
    try:
        if value:
            return str(int(parsedate_to_datetime(value).timestamp()))
    except Exception:
        pass
    return str(int(time.time()) + 180 * 24 * 3600)


def _to_netscape(cookies, domain):
    lines, names = [], set()
    for c in cookies or []:
        for name, m in c.items():
            dom = m["domain"] or "." + domain
            if domain not in dom:
                continue
            if not dom.startswith("."):
                dom = "." + dom
            lines.append("\t".join([dom, "TRUE", m["path"] or "/",
                                    "TRUE" if m["secure"] else "FALSE",
                                    _expiry(m["expires"]), name, m.value]))
            names.add(name)
    return lines, names


def run(site, out_path):
    import webview

    url, domain, key = SITES[site]
    result = {"ok": False, "domain": "." + domain, "lines": []}
    window = webview.create_window(f"Log in to {site} - MeyDownloader", url,
                                   width=520, height=780)

    def watch(win):
        while True:
            time.sleep(1.5)
            try:
                lines, names = _to_netscape(win.get_cookies(), domain)
            except Exception:
                return                      # window was closed
            if lines:
                result["lines"] = lines
            if key in names:
                result["ok"] = True
                time.sleep(1.0)             # let the site finish setting cookies
                try:
                    result["lines"] = _to_netscape(win.get_cookies(), domain)[0] or lines
                except Exception:
                    pass
                win.destroy()
                return

    gui = "edgechromium" if os.name == "nt" else None
    webview.start(watch, window, gui=gui, private_mode=False, storage_path=storage_dir())

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f)


def logout():
    import shutil
    shutil.rmtree(storage_dir(), ignore_errors=True)


def launch_command(site, out_path):
    """Command that starts this login window in a separate process."""
    if getattr(sys, "frozen", False):
        return [sys.executable, "--login", site, out_path]
    main = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
    return [sys.executable, main, "--login", site, out_path]
