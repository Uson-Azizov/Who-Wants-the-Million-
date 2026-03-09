from __future__ import annotations

import tkinter as tk

from src.config import (
    DATABASE_CONNECT_TIMEOUT,
    DATABASE_URL,
    PLAYER_NAME,
    QUESTIONS_FILES,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    START_FULLSCREEN,
    TITLE,
)
from src.database import DatabaseClient
from src.models import Difficulty
from src.repository import QuestionRepository
from src.screens.base import Screen
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
        self.database = DatabaseClient(DATABASE_URL, connect_timeout=DATABASE_CONNECT_TIMEOUT)
        db_health = self.database.initialize()
        self.db_status_var = tk.StringVar(value=db_health.message)

        repository = QuestionRepository(QUESTIONS_FILES)
        self.questions = repository.load_all()
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
        self.status_text_var.set(health.message if health.connected else "Ошибка подключения PostgreSQL")

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
            self.db_status_var.set("Результат игры сохранен в PostgreSQL")
            return

        if self.database.enabled:
            message = self.database.last_error or "Не удалось сохранить результат в PostgreSQL"
            self.db_status_var.set(message)

    def run(self) -> None:
        self.root.mainloop()
