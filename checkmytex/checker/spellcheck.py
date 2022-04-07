import re
import typing
import urllib.parse

from spellchecker import SpellChecker
from checkmytex.checker.abstract_checker import Checker
from checkmytex.latex_document import LatexDocument
from checkmytex.problem import Problem


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
