# PyInstaller spec for MeyDownloader. Run from the project root:
#   pyinstaller windows/meydownloader.spec             -> dist/MeyDownloader/      (folder, used by installer)
#   set MD_ONEFILE=1 & pyinstaller windows/meydownloader.spec -> dist/MeyDownloader.exe (portable single file)
import os
from kivy_deps import sdl2, glew, angle
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = os.path.abspath(".")
BIN = os.path.join(ROOT, "windows", "bin")
ONEFILE = os.environ.get("MD_ONEFILE") == "1"
ICON = os.path.join(ROOT, "windows", "icon.ico")

binaries = [(os.path.join(BIN, f), ".") for f in os.listdir(BIN)
            if f.lower().endswith((".exe", ".dll"))]

# Modules the app never uses (pure size savings, no effect on speed)
EXCLUDES = [
    "numpy", "cv2", "PIL", "docutils", "pygments", "IPython", "jedi",
    "unittest", "pydoc", "pydoc_data", "doctest", "lib2to3", "idlelib",
    "xmlrpc", "distutils", "setuptools", "pip", "test", "ensurepip",
    "kivy.tests", "kivy.tools", "kivy.lib.gstplayer", "kivy.core.video",
    "kivy.core.audio", "kivy.core.camera", "kivy.core.spelling", "kivy.garden",
    "kivy.uix.video", "kivy.uix.videoplayer", "kivy.uix.camera",
    "kivy.uix.rst", "kivy.uix.codeinput",
    "yt_dlp.__pyinstaller", "Cryptodome.SelfTest",
]

a = Analysis(
    [os.path.join(ROOT, "app", "main.py")],
    pathex=[os.path.join(ROOT, "app")],
    binaries=binaries,
    datas=[(os.path.join(ROOT, "app", "logo.png"), ".")]
          + collect_data_files("yt_dlp_ejs") + collect_data_files("certifi"),
    hiddenimports=collect_submodules("yt_dlp", filter=lambda m: "__pyinstaller" not in m)
                  + collect_submodules("yt_dlp_ejs")
                  + ["tkinter", "tkinter.filedialog"],
    excludes=EXCLUDES,
    optimize=1,          # strips asserts only; safe
)
pyz = PYZ(a.pure)
kivy_trees = [Tree(p) for p in (sdl2.dep_bins + glew.dep_bins + angle.dep_bins)]
common = dict(name="MeyDownloader", console=False, upx=False, icon=ICON,
              version=os.path.join(ROOT, "windows", "version_info.txt"))

if ONEFILE:
    exe = EXE(pyz, a.scripts, a.binaries, a.datas, *kivy_trees, **common)
else:
    exe = EXE(pyz, a.scripts, [], exclude_binaries=True, **common)
    coll = COLLECT(exe, a.binaries, a.datas, *kivy_trees, upx=False, name="MeyDownloader")
