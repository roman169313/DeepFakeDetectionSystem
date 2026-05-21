#!/usr/bin/env bash
# Deploy Deep Fake Detection on Ubuntu VPS (alongside Node/PM2 apps).
# Usage:
#   chmod +x deploy/deploy.sh
#   ./deploy/deploy.sh --help
#   ./deploy/deploy.sh --full          # system deps + app + systemd + nginx
#   ./deploy/deploy.sh --app           # venv, pip, migrate, collectstatic only
#   ./deploy/deploy.sh --systemd       # install/refresh systemd unit
#   ./deploy/deploy.sh --nginx         # install nginx site config
#
# Before first run, edit the CONFIG section below.

set -euo pipefail

# =============================================================================
# CONFIG — edit these for your server
# =============================================================================
APP_USER="${APP_USER:-deploy}"
APP_GROUP="${APP_GROUP:-www-data}"
APP_DIR="${APP_DIR:-/var/www/deepfake/DeepFakeDetectionSystem}"
GUNICORN_BIND="${GUNICORN_BIND:-127.0.0.1:8000}"
NGINX_SERVER_NAME="${NGINX_SERVER_NAME:-deepfake.yourdomain.com}"
SYSTEMD_SERVICE="${SYSTEMD_SERVICE:-deepfake}"
PYTHON="${PYTHON:-python3}"

# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

log() { echo "[deploy] $*"; }
die() { echo "[deploy] ERROR: $*" >&2; exit 1; }

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing command: $1"
}

as_root() {
  if [[ "${EUID}" -ne 0 ]]; then
    sudo "$@"
  else
    "$@"
  fi
}

# Replace placeholders in template files
render_template() {
  local src="$1" dest="$2"
  sed -e "s|@APP_USER@|${APP_USER}|g" \
      -e "s|@APP_GROUP@|${APP_GROUP}|g" \
      -e "s|@APP_DIR@|${APP_DIR}|g" \
      -e "s|@GUNICORN_BIND@|${GUNICORN_BIND}|g" \
      -e "s|@NGINX_SERVER_NAME@|${NGINX_SERVER_NAME}|g" \
      "${src}" > "${dest}"
}

install_system_packages() {
  log "Installing system packages (apt)..."
  as_root apt-get update -qq
  as_root apt-get install -y \
    "${PYTHON}" "${PYTHON}-venv" "${PYTHON}-pip" "${PYTHON}-dev" \
    build-essential pkg-config \
    libmysqlclient-dev \
    ffmpeg libsndfile1 libsndfile1-dev \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 \
    libimage-exiftool-perl exiv2 \
    nginx
  log "System packages installed."
}

ensure_app_dir() {
  if [[ ! -d "${APP_DIR}" ]]; then
    log "Creating ${APP_DIR}..."
    as_root mkdir -p "$(dirname "${APP_DIR}")"
    as_root mkdir -p "${APP_DIR}"
    as_root chown -R "${APP_USER}:${APP_GROUP}" "$(dirname "${APP_DIR}")"
  fi
}

ensure_env_file() {
  local env_file="${APP_DIR}/.env"
  if [[ ! -f "${env_file}" ]]; then
    log "Creating ${env_file} from .env.example..."
    cp "${REPO_ROOT}/.env.example" "${env_file}"
    # Production defaults
    sed -i 's/DJANGO_DEBUG=True/DJANGO_DEBUG=False/' "${env_file}" 2>/dev/null || \
      sed -i '' 's/DJANGO_DEBUG=True/DJANGO_DEBUG=False/' "${env_file}"
    echo "DJANGO_ALLOWED_HOSTS=${NGINX_SERVER_NAME},127.0.0.1" >> "${env_file}"
    log "IMPORTANT: Edit ${env_file} — set DJANGO_SECRET_KEY and DB_PASSWORD"
  else
    log "Using existing ${env_file}"
  fi
}

setup_venv_and_deps() {
  log "Setting up Python venv in ${APP_DIR}..."
  cd "${APP_DIR}"
  if [[ ! -d venv ]]; then
    "${PYTHON}" -m venv venv
  fi
  # shellcheck disable=SC1091
  source venv/bin/activate
  pip install --upgrade pip wheel
  pip install -r requirements.txt
  log "Python dependencies installed."
}

