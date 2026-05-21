# Gunicorn config — use with:
#   gunicorn -c deploy/gunicorn.conf.py deepFakeDetection.wsgi:application
#
# Copy to your server and edit bind/workers if needed.

import os

bind = os.environ.get("GUNICORN_BIND", "127.0.0.1:8000")
workers = 1
threads = 2
timeout = 300
keepalive = 5

# TensorFlow + 3 models: keep workers=1 to avoid OOM
worker_class = "gthread"

accesslog = "-"
errorlog = "-"
loglevel = "info"

# WSGI app (chdir should be project root when starting gunicorn)
wsgi_app = "deepFakeDetection.wsgi:application"
