# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CheckMyTex is a CLI tool for checking complex LaTeX documents (dissertations, papers) for spelling, grammar, and LaTeX-specific errors. It combines multiple checking tools (aspell/pyspellchecker, LanguageTool, ChkTeX, Proselint) with a unified interface and sophisticated whitelisting system.

**Key Design Philosophy:**
- Work on whole documents, not individual files
- Provide exact problem locations with file paths and line numbers
- Support interactive CLI workflow with vim/nano integration
- Allow whitelisting of false positives (`.whitelist.txt`)
- Support both CLI and web interfaces

## Development Commands

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=checkmytex --cov-report=term-missing

# Run specific test file
pytest tests/test_line_length_checker.py

# Run tests across Python versions
tox
```

### Linting and Formatting
```bash
# Lint with ruff
ruff check .

# Format with ruff
ruff format .

# Type check with mypy
mypy checkmytex tests

# Run pre-commit hooks manually
pre-commit run --all-files
```

### Running the Tool
```bash
# Install in development mode
pip install -e ".[dev]"

# Run on a LaTeX document
checkmytex main.tex

# With custom whitelist
checkmytex -w custom_whitelist.txt main.tex

# Export as HTML
checkmytex --html output.html main.tex

# Export as JSON
checkmytex --json output.json main.tex
```

### Web Interface
```bash
# Run web app locally
cd web_app
python app.py
# OR
uvicorn app:app --reload --host 0.0.0.0 --port 5000
```

## Architecture

### Core Components

1. **LatexDocument** (`checkmytex/latex_document/`)
   - Central abstraction that provides both source and detexed text
   - Uses `flachtex` to flatten multi-file LaTeX projects into single source string
   - Uses `yalafi` to convert LaTeX to plain text (detex)
   - **Critical feature:** Bidirectional origin tracking - can trace any fragment in source or text back to original file/line
   - `Origin` and `OriginPointer` classes track position mappings between text, source, and original files

2. **DocumentAnalyzer** (`checkmytex/document_analyzer.py`)
   - Orchestrates checking workflow
   - Manages collection of `Checker` instances
   - Applies `Filter` pipeline to reduce false positives
   - Returns `AnalyzedDocument` with sorted problems

3. **Checkers** (`checkmytex/finding/`)
   - Abstract base: `Checker` class with `check()` method
   - Each checker returns `Problem` objects with origin information
   - Built-in checkers:
     - `AspellChecker` / `CheckSpell`: Spelling (detexed text)
     - `Languagetool`: Grammar checking (detexed text)
     - `ChkTex`: LaTeX syntax checking (source)
     - `Proselint`: Writing style advice (detexed text)
     - `SiUnitx`: Detects raw numbers without siunitx package
     - `Cleveref`: Checks proper cleveref usage
     - `UniformNpHard`: NP-hard/complete consistency
     - `LineLengthChecker`: Lines >100 characters (source-based)
     - `TodoChecker`: Finds TODO/FIXME markers (source-based)

4. **Filters** (`checkmytex/filtering/`)
   - Pipeline to remove false positives
   - Each filter has `prepare(document)` and `filter(problems)` methods
   - Built-in filters:
     - `Whitelist`: User-maintained problem whitelist
     - `IgnoreIncludegraphics`: Ignores spelling in image paths
     - `IgnoreRefs`: Ignores spelling in labels/refs
     - `IgnoreLikelyAuthorNames`: Detects author names before citations
     - `IgnoreWordsFromBibliography`: Uses bibliography to whitelist technical terms
     - `IgnoreSpellingWithMath`: Ignores words containing `\` or `$`
     - `MathMode`: Ignores specific tools in math environments
     - `IgnoreCodeListings`: Ignores errors in code environments

5. **CLI** (`checkmytex/cli/`)
   - Interactive problem resolution using `rich` for terminal formatting
   - Actions: skip, Skip all, whitelist, Ignore all, edit, find, look up
   - Editor integration tracks line changes without reprocessing
   - Outputs to terminal, HTML, or JSON

6. **Web Interface** (`web_app/`)
   - FastAPI-based web application
   - Drag-and-drop ZIP upload
   - Configurable checkers and filters
   - Terminal-styled HTML output
   - Production deployment with nginx, rate limiting, SSL

### Data Flow

```
LaTeX Files → LatexDocument (flachtex + yalafi)
                    ↓
              DocumentAnalyzer
                    ↓
         [Checkers in parallel]
                    ↓
              Raw Problems
                    ↓
           [Filter Pipeline]
                    ↓
         Filtered Problems (sorted)
                    ↓
       CLI / HTML / JSON Output
