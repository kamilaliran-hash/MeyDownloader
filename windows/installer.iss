; Inno Setup script - builds Output/MeyDownloader-Setup.exe
; Compile:  iscc windows\installer.iss   (after PyInstaller has produced dist\MeyDownloader.exe)

#define AppName "MeyDownloader"
#define AppVersion "1.3.0"

[Setup]
AppId={{3F7A2D91-6C4E-4E1B-A8D5-2B9C7E04F6A3}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Kamil
AppCopyright=© 2026 Kamil. All rights reserved.
VersionInfoCompany=Kamil
VersionInfoVersion=1.3.0
VersionInfoDescription=MeyDownloader Setup
DefaultDirName={autopf}\MeyDownloader
DefaultGroupName={#AppName}
OutputDir=..\Output
OutputBaseFilename=MeyDownloader-Setup
Compression=lzma2/ultra64
LZMAUseSeparateProcess=yes
LZMADictionarySize=65536
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\MeyDownloader.exe
SetupIconFile=icon.ico

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"

[Files]
Source: "..\dist\MeyDownloader\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\MeyDownloader.exe"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\MeyDownloader.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\MeyDownloader.exe"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent
