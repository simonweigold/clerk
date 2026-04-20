# Docker Compose Deployment

Deploy Clerk using Docker Compose for a complete, production-ready multi-container setup.

---

## Quick Start

Get Clerk running in minutes with a single command:

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) 20.10+ installed
- [Docker Compose](https://docs.docker.com/compose/install/) 2.0+ installed
- Git (to clone the repository)

### One-Command Deployment

```bash
# Clone the repository
git clone https://github.com/your-org/clerk.git
cd clerk

# Copy environment template
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Start all services
docker-compose up
```

Once running, access Clerk at:
- **Frontend**: http://localhost (or http://localhost:8080 if FRONTEND_PORT is set)
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

To run in background mode:
```bash
docker-compose up -d
```

---

## Architecture Overview

Clerk uses a multi-container architecture with three main services:

```
┌─────────────────┐
│   User Request  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│     Frontend    │────▶│     Backend     │
│   (React/nginx) │     │  (Python/FastAPI)│
└─────────────────┘     └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   PostgreSQL    │
                        │    (Database)   │
                        └─────────────────┘
```

### Services

| Service | Technology | Purpose | Port |
|---------|------------|---------|------|
| **db** | PostgreSQL 16 | Persistent data storage | 5432 (internal) |
| **backend** | Python 3.13 + FastAPI | API server, LLM workflows | 8000 |
| **frontend** | React + nginx | Static UI, reverse proxy | 80 (configurable) |

### Data Flow

1. **User** accesses the frontend at `http://localhost`
2. **Frontend** (nginx) serves static React files and proxies API calls
3. **Backend** processes requests, runs reasoning workflows via LangChain
4. **Database** persists reasoning kits, evaluations, and user data

---

## Configuration

### Environment Variables

All configuration is managed through the `.env` file mounted into containers:

```bash
# Copy the template
cp .env.example .env

# Edit with your values
nano .env
```

**Key variables to configure:**

```env
# Required: Your OpenAI API key
OPENAI_API_KEY=sk-...

# Required: PostgreSQL connection (matches docker-compose defaults)
DATABASE_URL=postgresql://clerk:clerk@db:5432/clerk

# Optional: Host port for frontend (default: 80)
FRONTEND_PORT=8080
```

See [Environment Variables](./environment.md) for complete documentation.

### Required Variables

These must be set before starting:

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API access | `sk-...` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://clerk:clerk@db:5432/clerk` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FRONTEND_PORT` | `80` | Host port for accessing the UI |
| `POSTGRES_USER` | `clerk` | Database username |
| `POSTGRES_PASSWORD` | `clerk` | Database password |
| `POSTGRES_DB` | `clerk` | Database name |
| `LOG_LEVEL` | `info` | Application logging level |
| `SECRET_KEY` | auto-generated | Session signing key |

---

## Data Persistence

### Named Volumes

PostgreSQL data is stored in a named Docker volume:

```yaml
# docker-compose.yml
volumes:
  postgres_data:
    driver: local
```

This ensures data persists across container restarts and updates.

### Backup and Restore

**Create a backup:**
```bash
# Backup database to file
docker-compose exec db pg_dump -U clerk clerk > backup_$(date +%Y%m%d).sql
```

**Restore from backup:**
```bash
# Stop services
docker-compose down

# Restore database (this will overwrite existing data!)
docker-compose up -d db
docker-compose exec -T db psql -U clerk clerk < backup_20250325.sql

# Start all services
docker-compose up -d
```

**Volume location on host:**
```bash
# Find volume location
docker volume inspect clerk_postgres_data

# Default location on Linux
/var/lib/docker/volumes/clerk_postgres_data/_data
```

### Automatic Backups

Consider setting up automated backups with a cron job:

```bash
# Add to crontab (daily at 2 AM)
0 2 * * * cd /path/to/clerk && docker-compose exec -T db pg_dump -U clerk clerk > backups/clerk_$(date +\%Y\%m\%d).sql
```

---

## Updating

### Pull Latest Images

When a new version is released:

```bash
# Pull latest images
docker-compose pull

# Restart with new version
docker-compose up -d
```

### Database Migrations

If the update includes database schema changes:

```bash
# Check for pending migrations
docker-compose exec backend clerk db status

# Run migrations
docker-compose exec backend clerk db migrate

# Or restart to auto-run migrations
docker-compose up -d
```

### Rolling Back

If you need to revert:

```bash
# Stop current version
docker-compose down

# Restore database from backup (if needed)
docker-compose exec -T db psql -U clerk clerk < backup_before_update.sql

# Start previous version (specify tag if using versioned images)
docker-compose up -d
```

---

## Troubleshooting

### Check Logs

View logs for all services:
```bash
docker-compose logs -f
```

View logs for specific service:
```bash
docker-compose logs -f backend
docker-compose logs -f db
docker-compose logs -f frontend
```

### Database Connection Issues

**Symptom:** Backend fails to connect to database

**Check:**
```bash
# Verify database is running
docker-compose ps

# Check database logs
docker-compose logs db

# Test connection manually
docker-compose exec backend python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
async def test():
    engine = create_async_engine('postgresql+asyncpg://clerk:clerk@db:5432/clerk')
    async with engine.connect() as conn:
        result = await conn.execute('SELECT 1')
        print('Connection successful!')
asyncio.run(test())
"
```

**Common fixes:**
- Ensure `DATABASE_URL` in `.env` matches docker-compose database credentials
- Wait for database to fully start before backend attempts connection
- Check that the `db` service is healthy: `docker-compose ps`

### Port Conflicts

**Symptom:** "Port is already allocated" error

**Fix:** Change `FRONTEND_PORT` in `.env`:
```env
FRONTEND_PORT=8080
```

Then restart:
```bash
docker-compose down
docker-compose up -d
```

### Permission Denied

**Symptom:** Cannot write to volumes

**Fix:** On Linux, ensure your user has Docker permissions:
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Re-login or run:
newgrp docker
```

### Out of Memory

**Symptom:** Containers crash with OOM errors

**Check resource usage:**
```bash
docker stats
```

**Minimum recommended resources:**
- 2 CPU cores
- 4 GB RAM
- 10 GB disk space

---

## Advanced Options

### Running in Background

Use the `-d` (detach) flag:
```bash
docker-compose up -d
```

View logs:
```bash
docker-compose logs -f
```

Stop services:
```bash
docker-compose down
```

### Scaling Backend Replicas

For increased load, scale the backend horizontally:

```bash
# Run 3 backend instances
docker-compose up -d --scale backend=3
```

**Note:** Requires a load balancer or service mesh for request distribution.

### Custom Networks

For advanced networking scenarios:

```yaml
# docker-compose.yml
networks:
  clerk_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Health Checks

Services include built-in health checks:

```bash
# Check service health
docker-compose ps

# View health status
docker-compose exec backend curl -f http://localhost:8000/health || echo "Unhealthy"
```

### Resource Limits

Set resource constraints in `docker-compose.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

---

## Next Steps

- Configure [Environment Variables](./environment.md) for your deployment
- Review [Production Considerations](./production.md) before going live
- Set up HTTPS and domain configuration
- Configure automated backups

---

## Reference

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Clerk Environment Variables](./environment.md)
- [Production Deployment Guide](./production.md)
- [`docker-compose.yml` Reference](https://docs.docker.com/compose/compose-file/)