```

### Problem Tracking

Each `Problem` has:
- `origin`: `Origin` object with file path, line numbers, text/source positions
- `context`: Snippet of surrounding source code
- `long_id`: Unique identifier for whitelisting (includes context)
- `rule`: Rule/error code from checker
- `tool`: Name of checker that found it

## Extending CheckMyTex

### Adding a New Checker

Create a class inheriting from `Checker`:

```python
from checkmytex.finding import Checker, Problem
from checkmytex import LatexDocument
import typing


class MyChecker(Checker):
    def check(self, document: LatexDocument) -> typing.Iterable[Problem]:
        # Access flattened source or detexed text
        source = document.get_source()

        # Find problems (e.g., with regex)
        for match in find_problems(source):
            # Trace back to original file/line
            origin = document.get_simplified_origin_of_source(
                match.start(), match.end()
            )
            context = document.get_source_context(origin)

            yield Problem(
                origin,
                "Error message here",
                context=context,
                long_id=f"MY_RULE:{context}",
                tool="MyChecker",
                rule="MY_RULE",
            )

    def is_available(self) -> bool:
        # Check if external dependencies are available
        return True
```

**Source-based vs Text-based checkers:**
- For LaTeX syntax: use `document.get_source()` and `get_simplified_origin_of_source()`
- For spelling/grammar: use `document.get_text()` and `get_simplified_origin_of_text()`

### Adding a New Filter

Create a class inheriting from `Filter`:

```python
from checkmytex.filtering import Filter
from checkmytex.finding import Problem
from checkmytex import LatexDocument
import typing


class MyFilter(Filter):
    def prepare(self, document: LatexDocument):
        # Optional: analyze document once before filtering
        pass

    def filter(self, problems: typing.Iterable[Problem]) -> typing.Iterable[Problem]:
        for problem in problems:
            if should_keep(problem):
                yield problem
```

### Language Support

For non-English languages, create a custom main file (see `examples/german.py`):
- Configure `AspellChecker(lang="de_DE")` or `CheckSpell(lang="de")`
- Configure `Languagetool(lang="de-DE")`
- Other checkers are language-agnostic

## Important Notes

### Origin Tracking
- The bidirectional mapping between detexed text → source → original files is the core innovation
- Always use `get_simplified_origin_of_source()` or `get_simplified_origin_of_text()` to ensure problems point to single file/line
- Never hardcode line numbers; always compute from origin tracking

### Source-Based Checkers (LineLengthChecker, TodoChecker)
- Access raw source with `document.sources.flat_source`
- Use `document.sources.trace_to_origin()` for position mapping
- Must handle multi-file projects correctly

### Test Documents
- `tests/test_document_*.tar.gz` are real LaTeX documents (papers, theses)
- Use these for integration testing
- Tests extract to temporary directories

### Whitelist Format
- Human-readable text file
- Each line: `long_id` of problem (includes context)
- Shared across collaborators via git

### Pre-commit Hooks
- Ruff formatting and linting
- Type checking with mypy
- Always run before committing

### External Dependencies
- aspell: Spell checking (optional, falls back to pyspellchecker)
- LanguageTool: Must be installed separately (Java-based)
- ChkTeX: From LaTeX distribution

## Project Structure
```
checkmytex/
├── __main__.py              # Entry point with default configuration
├── document_analyzer.py     # Orchestration layer
├── analyzed_document.py     # Analysis results container
├── latex_document/          # Document abstraction with origin tracking
│   ├── latex_document.py    # Main LatexDocument class
│   ├── source.py            # LatexSource (flachtex wrapper)
│   ├── detex.py             # DetexedText (yalafi wrapper)
│   ├── origin.py            # Origin tracking classes
│   └── parser.py            # LaTeX parsing utilities
├── finding/                 # Checkers (problem detection)
│   ├── abstract_checker.py  # Base Checker class
│   ├── spellcheck.py        # Aspell + pyspellchecker
│   ├── languagetool.py      # Grammar checking
│   ├── chktex.py            # LaTeX linting
│   ├── line_length.py       # Line length checker (source-based)
│   ├── todo_checker.py      # TODO/FIXME finder (source-based)
│   └── ...                  # Other checkers
├── filtering/               # Filters (false positive reduction)
│   ├── filter.py            # Base Filter class + simple filters
│   ├── whitelist.py         # Whitelist management
│   ├── authors.py           # Author name detection
│   ├── math_mode.py         # Math environment filtering
│   ├── code_listings.py     # Code environment filtering
│   └── ...
├── cli/                     # Command-line interface
│   ├── cli.py               # Interactive workflow
│   ├── arguments.py         # Argument parsing
│   └── rich_printer.py      # Terminal formatting
└── utils/                   # Utilities (editor, choices)

web_app/                     # Web interface
├── app.py                   # FastAPI application
├── templates/               # Jinja2 templates
└── nginx.conf               # Production nginx config

tests/                       # Test suite
└── test_document_*.tar.gz   # Real LaTeX documents for testing
```
