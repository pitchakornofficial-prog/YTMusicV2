#define MyAppName "TYMusicV2"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "TYMusicV2"
#define MyAppExeName "TYMusicV2.exe"

[Setup]
AppId={{8A5E6D31-4B7A-4E95-9D1C-6B4F3F5A21C8}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}

OutputDir=installer
OutputBaseFilename=TYMusicV2-Setup

Compression=lzma
SolidCompression=yes

WizardStyle=modern

PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; \
    Description: "Create a desktop shortcut"; \
    GroupDescription: "Additional shortcuts:"; \
    Flags: unchecked

[Files]
Source: "dist\TYMusicV2.exe"; \
    DestDir: "{app}"; \
    Flags: ignoreversion

[Icons]
Name: "{group}\TYMusicV2"; \
    Filename: "{app}\TYMusicV2.exe"

Name: "{autodesktop}\TYMusicV2"; \
    Filename: "{app}\TYMusicV2.exe"; \
    Tasks: desktopicon

[UninstallDelete]
Type: filesandordirs; \
    Name: "{app}"