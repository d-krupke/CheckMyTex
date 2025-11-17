import shutil
import tarfile
import urllib.request
from pathlib import Path

from checkmytex import DocumentAnalyzer
from checkmytex.cli.rich_printer import RichPrinter
from checkmytex.filtering import (
    IgnoreIncludegraphics,
    IgnoreLikelyAuthorNames,
    IgnoreRefs,
    IgnoreRepeatedWords,
    IgnoreSpellingWithMath,
    IgnoreWordsFromBibliography,
    MathMode,
)
from checkmytex.latex_document.parser import LatexParser


def analyze(path):
    path = str(path)
    parser = LatexParser()
    latex_document = parser.parse(path)
    engine = DocumentAnalyzer()
    engine.setup_default()
    # Add filter
    # engine.add_filter(whitelist)
    engine.add_filter(IgnoreIncludegraphics())
    engine.add_filter(IgnoreRefs())
    engine.add_filter(IgnoreRepeatedWords(["problem", "problems"]))
    engine.add_filter(IgnoreLikelyAuthorNames())
    engine.add_filter(IgnoreWordsFromBibliography())
    engine.add_filter(IgnoreSpellingWithMath())
    engine.add_filter(
        MathMode({"SPELLING": None, "languagetool": None, "Proselint": None})
    )
    analyzed_document = engine.analyze(latex_document)
    RichPrinter(analyzed_document).to_html(f"{path}_analysis.html")


def download(url, extract_to, main_file):
    def tex_file_filter(tarinfo, _path):
        if tarinfo.name.endswith(".tex"):
            return tarinfo
        return None

    if not Path(main_file).is_dir():
        path_tar = extract_to + ".tar.gz"
        urllib.request.urlretrieve(url, path_tar)
        assert tarfile.is_tarfile(path_tar)
        with tarfile.open(path_tar) as tar:
            tar.extractall(extract_to, filter=tex_file_filter)


class TestArxiv:
    def test_1(self):
        if not bool(shutil.which("languagetool")):
            return
        url = "https://arxiv.org/e-print/1505.03116"
        path_folder = "test_document_1"
        main_path = Path(path_folder) / "main.tex"
        download(url, path_folder, main_path)
        analyze(main_path)

    def test_2(self):
        if not bool(shutil.which("languagetool")):
            return
        url = "https://arxiv.org/e-print/2203.07444"
        path_folder = "test_document_2"
        main_path = Path(path_folder) / "survey.tex"
        download(url, path_folder, main_path)
        analyze(main_path)

    def test_3(self):
        if not bool(shutil.which("languagetool")):
            return
        url = "https://arxiv.org/e-print/2103.14599"
        path_folder = "test_document_3"
        main_path = Path(path_folder) / "main.tex"
        download(url, path_folder, main_path)
        analyze(main_path)

    def test_4(self):
        if not bool(shutil.which("languagetool")):
            return
        url = "https://arxiv.org/e-print/2204.10836"
        path_folder = "test_document_4"
        main_path = Path(path_folder) / "main.tex"
        download(url, path_folder, main_path)
        analyze(main_path)

    def test_5(self):
        if not bool(shutil.which("languagetool")):
            return
        url = "https://arxiv.org/e-print/1604.06057"
        path_folder = "test_document_5"
        main_path = Path(path_folder) / "main.tex"
        download(url, path_folder, main_path)
        analyze(main_path)

    def test_6(self):
        if not bool(shutil.which("languagetool")):
            return
        url = "https://arxiv.org/e-print/2305.16303"
        path_folder = "test_document_6"
        main_path = Path(path_folder) / "main.tex"
        download(url, path_folder, main_path)
        analyze(main_path)
