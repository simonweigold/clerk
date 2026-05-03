# Production Deployment Guide

Best practices for deploying Clerk in production environments with HTTPS, security hardening, scaling, and monitoring.

---

## HTTPS Setup

HTTPS is **essential** for production deployments to protect sensitive data and API keys in transit.

### Option 1: Reverse Proxy (Recommended)

Use nginx, Traefik, or Caddy as a reverse proxy with SSL termination.

#### nginx Configuration

```nginx
# /etc/nginx/sites-available/clerk
server {
    listen 80;
    server_name clerk.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name clerk.example.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/clerk.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/clerk.example.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Frontend
    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Enable configuration:**
```bash
sudo ln -s /etc/nginx/sites-available/clerk /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### Traefik Configuration (Docker Compose)

```yaml
# docker-compose.yml
services:
  traefik:
    image: traefik:v3.0
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@example.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "./letsencrypt:/letsencrypt"

  frontend:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.frontend.rule=Host(`clerk.example.com`)"
      - "traefik.http.routers.frontend.entrypoints=websecure"
      - "traefik.http.routers.frontend.tls.certresolver=letsencrypt"
```

### Option 2: Let's Encrypt Certificates

**Using Certbot:**
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d clerk.example.com

# Auto-renewal (automatically configured)
sudo certbot renew --dry-run
```

**Using acme.sh:**
```bash
# Install acme.sh
curl https://get.acme.sh | sh

# Issue certificate
~/.acme.sh/acme.sh --issue -d clerk.example.com --nginx

# Install certificate
~/.acme.sh/acme.sh --install-cert -d clerk.example.com \
  --key-file /etc/nginx/ssl/clerk.key \
  --fullchain-file /etc/nginx/ssl/clerk.crt \
  --reloadcmd "systemctl reload nginx"
```

### Option 3: Cloudflare Proxy

Use Cloudflare as a CDN and SSL provider:

1. **Add your domain to Cloudflare**
2. **Update DNS** to point to Cloudflare
3. **Enable SSL/TLS**:
   - SSL/TLS mode: **Full (strict)**
   - Always Use HTTPS: **On**
   - Automatic HTTPS Rewrites: **On**
4. **Update VITE_API_URL**:
   ```env
   VITE_API_URL=https://clerk.example.com/api
   ```

### Updating VITE_API_URL for HTTPS

After setting up HTTPS, update the frontend environment variable:

```env
# Before (HTTP)
VITE_API_URL=http://localhost:8000

# After (HTTPS)
VITE_API_URL=https://clerk.example.com/api
```

Then rebuild and restart:
```bash
docker-compose down
docker-compose up -d --build
```

---

## Database Security

### Strong Passwords

Generate secure database passwords:

```bash
# Generate strong password
openssl rand -base64 32

# Update .env
POSTGRES_PASSWORD=your-generated-password
```

### Network Isolation

**Never expose PostgreSQL port (5432) publicly.**

Verify in `docker-compose.yml`:
```yaml
services:
  db:
    # Do NOT add ports section for production
    # ports:
    #   - "5432:5432"  # ❌ Never do this in production
    
    # Only internal network access
    networks:
      - clerk_network
```

### Regular Backups

**Automated backup script:**
```bash
#!/bin/bash
# /opt/clerk/backup.sh

BACKUP_DIR="/backups/clerk"
DATE=$(date +%Y%m%d_%H%M%S)
FILENAME="clerk_backup_${DATE}.sql"

# Create backup
docker-compose exec -T db pg_dump -U clerk clerk > "${BACKUP_DIR}/${FILENAME}"

# Compress
gzip "${BACKUP_DIR}/${FILENAME}"

# Keep only last 30 days
find "${BACKUP_DIR}" -name "clerk_backup_*.sql.gz" -mtime +30 -delete

# Optional: Encrypt backup
gpg --symmetric --cipher-algo AES256 "${BACKUP_DIR}/${FILENAME}.gz"
rm "${BACKUP_DIR}/${FILENAME}.gz"
```

**Cron job for daily backups:**
```bash
# Edit crontab
sudo crontab -e

# Add line for daily 2 AM backup
0 2 * * * /opt/clerk/backup.sh >> /var/log/clerk-backup.log 2>&1
```

### Backup Encryption

Encrypt backups before storing offsite:

```bash
# Encrypt with GPG
gpg --symmetric --cipher-algo AES256 backup.sql

# Decrypt when needed
gpg --decrypt backup.sql.gpg > backup.sql
```

### Point-in-Time Recovery

Enable PostgreSQL WAL archiving for point-in-time recovery:

```yaml
services:
  db:
    command: >
      postgres
      -c wal_level=replica
      -c archive_mode=on
      -c archive_command='test ! -f /backups/wal/%f && cp %p /backups/wal/%f'
