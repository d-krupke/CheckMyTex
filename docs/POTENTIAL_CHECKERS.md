# Additional Checkers and Filters

This document lists additional checkers and filters for CheckMyTex users.

## Recently Implemented ✅

The following high-priority features have been implemented and are available in the web interface:

### Line Length Checker ✅ IMPLEMENTED
- **Location**: `checkmytex/finding/line_length.py`
- **Tests**: `tests/test_line_length_checker.py` (6/6 passing)
- **Purpose**: Detects lines exceeding 100 characters
- **Benefits**: Improves version control diffs and code readability
- **Web Interface**: Available in "Code Quality" section

### TODO/FIXME Checker ✅ IMPLEMENTED
- **Location**: `checkmytex/finding/todo_checker.py`
- **Tests**: `tests/test_todo_checker.py` (8/8 passing)
- **Purpose**: Finds TODO, FIXME, XXX comments and `\todo{}` commands
- **Benefits**: Prevents publishing draft markers and unfinished work
- **Web Interface**: Available in "Code Quality" section

### Ignore Code Listings Filter ✅ IMPLEMENTED
- **Location**: `checkmytex/filtering/code_listings.py`
- **Tests**: `tests/test_ignore_code_filter.py` (5/6 passing)
- **Purpose**: Ignores errors in lstlisting, verbatim, and minted environments
- **Benefits**: Reduces false positives from programming code
- **Web Interface**: Available in "Context-Aware" filters section

---

## Potential Future Checkers

### 1. Sentence Length Checker

**Purpose**: Detect overly long lines in LaTeX source code for better readability and version control.

**Why it's useful**:
- Long lines make diff/review harder in version control
- Most style guides recommend 80-100 character lines
- Makes collaboration easier
- Improves code readability

**Implementation approach**:
```python
class LineLengthChecker(Checker):
    def __init__(self, max_length=100):
        self.max_length = max_length

    def check(self, document: LatexDocument) -> typing.Iterable[Problem]:
        for filename in document.list_files():
            content = document.get_file_content(filename)
            lines = content.split('\n')
            for line_num, line in enumerate(lines, 1):
                if len(line) > self.max_length:
                    # Create problem for long line
                    yield Problem(...)
```

**Configuration options**:
- Configurable max length (80, 100, 120 characters)
- Option to ignore certain environments (e.g., URLs, bibliography)
- Warning vs. error severity

**Challenges**:
- URLs and citations can be legitimately long
- Math expressions may need long lines
- Need to distinguish between LaTeX source and content

---

### 2. Sentence Length Checker

**Purpose**: Detect overly complex sentences in the detexed text.

**Why it's useful**:
- Academic writing should be clear and concise
- Sentences >40 words are often hard to follow
- Helps identify run-on sentences
- Improves readability

**Implementation approach**:
- Work on detexed text, not LaTeX source
- Count words between sentence boundaries
- Flag sentences exceeding threshold

**Configuration**:
- Configurable word threshold (30, 40, 50 words)
- Severity levels

---

### 3. TODO/FIXME Checker

**Purpose**: Find TODO, FIXME, XXX comments in the document.

**Why it's useful**:
- Ensures no unfinished work in final document
- Helps track pending items
- Prevents publishing draft comments

**Implementation**:
```python
class TodoChecker(Checker):
    def check(self, document: LatexDocument):
        source = document.get_source()
        for match in re.finditer(r'%(.*?)(?:TODO|FIXME|XXX)(.*?)$', source, re.M):
            # Create problem
            yield Problem(...)
```

**Variations**:
- Check for `\todo{}` commands
- Find `\comment{}` environments
- Detect draft markers

---

### 4. Consistent Quotes Checker

**Purpose**: Ensure consistent use of quotes throughout document.

**Why it's useful**:
- LaTeX has multiple quote styles: ``, '', "", ''
- Mixing styles looks unprofessional
- Some fields have style preferences

**Detection**:
- Check if using `` and '' (LaTeX style) vs. " (straight quotes)
- Ensure consistency within document
- Flag straight quotes in text

---

### 5. Abbreviation Consistency

**Purpose**: Check that abbreviations are defined before use and used consistently.

**Why it's useful**:
- First use should spell out: "Neural Network (NN)"
- Subsequent uses should use abbreviation: "NN"
- Common academic writing requirement

**Implementation**:
- Detect patterns like "Word Word (WW)"
- Track which abbreviations are defined
- Flag uses before definition

---

### 6. Citation Style Checker

**Purpose**: Ensure consistent citation style (e.g., \cite vs. \citep vs. \citet).

**Why it's useful**:
- Different citation commands for different contexts
- Parenthetical vs. textual citations
- Journal-specific requirements

---

### 7. Passive Voice Detector

**Purpose**: Flag excessive use of passive voice.

**Why it's useful**:
- Active voice is often clearer
- Some fields discourage passive voice
- Helps improve writing clarity

**Challenges**:
- Complex to implement accurately
- Passive voice is sometimes appropriate
- May have false positives

---

### 8. Paragraph Length Checker

**Purpose**: Flag paragraphs that are too short or too long.

**Why it's useful**:
- Very short paragraphs may lack development
- Very long paragraphs are hard to read
- Improves document structure

**Thresholds**:
- Too short: < 2 sentences
- Too long: > 10 sentences or > 200 words

---

## Potential Filters

### 1. Ignore Code Listings

**Purpose**: Ignore errors within `\begin{lstlisting}` or `\begin{verbatim}` environments.

