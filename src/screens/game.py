from __future__ import annotations

import tkinter as tk

from src.config import MENU_BACKGROUND_IMAGE_PATH
from src.models import Difficulty, Question
from src.screens.base import Screen
from src.ui.animated_background import AnimatedBackground
from src.ui.components import GlassButton


class GameScreen(Screen):
    def __init__(self, app: "GameApp", difficulty: Difficulty) -> None:
        super().__init__(app)
        self.difficulty = difficulty

        self.canvas = tk.Canvas(self.container, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)

        self.background = AnimatedBackground(
            self.canvas,
            MENU_BACKGROUND_IMAGE_PATH,
            darken_alpha=132,
            drift_x=2,
            drift_y=2,
            show_scanline=True,
        )

        self.panel = tk.Frame(
            self.canvas,
            bg=self.app.theme.panel_bg,
            highlightthickness=2,
            highlightbackground=self.app.theme.panel_border,
            padx=28,
            pady=20,
        )
        self.panel_window = self.canvas.create_window(0, 0, window=self.panel, anchor="nw")

        self.current_question: Question | None = None
        self.answer_buttons: list[GlassButton] = []
        self.pending_next_question = False

        self._build_content()
        self.background.start()
        self.on_resize(self.app.width, self.app.height)
        self._load_question()

    def _build_content(self) -> None:
        self.title_label = tk.Label(
            self.panel,
            text=f"Mindset | Сложность: {self.difficulty.value}",
            bg=self.app.theme.panel_bg,
            fg=self.app.theme.text_primary,
            font=("Arial", 24, "bold"),
        )
        self.title_label.pack(pady=(4, 8))

        self.question_label = tk.Label(
            self.panel,
            text="",
            bg=self.app.theme.panel_bg,
            fg=self.app.theme.text_primary,
            font=("Arial", 18, "bold"),
            justify="center",
            wraplength=900,
        )
        self.question_label.pack(pady=(8, 14))

        self.feedback_label = tk.Label(
            self.panel,
            text="",
            bg=self.app.theme.panel_bg,
            fg=self.app.theme.text_secondary,
            font=("Arial", 13),
        )
        self.feedback_label.pack(pady=(0, 10))

        self.answers_holder = tk.Frame(self.panel, bg=self.app.theme.panel_bg)
        self.answers_holder.pack(fill="x", pady=(4, 10))

        footer = tk.Frame(self.panel, bg=self.app.theme.panel_bg)
        footer.pack(fill="x", side="bottom", pady=(10, 4))

        self.score_label = tk.Label(
            footer,
            text="Счет: 0",
            bg=self.app.theme.panel_bg,
            fg=self.app.theme.text_secondary,
            font=("Arial", 12, "bold"),
        )
        self.score_label.pack(side="left")

        tk.Label(
            footer,
            text="ESC - в меню",
            bg=self.app.theme.panel_bg,
            fg=self.app.theme.text_secondary,
            font=("Arial", 12),
        ).pack(side="right")

    def _clear_answer_buttons(self) -> None:
        for button in self.answer_buttons:
            button.destroy()
        self.answer_buttons = []

    def _set_answers_enabled(self, enabled: bool) -> None:
        for button in self.answer_buttons:
            button.configure(state="normal" if enabled else "disabled")

    def _load_question(self) -> None:
        self.pending_next_question = False
        self.current_question = self.app.game_service.get_next_question(self.difficulty)
        self._clear_answer_buttons()

        if self.current_question is None:
            self.question_label.configure(text="В этой сложности больше нет вопросов.")
            self.feedback_label.configure(text="Вернись в меню и выбери режим снова.")
            return

        self.question_label.configure(text=self.current_question.text)
        self.feedback_label.configure(text="Выбери один правильный вариант")

        for index, option in enumerate(self.current_question.options):
            button = GlassButton(
                self.answers_holder,
                text=option,
                command=lambda i=index: self._submit_answer(i),
                theme=self.app.theme,
                font=("Arial", 14, "bold"),
                width=38,
            )
            button.pack(fill="x", padx=36, pady=6)
            self.answer_buttons.append(button)

    def _submit_answer(self, selected_index: int) -> None:
        if self.current_question is None or self.pending_next_question:
            return

        is_correct = self.app.game_service.submit_answer(selected_index)
        self.score_label.configure(text=f"Счет: {self.app.game_service.session.score}")
        self._set_answers_enabled(False)

        if is_correct:
            self.feedback_label.configure(text="Верно! Следующий вопрос...")
            self.pending_next_question = True
            self.container.after(450, self._load_question)
            return

        self.feedback_label.configure(text="Неправильно. Возврат в главное меню...")
        self.container.after(900, self.app.open_menu)

    def on_resize(self, width: int, height: int) -> None:
        panel_width = int(width * 0.86)
        panel_height = int(height * 0.84)
        panel_x = (width - panel_width) // 2
        panel_y = int(height * 0.08)

        self.canvas.coords(self.panel_window, panel_x, panel_y)
        self.canvas.itemconfigure(self.panel_window, width=panel_width, height=panel_height)
        self.question_label.configure(wraplength=max(400, int(panel_width * 0.88)))

    def on_escape(self) -> None:
        self.app.open_menu()

    def on_destroy(self) -> None:
        self.background.stop()


class GameApp:
    theme: object
    width: int
    height: int
    game_service: object

    def open_menu(self) -> None:
        raise NotImplementedError





