```

---

## Application Security

### Strong SECRET_KEY

Generate a cryptographically secure session key:

```bash
# Recommended: 64 characters (32 bytes hex)
openssl rand -hex 32
```

Update `.env`:
```env
CLERK_SESSION_SECRET=a1b2c3d4e5f6...64-char-hex-string
```

### OPENAI_API_KEY Protection

- Store in `.env` file with `chmod 600` permissions
- Rotate keys every 90 days
- Use separate keys for dev/staging/production
- Monitor usage on OpenAI dashboard
- Set up spending alerts

### Rate Limiting

Consider adding rate limiting at the reverse proxy level:

```nginx
# nginx rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

server {
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://backend;
    }
    
    location /api/auth/ {
        limit_req zone=login burst=5 nodelay;
        proxy_pass http://backend;
    }
}
```

### Input Validation

Clerk includes built-in input validation via Pydantic models. Ensure:
- Validation schemas are up to date
- Error messages don't leak sensitive info
- File uploads have size and type restrictions

### Security Headers

The frontend nginx configuration already includes security headers:

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
```

---

## Scaling Considerations

### Horizontal Scaling: Backend Replicas

Scale backend horizontally by running multiple instances:

```yaml
services:
  backend:
    deploy:
      replicas: 3
    environment:
      - DATABASE_URL=postgresql+asyncpg://clerk:pass@db:5432/clerk
```

**Note:** Requires sticky sessions or stateless authentication for WebSocket support.

### Database Read Replicas

For read-heavy workloads, consider PostgreSQL read replicas:

```yaml
services:
  backend:
    environment:
      - DATABASE_URL=postgresql+asyncpg://clerk:pass@db-primary:5432/clerk
      - DATABASE_READ_URL=postgresql+asyncpg://clerk:pass@db-replica:5432/clerk
```

### Connection Pooling with PgBouncer

Add PgBouncer to reduce database connection overhead:

```yaml
services:
  pgbouncer:
    image: pgbouncer/pgbouncer:latest
    environment:
      DATABASES_HOST: db
      DATABASES_PORT: 5432
      DATABASES_DATABASE: clerk
      POOL_MODE: transaction
      MAX_CLIENT_CONN: 1000
      DEFAULT_POOL_SIZE: 25
```

### Load Balancing

**nginx upstream configuration:**
```nginx
upstream backend {
    least_conn;
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
    keepalive 32;
}

server {
    location /api/ {
        proxy_pass http://backend;
    }
}
```

### When to Scale vs Optimize

| Metric | Threshold | Action |
|--------|-----------|--------|
| CPU > 80% | Sustained 5 min | Scale up replicas |
| Memory > 80% | Sustained 5 min | Optimize or scale |
| DB connections > 80% | Peak hours | Add PgBouncer |
| Response time > 500ms | P95 | Optimize queries |
| Error rate > 1% | Any | Investigate bugs |

---

## Monitoring & Logging

### Centralized Logging

Forward container logs to external system:

```yaml
services:
  backend:
    logging:
      driver: "fluentd"
      options:
        fluentd-address: localhost:24224
        tag: clerk.backend
```

**Docker logging drivers:**
- `json-file` (default)
- `syslog`
- `journald`
- `fluentd`
- `awslogs`
- `gcplogs`

### Health Check Endpoints

Clerk provides health check endpoints:

```bash
# Liveness probe
curl -f http://localhost:8000/health/live || echo "Not live"

# Readiness probe
curl -f http://localhost:8000/health/ready || echo "Not ready"

# Full health check
curl http://localhost:8000/health
```

**Docker Compose health checks:**
```yaml
services:
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Metrics Collection

Export metrics to Prometheus:

```yaml
services:
  backend:
    environment:
      - METRICS_ENABLED=true
      - METRICS_PORT=9090
```

**Prometheus scrape configuration:**
```yaml
scrape_configs:
  - job_name: 'clerk'
    static_configs:
      - targets: ['clerk:9090']
```

### Alerting

**Prometheus AlertManager example:**
```yaml
groups:
  - name: clerk
    rules:
      - alert: ClerkHighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
      
      - alert: ClerkDown
        expr: up{job="clerk"} == 0
        for: 1m
        labels:
          severity: critical
```

### Log Retention

Set log retention policies:

```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "5"
```

---

## Updates & Maintenance

### Zero-Downtime Deployments

Use blue-green deployment or rolling updates:

```bash
# Rolling update
docker-compose up -d --no-deps --build backend

# Verify new version
curl -f http://localhost:8000/health

# If failed, rollback
docker-compose up -d --no-deps backend-previous
```

### Database Migration Strategy

**Pre-deployment:**
```bash
# Test migrations in staging
docker-compose -f docker-compose.staging.yml exec backend clerk db migrate
```

**Production deployment:**
```bash
# 1. Backup database first
./backup.sh

