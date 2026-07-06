# Deploying HabitFlow on a VPS

Complete walkthrough from a blank Ubuntu server to a live HTTPS deployment with
Telegram login and bot reminders. Assumes Ubuntu 22.04/24.04, a domain you control,
and a Telegram account.

**What you end up with:**

```
https://habitflow.example.com
        │
   [nginx :443] ─ TLS, security headers, gzip
        ├── /            → frontend (Nuxt, node)
        ├── /api, /health → api (FastAPI, uvicorn)
        └── (bot worker — no HTTP, talks to Telegram directly)
   [sqlite volume] shared by api + bot (WAL mode)
```

---

## 1. Create the Telegram bot

1. Open [@BotFather](https://t.me/BotFather) → `/newbot`.
2. Pick a display name and a username (must end in `bot`, e.g. `habitflow_prod_bot`).
3. Save the **bot token** (`123456789:AA...`) — this is `BOT_TOKEN`.
4. The username **without `@`** is `BOT_USERNAME`.
5. In the BotFather mini app: **Bot Settings → Web Login** — note the **Client ID**
   (this is `TG_CLIENT_ID`). You'll register your site URL there in step 7, once
   HTTPS is live.

## 2. Prepare the server

**Sizing**: 2 GB RAM minimum to build the images on the server itself (the Nuxt build
peaks well above 1 GB). On a 1–2 GB VPS, add swap first — the frontend build will
otherwise die with `JavaScript heap out of memory` (exit code 134):

```bash
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab   # persist across reboots
```

SSH in as root (or a sudo user):

```bash
apt update && apt upgrade -y

# Create a deploy user
adduser --disabled-password --gecos "" deploy
usermod -aG sudo deploy

# Basic firewall: SSH + HTTP + HTTPS only
apt install -y ufw
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
```

Install Docker (official repo, includes compose plugin):

```bash
curl -fsSL https://get.docker.com | sh
usermod -aG docker deploy
```

Log out and back in as `deploy` so the docker group applies:

```bash
su - deploy
docker ps        # should work without sudo
```

## 3. Point DNS at the server

At your DNS provider, create an **A record**:

```
habitflow.example.com  →  <server IPv4>
```

(Optionally an AAAA record for IPv6.) Wait until `dig +short habitflow.example.com`
returns the server IP before requesting certificates.

## 4. Clone and configure

```bash
git clone https://github.com/nurzhqn0/habit-tracker.git
cd habit-tracker

cp .env.example .env
nano .env
```

Set these values in `.env`:

```dotenv
ENVIRONMENT=production
JWT_SECRET=<paste output of: openssl rand -hex 32>
BOT_TOKEN=123456789:AA...            # from BotFather
BOT_USERNAME=habitflow_prod_bot      # without @
FRONTEND_ORIGIN=https://habitflow.example.com
TEST_MODE=false
```

> The API refuses to start in production with a missing/short `JWT_SECRET` or with
> `TEST_MODE=1` — if the api container crash-loops, check `docker compose logs api`.

## 5. First start (HTTP only)

```bash
docker compose up -d --build
docker compose ps          # nginx, api, frontend "Up"; api "healthy"; bot "Up"
curl -s localhost/health   # {"status":"ok"}
```

The site is now reachable at `http://habitflow.example.com`. Telegram login will not
work yet — the widget requires the registered HTTPS domain.

## 6. Enable TLS

Get certificates with certbot in standalone mode (nginx must be stopped for a moment,
or use the webroot/DNS method if you prefer):

```bash
sudo apt install -y certbot
docker compose stop nginx
sudo certbot certonly --standalone -d habitflow.example.com
docker compose start nginx
```

Copy the certificates where the nginx container reads them, and switch to the TLS
config:

```bash
sudo cp /etc/letsencrypt/live/habitflow.example.com/fullchain.pem nginx/certs/
sudo cp /etc/letsencrypt/live/habitflow.example.com/privkey.pem  nginx/certs/
sudo chown deploy: nginx/certs/*.pem

cp nginx/nginx-tls.conf.example nginx/nginx.conf
sed -i 's/habitflow.example.com/<your-domain>/g' nginx/nginx.conf

docker compose restart nginx
```

Verify: `https://habitflow.example.com` loads, `http://` redirects to `https://`.

**Auto-renewal** — certbot renews via systemd timer; add a deploy hook so nginx picks
up new certs:

```bash
sudo tee /etc/letsencrypt/renewal-hooks/deploy/habitflow.sh > /dev/null <<'EOF'
#!/bin/sh
DOMAIN=habitflow.example.com
APP=/home/deploy/habit-tracker
cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem $APP/nginx/certs/
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem  $APP/nginx/certs/
chown deploy: $APP/nginx/certs/*.pem
cd $APP && docker compose restart nginx
EOF
sudo chmod +x /etc/letsencrypt/renewal-hooks/deploy/habitflow.sh
```

## 7. Register the site with the bot

In the [@BotFather](https://t.me/BotFather) mini app: **Bot Settings → Web Login →
Allowed URLs** — add your site origin:

```
https://habitflow.example.com
```

Make sure `.env` has the matching `TG_CLIENT_ID` (shown on the same Web Login page),
then recreate the affected services if you just added it:

```bash
docker compose up -d --force-recreate api frontend
```

Now the **Sign in with Telegram** button works on the landing page (popup-based
OIDC flow; the backend verifies the returned id_token against Telegram's JWKS).
After logging in, open **Settings → Connect bot** and press **Start** in the chat —
reminders and room notifications are delivered from then on.

## 8. Backups

Manual snapshot (WAL-safe, uses the sqlite3 backup API inside the container):

```bash
make backup                # → backups/habitflow-YYYYmmdd-HHMMSS.db
```

Nightly cron at 03:30 with 14-day retention:

```bash
crontab -e
# add:
30 3 * * * cd /home/deploy/habit-tracker && make backup && find backups -name '*.db' -mtime +14 -delete
```

Copy backups off the server (rsync/rclone to object storage) for real durability.

**Restore**: stop the stack, replace the DB inside the volume, start again:

```bash
docker compose down
docker compose run --rm --no-deps -v ./backups:/restore api \
  sh -c "cp /restore/habitflow-<STAMP>.db /srv/app/data/habitflow.db"
docker compose up -d
```

## 9. Updating the app

```bash
cd ~/habit-tracker
make backup                          # snapshot before anything else
git pull
docker compose up -d --build         # rebuild changed images; alembic migrates on api start
docker compose ps                    # confirm healthy
```

Rollback = `git checkout <previous-tag-or-sha>` + same command (plus DB restore if a
migration changed the schema).

## 10. Operations cheat sheet

```bash
docker compose logs -f api           # API logs
docker compose logs -f bot           # bot worker (reminders, notifications)
docker compose ps                    # health overview
docker compose restart api           # bounce one service
docker system prune -f               # reclaim old image layers after updates
```

## Troubleshooting

| Symptom | Check |
|---|---|
| Frontend build dies with exit 134 / "heap out of memory" | Not enough RAM — add swap (step 2) and rerun `docker compose up -d --build` |
| api container restarts forever | `docker compose logs api` — usually the JWT_SECRET/TEST_MODE production guard or a bad `DATABASE_URL` |
| Telegram button missing, "Dev login" shown instead | `BOT_USERNAME` empty in `.env` → rebuild frontend: `docker compose up -d --build frontend` |
| Telegram login returns "Login failed" | Domain not set via `/setdomain`, or `BOT_TOKEN` mismatch between the bot that signed the widget payload and the API verifying it |
| Bot never messages users | User must press **Start** in the bot chat first (Settings → Connect bot); check `docker compose logs bot` |
| Reminders at the wrong time | User timezone in Settings; reminders fire in the user's timezone, server timezone is irrelevant |
| 401 loops in the UI | Clock skew on the server (JWT `exp`) — `timedatectl` should show NTP synchronized |
| Rate limit hits legitimate users | Confirm nginx is the only path to the API (uvicorn trusts `X-Forwarded-For`; don't expose port 8000 publicly) |

## Security notes

- Only ports 22/80/443 are open; the API and frontend are reachable exclusively
  through nginx.
- Production guard enforces a ≥32-char `JWT_SECRET`, disables `/docs`, and rejects
  `TEST_MODE`.
- Refresh tokens are stored hashed and rotate on every use; Telegram login payloads
  are HMAC-verified, expire after 24h, and are single-use.
- Auth endpoints are rate-limited per client IP (10/min login, 30/min refresh).
- Keep the server patched: `sudo apt update && sudo apt upgrade` on a schedule, and
  consider `unattended-upgrades`.
