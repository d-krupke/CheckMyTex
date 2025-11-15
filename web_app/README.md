# CheckMyTex Web Interface

A simple Flask web interface for CheckMyTex that displays the beautiful Rich HTML output.

## Features

- 📤 Drag-and-drop ZIP file upload
- 🎨 Beautiful, responsive UI
- 📝 Displays CheckMyTex analysis using the native Rich HTML output
- 🐳 Docker-ready for easy deployment

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

Visit http://localhost:5000

## Docker Deployment

```bash
# Build the image
cd /path/to/CheckMyTex
docker build -t checkmytex-web -f web_app/Dockerfile .

# Run the container
docker run -p 5000:5000 checkmytex-web
```

Visit http://localhost:5000

## How It Works

1. User uploads a ZIP file containing their LaTeX project
2. Server extracts the ZIP and finds the main .tex file
3. CheckMyTex analyzes the document
4. RichPrinter generates beautiful HTML output
5. HTML is served directly to the user's browser

No styling conflicts, no iframe issues - just the beautiful CLI output in the browser!
