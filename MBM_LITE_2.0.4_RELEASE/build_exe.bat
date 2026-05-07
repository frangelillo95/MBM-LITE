@echo off
setlocal

cd /d "%~dp0"

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

set APP_NAME=MBM-LITE-2.0.4
set ENTRYPOINT=source\main.py
set ICON_FILE=source\assets\MBM.ico
set ADD_DATA_ICON=source\assets\MBM.ico;source\assets

set ADD_DATA_PNG=
if exist source\assets\MBM_48.png (
    set ADD_DATA_PNG=--add-data "source\assets\MBM_48.png;source\assets"
)

pyinstaller ^
  --noconfirm ^
  --clean ^
  --windowed ^
  --name "%APP_NAME%" ^
  --icon "%ICON_FILE%" ^
  --add-data "%ADD_DATA_ICON%" ^
  %ADD_DATA_PNG% ^
  "%ENTRYPOINT%"

endlocal
