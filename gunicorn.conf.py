#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Gunicorn configuration for nDART (Flask-SocketIO).

Gunicorn auto-loads this file from the working directory when present.
Keep it aligned with docker-compose.production.yml (gevent, single worker).

Do NOT enable max_requests or preload_app with a single Socket.IO worker:
recycling the only worker can hang on exit and cause Cloudflare 524s.
"""

import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('FLASK_PORT', 5000)}"
backlog = 2048

# Worker processes — Socket.IO requires a single async worker unless using a message queue
workers = 1
worker_class = os.environ.get("GUNICORN_WORKER_CLASS", "gevent")
worker_connections = 1000
timeout = 120
keepalive = 5
graceful_timeout = 30

# Disable request-based worker recycling (0 = off)
max_requests = 0
max_requests_jitter = 0

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "ndart"

# Server mechanics
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None
preload_app = False

# SSL (optional)
keyfile = os.environ.get("SSL_KEYFILE", None)
certfile = os.environ.get("SSL_CERTFILE", None)


def when_ready(server):
    server.log.info("nDART server is ready. Workers: %s", server.cfg.workers)


def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")


def worker_abort(worker):
    worker.log.info("worker received SIGABRT signal")
