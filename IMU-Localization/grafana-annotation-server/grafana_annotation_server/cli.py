import click
import json
import time
import threading

from flask import Flask, render_template, request, jsonify

def setInterval(interval):
    def decorator(function):
        def wrapper(*args, **kwargs):
            stopped = threading.Event()

            def loop(): # executed in another thread
                while not stopped.wait(interval): # until stopped
                    function(*args, **kwargs)

            t = threading.Thread(target=loop)
            t.daemon = True # stop if the program exits
            t.start()
            return stopped
        return wrapper
    return decorator

class Annotation(object):

    def __init__(self, file_name):
        """
        """
        self._file_name = file_name
        self.load()
        self.dump()

    def log(self, target_class, time_range, source_class):
        """
        """
        if target_class in self._data["annotations"]:
            self._data["annotations"][target_class].append([time_range, source_class])
        else:
            self._data["annotations"][target_class] = [[time_range, source_class]]

    def load(self):
        """
        """
        def schema():
            return {
                "created": time.time(),
                "annotations": {}
            }

        try:
            with open(self._file_name, "r") as minion:
                self._data = json.loads(minion.read())

                if "annotations" not in self._data:
                    self._data = schema()
                    click.echo("Invalid Schema. Created New.")
                else:
                    click.echo("Loaded existing data annotations.")

        except (FileNotFoundError, ValueError):
            #: Whoopsie!
            self._data = schema()
            click.echo("Created new data annotations file")

    @setInterval(10)
    def dump(self):
        """
        """
        self._data["modified"] = time.time()

        with open(self._file_name, "w") as minion:
            click.echo("Ran dump Routine")
            minion.write(json.dumps(self._data, indent = 4))

app = Flask(__name__)
annotation_db = None

@app.route('/', methods=['POST','GET'])
def index():
    response = {
        "ready": True,
        "version": "0.0.1",
        "uid": "Grafana Annotation Server"
    }
    return jsonify(response), 200

@app.route('/log', methods = ['PUT'])
def log():
    try:
        payload = {
            "target_class": request.form['annotation_class'],
            "time_range": [request.form['from'], request.form['to']],
            "source_class": request.form['source_class']
        }

        annotation_db.log(**payload)

        return jsonify({"error": False}), 201

    except Exception:
        return jsonify({"error": True, "error_msg": "Incorrect Payload data"}), 400

@click.command()
@click.option('--port', '-p', help='HTTP Server Port', default = 8000, type = int)
@click.argument('file_name', required = True)
def main(file_name, port):
    """HTTP Backend API for Grafana Annotations."""
    global annotation_db
    annotation_db = Annotation(file_name)

    app.run(host = '0.0.0.0', port = port, debug = True, threaded=True)
