@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
    if errorlevel 1 goto erro
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto erro
".venv\Scripts\python.exe" -m streamlit run app.py
if errorlevel 1 goto erro
exit /b 0
:erro
echo Nao foi possivel iniciar. Confira se o Python esta instalado e se ha conexao com a internet.
pause
exit /b 1
