from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime

from src.models import Difficulty, Question


@dataclass(frozen=True)
class DatabaseHealth:
    connected: bool
    message: str


@dataclass(frozen=True)
class LeaderboardEntry:
    player_name: str
    difficulty: str
    score: int
    asked_questions: int
    is_win: bool
    created_at: str


class DatabaseClient:
    def __init__(self, database_path: str) -> None:
        self.database_path = database_path.strip()
        self.last_error = ""

    @property
    def enabled(self) -> bool:
        return bool(self.database_path)

    def initialize(self) -> DatabaseHealth:
        if not self.enabled:
            return DatabaseHealth(False, "SQLite отключен (SQLITE_DB_PATH не задан)")

        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS questions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        difficulty TEXT NOT NULL,
                        question_text TEXT NOT NULL,
                        options_json TEXT NOT NULL,
                        correct_index INTEGER NOT NULL,
                        UNIQUE(difficulty, question_text)
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS game_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        player_name TEXT NOT NULL,
                        difficulty TEXT NOT NULL,
                        score INTEGER NOT NULL,
                        asked_questions INTEGER NOT NULL,
                        is_win INTEGER NOT NULL,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            return DatabaseHealth(True, f"SQLite подключен: {self.database_path}")
        except Exception as exc:
            self.last_error = str(exc)
            return DatabaseHealth(False, f"SQLite недоступен: {exc}")

    def sync_questions(self, questions_by_difficulty: dict[Difficulty, list[Question]]) -> tuple[bool, str]:
        if not self.enabled:
            return False, "SQLite отключен (SQLITE_DB_PATH не задан)"

        try:
            with self._connect() as conn:
                conn.execute("DELETE FROM questions")
                rows = []
                for difficulty, questions in questions_by_difficulty.items():
                    for question in questions:
                        rows.append(
                            (
                                difficulty.value,
                                question.text,
                                json.dumps(question.options, ensure_ascii=False),
                                question.correct_index,
                            )
                        )
                conn.executemany(
                    """
                    INSERT INTO questions (
                        difficulty,
                        question_text,
                        options_json,
                        correct_index
                    ) VALUES (?, ?, ?, ?)
                    """,
                    rows,
                )
            return True, f"Вопросы загружены в SQLite: {len(rows)}"
        except Exception as exc:
            self.last_error = str(exc)
            return False, f"Не удалось загрузить вопросы в SQLite: {exc}"

    def load_questions(self) -> tuple[dict[Difficulty, list[Question]], str]:
        empty: dict[Difficulty, list[Question]] = {
            Difficulty.EASY: [],
            Difficulty.MEDIUM: [],
            Difficulty.HARD: [],
        }
        if not self.enabled:
            return empty, "SQLite отключен (SQLITE_DB_PATH не задан)"

        try:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT difficulty, question_text, options_json, correct_index
                    FROM questions
                    ORDER BY difficulty, id
                    """
                ).fetchall()

            questions = empty.copy()
            for difficulty_value, question_text, options_json, correct_index in rows:
                difficulty = Difficulty(str(difficulty_value))
                options = json.loads(str(options_json))
                questions[difficulty].append(
                    Question(
                        text=str(question_text),
                        options=[str(option) for option in options],
                        correct_index=int(correct_index),
                        difficulty=difficulty,
                    )
                )
            return questions, f"Вопросы загружены из SQLite: {len(rows)}"
        except Exception as exc:
            self.last_error = str(exc)
            return empty, f"Не удалось загрузить вопросы из SQLite: {exc}"

    def save_game_result(
        self,
        *,
        player_name: str,
        difficulty: str,
        score: int,
        asked_questions: int,
        is_win: bool,
    ) -> bool:
        if not self.enabled:
            return False

        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO game_results (
                        player_name,
                        difficulty,
                        score,
                        asked_questions,
                        is_win
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        player_name,
                        difficulty,
                        score,
                        asked_questions,
                        int(is_win),
                    )
                )
            return True
        except Exception as exc:
            self.last_error = str(exc)
            return False

    def get_leaderboard(self, limit: int = 25) -> tuple[list[LeaderboardEntry], str]:
        if not self.enabled:
            return [], "SQLite отключен (SQLITE_DB_PATH не задан)"

        safe_limit = max(1, min(200, int(limit)))

        try:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT
                        player_name,
                        difficulty,
                        score,
                        asked_questions,
                        is_win,
                        created_at
                    FROM game_results
                    ORDER BY score DESC, created_at ASC
                    LIMIT ?
                    """,
                    (safe_limit,),
                ).fetchall()

            entries = [self._map_leaderboard_row(row) for row in rows]
            return entries, "Рекорды загружены из SQLite"
        except Exception as exc:
            self.last_error = str(exc)
            return [], f"Не удалось загрузить рекорды: {exc}"

    @staticmethod
    def _map_leaderboard_row(row: tuple[object, ...]) -> LeaderboardEntry:
        player_name, difficulty, score, asked_questions, is_win, created_at = row
        date_text = (
            created_at.strftime("%Y-%m-%d %H:%M")
            if isinstance(created_at, datetime)
            else str(created_at)
        )
        return LeaderboardEntry(
            player_name=str(player_name),
            difficulty=str(difficulty),
            score=int(score),
            asked_questions=int(asked_questions),
            is_win=bool(is_win),
            created_at=date_text,
        )

    def _connect(self):
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        return conn
