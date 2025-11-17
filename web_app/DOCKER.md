# Docker Deployment

Quick Docker setup for CheckMyTex web interface with all checkers enabled.

## Quick Start

```bash
cd web_app
./setup.sh
```

Visit http://localhost

## What's Included

**All 10 checkers enabled:**
- AspellChecker (spell), Languagetool (grammar), ChkTex (LaTeX), Proselint (style)
- CheckSpell, SiUnitx, Cleveref, UniformNpHard, LineLengthChecker, TodoChecker

**Security features:**
- Rate limiting (10 analysis/min, adjust for production)
- Resource limits (2 CPU, 2GB RAM)
- Security headers, isolated network

## Manual Start

```bash
cd web_app
cp .env.example .env        # Optional: customize HTTP_PORT
docker compose up -d        # Start services
docker compose logs -f      # View logs
```

## Configuration

### Change Port

Edit `.env`:
```bash
HTTP_PORT=8080
```

### Adjust Rate Limits (for production)

Edit `nginx-docker.conf` line 7:
```nginx
# Development (current): 10r/m = 600/hour
limit_req_zone $binary_remote_addr zone=analyze:10m rate=10r/m;

# Production (strict): 1r/m = 60/hour
limit_req_zone $binary_remote_addr zone=analyze:10m rate=1r/m;
```

Then: `docker compose exec nginx nginx -s reload`

## VPS Deployment

### Option 1: Standalone (nginx included)
```bash
# Set port 80
echo "HTTP_PORT=80" > .env
docker compose up -d
# Add SSL: see DEPLOYMENT.md for Let's Encrypt setup
```

### Option 2: Behind Shared Nginx (recommended)
```bash
# In docker-compose.yml, comment out nginx service
# Change checkmytex service to expose port:
#   ports:
#     - "127.0.0.1:5000:5000"

docker compose up -d checkmytex

# Configure host nginx to proxy to localhost:5000
# See nginx.conf for example configuration
```

## Dependencies

### System packages (auto-installed in container):
- `aspell`, `aspell-en` - spell checking
- `chktex` - LaTeX linting
- `default-jre-headless` - Java for LanguageTool
- LanguageTool (~250 MB) - grammar checking

### Image size: ~586 MB

To reduce size, remove LanguageTool (~400 MB savings):
```dockerfile
# Comment out in Dockerfile:
# - default-jre-headless
# - LanguageTool download section
```

## Verification

Check all dependencies are working:
```bash
docker compose exec checkmytex which aspell
docker compose exec checkmytex which chktex
docker compose exec checkmytex languagetool --version
docker compose exec checkmytex java -version
```

## Management

```bash
# View logs
docker compose logs -f

# Restart
docker compose restart

# Update
git pull && docker compose up -d --build

# Stop
docker compose down

# Clean up
docker system prune -a
```

## Troubleshooting

**Port already in use:**
```bash
echo "HTTP_PORT=8080" > .env
docker compose up -d
```

**Container won't start:**
```bash
docker compose logs checkmytex
docker compose down
docker compose build --no-cache
docker compose up -d
```

**LanguageTool not found:**
```bash
docker compose exec checkmytex ls -l /usr/local/bin/languagetool
docker compose exec checkmytex java -jar /opt/languagetool/languagetool-commandline.jar --version
```

## Files

- `docker-compose.yml` - Service definitions
- `nginx-docker.conf` - Nginx config
- `Dockerfile` - App container
- `.env.example` - Config template
- `setup.sh` - Automated setup script

For traditional VPS deployment (non-Docker), see [DEPLOYMENT.md](DEPLOYMENT.md)
For security details, see [SECURITY.md](SECURITY.md)
