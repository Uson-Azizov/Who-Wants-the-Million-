from __future__ import annotations

import json
from pathlib import Path

from src.database import DatabaseClient
from src.models import Difficulty, Question


class QuestionRepository:
    def __init__(self, file_map: dict[str, Path], database: DatabaseClient) -> None:
        self.file_map = file_map
        self.database = database

    def load_all(self) -> dict[Difficulty, list[Question]]:
        file_questions: dict[Difficulty, list[Question]] = {
            Difficulty.EASY: [],
            Difficulty.MEDIUM: [],
            Difficulty.HARD: [],
        }

        for difficulty in Difficulty:
            path = self.file_map[difficulty.value]
            file_questions[difficulty] = self._load_file(path, difficulty)

        synced, message = self.database.sync_questions(file_questions)
        if not synced:
            raise RuntimeError(message)

        db_questions, message = self.database.load_questions()
        if not any(db_questions.values()):
            raise RuntimeError(message)

        return db_questions

    def _load_file(self, path: Path, difficulty: Difficulty) -> list[Question]:
        if not path.exists() or path.stat().st_size == 0:
            return []

        with path.open("r", encoding="utf-8") as file:
            raw = json.load(file)

        items = self._extract_items(raw, path.name)

        questions: list[Question] = []
        for index, item in enumerate(items, start=1):
            questions.append(self._parse_question(item, index, path.name, difficulty))

        return questions

    @staticmethod
    def _extract_items(raw: object, file_name: str) -> list[object]:
        if isinstance(raw, list):
            return raw
        if isinstance(raw, dict):
            quiz_items = raw.get("quiz")
            if isinstance(quiz_items, list):
                return quiz_items
        raise ValueError(f"{file_name}: root JSON value must be an array or object with `quiz` array")

    @staticmethod
    def _parse_question(
        item: object,
        index: int,
        file_name: str,
        difficulty: Difficulty,
    ) -> Question:
        if not isinstance(item, dict):
            raise ValueError(f"{file_name}[{index}]: item must be an object")

        text = item.get("question")
        options_raw = item.get("options")
        answer = item.get("answer")
        if answer is None:
            answer = item.get("correct_answer")

        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"{file_name}[{index}].question must be non-empty string")
        options = QuestionRepository._normalize_options(options_raw, file_name, index)
        answer_index = QuestionRepository._resolve_answer_index(
            answer, options_raw, options, file_name, index
        )

        return Question(text=text.strip(), options=options, correct_index=answer_index, difficulty=difficulty)

    @staticmethod
    def _normalize_options(options_raw: object, file_name: str, index: int) -> list[str]:
        if isinstance(options_raw, list):
            if len(options_raw) != 4 or not all(isinstance(o, str) for o in options_raw):
                raise ValueError(f"{file_name}[{index}].options must contain exactly 4 strings")
            return options_raw

        if isinstance(options_raw, dict):
            labels = ["A", "B", "C", "D"]
            if not all(label in options_raw and isinstance(options_raw[label], str) for label in labels):
                raise ValueError(f"{file_name}[{index}].options dict must contain A, B, C, D keys")
            return [options_raw[label] for label in labels]

        raise ValueError(f"{file_name}[{index}].options must be list or dict")

    @staticmethod
    def _resolve_answer_index(
        answer: object,
        options_raw: object,
        options: list[str],
        file_name: str,
        index: int,
    ) -> int:
        if isinstance(answer, int) and 0 <= answer <= 3:
            return answer

        if isinstance(answer, str):
            normalized = answer.strip()

            # Support letter answer when options are encoded as A/B/C/D.
            if isinstance(options_raw, dict):
                letter_order = ["A", "B", "C", "D"]
                if normalized.upper() in letter_order:
                    return letter_order.index(normalized.upper())

            for idx, option in enumerate(options):
                if option.strip() == normalized:
                    return idx

        raise ValueError(
            f"{file_name}[{index}].answer must be int 0..3, letter A..D, or match option text"
        )
