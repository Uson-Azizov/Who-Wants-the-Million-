from __future__ import annotations

import tkinter as tk

from src.models import Difficulty, Question
from src.screens.base import Screen
from src.ui.components import GlassButton

EASY_AMOUNTS = [500, 1000, 2000, 3000, 5000]
MEDIUM_AMOUNTS = [10000, 15000, 25000, 50000]
HARD_AMOUNTS = [100000, 200000, 400000, 800000, 1000000, 3000000]

PRIZE_LEVELS: list[tuple[int, Difficulty]] = (
    [(amount, Difficulty.EASY) for amount in EASY_AMOUNTS]
    + [(amount, Difficulty.MEDIUM) for amount in MEDIUM_AMOUNTS]
    + [(amount, Difficulty.HARD) for amount in HARD_AMOUNTS]
)

BG_PURPLE = "#2a0288"
PANEL_PURPLE = "#2a0288"
CARD_BG = "#060045"
ACCENT_CYAN = "#23dcff"
ACCENT_ORANGE = "#ff9d19"
TEXT_PRIMARY = "#f4f8ff"
TEXT_SECONDARY = "#9fc8ff"


class GameScreen(Screen):
    def __init__(self, app: "GameApp") -> None:
        super().__init__(app)

        self.canvas = tk.Canvas(self.container, highlightthickness=0, bd=0, bg=BG_PURPLE)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.background_base_id = self.canvas.create_rectangle(0, 0, 0, 0, fill=BG_PURPLE, outline="", tags="bg")
        self.background_tint_id = self.canvas.create_rectangle(
            0,
            0,
            0,
            0,
            fill=BG_PURPLE,
            outline="",
            tags="bg",
        )

        self.root_panel = tk.Frame(
            self.canvas,
            bg=BG_PURPLE,
            highlightthickness=0,
            padx=20,
            pady=14,
        )
        self.root_panel_window = self.canvas.create_window(0, 0, window=self.root_panel, anchor="n")

        self.current_question: Question | None = None
        self.answer_buttons: dict[int, GlassButton] = {}
        self.answer_badges: dict[int, tuple[tk.Canvas, int, int]] = {}
        self.pending_next_question = False
        self.result_saved = False
        self.level_index = 0

        self._build_content()
        self.on_resize(self.app.width, self.app.height)
        self._load_question()

    def _build_content(self) -> None:
        self._build_header()
        self._build_question_block()
        self._build_lifelines()
        self._build_answers()

    def _build_header(self) -> None:
        header = tk.Frame(self.root_panel, bg=PANEL_PURPLE)
        header.pack(fill="x", pady=(0, 12))
        header.columnconfigure(1, weight=1)

        self.menu_btn = GlassButton(
            header,
            text="Меню",
            command=self.app.open_menu,
            theme=self.app.theme,
            font=("Arial", 14, "bold"),
            width=11,
            height=46,
            radius=22,
            bg_color=CARD_BG,
            hover_color="#101060",
            border_color=ACCENT_CYAN,
            text_color=TEXT_PRIMARY,
            canvas_bg=PANEL_PURPLE,
        )
        self.menu_btn.grid(row=0, column=0, sticky="w")

        self.progress_btn = GlassButton(
            header,
            text="1/15",
            command=lambda: None,
            theme=self.app.theme,
            font=("Arial", 18, "bold"),
            width=12,
            height=46,
            radius=22,
            bg_color=CARD_BG,
            hover_color="#101060",
            border_color=ACCENT_CYAN,
            text_color=TEXT_PRIMARY,
            canvas_bg=PANEL_PURPLE,
        )
        self.progress_btn.grid(row=0, column=1)

        self.amount_btn = GlassButton(
            header,
            text="500сом",
            command=lambda: None,
            theme=self.app.theme,
            font=("Arial", 18, "bold"),
            width=13,
            height=46,
            radius=22,
            bg_color=CARD_BG,
            hover_color="#101060",
            border_color=ACCENT_CYAN,
            text_color=TEXT_PRIMARY,
            canvas_bg=PANEL_PURPLE,
        )
        self.amount_btn.grid(row=0, column=2, sticky="e")

    def _build_question_block(self) -> None:
        question_wrap = tk.Frame(
            self.root_panel,
            bg=CARD_BG,
            highlightthickness=4,
            highlightbackground=ACCENT_CYAN,
            padx=28,
            pady=22,
        )
        question_wrap.pack(fill="x", pady=(92, 20))

        question_row = tk.Frame(question_wrap, bg=CARD_BG)
        question_row.pack(fill="x")
        question_row.columnconfigure(1, weight=1)

        self.question_prefix_label = tk.Label(
            question_row,
            text="Вопрос:",
            bg=CARD_BG,
            fg=ACCENT_CYAN,
            font=("Arial", 22, "bold"),
            anchor="nw",
        )
        self.question_prefix_label.grid(row=0, column=0, sticky="nw", padx=(0, 8))

        self.question_label = tk.Label(
            question_row,
            text="",
            bg=CARD_BG,
            fg=TEXT_PRIMARY,
            font=("Arial", 22, "bold"),
            justify="left",
            anchor="nw",
            wraplength=900,
        )
        self.question_label.grid(row=0, column=1, sticky="nwe")

    def _build_lifelines(self) -> None:
        lifelines = tk.Frame(self.root_panel, bg=PANEL_PURPLE)
        lifelines.pack(fill="x", pady=(14, 16))
        lifelines.columnconfigure(0, weight=1)
        lifelines.columnconfigure(1, weight=1)
        lifelines.columnconfigure(2, weight=1)

        self.hint_bird = self._build_round_hint(lifelines, "🕊", ACCENT_ORANGE)
        self.hint_bird.grid(row=0, column=0, sticky="w", padx=(6, 0))

        self.hint_5050 = self._build_round_hint(lifelines, "50\n50", ACCENT_ORANGE)
        self.hint_5050.grid(row=0, column=1)

        self.hint_2x = self._build_round_hint(lifelines, "2X", ACCENT_ORANGE)
        self.hint_2x.grid(row=0, column=2, sticky="e", padx=(0, 6))

        self.feedback_label = tk.Label(
            lifelines,
            text="",
            bg=PANEL_PURPLE,
            fg=TEXT_SECONDARY,
            font=("Arial", 13, "bold"),
            anchor="center",
        )
        self.feedback_label.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(4, 0))

    def _build_round_hint(self, parent: tk.Misc, text: str, border_color: str) -> tk.Canvas:
        hint = tk.Canvas(parent, width=104, height=104, highlightthickness=0, bd=0, bg=PANEL_PURPLE)
        hint.create_oval(8, 8, 96, 96, outline=border_color, width=4, fill=CARD_BG)
        hint.create_text(52, 52, text=text, fill=ACCENT_CYAN, font=("Arial", 23, "bold"), justify="center")
        return hint

    def _build_answers(self) -> None:
        self.answers_grid = tk.Frame(self.root_panel, bg=PANEL_PURPLE)
        self.answers_grid.pack(fill="x", pady=(24, 4), padx=0)
        self.answers_grid.columnconfigure(0, weight=1, uniform="answer_col")
        self.answers_grid.columnconfigure(1, weight=1, uniform="answer_col")

    def _clear_answer_buttons(self) -> None:
        for child in self.answers_grid.winfo_children():
            child.destroy()
        self.answer_buttons = {}
        self.answer_badges = {}

    def _mark_selected_badge(self, selected_index: int, is_correct: bool) -> None:
        badge = self.answer_badges.get(selected_index)
        if badge is None:
            return

        badge_canvas, oval_id, text_id = badge
        if is_correct:
            outline = "#2fff7f"
            fill = "#03351c"
            text_color = "#79ffb2"
        else:
            outline = "#ff3b30"
            fill = "#3a0606"
            text_color = "#ff9e97"

        badge_canvas.itemconfigure(oval_id, outline=outline, fill=fill, width=5)
        badge_canvas.itemconfigure(text_id, fill=text_color)

    def _set_answers_enabled(self, enabled: bool) -> None:
        for button in self.answer_buttons.values():
            button.configure(state="normal" if enabled else "disabled")

    def _set_question_text(self, prefix: str, body: str) -> None:
        self.question_prefix_label.configure(text=prefix)
        self.question_label.configure(text=body)

    def _format_amount(self, value: int) -> str:
        return f"{value:,}".replace(",", " ") + "сом"

    def _update_header_progress(self) -> None:
        current_step = min(self.level_index + 1, len(PRIZE_LEVELS))
        total_steps = len(PRIZE_LEVELS)
        self.progress_btn.configure(text=f"{current_step}/{total_steps}")

        target_amount = PRIZE_LEVELS[min(self.level_index, len(PRIZE_LEVELS) - 1)][0]
        self.amount_btn.configure(text=self._format_amount(target_amount))

    def _load_question(self) -> None:
        self.pending_next_question = False
        self._clear_answer_buttons()

        if self.level_index >= len(PRIZE_LEVELS):
            self._finish_game_win()
            return

        self._update_header_progress()
        target_amount, difficulty = PRIZE_LEVELS[self.level_index]

        self.current_question = self.app.game_service.get_next_question(difficulty)
        if self.current_question is None:
            self._set_question_text("Ошибка:", f"Недостаточно вопросов ({difficulty.value})")
            self.feedback_label.configure(text="Возврат в меню...")
            self.container.after(1200, self.app.open_menu)
            return

        self._set_question_text("Вопрос:", self.current_question.text)
        self.feedback_label.configure(text="")

        answer_style = dict(
            theme=self.app.theme,
            font=("Arial", 14, "bold"),
            width=26,
            height=62,
            radius=24,
            bg_color=CARD_BG,
            hover_color="#0f1168",
            border_color=ACCENT_CYAN,
            text_color=TEXT_PRIMARY,
            canvas_bg=PANEL_PURPLE,
        )

        layout = [
            (0, 0, 0, "A"),
            (0, 1, 2, "C"),
            (1, 0, 1, "B"),
            (1, 1, 3, "D"),
        ]

        for row, col, index, letter in layout:
            option_text = self.current_question.options[index]

            wrap = tk.Frame(self.answers_grid, bg=PANEL_PURPLE)
            wrap.grid(row=row, column=col, sticky="ew", padx=4, pady=10)
            wrap.columnconfigure(1, weight=1)
            wrap.columnconfigure(0, minsize=70)

            tag = tk.Canvas(wrap, width=66, height=66, highlightthickness=0, bd=0, bg=PANEL_PURPLE)
            oval_id = tag.create_oval(6, 6, 60, 60, outline=ACCENT_ORANGE, width=4, fill=CARD_BG)
            text_id = tag.create_text(33, 33, text=letter, fill=ACCENT_CYAN, font=("Arial", 24, "bold"))
            tag.grid(row=0, column=0, padx=(0, 6))
            self.answer_badges[index] = (tag, oval_id, text_id)

            button = GlassButton(
                wrap,
                text=option_text,
                command=lambda i=index: self._submit_answer(i),
                **answer_style,
            )
            button.grid(row=0, column=1, sticky="ew")
            self.answer_buttons[index] = button

    def _finish_game_win(self) -> None:
        top_amount = PRIZE_LEVELS[-1][0]
        self._set_question_text("Итог:", f"Поздравляем! Вы дошли до {self._format_amount(top_amount)}")
        self.feedback_label.configure(text="Игра завершена")
        self.progress_btn.configure(text=f"{len(PRIZE_LEVELS)}/{len(PRIZE_LEVELS)}")
        self.amount_btn.configure(text=self._format_amount(top_amount))

        if not self.result_saved:
            self.app.save_game_result("mixed", True)
            self.result_saved = True

        self.container.after(1400, self.app.open_menu)

    def _submit_answer(self, selected_index: int) -> None:
        if self.current_question is None or self.pending_next_question:
            return

        is_correct = self.app.game_service.submit_answer(selected_index)
        self._set_answers_enabled(False)
        self._mark_selected_badge(selected_index, is_correct)

        if is_correct:
            self.feedback_label.configure(text="Верно!")
            self.level_index += 1
            self.pending_next_question = True
            self.container.after(450, self._load_question)
            return

        self.feedback_label.configure(text="Неправильно. Возврат в главное меню...")
        if not self.result_saved:
            self.app.save_game_result("mixed", False)
            self.result_saved = True
        self.container.after(900, self.app.open_menu)

    def on_resize(self, width: int, height: int) -> None:
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        draw_w = canvas_w if canvas_w > 1 else width
        draw_h = canvas_h if canvas_h > 1 else height

        panel_width = min(int(draw_w * 0.74), 1120)
        panel_center_x = draw_w // 2
        panel_y = max(8, int(draw_h * 0.02))

        self.canvas.coords(self.background_base_id, 0, 0, draw_w, draw_h)
        self.canvas.coords(self.background_tint_id, 0, 0, draw_w, draw_h)

        self.canvas.coords(self.root_panel_window, panel_center_x, panel_y)
        self.canvas.itemconfigure(self.root_panel_window, width=panel_width)
        self.question_label.configure(wraplength=max(360, int(panel_width * 0.66)))

        self.canvas.tag_raise("bg")
        self.canvas.tag_raise(self.root_panel_window)

    def _on_canvas_configure(self, event: tk.Event) -> None:
        if event.width <= 1 or event.height <= 1:
            return
        self.on_resize(event.width, event.height)

    def on_escape(self) -> None:
        self.app.open_menu()


class GameApp:
    theme: object
    width: int
    height: int
    game_service: object

    def open_menu(self) -> None:
        raise NotImplementedError

    def save_game_result(self, difficulty: Difficulty | str, is_win: bool) -> None:
        raise NotImplementedError
