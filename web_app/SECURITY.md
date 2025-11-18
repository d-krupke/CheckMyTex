# Security Implementation Guide

This document explains the security features implemented in the CheckMyTex web interface and provides guidance on additional protections.

## Recent Security Enhancements (2025-11)

### Enhanced Path Traversal Protection ✅ (Critical)
**Location**: `zip_handler.py:22-75`

**Improvements**:
- **Unicode normalization (NFKC)**: Prevents Unicode homograph attacks
- **Comprehensive path validation**: Rejects absolute paths, `..`, backslashes
- **Symlink detection**: Blocks symbolic links in ZIP archives
- **Directory filtering**: Skips directory entries
- **PurePosixPath validation**: Safe cross-platform path parsing

**What it protects against**:
- `../../etc/passwd` - Parent directory traversal
- `/etc/passwd` - Absolute path access
- `C:\Windows\System32` - Windows absolute paths
- `\\server\share` - UNC paths
- `%2e%2e/file` - URL-encoded traversal
- Unicode tricks (e.g., fullwidth dots)
- Symlinks pointing outside extraction directory

### Request Correlation IDs ✅ (Important)
**Location**: `app.py:77`

**Implementation**:
```python
request_id = str(uuid.uuid4())[:8]  # e.g., "a3f2b1c9"
logger.info("[%s] Analysis request from %s...", request_id, client_ip)
```

**Benefits**:
- Track individual requests across log entries
- Correlate errors with specific uploads
- Identify abuse patterns from specific IPs
- Debug issues with unique identifiers

**Example logs**:
```
[a3f2b1c9] Analysis request from 192.168.1.100 using zip input
[a3f2b1c9] Validating ZIP file: 156.3KB
[a3f2b1c9] Found main .tex file: thesis/main.tex
[a3f2b1c9] Analysis completed for 192.168.1.100 in 26.3s
```

### Proper Logging Practices ✅
**All logging now uses lazy evaluation** instead of f-strings:
```python
# ❌ BAD (eager evaluation)
logger.info(f"Request from {ip} for {file}")

# ✅ GOOD (lazy evaluation - only formats if logged)
logger.info("Request from %s for %s", ip, file)
```

**Why it matters**:
- More efficient (no string formatting if log level disabled)
- Better performance under load
- Prevents side effects in format strings

## Implemented Security Features

### 1. File Size Limits ✅ (Critical)

**What it does**: Prevents users from uploading files that are too large, protecting against resource exhaustion attacks.

**Implementation**:
```python
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_UNCOMPRESSED_SIZE = 50 * 1024 * 1024  # 50MB

# Check file size before processing
if len(content) > MAX_FILE_SIZE:
    raise HTTPException(status_code=413, detail="File too large")
```

**Why it's critical**:
- Prevents disk exhaustion
- Limits memory usage
- Prevents DoS attacks via large file uploads
- Fast rejection before expensive processing

**Adjusting limits**:
Edit constants in `app.py`:
- `MAX_FILE_SIZE`: Maximum compressed ZIP size (default: 10MB)
- `MAX_UNCOMPRESSED_SIZE`: Maximum uncompressed content (default: 50MB)

### 2. Request Timeouts ✅ (Important)

**What it does**: Prevents long-running requests from consuming resources indefinitely.

**Implementation**:
```python
ANALYSIS_TIMEOUT = 120  # 2 minutes

# ZIP extraction timeout (30 seconds)
async with asyncio.timeout(30):
    await asyncio.to_thread(extract_zip)

# Analysis timeout (2 minutes)
async with asyncio.timeout(ANALYSIS_TIMEOUT):
    analyzed_document = await asyncio.to_thread(run_analysis)
```

**Why it's important**:
- Prevents hanging processes
- Limits resource consumption per request
- Protects against algorithmic complexity attacks
- Ensures fair resource distribution among users

**Timeout stages**:
1. **ZIP extraction**: 30 seconds (maliciously crafted ZIPs)
2. **Analysis**: 120 seconds (complex documents)

