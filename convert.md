Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue

python -m PyInstaller --clean --noconfirm --onedir --windowed --name WinCleaner --icon="D:\wincleaner\wincleaner.ico" --add-data "D:\wincleaner\wincleaner.ico;." wincleaner.py

VCRUNTIME140.dll
python -m pip install --upgrade pyinstaller pyinstaller-hooks-contrib