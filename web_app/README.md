# CheckMyTex Web Interface

Modern web interface for CheckMyTex with drag-and-drop upload, configurable checkers, and terminal-styled output.

## Quick Start

**Docker (recommended):**
```bash
cd web_app
./setup.sh
```
Visit http://localhost → See [DOCKER.md](DOCKER.md)

**Local development (Python 3.11+):**
```bash
pip install -e .. -r requirements.txt
python app.py
```
Visit http://localhost:5000

**Production VPS:** See [DEPLOYMENT.md](DEPLOYMENT.md)

## Features

- **10 Checkers**: Aspell, LanguageTool, ChkTeX, Proselint, SiUnitx, Cleveref, NP-Hard, LineLengthChecker, TodoChecker, CheckSpell
- **Flexible Input**: Upload a ZIP project or paste a single LaTeX file directly
- **8 Filters**: Configurable false positive reduction
- **Security**: Rate limiting, file validation, resource limits
- **Output**: Terminal-styled HTML with syntax highlighting

## API

- `GET /` - Upload interface
- `GET /licenses` - License info
- `POST /analyze` - Analyze ZIP (returns HTML report)
  - Interactive docs: http://localhost:5000/docs

## Files

- `app.py` - FastAPI application
- `docker-compose.yml`, `Dockerfile` - Docker setup
- `nginx-docker.conf` - Nginx config for Docker
- `nginx.conf` - Nginx config for traditional deployment
- `setup.sh` - Automated Docker setup
- `DOCKER.md` - Docker deployment guide
- `DEPLOYMENT.md` - Traditional VPS deployment guide
- `SECURITY.md` - Security considerations

## License

MIT License - See `/licenses` endpoint for third-party dependencies