**Monitoring timeouts**:
```bash
# Check logs for timeout events
grep "timeout" /var/log/checkmytex/app.log
```

### 3. Better Temp File Cleanup ✅ (Important)

**What it does**: Ensures temporary files are always deleted, even if errors occur.

**Implementation**:
```python
@contextmanager
def temp_workspace():
    """Create a temporary workspace that is always cleaned up."""
    temp_dir = Path(tempfile.mkdtemp(prefix='checkmytex_'))
    try:
        yield temp_dir
    finally:
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            logger.error(f"Failed to cleanup: {e}")

# Usage
with temp_workspace() as temp_dir:
    # Work with files
    # Cleanup happens automatically even if exceptions occur
```

**Why it's important**:
- Prevents disk exhaustion over time
- Ensures cleanup even on errors/timeouts
- No leaked temporary directories
- Automatic resource management

**Monitoring disk usage**:
```bash
# Check temporary directories
ls -lh /tmp/checkmytex_*

# Disk usage
df -h /tmp

# Add cron job for cleanup (belt and suspenders)
0 2 * * * find /tmp/checkmytex_* -type d -mtime +1 -exec rm -rf {} + 2>/dev/null
```

### 4. Zip Bomb Protection ✅ (Critical)

**What it does**: Detects and rejects maliciously crafted ZIP files designed to exhaust resources.

**Implementation**:
```python
MAX_COMPRESSION_RATIO = 100  # Reject if >100x compression

def validate_zip_file(zip_path: Path) -> None:
    compressed_size = zip_path.stat().st_size
    uncompressed_size = sum(info.file_size for info in zf.infolist())

    ratio = uncompressed_size / compressed_size
    if ratio > MAX_COMPRESSION_RATIO:
        raise HTTPException(400, "Suspicious ZIP detected")

    if uncompressed_size > MAX_UNCOMPRESSED_SIZE:
        raise HTTPException(413, "Uncompressed content too large")
```

**Why it's critical**:
- Classic zip bomb: 42KB → 4.5GB (>100,000x)
- Can exhaust all disk space
- Can trigger OOM killer
- Can crash the system

**Example attack**:
A 42KB ZIP file containing nested ZIPs that expand to 4.5GB is rejected:
```
Ratio: 4,500,000 KB / 42 KB = 107,142x > 100x threshold ❌ REJECTED
```

**Legitimate large documents**:
```
Ratio: 5,000 KB / 100 KB = 50x < 100x threshold ✅ ALLOWED
```

### 5. Monitoring and Logging ✅ (Important)

**What it does**: Tracks all requests, errors, and security events for analysis and debugging.

**Implementation**:
```python
# Structured logging with levels
logger.info(f"Analysis request from {client_ip} for file: {file.filename}")
logger.warning(f"File too large from {client_ip}: {size}MB")
logger.error(f"Analysis failed: {error}", exc_info=True)

# Metrics logged:
# - Request start/completion times
# - Client IP addresses
# - File sizes and compression ratios
# - Analysis duration
# - Error types and stack traces
# - Configuration used
```

**Why it's important**:
- Detect attack patterns
- Debug issues
- Monitor performance
- Audit usage
- Capacity planning

**Log examples**:
```
2025-11-16 10:23:45 - INFO - Analysis request from 192.168.1.100 for file: thesis.zip
2025-11-16 10:23:46 - INFO - ZIP validation passed: 156.3KB compressed, 1.2MB uncompressed (ratio: 7.9x)
2025-11-16 10:23:46 - INFO - Found main .tex file: main.tex
2025-11-16 10:24:12 - INFO - Analysis completed for 192.168.1.100 in 26.3s (47 problems found)
```

**Suspicious activity**:
```
2025-11-16 10:25:01 - WARNING - File too large from 203.0.113.42: 15.2MB (max 10MB)
2025-11-16 10:25:03 - WARNING - Suspicious ZIP detected: ratio 156.2x (threshold: 100x)
2025-11-16 10:25:05 - ERROR - Analysis timeout from 203.0.113.42 after 120s
```

