# CheckMyTex Web Interface

A modern, user-friendly web interface for CheckMyTex built with FastAPI.

## Features

### 🎨 Clean, Modern Design
- Responsive interface with drag-and-drop file upload
- Terminal-styled HTML output for analysis results
- Syntax highlighting for LaTeX code
- Inline character-level error highlighting

### ⚙️ Configurable Analysis
- **Checkers**: Enable/disable individual checking tools
  - Aspell (Spelling)
  - LanguageTool (Grammar)
  - ChkTeX (LaTeX Syntax)
  - SiUnitx (Units)
  - Cleveref (References)
  - Proselint (Style)
  - Uniform NP-Hard
  - **Line Length** - Detects lines >100 characters ⭐ NEW
  - **TODO/FIXME** - Finds draft markers and unfinished work ⭐ NEW

- **Filters**: Configure false positive reduction
  - Ignore includegraphics paths
  - Ignore references
  - Ignore repeated words
  - Math/Commands filtering
  - Math mode filtering
  - Author name detection
  - Bibliography word filtering
  - **Code Listings** - Ignores errors in code environments ⭐ NEW

### 📜 Open Source Attribution
- Dedicated licenses page
- Links to all upstream projects
- Compliance information for GPL/LGPL dependencies

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py

# Or with uvicorn
uvicorn app:app --reload --host 0.0.0.0 --port 5000
```

Visit http://localhost:5000

### Docker Deployment

```bash
# Build the image
docker build -t checkmytex-web -f Dockerfile .

# Run the container
docker run -p 5000:5000 checkmytex-web
```

## Production Deployment

For production deployment with Nginx reverse proxy, rate limiting, SSL, and security hardening:

**📖 See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment guide**

Key features covered:
- Nginx reverse proxy with rate limiting (5 requests/hour for analysis)
- SSL/HTTPS setup with Let's Encrypt
- Systemd service configuration
- Security hardening (firewall, fail2ban, resource limits)
- Monitoring and maintenance

## API Endpoints

- `GET /` - Main upload interface
- `GET /licenses` - Open source licenses page
- `POST /analyze` - Analyze uploaded ZIP file
  - Parameters:
    - `file`: ZIP file containing LaTeX project
    - `checkers`: JSON array of enabled checkers
    - `filters`: JSON array of enabled filters
  - Returns: Terminal-styled HTML report

## How It Works

1. User uploads a ZIP file containing their LaTeX project
2. Server extracts ZIP and validates content
3. Finds main .tex file (looks for \documentclass)
4. Creates analyzer with selected checkers and filters
5. Analyzes document with CheckMyTex
6. Generates terminal-styled HTML with inline highlighting
7. Returns HTML report to user's browser

## Security Features

The web interface includes:
- File size validation (10MB limit)
- ZIP structure validation
- Temporary file cleanup
- Safe file extraction
- Rate limiting via Nginx (production)
- Security headers
- Input sanitization

## Development

```bash
# Install CheckMyTex in development mode
cd ..
pip install -e ".[dev]"

# Install web app dependencies
cd web_app
pip install -r requirements.txt

# Run with auto-reload
uvicorn app:app --reload --host 0.0.0.0 --port 5000
```

### Project Structure

```
web_app/
├── app.py                    # FastAPI application
├── templates/
│   ├── index.html           # Main upload interface
│   └── licenses.html        # Licenses page
├── nginx.conf               # Nginx configuration
├── DEPLOYMENT.md            # Production deployment guide
├── Dockerfile               # Docker configuration
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Configuration Files

- **nginx.conf**: Production Nginx configuration with rate limiting
  - `/analyze`: 5 requests/hour per IP
  - General pages: 30 requests/minute per IP

- **Dockerfile**: Container configuration with all dependencies

- **requirements.txt**: Python dependencies
  - FastAPI and Uvicorn for web server
  - Jinja2 for templates
  - CheckMyTex core dependencies

## API Documentation

FastAPI provides automatic interactive documentation:
- Swagger UI: http://localhost:5000/docs
- ReDoc: http://localhost:5000/redoc

## License

This web interface is part of CheckMyTex and is licensed under the MIT License.

See the `/licenses` page for information about third-party dependencies.
