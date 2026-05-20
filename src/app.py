from __future__ import annotations

import csv
import json
import tkinter as tk
from datetime import datetime

from src.config import (
    ADMIN_DEFAULT_CODE,
    ADMIN_DEFAULT_LOGIN,
    DATABASE_BACKEND,
    DATABASE_CONNECT_TIMEOUT,
    DATABASE_URL,
    EXPORTS_DIR,
    PLAYER_NAME,
    QUESTIONS_FILES,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SQLITE_DATABASE_PATH,
    START_FULLSCREEN,
    TITLE,
)
from src.database import DatabaseClient
from src.models import Difficulty
from src.repository import QuestionRepository
from src.screens.base import Screen
from src.screens.admin_login import AdminLoginScreen
from src.screens.admin_panel import AdminPanelScreen
from src.screens.game import GameScreen
from src.screens.leaderboard import LeaderboardScreen
from src.screens.menu import MenuScreen
from src.screens.settings import SettingsScreen
from src.services import GameService
from src.ui.theme import Theme


class MillionaireGameApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title(TITLE)

        self.theme = Theme()
        self.root.configure(bg=self.theme.window_bg)

        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self.fullscreen = START_FULLSCREEN

        if self.fullscreen:
            self.root.attributes("-fullscreen", True)
        else:
            self.root.geometry(f"{SCREEN_WIDTH}x{SCREEN_HEIGHT}")

        self.root.minsize(980, 620)

        self.status_text_var = tk.StringVar(value="Главное меню")
        self.player_name = PLAYER_NAME
        self.database = DatabaseClient(
            DATABASE_URL,
            sqlite_path=SQLITE_DATABASE_PATH,
            backend=DATABASE_BACKEND,
            connect_timeout=DATABASE_CONNECT_TIMEOUT,
        )
        db_health = self.database.initialize()
        if db_health.connected:
            self.database.ensure_admin_user(ADMIN_DEFAULT_LOGIN, ADMIN_DEFAULT_CODE)
        self.db_status_var = tk.StringVar(value=db_health.message)
        self.sfx_level_var = tk.DoubleVar(value=0.40)
        self.music_level_var = tk.DoubleVar(value=0.25)
        self.vibration_enabled_var = tk.BooleanVar(value=False)

        repository = QuestionRepository(QUESTIONS_FILES)
        file_questions = repository.load_all()
        self.questions = file_questions
        if db_health.connected:
            summary, _ = self.database.get_questions_summary()
            if summary is None or summary.total == 0:
                self.database.replace_questions(file_questions)
            db_questions, db_message = self.database.get_game_questions()
            if db_questions is not None and any(db_questions.values()):
                self.questions = db_questions
                self.db_status_var.set(db_message)
        self.game_service = GameService(self.questions)

        self.current_screen: Screen | None = None

        self.root.bind("<F11>", self._on_f11)
        self.root.bind("<Escape>", self._on_escape)
        self.root.bind("<Configure>", self._on_configure)

        self.open_menu()

    def _switch_screen(self, screen: Screen) -> None:
        if self.current_screen is not None:
            self.current_screen.destroy()

        self.current_screen = screen
        self.current_screen.show()
        self.current_screen.on_resize(self.width, self.height)

    def _on_f11(self, _event: tk.Event) -> str:
        self.toggle_fullscreen()
        return "break"

    def _on_escape(self, _event: tk.Event) -> str:
        if self.current_screen is not None:
            self.current_screen.on_escape()
        return "break"

    def _on_configure(self, event: tk.Event) -> None:
        if event.widget is not self.root:
            return
        if event.width <= 1 or event.height <= 1:
            return

        self.width = event.width
        self.height = event.height

        if self.current_screen is not None:
            self.current_screen.on_resize(self.width, self.height)

    def toggle_fullscreen(self) -> None:
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)

    def open_menu(self) -> None:
        self.status_text_var.set("Главное меню")
        self._switch_screen(MenuScreen(self))

    def open_leaderboard(self) -> None:
        self.status_text_var.set("Рекорды")
        self._switch_screen(LeaderboardScreen(self))

    def open_settings(self) -> None:
        self.status_text_var.set("Настройки")
        self._switch_screen(SettingsScreen(self))

    def open_admin_login(self) -> None:
        self.status_text_var.set("Вход в админку")
        self._switch_screen(AdminLoginScreen(self))

    def open_admin_panel(self) -> None:
        self.status_text_var.set("Админка")
        self._switch_screen(AdminPanelScreen(self))

    def start_game(self, difficulty: Difficulty | None = None) -> None:
        missing = [diff.value for diff in Difficulty if not self.questions[diff]]
        if missing:
            self.status_text_var.set(f"Нет вопросов: {', '.join(missing)}")
            self.open_menu()
            return

        self.game_service.reset()
        self.status_text_var.set("Игра запущена")
        self._switch_screen(GameScreen(self))

    def quit(self) -> None:
        self.root.destroy()

    def check_database(self) -> None:
        health = self.database.initialize()
        self.db_status_var.set(health.message)
        self.status_text_var.set(health.message if health.connected else "Ошибка подключения к базе данных")

    def get_leaderboard(self, limit: int = 25):
        entries, message = self.database.get_leaderboard(limit=limit)
        self.db_status_var.set(message)
        return entries, message

    def save_game_result(self, difficulty: Difficulty | str, is_win: bool) -> None:
        difficulty_value = difficulty.value if isinstance(difficulty, Difficulty) else str(difficulty)
        saved = self.database.save_game_result(
            player_name=self.player_name,
            difficulty=difficulty_value,
            score=self.game_service.session.score,
            asked_questions=self.game_service.session.asked,
            is_win=is_win,
        )

        if saved:
            self.db_status_var.set("Результат игры сохранен в базе данных")
            return

        if self.database.enabled:
            message = self.database.last_error or "Не удалось сохранить результат в базе данных"
            self.db_status_var.set(message)

    def sync_questions_to_database(self) -> str:
        summary, message = self.database.replace_questions(self.questions)
        self.db_status_var.set(message)
        self.status_text_var.set(message if summary is not None else "Импорт вопросов не выполнен")
        return message

    def verify_admin_login(self, login: str, code: str) -> tuple[bool, str]:
        return self.database.verify_admin_user(login, code)

    def get_admin_questions(self):
        return self.database.get_admin_questions()

    def add_admin_question(
        self,
        *,
        difficulty: str,
        question_text: str,
        options: list[str],
        correct_index: int,
    ) -> tuple[bool, str]:
        success, message = self.database.add_question(
            difficulty=difficulty,
            question_text=question_text,
            options=options,
            correct_index=correct_index,
        )
        if success:
            db_questions, _ = self.database.get_game_questions()
            if db_questions is not None:
                self.questions = db_questions
                self.game_service.questions = db_questions
        self.db_status_var.set(message)
        self.status_text_var.set(message)
        return success, message

    def export_game_data(self, format_name: str) -> tuple[bool, str]:
        payload, message = self.database.get_export_payload()
        if payload is None:
            self.db_status_var.set(message)
            return False, message

        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        format_key = format_name.strip().lower()

        try:
            if format_key == "json":
                target = EXPORTS_DIR / f"mindset_export_{timestamp}.json"
                target.write_text(
                    json.dumps(payload, ensure_ascii=False, indent=2, default=str),
                    encoding="utf-8",
                )
                result_message = f"Экспортировано в {target.name}"
            elif format_key == "txt":
                target = EXPORTS_DIR / f"mindset_export_{timestamp}.txt"
                text = self._build_text_export(payload)
                target.write_text(text, encoding="utf-8")
                result_message = f"Экспортировано в {target.name}"
            elif format_key == "csv":
                questions_file = EXPORTS_DIR / f"questions_{timestamp}.csv"
                results_file = EXPORTS_DIR / f"game_results_{timestamp}.csv"
                self._write_csv(questions_file, payload.get("questions", []))
                self._write_csv(results_file, payload.get("game_results", []))
                result_message = f"Экспортировано в {questions_file.name} и {results_file.name}"
            else:
                return False, "Неизвестный формат экспорта"
        except Exception as exc:
            self.db_status_var.set(str(exc))
            return False, f"Ошибка экспорта: {exc}"

        self.db_status_var.set(result_message)
        self.status_text_var.set(result_message)
        return True, result_message

    @staticmethod
    def _write_csv(path, rows) -> None:
        rows = list(rows)
        columns = list(rows[0].keys()) if rows else ["empty"]
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()
            if rows:
                writer.writerows(rows)

    @staticmethod
    def _build_text_export(payload: dict[str, object]) -> str:
        lines = [f"Backend: {payload.get('backend', '')}", ""]
        questions = payload.get("questions", [])
        results = payload.get("game_results", [])

        lines.append("QUESTIONS")
        for item in questions if isinstance(questions, list) else []:
            lines.append(f"- [{item.get('difficulty')}] {item.get('question_text')}")
            lines.append(f"  A: {item.get('option_a')}")
            lines.append(f"  B: {item.get('option_b')}")
            lines.append(f"  C: {item.get('option_c')}")
            lines.append(f"  D: {item.get('option_d')}")
            lines.append(f"  Correct index: {item.get('correct_index')}")
            lines.append("")

        lines.append("GAME RESULTS")
        for item in results if isinstance(results, list) else []:
            lines.append(
                f"- {item.get('player_name')} | {item.get('difficulty')} | score={item.get('score')} | "
                f"asked={item.get('asked_questions')} | win={item.get('is_win')} | {item.get('created_at')}"
            )

        return "\n".join(lines)

    def run(self) -> None:
        self.root.mainloop()
