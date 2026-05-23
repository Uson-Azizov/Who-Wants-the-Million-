from __future__ import annotations

import tkinter as tk

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
CARD_COLOR = "#34107D"
CARD_SHADOW = "#240759"
ACCENT = "#62BDD0"
BUTTON_FILL = "#070534"
TEXT_PRIMARY = "#FFFFFF"
TEXT_MUTED = "#D9D6E8"
TEXT_HINT = "#B7AED9"
INPUT_TEXT = "#1F1F1F"

MENU_BUTTON = (-126, 34, 412, 122, 61)
LOGO_RECT = (1257, 11, 172, 171)
CARD_RECT = (546, 178, 438, 538, 24)


class AdminLoginScreen(Screen):
    def __init__(self, app: "AdminLoginApp") -> None:
        super().__init__(app)

        self.canvas = tk.Canvas(self.container, highlightthickness=0, bd=0, bg=BACKGROUND_COLOR, cursor="arrow")
        self.canvas.pack(fill="both", expand=True)

        self.logo_source = self._load_logo_source()
        self.logo_image: ImageTk.PhotoImage | tk.PhotoImage | None = None
        self.scale = 1.0
        self.stage_left = 0
        self.stage_top = 0
        self.menu_bounds: tuple[float, float, float, float] | None = None
        self.menu_hovered = False
        self.card_window_id: int | None = None

        self.login_var = tk.StringVar()
        self.code_var = tk.StringVar()
        self.remember_var = tk.BooleanVar(value=False)
        self.message_var = tk.StringVar(value="")

        self.card_frame = tk.Frame(self.canvas, bg=CARD_COLOR, bd=0, highlightthickness=0)
        self.card_frame.grid_propagate(False)
        self.content_frame = tk.Frame(self.card_frame, bg=CARD_COLOR, bd=0, highlightthickness=0)

        self.title_label = tk.Label(self.content_frame, text="Sign in", bg=CARD_COLOR, fg=TEXT_PRIMARY)
        self.subtitle_label = tk.Label(
            self.content_frame,
            text="Sign in and start managing your candidates!",
            bg=CARD_COLOR,
            fg=TEXT_MUTED,
        )
        self.login_entry = tk.Entry(
            self.content_frame,
            textvariable=self.login_var,
            relief="flat",
            bd=0,
            fg=INPUT_TEXT,
            bg="#FFFFFF",
            insertbackground=INPUT_TEXT,
        )
        self.code_entry = tk.Entry(
            self.content_frame,
            textvariable=self.code_var,
            relief="flat",
            bd=0,
            fg=INPUT_TEXT,
            bg="#FFFFFF",
            insertbackground=INPUT_TEXT,
            show="*",
        )
        self.options_frame = tk.Frame(self.content_frame, bg=CARD_COLOR, bd=0, highlightthickness=0)
        self.remember_check = tk.Checkbutton(
            self.options_frame,
            text="Remember me",
            variable=self.remember_var,
            bg=CARD_COLOR,
            fg=TEXT_PRIMARY,
            activebackground=CARD_COLOR,
            activeforeground=TEXT_PRIMARY,
            selectcolor=BUTTON_FILL,
            highlightthickness=0,
            bd=0,
            anchor="w",
        )
        self.forgot_label = tk.Label(
            self.options_frame,
            text="Forgot password?",
            bg=CARD_COLOR,
            fg=TEXT_HINT,
        )
        self.submit_button = tk.Button(
            self.content_frame,
            text="Start As Admin",
            command=self._submit,
            relief="flat",
            bd=0,
            bg=BUTTON_FILL,
            fg="#F2E8D2",
            activebackground=BUTTON_FILL,
            activeforeground="#F2E8D2",
            cursor="hand2",
            highlightthickness=0,
        )
        self.message_label = tk.Label(
            self.content_frame,
            textvariable=self.message_var,
            bg=CARD_COLOR,
            fg=TEXT_MUTED,
            justify="center",
        )

        self._build_card()

        self.login_entry.bind("<Return>", lambda _event: self._submit())
        self.code_entry.bind("<Return>", lambda _event: self._submit())
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.bind("<Button-1>", self._on_press)

        self.on_resize(self.app.width, self.app.height)

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

    def _build_card(self) -> None:
        self.content_frame.pack(fill="both", expand=True, padx=34, pady=34)
        self.content_frame.grid_columnconfigure(0, weight=1)

        self.title_label.grid(row=0, column=0, sticky="ew", pady=(6, 8))
        self.subtitle_label.grid(row=1, column=0, sticky="ew", pady=(0, 30))

        self.login_entry.grid(row=2, column=0, sticky="ew", ipady=12, pady=(0, 18))
        self.code_entry.grid(row=3, column=0, sticky="ew", ipady=12, pady=(0, 22))

        self.options_frame.grid(row=4, column=0, sticky="ew", pady=(0, 26))
        self.options_frame.grid_columnconfigure(0, weight=1)
        self.options_frame.grid_columnconfigure(1, weight=1)
        self.remember_check.grid(row=0, column=0, sticky="w")
        self.forgot_label.grid(row=0, column=1, sticky="e")

        self.submit_button.grid(row=5, column=0, sticky="ew", ipady=11)
        self.message_label.grid(row=6, column=0, sticky="ew", pady=(18, 0))

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

    def _draw_waves(self) -> None:
        bottom = self._sy(DESIGN_HEIGHT)
        left = self._sx(0)
        right = self._sx(DESIGN_WIDTH)
        self.canvas.create_polygon(
            self._sx(0),
            bottom,
            self._sx(0),
            self._sy(915),
            self._sx(220),
            self._sy(962),
            self._sx(530),
            self._sy(1002),
            self._sx(875),
            self._sy(955),
            self._sx(1112),
            self._sy(979),
            right,
            self._sy(956),
            right,
            bottom,
            fill="#4A3A9B",
            outline="",
            tags="bg",
        )
        self.canvas.create_polygon(
            left,
            bottom,
            left,
            self._sy(979),
            self._sx(310),
            self._sy(1021),
            self._sx(666),
            self._sy(966),
            self._sx(830),
            self._sy(1010),
            self._sx(1172),
            self._sy(968),
            right,
            self._sy(999),
            right,
            bottom,
            fill="#5E4AAC",
            outline="",
            tags="bg",
        )

    def _layout_card(self) -> None:
        x, y, w, h, radius = CARD_RECT
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
            fill=CARD_SHADOW,
        )
        self._create_round_rect(
            x1,
            y1,
            x2,
            y2,
            radius * self.scale,
            fill=CARD_COLOR,
        )

        frame_w = max(320, int(w * self.scale))
        frame_h = max(420, int(h * self.scale))
        self.card_frame.configure(width=frame_w, height=frame_h)

        if self.card_window_id is None:
            self.card_window_id = self.canvas.create_window(
                x1,
                y1,
                window=self.card_frame,
                anchor="nw",
            )
        else:
            self.canvas.coords(self.card_window_id, x1, y1)

        self.canvas.tag_raise(self.card_window_id)

        self.title_label.configure(font=self._font(54))
        self.subtitle_label.configure(font=self._font(14))
        self.login_entry.configure(font=self._font(18), justify="left")
        self.code_entry.configure(font=self._font(18), justify="left")
        self.remember_check.configure(font=self._font(14))
        self.forgot_label.configure(font=self._font(12))
        self.submit_button.configure(font=self._font(22))
        self.message_label.configure(font=self._font(12))

    def _draw_screen(self) -> None:
        self.canvas.delete("bg")
        self.menu_bounds = None
        self.canvas.create_rectangle(0, 0, self.app.width, self.app.height, fill=BACKGROUND_COLOR, outline="", tags="bg")
        self._draw_menu_button()
        self._draw_logo()
        self._draw_waves()
        self._layout_card()

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
        self._draw_screen()

    def _on_motion(self, event: tk.Event) -> None:
        hovered = self._hit_test(event.x, event.y) == "menu"
        self.canvas.configure(cursor="hand2" if hovered else "arrow")
        if hovered != self.menu_hovered:
            self.menu_hovered = hovered
            self._draw_screen()

    def _on_press(self, event: tk.Event) -> None:
        if self._hit_test(event.x, event.y) == "menu":
            self.app.open_menu()

    def _submit(self) -> None:
        login = self.login_var.get().strip()
        code = self.code_var.get().strip()
        if not login or not code:
            self.message_var.set("Введите login и admins code.")
            return

        success, message = self.app.verify_admin_login(login, code)
        self.app.status_text_var.set(message)
        if success:
            self.message_var.set("Вход выполнен")
            self.root.after(150, self.app.open_admin_panel)
            return
        self.message_var.set(message)

    def on_resize(self, width: int, height: int) -> None:
        self.scale, self.stage_left, self.stage_top = self._fit_stage(width, height)
        self._draw_screen()

    def on_escape(self) -> None:
        self.app.open_settings()


class AdminLoginApp:
    width: int
    height: int
    status_text_var: tk.StringVar

    def open_menu(self) -> None:
        raise NotImplementedError

    def open_settings(self) -> None:
        raise NotImplementedError

    def verify_admin_login(self, login: str, code: str) -> tuple[bool, str]:
        raise NotImplementedError

    def open_admin_panel(self) -> None:
        raise NotImplementedError
