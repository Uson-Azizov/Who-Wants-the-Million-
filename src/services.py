from __future__ import annotations

import random

from src.models import Difficulty, GameSession, Question


class GameService:
    def __init__(self, questions: dict[Difficulty, list[Question]]) -> None:
        self.questions = questions
        self.session = GameSession()

    def reset(self) -> None:
        self.session = GameSession()

    def get_next_question(self, difficulty: Difficulty) -> Question | None:
        pool = self.questions.get(difficulty, [])
        available = [q for q in pool if (q.text, q.difficulty.value) not in self.session.used_questions]

        if not available:
            return None

        question = random.choice(available)
        self.session.current_question = question
        self.session.asked += 1
        self.session.used_questions.add((question.text, question.difficulty.value))
        return question

    def submit_answer(self, selected_index: int) -> bool:
        current = self.session.current_question
        if current is None:
            return False

        is_correct = selected_index == current.correct_index
        if is_correct:
            self.session.score += 1
        else:
            self.session.completed = True

        return is_correct
