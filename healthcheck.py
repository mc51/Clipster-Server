"""
Container health check: succeeds if the app answers HTTP requests.

Any response below 500 counts as healthy, also the 400 Django sends if ALLOWED_HOSTS does not
include the health check's host name. That still proves gunicorn and Django are up.
"""

import sys
import urllib.error
import urllib.request

URL = "http://127.0.0.1:8000/api-auth/login/"

try:
    urllib.request.urlopen(URL, timeout=4)
except urllib.error.HTTPError as e:
    sys.exit(0 if e.code < 500 else 1)
except Exception:
    sys.exit(1)
