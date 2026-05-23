from __future__ import annotations

import random
import tkinter as tk

from src.config import IMAGES_DIR
from src.models import Difficulty, Question
from src.screens.base import Screen
from src.ui.components import GlassButton

try:
    from PIL import Image, ImageTk
except Exception:  # pragma: no cover - optional dependency
    Image = None
    ImageTk = None


EASY_AMOUNTS = [500, 1000, 2000, 3000, 5000]
MEDIUM_AMOUNTS = [10000, 15000, 25000, 50000]
HARD_AMOUNTS = [100000, 200000, 400000, 800000, 1000000, 3000000]

PRIZE_LEVELS: list[tuple[int, Difficulty]] = (
    [(amount, Difficulty.EASY) for amount in EASY_AMOUNTS]
    + [(amount, Difficulty.MEDIUM) for amount in MEDIUM_AMOUNTS]
    + [(amount, Difficulty.HARD) for amount in HARD_AMOUNTS]
)

DESIGN_WIDTH = 1440
DESIGN_HEIGHT = 1024
LAYOUT_SCALE_BOOST = 1.0
LAYOUT_SHIFT_Y = 0
BG_PURPLE = "#2a0288"
CARD_BG = "#060045"
ACCENT_CYAN = "#5adcf4"
ACCENT_ORANGE = "#f39a1f"
TEXT_PRIMARY = "#f4f8ff"
TEXT_SECONDARY = "#9fc8ff"
TEXT_MUTED = "#69739B"
LIFELINE_USED = "#5D617A"

MENU_SPEC = (34, 52, 236, 66, 34)
PROGRESS_SPEC = (548, 54, 344, 74, 36)
AMOUNT_SPEC = (1068, 54, 332, 74, 36)
QUESTION_RECT = (160, 226, 1120, 106)
LIFELINE_CENTERS = {
    "phoenix": (255, 540),
    "5050": (720, 540),
    "2x": (1185, 540),
}
ANSWER_LAYOUT = {
    0: (150, 748),
    1: (780, 748),
    2: (150, 872),
    3: (780, 872),
}
ANSWER_TOP_LAYOUT = {
    0: (150, 748),
    1: (780, 748),
}
ANSWER_BADGE_SIZE = 76
ANSWER_BUTTON_SIZE = (520, 88)
LIFELINE_OUTER_RADIUS = 64
LIFELINE_PHOENIX_PATH = IMAGES_DIR / "lifeline_phoenix.png"
LIFELINE_5050_PATH = IMAGES_DIR / "lifeline_5050.png"
LIFELINE_2X_PATH = IMAGES_DIR / "lifeline_2x.png"


