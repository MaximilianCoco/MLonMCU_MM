import subprocess
import sys

subprocess.run([sys.executable, r"C:\Users\Faebe\Desktop\MLonMCU\project\demonstration\MMTest\prepimg.py"], check=True)
subprocess.run([sys.executable, r"C:\Users\Faebe\Desktop\MLonMCU\project\demonstration\MMTest\imgtoh.py"], check=True)
#subprocess.run([sys.executable, r"C:\Users\Faebe\Desktop\MLonMCU\project\demonstration\MMTest\demo.py"], check=True)
subprocess.run([sys.executable, r"C:\Users\Faebe\Desktop\MLonMCU\project\demonstration\MMTest\demo_display.py"], check=True)