@echo off
call conda activate tools

REM Get zhconv path
python -c "import zhconv; print(zhconv.__path__[0])" > temp.txt
set /p ZHCONV_PATH=<temp.txt
del temp.txt

echo zhconv path: %ZHCONV_PATH%

REM Build with Nuitka
nuitka --standalone --enable-plugin=tk-inter --windows-disable-console --jobs=4 --output-dir=dist --include-package=zhconv --include-data-dir=%ZHCONV_PATH%=zhconv index.py

echo Build done! Output in dist\index.dist
pause
