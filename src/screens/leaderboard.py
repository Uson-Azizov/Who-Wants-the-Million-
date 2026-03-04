from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from src.database import LeaderboardEntry
from src.screens.base import Screen
from src.ui.components import GlassButton


class LeaderboardScreen(Screen):
    def __init__(self, app: "LeaderboardApp") -> None:
        super().__init__(app)

        self.container.configure(bg=self.app.theme.window_bg)

        panel = tk.Frame(
            self.container,
            bg=self.app.theme.panel_bg,
            highlightthickness=2,
            highlightbackground=self.app.theme.panel_border,
            padx=20,
            pady=18,
        )
        panel.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.86, relheight=0.82)

        tk.Label(
            panel,
            text="Рекорды",
            bg=self.app.theme.panel_bg,
            fg=self.app.theme.text_primary,
            font=("Arial", 32, "bold"),
        ).pack(pady=(2, 8))

        tk.Label(
            panel,
            text="Топ результатов по количеству правильных ответов",
            bg=self.app.theme.panel_bg,
            fg=self.app.theme.text_secondary,
            font=("Arial", 13),
        ).pack(pady=(0, 10))

        self._configure_tree_style()
        self.tree = ttk.Treeview(
            panel,
            columns=("rank", "player", "difficulty", "score", "asked", "win", "date"),
            show="headings",
            height=14,
            style="Leaderboard.Treeview",
        )

        headers = [
            ("rank", "#", 50),
            ("player", "Игрок", 180),
            ("difficulty", "Сложность", 120),
            ("score", "Верных", 90),
            ("asked", "Вопросов", 100),
            ("win", "Победа", 90),
            ("date", "Дата", 170),
        ]
        for col, title, width in headers:
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=8, pady=8)

        bottom = tk.Frame(panel, bg=self.app.theme.panel_bg)
        bottom.pack(fill="x", pady=(8, 2))

        GlassButton(
            bottom,
            text="Обновить",
            command=self.load_leaderboard,
            theme=self.app.theme,
            font=("Arial", 13, "bold"),
            width=20,
        ).pack(side="left", padx=(0, 8))

        GlassButton(
            bottom,
            text="Назад в меню",
            command=self.app.open_menu,
            theme=self.app.theme,
            font=("Arial", 13, "bold"),
            width=20,
        ).pack(side="left")

        tk.Label(
            bottom,
            textvariable=self.app.db_status_var,
            bg=self.app.theme.panel_bg,
            fg=self.app.theme.text_secondary,
            font=("Arial", 11),
            anchor="e",
        ).pack(side="right")

        self.load_leaderboard()

    def _configure_tree_style(self) -> None:
        style = ttk.Style(self.container)
        style.theme_use("default")
        style.configure(
            "Leaderboard.Treeview",
            background="#0f1f35",
            fieldbackground="#0f1f35",
            foreground="#eaf4ff",
            rowheight=28,
            borderwidth=0,
            relief="flat",
            font=("Arial", 11),
        )
        style.configure(
            "Leaderboard.Treeview.Heading",
            background="#1f3a5f",
            foreground="#f4f9ff",
            relief="flat",
            font=("Arial", 11, "bold"),
        )
        style.map(
            "Leaderboard.Treeview",
            background=[("selected", "#2a5387")],
            foreground=[("selected", "#ffffff")],
        )
    def _difficulty_label(self, value: str) -> str:
        mapping = {"easy": "Легкая", "medium": "Нормальная", "hard": "Сложная"}
        return mapping.get(value.lower(), value)

    def load_leaderboard(self) -> None:
        entries, message = self.app.get_leaderboard(limit=25)
        self.app.db_status_var.set(message)

        self.tree.delete(*self.tree.get_children())

        if not entries:
            self.tree.insert(
                "",
                "end",
                values=("-", "Нет данных", "-", "-", "-", "-", "-"),
            )
            return

        for index, item in enumerate(entries, start=1):
            self.tree.insert(
                "",
                "end",
                values=(
                    index,
                    item.player_name,
                    self._difficulty_label(item.difficulty),
                    item.score,
                    item.asked_questions,
                    "Да" if item.is_win else "Нет",
                    item.created_at,
                ),
            )

    def on_escape(self) -> None:
        self.app.open_menu()


class LeaderboardApp:
    theme: object
    db_status_var: tk.StringVar

    def open_menu(self) -> None:
        raise NotImplementedError

    def get_leaderboard(self, limit: int = 25) -> tuple[list[LeaderboardEntry], str]:
        raise NotImplementedError
