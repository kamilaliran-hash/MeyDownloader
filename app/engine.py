"""In-app updater for the download engine (yt-dlp).

Sites like Facebook, Instagram and YouTube change often, and yt-dlp ships fixes
every few weeks. Instead of rebuilding the app, MeyDownloader downloads the
official platform-independent yt-dlp release (a Python zip) into its own storage
and loads it in place of the built-in copy on the next launch.

install_override() must run BEFORE anything imports yt_dlp.
"""
import importlib.abc
import importlib.machinery
import json
import os
import shutil
import ssl
import sys
import time
import urllib.request
import zipfile

IS_ANDROID = "ANDROID_ARGUMENT" in os.environ or "ANDROID_PRIVATE" in os.environ
LATEST_API = "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest"
ZIP_URL = "https://github.com/yt-dlp/yt-dlp/releases/download/{tag}/yt-dlp"
CHECK_EVERY = 24 * 3600


def engine_dir():
    base = os.environ.get("ANDROID_PRIVATE") if IS_ANDROID else \
        os.path.join(os.path.expanduser("~"), "MeyDownloader")
    d = os.path.join(base, "engine")
    os.makedirs(d, exist_ok=True)
    return d


ZIP_PATH = lambda: os.path.join(engine_dir(), "yt-dlp.zip")
STATE_PATH = lambda: os.path.join(engine_dir(), "state.json")


def _state():
    try:
        with open(STATE_PATH()) as f:
            return json.load(f)
    except Exception:
        return {}


def _save_state(**kw):
    s = _state()
    s.update(kw)
    with open(STATE_PATH(), "w") as f:
        json.dump(s, f)


# ---------------------------------------------------------------- loading
class _ZipFirstFinder(importlib.abc.MetaPathFinder):
    """Serve yt_dlp (and yt_dlp_ejs if bundled) from the downloaded zip, ahead of
    the built-in / PyInstaller-frozen copy."""

    def __init__(self, zpath, packages):
        self.zpath = zpath
        self.packages = packages

    def find_spec(self, fullname, path=None, target=None):
        top = fullname.split(".", 1)[0]
        if top not in self.packages:
            return None
        search = [self.zpath] if "." not in fullname else path
        return importlib.machinery.PathFinder.find_spec(fullname, search)


_finder = None


def install_override():
    """Use the downloaded engine if present and healthy. Returns its version or None."""
    global _finder
    zpath = ZIP_PATH()
    if not os.path.isfile(zpath):
        return None
    try:
        with zipfile.ZipFile(zpath) as z:
            names = {n.split("/", 1)[0] for n in z.namelist()}
        packages = {p for p in ("yt_dlp", "yt_dlp_ejs") if p in names}
        if "yt_dlp" not in packages:
            raise ValueError("not a yt-dlp zip")
        _finder = _ZipFirstFinder(zpath, packages)
        sys.meta_path.insert(0, _finder)
        import yt_dlp  # noqa: F401  (verify it really loads)
        from yt_dlp.version import __version__
        return __version__
    except Exception:
        remove_override(delete=True)
        return None


def remove_override(delete=False):
    global _finder
    if _finder in sys.meta_path:
        sys.meta_path.remove(_finder)
    _finder = None
    for m in [m for m in sys.modules if m == "yt_dlp" or m.startswith(("yt_dlp.", "yt_dlp_ejs"))]:
        del sys.modules[m]
    if delete:
        try:
            os.remove(ZIP_PATH())
        except Exception:
            pass


# ---------------------------------------------------------------- updating
def _ctx():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "MeyDownloader"})
    return urllib.request.urlopen(req, timeout=timeout, context=_ctx())


def current_version():
    try:
        from yt_dlp.version import __version__
        return __version__
    except Exception:
        return "?"


def check_and_update(force=False):
    """Download a newer yt-dlp if one exists. Returns (status, message) where
    status is 'updated', 'current', 'skipped' or 'error'."""
    if not force and time.time() - _state().get("last_check", 0) < CHECK_EVERY:
        return "skipped", ""
    try:
        with _get(LATEST_API) as r:
            tag = json.load(r)["tag_name"]
        _save_state(last_check=time.time())
        have = _state().get("downloaded") or current_version()
        if tag.lstrip("v") <= have:
            return "current", f"Download engine is up to date ({have})."

        tmp = ZIP_PATH() + ".part"
        with _get(ZIP_URL.format(tag=tag), timeout=120) as r, open(tmp, "wb") as f:
            shutil.copyfileobj(r, f)
        with zipfile.ZipFile(tmp) as z:  # sanity check
            if not any(n.startswith("yt_dlp/") for n in z.namelist()):
                raise ValueError("downloaded file is not yt-dlp")
        os.replace(tmp, ZIP_PATH())
        _save_state(downloaded=tag)
        return "updated", f"Download engine updated to {tag}. Restart the app to use it."
    except Exception as e:
        return "error", f"Engine update failed: {e}"


def reset():
    """Go back to the built-in engine on next launch (if an update misbehaves)."""
    try:
        os.remove(ZIP_PATH())
    except Exception:
        pass
    _save_state(downloaded=None, last_check=0)
