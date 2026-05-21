# Manual deployment (Gunicorn + Nginx + optional PM2)

Replace these values everywhere:

| Variable | Example |
|----------|---------|
| `APP_DIR` | `/var/www/deepfake/DeepFakeDetectionSystem` |
| `APP_USER` | `root` or `deploy` |
| `DOMAIN` | `deepfake.yourdomain.com` |
| `GUNICORN_PORT` | `8000` (must not conflict with PM2 Node ports) |

---

## 1. `.env` (required)

```bash
cd /var/www/deepfake/DeepFakeDetectionSystem
cp .env.production.example .env
nano .env
```

```env
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=your-long-random-secret
DJANGO_ALLOWED_HOSTS=deepfake.yourdomain.com,YOUR_SERVER_IP

DB_NAME=ml_db
DB_USER=deepfake_user
DB_PASSWORD=your_mysql_password
DB_HOST=127.0.0.1
DB_PORT=3306

TF_USE_LEGACY_KERAS=1
```

```bash
source venv/bin/activate
export TF_USE_LEGACY_KERAS=1
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

---

## 2. Gunicorn (test by hand)

```bash
cd /var/www/deepfake/DeepFakeDetectionSystem
source venv/bin/activate
export TF_USE_LEGACY_KERAS=1
export TF_ENABLE_ONEDNN_OPTS=0

# Option A — command line
gunicorn deepFakeDetection.wsgi:application \
  --bind 127.0.0.1:8000 \
  --workers 1 \
  --threads 2 \
  --timeout 300 \
  --access-logfile - \
  --error-logfile -

# Option B — config file
gunicorn -c deploy/gunicorn.conf.py deepFakeDetection.wsgi:application
```

Test: `curl -I http://127.0.0.1:8000` then Ctrl+C.

---

## 3. systemd (recommended — not PM2)

Create `/etc/systemd/system/deepfake.service`:

```ini
[Unit]
Description=Deep Fake Detection (Django/Gunicorn)
After=network.target mysqld.service
Wants=mysqld.service

[Service]
Type=simple
User=root
Group=www-data
WorkingDirectory=/var/www/deepfake/DeepFakeDetectionSystem
EnvironmentFile=/var/www/deepfake/DeepFakeDetectionSystem/.env
Environment=PATH=/var/www/deepfake/DeepFakeDetectionSystem/venv/bin
Environment=TF_USE_LEGACY_KERAS=1
Environment=TF_ENABLE_ONEDNN_OPTS=0

ExecStart=/var/www/deepfake/DeepFakeDetectionSystem/venv/bin/gunicorn \
    -c /var/www/deepfake/DeepFakeDetectionSystem/deploy/gunicorn.conf.py \
    deepFakeDetection.wsgi:application

Restart=on-failure
RestartSec=5
KillMode=mixed
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
```

Enable:

```bash
sudo systemctl daemon-reload
sudo systemctl enable deepfake
sudo systemctl start deepfake
sudo systemctl status deepfake
sudo journalctl -u deepfake -f
```

---

## 4. PM2 (optional alternative to systemd)

Edit paths in `deploy/ecosystem.config.js`, then:

```bash
cd /var/www/deepfake/DeepFakeDetectionSystem
pm2 start deploy/ecosystem.config.js
pm2 save
pm2 list
pm2 logs deepfake-django
```

**Do not** run both systemd `deepfake` and PM2 `deepfake-django` on the same port.

---

## 5. Nginx

### RHEL / Alma / CentOS (`/etc/nginx/conf.d/`)

Create `/etc/nginx/conf.d/deepfake.conf`:

```nginx
server {
    listen 80;
    server_name deepfake.yourdomain.com;

    client_max_body_size 100M;

    location /static/ {
        alias /var/www/deepfake/DeepFakeDetectionSystem/staticfiles/;
    }

    location /media/ {
        alias /var/www/deepfake/DeepFakeDetectionSystem/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

### Ubuntu / Debian (`sites-available`)

```bash
sudo cp deploy/nginx-deepfake.conf /etc/nginx/sites-available/deepfake
# Edit server_name and paths (replace @APP_DIR@ → real path, @NGINX_SERVER_NAME@ → domain)
sudo ln -s /etc/nginx/sites-available/deepfake /etc/nginx/sites-enabled/
```

### Reload Nginx

```bash
sudo nginx -t
sudo systemctl reload nginx
```

HTTPS:

```bash
sudo certbot --nginx -d deepfake.yourdomain.com
```

---

## 6. Verify (PM2 Node apps unchanged)

```bash
pm2 list
curl -I http://127.0.0.1:8000
curl -I http://deepfake.yourdomain.com
```

---

## 7. Restart after code update

**systemd:**

```bash
cd /var/www/deepfake/DeepFakeDetectionSystem
git pull
source venv/bin/activate
pip install -r requirements-py39.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart deepfake
```

**PM2:**

```bash
pm2 restart deepfake-django
```
