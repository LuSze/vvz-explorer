# Deployment Guide

## Quick Start (Development)

```bash
cd vvz-explorer
docker compose --profile dev up
```

Services:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/

## Production Deployment

### Prerequisites

- Docker & Docker Compose v2+
- Domain name (or use Tailscale Funnel for testing)
- TLS certificates (Let's Encrypt or self-signed for internal)

### Configuration

1. **Copy and edit environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

2. **Generate secrets:**
   ```bash
   # Django secret key
   python -c "import secrets; print(secrets.token_urlsafe(32))" > secrets/django_secret.txt
   ```

3. **TLS certificates (for nginx):**
   ```bash
   mkdir -p nginx/certs
   # Place your fullchain.pem and privkey.pem in nginx/certs/
   # Or use Let's Encrypt with certbot
   ```

### Deploy

```bash
docker compose --profile prod up -d
```

Services:
- Nginx (ports 80/443) → Frontend (3000) + Backend (8000)
- SQLite + sqlite-vec (mounted volume)
- Backend: gunicorn 3 workers
- Frontend: Next.js standalone output


### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DJANGO_SECRET_KEY` | Django signing key | Prod |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hosts | Prod |
| `CORS_ALLOWED_ORIGINS` | Comma-separated origins | Prod |
| `SECURE_SSL_REDIRECT` | Force HTTPS | Prod |
| `NEXT_PUBLIC_API_URL` | Backend API URL | Both |

### Data Persistence

- **SQLite databases**: `data/` folder (gitignored, used for all environments)
- **Static files**: `staticfiles` volume (collected by Django)

### Monitoring

Add to prod profile:
- **Plausible/Umami** for analytics
- **Prometheus/Grafana** for metrics
- **Sentry** for error tracking

### Backup

```bash
# Backup SQLite databases
cp data/lectures_*.db data/embeddings_*.db /backup/

# Restore
cp /backup/*.db data/
```

## Tailscale Funnel (Quick Public Access)

For testing without a domain:

```bash
tailscale funnel 443
# Gives you https://<machine-name>.<tailnet>.ts.net
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `sqlite_vec` load failed | Ensure `sqlite-vec` is installed in backend image |
| Embeddings not found | Run `./backend/embed.sh` first |
| CORS errors | Set `CORS_ALLOWED_ORIGINS` in prod |
| Static files 404 | Run `collectstatic` (done in Dockerfile) |
| Migration errors | `docker compose exec backend python manage.py migrate` |