#define MyAppName "Voxnote"
#define MyAppVersion "0.1.1"
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
Source: "..\assets\branding\voxnote-app-icon.ico"; DestDir: "{app}\assets\branding"; DestName: "voxnote-app-icon-{#MyAppVersion}.ico"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\branding\voxnote-app-icon-{#MyAppVersion}.ico"; IconIndex: 0
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\branding\voxnote-app-icon-{#MyAppVersion}.ico"; IconIndex: 0; Tasks: desktopicon

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

procedure RefreshDesktopShortcutIcon();
var
  shortcutPath: String;
  appPath: String;
  iconPath: String;
begin
  shortcutPath := ExpandConstant('{autodesktop}\{#MyAppName}.lnk');
  if not FileExists(shortcutPath) then
    Exit;

  appPath := ExpandConstant('{app}\{#MyAppExeName}');
  iconPath := ExpandConstant('{app}\assets\branding\voxnote-app-icon-{#MyAppVersion}.ico');
  DeleteFile(shortcutPath);
  CreateShellLink(shortcutPath, '{#MyAppName}', appPath, '', ExpandConstant('{app}'), iconPath, 0, SW_SHOWNORMAL);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    RefreshDesktopShortcutIcon();
end;
