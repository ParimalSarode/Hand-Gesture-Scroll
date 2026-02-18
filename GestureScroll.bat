@echo off
title Gesture Scroll App
echo Starting Gesture Scroll...
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo App crashed or closed with error.
    pause
)
