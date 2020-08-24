#!/bin/sh
# MC51 - Install script for Clipster Server
# Borrowed stuff from the https://get.docker.com shell script
set -e
DEFAULT_INTERFACE="0.0.0.0:9999"
RANDOM_SECRET=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)

command_exists() {
    command -v "$@" > /dev/null 2>&1
}

userid="$(id -u 2>/dev/null || true)"
sh_c="sh -c"
if [ "$userid" -ne 0 ]; then
    if command_exists sudo; then
        sh_c="sudo -E sh -c"
    elif command_exists su; then
        sh_c="su -c"
    else
        echo
        echo "ERROR: installer needs the ability to run commands as root to install requirements"
        echo "Unable to find either \"sudo\" or \"su\" to make this happen"
        exit 1
    fi
fi

echo
echo "OK: Running as user $USER"
echo

if command_exists pip; then
    echo "OK: Found \"pip\". Ready to install python script"
    echo
    pip install --user .
else
    echo "ERROR: Could not find pip, which is required. Learn how to install it here: https://pip.pypa.io/en/stable/installing/"
    exit 1
fi

echo
echo "INFO: We will prepare django now"
echo

export CLIPSTER_SECRET=$RANDOM_SECRET
python manage.py migrate

if command_exists gunicorn; then
    echo
    echo "INFO: Setting up gunicorn (WSGCI-Server)"
    sleep 2s
else
    echo
    echo "ERROR: Could not find gunicorn (WSGCI-Server). Make sure it is installed"
    exit 1
fi

echo
read -r -p "On which ip:port should the gunicorn server listen [Enter for default $DEFAULT_INTERFACE]:  " INTERFACE
echo
if [ -z "$INTERFACE" ]; then
    INTERFACE=$DEFAULT_INTERFACE
    echo "OK: Using default - $INTERFACE"
else
    echo "OK: using - $INTERFACE"
    exit 1
fi

echo
echo "INFO: gunicorn must be used via HTTPS only. You will need to specify your SSL certificate files."
echo "INFO: You can use a self signed certificate or get a free signed one from https://letsencrypt.org/"
echo
echo

read -r -p "Enter the absolute path to your SSL cert file [e.g. /etc/letsencrypt/live/data-dive.com/fullchain.pem]:  " CERTFILE
while [ ! -f "$CERTFILE" ] || [ -z "$CERTFILE"  ]; do
  echo "ERROR: $CERTFILE cannot be accessed. Make sure it exists and is readable "
  echo
  read -r -p "Enter the absolute path to your SSL cert file [e.g. /etc/letsencrypt/live/data-dive.com/fullchain.pem]:  " CERTFILE
done
echo "OK: $CERTFILE can be accessed. We will use it "

echo
read -r -p "Enter the absolute path to your SSL key file [e.g. /etc/letsencrypt/live/data-dive.com/privkey.pem]:  " KEYFILE
while [ ! -f "$KEYFILE" ] || [ -z "$KEYFILE"  ]; do
  echo "ERROR: $KEYFILE cannot be accessed. Make sure it exists and is readable "
  echo
  read -r -p "Enter the absolute path to your SSL key file [e.g. /etc/letsencrypt/live/data-dive.com/privkey.pem]:  " KEYFILE
done
echo "OK: $KEYFILE can be accessed. We will use it "

GUNI_CONFIG_FILE=${PWD}"/guni_clipster.py"

echo
echo "INFO: creating gunicorn configuration file $GUNI_CONFIG_FILE"
echo

# Write gunicorn config file for serving clipster server
echo "
import sys

BASE_DIR = '$PWD'
sys.path.append(BASE_DIR)

bind = '$INTERFACE'
backlog = 20

import multiprocessing
workers = 1
worker_class = 'sync'
worker_connections = 10
timeout = 300
keepalive = 2

certfile = '$CERTFILE'
keyfile = '$KEYFILE'
ssl_version = 'TLS'

spew = False
loglevel = 'error'
accesslog = '/tmp/clipster_access_log'
errorlog = '/tmp/clipster_error_log'

def post_fork(server, worker):
    server.log.info('Worker spawned (pid: %s)', worker.pid)

def pre_fork(server, worker):
    pass

def pre_exec(server):
    server.log.info('Forked child, re-executing.')

def when_ready(server):
    server.log.info('Server is ready. Spawning workers')

def worker_int(worker):
    worker.log.info('worker received INT or QUIT signal')

    ## get traceback info
    import threading, sys, traceback
    id2name = dict([(th.ident, th.name) for th in threading.enumerate()])
    code = []
    for threadId, stack in sys._current_frames().items():
        code.append('\\\n# Thread: %s(%d)' % (id2name.get(threadId,''),
            threadId))
        for filename, lineno, name, line in traceback.extract_stack(stack):
            code.append('File: '%s', line %d, in %s' % (filename,
                lineno, name))
            if line:
                code.append('  %s' % (line.strip()))
    worker.log.debug('\\\n'.join(code))

def worker_abort(worker):
    worker.log.info('worker received SIGABRT signal')

" | tee $GUNI_CONFIG_FILE

echo
echo "INFO: making $GUNI_CONFIG_FILE executable"
chmod 755 $GUNI_CONFIG_FILE

# Write service file to autostart gunicorn
# Get path to executable
GUNI_BIN_FILE=$(which gunicorn)
echo
echo "OK: Found \"gunicorn\" command in $GUNI_BIN_FILE."
echo
echo "INFO: Creating /etc/systemd/system/clipster_server.service file"
echo
echo "INFO: We will need to run the following commands as root "
echo

# Write Systemd config file for auto loading script
echo "
[Unit]
Description=Clipster Server - A Multi Platform Cloud Clipboard
After=network.target

[Service]
WorkingDirectory=$PWD
ExecStart=$GUNI_BIN_FILE --config $GUNI_CONFIG_FILE server.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
ExecStop=/bin/kill -s TERM \$MAINPID
Restart=always
RestartSec=1
PrivateTmp=true
User=$USER
Environment=CLIPSTER_SECRET=$RANDOM_SECRET

[Install]
WantedBy=multi-user.target" | $sh_c tee /etc/systemd/system/clipster_server.service

echo
echo "INFO: running \"systemctl daemon-reload\" to reload systemd daemon config."
$sh_c "systemctl daemon-reload"
echo
echo "INFO: running \"systemctl enable clipster_server\" to enable autostart of clipster as daemon."
$sh_c "systemctl enable clipster_server"
echo
echo "INFO: running \"systemctl start clipster_server\" to start clipster daemon."
$sh_c "systemctl stop clipster_server"
$sh_c "systemctl start clipster_server"
echo
echo "INFO: running \"systemctl status clipster_server\" to check if clipster is running."

if $sh_c "systemctl status clipster_server"; then
    echo
    echo "OK: Installation completed. Clipster Server is running."
    echo
    exit 0
else
    echo
    echo "ERROR: Installation failed. Clipster Server daemon is not running."
    echo
    exit 1
fi
