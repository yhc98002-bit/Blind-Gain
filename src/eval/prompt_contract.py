from __future__ import annotations


ANSWER_FORMAT_CONTRACT = (
    "Give your final answer inside <answer> and </answer> tags. "
    "Keep the tagged span to the shortest answer that resolves the question."
)


def format_question(question: str) -> str:
    return f"{question.strip()}\n\n{ANSWER_FORMAT_CONTRACT}"
