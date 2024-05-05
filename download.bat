@echo off
setlocal EnableExtensions EnableDelayedExpansion
goto UserPrompt

:UserPrompt
cls
echo/
echo Please type the database base folder path and press ENTER.
echo/
echo Or alternatively drag ^& drop the folder from Windows
echo Explorer on this console window and press ENTER.
echo/

set "BaseFolder=""
set /P "BaseFolder=Path: "
if "!BaseFolder!" == "" goto UserPrompt
echo/

if not exist "!BaseFolder!\starsector-core\data\" (
    echo There is no folder "!BaseFolder!\data".
    echo/
    choice "Do you want to enter the path once again "
    goto UserPrompt
)

echo "Installation found!"

REM python helper.py --src "$1" --action upload
