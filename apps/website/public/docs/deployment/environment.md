# Environment Variables Reference

Complete reference for all Clerk environment variables with descriptions, defaults, and security best practices.

---

## Overview

Clerk uses environment variables for all configuration. These are loaded from a `.env` file mounted into Docker containers at runtime.

### How Environment Variables Work

1. **Create `.env` file**: Copy from `.env.example` template
2. **Mount into containers**: Docker Compose mounts `.env` automatically
3. **Variable substitution**: Values are injected into running containers
4. **Security**: File permissions should be restricted (`chmod 600 .env`)

### Basic Usage

```bash
# Copy template
cp .env.example .env

# Edit with your values
nano .env

# Protect file permissions (production)
chmod 600 .env
```

---

## Required Variables

These variables must be set for Clerk to function properly.

### OPENAI_API_KEY

Your OpenAI API key for running LLM reasoning workflows.

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
```

| Property | Value |
|----------|-------|
| **Required** | Yes |
| **Default** | None |
| **Format** | `sk-` followed by 48 characters |

**How to obtain:**
1. Visit [OpenAI Platform](https://platform.openai.com)
2. Sign in or create an account
3. Go to **API Keys** → **Create new secret key**
4. Copy the key immediately (shown only once)

**Security notes:**
- Never commit this key to version control
- Rotate keys regularly (recommended: every 90 days)
- Use separate keys for development and production
- Monitor usage on the OpenAI dashboard

---

### DATABASE_URL

PostgreSQL connection string for the backend database.

```env
# For Docker Compose deployment
DATABASE_URL=postgresql+asyncpg://clerk:clerk@db:5432/clerk

# For external PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/dbname
```

| Property | Value |
|----------|-------|
| **Required** | Yes |
| **Default** | None |
| **Format** | `postgresql+asyncpg://user:password@host:port/database` |

**Format breakdown:**
- `postgresql+asyncpg://` — Protocol (asyncpg driver required)
- `user:password` — Authentication credentials
- `@host:port` — Server address and port
- `/database` — Database name

**Docker Compose example:**
```env
DATABASE_URL=postgresql+asyncpg://clerk:clerk@db:5432/clerk
```

This connects to the `db` service defined in `docker-compose.yml`.

---

## Application Variables

### CLERK_SESSION_SECRET

Secret key for signing session cookies and CSRF tokens.

```env
CLERK_SESSION_SECRET=your-secret-key-here
```

| Property | Value |
|----------|-------|
| **Required** | Yes (auto-generated if missing) |
| **Default** | `clerk-session-secret-change-in-production` |
| **Format** | String, minimum 32 characters recommended |

**Generate a secure key:**
```bash
# Using OpenSSL
openssl rand -hex 32

# Using Python
python -c "import secrets; print(secrets.token_hex(32))"
```

**Security notes:**
- Must be kept secret in production
- Change from default immediately
- Use different keys for different environments
- Rotate if compromised

---

### LOG_LEVEL

Application logging verbosity level.

```env
LOG_LEVEL=info
```

| Property | Value |
|----------|-------|
| **Required** | No |
| **Default** | `info` |
| **Options** | `debug`, `info`, `warning`, `error`, `critical` |

**Level descriptions:**

| Level | Description | Use Case |
|-------|-------------|----------|
| `debug` | Detailed debug information | Development, troubleshooting |
| `info` | General operational events | Normal production operation |
| `warning` | Unexpected but handled issues | Minor issues, deprecated features |
| `error` | Errors that affect functionality | Errors requiring attention |
| `critical` | Serious errors, application failure | Immediate action required |

---

## Optional Integrations

### Supabase Configuration

Supabase provides managed PostgreSQL, authentication, and storage. Clerk can use Supabase instead of local PostgreSQL.

#### SUPABASE_URL

Your Supabase project URL.

```env
SUPABASE_URL=https://abcdefghijklmnop.supabase.co
```

| Property | Value |
|----------|-------|
| **Required** | No (for Supabase mode) |
| **Default** | None |
| **Format** | `https://project-ref.supabase.co` |

