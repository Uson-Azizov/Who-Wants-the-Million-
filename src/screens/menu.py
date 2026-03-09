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
            darken_alpha=62,
            drift_x=1,
            drift_y=1,
            show_scanline=False,
        )

        self._build_static_elements()
        self._build_buttons()

        self.background.start()
        self.on_resize(self.app.width, self.app.height)

    def _build_static_elements(self) -> None:
        self.title_main_glow_id = self.canvas.create_text(
            0,
            0,
            text="Who Wants to Be a",
            fill="#7fd4ff",
            font=("Arial", 58, "bold"),
            anchor="nw",
        )
        self.title_highlight_glow_id = self.canvas.create_text(
            0,
            0,
            text="Millionaire",
            fill="#6fe8ff",
            font=("Arial", 58, "bold"),
            anchor="nw",
        )

        self.title_main_id = self.canvas.create_text(
            0,
            0,
            text="Who Wants to Be a",
            fill="#ffffff",
            font=("Arial", 58, "bold"),
            anchor="nw",
        )
        self.title_highlight_id = self.canvas.create_text(
            0,
            0,
            text="Millionaire",
            fill="#35deff",
            font=("Arial", 58, "bold"),
            anchor="nw",
        )

        self.logo_outer_id = self.canvas.create_oval(0, 0, 0, 0, outline="#f6de71", width=5, fill="#2d3569")
        self.logo_inner_id = self.canvas.create_oval(0, 0, 0, 0, outline="#f9ebb2", width=3, fill="#1d2557")
        self.logo_text_id = self.canvas.create_text(
            0,
            0,
            text="MINDSET\nMILLIONAIRE",
            fill="#ffefad",
            font=("Arial", 18, "bold"),
            justify="center",
        )

        self.status_id = self.canvas.create_text(
            0,
            0,
            text="",
            fill="#a9c9f3",
            font=("Arial", 11),
            anchor="n",
        )
        self.hint_id = self.canvas.create_text(
            0,
            0,
            text="F11 - fullscreen",
            fill="#a6cbf6",
            font=("Arial", 12),
            anchor="se",
        )

    def _build_buttons(self) -> None:
        style = dict(
            theme=self.app.theme,
            font=("Arial", 20, "bold"),
            width=30,
            height=62,
            radius=19,
            bg_color="#070742",
            hover_color="#111b69",
            border_color="#dceaff",
            text_color="#34d5ff",
            canvas_bg="#062460",
        )

        self.play_btn = GlassButton(self.container, text="Играть", command=self.app.start_game, **style)
        self.settings_btn = GlassButton(self.container, text="Настройки", command=self.app.open_settings, **style)
        self.exit_btn = GlassButton(self.container, text="Выход", command=self.app.quit, **style)

        self.records_btn = GlassButton(
            self.container,
            text="Рекорды",
            command=self.app.open_leaderboard,
            theme=self.app.theme,
            font=("Arial", 13, "bold"),
            width=16,
            height=42,
            radius=14,
            bg_color="#091645",
            hover_color="#12306f",
            border_color="#89bfff",
            text_color="#9ee8ff",
            canvas_bg="#062460",
        )

        self.play_btn_id = self.canvas.create_window(0, 0, window=self.play_btn, anchor="n")
        self.settings_btn_id = self.canvas.create_window(0, 0, window=self.settings_btn, anchor="n")
        self.exit_btn_id = self.canvas.create_window(0, 0, window=self.exit_btn, anchor="n")
        self.records_btn_id = self.canvas.create_window(0, 0, window=self.records_btn, anchor="n")

    def on_resize(self, width: int, height: int) -> None:
        center_x = width // 2

        title_y = int(height * 0.08)
        self.canvas.coords(self.title_main_id, 0, title_y)
        self.canvas.coords(self.title_highlight_id, 0, title_y)
        self.canvas.coords(self.title_main_glow_id, 0, title_y)
        self.canvas.coords(self.title_highlight_glow_id, 0, title_y)
        main_bbox = self.canvas.bbox(self.title_main_id)
        high_bbox = self.canvas.bbox(self.title_highlight_id)
        if main_bbox and high_bbox:
            main_w = main_bbox[2] - main_bbox[0]
            high_w = high_bbox[2] - high_bbox[0]
            gap = 18
            start_x = center_x - (main_w + gap + high_w) // 2
            self.canvas.coords(self.title_main_id, start_x, title_y)
            self.canvas.coords(self.title_highlight_id, start_x + main_w + gap, title_y)
            self.canvas.coords(self.title_main_glow_id, start_x - 1, title_y - 1)
            self.canvas.coords(self.title_highlight_glow_id, start_x + main_w + gap - 1, title_y - 1)

        logo_size = int(min(width, height) * 0.19)
        logo_top = int(height * 0.30)
        self.canvas.coords(
            self.logo_outer_id,
            center_x - logo_size // 2,
            logo_top,
            center_x + logo_size // 2,
            logo_top + logo_size,
        )
        inset = 12
        self.canvas.coords(
            self.logo_inner_id,
            center_x - logo_size // 2 + inset,
            logo_top + inset,
            center_x + logo_size // 2 - inset,
            logo_top + logo_size - inset,
        )
        self.canvas.coords(self.logo_text_id, center_x, logo_top + logo_size // 2)

        button_width = int(width * 0.33)
        button_center_x = center_x + int(width * 0.065)
        start_y = int(height * 0.64)  # centered and a bit lower
        gap = 86

        self.canvas.coords(self.play_btn_id, button_center_x, start_y)
        self.canvas.coords(self.settings_btn_id, button_center_x, start_y + gap)
        self.canvas.coords(self.exit_btn_id, button_center_x, start_y + gap * 2)
        self.canvas.coords(self.records_btn_id, button_center_x, start_y + gap * 3 + 10)

        for item in [self.play_btn_id, self.settings_btn_id, self.exit_btn_id]:
            self.canvas.itemconfigure(item, width=button_width)

        self.canvas.itemconfigure(self.records_btn_id, width=int(button_width * 0.55))

        self.canvas.itemconfigure(self.status_id, text=self.app.status_text_var.get())
        self.canvas.coords(self.status_id, center_x, int(height * 0.95))
        self.canvas.coords(self.hint_id, width - 24, height - 18)

    def on_destroy(self) -> None:
        self.background.stop()


class MenuApp:
    theme: object
    width: int
    height: int
    status_text_var: tk.StringVar

    def start_game(self) -> None:
        raise NotImplementedError

    def open_settings(self) -> None:
        raise NotImplementedError

    def open_leaderboard(self) -> None:
        raise NotImplementedError

    def quit(self) -> None:
        raise NotImplementedError
