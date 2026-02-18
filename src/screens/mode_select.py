from __future__ import annotations

import tkinter as tk

from src.config import MENU_BACKGROUND_IMAGE_PATH
from src.models import Difficulty
from src.screens.base import Screen
from src.ui.animated_background import AnimatedBackground
from src.ui.components import GlassButton


class ModeSelectScreen(Screen):
    def __init__(self, app: "ModeSelectApp") -> None:
        super().__init__(app)

        self.canvas = tk.Canvas(self.container, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)

        self.background = AnimatedBackground(
            self.canvas,
            MENU_BACKGROUND_IMAGE_PATH,
            darken_alpha=120,
            drift_x=2,
            drift_y=1,
            show_scanline=True,
        )

        self.panel = tk.Frame(
            self.canvas,
            bg=self.app.theme.panel_bg,
            highlightthickness=2,
            highlightbackground=self.app.theme.panel_border,
            padx=32,
            pady=24,
        )
        self.panel_window = self.canvas.create_window(0, 0, window=self.panel, anchor="nw")

        self._build_content()
        self.background.start()
        self.on_resize(self.app.width, self.app.height)

    def _build_content(self) -> None:
        tk.Label(
            self.panel,
            text="РЕЖИМ ИГРЫ",
            bg=self.app.theme.panel_bg,
            fg=self.app.theme.text_primary,
            font=("Arial", 34, "bold"),
        ).pack(pady=(4, 6))

        tk.Label(
            self.panel,
            text="Выбери сложность перед стартом",
            bg=self.app.theme.panel_bg,
            fg=self.app.theme.text_secondary,
            font=("Arial", 14),
        ).pack(pady=(0, 18))

        buttons_holder = tk.Frame(self.panel, bg=self.app.theme.panel_bg)
        buttons_holder.pack(fill="x", pady=(4, 10))

        for text, difficulty in [
            ("Легкие вопросы", Difficulty.EASY),
            ("Нормальные вопросы", Difficulty.MEDIUM),
            ("Сложные вопросы", Difficulty.HARD),
        ]:
            GlassButton(
                buttons_holder,
                text=text,
                command=lambda d=difficulty: self.app.start_game(d),
                theme=self.app.theme,
                font=("Arial", 15, "bold"),
                width=30,
            ).pack(fill="x", pady=7)

        GlassButton(
            buttons_holder,
            text="Назад",
            command=self.app.open_menu,
            theme=self.app.theme,
            font=("Arial", 14, "bold"),
            width=30,
        ).pack(fill="x", pady=(12, 4))

        tk.Label(
            self.panel,
            textvariable=self.app.status_text_var,
            bg=self.app.theme.panel_bg,
            fg=self.app.theme.text_secondary,
            font=("Arial", 11),
        ).pack(pady=(10, 0))

    def on_resize(self, width: int, height: int) -> None:
        panel_width = int(width * 0.56)
        panel_height = int(height * 0.70)
        panel_x = (width - panel_width) // 2
        panel_y = int(height * 0.14)
        self.canvas.coords(self.panel_window, panel_x, panel_y)
        self.canvas.itemconfigure(self.panel_window, width=panel_width, height=panel_height)

    def on_escape(self) -> None:
        self.app.open_menu()

    def on_destroy(self) -> None:
        self.background.stop()


class ModeSelectApp:
    theme: object
    width: int
    height: int
    status_text_var: tk.StringVar

    def start_game(self, difficulty: Difficulty) -> None:
        raise NotImplementedError

    def open_menu(self) -> None:
        raise NotImplementedError
