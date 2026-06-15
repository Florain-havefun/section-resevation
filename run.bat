@echo off
chcp 65001 >nul 2>nul
cd /d "%~dp0"
echo starting...
C:\Users\Florian\.local\bin\python3.14.exe book.py
echo done
pause
