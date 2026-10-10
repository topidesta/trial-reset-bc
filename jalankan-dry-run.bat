@echo off
REM ============================================================
REM  BC-RESET — launcher praktis
REM  Jalankan file ini lewat double-click.
REM
REM  Default: DRY-RUN (hanya melihat, tidak menghapus apa pun).
REM  Untuk benar-benar reset trial, edit baris di bawah dan
REM  hapus tanda "REM" di depan baris --apply.
REM ============================================================

setlocal
cd /d "%~dp0"

REM --- Mode aman (dry-run): cuma menampilkan apa yang akan dihapus ---
"%~dp0dist\BC-RESET-fixed-console.exe" --no-gui

REM --- Mode hapus sungguhan (dengan backup). Aktifkan dengan menghapus "REM": ---
REM "%~dp0dist\BC-RESET-fixed-console.exe" --backup "%~dp0backup-cacheid.json" --apply --no-gui

echo.
pause
endlocal
