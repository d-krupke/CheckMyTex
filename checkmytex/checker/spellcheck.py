import re
import shutil
import typing
import urllib.parse

from spellchecker import SpellChecker
from .abstract_checker import Checker
from checkmytex.latex_document import LatexDocument, Origin
from .problem import Problem


class AspellChecker(Checker):
    def _get_words(self, document: LatexDocument) -> typing.Dict[
        str, typing.List[Origin]]:
        word_occurrences = dict()
        word_regex = re.compile(r"(^|[\s(-])(?P<word>[^\s-]+)")
        text = document.get_text()
        is_word = re.compile(r'[A-Z]?[a-z]+-?[A-Z]?[a-z]+', re.UNICODE)
        for match in word_regex.finditer(text):
            word = match.group("word").strip()
            if word[-1] in ":,.!?)":
                word = word[:-1]
            if not is_word.fullmatch(word):
                continue
            begin = match.start("word")
            origin = document.get_origin_of_text(begin, begin + len(word))
            if word not in word_occurrences:
                word_occurrences[word] = []
            word_occurrences[word].append(origin)
        return word_occurrences

    def check(self, document: LatexDocument) -> typing.Iterable[Problem]:
        print("Running spellchecking...")
        words = self._get_words(document)
        bin = shutil.which("aspell")
        word_list = '\n'.join(words.keys())
        out, err, code = self._run(f"{bin}  -a --lang=en_US", input=word_list)
        regex = re.compile(r"^\s*&\s*(?P<word>\w+)[0-9\s]*:(?P<sugg>.*)$", re.MULTILINE)
        for match in regex.finditer(out):
            word = match.group("word").strip()
            sugg = match.group("sugg").strip().split(",")
            sugg = ", ".join(sugg[:min(5, len(sugg))])
            occ = words[word]
            message = f"Check spelling of word '{word}'. Suggestions: {sugg}. Occurrences in text: {len(occ)}"
            for origin in occ:
                yield Problem(origin=origin,
                              message=message,
                              long_id=f"SPELL-{word}",
                              tool="aspell",
                              context=document.get_source_context(origin),
                              rule="SPELLING",
                              look_up_url=f"https://www.google.com/search?q={urllib.parse.quote(word)}")

    def is_available(self) -> bool:
        bin = shutil.which("aspell")
        if not bin:
            return False
        out, err, code = self._run(f"{bin} dicts")
        if "en_US" in out.split("\n"):
            return True


class CheckSpell(Checker):
    def __init__(self):
        self.spell = SpellChecker(distance=1)
        # self._word_finder = re.compile(r"")

    def check(self, document: LatexDocument) -> typing.Iterable[Problem]:
        print("Running spellchecking...")
        word_regex = re.compile(r"(^|[\s(])(?P<word>[^\s]+)")
        text = document.get_text()
        is_word = re.compile(r'[A-Z]?[a-z]+-?[A-Z]?[a-z]+', re.UNICODE)
        for match in word_regex.finditer(text):
            word = match.group("word")
            if word[-1] in ":,.!?)":
                word = word[:-1]
            if not is_word.fullmatch(word):
                continue
            if self.spell.unknown([word]):
                begin = match.start("word")
                for p in self._create_word_problems(word, begin, document,
                                                    text):
                    yield p

    def _create_word_problems(self, word, begin, document, text):
        word_elements = word.split("-")
        for word_element in word_elements:
            if len(word_element) >= 2 and self.spell.unknown([word_element]):
                origin = document.get_origin_of_text(begin, begin + len(word))
                candidates = [c for c in self.spell.candidates(word_element) if
                              c != word_element]
                context = text[max(0, begin - 20):min(len(text),
                                                      begin + len(word) + 20)]
                yield Problem(origin=origin,
                              message=f"Spelling '{word}'. Candidates: {candidates}.",
                              long_id=f"SPELL-{word}",
                              tool="pyspellchecker", context=context,
                              rule="SPELLING",
                              look_up_url=f"https://www.google.com/search?q={urllib.parse.quote(word)}")
                return  # only one problem per word, even if composite

    def is_available(self) -> bool:
        return True

    def needs_detex(self):
        return True
