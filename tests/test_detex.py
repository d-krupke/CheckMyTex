from checkmytex.latex_document.detex import DetexedText


class TestDetex:
    def test_single_line(self):
        detex = DetexedText("0123456789")
        for i in range(10):
            assert detex.get_position_in_source(i) == i
