import os

#init db
if os.path.isdir("./mongodb") == False:
    os.mkdir("./mongodb")

import subprocess
import signal
import time


commands = [
    'mongod --port 14701 --bind_ip localhost --dbpath ./mongodb',
    'uvicorn app:app --workers 4 --port 11133'
]
# Command with shell expansion
processes = []
for command in commands:
    processes.append(subprocess.Popen(command, shell=True))

while True:
    try:
        time.sleep(1000000)
    except KeyboardInterrupt:
        for process in processes:
            process.send_signal(signal.SIGINT)
        break