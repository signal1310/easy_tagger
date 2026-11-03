@echo off
chcp 65001 > nul
echo [Easy Tagger] PyInstaller 빌드를 시작합니다...
python -m PyInstaller --clean --noconsole --onefile --paths="." --icon="assets/icon.ico" --name="EasyTagger" --add-data="assets;assets" main.py
if %ERRORLEVEL% EQU 0 (
    echo [Easy Tagger] 빌드 성공! 결과물: dist\EasyTagger.exe
    python -c "import zipfile, os; zf = zipfile.ZipFile('dist/EasyTagger-v1.1.0-windows-x64.zip', 'w', zipfile.ZIP_DEFLATED); zf.write('dist/EasyTagger.exe', 'EasyTagger.exe'); zf.close()"
    echo [Easy Tagger] 배포 패키지 생성 완료: dist\EasyTagger-v1.1.0-windows-x64.zip
) else (
    echo [Easy Tagger] 빌드 중 오류가 발생했습니다.
)
pause
