python -m PyInstaller --clean --noconfirm --onedir --windowed --name WinCleaner --icon=wincleaner.ico wincleaner.py


Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue

VCRUNTIME140.dll
python -m pip install --upgrade pyinstaller pyinstaller-hooks-contrib