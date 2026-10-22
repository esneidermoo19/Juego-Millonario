@echo off
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
    echo No se encontro Python. Instalalo desde https://www.python.org/downloads/ y vuelve a intentarlo.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    py -3 -m venv .venv
    if errorlevel 1 goto :error
)

.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
if errorlevel 1 goto :error

rem Voces de los presentadores (solo la primera vez). Si falla, el juego usa una voz de respaldo.
if not exist "backend\tts_voices\en_US-ryan-medium.onnx" (
    echo Descargando voces de los presentadores, ~126 MB...
    .venv\Scripts\python.exe -m piper.download_voices --data-dir backend\tts_voices es_MX-ald-medium en_US-ryan-medium
    if errorlevel 1 echo No se pudieron descargar las voces; se usara la voz de respaldo.
)

start "" "http://localhost:5000"
.venv\Scripts\python.exe -m backend.app
pause
exit /b 0

:error
echo No se pudo preparar el juego. Revisa que Python 3 y pip esten instalados.
pause
exit /b 1
