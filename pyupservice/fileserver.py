
import logging
import time

import requests
from flask import Flask, request, send_from_directory

LOCALHOST = '127.0.0.1'

logger = logging.getLogger(__name__)


def RunFileServer(fileServerDir, fileServerPort):
    """
    Run a Flask file server on the given port.

    Explicitly specify instance_path, because Flask's
    auto_find_instance_path can fail when run in a frozen app.
    """
    app = Flask(__name__, instance_path=fileServerDir)

    @app.route('/fileserver-is-ready', methods=['GET'])
    def FileserverIsReady():  # pylint: disable=unused-variable
        """
        Used to test if file server has started.
        """
        return 'Fileserver is ready!'

    @app.route('/<path:filename>', methods=['GET'])
    def ServeFile(filename):  # pylint: disable=unused-variable
        """
        Serves up a file from PYUPDATER_FILESERVER_DIR.
        """
        return send_from_directory(fileServerDir, filename.strip('/'))

    def ShutDownServer():
        """
        Shut down the file server.
        """
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()

    @app.route('/shutdown', methods=['POST'])
    def ShutDown():  # pylint: disable=unused-variable
        """
        Respond to a POSTed request to shut down the file server.
        """
        ShutDownServer()
        return 'Server shutting down...'

    app.run(host=LOCALHOST, port=fileServerPort)


def WaitForFileServerToStart(url,httptimeout):
    """
    Wait for file server to start up. If we receive
    a ConnectionError, we continue waiting, but if we receive an HTTP
    response code (404), we return True.  For a frozen app, e.g. a
    Mac .app bundle, the location of the updates must be supplied by
    an environment variable, whereas when running from the source repo,
    the location of the updates is likely to be ./pyu-data/deploy/
    """
    attempts = 0
    while True:
        try:
            attempts += 1
            r=requests.get(url, timeout=httptimeout)
            return r.status_code
        except requests.exceptions.ConnectionError:
            time.sleep(0.25)
            print('Connection failed: timeout')
            if attempts > 5:
                return

def ShutDownFileServer(port):
    """
    Shut down the file server.
    """
    url = "http://%s:%s/shutdown" % (LOCALHOST, port)
    requests.post(url, timeout=1)
