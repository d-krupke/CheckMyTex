from checkmytex.latex_document.parser import LatexParser
from flachtex import FileFinder


class TestLatexDocument:
    def test_1(self):
        sources = {"/main.tex": "0123\n\tBCD\nXYZ\n"}
        parser = LatexParser(file_finder=FileFinder("/", sources))
        document = parser.parse("/main.tex")
        assert document.get_source() == sources["/main.tex"]
        assert document.get_text() == sources["/main.tex"]
        for i in range(4):
            o1 = document.get_simplified_origin_of_source(i, i + 1)
            o2 = document.get_simplified_origin_of_text(i, i + 1)
            assert o1 == o2
        for i in range(5, 8):
            o1 = document.get_simplified_origin_of_source(i, i + 1)
            o2 = document.get_simplified_origin_of_text(i, i + 1)
            assert o1 == o2

    def test_2(self):
        sources = {"/main.tex": "0123\n\\input{sub.tex}\nXYZ\n", "/sub.tex": "ABC\n"}
        parser = LatexParser(file_finder=FileFinder("/", sources))
        document = parser.parse("/main.tex")
        for i in range(4):
            o1 = document.get_simplified_origin_of_source(i, i + 1)
            o2 = document.get_simplified_origin_of_text(i, i + 1)
            assert o1 == o2
        for i in range(5, 8):
            o1 = document.get_simplified_origin_of_source(i, i + 1)
            o2 = document.get_simplified_origin_of_text(i, i + 1)
            assert o1 == o2
            assert o1.get_file() == "/sub.tex"
            assert o1.get_file_span() == (i - 5, i - 5 + 1)

    def test_3(self):
        sources = {
            "/main.tex": "\\input{sub.tex}\n",
            "/sub.tex": "\\input{A.tex}\n\\input{B.tex}\n\\input{C.tex}",
            "/A.tex": "A0\nA1\nA2\n",
            "/B.tex": "B0\nB1\nB2\n",
            "/C.tex": "C0\nC1\nC2",
        }
        parser = LatexParser(file_finder=FileFinder("/", sources))
        document = parser.parse("/main.tex")
        for f in ["A", "B", "C"]:
            for i in range(3):
                key = f"{f}{i}"
                p = document.get_text().find(key)
                origin = document.get_simplified_origin_of_source(p, p + 1)
                assert origin == document.get_simplified_origin_of_text(p, p + 1)
                assert origin.get_file() == "/" + f + ".tex"
                assert origin.get_file_span()[0] == 3 * i
                assert origin.get_file_line() == i

    def test_4(self):
        sources = {
            "/main.tex": "\\input{sub.tex}\n",
            "/sub.tex": "\\input{A.tex}\n\\input{B.tex}\n\\input{C.tex}",
            "/A.tex": "A0\nA1\nA2\n",
            "/B.tex": "\nB1\nB2\n",
            "/C.tex": "C0\nC1\nC2",
        }
        parser = LatexParser(file_finder=FileFinder("/", sources))
        document = parser.parse("/main.tex")
        for f in ["A", "B", "C"]:
            for i in range(3):
                key = f"{f}{i}"
                if key == "B0":
                    continue
                if f == "B":
                    file = "/" + f + ".tex"
                    pos_begin = 3 * i - 2
                    pos_end = 3 * i + 1 - 2
                else:
                    file = "/" + f + ".tex"
                    pos_begin = 3 * i
                    pos_end = 3 * i + 1
                p = document.get_text().find(key)
                origin = document.get_simplified_origin_of_source(p, p + 1)
                assert origin.get_file() == file
                assert origin.get_file_span() == (pos_begin, pos_end)
