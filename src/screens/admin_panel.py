from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from src.config import MENU_LOGO_IMAGE_PATH
from src.screens.base import Screen

try:
    from PIL import Image, ImageTk
except Exception:  # pragma: no cover - optional dependency
    Image = None
    ImageTk = None


DESIGN_WIDTH = 1440
DESIGN_HEIGHT = 1024
BACKGROUND_COLOR = "#29007A"
PANEL_COLOR = "#34107D"
PANEL_SHADOW = "#240759"
BUTTON_FILL = "#070534"
ACCENT = "#62BDD0"
TEXT_PRIMARY = "#FFFFFF"
TEXT_MUTED = "#D9D6E8"
ENTRY_BG = "#FFFFFF"
ENTRY_TEXT = "#1F1F1F"

MENU_BUTTON = (-126, 34, 412, 122, 61)
LOGO_RECT = (1257, 11, 172, 171)
LEFT_PANEL_RECT = (72, 190, 720, 650, 24)
RIGHT_PANEL_RECT = (836, 190, 532, 650, 24)


class AdminPanelScreen(Screen):
    def __init__(self, app: "AdminPanelApp") -> None:
        super().__init__(app)

        self.container.configure(bg=BACKGROUND_COLOR)
        self.canvas = tk.Canvas(self.container, bg=BACKGROUND_COLOR, highlightthickness=0, bd=0, cursor="arrow")
        self.canvas.pack(fill="both", expand=True)

        self.logo_source = self._load_logo_source()
        self.logo_image: ImageTk.PhotoImage | tk.PhotoImage | None = None
        self.scale = 1.0
        self.stage_left = 0
        self.stage_top = 0
        self.menu_bounds: tuple[float, float, float, float] | None = None
        self.menu_hovered = False

        self.message_var = tk.StringVar(value="")
        self.details_var = tk.StringVar(value="Выберите вопрос слева, чтобы увидеть правильный ответ и варианты.")
        self.difficulty_var = tk.StringVar(value="easy")
        self.correct_var = tk.StringVar(value="A")
        self.option_vars = {key: tk.StringVar() for key in ("A", "B", "C", "D")}
        self.question_entries = []

        self.left_panel = tk.Frame(self.canvas, bg=PANEL_COLOR, bd=0, highlightthickness=0)
        self.right_panel = tk.Frame(self.canvas, bg=PANEL_COLOR, bd=0, highlightthickness=0)
        self.left_panel.grid_propagate(False)
        self.right_panel.grid_propagate(False)
        self.left_window_id: int | None = None
        self.right_window_id: int | None = None

        self.tree = ttk.Treeview(
            self.left_panel,
            columns=("difficulty", "question", "answer"),
            show="headings",
            height=14,
        )
        self.scrollbar = ttk.Scrollbar(self.left_panel, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.tree.heading("difficulty", text="Level")
        self.tree.heading("question", text="Question")
        self.tree.heading("answer", text="Correct")
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        self.left_title = tk.Label(self.left_panel, text="Question Bank", bg=PANEL_COLOR, fg=TEXT_PRIMARY)
        self.left_subtitle = tk.Label(
            self.left_panel,
            text="All questions with answers from your SQL database",
            bg=PANEL_COLOR,
            fg=TEXT_MUTED,
            anchor="w",
            justify="left",
        )
        self.details_label = tk.Label(
            self.left_panel,
            textvariable=self.details_var,
            bg=PANEL_COLOR,
            fg=TEXT_MUTED,
            anchor="nw",
            justify="left",
        )

        self.right_title = tk.Label(self.right_panel, text="Add Question", bg=PANEL_COLOR, fg=TEXT_PRIMARY)
        self.right_subtitle = tk.Label(
            self.right_panel,
            text="Create a new question for the game right from admin mode",
            bg=PANEL_COLOR,
            fg=TEXT_MUTED,
            anchor="w",
            justify="left",
        )
        self.form_frame = tk.Frame(self.right_panel, bg=PANEL_COLOR, bd=0, highlightthickness=0)

        self.question_text = tk.Text(self.form_frame, wrap="word", relief="flat", bd=0)
        self.status_label = tk.Label(
            self.right_panel,
            textvariable=self.message_var,
            bg=PANEL_COLOR,
            fg=TEXT_PRIMARY,
            justify="left",
            anchor="w",
        )

        self._style_tree()
        self._build_panels()

        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.bind("<Button-1>", self._on_press)

        self.on_resize(self.app.width, self.app.height)
        self.refresh_questions()

    def _load_logo_source(self):
        if not MENU_LOGO_IMAGE_PATH.exists():
            return None
        if Image is not None:
            try:
                return Image.open(MENU_LOGO_IMAGE_PATH).convert("RGBA")
            except Exception:
                return None
        try:
            return tk.PhotoImage(file=str(MENU_LOGO_IMAGE_PATH))
        except tk.TclError:
            return None

    @staticmethod
    def _fit_stage(width: int, height: int) -> tuple[float, int, int]:
        scale = min(width / DESIGN_WIDTH, height / DESIGN_HEIGHT)
        stage_width = int(DESIGN_WIDTH * scale)
        stage_height = int(DESIGN_HEIGHT * scale)
        left = (width - stage_width) // 2
        top = (height - stage_height) // 2
        return scale, left, top

    def _font(self, size: int, weight: str = "normal") -> tuple[str, int, str]:
        return ("Arial", max(10, int(size * self.scale * 0.82)), weight)

    def _sx(self, value: float) -> float:
        return self.stage_left + value * self.scale

    def _sy(self, value: float) -> float:
        return self.stage_top + value * self.scale

    def _create_round_rect(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        radius: float,
        *,
        fill: str,
        outline: str = "",
        width: float = 1,
        tags: str = "bg",
    ) -> None:
        r = max(0.0, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))
        if r == 0:
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline=outline, width=width, tags=tags)
            return

        self.canvas.create_rectangle(x1 + r, y1, x2 - r, y2, fill=fill, outline="", tags=tags)
        self.canvas.create_rectangle(x1, y1 + r, x2, y2 - r, fill=fill, outline="", tags=tags)
        corners = [
            (x1, y1, x1 + 2 * r, y1 + 2 * r, 90),
            (x2 - 2 * r, y1, x2, y1 + 2 * r, 0),
            (x2 - 2 * r, y2 - 2 * r, x2, y2, 270),
            (x1, y2 - 2 * r, x1 + 2 * r, y2, 180),
        ]
        for cx1, cy1, cx2, cy2, start in corners:
            self.canvas.create_arc(
                cx1,
                cy1,
                cx2,
                cy2,
                start=start,
                extent=90,
                style="pieslice",
                fill=fill,
                outline="",
                tags=tags,
            )
        if outline:
            self.canvas.create_line(x1 + r, y1, x2 - r, y1, fill=outline, width=width, tags=tags)
            self.canvas.create_line(x2, y1 + r, x2, y2 - r, fill=outline, width=width, tags=tags)
            self.canvas.create_line(x1 + r, y2, x2 - r, y2, fill=outline, width=width, tags=tags)
            self.canvas.create_line(x1, y1 + r, x1, y2 - r, fill=outline, width=width, tags=tags)
            for cx1, cy1, cx2, cy2, start in corners:
                self.canvas.create_arc(
                    cx1,
                    cy1,
                    cx2,
                    cy2,
                    start=start,
                    extent=90,
                    style="arc",
                    outline=outline,
                    width=width,
                    tags=tags,
                )

    def _style_tree(self) -> None:
        style = ttk.Style()
        style.configure(
            "Admin.Treeview",
            background="#1F1450",
            foreground=TEXT_PRIMARY,
            fieldbackground="#1F1450",
            borderwidth=0,
            rowheight=28,
            relief="flat",
        )
        style.configure(
            "Admin.Treeview.Heading",
            background="#110A33",
            foreground=TEXT_PRIMARY,
            relief="flat",
        )
        style.map("Admin.Treeview", background=[("selected", "#3B1E81")], foreground=[("selected", TEXT_PRIMARY)])
        self.tree.configure(style="Admin.Treeview")

    def _build_panels(self) -> None:
        self.left_title.place(x=28, y=24)
        self.left_subtitle.place(x=28, y=68)
        self.tree.place(x=28, y=108)
        self.scrollbar.place(y=108)
        self.details_label.place(x=28)

        self.right_title.place(x=28, y=24)
        self.right_subtitle.place(x=28, y=68)
        self.form_frame.place(x=28, y=112)
        self.status_label.place(x=28)

    def _draw_logo(self) -> None:
        if self.logo_source is None:
            return

        x, y, w, h = LOGO_RECT
        width = max(40, int(w * self.scale))
        height = max(40, int(h * self.scale))

        if Image is not None and hasattr(self.logo_source, "resize"):
            resample = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
            resized = self.logo_source.resize((width, height), resample)
            self.logo_image = ImageTk.PhotoImage(resized)
        else:
            self.logo_image = self.logo_source

        self.canvas.create_image(self._sx(x), self._sy(y), image=self.logo_image, anchor="nw", tags="bg")

    def _draw_menu_button(self) -> None:
        x, y, w, h, radius = MENU_BUTTON
        x1 = self._sx(x)
        y1 = self._sy(y)
        x2 = x1 + w * self.scale
        y2 = y1 + h * self.scale
        border = ACCENT if not self.menu_hovered else "#8EDDE8"
        self._create_round_rect(
            x1,
            y1,
            x2,
            y2,
            radius * self.scale,
            fill=BUTTON_FILL,
            outline=border,
            width=max(4, int(8 * self.scale * 0.65)),
        )
        self.canvas.create_text(
            (x1 + x2) / 2,
            (y1 + y2) / 2,
            text="Menu",
            fill=TEXT_PRIMARY,
            font=self._font(50, "bold"),
            tags="bg",
        )
        self.menu_bounds = (x1, y1, x2, y2)

    def _draw_background(self) -> None:
        self.canvas.delete("bg")
        self.canvas.create_rectangle(0, 0, self.app.width, self.app.height, fill=BACKGROUND_COLOR, outline="", tags="bg")
        self._draw_menu_button()
        self._draw_logo()
        self._draw_panel_boxes()

    def _draw_panel_boxes(self) -> None:
        for rect in (LEFT_PANEL_RECT, RIGHT_PANEL_RECT):
            x, y, w, h, radius = rect
            x1 = self._sx(x)
            y1 = self._sy(y)
            x2 = self._sx(x + w)
            y2 = self._sy(y + h)
            self._create_round_rect(
                x1 + 10 * self.scale,
                y1 + 12 * self.scale,
                x2 + 10 * self.scale,
                y2 + 12 * self.scale,
                radius * self.scale,
                fill=PANEL_SHADOW,
            )
            self._create_round_rect(
                x1,
                y1,
                x2,
                y2,
                radius * self.scale,
                fill=PANEL_COLOR,
            )

    def _layout_windows(self) -> None:
        left_x, left_y, left_w, left_h, _ = LEFT_PANEL_RECT
        right_x, right_y, right_w, right_h, _ = RIGHT_PANEL_RECT

        left_x_px = self._sx(left_x)
        left_y_px = self._sy(left_y)
        left_w_px = max(540, int(left_w * self.scale))
        left_h_px = max(480, int(left_h * self.scale))
        right_x_px = self._sx(right_x)
        right_y_px = self._sy(right_y)
        right_w_px = max(390, int(right_w * self.scale))
        right_h_px = max(480, int(right_h * self.scale))

        self.left_panel.configure(width=left_w_px, height=left_h_px)
        self.right_panel.configure(width=right_w_px, height=right_h_px)

        if self.left_window_id is None:
            self.left_window_id = self.canvas.create_window(left_x_px, left_y_px, window=self.left_panel, anchor="nw")
        else:
            self.canvas.coords(self.left_window_id, left_x_px, left_y_px)

        if self.right_window_id is None:
            self.right_window_id = self.canvas.create_window(right_x_px, right_y_px, window=self.right_panel, anchor="nw")
        else:
            self.canvas.coords(self.right_window_id, right_x_px, right_y_px)

        self._apply_left_layout(left_w_px, left_h_px)
        self._apply_right_layout(right_w_px, right_h_px)

    def _apply_left_layout(self, width: int, height: int) -> None:
        self.left_title.configure(font=self._font(30, "bold"))
        self.left_subtitle.configure(font=self._font(13), wraplength=width - 56)
        self.details_label.configure(font=self._font(13), wraplength=width - 56)

        tree_y = int(112 * self.scale)
        tree_h = max(220, height - int(292 * self.scale))
        tree_w = max(320, width - 72)

        self.tree.place(x=28, y=tree_y, width=tree_w - 22, height=tree_h)
        self.scrollbar.place(x=width - 46, y=tree_y, width=18, height=tree_h)
        self.details_label.place(x=28, y=tree_y + tree_h + 18, width=tree_w)

        self.tree.column("difficulty", width=max(90, int(110 * self.scale)), anchor="center")
        self.tree.column("question", width=max(200, int((tree_w - 160) * 0.62)), anchor="w")
        self.tree.column("answer", width=max(120, int((tree_w - 160) * 0.38)), anchor="w")

    def _apply_right_layout(self, width: int, height: int) -> None:
        self.right_title.configure(font=self._font(30, "bold"))
        self.right_subtitle.configure(font=self._font(13), wraplength=width - 56)
        self.status_label.configure(font=self._font(12), wraplength=width - 56)
        self.form_frame.place(x=28, y=112, width=width - 56, height=height - 210)
        self.status_label.place(x=28, y=height - 72, width=width - 56)
        self._build_form(width - 56)

    def _build_form(self, form_width: int) -> None:
        cached_question = self.question_text.get("1.0", "end-1c") if self.question_text.winfo_exists() else ""
        for child in self.form_frame.winfo_children():
            child.destroy()

        entry_font = self._font(13)
        label_font = self._font(13, "bold")
        row = 0
        self.form_frame.grid_columnconfigure(0, weight=1)

        tk.Label(self.form_frame, text="Difficulty", bg=PANEL_COLOR, fg=TEXT_MUTED, font=label_font).grid(row=row, column=0, sticky="w", pady=(0, 6))
        row += 1
        difficulty_menu = ttk.Combobox(
            self.form_frame,
            textvariable=self.difficulty_var,
            values=("easy", "medium", "hard"),
            state="readonly",
            font=entry_font,
        )
        difficulty_menu.grid(row=row, column=0, sticky="ew", pady=(0, 16))
        row += 1

        tk.Label(self.form_frame, text="Question", bg=PANEL_COLOR, fg=TEXT_MUTED, font=label_font).grid(row=row, column=0, sticky="w", pady=(0, 6))
        row += 1
        self.question_text = tk.Text(
            self.form_frame,
            height=5,
            wrap="word",
            relief="flat",
            bd=0,
            bg=ENTRY_BG,
            fg=ENTRY_TEXT,
            insertbackground=ENTRY_TEXT,
            font=entry_font,
        )
        self.question_text.grid(row=row, column=0, sticky="ew", pady=(0, 16))
        if cached_question:
            self.question_text.insert("1.0", cached_question)
        row += 1

        self.question_entries = []
        for key in ("A", "B", "C", "D"):
            tk.Label(self.form_frame, text=f"Option {key}", bg=PANEL_COLOR, fg=TEXT_MUTED, font=label_font).grid(row=row, column=0, sticky="w", pady=(0, 6))
            row += 1
            entry = tk.Entry(
                self.form_frame,
                textvariable=self.option_vars[key],
                relief="flat",
                bd=0,
                bg=ENTRY_BG,
                fg=ENTRY_TEXT,
                insertbackground=ENTRY_TEXT,
                font=entry_font,
            )
            entry.grid(row=row, column=0, sticky="ew", pady=(0, 12), ipady=8)
            self.question_entries.append(entry)
            row += 1

        footer = tk.Frame(self.form_frame, bg=PANEL_COLOR, bd=0, highlightthickness=0)
        footer.grid(row=row, column=0, sticky="ew", pady=(8, 0))
        footer.grid_columnconfigure(1, weight=1)
        tk.Label(footer, text="Correct answer", bg=PANEL_COLOR, fg=TEXT_MUTED, font=label_font).grid(row=0, column=0, sticky="w", padx=(0, 12))
        correct_menu = ttk.Combobox(
            footer,
            textvariable=self.correct_var,
            values=("A", "B", "C", "D"),
            state="readonly",
            width=8,
            font=entry_font,
        )
        correct_menu.grid(row=0, column=1, sticky="w")
        row += 1

        add_button = tk.Button(
            self.form_frame,
            text="Add Question",
            command=self._add_question,
            relief="flat",
            bd=0,
            bg=BUTTON_FILL,
            fg=ACCENT,
            activebackground="#10105D",
            activeforeground=ACCENT,
            cursor="hand2",
            font=self._font(18, "bold"),
        )
        add_button.grid(row=row, column=0, sticky="ew", pady=(18, 0), ipady=10)

    def _hit_test(self, x: float, y: float) -> str | None:
        if self.menu_bounds is not None:
            x1, y1, x2, y2 = self.menu_bounds
            if x1 <= x <= x2 and y1 <= y <= y2:
                return "menu"
        return None

    def _on_leave(self, _event: tk.Event) -> None:
        if not self.menu_hovered:
            return
        self.menu_hovered = False
        self.canvas.configure(cursor="arrow")
        self._draw_background()

    def _on_motion(self, event: tk.Event) -> None:
        hovered = self._hit_test(event.x, event.y) == "menu"
        self.canvas.configure(cursor="hand2" if hovered else "arrow")
        if hovered != self.menu_hovered:
            self.menu_hovered = hovered
            self._draw_background()

    def _on_press(self, event: tk.Event) -> None:
        if self._hit_test(event.x, event.y) == "menu":
            self.app.open_settings()

    def refresh_questions(self) -> None:
        entries, message = self.app.get_admin_questions()
        self.tree.delete(*self.tree.get_children())
        if entries is None:
            self.message_var.set(message)
            self.details_var.set(message)
            return

        self._entries_by_item: dict[str, object] = {}
        for entry in entries:
            options = [entry.option_a, entry.option_b, entry.option_c, entry.option_d]
            correct_answer = options[entry.correct_index] if 0 <= entry.correct_index < 4 else ""
            item_id = self.tree.insert("", "end", values=(entry.difficulty, entry.question_text, correct_answer))
            self._entries_by_item[item_id] = entry
        self.message_var.set(f"Loaded {len(entries)} questions")
        self.details_var.set("Выберите вопрос слева, чтобы увидеть варианты A/B/C/D и правильный ответ.")

    def _on_tree_select(self, _event: tk.Event) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        entry = self._entries_by_item.get(selected[0])
        if entry is None:
            return
        options = [
            f"A: {entry.option_a}",
            f"B: {entry.option_b}",
            f"C: {entry.option_c}",
            f"D: {entry.option_d}",
        ]
        correct_key = ["A", "B", "C", "D"][entry.correct_index] if 0 <= entry.correct_index < 4 else "?"
        self.details_var.set(
            f"{entry.question_text}\n\n"
            + "\n".join(options)
            + f"\n\nCorrect answer: {correct_key}"
        )

    def _add_question(self) -> None:
        question_text = self.question_text.get("1.0", "end").strip()
        options = [self.option_vars[key].get().strip() for key in ("A", "B", "C", "D")]
        if not question_text:
            self.message_var.set("Введите текст вопроса")
            return
        if any(not option for option in options):
            self.message_var.set("Заполните все 4 варианта ответа")
            return

        correct_index = ["A", "B", "C", "D"].index(self.correct_var.get())
        success, message = self.app.add_admin_question(
            difficulty=self.difficulty_var.get(),
            question_text=question_text,
            options=options,
            correct_index=correct_index,
        )
        self.message_var.set(message)
        if not success:
            return

        self.question_text.delete("1.0", "end")
        for var in self.option_vars.values():
            var.set("")
        self.correct_var.set("A")
        self.refresh_questions()

    def on_resize(self, width: int, height: int) -> None:
        self.scale, self.stage_left, self.stage_top = self._fit_stage(width, height)
        self._draw_background()
        self._layout_windows()

    def on_escape(self) -> None:
        self.app.open_settings()


class AdminPanelApp:
    width: int
    height: int

    def open_settings(self) -> None:
        raise NotImplementedError

    def get_admin_questions(self):
        raise NotImplementedError

    def add_admin_question(
        self,
        *,
        difficulty: str,
        question_text: str,
        options: list[str],
        correct_index: int,
    ) -> tuple[bool, str]:
        raise NotImplementedError
