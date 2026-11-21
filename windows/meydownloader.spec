# PyInstaller spec - builds dist/MeyDownloader.exe (single file, no console)
# Run from the project root:  pyinstaller windows/meydownloader.spec
import os
from kivy_deps import sdl2, glew, angle
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = os.path.abspath(".")
BIN = os.path.join(ROOT, "windows", "bin")

binaries = [(os.path.join(BIN, f), ".") for f in ("ffmpeg.exe", "ffprobe.exe", "deno.exe")
            if os.path.exists(os.path.join(BIN, f))]

a = Analysis(
    [os.path.join(ROOT, "app", "main.py")],
    pathex=[os.path.join(ROOT, "app")],
    binaries=binaries,
    datas=[(os.path.join(ROOT, "app", "logo.png"), ".")] + collect_data_files("yt_dlp_ejs") + collect_data_files("certifi"),
    hiddenimports=collect_submodules("yt_dlp") + collect_submodules("yt_dlp_ejs")
                  + ["tkinter", "tkinter.filedialog"],
    excludes=["numpy", "PIL.ImageQt", "cv2"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas,
    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins + angle.dep_bins)],
    name="MeyDownloader",
    console=False,
    upx=False,
    icon=os.path.join(ROOT, "windows", "icon.ico") if os.path.exists(os.path.join(ROOT, "windows", "icon.ico")) else None,
)
