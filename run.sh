#!/bin/bash
exec .venv/bin/gunicorn server.wsgi:application -w 2 -b localhost:9999
