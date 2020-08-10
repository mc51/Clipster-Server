# Clipster - Cloud Server

Clipster is a multi platform cloud clipboard:  
Copy a text on your smartphone and paste it on your desktop, or vice versa.  
Easy, secure, open source.  
Supports Android, Linux, MacOS and Windows.  


## Setup

First, clone the repo and enter the directory:

``` bash
git clone https://github.com/mc51/Clipster-Desktop.git && cd Clipster-Desktop
```

Then, just run the install script:

``` bash
sh install.sh
```

The install script takes care of everything.  
  
If you absolutely need to, you can install manually.  
  
First, install the python package:

``` bash
pip install .
```

Now, the `clipster` command will be available in the command line. Clipster depends on the `xsel` or `xclip` packages. On some distributions, you will to need manually install them. On Debian/Ubuntu do:

```bash
sudo apt-get install xsel
```

Now, you can start the account registration:

``` bash
clipster register
```

You can use your own [clipster-server](https://github.com/mc51/Clipster-Server), or the default public server.  
After registering an account, you need to create a config file in `~/.config/clipster/config`. The file should contain your settings from the registration:

``` bash
[settings]
server = https://data-dive.com:9999
username = YourUser
password = YourPassword
```

For a convenient experience, you should run clipster as a background service. This will automatically take care of copying and pasting to the server and is the intended use.  
For this, you need to setup a `systemd` service. First, find the absolute path to your installation:

```bash
whereis clipster
```

Following, create the file (as root) `/etc/systemd/system/clipster.service` with the following content:

```
[Unit]
Description=Clipster - A Multi Platform Cloud Clipboard Clipboard
After=network.target

[Service]
Environment="DISPLAY=:0.0"
WorkingDirectory=/tmp
ExecStart=<PATH>
ExecReload=/bin/kill -s HUP $MAINPID
ExecStop=/bin/kill -s TERM $MAINPID
Restart=always
RestartSec=1

[Install]
WantedBy=multi-user.target
```

Change \<PATH\> to your installation path. Now, run the following to reload the configuration, enable auto start, and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable clipster
sudo systemctl start clipster
```

Finally, check the status with:

```bash
sudo systemctl status clipster
```

If all went fine, you should see:

``` bash
● clipster.service - Clipster - A Multi Platform Cloud Clipboard
   Loaded: loaded (/etc/systemd/system/clipster.service; enabled; vendor preset: enabled)
   Active: active (running) since Mon 2020-08-01 12:00:0 CEST; 30min ago
```

Now, you can [use](#usage) clipster!

## Usage

When clipster is running as a background service, your current clipboard text will automatically be sent to the server.  
To get the current text from the server, copy the keyword "clipster" to your clipboard. Clipster will fetch the current text from the server and put it in your local clipboard.  
  
For manual usage, there are the following commands.  
To copy the current clipboard text to the server:  

```bash
clipster copy
```

To retrieve a text from the server to the local clipboard:
```bash
clipster paste
```

To register a new account or change your current account (this will change your `~/.config/clipster/config` file):
```bash
clipster register
```

To run clipster in the background (only needed during [setup](#setup)):
```bash
clipster listen
```


## Credits

Server based on [cloud-clipboard](https://github.com/krsoninikhil/cloud-clipboard)  
