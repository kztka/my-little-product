@echo off
setlocal
echo Change PDF to PNG in this directory
for %%F in (%~dp0*.pdf) do (
  echo magick.exe -density 400 -colorspace RGB %%F %%~dpnF.png
  magick.exe -density 400 -colorspace RGB %%F %%~dpnF.png
)
echo Process is completed.
pause