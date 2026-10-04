# Clipster - Linux Cloud Server

Clipster is a multi platform cloud clipboard:  
Copy a text on your smartphone and paste it on your desktop, or vice versa.  
Easy, secure, open source.  
Supports Android, Linux, MacOS, Windows and all browsers.  
  
This package allows you to set up your own Linux server including a web front-end.  
For the mobile client see [Clipster-Android](https://github.com/mc51/Clipster-Android).  
For a client for Linux, Windows and MacOS check [Clipster-Desktop](https://github.com/mc51/Clipster-Desktop).  

## Setup

The server runs with [Docker Compose](https://docs.docker.com/compose/install/). Clone the repo and create your configuration:

```bash
git clone https://github.com/mc51/Clipster-Server.git && cd Clipster-Server
cp .env.example .env
```

Edit `.env` and at least set a `SECRET_KEY` (e.g. generated with `openssl rand -base64 48`). Then start the server:

```bash
docker compose up -d
```

The database lives in `./data/db.sqlite3`, migrations are applied automatically on every start.

### HTTPS

Always run the server over **HTTPS only**, so that traffic is encrypted. There are two options:

- **Built-in**: uncomment `COMPOSE_PROFILES=caddy` and `DOMAIN=...` in `.env`. A [Caddy](https://caddyserver.com/) container then serves Clipster at `https://<DOMAIN>` with an automatic [Let's Encrypt](https://letsencrypt.org) certificate. Your domain must point to the server and ports 80 and 443 must be reachable from the internet.
- **Your own reverse proxy** (nginx, Traefik, ...): point it to `http://127.0.0.1:9999` (see `BIND` in `.env`) and make it send the `X-Forwarded-Proto` header.

Now you can connect with [Clipster-Desktop](https://github.com/mc51/Clipster-Desktop), [Clipster-Android](https://github.com/mc51/Clipster-Android) or via browser using the front-end at `https://<your-domain>`.

### Common tasks

```bash
docker compose logs -f                                         # show logs
docker compose exec clipster python manage.py createsuperuser  # create an admin for /admin
git pull && docker compose up -d --build                       # update
cp data/db.sqlite3 backup.sqlite3                              # backup
```

### Migrating from the old install script setup

Do a fresh clone as described above, then stop the old service and take over its database and secret key:

```bash
sudo systemctl disable --now clipster_server
sudo rm /etc/systemd/system/clipster_server.service
cp /path/to/old/Clipster-Server/db.sqlite3 data/db.sqlite3
grep SECRET_KEY /path/to/old/Clipster-Server/server/settings.py  # copy the value into .env
docker compose run --rm clipster python manage.py migrate clipster --fake
docker compose up -d
```

The `--fake` step is needed because the old install script generated its own migration files. They are named differently from the ones in this repo, although the resulting database tables are the same.

The container runs as user id 1000. If your user has a different id, run `sudo chown -R 1000:1000 data`.  
Note that clients previously connected to `https://<domain>:9999`. With the built-in Caddy setup the address is `https://<domain>` now.

## Development

Install [uv](https://docs.astral.sh/uv/), then:

```bash
export SECRET_KEY=dev DEBUG=true
uv run manage.py migrate
uv run manage.py test
uv run manage.py runserver
```
