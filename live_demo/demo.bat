@echo off
cd C:\Users\Faebe
del /q "C:\Users\Faebe\Desktop\MLonMCU\project\demonstration\MMTest\pics\2026*"
rmdir /s /q "C:\Users\Faebe\Desktop\MLonMCU\project\demonstration\MMTest\headers\" && mkdir "C:\Users\Faebe\Desktop\MLonMCU\project\demonstration\MMTest\headers\"
rmdir /s /q "C:\Users\Faebe\Desktop\MLonMCU\project\demonstration\MMTest\results\" && mkdir "C:\Users\Faebe\Desktop\MLonMCU\project\demonstration\MMTest\results\"
rmdir /s /q "C:\Users\Faebe\Desktop\MLonMCU\project\demonstration\MMTest\cropped\" && mkdir "C:\Users\Faebe\Desktop\MLonMCU\project\demonstration\MMTest\cropped\"
node C:\Users\Faebe\Desktop\whatsapp-dl\wa-download_old.js "Max Coco" C:\Users\Faebe\Desktop\MLonMCU\project\demonstration\MMTest\pics
python C:\Users\Faebe\Desktop\MLonMCU\project\demonstration\MMTest\run_demo.py
pause