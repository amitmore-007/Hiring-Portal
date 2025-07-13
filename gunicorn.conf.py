import os
import multiprocessing

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
backlog = 2048

# Worker processes
workers = min(multiprocessing.cpu_count() * 2 + 1, 4)  # Cap at 4 workers for memory efficiency
worker_class = "sync"
worker_connections = 1000
timeout = 120  # Increased timeout for AI processing
keepalive = 2
max_requests = 1000
max_requests_jitter = 100

# Restart workers to prevent memory leaks
preload_app = True

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "hiring_portal"

# Server mechanics
daemon = False
pidfile = None
tmp_upload_dir = None

# Memory and performance
worker_tmp_dir = "/dev/shm"  # Use shared memory for better performance

# SSL (if needed in production)
keyfile = None
certfile = None

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
