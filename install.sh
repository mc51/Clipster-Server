#!/bin/sh
# MC51 - Install script for Clipster Server
# https://github.com/mc51/Clipster-Server
# Borrowed stuff from the https://get.docker.com shell script

set -e
DEFAULT_INTERFACE="0.0.0.0:9999"
RANDOM_SECRET=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
PYTHON_EXEC=python3
BASE_DIR="$PWD"

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
echo "INFO: Running as user $USER"


if command_exists $PYTHON_EXEC; then
    ver=$(${PYTHON_EXEC} -V 2>&1 | sed 's/.* \([0-9]\).\([0-9]\).*/\1\2/')
    while [ "$ver" -lt "36" ]; do
        echo
        echo "ERROR: This package requires python 3.6 or greater. Your python3 executable is only $ver "
        echo
        read -r -p "Enter path or name to a different python version [e.g. /usr/bin/python3.7]:  " PYTHON_EXEC
        ver=$(${PYTHON_EXEC} -V 2>&1 | sed 's/.* \([0-9]\).\([0-9]\).*/\1\2/')
    done
        echo
        echo "INFO: Using Python $ver"
    if ${PYTHON_EXEC} -m pip -V; then
        echo
        echo "INFO: Found pip. Ready to install clipster_server python package and requirements"
        echo
        $PYTHON_EXEC -m pip install --user .
    else
        echo
        echo "ERROR: Could not find pip, which is required. Learn how to install it here: https://pip.pypa.io/en/stable/installing/"
        exit 1
    fi
else
    echo "ERROR: Coult not find $PYTHON_EXEC exectuable. Make sure python is available "
fi

echo
echo "INFO: We will prepare django now"
echo

# Set a random SECRET KEY for Django
sed -i "s/^SECRET_KEY = None$/SECRET_KEY=\"${RANDOM_SECRET}\"/" server/settings.py
# Run Django migrations: Create DB Tables
$PYTHON_EXEC manage.py makemigrations
$PYTHON_EXEC manage.py migrate
$PYTHON_EXEC manage.py collectstatic

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
echo "INFO: gunicorn must be used via HTTPS only. You will need to specify your SSL certificate files"
echo "INFO: You can get a free certificate from https://letsencrypt.org/"
echo "INFO: You can also create your own self signed certificate"
echo
read -r -p "Do you want to create a self signed certificate now (skip if you already have one) [y/N]: " response
echo ""
case "$response" in
    [yY][eE][sS]|[yY])
    if command_exists openssl; then
        echo "INFO: Found openssl. Creating a self signed SSL certificate"
        echo
        openssl req -newkey rsa -x509 -sha256 -days 3650 -nodes -out clipster-ssl.crt -keyout clipster-ssl.key
        CERTFILE="$BASE_DIR/clipster-ssl.crt"
        KEYFILE="$BASE_DIR/clipster-ssl.key"
    else
        echo
        echo "ERROR: Could not find openssl, which is needed to create a certificate. Make sure to install it"
        echo "ERROR: Use e.g. on Ubuntu/Debian: sudo apt-get install openssl"
        exit 1
    fi
    ;;
    *)
    read -r -p "Enter the absolute path to your SSL cert file [e.g. /etc/letsencrypt/live/data-dive.com/fullchain.pem]:  " CERTFILE
    while [ ! -f "$CERTFILE" ] || [ -z "$CERTFILE"  ]; do
        echo "ERROR: File $CERTFILE cannot be accessed. Make sure it exists and is readable "
        echo
        read -r -p "Enter the absolute path to your SSL cert file [e.g. /etc/letsencrypt/live/data-dive.com/fullchain.pem]:  " CERTFILE
    done
    echo "OK: $CERTFILE can be accessed. We will use it "
    echo
    read -r -p "Enter the absolute path to your SSL key file [e.g. /etc/letsencrypt/live/data-dive.com/privkey.pem]:  " KEYFILE
    while [ ! -f "$KEYFILE" ] || [ -z "$KEYFILE"  ]; do
        echo "ERROR: File $KEYFILE cannot be accessed. Make sure it exists and is readable "
        echo
        read -r -p "Enter the absolute path to your SSL key file [e.g. /etc/letsencrypt/live/data-dive.com/privkey.pem]:  " KEYFILE
    done
    echo "OK: $KEYFILE can be accessed. We will use it "
    ;;
esac


GUNI_CONFIG_FILE=${PWD}"/guni_clipster.py"

echo
echo "INFO: creating gunicorn configuration file $GUNI_CONFIG_FILE"
echo
sleep 1s

# Write gunicorn config file for serving clipster server
echo "import sys

BASE_DIR = '$PWD'
sys.path.append(BASE_DIR)

bind = '$INTERFACE'
backlog = 20

import multiprocessing
workers = 3
worker_class = 'sync'
worker_connections = 10
timeout = 30
keepalive = 2

certfile = '$CERTFILE'
keyfile = '$KEYFILE'
ssl_version = 'TLS'

spew = False
loglevel = 'ERROR'
accesslog = '/tmp/clipster_access.log'
errorlog = '/tmp/clipster_error.log'

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
            code.append(\"File: '%s', line %d, in %s\" % (filename, lineno, name))
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
sleep 1s

# Write Systemd config file for auto loading script
echo "[Unit]
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

[Install]
WantedBy=multi-user.target" | $sh_c "tee /etc/systemd/system/clipster_server.service"

echo
echo "INFO: running \"systemctl daemon-reload\" to reload systemd daemon config"
$sh_c "systemctl daemon-reload"
echo
echo "INFO: running \"systemctl enable clipster_server\" to enable autostart of clipster as daemon"
sleep 1s
$sh_c "systemctl enable clipster_server"
echo
echo "INFO: running \"systemctl start clipster_server\" to start clipster daemon."
$sh_c "systemctl stop clipster_server"
$sh_c "systemctl start clipster_server"
echo
echo "INFO: running \"systemctl status clipster_server\" to check if clipster is running."
echo

sleep 3s
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
