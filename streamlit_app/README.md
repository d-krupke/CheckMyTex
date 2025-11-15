# CheckMyTex Streamlit Interface

A student-friendly web interface for CheckMyTex built with Streamlit.

## Architecture

### Directory Structure

```
streamlit_app/
├── app.py                    # Main Streamlit app (thin orchestration)
├── components/
│   ├── __init__.py
│   ├── file_upload.py       # ZIP upload & extraction with security
│   ├── problem_viewer.py    # Display problems with action buttons
│   ├── todo_manager.py      # Manage todo list (add, comment, export)
│   └── progress.py          # Progress bar utilities
├── models/
│   ├── __init__.py
│   └── todo_item.py         # TodoItem dataclass
├── utils/
│   ├── __init__.py
│   ├── security.py          # ZIP validation, path sanitization
│   ├── analysis.py          # Run CheckMyTex analysis
│   └── export.py            # Export todo list to various formats
└── requirements.txt         # Streamlit-specific dependencies
```

## Features

- **Secure ZIP Upload**: Upload your LaTeX project as a ZIP file
- **Interactive Problem Viewer**: See problems with inline action buttons
- **Todo List Management**: Collect problems to fix with personal comments
- **Progress Tracking**: Real-time progress during analysis
- **Export Options**: Download todo list as JSON, Markdown, or CSV

## Installation

```bash
cd streamlit_app
pip install -r requirements.txt
```

## Usage

```bash
streamlit run app.py
```

## Security

- ZIP file validation (size limits, safe extensions)
- Path traversal protection
- Temporary file cleanup
- Safe file type whitelist
