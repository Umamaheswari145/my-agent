from collections.abc import Sequence
import math
import re


_WORD_PATTERN = re.compile(r"[a-z0-9]+")


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def tokenize(text: str) -> set[str]:
    return set(_WORD_PATTERN.findall(text.lower()))


def keyword_score(query: str, text: str) -> float:
    query_tokens = tokenize(query)
    text_tokens = tokenize(text)
    if not query_tokens or not text_tokens:
        return 0.0
    overlap = query_tokens & text_tokens
    return len(overlap) / math.sqrt(len(query_tokens) * len(text_tokens))
