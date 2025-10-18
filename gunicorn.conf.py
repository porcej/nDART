#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Gunicorn Configuration for nDART

This configuration is optimized for Flask-SocketIO applications with eventlet.
"""

import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('FLASK_PORT', 5000)}"
backlog = 2048

# Worker processes
workers = 1  # Use 1 worker for SocketIO (eventlet doesn't support multiple workers)
worker_class = "eventlet"
worker_connections = 1000
timeout = 120
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

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

# SSL (if needed)
keyfile = os.environ.get('SSL_KEYFILE', None)
certfile = os.environ.get('SSL_CERTFILE', None)

# Preload application for better performance
preload_app = True

# Worker timeout for graceful shutdown
graceful_timeout = 30

# Environment variables
raw_env = [
    "FLASK_APP=wsgi.py",
    f"FLASK_ENV={os.environ.get('FLASK_ENV', 'production')}",
]

# SocketIO specific settings
def when_ready(server):
    """Called just after the server is started."""
    server.log.info("nDART server is ready. Workers: %s", server.cfg.workers)

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("Forked child, re-executing.")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Server is ready. Spawning workers")

def worker_abort(worker):
    """Called when a worker received the SIGABRT signal."""
    worker.log.info("worker received SIGABRT signal")
