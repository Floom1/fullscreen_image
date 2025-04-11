[Setup]
AppName=Full Screen App
AppVersion=1.0
DefaultDirName={pf}\FullScreenApp1
OutputDir=.
OutputBaseFilename=setup

[Files]
Source: "dist\main.exe"; DestDir: "{app}"
Source: "config.ini"; DestDir: "{app}"

[Run]
Filename: "{app}\main.exe"; Description: "Запустить приложение"; Flags: nowait