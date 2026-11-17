"""
Copyright (c) Cutleast
"""

from cutleast_core_lib.core.utilities.text_diff import DiffChunk, get_word_diff


class TestTextDiff:
    """
    Tests `cutleast_core_lib.core.utilities.text_diff`.
    """

    def test_identical_texts(self) -> None:
        """
        Tests that identical texts result in a single equal chunk.
        """

        # given
        text: str = "This is a sword."

        # when
        chunks: list[DiffChunk] = get_word_diff(text, text)

        # then
        assert chunks == [DiffChunk(kind=DiffChunk.Kind.Equal, text=text)]

    def test_empty_texts(self) -> None:
        """
        Tests that two empty texts result in no chunks.
        """

        # when
        chunks: list[DiffChunk] = get_word_diff("", "")

        # then
        assert chunks == []

    def test_insertion(self) -> None:
        """
        Tests that inserted words result in an added chunk.
        """

        # when
        chunks: list[DiffChunk] = get_word_diff("A sword.", "A sharp sword.")

        # then
        assert chunks == [
            DiffChunk(kind=DiffChunk.Kind.Equal, text="A"),
            DiffChunk(kind=DiffChunk.Kind.Added, text=" sharp"),
            DiffChunk(kind=DiffChunk.Kind.Equal, text=" sword."),
        ]

    def test_deletion(self) -> None:
        """
        Tests that deleted words result in a removed chunk.
        """

        # when
        chunks: list[DiffChunk] = get_word_diff("A sharp sword.", "A sword.")

        # then
        assert chunks == [
            DiffChunk(kind=DiffChunk.Kind.Equal, text="A"),
            DiffChunk(kind=DiffChunk.Kind.Removed, text=" sharp"),
            DiffChunk(kind=DiffChunk.Kind.Equal, text=" sword."),
        ]

    def test_replacement(self) -> None:
        """
        Tests that replaced words result in a removed chunk followed by an added chunk.
        """

        # when
        chunks: list[DiffChunk] = get_word_diff(
            "Das ist ein Schwert.", "Das ist der Schwert."
        )

        # then
        assert chunks == [
            DiffChunk(kind=DiffChunk.Kind.Equal, text="Das ist "),
            DiffChunk(kind=DiffChunk.Kind.Removed, text="ein"),
            DiffChunk(kind=DiffChunk.Kind.Added, text="der"),
            DiffChunk(kind=DiffChunk.Kind.Equal, text=" Schwert."),
        ]

    def test_multiline_texts(self) -> None:
        """
        Tests that the chunks of multiline texts reconstruct both texts.
        """

        # given
        old: str = "First line.\nSecond line.\n\nThird line."
        new: str = "First line.\nChanged second line.\nThird line!"

        # when
        chunks: list[DiffChunk] = get_word_diff(old, new)

        # then
        assert (
            "".join(chunk.text for chunk in chunks if chunk.kind != DiffChunk.Kind.Added)
            == old
        )
        assert (
            "".join(
                chunk.text for chunk in chunks if chunk.kind != DiffChunk.Kind.Removed
            )
            == new
        )

    def test_text_from_empty(self) -> None:
        """
        Tests that a text compared to an empty text results in a single added chunk.
        """

        # when
        chunks: list[DiffChunk] = get_word_diff("", "New text")

        # then
        assert chunks == [DiffChunk(kind=DiffChunk.Kind.Added, text="New text")]
