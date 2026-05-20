from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.models import Difficulty, Question

try:
    import psycopg
except Exception:  # pragma: no cover - optional dependency at runtime
    psycopg = None

try:
    import psycopg2
except Exception:  # pragma: no cover - optional dependency at runtime
    psycopg2 = None


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


@dataclass(frozen=True)
class QuestionImportSummary:
    total: int
    by_difficulty: dict[str, int]


@dataclass(frozen=True)
class AdminQuestionEntry:
    id: int
    difficulty: str
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_index: int
    imported_at: str


class DatabaseClient:
    def __init__(
        self,
        database_url: str = "",
        *,
        sqlite_path: str | Path | None = None,
        backend: str = "sqlite",
        connect_timeout: int = 8,
    ) -> None:
        self.database_url = database_url.strip()
        self.sqlite_path = Path(sqlite_path) if sqlite_path else None
        self.backend = backend.strip().lower() or "sqlite"
        self.connect_timeout = connect_timeout
        self.last_error = ""

    @property
    def backend_name(self) -> str:
        return "SQLite" if self.backend == "sqlite" else "PostgreSQL"

    @property
    def enabled(self) -> bool:
        if self.backend == "sqlite":
            return self.sqlite_path is not None
        return bool(self.database_url)

    @property
    def available(self) -> bool:
        if self.backend == "sqlite":
            return True
        return psycopg is not None or psycopg2 is not None

    def initialize(self) -> DatabaseHealth:
        if not self.enabled:
            return DatabaseHealth(False, f"{self.backend_name} отключен")
        if not self.available:
            return DatabaseHealth(False, f"Драйвер {self.backend_name} не установлен")

        try:
            conn = self._connect()
            try:
                cur = conn.cursor()
                if self.backend == "sqlite":
                    cur.execute(
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
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS questions (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            difficulty TEXT NOT NULL,
                            question_text TEXT NOT NULL,
                            option_a TEXT NOT NULL,
                            option_b TEXT NOT NULL,
                            option_c TEXT NOT NULL,
                            option_d TEXT NOT NULL,
                            correct_index INTEGER NOT NULL CHECK (correct_index BETWEEN 0 AND 3),
                            imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                        )
                        """
                    )
                    cur.execute(
                        """
                        CREATE UNIQUE INDEX IF NOT EXISTS questions_difficulty_text_idx
                        ON questions (difficulty, question_text)
                        """
                    )
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS admin_users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            login TEXT NOT NULL UNIQUE,
                            password_hash TEXT NOT NULL,
                            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                        )
                        """
                    )
                else:
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS game_results (
                            id BIGSERIAL PRIMARY KEY,
                            player_name TEXT NOT NULL,
                            difficulty TEXT NOT NULL,
                            score INTEGER NOT NULL,
                            asked_questions INTEGER NOT NULL,
                            is_win BOOLEAN NOT NULL,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                        )
                        """
                    )
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS questions (
                            id BIGSERIAL PRIMARY KEY,
                            difficulty TEXT NOT NULL,
                            question_text TEXT NOT NULL,
                            option_a TEXT NOT NULL,
                            option_b TEXT NOT NULL,
                            option_c TEXT NOT NULL,
                            option_d TEXT NOT NULL,
                            correct_index INTEGER NOT NULL CHECK (correct_index BETWEEN 0 AND 3),
                            imported_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                        )
                        """
                    )
                    cur.execute(
                        """
                        CREATE UNIQUE INDEX IF NOT EXISTS questions_difficulty_text_idx
                        ON questions (difficulty, question_text)
                        """
                    )
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS admin_users (
                            id BIGSERIAL PRIMARY KEY,
                            login TEXT NOT NULL UNIQUE,
                            password_hash TEXT NOT NULL,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                        )
                        """
                    )
                conn.commit()
            finally:
                conn.close()
            return DatabaseHealth(True, f"{self.backend_name} подключен")
        except Exception as exc:
            self.last_error = str(exc)
            return DatabaseHealth(False, f"{self.backend_name} недоступен: {exc}")

    def ensure_admin_user(self, login: str, password: str) -> tuple[bool, str]:
        if not self.enabled:
            return False, f"{self.backend_name} отключен"
        if not self.available:
            return False, f"Драйвер {self.backend_name} не установлен"

        password_hash = self._hash_password(password)
        try:
            conn = self._connect()
            try:
                cur = conn.cursor()
                if self.backend == "sqlite":
                    cur.execute("SELECT login FROM admin_users WHERE login = ?", (login,))
                    existing = cur.fetchone()
                    if existing is None:
                        cur.execute(
                            "INSERT INTO admin_users (login, password_hash) VALUES (?, ?)",
                            (login, password_hash),
                        )
                    else:
                        cur.execute(
                            "UPDATE admin_users SET password_hash = ? WHERE login = ?",
                            (password_hash, login),
                        )
                else:
                    cur.execute("SELECT login FROM admin_users WHERE login = %s", (login,))
                    existing = cur.fetchone()
                    if existing is None:
                        cur.execute(
                            "INSERT INTO admin_users (login, password_hash) VALUES (%s, %s)",
                            (login, password_hash),
                        )
                    else:
                        cur.execute(
                            "UPDATE admin_users SET password_hash = %s WHERE login = %s",
                            (password_hash, login),
                        )
                conn.commit()
            finally:
                conn.close()
            return True, "Учётка админа готова"
        except Exception as exc:
            self.last_error = str(exc)
            return False, f"Не удалось подготовить учётку админа: {exc}"

    def verify_admin_user(self, login: str, password: str) -> tuple[bool, str]:
        if not self.enabled:
            return False, f"{self.backend_name} отключен"
        if not self.available:
            return False, f"Драйвер {self.backend_name} не установлен"

        password_hash = self._hash_password(password)
        try:
            conn = self._connect()
            try:
                cur = conn.cursor()
                if self.backend == "sqlite":
                    cur.execute(
                        "SELECT 1 FROM admin_users WHERE login = ? AND password_hash = ?",
                        (login, password_hash),
                    )
                else:
                    cur.execute(
                        "SELECT 1 FROM admin_users WHERE login = %s AND password_hash = %s",
                        (login, password_hash),
                    )
                found = cur.fetchone() is not None
            finally:
                conn.close()
            if found:
                return True, "Вход выполнен"
            return False, "Неверный login или admins code"
        except Exception as exc:
            self.last_error = str(exc)
            return False, f"Не удалось проверить логин админа: {exc}"

    def get_export_payload(self) -> tuple[dict[str, object] | None, str]:
        if not self.enabled:
            return None, f"{self.backend_name} отключен"
        if not self.available:
            return None, f"Драйвер {self.backend_name} не установлен"

        try:
            conn = self._connect()
            try:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT difficulty, question_text, option_a, option_b, option_c, option_d, correct_index, imported_at
                    FROM questions
                    ORDER BY difficulty, id
                    """
                )
                questions = self._rows_to_dicts(cur)

                cur.execute(
                    """
                    SELECT player_name, difficulty, score, asked_questions, is_win, created_at
                    FROM game_results
                    ORDER BY created_at DESC, id DESC
                    """
                )
                results = self._rows_to_dicts(cur)
            finally:
                conn.close()

            payload = {
                "backend": self.backend_name,
                "questions": questions,
                "game_results": results,
            }
            return payload, "Данные подготовлены для экспорта"
        except Exception as exc:
            self.last_error = str(exc)
            return None, f"Не удалось подготовить экспорт: {exc}"

    def get_game_questions(self) -> tuple[dict[Difficulty, list[Question]] | None, str]:
        entries, message = self.get_admin_questions()
        if entries is None:
            return None, message

        grouped: dict[Difficulty, list[Question]] = {
            Difficulty.EASY: [],
            Difficulty.MEDIUM: [],
            Difficulty.HARD: [],
        }
        mapping = {
            "easy": Difficulty.EASY,
            "medium": Difficulty.MEDIUM,
            "hard": Difficulty.HARD,
        }
        for entry in entries:
            difficulty = mapping.get(entry.difficulty)
            if difficulty is None:
                continue
            grouped[difficulty].append(
                Question(
                    text=entry.question_text,
                    options=[entry.option_a, entry.option_b, entry.option_c, entry.option_d],
                    correct_index=entry.correct_index,
                    difficulty=difficulty,
                )
            )
        return grouped, "Вопросы загружены из базы"

    def get_admin_questions(self) -> tuple[list[AdminQuestionEntry] | None, str]:
        if not self.enabled:
            return None, f"{self.backend_name} отключен"
        if not self.available:
            return None, f"Драйвер {self.backend_name} не установлен"

        try:
            conn = self._connect()
            try:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT id, difficulty, question_text, option_a, option_b, option_c, option_d, correct_index, imported_at
                    FROM questions
                    ORDER BY difficulty, id
                    """
                )
                rows = cur.fetchall()
            finally:
                conn.close()

            entries = [
                AdminQuestionEntry(
                    id=int(row[0]),
                    difficulty=str(row[1]),
                    question_text=str(row[2]),
                    option_a=str(row[3]),
                    option_b=str(row[4]),
                    option_c=str(row[5]),
                    option_d=str(row[6]),
                    correct_index=int(row[7]),
                    imported_at=str(row[8]),
                )
                for row in rows
            ]
            return entries, "Список вопросов загружен"
        except Exception as exc:
            self.last_error = str(exc)
            return None, f"Не удалось загрузить вопросы: {exc}"

    def add_question(
        self,
        *,
        difficulty: str,
        question_text: str,
        options: list[str],
        correct_index: int,
    ) -> tuple[bool, str]:
        if not self.enabled:
            return False, f"{self.backend_name} отключен"
        if not self.available:
            return False, f"Драйвер {self.backend_name} не установлен"
        if len(options) != 4:
            return False, "Нужно ровно 4 варианта ответа"

        normalized_difficulty = difficulty.strip().lower()
        if normalized_difficulty not in {"easy", "medium", "hard"}:
            return False, "Неизвестная сложность"

        try:
            conn = self._connect()
            try:
                cur = conn.cursor()
                if self.backend == "sqlite":
                    cur.execute(
                        """
                        INSERT INTO questions (
                            difficulty,
                            question_text,
                            option_a,
                            option_b,
                            option_c,
                            option_d,
                            correct_index
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            normalized_difficulty,
                            question_text,
                            options[0],
                            options[1],
                            options[2],
                            options[3],
                            correct_index,
                        ),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO questions (
                            difficulty,
                            question_text,
                            option_a,
                            option_b,
                            option_c,
                            option_d,
                            correct_index
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            normalized_difficulty,
                            question_text,
                            options[0],
                            options[1],
                            options[2],
                            options[3],
                            correct_index,
                        ),
                    )
                conn.commit()
            finally:
                conn.close()
            return True, "Вопрос добавлен"
        except Exception as exc:
            self.last_error = str(exc)
            return False, f"Не удалось добавить вопрос: {exc}"

    def save_game_result(
        self,
        *,
        player_name: str,
        difficulty: str,
        score: int,
        asked_questions: int,
        is_win: bool,
    ) -> bool:
        if not self.enabled or not self.available:
            return False

        try:
            conn = self._connect()
            try:
                cur = conn.cursor()
                if self.backend == "sqlite":
                    cur.execute(
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
                            1 if is_win else 0,
                        ),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO game_results (
                            player_name,
                            difficulty,
                            score,
                            asked_questions,
                            is_win
                        ) VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            player_name,
                            difficulty,
                            score,
                            asked_questions,
                            is_win,
                        ),
                    )
                conn.commit()
                return True
            finally:
                conn.close()
        except Exception as exc:
            self.last_error = str(exc)
            return False

    def get_leaderboard(self, limit: int = 25) -> tuple[list[LeaderboardEntry], str]:
        if not self.enabled:
            return [], f"{self.backend_name} отключен"
        if not self.available:
            return [], f"Драйвер {self.backend_name} не установлен"

        safe_limit = max(1, min(200, int(limit)))

        try:
            conn = self._connect()
            try:
                cur = conn.cursor()
                if self.backend == "sqlite":
                    cur.execute(
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
                    )
                else:
                    cur.execute(
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
                        LIMIT %s
                        """,
                        (safe_limit,),
                    )
                rows = cur.fetchall()
            finally:
                conn.close()

            entries = [self._map_leaderboard_row(row) for row in rows]
            return entries, f"Рекорды загружены из {self.backend_name}"
        except Exception as exc:
            self.last_error = str(exc)
            return [], f"Не удалось загрузить рекорды: {exc}"

    def replace_questions(
        self,
        questions_by_difficulty: dict[Difficulty, list[Question]] | dict[str, list[Question]],
    ) -> tuple[QuestionImportSummary | None, str]:
        if not self.enabled:
            return None, f"{self.backend_name} отключен"
        if not self.available:
            return None, f"Драйвер {self.backend_name} не установлен"

        rows: list[tuple[str, str, str, str, str, str, int]] = []
        counts: dict[str, int] = {}
        for difficulty_key, questions in questions_by_difficulty.items():
            difficulty = difficulty_key.value if isinstance(difficulty_key, Difficulty) else str(difficulty_key)
            counts[difficulty] = len(questions)
            for question in questions:
                rows.append(
                    (
                        difficulty,
                        question.text,
                        question.options[0],
                        question.options[1],
                        question.options[2],
                        question.options[3],
                        question.correct_index,
                    )
                )

        try:
            conn = self._connect()
            try:
                cur = conn.cursor()
                cur.execute("DELETE FROM questions")
                if self.backend == "sqlite":
                    cur.executemany(
                        """
                        INSERT INTO questions (
                            difficulty,
                            question_text,
                            option_a,
                            option_b,
                            option_c,
                            option_d,
                            correct_index
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        rows,
                    )
                else:
                    cur.executemany(
                        """
                        INSERT INTO questions (
                            difficulty,
                            question_text,
                            option_a,
                            option_b,
                            option_c,
                            option_d,
                            correct_index
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        rows,
                    )
                conn.commit()
            finally:
                conn.close()

            summary = QuestionImportSummary(total=len(rows), by_difficulty=counts)
            details = ", ".join(f"{name}: {count}" for name, count in sorted(counts.items()))
            return summary, f"Импортировано {len(rows)} вопросов в {self.backend_name} ({details})"
        except Exception as exc:
            self.last_error = str(exc)
            return None, f"Не удалось импортировать вопросы: {exc}"

    def get_questions_summary(self) -> tuple[QuestionImportSummary | None, str]:
        if not self.enabled:
            return None, f"{self.backend_name} отключен"
        if not self.available:
            return None, f"Драйвер {self.backend_name} не установлен"

        try:
            conn = self._connect()
            try:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT difficulty, COUNT(*)
                    FROM questions
                    GROUP BY difficulty
                    ORDER BY difficulty
                    """
                )
                rows = cur.fetchall()
            finally:
                conn.close()

            counts = {str(difficulty): int(count) for difficulty, count in rows}
            total = sum(counts.values())
            return QuestionImportSummary(total=total, by_difficulty=counts), "Вопросы загружены"
        except Exception as exc:
            self.last_error = str(exc)
            return None, f"Не удалось получить список вопросов: {exc}"

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

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    @staticmethod
    def _rows_to_dicts(cursor) -> list[dict[str, object]]:
        columns = [column[0] for column in cursor.description or []]
        rows = cursor.fetchall()
        return [dict(zip(columns, row, strict=False)) for row in rows]

    def _connect(self):
        if self.backend == "sqlite":
            if self.sqlite_path is None:
                raise RuntimeError("SQLite path is not configured")
            conn = sqlite3.connect(self.sqlite_path)
            return conn

        if psycopg is not None:
            return psycopg.connect(
                self.database_url,
                connect_timeout=self.connect_timeout,
                sslmode="require",
                autocommit=False,
            )

        if psycopg2 is not None:
            conn = psycopg2.connect(
                self.database_url,
                connect_timeout=self.connect_timeout,
                sslmode="require",
            )
            conn.autocommit = False
            return conn

        raise RuntimeError("No supported SQL driver is installed")
