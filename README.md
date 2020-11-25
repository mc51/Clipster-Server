# Clipster - Linux Cloud Server

Clipster is a multi platform cloud clipboard:  
Copy a text on your smartphone and paste it on your desktop, or vice versa.  
Easy, secure, open source.  
Supports Android, Linux, MacOS and Windows.  
  
This package allows you to set up your own Linux server.  
For the mobile client see [Clipster-Android](https://github.com/mc51/Clipster-Android).  
And here is the [Clipster-Desktop](https://github.com/mc51/Clipster-Desktop) client.  
  
Clipster-Server is based on [cloud-clipboard](https://github.com/krsoninikhil/cloud-clipboard) and runs as a [Django](https://www.djangoproject.com/) App. To serve the app the light weight [Gunicorn](https://gunicorn.org/) WSGI HTTP server is used. 

## Automatic Setup

First, clone the repo and enter the directory:

``` bash
git clone https://github.com/mc51/Clipster-Server.git && cd Clipster-Server
```

Then, just run the install script:

``` bash
sh install.sh
```

The install script takes care of everything.  

## Manual Setup
  
If you need to, you can install manually.  
  
First, install the python package, which will also install the requirements:

``` bash
pip install --user .
```

Then, set a secret key for the Django installation:

```bash
sed -i "s/^SECRET_KEY = None$/SECRET_KEY='YourSuperSecretAndLongKey'/" server/settings.py
```

Next, prepare Django (this creates the database tables)

```bash
python manage.py migrate
```

[Gunicorn](https://docs.gunicorn.org/en/latest/) is the WSGCI server that will serve our App. It deals with requests to clipster.  
To configure it, create a file `guni_config.py` with this content:

```python
import sys

BASE_DIR = <CLIPSTER_SERVER_DIR>
sys.path.append(BASE_DIR)

bind = '0.0.0.0:9999'
backlog = 20

import multiprocessing
workers = 1
worker_class = 'sync'
worker_connections = 10
timeout = 300
keepalive = 2

certfile = <CERTFILE>
keyfile = <KEYFILE>
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
        code.append('\n# Thread: %s(%d)' % (id2name.get(threadId,''),
            threadId))
        for filename, lineno, name, line in traceback.extract_stack(stack):
            code.append('File: '%s', line %d, in %s' % (filename,
                lineno, name))
            if line:
                code.append('  %s' % (line.strip()))
    worker.log.debug('\n'.join(code))

def worker_abort(worker):
    worker.log.info('worker received SIGABRT signal')
```

Replace `<CLIPSTER_SERVER_DIR>` with the current directory.  
You should always run the server over **HTTPS only**. To configure SSL, replace `<CERTFILE>` with your SSL certification file and `<KEYFILE>` with your SSL private key file.  
Per default, the server will listen on all interfaces on port 9999. Change the `bind=` line to restrict access, e.g. listen only on your home network. For more options, check the [documentation](https://docs.gunicorn.org/en/stable/configure.html).  
Then, make the config file executable:

``` bash
chmod 755 guni_config.py
```

Following, get the path to your `gunicorn` binary:

``` bash
whereis gunicorn
```

Next, we set up a `systemd` service to automatically take care of (re)starting the gunicorn server.  
Create a new file (as root) `/etc/systemd/system/clipster_server.service`:

``` bash
[Unit]
Description=Clipster Server - A Multi Platform Cloud Clipboard
After=network.target

[Service]
WorkingDirectory=<CLIPSTER_SERVER_DIR>
ExecStart=<GUNICORN_BIN> --config <GUNI_CONFIG_FILE> server.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
ExecStop=/bin/kill -s TERM $MAINPID
Restart=always
RestartSec=1
PrivateTmp=true
User=<USER>

[Install]
WantedBy=multi-user.target"
```

Replace `<CLIPSTER_SERVER_DIR>` with the path to the cloned repository. For `<GUNICORN_BIN>` set the path from just before to the gunicorn executable. The path to the config file for gunicorn we've created before goes into `<GUNI_CONFIG_FILE>`. Finally, replace `<USER>` with your username.  
Now, run the following to reload the configuration, enable auto start, and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable clipster_server
sudo systemctl start clipster_server
```

Finally, check the status with:

```bash
sudo systemctl status clipster_server
```

If all went fine, you should see:

``` bash
● clipster_server.service - Clipster Server - A Multi Platform Cloud Clipboard
   Loaded: loaded (/etc/systemd/system/clipster_server.service; enabled; vendor preset: enabled)
   Active: active (running) since Sun 2020-08-23 20:43:15 CEST; 13h ago
 Main PID: 16672 (gunicorn)
    Tasks: 2 (limit: 4915)
   CGroup: /system.slice/clipster_server.service
           ├─16672 /opt/bin/python /opt/bin/gunicorn --config /home/mc/clipster-server/guni_clipster.py server.wsgi:application
           └─17464 /opt/bin/python /opt/bin/gunicorn --config /home/mc/clipster-server/guni_clipster.py server.wsgi:application

Aug 23 20:43:15 ace systemd[1]: Started Clipster Server - A Multi Platform Cloud Clipboard.
```

Now, you should be able to connect to your server with [Clipster-Desktop](https://github.com/mc51/Clipster-Desktop) or via browser using the URL `https://yourserver.com:9999`. 


## Credits

Server based on [cloud-clipboard](https://github.com/krsoninikhil/cloud-clipboard).  
Running on [Django](https://www.djangoproject.com/) and served by [Gunicorn](https://gunicorn.org/).
