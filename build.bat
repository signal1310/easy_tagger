@echo off
chcp 65001 > nul
echo [Easy Tagger] PyInstaller 빌드를 시작합니다...
python -m PyInstaller --clean --noconsole --onefile --paths="." --icon="assets/icon.ico" --name="EasyTagger" --add-data="assets;assets" --add-data="config.init.json;." main.py
if %ERRORLEVEL% EQU 0 (
    echo [Easy Tagger] 빌드 성공! 결과물: dist\EasyTagger.exe
) else (
    echo [Easy Tagger] 빌드 중 오류가 발생했습니다.
)
pause
