# CheckMyTex Web Interface - Deployment Guide

This guide covers deploying the CheckMyTex web interface to a production VPS with Nginx reverse proxy and security hardening.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [System Dependencies](#system-dependencies)
3. [Application Setup](#application-setup)
4. [Nginx Configuration](#nginx-configuration)
5. [SSL/HTTPS Setup](#sslhttps-setup)
6. [Systemd Service](#systemd-service)
7. [Security Hardening](#security-hardening)
8. [Monitoring](#monitoring)

## Prerequisites

- Ubuntu 20.04+ or Debian 11+ (recommended)
- Root or sudo access
- Domain name pointing to your server (optional but recommended)
- At least 2GB RAM, 2 CPU cores

## System Dependencies

### 1. Install Required Packages

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and build tools
sudo apt install -y python3.11 python3.11-venv python3-pip

# Install LaTeX and checking tools
sudo apt install -y \
    texlive-latex-base \
    texlive-latex-extra \
    chktex \
    aspell aspell-en \
    default-jre \
    wget unzip

# Install Nginx
sudo apt install -y nginx

# Install certbot for SSL (optional)
sudo apt install -y certbot python3-certbot-nginx
```

### 2. Install LanguageTool

```bash
cd /opt
sudo wget https://languagetool.org/download/LanguageTool-stable.zip
sudo unzip LanguageTool-stable.zip
sudo rm LanguageTool-stable.zip
sudo mv LanguageTool-* /opt/languagetool

# Test LanguageTool
java -jar /opt/languagetool/languagetool-server.jar --port 8081 &
# Stop it after testing
pkill -f languagetool
```

## Application Setup

### 1. Create Application User

```bash
# Create dedicated user for running the app
sudo useradd -r -s /bin/bash -d /opt/checkmytex checkmytex
sudo mkdir -p /opt/checkmytex
sudo chown checkmytex:checkmytex /opt/checkmytex
```

### 2. Install Application

```bash
# Switch to application user
sudo -u checkmytex -i

# Clone repository (or copy files)
cd /opt/checkmytex
git clone https://github.com/d-krupke/CheckMyTex.git
cd CheckMyTex

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -e .
pip install -r web_app/requirements.txt

# Test the application
cd web_app
python app.py  # Should start on port 5000
# Press Ctrl+C to stop

exit  # Exit from checkmytex user
```

### 3. Create Systemd Service

```bash
sudo nano /etc/systemd/system/checkmytex.service
```

Add the following content:

```ini
[Unit]
Description=CheckMyTex Web Interface
After=network.target

[Service]
Type=simple
User=checkmytex
Group=checkmytex
WorkingDirectory=/opt/checkmytex/CheckMyTex/web_app
Environment="PATH=/opt/checkmytex/CheckMyTex/venv/bin"
ExecStart=/opt/checkmytex/CheckMyTex/venv/bin/uvicorn app:app --host 127.0.0.1 --port 5000 --workers 2

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/tmp

# Resource limits
LimitNOFILE=4096
MemoryLimit=2G
CPUQuota=200%

# Restart policy
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable checkmytex
sudo systemctl start checkmytex
sudo systemctl status checkmytex
```

## Nginx Configuration

### 1. Install Nginx Configuration

```bash
# Copy the provided nginx.conf
sudo cp /opt/checkmytex/CheckMyTex/web_app/nginx.conf /etc/nginx/sites-available/checkmytex

# Edit with your domain name
sudo nano /etc/nginx/sites-available/checkmytex
# Replace 'checkmytex.example.com' with your domain

# Enable the site
sudo ln -s /etc/nginx/sites-available/checkmytex /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### 2. Firewall Configuration

```bash
# Enable UFW firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
sudo ufw status
```

## SSL/HTTPS Setup

### Using Let's Encrypt (Recommended)

```bash
# Obtain certificate
sudo certbot --nginx -d checkmytex.example.com

# Follow prompts to:
# 1. Enter email
# 2. Agree to terms
# 3. Choose whether to redirect HTTP to HTTPS (recommended: yes)

# Test automatic renewal
sudo certbot renew --dry-run
```

### Manual Certificate

If using a different SSL provider, uncomment the HTTPS section in `nginx.conf` and configure your certificate paths.

## Security Hardening

### 1. Additional Security Measures

```bash
# Limit file descriptors for checkmytex user
sudo nano /etc/security/limits.conf
```

Add:
```
checkmytex soft nofile 4096
checkmytex hard nofile 8192
```

### 2. Fail2Ban (Optional but Recommended)

```bash
sudo apt install -y fail2ban

# Create custom filter for rate limit violations
sudo nano /etc/fail2ban/filter.d/nginx-rate-limit.conf
```

Add:
```ini
[Definition]
failregex = limiting requests, excess:.* client: <HOST>
ignoreregex =
```

Configure jail:
```bash
sudo nano /etc/fail2ban/jail.local
```

Add:
```ini
[nginx-rate-limit]
enabled = true
filter = nginx-rate-limit
logpath = /var/log/nginx/checkmytex_error.log
maxretry = 5
findtime = 3600
bantime = 7200
```

Restart fail2ban:
```bash
sudo systemctl restart fail2ban
```

### 3. Automated Updates

```bash
# Enable unattended upgrades
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

## Monitoring

### 1. View Application Logs

```bash
# Service logs
sudo journalctl -u checkmytex -f

# Nginx access logs
sudo tail -f /var/log/nginx/checkmytex_access.log

# Nginx error logs
sudo tail -f /var/log/nginx/checkmytex_error.log
```

### 2. Check Service Status

```bash
# Application status
sudo systemctl status checkmytex

# Nginx status
sudo systemctl status nginx

# Check listening ports
sudo ss -tlnp | grep -E ':(80|443|5000)'
```

### 3. Resource Monitoring

```bash
# Install htop
sudo apt install -y htop
htop

# Or use traditional tools
top
df -h
free -h
```

## Rate Limiting Details

The Nginx configuration includes the following rate limits:

| Endpoint | Rate Limit | Burst | Description |
|----------|------------|-------|-------------|
| `/analyze` | 5/hour | 2 | Strict limit for analysis requests |
| `/` and `/licenses` | 30/minute | 10-20 | General browsing |

These can be adjusted in `/etc/nginx/sites-available/checkmytex`.

## Troubleshooting

### Application won't start

```bash
# Check logs
sudo journalctl -u checkmytex -n 50

# Check if port 5000 is in use
sudo ss -tlnp | grep 5000

# Test manually
sudo -u checkmytex -i
cd /opt/checkmytex/CheckMyTex/web_app
source ../venv/bin/activate
python app.py
```

### Nginx errors

```bash
# Check configuration syntax
sudo nginx -t

# View detailed error log
sudo tail -n 100 /var/log/nginx/error.log

# Restart Nginx
sudo systemctl restart nginx
```

### Permission issues

```bash
# Ensure correct ownership
sudo chown -R checkmytex:checkmytex /opt/checkmytex

# Check tmp directory permissions
ls -la /tmp/checkmytex_*
```

## Maintenance

### Updating the Application

```bash
sudo -u checkmytex -i
cd /opt/checkmytex/CheckMyTex
source venv/bin/activate
git pull
pip install -e .
exit

sudo systemctl restart checkmytex
```

### Cleaning Up Temp Files

Add to crontab:
```bash
sudo crontab -e
```

Add:
```
# Clean checkmytex temp files older than 1 day
0 2 * * * find /tmp/checkmytex_* -type d -mtime +1 -exec rm -rf {} + 2>/dev/null
```

## Performance Tuning

### For High Traffic

1. **Increase worker processes** in systemd service:
   ```ini
   ExecStart=.../uvicorn app:app --workers 4
   ```

2. **Adjust Nginx worker connections**:
   ```bash
   sudo nano /etc/nginx/nginx.conf
   ```
   Set `worker_connections 2048;`

3. **Enable Nginx caching** for static content

4. **Monitor and adjust resource limits** based on usage

## Backup

```bash
# Backup configuration
tar -czf checkmytex-config-$(date +%Y%m%d).tar.gz \
  /etc/nginx/sites-available/checkmytex \
  /etc/systemd/system/checkmytex.service \
  /opt/checkmytex/CheckMyTex/web_app/

# Backup to remote location
scp checkmytex-config-*.tar.gz user@backup-server:/backups/
```

## Support

For issues or questions:
- GitHub: https://github.com/d-krupke/CheckMyTex
- Issues: https://github.com/d-krupke/CheckMyTex/issues
