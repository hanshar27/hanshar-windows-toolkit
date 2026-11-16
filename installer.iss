; Inno Setup Script
; For Windows installer generation

[Setup]
AppName=Hanshar Windows Toolkit
AppVersion=1.0.0
DefaultDirName={autopf}\Hanshar Windows Toolkit
DefaultGroupName=Hanshar Windows Toolkit
OutputBaseFilename=HansharWindowsToolkit-Setup
Compression=lzma
SolidCompression=yes
UninstallDisplayIcon={app}\HansharWindowsToolkit.exe
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
AppPublisher=Hanshar
AppId={{A2D2812C-8D31-4A8C-9F77-43A3EC78EA7A}}
SetupIconFile=assets\app_icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\HansharWindowsToolkit.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "config.json"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Hanshar Windows Toolkit"; Filename: "{app}\HansharWindowsToolkit.exe"
Name: "{commondesktop}\Hanshar Windows Toolkit"; Filename: "{app}\HansharWindowsToolkit.exe"

[Run]
Filename: "{app}\HansharWindowsToolkit.exe"; Description: "Launch Hanshar Windows Toolkit"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{uninstallexe}"; Parameters: "/VERYSILENT"; Flags: runhidden