**Accessing logs**:
```bash
# Application logs (stdout/stderr)
sudo journalctl -u checkmytex -f

# Or if logging to file
tail -f /var/log/checkmytex/app.log

# Search for specific events
grep "WARNING\|ERROR" /var/log/checkmytex/app.log

# Monitor specific IP
grep "203.0.113.42" /var/log/checkmytex/app.log
```

## Recommended Additional Protections

### 6. Nginx Rate Limiting (Production Required)

**What it does**: Limits request rate per IP at the reverse proxy level.

**Why use Nginx instead of application-level**:
1. ✅ **More efficient**: Rejects requests before reaching application
2. ✅ **Lower resource usage**: No Python process spawned
3. ✅ **Battle-tested**: Nginx rate limiting is extremely robust
4. ✅ **DDoS protection**: Handles thousands of requests efficiently
5. ✅ **Flexible**: Different limits for different endpoints

**Implementation**: Already provided in `nginx.conf`:
```nginx
# Define rate limit zones
limit_req_zone $binary_remote_addr zone=analyze:10m rate=5r/h;
limit_req_zone $binary_remote_addr zone=general:10m rate=30r/m;

# Apply to endpoints
location /analyze {
    limit_req zone=analyze burst=2 nodelay;
    # ... proxy settings
}
```

**Rate limits**:
- `/analyze`: 5 requests/hour per IP (burst: 2)
- General pages: 30 requests/minute per IP (burst: 10-20)

**How it works**:
1. Nginx tracks requests per IP in shared memory (10MB zone)
2. Requests exceeding limit get HTTP 429 (Too Many Requests)
3. Optional `burst` allows temporary spikes
4. `nodelay` rejects immediately vs queueing

**Testing**:
```bash
# Burst will allow 2 extra requests, then reject
for i in {1..10}; do curl -X POST http://your-server/analyze; done

# Should see HTTP 429 after 7 requests (5 + 2 burst)
```

**Monitoring**:
```bash
# Check Nginx logs for rate limiting
grep "limiting requests" /var/log/nginx/error.log

# See rejected requests
tail -f /var/log/nginx/checkmytex_error.log | grep "limiting"
```

**Adjusting limits**:
Edit `/etc/nginx/sites-available/checkmytex`:
```nginx
# More permissive: 10 requests/hour
limit_req_zone $binary_remote_addr zone=analyze:10m rate=10r/h;

# More restrictive: 3 requests/hour
limit_req_zone $binary_remote_addr zone=analyze:10m rate=3r/h;
```

Then reload:
```bash
sudo nginx -t  # Test configuration
sudo systemctl reload nginx
```

### 7. Docker Resource Limits (Recommended)

**What it does**: Limits CPU and memory usage at the container level.

**Why use Docker**:
1. ✅ **Isolation**: Process isolation from host
2. ✅ **Resource limits**: Hard CPU/memory caps
3. ✅ **Easy deployment**: Consistent environment
4. ✅ **Rollback**: Easy version management
5. ✅ **Security**: Additional kernel-level isolation

**Implementation with docker-compose**:

```yaml
version: '3.8'

services:
  checkmytex:
    build: .
    ports:
      - "127.0.0.1:5000:5000"  # Only expose to localhost

    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '2.0'      # Max 2 CPU cores
          memory: 2G       # Max 2GB RAM
        reservations:
          cpus: '0.5'      # Guaranteed 0.5 cores
          memory: 512M     # Guaranteed 512MB

    # Security options
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETUID
      - SETGID

    # Restart policy
    restart: unless-stopped

    # Health check
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

    # Logging
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

**Why resource limits matter**:
- **Without limits**: One analysis can use 100% of all CPUs and RAM
- **With limits**: Maximum 2 cores and 2GB, protecting other services
- **OOM protection**: Container killed instead of crashing host

**Testing resource limits**:
```bash
# Monitor resource usage
docker stats checkmytex

# Should show max 2.0 CPUs and 2GB memory
```

**Kubernetes alternative**:
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "2000m"
```

### 8. Authentication (Optional but Recommended)