django_prepare() {
  log "Running migrations and collectstatic..."
  cd "${APP_DIR}"
  # shellcheck disable=SC1091
  source venv/bin/activate
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
  mkdir -p media media/video_frames
  python manage.py migrate --noinput
  python manage.py collectstatic --noinput
  log "Django database and static files ready."
}

install_systemd() {
  log "Installing systemd unit: ${SYSTEMD_SERVICE}.service"
  local tmp="/tmp/${SYSTEMD_SERVICE}.service"
  render_template "${SCRIPT_DIR}/deepfake.service" "${tmp}"
  as_root cp "${tmp}" "/etc/systemd/system/${SYSTEMD_SERVICE}.service"
  as_root systemctl daemon-reload
  as_root systemctl enable "${SYSTEMD_SERVICE}"
  as_root systemctl restart "${SYSTEMD_SERVICE}"
  as_root systemctl --no-pager status "${SYSTEMD_SERVICE}" || true
  log "Service ${SYSTEMD_SERVICE} is running on ${GUNICORN_BIND}"
  log "PM2 / Node apps were not modified."
}

install_nginx() {
  log "Installing Nginx site for ${NGINX_SERVER_NAME}..."
  local tmp="/tmp/nginx-deepfake.conf"
  render_template "${SCRIPT_DIR}/nginx-deepfake.conf" "${tmp}"
  as_root cp "${tmp}" "/etc/nginx/sites-available/deepfake"
  as_root ln -sf /etc/nginx/sites-available/deepfake /etc/nginx/sites-enabled/deepfake
  as_root nginx -t
  as_root systemctl reload nginx
  log "Nginx configured. Site: http://${NGINX_SERVER_NAME}"
}

sync_code() {
  log "Syncing project files to ${APP_DIR}..."
  if [[ "${REPO_ROOT}" == "${APP_DIR}" ]]; then
    log "REPO_ROOT equals APP_DIR — skipping rsync."
    return
  fi
  need_cmd rsync
  rsync -a --delete \
    --exclude 'venv/' \
    --exclude '.env' \
    --exclude 'media/' \
    --exclude '__pycache__/' \
    --exclude '.git/' \
    "${REPO_ROOT}/" "${APP_DIR}/"
  log "Code synced."
}

usage() {
  cat <<EOF
Deep Fake Detection — VPS deploy script (does not touch PM2)

Config (env overrides):
  APP_USER=${APP_USER}
  APP_DIR=${APP_DIR}
  GUNICORN_BIND=${GUNICORN_BIND}
  NGINX_SERVER_NAME=${NGINX_SERVER_NAME}

Commands:
  --full       Install apt packages, sync code, venv, django, systemd, nginx
  --app        venv + pip + migrate + collectstatic (run from APP_DIR or sync first)
  --systemd    Install/refresh systemd unit and restart service
  --nginx      Install Nginx site and reload
  --sync       rsync repo to APP_DIR only
  --help       Show this help

Examples:
  APP_DIR=/var/www/deepfake/DeepFakeDetectionSystem NGINX_SERVER_NAME=df.example.com ./deploy/deploy.sh --full
  ./deploy/deploy.sh --app --systemd
EOF
}

main() {
  local cmd="${1:---help}"
  case "${cmd}" in
    --help|-h)
      usage
      ;;
    --sync)
      ensure_app_dir
      sync_code
      ;;
    --app)
      [[ -f "${APP_DIR}/manage.py" ]] || die "APP_DIR missing manage.py: ${APP_DIR}"
      ensure_env_file
      setup_venv_and_deps
      django_prepare
      ;;
    --systemd)
      install_systemd
      ;;
    --nginx)
      install_nginx
      ;;
    --full)
      need_cmd "${PYTHON}"
      install_system_packages
      ensure_app_dir
      sync_code
      as_root chown -R "${APP_USER}:${APP_GROUP}" "${APP_DIR}"
      cd "${APP_DIR}"
      ensure_env_file
      setup_venv_and_deps
      django_prepare
      install_systemd
      install_nginx
      log "Deploy complete."
      log "  Django:  ${GUNICORN_BIND} (systemd: ${SYSTEMD_SERVICE})"
      log "  Nginx:   http://${NGINX_SERVER_NAME}"
      log "  PM2:     unchanged — verify with: pm2 list"
      ;;
    *)
      usage
      die "Unknown option: ${cmd}"
      ;;
  esac
}

main "$@"
