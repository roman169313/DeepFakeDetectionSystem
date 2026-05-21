# VPS deployment (Django + Gunicorn + Nginx)

Runs **beside** Node/PM2 apps on port **8000** (localhost only). PM2 is not used or modified.

## Prerequisites

- **Python 3.10, 3.11, or 3.12** (required for `requirements.txt` / Django 5.1)
- MySQL database `ml_db` and user created
- Domain/subdomain DNS pointing to the VPS (for Nginx + HTTPS)
- ML `.h5` files in `deepFake/mlModel/`

### Fix: `No matching distribution found for Django==5.1.5`

Your venv was created with **old Python** (3.6/3.8/3.9). Django 5.1 needs **3.10+**.

```bash
python3 --version          # if < 3.10, install 3.11:
# Alma/RHEL/CentOS:
sudo dnf install python3.11 python3.11-devel
# Ubuntu/Debian:
sudo apt install python3.11 python3.11-venv python3.11-dev

cd /var/www/deepfake/DeepFakeDetectionSystem
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Cannot upgrade Python?** Use Django 4.2 on Python 3.9:

```bash
pip install -r requirements-py39.txt
```

### Fix: `mysqlclient` / `pkg-config` / `Can not find valid pkg-config name`

`requirements-py39.txt` and `requirements.txt` use **PyMySQL** (no compile). Pull latest code, then:

```bash
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-py39.txt
```

If you prefer **mysqlclient**, install headers first then set `DB_USE_MYSQLCLIENT=1` in `.env`:

```bash
sudo dnf install mariadb-devel gcc python3-devel pkgconfig   # Alma/RHEL/CentOS
# sudo apt install libmysqlclient-dev build-essential        # Ubuntu
pip install mysqlclient
```

## Quick start

```bash
# 1. Clone on the server
sudo mkdir -p /var/www/deepfake
sudo chown deploy:deploy /var/www/deepfake
git clone YOUR_REPO_URL /var/www/deepfake/DeepFakeDetectionSystem
cd /var/www/deepfake/DeepFakeDetectionSystem

# 2. Edit config (optional — defaults in deploy.sh)
export APP_USER=deploy
export APP_DIR=/var/www/deepfake/DeepFakeDetectionSystem
export NGINX_SERVER_NAME=deepfake.yourdomain.com

# 3. Configure secrets
cp .env.example .env
nano .env   # DJANGO_DEBUG=False, SECRET_KEY, DB_*, ALLOWED_HOSTS

# 4. Full deploy
chmod +x deploy/deploy.sh
./deploy/deploy.sh --full

# 5. HTTPS (optional)
sudo certbot --nginx -d deepfake.yourdomain.com
```

## Commands

| Flag | Action |
|------|--------|
| `--full` | apt packages, sync, venv, migrate, systemd, nginx |
| `--app` | venv + pip + migrate + collectstatic only |
| `--systemd` | Install/restart Gunicorn service |
| `--nginx` | Install Nginx site config |
| `--sync` | rsync repo → `APP_DIR` |

## After code updates

```bash
cd /var/www/deepfake/DeepFakeDetectionSystem
git pull
./deploy/deploy.sh --app
sudo systemctl restart deepfake
```

## Verify (PM2 untouched)

```bash
pm2 list
sudo systemctl status deepfake
curl -I http://127.0.0.1:8000
```

## Files

- `deploy.sh` — main installer
- `deepfake.service` — systemd unit template
- `nginx-deepfake.conf` — Nginx site template