**When to use**:
- Private instances
- Limited user base
- Sensitive documents
- Cost control

**Simple implementation options**:

**A) Basic HTTP Auth (Nginx)**:
```nginx
# In nginx.conf
location / {
    auth_basic "CheckMyTex";
    auth_basic_user_file /etc/nginx/.htpasswd;
    # ... proxy settings
}
```

Create password file:
```bash
sudo apt install apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd admin
```

**B) API Key (Application)**:
```python
from fastapi import Header, HTTPException

API_KEY = os.getenv("CHECKMYTEX_API_KEY", "changeme")

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(401, "Invalid API key")

@app.post("/analyze", dependencies=[Depends(verify_api_key)])
async def analyze(...):
    # Requires: curl -H "X-API-Key: secret" ...
```

**C) OAuth2 (Advanced)**:
- Integrate with Google, GitHub, etc.
- Use libraries like `authlib` or `fastapi-users`

## Security Best Practices Checklist

### Application Level ✅
- [x] File size limits
- [x] Timeout protection
- [x] Automatic cleanup
- [x] Zip bomb detection
- [x] Comprehensive logging
- [x] Error handling without info leakage

### Infrastructure Level (Nginx) ✅
- [x] Rate limiting configuration
- [x] Security headers
- [x] File upload size limits
- [x] Timeouts configured
- [x] SSL/HTTPS ready
- [x] Connection limits

### System Level (Recommended)
- [ ] Deploy with Docker + resource limits
- [ ] Use dedicated user (not root)
- [ ] Enable firewall (UFW)
- [ ] Set up fail2ban
- [ ] Regular updates (unattended-upgrades)
- [ ] Monitor disk usage
- [ ] Set up log rotation

### Monitoring
- [ ] Check logs regularly
- [ ] Monitor resource usage
- [ ] Track error rates
- [ ] Alert on suspicious patterns
- [ ] Backup configurations

## Testing Security Features

### Test File Size Limits
```bash
# Create 15MB file (should fail)
dd if=/dev/zero of=large.zip bs=1M count=15
curl -F "file=@large.zip" http://localhost:5000/analyze
# Expected: HTTP 413 Payload Too Large
```

### Test Zip Bomb Protection
```bash
# Create a 42KB zip bomb (CAREFUL!)
# Don't run this test without protection enabled!
python3 -c "
import zipfile
with zipfile.ZipFile('bomb.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('bomb.txt', 'A' * (10**6))
"
curl -F "file=@bomb.zip" http://localhost:5000/analyze
# Expected: HTTP 400 Suspicious ZIP detected
```

### Test Timeout
```bash
# Upload extremely complex document
# Should timeout after 120 seconds
# Expected: HTTP 504 Gateway Timeout
```

### Test Rate Limiting (with Nginx)
```bash
# Send 10 requests rapidly
for i in {1..10}; do
    curl -X POST http://localhost/analyze \
         -F "file=@test.zip" &
done
# Expected: Some requests get HTTP 429
```

## Incident Response

### Disk Full
```bash
# Check disk usage
df -h

# Find large temp directories
du -sh /tmp/checkmytex_*

# Clean old temp files
find /tmp/checkmytex_* -type d -mtime +1 -delete

# Check running processes
ps aux | grep checkmytex
```

### High CPU Usage
```bash
# Check process CPU
top -p $(pgrep -f checkmytex)

# Check for stuck processes
ps aux | grep checkmytex | grep -v grep

# Restart service
sudo systemctl restart checkmytex
```

### Suspicious Activity
```bash
# Check logs for attack patterns
grep -E "429|413|timeout|suspicious" /var/log/nginx/checkmytex_access.log

# Find most active IPs
awk '{print $1}' /var/log/nginx/checkmytex_access.log | sort | uniq -c | sort -rn | head

# Block IP (temporary)
sudo ufw deny from 203.0.113.42

# Or use fail2ban (automatic)
```

## Further Reading

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Nginx Rate Limiting](https://www.nginx.com/blog/rate-limiting-nginx/)
- [Docker Security](https://docs.docker.com/engine/security/)
