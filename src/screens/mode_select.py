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
            darken_alpha=72,
            drift_x=1,
            drift_y=1,
            show_scanline=False,
        )

        self.title_id = self.canvas.create_text(
            0,
            0,
            text="Выберите сложность",
            fill="#f2f8ff",
            font=("Arial", 42, "bold"),
            anchor="n",
        )
        self.subtitle_id = self.canvas.create_text(
            0,
            0,
            text="Сложность влияет на набор вопросов",
            fill="#9fd3ff",
            font=("Arial", 16),
            anchor="n",
        )

        self.buttons_frame = tk.Frame(self.canvas, bg="#060d33")
        self.buttons_window = self.canvas.create_window(0, 0, window=self.buttons_frame, anchor="n")

        self._build_buttons()
        self.background.start()
        self.on_resize(self.app.width, self.app.height)

    @staticmethod
    def _clamp(value: int, minimum: int, maximum: int) -> int:
        return max(minimum, min(maximum, value))

    def _build_buttons(self) -> None:
        style = dict(
            theme=self.app.theme,
            font=("Arial", 18, "bold"),
            width=30,
            height=62,
            radius=19,
            bg_color="#070742",
            hover_color="#111b69",
            border_color="#dceaff",
            text_color="#34d5ff",
        )

        GlassButton(
            self.buttons_frame,
            text="Легкие вопросы",
            command=lambda: self.app.start_game(Difficulty.EASY),
            **style,
        ).pack(fill="x", pady=7)

        GlassButton(
            self.buttons_frame,
            text="Нормальные вопросы",
            command=lambda: self.app.start_game(Difficulty.MEDIUM),
            **style,
        ).pack(fill="x", pady=7)

        GlassButton(
            self.buttons_frame,
            text="Сложные вопросы",
            command=lambda: self.app.start_game(Difficulty.HARD),
            **style,
        ).pack(fill="x", pady=7)

        GlassButton(
            self.buttons_frame,
            text="Назад",
            command=self.app.open_menu,
            theme=self.app.theme,
            font=("Arial", 14, "bold"),
            width=16,
            height=42,
            radius=14,
            bg_color="#091645",
            hover_color="#12306f",
            border_color="#89bfff",
            text_color="#9ee8ff",
        ).pack(pady=(14, 0))

    def on_resize(self, width: int, height: int) -> None:
        scale = min(width / 1280, height / 720)
        center_x = width // 2
        self.canvas.itemconfigure(self.title_id, font=("Arial", self._clamp(int(42 * scale), 24, 42), "bold"))
        self.canvas.itemconfigure(self.subtitle_id, font=("Arial", self._clamp(int(16 * scale), 11, 16)))
        self.canvas.coords(self.title_id, center_x, int(height * 0.11))
        self.canvas.coords(self.subtitle_id, center_x, int(height * 0.19))
        self.canvas.coords(self.buttons_window, center_x, int(height * 0.31))
        self.canvas.itemconfigure(self.buttons_window, width=self._clamp(int(width * 0.40), 320, 560))

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
