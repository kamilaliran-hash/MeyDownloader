"""MeyDownloader launcher (owner: Kamil).

Crash diagnostics (Android): if the app cannot start, the error is written to
    Download/MeyDownloader/crash-log.txt
using only Android APIs (no Kivy needed), so it works even if Kivy itself fails.
Native crashes are recorded with faulthandler and exported on the next launch.
"""
import os
import sys
import time
import traceback

IS_ANDROID = "ANDROID_ARGUMENT" in os.environ or "ANDROID_PRIVATE" in os.environ
PRIVATE = os.environ.get("ANDROID_PRIVATE") or os.path.dirname(os.path.abspath(__file__))
FAULT_LOG = os.path.join(PRIVATE, "fault.log")
RUN_LOG = os.path.join(PRIVATE, "run.log")


class _NullStream:
    """The windowed .exe has no console: give Python harmless stdout/stderr."""
    encoding = "utf-8"

    def write(self, s):
        return len(s) if isinstance(s, str) else 0

    def flush(self):
        pass

    def isatty(self):
        return False

    def fileno(self):
        import io
        raise io.UnsupportedOperation("no console")


for _name in ("stdout", "stderr"):
    if not hasattr(getattr(sys, _name, None), "write"):
        setattr(sys, _name, _NullStream())


# ---------------------------------------------------------------- Android export
def _export_to_downloads(text, name="crash-log.txt"):
    """Write text to the public Download/MeyDownloader folder (no Kivy needed)."""
    if not IS_ANDROID:
        try:
            with open(os.path.join(os.path.expanduser("~"), "meydownloader_" + name), "w",
                      encoding="utf-8") as f:
                f.write(text)
        except Exception:
            pass
        return
    try:
        from jnius import autoclass
        act = autoclass("org.kivy.android.PythonActivity").mActivity
        sdk = autoclass("android.os.Build$VERSION").SDK_INT
        if sdk >= 29:
            Downloads = autoclass("android.provider.MediaStore$Downloads")
            Cols = autoclass("android.provider.MediaStore$MediaColumns")
            ContentValues = autoclass("android.content.ContentValues")
            cv = ContentValues()
            cv.put(Cols.DISPLAY_NAME, name)
            cv.put(Cols.MIME_TYPE, "text/plain")
            cv.put(Cols.RELATIVE_PATH, "Download/MeyDownloader")
            uri = act.getContentResolver().insert(Downloads.EXTERNAL_CONTENT_URI, cv)
            pfd = act.getContentResolver().openFileDescriptor(uri, "w")
            with os.fdopen(pfd.detachFd(), "w", encoding="utf-8") as f:
                f.write(text)
        else:
            d = "/storage/emulated/0/Download/MeyDownloader"
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, name), "w", encoding="utf-8") as f:
                f.write(text)
    except Exception:
        try:
            with open(os.path.join(PRIVATE, name), "w", encoding="utf-8") as f:
                f.write(text + "\n\nExport failed:\n" + traceback.format_exc())
        except Exception:
            pass


def _device_info():
    lines = [f"MeyDownloader crash report  {time.strftime('%Y-%m-%d %H:%M:%S')}",
             f"Python {sys.version}"]
    if IS_ANDROID:
        try:
            from jnius import autoclass
            B, V = autoclass("android.os.Build"), autoclass("android.os.Build$VERSION")
            lines.append(f"Device {B.MANUFACTURER} {B.MODEL}, Android {V.RELEASE} (SDK {V.SDK_INT})")
        except Exception as e:
            lines.append(f"(device info unavailable: {e})")
    return "\n".join(lines)


def _read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return ""


def _export_previous_native_crash():
    """faulthandler output from a hard crash last time -> Downloads."""
    fault = _read(FAULT_LOG).strip()
    if fault:
        _export_to_downloads(_device_info() + "\n\n=== Native crash (previous launch) ===\n"
                             + fault + "\n\n=== Last log lines ===\n" + _read(RUN_LOG)[-20000:])
    for p in (FAULT_LOG,):
        try:
            os.remove(p)
        except Exception:
            pass


# ---------------------------------------------------------------- crash screen
def _show_crash(text):
    from kivy.app import App
    from kivy.core.clipboard import Clipboard
    from kivy.metrics import dp
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.button import Button
    from kivy.uix.label import Label
    from kivy.uix.scrollview import ScrollView

    class CrashApp(App):
        title = "MeyDownloader - error"

        def build(self):
            root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
            root.add_widget(Label(text="[b]MeyDownloader could not start[/b]\n"
                                       "Saved to Download/MeyDownloader/crash-log.txt",
                                  markup=True, size_hint_y=None, height=dp(56)))
            sv = ScrollView()
            lbl = Label(text=text, font_size="11sp", size_hint_y=None, halign="left",
                        valign="top")
            lbl.bind(width=lambda w, v: setattr(w, "text_size", (v, None)),
                     texture_size=lambda w, v: setattr(w, "height", v[1]))
            sv.add_widget(lbl)
            root.add_widget(sv)
            root.add_widget(Button(text="Copy error", size_hint_y=None, height=dp(48),
                                   on_release=lambda *_: Clipboard.copy(text)))
            return root

    CrashApp().run()


def _start():
    if IS_ANDROID:
        # Tee everything printed (incl. Kivy's log) into run.log
        try:
            log = open(RUN_LOG, "w", encoding="utf-8", buffering=1)

            class _Tee:
                def __init__(self, a):
                    self.a = a
                def write(self, s):
                    try:
                        log.write(s)
                    except Exception:
                        pass
                    return self.a.write(s)
                def flush(self):
                    try:
                        log.flush()
                    except Exception:
                        pass
                    self.a.flush()
                def __getattr__(self, n):
                    return getattr(self.a, n)

            sys.stdout, sys.stderr = _Tee(sys.stdout), _Tee(sys.stderr)
        except Exception:
            pass
        _export_previous_native_crash()
        try:
            import faulthandler
            faulthandler.enable(open(FAULT_LOG, "w"), all_threads=True)
        except Exception:
            pass

    try:
        import engine
        v = engine.install_override()
        print(f"[MeyDownloader] engine: {'updated ' + v if v else 'built-in'}")
    except Exception:
        traceback.print_exc()

    try:
        print("[MeyDownloader] importing UI")
        from ui import MeyDownloaderApp
        print("[MeyDownloader] starting app")
        MeyDownloaderApp().run()
    except BaseException as e:
        if isinstance(e, SystemExit) and not e.code:
            return
        tb = _device_info() + "\n\n" + traceback.format_exc() + \
            "\n=== Log ===\n" + _read(RUN_LOG)[-20000:]
        _export_to_downloads(tb)
        try:
            _show_crash(tb)
        except BaseException:
            _export_to_downloads(tb + "\n\nCrash screen failed too:\n" + traceback.format_exc(),
                                 "crash-log-2.txt")


if __name__ == "__main__":
    os.environ.setdefault("KIVY_NO_ARGS", "1")
    if len(sys.argv) >= 4 and sys.argv[1] == "--login":
        # Windows login window (separate process, see desktop_login.py)
        import desktop_login
        desktop_login.run(sys.argv[2], sys.argv[3])
        sys.exit(0)
    _start()
