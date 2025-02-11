@echo off

REM Jalankan Frontend JavaScript
cd C:\Ilham\Development\Absen\jalin-attandance-fe
start "" cmd /k npm run dev

REM Jalankan Backend Flask
cd C:\Ilham\Development\Absen\Jallin-Attendance-BE
start "" cmd /k "pip install -r requirements.txt && flask --app main run --port 5001"