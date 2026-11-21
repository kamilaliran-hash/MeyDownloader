@echo off
REM Local Windows build for MeyDownloader (owner: Kamil)
REM Produces: dist-portable\MeyDownloader.exe and Output\MeyDownloader-Setup.exe
REM Needs: Python 3.11 (64-bit) and Inno Setup 6. Run from anywhere.
REM Tip: for the small build, put the slim ffmpeg.exe/ffprobe.exe from the GitHub
REM "ffmpeg-windows" artifact into windows\bin first; otherwise the full ffmpeg is downloaded.
setlocal
cd /d "%~dp0\.."

python -m pip install -r requirements-desktop.txt || exit /b 1
if not exist windows\bin mkdir windows\bin

if not exist windows\bin\ffmpeg.exe (
  echo Downloading full ffmpeg...
  powershell -Command "Invoke-WebRequest https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip -OutFile ff.zip; Expand-Archive ff.zip ffx -Force; Copy-Item ffx\*\bin\ffmpeg.exe,ffx\*\bin\ffprobe.exe windows\bin\; Remove-Item ff.zip,ffx -Recurse"
)
if not exist windows\bin\deno.exe (
  echo Downloading deno...
  powershell -Command "Invoke-WebRequest https://github.com/denoland/deno/releases/latest/download/deno-x86_64-pc-windows-msvc.zip -OutFile deno.zip; Expand-Archive deno.zip windows\bin -Force; Remove-Item deno.zip"
)

pyinstaller --noconfirm windows\meydownloader.spec || exit /b 1
set MD_ONEFILE=1
pyinstaller --noconfirm --workpath build-onefile --distpath dist-portable windows\meydownloader.spec || exit /b 1
set MD_ONEFILE=

set ISCC="%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist %ISCC% (%ISCC% windows\installer.iss) else (echo Inno Setup not found - skipping installer.)
echo.
echo Done. Portable: dist-portable\MeyDownloader.exe   Installer: Output\MeyDownloader-Setup.exe
