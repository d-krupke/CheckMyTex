"""
A collection of tools (or their wrappers) to find problems in a latex document.
"""
# flake8: noqa F401
from .abstract_checker import Checker
from .chktex import ChkTex
from .cleveref import Cleveref
from .languagetool import Languagetool
from .nphard import UniformNpHard
from .problem import Problem
from .proselint import Proselint
from .siunitx import SiUnitx
from .spellcheck import AspellChecker, CheckSpell

__all__ = (
    Checker,
    ChkTex,
    Cleveref,
    Languagetool,
    UniformNpHard,
    Problem,
    Proselint,
    SiUnitx,
    AspellChecker,
    CheckSpell,
)
