import os

bind = "0.0.0.0:8000"
workers = int(os.getenv("GUNICORN_WORKERS", "2"))
accesslog = "-"
control_socket_disable = True
# Trust X-Forwarded-Proto from the reverse proxy, so Django knows requests arrived via HTTPS
forwarded_allow_ips = "*"
