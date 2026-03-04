from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

try:
    import psycopg
except Exception:  # pragma: no cover - optional dependency at runtime
    psycopg = None


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
    def __init__(self, database_url: str, connect_timeout: int = 8) -> None:
        self.database_url = database_url.strip()
        self.connect_timeout = connect_timeout
        self.last_error = ""

    @property
    def enabled(self) -> bool:
        return bool(self.database_url)

    @property
    def available(self) -> bool:
        return psycopg is not None

    def initialize(self) -> DatabaseHealth:
        if not self.enabled:
            return DatabaseHealth(False, "PostgreSQL отключен (DATABASE_URL не задан)")

        if not self.available:
            return DatabaseHealth(False, "PostgreSQL драйвер не установлен (psycopg)")

        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
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
            return DatabaseHealth(True, "PostgreSQL подключен")
        except Exception as exc:
            self.last_error = str(exc)
            return DatabaseHealth(False, f"PostgreSQL недоступен: {exc}")

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
            with self._connect() as conn:
                with conn.cursor() as cur:
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
            return True
        except Exception as exc:
            self.last_error = str(exc)
            return False

    def get_leaderboard(self, limit: int = 25) -> tuple[list[LeaderboardEntry], str]:
        if not self.enabled:
            return [], "PostgreSQL отключен (DATABASE_URL не задан)"
        if not self.available:
            return [], "PostgreSQL драйвер не установлен (psycopg)"

        safe_limit = max(1, min(200, int(limit)))

        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
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

            entries = [self._map_leaderboard_row(row) for row in rows]
            return entries, "Рекорды загружены из PostgreSQL"
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
        if psycopg is None:
            raise RuntimeError("psycopg is not installed")
        return psycopg.connect(
            self.database_url,
            connect_timeout=self.connect_timeout,
            sslmode="require",
            autocommit=True,
        )
