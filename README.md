# CheckMyTex

A tool to comfortably check complex LaTeX documents, e.g., dissertations, for
common errors. There are already pretty good correction tools for LaTex, e.g.,
[TeXtidote](https://github.com/sylvainhalle/textidote),
[YaLafi](https://github.com/matze-dd/YaLafi) (of which we use the tex2text
engine), or [LaTeXBuddy](https://gitlab.com/LaTeXBuddy/LaTeXBuddy) (in which I
was involved and of which I copied some things), but they had shortcomings with
complex documents, and they also did not fit my workflow. CheckMyTex builds upon
YaLafi, but provides a simple CLI with some additional magic and tricks to deal
with hopefully any document. The primary difference to its main contenders is
the focus on CLI and whitelists.

> :warning: Your terminal needs to support rich (should be most terminals)!

Primary concepts are

- not just listing problems but also their exact locations,
- working on the whole document, not just individual files (because otherwise,
  you forget to check some files),
- lots of predefined rules such as newcommand-substitution, todo-removal, etc.,
- simple extension of further checking modules,
- ability to whitelist found problems and share this whitelist,
- edit the errors directly (in Vim with automatic jump to line), and
- having a single, simple command that you can easily run before every commit.

This tool has a fancy HTML-output (like other tools), but its primary intention
is to be used as CLI:

1. Thanks to colored output, the highlighting works just as nice in CLI as in
   HTML. No need to switch to your browser.
2. The CLI can use your favourite editor (currently, only (n)vim and nano have
   full support) without switching context.

An example output can be seen
[here](https://htmlpreview.github.io/?https://github.com/d-krupke/CheckMyTex/blob/main/example_output.html).
The CLI version looks nearly identical (thanks to
[rich](https://rich.readthedocs.io/en/stable/introduction.html), but you are
iteratively asked how to deal with each problem.

## What does CheckMyTex currently check for you?

- Spelling errors using aspell or
  [pyspellchecker](https://pypi.org/project/pyspellchecker/)
- Grammar errors using [languagetool](https://languagetool.org/)
- LaTeX-smells using [ChkTeX](https://www.nongnu.org/chktex/)
- Raw numbers instead of siunitx ([simple regex](checkmytex/finding/siunitx.py),
  showing you how easy new modules can be added)
- Additional advise from [proselint](https://github.com/amperser/proselint)
- (Correct) usage of cleveref.
- Uniform writing style of NP-hard/complete (this is probably a problem only
  within my community, but it doesn't harm you)

I found this set of tools to be sufficient to find most problems in text and
LaTeX-source, and I am constantly surprised on how well it works.

The sources are detexed before applying grammar or spelling checking using
[YaLafi](https://github.com/matze-dd/YaLafi).

Further checks may be added in the future. I do a lot of collaborative writing
on papers and am constantly confronted with bad LaTeX that I try to detect
automatically.

## Install

You can install CheckMyTex using pip (if you have Python3 installed)

```
pip install checkmytex
```

You additionally need to install [languagetool](https://languagetool.org/) and a
LaTeX-distribution (which should contain ChkTeX). To have a better spell
checker, you should also install aspell and the corresponding dictionaries. All
these should be available via yours systems package manages, e.g. `pacman`,
`apt`, or `brew`.

> :warning: This tool currently only supports Unix (Linux and Mac OS). It could
> work in some windows configurations, but probably you get some unexpected
> behavior due to incompatible system calls.

### Mac

```shell
brew install --cask mactex  # install a tex distribution
brew install languagetool  # install the grammar checker languagetool
brew install aspell  # install a dictionary
```

### Arch Linux

```shell
sudo pacman -S texlive-most languagetool aspell aspell-en
```

## Usage

```bash
checkmytex main.tex
```

CheckMyTex will now guide you through your document and show you all problems,
skipping over good parts. For each problem, you will be asked what to do

```
[s]kip,[S]kip all,[w]hitelist,[I]gnore all,[n]ext file,[e]dit,[l]ook up,[f]ind,[?]:
```

- _skip_ will skip this concrete problem, but ask you again next time you run
  CheckMyTex.
- _Skip all_ will skip this problem and all identical problems, but ask you
  again on the next run of CheckMyTex.
- _whitelist_ will whitelist the problem and never ask you about it again (for
  this document).
- _Ignore_ will ignore all problems that belong to the same rule, but ask you
  again next time you run CheckMyTex.
- _next file_ will jump to the next file.
- _edit_ will open you `$EDITOR` at the location of the problem. It tries to
  keep track of line changes without reprocessing the document.
- _look up_ will google the problem for you (if available). E.g., you can check
  for rare technical terms.
- _find_ allows to search with a regular expression for further occurrences. Use
  this, e.g., to find a uniform spelling.
- _?_ provides further information of the problem. Primarily for debugging and
  fine-tuning.

Whitelisted problems are by default saved in `.whitelist.txt` (document root)
and are human-readable. You can copy it to use also for other documents or
change the path using the `-w` argument with a path when calling CheckMyTex.

This tool will have problems with some areas of you document. You can exclude
these areas by adding lines with `%%PAUSE-CHECKING` and `%%CONTINUE-CHECKING`.
This may be easier than whitelisting all the problems.

The time to check a 300-page dissertation is around a few seconds. A better
spell checking would be available but drastically increase the runtime.

If you want to process the output with another tool, you can export the result
as json using:

```bash
checkmytex --json analysis.json main.tex
```

If you want an HTML-document you can share with your co-authors, use

```bash
checkmytex --html analysis.html main.tex
```

## Extending CheckMyTex

### Finding problems in the LaTeX document

CheckMyTex already comes with a set of very useful tools and rules to find
potential problems.

```python
from checkmytex.finding import (
    Languagetool,
    AspellChecker,
    CheckSpell,
    UniformNpHard,
    Cleveref,
    Proselint,
    SiUnitx,
)
```

You can also easily create your own rule. For example, a common antipattern in
my community is to exclude many lines of text by defining a `\old{..}`-command.
Let us quickly write a rule that detects this behavior, using a simple regular
expression.

Note that `LatexDocument` provides us with all the necessary tools to read
source and compiled latex, as well as trace the problem back to its origin.

```python
import re
from checkmytex.finding import Checker, Problem
from checkmytex import LatexDocument
import typing


class NoOld(Checker):
    def check(self, document: LatexDocument) -> typing.Iterable[Problem]:
        source = document.get_source()
        for match in re.finditer(r"\\old\{", source):
            origin = document.get_simplified_origin_of_source(
                match.start(), match.end()
            )
            context = document.get_source_context(origin)
            long_id = f"NO_OLD:{context}"
            yield Problem(
                origin,
                "Please do not use \\old{! (it confuses highlighting)",
                context=context,
                long_id=long_id,
                tool="CustomNoOld",
                rule="NO_OLD",
            )
```

This is all! Now you can add this rule to the `DocumentAnalyzer` with
`add_checker`. You may want to copy the main.py and build yourself a custom
version that directly includes this rule.

### Filtering patterns of false positives

Some false positives follow some pattern. For example author names are usually
not in any dictionary. The current default already tries to detect if a spelling
error is actually an author name and automatically removes it. You can easily
write such a filter yourself.

By default, CheckMyTex comes with the following filtering rules:

- Spelling errors in `\includegraphics`-paths.
- Spelling errors in labels.
- Spelling errors of words used in the bibliography. This also removes a lot of
  author names from the problem list.
- Spelling errors of author names before a `\cite`
- Problems in the whitelist.
- Ignore words used repeatedly in adjacent sentences (currently only the word
  "problem").
- Words with `\` or `$` in them. They are usually terms and not proper words.

Let us extend these rules: imagine you don't want any errors within an
align-environment shown.

```python
import re
import typing

from checkmytex.filtering import Filter
from checkmytex.finding import Problem
from checkmytex import LatexDocument


class FilterAlign(Filter):
    def __init__(self):
        self._ranges = []

    def prepare(self, document: LatexDocument):
        #  analyze which parts of the source are align-environments using a regular expression
        expr = r"\\begin\{align\}.*?\\end\{align\}"
        source = document.get_source()
        for match in re.finditer(expr, source, re.MULTILINE | re.DOTALL):
            self._ranges.append((match.start(), match.end()))

    def filter(self, problems: typing.Iterable[Problem]) -> typing.Iterable[Problem]:
        for p in problems:
            s_span = p.origin.get_source_span()
            if any(r[0] <= s_span[0] < r[1] for r in self._ranges):
                continue  # problem starts within a previous found range of an align-environment
            yield p
```

We can add this filter similar to a checker to the `DocumentAnalyzer`.

## Other Languages

Other languages are partially supported: You need to create your own main-file
and provide the right language codes for the different tools. An example for
german can be found in [german.py](./examples/german.py).

## Development Status

This tool is still under development but already usable. Just expect some
imperfections. Ideas are welcome.

### TODOs

- Reduce double-whitespace matches. They do not matter in LaTeX. Maybe clean the
  detexed file instead of just disabling the corresponding rules?
- More configuration options. Currently, the best option is to simply build your
  own [main.py](./checkmytex/__main__.py)

## Changes

- 0.10.5: Fixing `--print` option.
- 0.10.4: Fixing exception when $EDITOR is not set.
- 0.10.3: Making project slightly more robust.
- 0.10.2: Making project pep compliant.
- 0.10.1: Also the interactive mode is now using rich.
- 0.10.0: Beautiful HTML-output using _rich_. Interactive CLI will follow soon.
- 0.9.0: Fundamental refactoring and JSON-ouput.
- 0.8.1: Fixing problem with text manipulated by commands. All found errors now
  should only span a single line. Solution is ugly and should be improved. For
  now, it is working. .
