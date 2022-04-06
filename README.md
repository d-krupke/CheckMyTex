# CheckMyTex

A tool to comfortably check complex LaTeX documents, e.g., dissertations.

This is a super early prototype.

## Components

* languagetool
* chktex
* YaLaFi
* flachtex
* pyspellchecker

These tools may have different licences.

## Features:

* Wraps a set of tools for checking LaTex-smells, spelling errors, and grammatical issues.
* Simple command line interface.
* Whitelist
* Directly edit the file. (works with vim and nano for now)
* Can process complex LaTeX-documents (most other tools work file based).

## Usage:

```bash
checkmytex main.tex
```
Problems are now listed one after the other and you get multiple
options to deal with it.