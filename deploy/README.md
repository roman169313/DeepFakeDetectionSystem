# VPS deployment (Django + Gunicorn + Nginx)

Runs **beside** Node/PM2 apps on port **8000** (localhost only). PM2 is not used or modified.

## Prerequisites

- Ubuntu 22.04+ VPS
- MySQL database `ml_db` and user created
- Domain/subdomain DNS pointing to the VPS (for Nginx + HTTPS)
- ML `.h5` files in `deepFake/mlModel/`

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
