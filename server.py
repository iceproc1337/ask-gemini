import signal
from app import create_app
from gevent import pywsgi

app = create_app()

# ---------------------------------------------Launch Server-------------------------------------------------
server = pywsgi.WSGIServer(("0.0.0.0", 8080), app, log=app.logger)


# ------------------------------------Handle terminate signal and quit--------------------------------------
def terminate(signal, frame):
    app.logger.info("----------------------------------------")
    app.logger.info("Signal SIGTERM received, terminating...")
    server.stop()


# Trap and terminate bot on receiving SIGTERM to this python process
signal.signal(signal.SIGTERM, terminate)

try:
    server.serve_forever()
except KeyboardInterrupt:
    server.stop()
