#define MyAppName "Voxnote"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Voxnote"
#define MyAppExeName "TranscritorLocal.exe"

[Setup]
AppId={{695C51DF-B730-4E51-B2D7-93F1457758D2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\TranscritorLocal
DefaultGroupName={#MyAppName}
OutputDir=output
OutputBaseFilename=TranscritorLocal-Setup-{#MyAppVersion}-win64
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
WizardStyle=modern
SetupIconFile=..\assets\branding\voxnote-app-icon.ico
SetupLogging=yes

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Files]
Source: "..\dist\TranscritorLocal\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos:"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  Result := IsWin64;
  if not Result then
    MsgBox('Este aplicativo requer Windows 10/11 de 64 bits.', mbError, MB_OK);
end;
