# CheckMyTex

A tool to comfortably check complex LaTeX documents, e.g., dissertations, for common errors.
There are already pretty good correction tools for LaTex, e.g., [TeXtidote](https://github.com/sylvainhalle/textidote),
[YaLafi](https://github.com/matze-dd/YaLafi), or [LaTeXBuddy](https://gitlab.com/LaTeXBuddy/LaTeXBuddy) (in which I was
involved and of which I copied some things), but they had shortcomings with complex documents, and they also did not
fit my workflow. CheckMyTex builds upon YaLafi, but provides a simple CLI with some additional magic and tricks to deal
with hopefully any document.

Primary concepts are
* not just listing problems but also their exact locations,
* working on the whole document, not just individual files (because otherwise, you forget to check some files)
* simple extension of further checking modules,
* ability to whitelist found problems and share this whitelist,
* edit the errors directly (in Vim with automatic jump to line), and
* having a single, simple command that you can easily run before every commit.

This tool does not have a fancy HTML-output (like the other tools), even though I first designed it that way.
The reason for sticking to a CLI are simple:
1. Thanks to colored output, the highlighting works just as nice in CLI as in HTML. No need to switch to your browser.
2. The CLI can use your favourite editor (currently, only (n)vim and nano have full support) without switching context.

## What does CheckMyTex currently check for you?

* Spelling errors using [pyspellchecker](https://pypi.org/project/pyspellchecker/)
* Grammar errors using [languagetool](https://languagetool.org/)
* LaTeX-smells using [ChkTeX](https://www.nongnu.org/chktex/)
* Raw numbers instead of siunitx ([simple regex](./checkmytex/checker/siunitx.py), showing you how easy new modules can be added)
* Additional advise from [proselint](https://github.com/amperser/proselint)
* (Correct) usage of cleveref.

The sources are detexed before applying grammar or spelling checking using [YaLafi](https://github.com/matze-dd/YaLafi).

Further checks may be added in the future. I do a lot of collaborative writing on papers and am constantly confronted
with bad LaTeX that I try to detect automatically.

## Install

You can install CheckMyTex using pip
```
pip install checkmytex
```

You additionally need to install [languagetool](https://languagetool.org/) and a LaTeX-distribution (which should
contain ChkTeX). 

**Currently, this tool will only work on Unix!**


## Usage

```bash
checkmytex main.tex
```

CheckMyTex will now guide you through your document and show you all problems, skipping over good parts.
For each problem, you will be asked what to do
```
[s]kip,[S]kip all,[w]hitelist,[I]gnore all,[n]ext file,[e]dit,[l]ook up,[f]ind,[?]:
```
* *skip* will skip this concrete problem, but ask you again next time you run CheckMyTex.
* *Skip all* will skip this problem and all identical problems, but ask you again on the next run of CheckMyTex.
* *whitelist* will whitelist the problem and never ask you about it again (for this document).
* *Ignore* will ignore all problems that belong to the same rule, but ask you again next time you run CheckMyTex.
* *next file* will jump to the next file.
* *edit* will open you `$EDITOR` at the location of the problem. It tries to keep track of line changes without reprocessing the document.
* *look up* will google the problem for you (if available). E.g., you can check for rare technical terms.
* *find* allows to search with a regular expression for further occurrences. Use this, e.g., to find a uniform spelling.
* *?* provides further information of the problem. Primarily for debugging and fine-tuning.

This all works with nice coloring, which I cannot directly show in this markdown file.

Whitelisted problems are by default saved in `.whitelist.txt` (document root) and are human-readable.
You can copy it to use also for other documents or change the path using the `-w` argument with a path when calling
CheckMyTex.

This tool will have problems with some areas of you document. You can exclude these areas by adding lines with
`%%PAUSE-CHECKING` and `%%CONTINUE-CHECKING`. This may be easier than whitelisting all the problems.

The time to check a 300-page dissertation is around a few seconds. A better spell checking would be available but
drastically increase the runtime.

## Development Status

This tool is still under development but already usable. Just expect some imperfections. Ideas are welcome.

### TODOs

* Reduce double-whitespace matches. They do not matter in LaTeX. Maybe clean the detexed file instead of just disabling the corresponding rules?