import os

bind = "0.0.0.0:8000"
# Heartbeat files go to memory instead of /tmp, which also works with a read-only container
worker_tmp_dir = "/dev/shm"
workers = int(os.getenv("GUNICORN_WORKERS", "2"))
# The master kills and replaces a worker that is stuck on a request for longer than this
timeout = 30
# Recycle workers regularly (jitter keeps them from restarting at the same time), so a
# slow memory leak never grows unbounded
max_requests = 1000
max_requests_jitter = 100
accesslog = "-"
control_socket_disable = True
# Trust X-Forwarded-Proto from the reverse proxy, so Django knows requests arrived via HTTPS
forwarded_allow_ips = "*"