class GameScreen(Screen):
    def __init__(self, app: "GameApp") -> None:
        super().__init__(app)

        self.canvas = tk.Canvas(self.container, highlightthickness=0, bd=0, bg=BG_PURPLE)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.stage_frame = tk.Frame(self.canvas, bg=BG_PURPLE, highlightthickness=0, bd=0)
        self.stage_frame.pack_propagate(False)
        self.stage_window = self.canvas.create_window(0, 0, window=self.stage_frame, anchor="nw")

        self.scale = 1.0
        self.stage_left = 0
        self.stage_top = 0
        self.stage_width = DESIGN_WIDTH
        self.stage_height = DESIGN_HEIGHT

        self.current_question: Question | None = None
        self.answer_buttons: dict[int, GlassButton] = {}
        self.answer_wrappers: dict[int, tk.Frame] = {}
        self.answer_badges: dict[int, tuple[tk.Canvas, int, int]] = {}
        self.hidden_answers: set[int] = set()
        self.pending_next_question = False
        self.result_saved = False
        self.level_index = 0
        self._after_jobs: set[str] = set()
        self.lifeline_used = {"phoenix": False, "5050": False, "2x": False}
        self.lifeline_armed = {"phoenix": False, "2x": False}
        self.lifeline_canvases: dict[str, tk.Canvas] = {}
        self.lifeline_images: dict[str, ImageTk.PhotoImage | None] = {}
        self.leave_dialog: tk.Toplevel | None = None
        self._lifeline_icon_sources = {
            "phoenix": self._load_icon_source(LIFELINE_PHOENIX_PATH, white_to_alpha=True),
            "5050": self._load_icon_source(LIFELINE_5050_PATH, white_to_alpha=False),
            "2x": self._load_icon_source(LIFELINE_2X_PATH, white_to_alpha=True),
        }

        self._build_stage()
        self.on_resize(self.app.width, self.app.height)
        self._load_question()

    def _load_icon_source(self, path, *, white_to_alpha: bool):
        if Image is None or not path.exists():
            return None
        try:
            image = Image.open(path).convert("RGBA")
        except Exception:
            return None

        pixels = image.load()
        for y in range(image.height):
            for x in range(image.width):
                r, g, b, a = pixels[x, y]
                if white_to_alpha and a and r > 245 and g > 245 and b > 245:
                    pixels[x, y] = (255, 255, 255, 0)

        bbox = image.getbbox()
        if bbox:
            image = image.crop(bbox)
        return image

    @staticmethod
    def _fit_stage(width: int, height: int) -> tuple[float, int, int, int, int]:
        scale = min(width / DESIGN_WIDTH, height / DESIGN_HEIGHT) * LAYOUT_SCALE_BOOST
        stage_width = max(1, int(DESIGN_WIDTH * scale))
        stage_height = max(1, int(DESIGN_HEIGHT * scale))
        left = (width - stage_width) // 2
        top = (height - stage_height) // 2 + int(LAYOUT_SHIFT_Y * scale)
        return scale, left, top, stage_width, stage_height

    def _font(self, size: int, weight: str = "bold") -> tuple[str, int, str]:
        return ("Arial", max(10, int(size * self.scale * 0.84)), weight)

    def _place_scaled(self, widget: tk.Misc, spec: tuple[int, int, int, int]) -> None:
        x, y, w, h = spec
        widget.place(
            x=int(x * self.scale),
            y=int(y * self.scale),
            width=max(1, int(w * self.scale)),
            height=max(1, int(h * self.scale)),
        )

    def _build_stage(self) -> None:
        self.menu_btn = GlassButton(
            self.stage_frame,
            text=self.app.tr("common.menu"),
            command=self._request_leave_game,
            theme=self.app.theme,
            font=("Arial", 18, "bold"),
            width=10,
            height=72,
            radius=34,
            bg_color=CARD_BG,
            hover_color="#101060",
            border_color=ACCENT_CYAN,
            text_color=TEXT_PRIMARY,
            canvas_bg=BG_PURPLE,
            border_width=3,
        )

        self.progress_btn = GlassButton(
            self.stage_frame,
            text=self.app.tr("game.round", current=1, total=len(PRIZE_LEVELS)),
            command=lambda: None,
            theme=self.app.theme,
            font=("Arial", 20, "bold"),
            width=18,
            height=72,
            radius=34,
            bg_color=CARD_BG,
            hover_color="#101060",
            border_color=ACCENT_CYAN,
            text_color=TEXT_PRIMARY,
            canvas_bg=BG_PURPLE,
            border_width=3,
        )

        self.amount_btn = GlassButton(
            self.stage_frame,
            text=self._format_amount(PRIZE_LEVELS[0][0]),
            command=lambda: None,
            theme=self.app.theme,
            font=("Arial", 20, "bold"),
            width=12,
            height=72,
            radius=34,
            bg_color=CARD_BG,
            hover_color="#101060",
            border_color=ACCENT_CYAN,
            text_color=TEXT_PRIMARY,
            canvas_bg=BG_PURPLE,
            border_width=3,
        )

        self.question_wrap = tk.Frame(
            self.stage_frame,
            bg=CARD_BG,
            highlightthickness=4,
            highlightbackground=ACCENT_CYAN,
            bd=0,
        )
        self.question_prefix_label = tk.Label(
            self.question_wrap,
            text=self.app.tr("game.question"),
            bg=CARD_BG,
            fg=ACCENT_CYAN,
            anchor="w",
        )
        self.question_label = tk.Label(
            self.question_wrap,
            text="",
            bg=CARD_BG,
            fg=TEXT_PRIMARY,
            anchor="w",
            justify="left",
            wraplength=940,
        )

        self.feedback_label = tk.Label(
            self.stage_frame,
            text="",
            bg=BG_PURPLE,
            fg=TEXT_SECONDARY,
            anchor="center",
            justify="center",
        )

        for name in ("phoenix", "5050", "2x"):
            canvas = tk.Canvas(self.stage_frame, highlightthickness=0, bd=0, bg=BG_PURPLE, cursor="hand2")
            canvas.bind("<Button-1>", lambda _event, lifeline=name: self._activate_lifeline(lifeline))
            self.lifeline_canvases[name] = canvas

        for index, letter in enumerate(("A", "B", "C", "D")):
            wrap = tk.Frame(self.stage_frame, bg=BG_PURPLE, bd=0, highlightthickness=0)
            badge = tk.Canvas(wrap, highlightthickness=0, bd=0, bg=BG_PURPLE)
            oval_id = badge.create_oval(6, 6, ANSWER_BADGE_SIZE - 6, ANSWER_BADGE_SIZE - 6, outline=ACCENT_ORANGE, width=4, fill=CARD_BG)
            text_id = badge.create_text(
                ANSWER_BADGE_SIZE // 2,
                ANSWER_BADGE_SIZE // 2,
                text=letter,
                fill=ACCENT_CYAN,
                font=("Arial", 28, "bold"),
            )
            badge.place(x=0, y=0, width=ANSWER_BADGE_SIZE, height=ANSWER_BADGE_SIZE)

            button = GlassButton(
                wrap,
                text="",
                command=lambda i=index: self._submit_answer(i),
                theme=self.app.theme,
                font=("Arial", 16, "bold"),
                width=33,
                height=ANSWER_BUTTON_SIZE[1],
                radius=30,
                bg_color=CARD_BG,
                hover_color="#101060",
                border_color=ACCENT_CYAN,
                text_color=TEXT_PRIMARY,
                canvas_bg=BG_PURPLE,
                border_width=3,
            )
            self.answer_badges[index] = (badge, oval_id, text_id)
            self.answer_buttons[index] = button
            self.answer_wrappers[index] = wrap

    def _draw_lifeline(self, name: str) -> None:
        canvas = self.lifeline_canvases[name]
        size = max(72, int(140 * self.scale))
        canvas.configure(width=size, height=size)
        canvas.delete("all")

        used = self.lifeline_used[name]
        armed = self.lifeline_armed.get(name, False)

        cx = size // 2
        cy = size // 2

        icon_source = self._lifeline_icon_sources.get(name)
        if icon_source is not None and Image is not None:
            icon_size = max(76, int(size * 0.86))
            resample = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
            icon = icon_source.resize((icon_size, icon_size), resample)
            if used:
                icon = icon.convert("LA").convert("RGBA")
            photo = ImageTk.PhotoImage(icon)
            self.lifeline_images[name] = photo
            canvas.create_image(cx, cy, image=photo)
        elif name == "5050":
            number_color = LIFELINE_USED if used else ACCENT_CYAN
            canvas.create_text(cx - int(14 * self.scale), cy - int(14 * self.scale), text="50", fill=number_color, font=self._font(27))
            canvas.create_text(cx + int(16 * self.scale), cy + int(16 * self.scale), text="50", fill=number_color, font=self._font(27))
        elif name == "2x":
            canvas.create_text(cx, cy, text="2X", fill=LIFELINE_USED if used else ACCENT_CYAN, font=self._font(24))
        else:
            canvas.create_text(cx, cy, text="P", fill=LIFELINE_USED if used else ACCENT_CYAN, font=self._font(24))

        if armed and not used:
            canvas.create_text(size // 2, int(size * 0.88), text="ON", fill=ACCENT_CYAN, font=self._font(11))

    def _clear_answer_buttons(self) -> None:
        for wrap in self.answer_wrappers.values():
            wrap.place_forget()
        self.hidden_answers = set()

    def _schedule_after(self, delay_ms: int, callback) -> None:
        job_id: str | None = None

        def runner() -> None:
            if job_id is not None:
                self._after_jobs.discard(job_id)
            if self.container.winfo_exists():
                callback()

        job_id = self.container.after(delay_ms, runner)
        self._after_jobs.add(job_id)

    def _cancel_pending_jobs(self) -> None:
        for job_id in list(self._after_jobs):
            try:
                self.container.after_cancel(job_id)
            except tk.TclError:
                pass
            self._after_jobs.discard(job_id)

    def _reset_question_state(self) -> None:
        self.pending_next_question = False
        self._clear_answer_buttons()

    def _set_badge_disabled(self, index: int) -> None:
        badge = self.answer_badges.get(index)
        if badge is None:
            return
        badge_canvas, oval_id, text_id = badge
        badge_canvas.itemconfigure(oval_id, outline=TEXT_MUTED, fill="#14183b", width=max(3, int(4 * self.scale)))
        badge_canvas.itemconfigure(text_id, fill=TEXT_MUTED)

    def _activate_lifeline(self, name: str) -> None:
        if self.current_question is None or self.pending_next_question:
            return

        if name == "5050":
            if self.lifeline_used["5050"]:
                self.feedback_label.configure(text=self.app.tr("game.lifeline.used_5050"))
                return
            self.lifeline_used["5050"] = True
            self._apply_fifty_fifty()
            self.feedback_label.configure(text=self.app.tr("game.lifeline.applied_5050"))
            self._draw_lifeline("5050")
            return

        if name == "2x":
            if self.lifeline_used["2x"]:
                self.feedback_label.configure(text=self.app.tr("game.lifeline.used_2x"))
                return
            self.lifeline_used["2x"] = True
            self.lifeline_armed["2x"] = True
            self.feedback_label.configure(text=self.app.tr("game.lifeline.applied_2x"))
            self._draw_lifeline("2x")
            return

        if self.lifeline_used["phoenix"]:
            self.feedback_label.configure(text=self.app.tr("game.lifeline.used_phoenix"))
            return
        if self.lifeline_armed["phoenix"]:
            self.feedback_label.configure(text=self.app.tr("game.lifeline.active_phoenix"))
            return
        self.lifeline_armed["phoenix"] = True
        self.feedback_label.configure(text=self.app.tr("game.lifeline.applied_phoenix"))
        self._draw_lifeline("phoenix")

    def _apply_fifty_fifty(self) -> None:
        if self.current_question is None:
            return
        wrong_indices = [index for index in range(4) if index != self.current_question.correct_index]
        removed = random.sample(wrong_indices, k=2)
        for index in removed:
            self.hidden_answers.add(index)
            button = self.answer_buttons.get(index)
            if button is not None:
                button.configure(state="disabled")
            self._set_badge_disabled(index)
        self._layout_answers()

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
        badge_canvas.itemconfigure(oval_id, outline=outline, fill=fill, width=max(3, int(4 * self.scale)))
        badge_canvas.itemconfigure(text_id, fill=text_color)

    def _set_answers_enabled(self, enabled: bool) -> None:
        for index, button in self.answer_buttons.items():
            if index in self.hidden_answers:
                continue
            button.configure(state="normal" if enabled else "disabled")

    def _set_question_text(self, prefix: str, body: str) -> None:
        self.question_prefix_label.configure(text=prefix)
        self.question_label.configure(text=body)

    def _format_amount(self, value: int) -> str:
        return f"{value:,}".replace(",", " ") + self.app.tr("game.currency_suffix")

    def _update_header_progress(self) -> None:
        current_step = min(self.level_index + 1, len(PRIZE_LEVELS))
        total_steps = len(PRIZE_LEVELS)
        self.progress_btn.configure(text=self.app.tr("game.round", current=current_step, total=total_steps))
        target_amount = PRIZE_LEVELS[min(self.level_index, len(PRIZE_LEVELS) - 1)][0]
        self.amount_btn.configure(text=self._format_amount(target_amount))

    def _layout_answers(self) -> None:
        badge_size = max(52, int(ANSWER_BADGE_SIZE * self.scale))
        button_w = max(340, int(ANSWER_BUTTON_SIZE[0] * self.scale))
        button_h = max(46, int(ANSWER_BUTTON_SIZE[1] * self.scale))
        button_gap = max(14, int(18 * self.scale))
        button_right_pad = max(6, int(8 * self.scale))

        visible_indices = [index for index in range(4) if index not in self.hidden_answers]
        if len(visible_indices) == 2:
            positions = list(ANSWER_TOP_LAYOUT.values())
        else:
            positions = [ANSWER_LAYOUT[index] for index in visible_indices]

        for index, wrap in self.answer_wrappers.items():
            if index in self.hidden_answers:
                wrap.place_forget()
                continue

            pos = positions[visible_indices.index(index)]
            x, y = pos
            x_px = int(x * self.scale)
            y_px = int(y * self.scale)
            wrap.place(
                x=x_px,
                y=y_px,
                width=badge_size + button_gap + button_w + button_right_pad,
                height=max(badge_size, button_h),
            )

            badge_canvas, _, _ = self.answer_badges[index]
            badge_canvas.configure(width=badge_size, height=badge_size)
            badge_canvas.place(x=0, y=max(0, (button_h - badge_size) // 2), width=badge_size, height=badge_size)
            oval_id = self.answer_badges[index][1]
            text_id = self.answer_badges[index][2]
            badge_canvas.coords(oval_id, 6, 6, badge_size - 6, badge_size - 6)
            badge_canvas.coords(text_id, badge_size // 2, badge_size // 2)
            badge_canvas.itemconfigure(text_id, font=self._font(26))
            button = self.answer_buttons[index]
            button.place(x=badge_size + button_gap, y=0, width=button_w, height=button_h)
            button.configure(
                font=self._font(15),
                height=button_h,
                radius=max(20, int(28 * self.scale)),
                border_width=max(2, int(3 * self.scale)),
            )

    def _load_question(self) -> None:
        self._reset_question_state()

        if self.level_index >= len(PRIZE_LEVELS):
            self._finish_game_win()
            return

        self._update_header_progress()
        _, difficulty = PRIZE_LEVELS[self.level_index]
        self.current_question = self.app.game_service.get_next_question(difficulty)
        if self.current_question is None:
            self._set_question_text(self.app.tr("game.error_title"), self.app.tr("game.error_questions", difficulty=difficulty.value))
            self.feedback_label.configure(text=self.app.tr("game.returning_menu"))
            self._schedule_after(1200, self.app.open_menu)
            return

        self._set_question_text(self.app.tr("game.question"), self.current_question.text)
        self.feedback_label.configure(text="")

        for index, button in self.answer_buttons.items():
            button.configure(text=self.current_question.options[index], state="normal")
            badge_canvas, oval_id, text_id = self.answer_badges[index]
            badge_canvas.itemconfigure(oval_id, outline=ACCENT_ORANGE, fill=CARD_BG, width=max(3, int(4 * self.scale)))
            badge_canvas.itemconfigure(text_id, fill=ACCENT_CYAN)

        self._layout_answers()

    def _finish_game_win(self) -> None:
        top_amount = PRIZE_LEVELS[-1][0]
        self._set_question_text(self.app.tr("game.finish_title"), self.app.tr("game.finish_text", amount=self._format_amount(top_amount)))
        self.feedback_label.configure(text=self.app.tr("game.finish"))
        self.progress_btn.configure(text=self.app.tr("game.round", current=len(PRIZE_LEVELS), total=len(PRIZE_LEVELS)))
        self.amount_btn.configure(text=self._format_amount(top_amount))

        if not self.result_saved:
            self.app.save_game_result("mixed", True)
            self.result_saved = True

        self._schedule_after(1400, self.app.open_menu)

    def _submit_answer(self, selected_index: int) -> None:
        if self.current_question is None or self.pending_next_question or selected_index in self.hidden_answers:
            return

        is_correct = self.app.game_service.submit_answer(selected_index)
        self._set_answers_enabled(False)
        self._mark_selected_badge(selected_index, is_correct)

        if is_correct:
            advance = 2 if self.lifeline_armed["2x"] else 1
            if self.lifeline_armed["2x"]:
                self.lifeline_armed["2x"] = False
                self._draw_lifeline("2x")
                self.feedback_label.configure(text=self.app.tr("game.correct_2x"))
            else:
                self.feedback_label.configure(text=self.app.tr("game.correct"))
            if self.lifeline_armed["phoenix"] and not self.lifeline_used["phoenix"]:
                self.lifeline_armed["phoenix"] = False
                self._draw_lifeline("phoenix")
            self.level_index += advance
            self._update_header_progress()
            self.pending_next_question = True
            self._schedule_after(450, self._load_question)
            return

        if self.lifeline_armed["phoenix"] and not self.lifeline_used["phoenix"]:
            self.lifeline_armed["phoenix"] = False
            self.lifeline_used["phoenix"] = True
            self.app.game_service.session.completed = False
            self._draw_lifeline("phoenix")
            self.feedback_label.configure(text=self.app.tr("game.lifeline.saved_phoenix"))
            self.pending_next_question = True
            self._schedule_after(700, self._load_question)
            return

        self.feedback_label.configure(text=self.app.tr("game.wrong_menu"))
        if not self.result_saved:
            self.app.save_game_result("mixed", False)
            self.result_saved = True
        self._schedule_after(900, self.app.open_menu)

    def _request_leave_game(self) -> None:
        if self.leave_dialog is not None and self.leave_dialog.winfo_exists():
            self.leave_dialog.lift()
            self.leave_dialog.focus_force()
            return
        self._open_leave_dialog()

    def _open_leave_dialog(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.configure(bg=BG_PURPLE)
        dialog.overrideredirect(True)
        dialog.grab_set()
        dialog.resizable(False, False)
        self.leave_dialog = dialog

        shell = tk.Frame(dialog, bg="#38108A", highlightthickness=2, highlightbackground=ACCENT_CYAN, bd=0)
        shell.pack(padx=18, pady=18)

        header = tk.Frame(shell, bg="#2C0E6B", height=44)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header,
            text=self.app.tr("game.leave.title"),
            bg="#2C0E6B",
            fg=TEXT_PRIMARY,
            font=("Arial", 16, "bold"),
        ).pack(expand=True)

        body = tk.Frame(shell, bg=CARD_BG, bd=0)
        body.pack(fill="both", expand=True, padx=16, pady=16)

        tk.Label(
            body,
            text=self.app.tr("game.leave.title"),
            bg=CARD_BG,
            fg=TEXT_PRIMARY,
            font=("Arial", 22, "bold"),
        ).pack(padx=28, pady=(18, 10))
        tk.Label(
            body,
            text=self.app.tr("game.leave.body"),
            bg=CARD_BG,
            fg=TEXT_SECONDARY,
            font=("Arial", 12),
            wraplength=360,
            justify="center",
        ).pack(padx=28, pady=(0, 22))

        buttons = tk.Frame(body, bg=CARD_BG)
        buttons.pack(padx=10, pady=(0, 8))

        tk.Button(
            buttons,
            text=self.app.tr("game.leave.stay"),
            command=self._close_leave_dialog,
            relief="flat",
            bd=0,
            bg="#171246",
            fg=TEXT_PRIMARY,
            activebackground="#20195C",
            activeforeground=TEXT_PRIMARY,
            highlightthickness=2,
            highlightbackground=ACCENT_CYAN,
            cursor="hand2",
            font=("Arial", 14, "bold"),
            width=12,
            pady=10,
        ).pack(side="left", padx=8)

        tk.Button(
            buttons,
            text=self.app.tr("game.leave.menu"),
            command=self._confirm_leave_to_menu,
            relief="flat",
            bd=0,
            bg="#171246",
            fg=ACCENT_CYAN,
            activebackground="#20195C",
            activeforeground=ACCENT_CYAN,
            highlightthickness=2,
            highlightbackground=ACCENT_CYAN,
            cursor="hand2",
            font=("Arial", 14, "bold"),
            width=12,
            pady=10,
        ).pack(side="left", padx=8)

        dialog.bind("<Escape>", lambda _event: self._close_leave_dialog())
        dialog.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def _close_leave_dialog(self) -> None:
        if self.leave_dialog is not None and self.leave_dialog.winfo_exists():
            self.leave_dialog.grab_release()
            self.leave_dialog.destroy()
        self.leave_dialog = None

    def _confirm_leave_to_menu(self) -> None:
        self._close_leave_dialog()
        self.app.open_menu()

    def _apply_scaled_layout(self) -> None:
        self.menu_btn.configure(font=self._font(17), height=max(42, int(MENU_SPEC[3] * self.scale)), radius=max(22, int(MENU_SPEC[4] * self.scale)))
        self.progress_btn.configure(font=self._font(19), height=max(42, int(PROGRESS_SPEC[3] * self.scale)), radius=max(22, int(PROGRESS_SPEC[4] * self.scale)))
        self.amount_btn.configure(font=self._font(19), height=max(42, int(AMOUNT_SPEC[3] * self.scale)), radius=max(22, int(AMOUNT_SPEC[4] * self.scale)))

        self._place_scaled(self.menu_btn, MENU_SPEC[:4])
        self._place_scaled(self.progress_btn, PROGRESS_SPEC[:4])
        self._place_scaled(self.amount_btn, AMOUNT_SPEC[:4])

        qx, qy, qw, qh = QUESTION_RECT
        self.question_wrap.place(x=int(qx * self.scale), y=int(qy * self.scale), width=max(300, int(qw * self.scale)), height=max(78, int(qh * self.scale)))
        self.question_prefix_label.configure(font=self._font(25))
        self.question_label.configure(font=self._font(21), wraplength=max(220, int((qw - 300) * self.scale)))
        self.question_prefix_label.place(x=int(28 * self.scale), y=int(26 * self.scale), height=max(24, int(30 * self.scale)))
        self.question_label.place(
            x=int(180 * self.scale),
            y=int(24 * self.scale),
            width=max(220, int((qw - 255) * self.scale)),
            height=max(26, int(34 * self.scale)),
        )

        feedback_y = int(646 * self.scale)
        self.feedback_label.configure(font=self._font(12))
        self.feedback_label.place(x=int(0.18 * self.stage_width), y=feedback_y, width=int(0.64 * self.stage_width))

        for name, center in LIFELINE_CENTERS.items():
            cx, cy = center
            size = max(82, int(160 * self.scale))
            self.lifeline_canvases[name].place(x=int(cx * self.scale - size / 2), y=int(cy * self.scale - size / 2), width=size, height=size)
            self._draw_lifeline(name)

        self._layout_answers()

    def on_resize(self, width: int, height: int) -> None:
        self.scale, self.stage_left, self.stage_top, self.stage_width, self.stage_height = self._fit_stage(width, height)
        self.canvas.coords(self.stage_window, self.stage_left, self.stage_top)
        self.canvas.itemconfigure(self.stage_window, width=self.stage_width, height=self.stage_height)
        self.stage_frame.configure(width=self.stage_width, height=self.stage_height)
        self._apply_scaled_layout()

    def _on_canvas_configure(self, event: tk.Event) -> None:
        if event.width <= 1 or event.height <= 1:
            return
        self.on_resize(event.width, event.height)

    def on_escape(self) -> None:
        self._request_leave_game()

    def on_destroy(self) -> None:
        self._cancel_pending_jobs()
        self._close_leave_dialog()

    def on_language_changed(self) -> None:
        self.menu_btn.configure(text=self.app.tr("common.menu"))
        self.question_prefix_label.configure(text=self.app.tr("game.question"))
        if self.current_question is not None:
            self._set_question_text(self.app.tr("game.question"), self.current_question.text)
        self._update_header_progress()


class GameApp:
    theme: object
    width: int
    height: int
    game_service: object

    def open_menu(self) -> None:
        raise NotImplementedError

    def save_game_result(self, difficulty: Difficulty | str, is_win: bool) -> None:
        raise NotImplementedError
