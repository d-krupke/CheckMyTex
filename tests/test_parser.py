import flachtex
from checkmytex.latex_document.parser import LatexParser


class TestSource:
    def test_single_line(self):
        files = {"main.tex": "0123456789"}
        parser = LatexParser(flachtex.FileFinder(file_system=files))
        sources = parser.parse_source("main.tex")
        assert str(sources.flat_source) == files["main.tex"]
        for i in range(10):
            assert sources.investigate_origin(i).position.index == i
            o = sources.get_simplified_origin_range(i, i + 1)
            assert o[0].position.index == i
            assert o[1].position.index == i + 1


class TestLatexDocument:
    def test_single_line(self):
        files = {"main.tex": "0123456789"}
        parser = LatexParser(flachtex.FileFinder(file_system=files))
        document = parser.parse("main.tex")
        for i in range(10):
            origin = document.get_simplified_origin_of_source(i, i + 1)
            assert origin.begin.file.position.index == i
            assert origin.end.file.position.index == i + 1
        for i in range(10):
            origin = document.get_simplified_origin_of_text(i, i + 1)
            assert origin.begin.file.position.index == i
            assert origin.end.file.position.index == i + 1
