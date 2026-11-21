@echo off
REM Local Windows build: produces dist\MeyDownloader.exe and Output\MeyDownloader-Setup.exe
REM Needs: Python 3.11 (64-bit) and Inno Setup 6 installed. Run from the project root.
setlocal
cd /d "%~dp0\.."

python -m pip install --upgrade pip
python -m pip install -r requirements-desktop.txt || exit /b 1

if not exist windows\bin mkdir windows\bin
if not exist windows\bin\ffmpeg.exe (
  echo Downloading ffmpeg...
  powershell -Command "Invoke-WebRequest https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip -OutFile ff.zip; Expand-Archive ff.zip ffx -Force; Copy-Item ffx\*\bin\ffmpeg.exe,ffx\*\bin\ffprobe.exe windows\bin\; Remove-Item ff.zip,ffx -Recurse"
)
if not exist windows\bin\deno.exe (
  echo Downloading deno...
  powershell -Command "Invoke-WebRequest https://github.com/denoland/deno/releases/latest/download/deno-x86_64-pc-windows-msvc.zip -OutFile deno.zip; Expand-Archive deno.zip windows\bin -Force; Remove-Item deno.zip"
)

pyinstaller --noconfirm windows\meydownloader.spec || exit /b 1

set ISCC="%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist %ISCC% (
  %ISCC% windows\installer.iss
) else (
  echo Inno Setup not found - skipping installer. Get it from https://jrsoftware.org/isdl.php
)
echo.
echo Done. EXE: dist\MeyDownloader.exe   Installer: Output\MeyDownloader-Setup.exe
