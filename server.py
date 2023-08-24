from flask import (
    Flask,
    render_template,
)
import subprocess
import logging

#This is a crazy workaround for making digitalocean scheduler work

logging.basicConfig(level=logging.DEBUG)
...
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/launch')
def launch():
    logging.debug("Launching Scheduler")
    subprocess.Popen(["python3","application/scheduler.py"])
    logging.debug("Scheduler Launched")
    return 'Successful', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
