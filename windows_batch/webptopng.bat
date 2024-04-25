@echo off
setlocal
echo Change WEBP to PNG in this directory
for %%F in (%~dp0*.webp) do (
  echo magick.exe -density 400 -colorspace RGB %%F %%~dpnF.png
  magick.exe -density 400 -colorspace RGB %%F %%~dpnF.png
)
echo Process is completed.
pause