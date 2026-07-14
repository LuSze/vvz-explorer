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
   # PostgreSQL password
   openssl rand -base64 32 > secrets/postgres_password.txt
   
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
- PostgreSQL + pgvector (internal)
- Backend: gunicorn 3 workers
- Frontend: Next.js standalone output

### VSETH Handover

When VSETH takes over hosting:

1. **Replace nginx** with their reverse proxy (Traefik/Caddy)
2. **Use their PostgreSQL** (managed instance)
3. **Configure their domain** (e.g., `vvz.vseth.ethz.ch`)
4. **Add their SSO/OIDC** for authentication
5. **Remove local nginx/certs** from compose

The `docker-compose.yml` is designed to work with external postgres by setting `DATABASE_URL`.

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DJANGO_SECRET_KEY` | Django signing key | Prod |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hosts | Prod |
| `CORS_ALLOWED_ORIGINS` | Comma-separated origins | Prod |
| `DATABASE_URL` | Postgres connection string | Prod |
| `POSTGRES_PASSWORD` | DB password (via secret) | Prod |
| `SECURE_SSL_REDIRECT` | Force HTTPS | Prod |
| `NEXT_PUBLIC_API_URL` | Backend API URL | Both |

### Data Persistence

- **PostgreSQL**: `pgdata` volume
- **Static files**: `staticfiles` volume (collected by Django)
- **SQLite databases**: `data/` folder (gitignored, for dev only)

### Monitoring

Add to prod profile:
- **Plausible/Umami** for analytics
- **Prometheus/Grafana** for metrics
- **Sentry** for error tracking

### Backup

```bash
# PostgreSQL backup
docker exec vvz-explorer-prod-postgres-1 pg_dump -U vvz vvz > backup_$(date +%F).sql

# Restore
cat backup.sql | docker exec -i vvz-explorer-prod-postgres-1 psql -U vvz vvz
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
| Embeddings not found | Run `./app/backend/embed.sh` first |
| CORS errors | Set `CORS_ALLOWED_ORIGINS` in prod |
| Static files 404 | Run `collectstatic` (done in Dockerfile) |
| Migration errors | `docker compose exec backend python manage.py migrate` |