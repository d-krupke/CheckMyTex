"""
Modules for spellchecking.
"""

import re
import shutil
import typing
import urllib.parse

from spellchecker import SpellChecker

from checkmytex.latex_document import LatexDocument, Origin

from .abstract_checker import Checker
from .problem import Problem


class AspellChecker(Checker):
    def __init__(self, lang: str = "en_US"):
        super().__init__()
        self.lang = lang

    def _get_words(self, document: LatexDocument) -> dict[str, list[Origin]]:
        word_occurrences: dict[str, list[Origin]] = {}
        word_regex = re.compile(r"(^|[\s(-])(?P<word>[^\s-]+)")
        text = document.get_text()
        is_word = re.compile(r"[A-Z]?[a-z]+-?[A-Z]?[a-z]+", re.UNICODE)
        for match in word_regex.finditer(text):
            word = match.group("word").strip()
            if word and word[-1] in ":,.!?)":
                word = word[:-1]
            if not is_word.fullmatch(word):
                continue
            begin = match.start("word")
            origin = document.get_simplified_origin_of_text(begin, begin + len(word))
            if word not in word_occurrences:
                word_occurrences[word] = []
            word_occurrences[word].append(origin)
        return word_occurrences

    def check(self, document: LatexDocument) -> typing.Iterable[Problem]:
        self.log("Running spellchecking...")
        words = self._get_words(document)
        bin = shutil.which("aspell")
        word_list = "\n".join(words.keys())
        out, _err, _code = self._run(f"{bin}  -a --lang={self.lang}", input=word_list)
        regex = re.compile(r"^\s*&\s*(?P<word>\w+)[0-9\s]*:(?P<sugg>.*)$", re.MULTILINE)
        for match in regex.finditer(out):
            word = match.group("word").strip()
            sugg = match.group("sugg").strip().split(",")
            sugg = ", ".join(sugg[: min(5, len(sugg))])
            occ = words[word]
            message = (
                f"Check spelling of word '{word}'."
                f" Suggestions: {sugg}. Occurrences in text: {len(occ)}"
            )
            url = f"https://www.google.com/search?q={urllib.parse.quote(word)}"
            for origin in occ:
                yield Problem(
                    origin=origin,
                    message=message,
                    long_id=f"SPELL-{word}",
                    tool="aspell",
                    context=document.get_source_context(origin),
                    rule="SPELLING",
                    look_up_url=url,
                )

    def is_available(self) -> bool:
        """
        Check if this tool is available on the system.
        :return: True if it is available.
        """
        bin_path = shutil.which("aspell")
        if not bin_path:
            return False
        out, err, code = self._run(f"{bin_path} dicts")
        if code:  # something happened.
            self.log("Could not query aspell dicts:", err)
            return False
        if self.lang in out.split("\n"):
            return True
        self.log(f"Could not find aspell dictionary for {self.lang}.")
        return False


class CheckSpell(Checker):
    def __init__(self, lang: str = "en"):
        super().__init__()
        self.spell = SpellChecker(distance=1, language=lang)
        # self._word_finder = re.compile(r"")

    def check(self, document: LatexDocument) -> typing.Iterable[Problem]:
        self.log("Running spellchecking...")
        word_regex = re.compile(r"(^|[\s(])(?P<word>[^\s]+)")
        text = document.get_text()
        is_word = re.compile(r"[A-Z]?[a-z]+-?[A-Z]?[a-z]+", re.UNICODE)
        for match in word_regex.finditer(text):
            word = match.group("word")
            if word and word[-1] in ":,.!?)":
                word = word[:-1]
            if not is_word.fullmatch(word):
                continue
            if self.spell.unknown([word]):
                begin = match.start("word")
                p = self._create_word_problems(word, begin, document, text)
                if p is not None:
                    yield p

    def _create_word_problems(self, word, begin, document, text):
        word_elements = word.split("-")
        for word_element in word_elements:
            if len(word_element) < 2 or not self.spell.unknown([word_element]):
                continue
            origin = document.get_simplified_origin_of_text(begin, begin + len(word))
            candidates = self.spell.candidates(word_element)
            candidates = (
                [c for c in self.spell.candidates(word_element) if c != word_element]
                if candidates
                else []
            )  # candidates can be none
            context = text[max(0, begin - 20) : min(len(text), begin + len(word) + 20)]
            url = f"https://www.google.com/search?q={urllib.parse.quote(word)}"
            msg = f"Spelling '{word}'. Candidates: {candidates}."
            return Problem(  # only one problem per word, even if composite
                origin=origin,
                message=msg,
                long_id=f"SPELL-{word}",
                tool="pyspellchecker",
                context=context,
                rule="SPELLING",
                look_up_url=url,
            )
        return None

    def is_available(self) -> bool:
        return True

    def needs_detex(self):
        return True
