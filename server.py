from flask import Flask
import os

app = Flask(__name__)

#This is a crazy workaround for making digitalocean scheduler work
@app.route('/')
def index():
    print("Launching Scheduler")
    os.system("python3 application/scheduler.py")
    print("Scheduler Launched")
    return 'Successful', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