**How to find:**
1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Go to **Project Settings** → **API**
4. Copy **Project URL**

---

#### SUPABASE_ANON_KEY

Supabase anonymous/public key for client-side operations.

```env
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...
```

| Property | Value |
|----------|-------|
| **Required** | No (for Supabase mode) |
| **Default** | None |
| **Format** | JWT token string |

**How to find:**
1. Supabase Dashboard → **Project Settings** → **API**
2. Copy **anon public** key

---

#### SUPABASE_SERVICE_ROLE_KEY

Supabase service role key for admin operations.

```env
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIs...
```

| Property | Value |
|----------|-------|
| **Required** | No (recommended for Supabase mode) |
| **Default** | None |
| **Format** | JWT token string |

**⚠️ Security Warning:**
- This key has full admin access to your Supabase project
- Never expose in client-side code
- Never commit to version control
- Use only in server-side/backend code

**How to find:**
1. Supabase Dashboard → **Project Settings** → **API**
2. Copy **service_role secret** key

---

#### Supabase vs Local PostgreSQL

| Feature | Local PostgreSQL | Supabase |
|---------|------------------|----------|
| **Setup** | Docker Compose | Cloud service |
| **Maintenance** | Self-managed | Managed |
| **Backups** | Manual setup | Automatic |
| **Scaling** | Manual | Automatic |
| **Auth** | Clerk built-in | Supabase Auth |
| **Storage** | Local filesystem | Supabase Storage |
| **Best for** | Self-hosted, development | Cloud deployments |

---

## Docker Compose Variables

These variables configure the Docker Compose environment itself.

### POSTGRES_USER

PostgreSQL superuser username.

```env
POSTGRES_USER=clerk
```

| Property | Value |
|----------|-------|
| **Required** | No |
| **Default** | `clerk` |

---

### POSTGRES_PASSWORD

PostgreSQL superuser password.

```env
POSTGRES_PASSWORD=clerk
```

| Property | Value |
|----------|-------|
| **Required** | No |
| **Default** | `clerk` |

**Security note:** Change default in production:
```bash
# Generate secure password
openssl rand -base64 32
```

---

### POSTGRES_DB

Default database name created on startup.

```env
POSTGRES_DB=clerk
```

| Property | Value |
|----------|-------|
| **Required** | No |
| **Default** | `clerk` |

---

### FRONTEND_PORT

Host port for accessing the frontend application.

```env
FRONTEND_PORT=80
```

| Property | Value |
|----------|-------|
| **Required** | No |
| **Default** | `80` |
| **Range** | 1-65535 |

**Common values:**
- `80` — Standard HTTP port (requires root/admin on Linux/Mac)
- `8080` — Alternative HTTP port
- `3000` — Common development port

**Note:** If port is already in use, Docker will report an error. Change to an available port.

---

## Frontend Variables

### VITE_API_URL

Backend API URL for the frontend to communicate with.

```env
VITE_API_URL=http://localhost:8000
```

| Property | Value |
|----------|-------|
| **Required** | No |
| **Default** | `http://localhost:8000` |
| **Format** | Full URL with protocol |

**Development:**
```env
VITE_API_URL=http://localhost:8000
```

**Production (with HTTPS):**
```env
VITE_API_URL=https://api.yourdomain.com
```

---

## Additional Variables

### CLERK_EMAIL / CLERK_PASSWORD

Credentials for testing purposes.

```env
CLERK_EMAIL=admin@example.com
CLERK_PASSWORD=secure-password
```

| Property | Value |
|----------|-------|
| **Required** | No |
| **Default** | None |
| **Use** | Development/testing only |

---

## Security Considerations

### File Permissions

Protect your `.env` file from unauthorized access:

```bash
# Set restrictive permissions (owner read/write only)
chmod 600 .env

# Verify permissions
ls -la .env
# -rw------- 1 user user  1234 Mar 25 10:00 .env
```

### Version Control

**Never commit `.env` to git:**

```bash
# Ensure .env is ignored
echo ".env" >> .gitignore

# Verify it's not tracked
git status
```

