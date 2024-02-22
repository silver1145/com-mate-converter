@echo off
where wt.exe 1>nul 2>nul
if %ERRORLEVEL%==1 cmc.exe & exit
if %ERRORLEVEL%==0 wt cmd -NoExit -Command "/k pushd "%~dp0" & title CMC & cmc.exe & exit"
