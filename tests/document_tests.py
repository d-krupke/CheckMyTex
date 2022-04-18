import unittest

from flachtex import FileFinder

from checkmytex.latex_document import LatexDocument, Origin


class LatexDocumentTest(unittest.TestCase):
    def test_1(self):
        sources = {"/main.tex": "0123\n\tBCD\nXYZ\n"}
        document = LatexDocument(
            "/main.tex", file_finder=FileFinder("/", "/main.tex", sources)
        )
        self.assertEqual(document.get_source(), sources["/main.tex"])
        self.assertEqual(document.get_text(), sources["/main.tex"])
        for i in range(4):
            o1 = document.get_origin_of_source(i, i + 1)
            o2 = document.get_origin_of_text(i, i + 1)
            o3 = Origin(
                "/main.tex",
                Origin.Position(i, 0, i, 0),
                Origin.Position(i + 1, 0, i + 1, 0),
            )
            self.assertEqual(o1, o2)
            self.assertEqual(o1, o3)
        for i in range(5, 8):
            j = i - 5
            o1 = document.get_origin_of_source(i, i + 1)
            o2 = document.get_origin_of_text(i, i + 1)
            o3 = Origin(
                "/main.tex",
                Origin.Position(i, 1, j, 0),
                Origin.Position(i + 1, 1, j + 1, 0),
            )
            self.assertEqual(o1, o2)
            self.assertEqual(o1, o3)

    def test_2(self):

        sources = {"/main.tex": "0123\n\\input{sub.tex}\nXYZ\n", "/sub.tex": "ABC\n"}
        document = LatexDocument(
            "/main.tex", file_finder=FileFinder("/", "/main.tex", sources)
        )
        for i in range(4):
            o1 = document.get_origin_of_source(i, i + 1)
            o2 = document.get_origin_of_text(i, i + 1)
            o3 = Origin(
                "/main.tex",
                Origin.Position(i, 0, i, 0),
                Origin.Position(i + 1, 0, i + 1, 0),
            )
            self.assertEqual(o1, o2)
            self.assertEqual(o1, o3)
        for i in range(5, 8):
            j = i - 5
            o1 = document.get_origin_of_source(i, i + 1)
            o2 = document.get_origin_of_text(i, i + 1)
            o3 = Origin(
                "/sub.tex",
                Origin.Position(j, 0, j, 0),
                Origin.Position(j + 1, 0, j + 1, 0),
            )
            self.assertEqual(o1, o2)
            self.assertEqual(o1, o3)

    def test_3(self):
        sources = {
            "/main.tex": "\\input{sub.tex}\n",
            "/sub.tex": "\\input{A.tex}\n\\input{B.tex}\n\\input{C.tex}",
            "/A.tex": "A0\nA1\nA2\n",
            "/B.tex": "B0\nB1\nB2\n",
            "/C.tex": "C0\nC1\nC2",
        }
        document = LatexDocument(
            "/main.tex", file_finder=FileFinder("/", "/main.tex", sources)
        )
        for f in ["A", "B", "C"]:
            for i in range(0, 3):
                key = f"{f}{i}"
                origin = Origin(
                    "/" + f + ".tex",
                    Origin.Position(3 * i, i, 0, 0),
                    Origin.Position(3 * i + 1, i, 1, 0),
                )
                p = document.get_text().find(key)
                self.assertEqual(origin, document.get_origin_of_source(p, p + 1))
                self.assertEqual(origin, document.get_origin_of_text(p, p + 1))

    def test_4(self):
        sources = {
            "/main.tex": "\\input{sub.tex}\n",
            "/sub.tex": "\\input{A.tex}\n\\input{B.tex}\n\\input{C.tex}",
            "/A.tex": "A0\nA1\nA2\n",
            "/B.tex": "\nB1\nB2\n",
            "/C.tex": "C0\nC1\nC2",
        }
        document = LatexDocument(
            "/main.tex", file_finder=FileFinder("/", "/main.tex", sources)
        )
        for f in ["A", "B", "C"]:
            for i in range(0, 3):
                key = f"{f}{i}"
                if key == "B0":
                    continue
                if f == "B":
                    origin = Origin(
                        "/" + f + ".tex",
                        Origin.Position(3 * i - 2, i, 0, 0),
                        Origin.Position(3 * i + 1 - 2, i, 1, 0),
                    )
                else:
                    origin = Origin(
                        "/" + f + ".tex",
                        Origin.Position(3 * i, i, 0, 0),
                        Origin.Position(3 * i + 1, i, 1, 0),
                    )
                p = document.get_text().find(key)
                self.assertEqual(origin, document.get_origin_of_source(p, p + 1))
                self.assertEqual(origin, document.get_origin_of_text(p, p + 1))