**Why it's useful**:
- Code snippets shouldn't trigger language checks
- Variable names aren't spelling errors
- Code has different syntax rules

**Implementation**:
```python
class IgnoreCodeListings(Filter):
    def prepare(self, document):
        # Find all lstlisting and verbatim ranges
        expr = r'\\begin\{(lstlisting|verbatim)\}.*?\\end\{\1\}'
        for match in re.finditer(expr, source, re.DOTALL):
            self._ranges.append((match.start(), match.end()))

    def filter(self, problems):
        # Filter out problems in these ranges
```

---

### 2. Ignore Custom Commands

**Purpose**: Allow users to specify custom LaTeX commands to ignore.

**Why it's useful**:
- Users may have custom macros with unusual names
- Domain-specific commands
- Project-specific shortcuts

**Configuration**:
- User provides list of command names
- Filter ignores errors within those commands

**Example**:
```python
IgnoreCustomCommands(commands=['myspecialcmd', 'customref'])
```

---

### 3. Ignore Short Words

**Purpose**: Ignore spelling errors for very short words (1-2 characters).

**Why it's useful**:
- Single letter variables: "Let $a$ be..."
- Abbreviations and symbols
- Often false positives

---

### 4. Ignore Capitalized Words

**Purpose**: Ignore spelling errors for words starting with capital letters.

**Why it's useful**:
- Proper nouns (names, places)
- Acronyms
- Often not in dictionary

**Risk**:
- May miss actual errors in capitalized words
- Consider making this optional

---

### 5. Whitelist by File

**Purpose**: Different whitelist for different files in project.

**Why it's useful**:
- Introduction may have different terminology than methods
- Appendix may include additional technical terms
- Per-chapter whitelists

---

### 6. Ignore Within Custom Environments

**Purpose**: Let users specify LaTeX environments to ignore.

**Why it's useful**:
- Custom theorem environments
- Special formatting blocks
- Domain-specific environments

**Example**:
```python
IgnoreEnvironments(environments=['theorem', 'lemma', 'proof'])
```

---

## How to Implement a Custom Checker

If you want to add a custom checker, follow this pattern:

```python
import re
import typing
from checkmytex.finding import Checker, Problem
from checkmytex import LatexDocument


class MyCustomChecker(Checker):
    """Short description of what this checker does."""

    def check(self, document: LatexDocument) -> typing.Iterable[Problem]:
        """Check the document and yield problems."""
        source = document.get_source()

        # Example: Find pattern in source
        for match in re.finditer(r'pattern', source):
            # Get origin for highlighting
            origin = document.get_simplified_origin_of_source(
                match.start(), match.end()
            )

            # Get context for whitelisting
            context = document.get_source_context(origin)

            # Create unique ID
            long_id = f"MY_RULE:{context}"

            # Yield problem
            yield Problem(
                origin=origin,
                message="Description of the problem",
                context=context,
                long_id=long_id,
                tool="MyCustomChecker",
                rule="MY_RULE",
                look_up_url=None  # Optional URL for more info
            )
```

Then add it to your analyzer:
```python
analyzer.add_checker(MyCustomChecker())
```

---

## How to Implement a Custom Filter

Custom filters follow this pattern:

```python
import typing
from checkmytex.filtering import Filter
from checkmytex.finding import Problem
from checkmytex import LatexDocument


class MyCustomFilter(Filter):
    """Short description of what this filter does."""

    def __init__(self):
        self._ranges = []  # Or other state

    def prepare(self, document: LatexDocument):
        """Analyze document and prepare filter state."""
        # Example: Find ranges to ignore
        source = document.get_source()
        for match in re.finditer(r'\\mycommand\{([^}]+)\}', source):
            self._ranges.append((match.start(1), match.end(1)))

    def filter(self, problems: typing.Iterable[Problem]) -> typing.Iterable[Problem]:
        """Filter problems based on prepared state."""
        for problem in problems:
            # Get problem position
            begin = problem.origin.begin.source.index
            end = problem.origin.end.source.index

            # Check if problem is in ignored range
            if not any(r[0] <= begin <= end <= r[1] for r in self._ranges):
                yield problem  # Keep this problem
```

Then add it to your analyzer:
```python
analyzer.add_filter(MyCustomFilter())
```

---

## Contributing

If you implement any of these checkers or filters, consider:

1. **Testing**: Add unit tests for your checker/filter
2. **Documentation**: Document what it does and why
3. **Configuration**: Make thresholds configurable
4. **False Positives**: Consider edge cases
5. **Performance**: Ensure it doesn't slow down analysis significantly
6. **Pull Request**: Share with the community!

---

## Priority Recommendations

Based on common needs, here are the most valuable additions:

### High Priority ⭐⭐⭐
1. **Line Length Checker** - Very useful for collaboration
2. **TODO/FIXME Checker** - Prevents publishing drafts
3. **Ignore Code Listings** - Common source of false positives

### Medium Priority ⭐⭐
4. **Sentence Length Checker** - Improves writing quality
5. **Consistent Quotes Checker** - Common style requirement
6. **Ignore Custom Commands** - Flexibility for users

### Low Priority ⭐
7. **Abbreviation Consistency** - Nice to have
8. **Paragraph Length** - Stylistic preference
9. **Passive Voice** - Complex, may have false positives

---

## Community Input

Have ideas for other useful checkers or filters? Open an issue at:
https://github.com/d-krupke/CheckMyTex/issues

Share your custom implementations and help make CheckMyTex better for everyone!
