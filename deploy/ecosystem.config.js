/**
 * PM2 config (OPTIONAL — systemd + Gunicorn is recommended for Django).
 * Use only if you prefer PM2 over systemd. Does not affect other PM2 apps
 * if you use a different name/port.
 *
 * Start:  pm2 start deploy/ecosystem.config.js
 * Save:   pm2 save
 * Logs:   pm2 logs deepfake-django
 */
module.exports = {
  apps: [
    {
      name: "deepfake-django",
      cwd: "/var/www/deepfake/DeepFakeDetectionSystem",
      script: "/var/www/deepfake/DeepFakeDetectionSystem/venv/bin/gunicorn",
      args: [
        "-c",
        "deploy/gunicorn.conf.py",
        "deepFakeDetection.wsgi:application",
      ],
      interpreter: "none",
      instances: 1,
      exec_mode: "fork",
      autorestart: true,
      max_memory_restart: "3G",
      env: {
        DJANGO_SETTINGS_MODULE: "deepFakeDetection.settings",
        TF_USE_LEGACY_KERAS: "1",
        TF_ENABLE_ONEDNN_OPTS: "0",
      },
      env_file: "/var/www/deepfake/DeepFakeDetectionSystem/.env",
    },
  ],
};
