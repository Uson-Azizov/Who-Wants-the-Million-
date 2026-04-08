from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Difficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass(frozen=True)
class Question:
    text: str
    options: list[str]
    correct_index: int
    difficulty: Difficulty


@dataclass
class GameSession:
    score: int = 0
    asked: int = 0
    current_question: Question | None = None
    completed: bool = False
    used_questions: set[tuple[str, str]] = field(default_factory=set)
