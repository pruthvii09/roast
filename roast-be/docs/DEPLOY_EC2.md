# Deploying to a free-tier EC2 instance

A cheap, single-box deployment for a hobby-scale instance of this app: Django/Celery/Postgres/
Redis all self-hosted in Docker on one EC2 instance, fronted by Caddy for free automatic HTTPS.
The Next.js frontend deploys separately to Vercel's free tier (its own git integration — not
covered by the scripts here). Every step that touches your AWS/GitHub/Vercel accounts is yours
to run — I can't do those for you — but every script/config file referenced below is already in
this repo.

## Why HTTPS is required even without a domain

Vercel always serves the frontend over HTTPS. Browsers block an HTTPS page from calling a
plain-HTTP API ("mixed content") — no workaround exists client-side. So the backend needs a real
TLS certificate, which needs a real hostname (not a bare IP — Certificate Authorities won't issue
for one). If you don't want to buy a domain, **sslip.io** solves this for free: it's a wildcard
DNS service with no signup — `<ip-with-dashes>.sslip.io` automatically resolves to that IP. e.g.
if your instance's IP is `3.15.22.10`, then `3-15-22-10.sslip.io` just works, today, with zero
configuration on your end. Caddy (already wired into `docker-compose.ec2.yml`) uses that
hostname to request and auto-renew a free Let's Encrypt certificate.

## 1. Launch the instance

1. EC2 console -> Launch instance.
2. AMI: **Ubuntu Server 24.04 LTS**.
3. Instance type: **t2.micro** or **t3.micro** (both free-tier eligible — check the "Free tier
   eligible" badge in the console, terms/eligibility do change, so verify against your own
   account rather than trusting this doc blindly).
4. Key pair: create a new one, download the `.pem`, keep it safe — you can't re-download it.
5. Network settings -> Edit security group rules. You want exactly three inbound rules:
   - SSH (22) — source: **My IP** (not 0.0.0.0/0 — no reason to expose SSH to the whole internet)
   - HTTP (80) — source: Anywhere (0.0.0.0/0) — needed for Let's Encrypt's ACME challenge
   - HTTPS (443) — source: Anywhere (0.0.0.0/0)
   - **Do not add a rule for 8000.** Caddy is the only thing that should be internet-reachable;
     `web` stays reachable only from inside the box/Docker network.
6. Storage: the default (usually 8GB gp3) is fine; free tier covers up to 30GB if you want more
   headroom for Docker images/logs.
7. Launch, then allocate an **Elastic IP** (EC2 console -> Elastic IPs -> Allocate) and associate
   it with the instance. This keeps the public IP stable across reboots — otherwise it changes
   every time you stop/start the instance, which breaks your sslip.io hostname, your GitHub
   Actions secret, and your Vercel env var every time. An Elastic IP is free *as long as it's
   attached to a running instance* — AWS bills for one sitting unattached or attached to a
   stopped instance, so don't allocate one and then stop the instance for a long period.

## 2. First-time server setup

SSH in once:
```bash
ssh -i /path/to/your-key.pem ubuntu@<elastic-ip>
```

You haven't pushed this repo to GitHub yet at this point, so the bootstrap script needs the repo
URL explicitly the first time:
```bash
curl -fsSL https://raw.githubusercontent.com/<you>/roast-be/main/scripts/ec2-bootstrap.sh -o bootstrap.sh
REPO_URL=https://github.com/<you>/roast-be.git bash bootstrap.sh
```
(That `curl` will 404 until you've actually pushed the repo — see step 3 first if you're doing
this in order. Alternatively just `scp scripts/ec2-bootstrap.sh` up and run it locally, or paste
its contents into a file over SSH — it doesn't need to come from GitHub, that's just convenient
once the repo exists.)

This script (idempotent, safe to re-run):
- Installs a 2GB swap file — **not optional** on a 1GB-RAM instance. Without it, the first
  `docker compose build` (compiling Python deps) will very likely OOM-kill itself partway
  through.
- Installs Docker Engine + the Compose plugin from Docker's official apt repo.
- Clones this repo into `/opt/roast-be`.
- Copies `.env.prod.example` to `.env` if one doesn't exist yet — it must be named exactly
  `.env`, not `.env.prod`: `docker-compose.prod.yml`'s services hardcode `env_file: - .env`
  (a literal path), which the `--env-file` CLI flag does **not** redirect — that flag only
  affects `${VAR}` substitution within the compose YAML itself. Naming it anything else means
  the containers silently get none of your real config.

