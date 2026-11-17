"""
Copyright (c) Cutleast
"""

import re
from difflib import SequenceMatcher
from enum import Enum

from pydantic import BaseModel

DIFF_TOKEN_PATTERN: re.Pattern[str] = re.compile(r"\w+|\s+|[^\w\s]")
"""Pattern for the tokens (words, whitespace and single symbols) that are compared."""


class DiffChunk(BaseModel, frozen=True):
    """
    Represents a contiguous part of a text diff.
    """

    class Kind(Enum):
        """
        Kinds of diff chunks.
        """

        Equal = "equal"
        """The text is contained in both the old and the new text."""

        Removed = "removed"
        """The text is only contained in the old text."""

        Added = "added"
        """The text is only contained in the new text."""

    kind: Kind
    """The kind of this chunk."""

    text: str
    """The text of this chunk."""


def get_word_diff(old: str, new: str) -> list[DiffChunk]:
    """
    Calculates a word-level diff between two texts. Adjacent chunks of the same kind are
    merged and replaced parts result in a removed chunk followed by an added chunk.

    Args:
        old (str): The old text.
        new (str): The new text.

    Returns:
        list[DiffChunk]: The chunks of the diff in text order.
    """

    old_tokens: list[str] = DIFF_TOKEN_PATTERN.findall(old)
    new_tokens: list[str] = DIFF_TOKEN_PATTERN.findall(new)
    matcher: SequenceMatcher[str] = SequenceMatcher(
        None, old_tokens, new_tokens, autojunk=False
    )

    chunks: list[DiffChunk] = []
    for tag, old_start, old_end, new_start, new_end in matcher.get_opcodes():
        if tag == "equal":
            _append_chunk(
                chunks, DiffChunk.Kind.Equal, "".join(old_tokens[old_start:old_end])
            )
            continue

        if tag in ("delete", "replace"):
            _append_chunk(
                chunks, DiffChunk.Kind.Removed, "".join(old_tokens[old_start:old_end])
            )

        if tag in ("insert", "replace"):
            _append_chunk(
                chunks, DiffChunk.Kind.Added, "".join(new_tokens[new_start:new_end])
            )

    return chunks


def _append_chunk(chunks: list[DiffChunk], kind: DiffChunk.Kind, text: str) -> None:
    """
    Appends a chunk to a list of chunks or merges it into the last chunk if that one is
    of the same kind. Empty texts are ignored.

    Args:
        chunks (list[DiffChunk]): The list of chunks to extend.
        kind (DiffChunk.Kind): The kind of the chunk.
        text (str): The text of the chunk.
    """

    if not text:
        return

    if chunks and chunks[-1].kind == kind:
        chunks[-1] = DiffChunk(kind=kind, text=chunks[-1].text + text)
    else:
        chunks.append(DiffChunk(kind=kind, text=text))
