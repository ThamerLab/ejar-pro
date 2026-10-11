# Ejar Pro — Deployment Guide

> **Security:** Use trusted LAN/VPN or HTTPS with a protected reverse proxy. Do not expose this app publicly without a complete security review. Database contains personal and financial information.

## Docker Compose

```bash
git clone https://github.com/ThamerLab/ejar-pro.git
cd ejar-pro
cp env.example .env
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
# Edit .env: put a unique value in SECRET_KEY and strong ADMIN_PASSWORD
docker compose config
docker compose up -d --build
docker compose ps
```

Default address on the Docker host: **http://127.0.0.1:9090**. `BIND_IP=127.0.0.1` prevents direct LAN exposure. To access via reverse proxy, route to the host loopback listener where supported. To access from LAN, bind to a trusted network interface explicitly, and restrict it by firewall.

`SECRET_KEY` must be at least 32 characters and cannot be a placeholder. `ADMIN_PASSWORD` must be at least 14 characters on a **fresh database**, and cannot be a known default. The environment variables are required for Compose. On an existing database, changing `ADMIN_PASSWORD` does **not** reset the existing account.

For HTTPS deployments, set `SECURE_COOKIES=true` and make sure that the browser exclusively connects over HTTPS.

## Portainer Git Stack

1. In Portainer, select **Stacks → Add stack → Repository**.
2. Use URL `https://github.com/ThamerLab/ejar-pro`, branch `main`, and Compose path `docker-compose.yml`.
3. Supply `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `APP_PORT`, `BIND_IP`, and `SECURE_COOKIES` as appropriate.
4. Ensure your Portainer/Docker environment supports the `build: .` context from this Git repository. Otherwise, build the image separately and adjust the stack.
5. Deploy and check the container logs and application page.

## Backup / restore

SQLite database: `/data/ejar.db` inside the container; Docker volume: `ejar_data` under the Compose project namespace. The actual volume name may be prefixed by the stack name.

Before upgrading, create a consistent backup. Use SQLite's backup API or stop the application before copying the DB from the volume. Do not assume `docker cp` of a live database is consistent. Keep backups encrypted, and do not store sensitive tenant records in Git.

Before restoring, stop application writes, retain an additional copy of the existing data, restore the SQLite backup and verify the application using the **same `SECRET_KEY`** if preserving session compatibility matters.

## Logs and troubleshooting

```bash
docker compose ps
docker compose logs --tail=100 ejar-pro
docker compose config
```

- Missing SECRET_KEY or ADMIN_PASSWORD: edit the local `.env` or Portainer stack environment. Placeholders are intentionally rejected.
- Browser connection refused: inspect `BIND_IP`, `APP_PORT`, reverse proxy, and firewall. Default is port **9090**, bound only to localhost.
- Login rejected after an update: stored user password hashes are not replaced by changing `.env`.
- Data seems missing: check the expected Compose stack name and persisted Docker volume before starting a fresh instance.

## Operational limits

The backend uses SQLite and initializes demo content on a fresh installation. Review and remove demonstration entries before entering real business records. Manual migrations, input validation, role enforcement, CSRF, financial atomicity and recovery should be assessed before production.
