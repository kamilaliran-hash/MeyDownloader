"""MeyDownloader launcher (owner: Kamil).
Starts the app; if anything fails during start-up, shows the error on screen
(with a Copy button) instead of letting the app close."""
import os
import sys
import traceback


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


def _save_crash(text):
    for d in (os.environ.get("ANDROID_PRIVATE"), os.path.expanduser("~"),
              os.path.dirname(os.path.abspath(__file__))):
        try:
            if d:
                with open(os.path.join(d, "meydownloader_crash.log"), "w", encoding="utf-8") as f:
                    f.write(text)
                return
        except Exception:
            continue


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
                                       "Please send this message to Kamil.",
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


if __name__ == "__main__":
    try:
        from ui import MeyDownloaderApp
        MeyDownloaderApp().run()
    except Exception:
        tb = traceback.format_exc()
        _save_crash(tb)
        _show_crash(tb)
