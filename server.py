import os
import signal
from app import create_app
from paste.translogger import TransLogger

from waitress import serve

app = create_app()

# ------------------------------------------Server Settings-------------------------------------------------
WAITRESS_PORT = os.getenv("WAITRESS_PORT")
WAITRESS_TRUSTED_PROXY = os.getenv("WAITRESS_TRUSTED_PROXY")


# ------------------------------------Handle terminate signal and quit--------------------------------------


def terminate(signal, frame):
    app.logger.info("----------------------------------------")
    app.logger.info("Signal SIGTERM received, terminating...")
    exit(0)


# Trap and terminate bot on receiving SIGTERM to this python process
signal.signal(signal.SIGTERM, terminate)

try:
    serve(
        TransLogger(app),
        host="0.0.0.0",
        port=WAITRESS_PORT,
        trusted_proxy_headers="forwarded",
        trusted_proxy=WAITRESS_TRUSTED_PROXY,
    )
except KeyboardInterrupt:
    exit(0)