Then:
```bash
# if this was Docker's first install on the box:
newgrp docker

nano /opt/roast-be/.env   # fill in every <CHANGE ME>
```

Fields that need real values — see `.env.prod.example`'s comments for what each does:
- `DJANGO_SECRET_KEY` — generate with `python3 -c "import secrets; print(secrets.token_urlsafe(50))"`
- `DJANGO_ALLOWED_HOSTS` and `SITE_ADDRESS` — both the same sslip.io hostname, e.g. `3-15-22-10.sslip.io`
- `POSTGRES_PASSWORD` — any strong random string
- `OPENAI_API_KEY` — from platform.openai.com, if you want real (non-stub) roast generation
- `CORS_ALLOWED_ORIGINS` and `FRONTEND_SHARE_BASE_URL` — your Vercel URL (step 5 below — it's
  fine to come back and fill these in after Vercel gives you the URL)

## 3. Push this repo to GitHub

This repo isn't a git checkout yet. From your machine:
```bash
cd roast-be
git init
git add .
git commit -m "Initial commit"
gh repo create roast-be --private --source=. --remote=origin --push
# or, without the gh CLI: create the repo on github.com first, then
#   git remote add origin https://github.com/<you>/roast-be.git
#   git push -u origin main
```

## 4. First manual deploy

Back on the SSH session:
```bash
cd /opt/roast-be
bash scripts/deploy.sh
```
This builds the image and starts `db`, `redis`, `web`, `worker`, `beat`, and `caddy`. The first
build on a 1-vCPU box will genuinely take a few minutes — that's expected. Once it finishes,
confirm:
```bash
curl https://<your-sslip.io-hostname>/api/v1/health/ready/
```
should return `{"status":"ok", ...}` with all three checks (database/redis/celery) healthy. If
Caddy can't get a cert yet (DNS/security-group issue), `docker compose -f docker-compose.prod.yml
-f docker-compose.ec2.yml logs caddy` is the first place to look.

## 5. Deploy the frontend to Vercel

1. vercel.com -> Add New -> Project -> import the `roast-fe` GitHub repo (push it the same way as
   step 3, as its own separate repo).
2. Set the environment variable `NEXT_PUBLIC_API_BASE_URL` to `https://<your-sslip.io-hostname>`.
3. Deploy. Vercel gives you a `https://<something>.vercel.app` URL.
4. Go back to `.env` on the EC2 box and set `CORS_ALLOWED_ORIGINS` /
   `FRONTEND_SHARE_BASE_URL` to that exact URL, then re-run `bash scripts/deploy.sh` (or just push
   to `main` once GitHub Actions is wired up — see step 6) so the change takes effect.

## 6. Wire up auto-deploy on push

In the `roast-be` GitHub repo -> Settings -> Secrets and variables -> Actions, add:
- `EC2_HOST` — the Elastic IP
- `EC2_USER` — `ubuntu`
- `EC2_SSH_KEY` — the full contents of the `.pem` file from step 1 (including the
  `-----BEGIN/END-----` lines)

`.github/workflows/deploy.yml` is already in the repo — the next push to `main` will SSH in and
run `scripts/deploy.sh` automatically. You can also trigger it manually from the Actions tab
(`workflow_dispatch`) without needing an empty commit.

## Cost notes (staying inside free tier)

- t2.micro/t3.micro + a single Elastic IP *attached to a running instance* + up to 30GB EBS is
  the free-tier envelope — verify current terms in your own AWS account, they do change.
- Nothing here uses RDS, ElastiCache, a load balancer, or a NAT gateway — all of those cost money
  even at low usage, which is why Postgres/Redis run self-hosted in Docker on the same box
  instead (this is also what `docker-compose.prod.yml`'s own top-of-file comment recommends
  moving away from *once you outgrow* a single-host hobby deploy, not before).
- Watch the AWS Billing dashboard for the first few days after launch to catch anything
  unexpected before it accumulates.
- Set up `scripts/backup_db.sh` (see `docs/BACKUP_RECOVERY.md`) if this ever holds data you'd
  actually miss — self-hosted Postgres on a single box has no automated backup by default.

## What this deliberately doesn't do

This is a hobby/demo-shaped deploy, not the "real production" setup `docs/PRODUCTION_READINESS.md`
§5 describes (managed Postgres/Redis, log aggregation, a secrets manager, multi-instance `web`).
If this project ever needs to handle real user data at real scale, read that section — the
storage abstraction, the throttle/quota system, and `docker-compose.prod.yml`'s own comments are
all already written with that migration path in mind.
