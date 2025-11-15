from checkmytex.latex_document.indexed_string import IndexedText


class TestIndexedString:
    def test_1(self):
        text = "123\n456\n789"
        inds = IndexedText(text)
        assert inds._index == [0, 4, 8]

        def to_tuple(pos):
            return pos.line, pos.line_offset

        assert to_tuple(inds.get_detailed_position(0)) == (0, 0)
        assert to_tuple(inds.get_detailed_position(2)) == (0, 2)
        assert to_tuple(inds.get_detailed_position(4)) == (1, 0)
        assert to_tuple(inds.get_detailed_position(5)) == (1, 1)
        assert to_tuple(inds.get_detailed_position(8)) == (2, 0)
        assert to_tuple(inds.get_detailed_position(9)) == (2, 1)

    def test_2(self):
        text = "123\n456\n789"
        inds = IndexedText(text)
        assert inds.get_line(0) == "123\n"
        assert inds.get_line(1) == "456\n"
        assert inds.get_line(2) == "789"
