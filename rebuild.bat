@echo off
REM Full rebuild - clean, build base, build, and start

echo.
echo ========================================
echo Full rebuild...
echo ========================================

call clean.bat
call build-base.bat
call build.bat
call up.bat

echo.
echo ========================================
echo Full rebuild complete!
echo ========================================
