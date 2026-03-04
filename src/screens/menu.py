from __future__ import annotations

import tkinter as tk

from src.config import MENU_BACKGROUND_IMAGE_PATH
from src.screens.base import Screen
from src.ui.animated_background import AnimatedBackground
from src.ui.components import GlassButton


class MenuScreen(Screen):
    def __init__(self, app: "MenuApp") -> None:
        super().__init__(app)

        self.canvas = tk.Canvas(self.container, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)

        self.background = AnimatedBackground(
            self.canvas,
            MENU_BACKGROUND_IMAGE_PATH,
            darken_alpha=110,
            drift_x=1,
            drift_y=1,
            show_scanline=False,
        )

        self.panel = tk.Frame(
            self.canvas,
            bg=self.app.theme.panel_bg,
            highlightthickness=2,
            highlightbackground=self.app.theme.panel_border,
            padx=28,
            pady=26,
        )
        self.panel_window = self.canvas.create_window(0, 0, window=self.panel, anchor="nw")

        self._build_content()
        self.background.start()
        self.on_resize(self.app.width, self.app.height)

    def _build_content(self) -> None:
        tk.Label(
            self.panel,
            text="MINDSET",
            bg=self.app.theme.panel_bg,
            fg=self.app.theme.text_primary,
            font=("Arial", 48, "bold"),
            anchor="w",
        ).pack(fill="x", anchor="w")

        tk.Label(
            self.panel,
            text="ИНТЕЛЛЕКТУАЛЬНАЯ ВИКТОРИНА",
            bg=self.app.theme.panel_bg,
            fg=self.app.theme.text_secondary,
            font=("Arial", 16, "bold"),
            anchor="w",
        ).pack(fill="x", anchor="w", pady=(4, 2))

        tk.Label(
            self.panel,
            text="Главное меню",
            bg=self.app.theme.panel_bg,
            fg=self.app.theme.text_secondary,
            font=("Arial", 13),
            anchor="w",
        ).pack(fill="x", anchor="w", pady=(0, 18))

        buttons_holder = tk.Frame(self.panel, bg=self.app.theme.panel_bg)
        buttons_holder.pack(fill="x", pady=(4, 14))

        for text, command in [
            ("Играть", self.app.open_mode_select),
            ("Рекорды", self.app.open_leaderboard),
            ("Настройки", self.app.open_settings),
            ("Выход", self.app.quit),
        ]:
            btn = GlassButton(
                buttons_holder,
                text=text,
                command=command,
                theme=self.app.theme,
                font=("Arial", 15, "bold"),
                width=26,
            )
            btn.pack(anchor="w", fill="x", pady=7)

        tk.Label(
            self.panel,
            textvariable=self.app.status_text_var,
            bg=self.app.theme.panel_bg,
            fg=self.app.theme.text_secondary,
            font=("Arial", 11),
            anchor="w",
        ).pack(fill="x", anchor="w", pady=(8, 2))

        tk.Label(
            self.panel,
            text="F11 - fullscreen",
            bg=self.app.theme.panel_bg,
            fg=self.app.theme.text_secondary,
            font=("Arial", 11),
            anchor="w",
        ).pack(fill="x", anchor="w")

    def on_resize(self, width: int, height: int) -> None:
        panel_width = int(width * 0.42)
        panel_height = int(height * 0.74)
        self.canvas.coords(self.panel_window, int(width * 0.07), int(height * 0.14))
        self.canvas.itemconfigure(self.panel_window, width=panel_width, height=panel_height)

    def on_destroy(self) -> None:
        self.background.stop()


class MenuApp:
    theme: object
    width: int
    height: int
    status_text_var: tk.StringVar

    def open_mode_select(self) -> None:
        raise NotImplementedError

    def open_settings(self) -> None:
        raise NotImplementedError

    def open_leaderboard(self) -> None:
        raise NotImplementedError

    def quit(self) -> None:
        raise NotImplementedError
