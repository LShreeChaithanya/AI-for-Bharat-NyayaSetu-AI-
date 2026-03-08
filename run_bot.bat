@echo off
setlocal enableextensions enabledelayedexpansion
if exist .env (
  for /f "usebackq tokens=*" %%a in (`type .env`) do set "%%a"
)
python bot.py
