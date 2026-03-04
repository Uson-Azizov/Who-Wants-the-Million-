from __future__ import annotations

import tkinter as tk

from src.screens.base import Screen
from src.ui.components import GlassButton


class SettingsScreen(Screen):
    def __init__(self, app: "SettingsApp") -> None:
        super().__init__(app)

        self.container.configure(bg=self.app.theme.window_bg)

        panel = tk.Frame(
            self.container,
            bg=self.app.theme.panel_bg,
            highlightthickness=2,
            highlightbackground=self.app.theme.panel_border,
            padx=28,
            pady=26,
        )
        panel.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.58, relheight=0.54)

        tk.Label(
            panel,
            text="Настройки",
            bg=self.app.theme.panel_bg,
            fg=self.app.theme.text_primary,
            font=("Arial", 34, "bold"),
        ).pack(pady=(8, 12))

        tk.Label(
            panel,
            text="Fullscreen переключается кнопкой F11",
            bg=self.app.theme.panel_bg,
            fg=self.app.theme.text_secondary,
            font=("Arial", 15),
        ).pack(pady=(4, 8))

        tk.Label(
            panel,
            text="Нажми ESC для возврата",
            bg=self.app.theme.panel_bg,
            fg=self.app.theme.text_secondary,
            font=("Arial", 14),
        ).pack(pady=(0, 18))

        tk.Label(
            panel,
            text="Статус PostgreSQL:",
            bg=self.app.theme.panel_bg,
            fg=self.app.theme.text_secondary,
            font=("Arial", 13, "bold"),
        ).pack(pady=(4, 2))

        tk.Label(
            panel,
            textvariable=self.app.db_status_var,
            bg=self.app.theme.panel_bg,
            fg=self.app.theme.text_primary,
            font=("Arial", 12),
            wraplength=620,
            justify="center",
        ).pack(pady=(0, 12))

        GlassButton(
            panel,
            text="Переключить Fullscreen",
            command=self.app.toggle_fullscreen,
            theme=self.app.theme,
            font=("Arial", 14, "bold"),
            width=28,
        ).pack(pady=8)

        GlassButton(
            panel,
            text="Проверить PostgreSQL",
            command=self.app.check_database,
            theme=self.app.theme,
            font=("Arial", 14, "bold"),
            width=28,
        ).pack(pady=8)

        GlassButton(
            panel,
            text="Назад в меню",
            command=self.app.open_menu,
            theme=self.app.theme,
            font=("Arial", 14, "bold"),
            width=28,
        ).pack(pady=8)

    def on_escape(self) -> None:
        self.app.open_menu()


class SettingsApp:
    theme: object
    db_status_var: tk.StringVar

    def open_menu(self) -> None:
        raise NotImplementedError

    def toggle_fullscreen(self) -> None:
        raise NotImplementedError

    def check_database(self) -> None:
        raise NotImplementedError
