import multiprocessing

# Server socket
bind = "0.0.0.0:10000"

# Worker processes
workers = 1  # Eventlet requires only 1 worker
worker_class = "eventlet"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "flexia-merchant-chat"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL
# keyfile = None
# certfile = None

# Server hooks
def on_starting(server):
    server.log.info("Starting Flexia Merchant Chat Server...")

def on_exit(server):
    server.log.info("Shutting down Flexia Merchant Chat Server...")