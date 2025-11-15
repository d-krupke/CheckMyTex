"""Simple FastAPI web interface for CheckMyTex."""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from checkmytex import DocumentAnalyzer
from checkmytex.cli.rich_printer import RichPrinter
from checkmytex.filtering import (
    IgnoreIncludegraphics,
    IgnoreLikelyAuthorNames,
    IgnoreRefs,
    IgnoreRepeatedWords,
    IgnoreWordsFromBibliography,
    MathMode,
)
from checkmytex.finding import (
    AspellChecker,
    CheckSpell,
    ChkTex,
    Cleveref,
    Languagetool,
    Proselint,
    SiUnitx,
    UniformNpHard,
)
from checkmytex.latex_document.parser import LatexParser

app = FastAPI(title="CheckMyTex Web Interface")


@app.get("/", response_class=HTMLResponse)
async def index():
    """Show upload form."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CheckMyTex - LaTeX Document Checker</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .container {
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            padding: 40px;
            max-width: 600px;
            width: 100%;
        }

        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 32px;
        }

        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 16px;
        }

        .upload-area {
            border: 2px dashed #667eea;
            border-radius: 8px;
            padding: 40px;
            text-align: center;
            margin-bottom: 20px;
            transition: all 0.3s ease;
            cursor: pointer;
        }

        .upload-area:hover {
            border-color: #764ba2;
            background-color: #f8f9fa;
        }

        .upload-area.dragover {
            background-color: #e9ecef;
            border-color: #764ba2;
        }

        .upload-icon {
            font-size: 48px;
            margin-bottom: 10px;
        }

        .upload-text {
            color: #666;
            margin-bottom: 10px;
        }

        input[type="file"] {
            display: none;
        }

        .file-name {
            margin-top: 10px;
            color: #667eea;
            font-weight: 500;
        }

        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 14px 32px;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        button:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }

        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        .info {
            background-color: #e7f3ff;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-top: 20px;
            border-radius: 4px;
        }

        .info h3 {
            color: #333;
            margin-bottom: 10px;
            font-size: 14px;
        }

        .info ul {
            margin-left: 20px;
            color: #666;
            font-size: 14px;
        }

        .info li {
            margin-bottom: 5px;
        }

        .loading {
            display: none;
            text-align: center;
            margin-top: 20px;
        }

        .loading.active {
            display: block;
        }

        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .error {
            background-color: #fee;
            border-left: 4px solid #e74c3c;
            padding: 15px;
            margin-top: 20px;
            border-radius: 4px;
            color: #c0392b;
            display: none;
        }

        .error.active {
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📝 CheckMyTex</h1>
        <p class="subtitle">Upload your LaTeX project for analysis</p>

        <form id="uploadForm">
            <div class="upload-area" id="uploadArea">
                <div class="upload-icon">📦</div>
                <div class="upload-text">
                    <strong>Click to upload</strong> or drag and drop
                </div>
                <div style="color: #999; font-size: 14px;">ZIP file (max 100MB)</div>
                <input type="file" name="file" id="fileInput" accept=".zip">
                <div class="file-name" id="fileName"></div>
            </div>

            <button type="submit" id="submitBtn" disabled>
                Analyze Document
            </button>
        </form>

        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p style="margin-top: 10px; color: #666;">Analyzing your document...</p>
        </div>

        <div class="error" id="error"></div>

        <div class="info">
            <h3>ℹ️ What gets checked:</h3>
            <ul>
                <li>Spelling and grammar</li>
                <li>LaTeX syntax (ChkTeX)</li>
                <li>Style and formatting</li>
                <li>Proper use of siunitx, cleveref, etc.</li>
            </ul>
        </div>
    </div>

    <script>
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const fileName = document.getElementById('fileName');
        const submitBtn = document.getElementById('submitBtn');
        const uploadForm = document.getElementById('uploadForm');
        const loading = document.getElementById('loading');
        const errorDiv = document.getElementById('error');

        // Click to upload
        uploadArea.addEventListener('click', () => fileInput.click());

        // File selection
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                fileName.textContent = `Selected: ${file.name}`;
                submitBtn.disabled = false;
            }
        });

        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');

            const file = e.dataTransfer.files[0];
            if (file && file.name.endsWith('.zip')) {
                fileInput.files = e.dataTransfer.files;
                fileName.textContent = `Selected: ${file.name}`;
                submitBtn.disabled = false;
            }
        });

        // Form submission
        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const file = fileInput.files[0];
            if (!file) return;

            loading.classList.add('active');
            errorDiv.classList.remove('active');
            submitBtn.disabled = true;

            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    const error = await response.text();
                    throw new Error(error);
                }

                // Open result in new window
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                window.open(url, '_blank');

            } catch (error) {
                errorDiv.textContent = `Error: ${error.message}`;
                errorDiv.classList.add('active');
            } finally {
                loading.classList.remove('active');
                submitBtn.disabled = false;
            }
        });
    </script>
</body>
</html>
    """


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    """Analyze uploaded ZIP file and return HTML report."""

    # Validate file
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Please upload a ZIP file")

    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp(prefix='checkmytex_'))

    try:
        # Save and extract ZIP
        zip_path = temp_dir / 'upload.zip'
        content = await file.read()
        zip_path.write_bytes(content)

        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(temp_dir / 'extracted')

        extract_dir = temp_dir / 'extracted'

        # Find main .tex file
        main_tex = find_main_tex(extract_dir)
        if not main_tex:
            raise HTTPException(status_code=400, detail="No .tex file found in ZIP")

        # Create analyzer
        analyzer = create_analyzer()

        # Parse and analyze
        parser = LatexParser()
        latex_document = parser.parse(str(main_tex))
        analyzed_document = analyzer.analyze(latex_document)

        # Generate HTML using RichPrinter
        printer = RichPrinter(analyzed_document, shorten=5)
        html_path = temp_dir / 'report.html'
        printer.to_html(str(html_path))

        # Return the HTML file
        return FileResponse(
            html_path,
            media_type='text/html',
            filename=f'checkmytex_report.html'
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing document: {str(e)}")


def create_analyzer() -> DocumentAnalyzer:
    """Create a DocumentAnalyzer with default configuration."""
    analyzer = DocumentAnalyzer()

    # Add checkers
    try:
        analyzer.add_checker(AspellChecker())
    except Exception:
        analyzer.add_checker(CheckSpell())

    try:
        analyzer.add_checker(Languagetool())
    except Exception:
        pass

    analyzer.add_checker(ChkTex())
    analyzer.add_checker(SiUnitx())
    analyzer.add_checker(UniformNpHard())
    analyzer.add_checker(Cleveref())

    try:
        analyzer.add_checker(Proselint())
    except Exception:
        pass

    # Add filters
    analyzer.add_filter(IgnoreIncludegraphics())
    analyzer.add_filter(IgnoreRefs())
    analyzer.add_filter(IgnoreRepeatedWords())
    analyzer.add_filter(MathMode())
    analyzer.add_filter(IgnoreLikelyAuthorNames())
    analyzer.add_filter(IgnoreWordsFromBibliography())

    return analyzer


def find_main_tex(directory: Path) -> Path | None:
    """Find the main .tex file in a directory."""
    # Common main file names
    common_names = ["main.tex", "document.tex", "thesis.tex", "paper.tex", "report.tex"]

    for name in common_names:
        candidate = directory / name
        if candidate.exists():
            return candidate

    # Search recursively for files with \documentclass
    for tex_file in directory.rglob("*.tex"):
        try:
            content = tex_file.read_text(encoding="utf-8", errors="ignore")
            if "\\documentclass" in content:
                return tex_file
        except Exception:
            continue

    # Return first .tex file found
    tex_files = list(directory.rglob("*.tex"))
    return tex_files[0] if tex_files else None


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5000)
