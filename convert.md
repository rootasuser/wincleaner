Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue

python -m PyInstaller --onefile --windowed --name WinCleaner `
  --icon wincleaner.ico --add-data "wincleaner.ico;." `
  --distpath dist_onefile --workpath build_onefile wincleaner.py
  
VCRUNTIME140.dll
python -m pip install --upgrade pyinstaller pyinstaller-hooks-contrib