# 2. Run migrations
docker-compose exec backend clerk db migrate

# 3. Deploy new code
docker-compose up -d --build

# 4. Verify
curl -f http://localhost:8000/health
```

### Rollback Procedures

**Code rollback:**
```bash
# Revert to previous image tag
docker-compose down
docker-compose -f docker-compose.yml -f docker-compose.previous.yml up -d
```

**Database rollback:**
```bash
# Restore from backup
docker-compose down
docker-compose up -d db
docker-compose exec -T db psql -U clerk clerk < backup_before_migration.sql
```

### Version Pinning

Pin Docker images to specific versions:

```yaml
services:
  db:
    image: postgres:16.2-alpine  # Pin to minor version
  
  backend:
    image: clerk/backend:v1.2.3  # Pin to exact version
```

---

## Resource Planning

### Minimum Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 cores | 4 cores |
| RAM | 4 GB | 8 GB |
| Disk | 20 GB SSD | 50 GB SSD |
| Network | 100 Mbps | 1 Gbps |

### PostgreSQL Memory Tuning

Optimize PostgreSQL for available memory:

```yaml
services:
  db:
    command: >
      postgres
      -c shared_buffers=2GB
      -c effective_cache_size=6GB
      -c maintenance_work_mem=512MB
      -c work_mem=16MB
      -c max_connections=200
```

**Memory allocation guide:**

| Total RAM | shared_buffers | effective_cache_size |
|-----------|----------------|---------------------|
| 4 GB | 1 GB | 3 GB |
| 8 GB | 2 GB | 6 GB |
| 16 GB | 4 GB | 12 GB |
| 32 GB | 8 GB | 24 GB |

### Connection Limits

Adjust connection limits based on expected load:

```yaml
services:
  db:
    command: >
      postgres
      -c max_connections=200
      -c superuser_reserved_connections=3
```

**Connection formula:**
```
max_connections = (backend_replicas × connection_pool_size) + buffer
                = (3 × 20) + 20 = 80
```

### Storage Growth Estimation

Estimate disk space requirements:

| Data Type | Size Estimate | Growth Rate |
|-----------|---------------|-------------|
| Base installation | 2 GB | Fixed |
| PostgreSQL data | 1 GB per 10k kits | +10% monthly |
| Logs | 100 MB/day | Rotated |
| Backups | 2x database size | Weekly full + daily incremental |

**Formula:**
```
Total Storage = Base + (DB Size × 3) + (Logs × Retention)
              = 2 GB + (10 GB × 3) + (100 MB × 30)
              = 35 GB minimum
```

---

## Production Checklist

### Pre-Deployment

- [ ] Environment variables configured
- [ ] `.env` file permissions set to `600`
- [ ] Strong passwords generated for database
- [ ] `CLERK_SESSION_SECRET` changed from default
- [ ] HTTPS configured with valid SSL certificate
- [ ] Domain DNS configured correctly
- [ ] Firewall rules configured (only 80/443 exposed)
- [ ] Database backups tested

### Post-Deployment

- [ ] Health check endpoints responding
- [ ] Frontend loads without mixed content warnings
- [ ] API requests succeed (test with curl)
- [ ] WebSocket connections working
- [ ] Login/logout functionality working
- [ ] File uploads working
- [ ] Error pages displaying correctly

### Monitoring Verification

- [ ] Log aggregation working
- [ ] Metrics collection active
- [ ] Alerting rules tested
- [ ] Dashboards configured
- [ ] On-call rotation established

### Backup Verification

- [ ] Automated backups running
- [ ] Backup files being created
- [ ] Backup restoration tested
- [ ] Offsite backup configured
- [ ] Backup encryption working

### Security Verification

- [ ] SSL Labs A+ rating achieved
- [ ] Security headers present
- [ ] Rate limiting active
- [ ] No sensitive data in logs
- [ ] Database port not exposed
- [ ] File permissions correct

---

## Environment File Security

Protect your `.env` file with proper permissions:

```bash
# Set owner-only read/write permissions
chmod 600 .env

# Verify permissions
ls -la .env
# Output should show: -rw-------

# Ensure correct ownership
sudo chown $USER:$USER .env
```

**What `chmod 600` means:**
- Owner: read and write (6 = 4+2)
- Group: no permissions (0)
- Others: no permissions (0)

**Verify in deployment:**
```bash
# Check on production server
ssh user@server "ls -la /opt/clerk/.env"
# Should show: -rw------- 1 clerk clerk
```

---

## Related Documentation

- [Docker Compose Deployment](./docker.md)
- [Environment Variables](./environment.md)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [PostgreSQL Security Guide](https://www.postgresql.org/docs/current/security.html)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