The `.env.example` template (without secrets) should be committed instead.

### Secret Rotation

Rotate secrets regularly:

| Secret Type | Rotation Frequency | How to Rotate |
|-------------|-------------------|---------------|
| `OPENAI_API_KEY` | Every 90 days | Generate new key in OpenAI dashboard |
| `CLERK_SESSION_SECRET` | Every 180 days | Generate new secret, restart containers |
| `POSTGRES_PASSWORD` | Every 180 days | Change in `.env`, restart services |
| `SUPABASE_SERVICE_ROLE_KEY` | Every 90 days | Regenerate in Supabase dashboard |

### Production Checklist

- [ ] Changed default `CLERK_SESSION_SECRET`
- [ ] Changed default `POSTGRES_PASSWORD`
- [ ] Set `LOG_LEVEL` to `info` or `warning`
- [ ] Set `.env` file permissions to `600`
- [ ] Added `.env` to `.gitignore`
- [ ] Using HTTPS for `VITE_API_URL` in production
- [ ] Rotated all API keys from development values

---

## Quick Reference Table

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | — | OpenAI API access key |
| `DATABASE_URL` | Yes | — | PostgreSQL connection string |
| `CLERK_SESSION_SECRET` | Yes | `clerk-session-secret...` | Session signing key |
| `LOG_LEVEL` | No | `info` | Application logging level |
| `SUPABASE_URL` | No | — | Supabase project URL |
| `SUPABASE_ANON_KEY` | No | — | Supabase public key |
| `SUPABASE_SERVICE_ROLE_KEY` | No | — | Supabase admin key |
| `POSTGRES_USER` | No | `clerk` | Database username |
| `POSTGRES_PASSWORD` | No | `clerk` | Database password |
| `POSTGRES_DB` | No | `clerk` | Database name |
| `FRONTEND_PORT` | No | `80` | Host port for UI |
| `VITE_API_URL` | No | `http://localhost:8000` | Backend API URL |
| `CLERK_EMAIL` | No | — | Test credentials |
| `CLERK_PASSWORD` | No | — | Test credentials |

---

## Example Production .env

```env
# =============================================================================
# Production Environment Configuration
# =============================================================================

# Required: API Keys
OPENAI_API_KEY=sk-prod-xxxxxxxxxxxxxxxxxxxxxxxx

# Required: Database (use connection pooler in production)
DATABASE_URL=postgresql+asyncpg://clerk:secure-db-password@db:5432/clerk

# Required: Session Security (generate with: openssl rand -hex 32)
CLERK_SESSION_SECRET=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6

# Logging
LOG_LEVEL=info

# Frontend
FRONTEND_PORT=443
VITE_API_URL=https://api.clerk.example.com

# Database Credentials (change defaults!)
POSTGRES_USER=clerk_prod
POSTGRES_DB=clerk_prod
POSTGRES_PASSWORD=complex-password-generated-with-openssl

# Optional: Supabase (if using instead of local PostgreSQL)
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_ANON_KEY=eyJhbG...
# SUPABASE_SERVICE_ROLE_KEY=eyJhbG...
```

---

## Troubleshooting

### Variable Not Found

**Error:** `KeyError: 'OPENAI_API_KEY'` or similar

**Fix:**
1. Check `.env` file exists in project root
2. Verify variable name spelling
3. Ensure no spaces around `=` sign
4. Restart containers: `docker-compose restart`

### Connection Refused

**Error:** Database or API connection failures

**Fix:**
1. Verify `DATABASE_URL` format (must use `postgresql+asyncpg://`)
2. Check host matches service name in docker-compose (e.g., `db`)
3. Ensure database credentials match `POSTGRES_*` variables

### Port Already in Use

**Error:** `Bind for 0.0.0.0:80 failed: port is already allocated`

**Fix:**
```bash
# Change FRONTEND_PORT in .env
FRONTEND_PORT=8080

# Restart
docker-compose down
docker-compose up -d
```

---

## Related Documentation

- [Docker Compose Deployment](./docker.md)
- [Production Considerations](./production.md)
- [`.env.example` Template](../../.env.example)
