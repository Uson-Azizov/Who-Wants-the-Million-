from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from typing import Callable

from src.config import MENU_LAYOUT_IMAGE_PATH
from src.screens.base import Screen

try:
    from PIL import Image, ImageTk
except Exception:  # pragma: no cover - optional dependency
    Image = None
    ImageTk = None


DESIGN_WIDTH = 1440
DESIGN_HEIGHT = 1024
BUTTON_LEFT = 481
BUTTON_TOP = 621
BUTTON_WIDTH = 478
BUTTON_HEIGHT = 84
BUTTON_GAP = 15
LAYOUT_SCALE_BOOST = 1.0
LAYOUT_SHIFT_X = 92
LAYOUT_SHIFT_Y = 74


@dataclass
class ButtonRegion:
    text: str
    command: Callable[[], None]
    bounds: tuple[float, float, float, float]

    def contains(self, x: float, y: float) -> bool:
        x1, y1, x2, y2 = self.bounds
        return x1 <= x <= x2 and y1 <= y <= y2


class MenuScreen(Screen):
    def __init__(self, app: "MenuApp") -> None:
        super().__init__(app)

        self.canvas = tk.Canvas(
            self.container,
            highlightthickness=0,
            bd=0,
            bg="#000F3E",
            cursor="arrow",
        )
        self.canvas.pack(fill="both", expand=True)

        self.layout_source = self._load_layout_source()
        self.layout_image: ImageTk.PhotoImage | tk.PhotoImage | None = None
        self.layout_id = self.canvas.create_image(0, 0, anchor="nw", state="hidden")
        self.fallback_text_id = self.canvas.create_text(
            0,
            0,
            text="Menu layout image not found",
            fill="#ffffff",
            font=("Arial", 20, "bold"),
            anchor="center",
            state="hidden",
        )

        self.button_regions: list[ButtonRegion] = []
        self.hover_index: int | None = None

        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.bind("<Button-1>", self._on_click)

        self.on_resize(self.app.width, self.app.height)

    def _load_layout_source(self):
        if not MENU_LAYOUT_IMAGE_PATH.exists():
            return None

        if Image is not None:
            try:
                return Image.open(MENU_LAYOUT_IMAGE_PATH).convert("RGBA")
            except Exception:
                return None

        try:
            return tk.PhotoImage(file=str(MENU_LAYOUT_IMAGE_PATH))
        except tk.TclError:
            return None

    @staticmethod
    def _cover_stage(width: int, height: int) -> tuple[float, int, int, int, int]:
        scale = max(width / DESIGN_WIDTH, height / DESIGN_HEIGHT) * LAYOUT_SCALE_BOOST
        stage_width = max(1, int(DESIGN_WIDTH * scale))
        stage_height = max(1, int(DESIGN_HEIGHT * scale))
        left = (width - stage_width) // 2 + LAYOUT_SHIFT_X
        top = (height - stage_height) // 2 + LAYOUT_SHIFT_Y
        return scale, left, top, stage_width, stage_height

    def _build_regions(self, scale: float, left: int, top: int) -> list[ButtonRegion]:
        step = (BUTTON_HEIGHT + BUTTON_GAP) * scale
        x1 = left + BUTTON_LEFT * scale
        x2 = left + (BUTTON_LEFT + BUTTON_WIDTH) * scale
        first_y = top + BUTTON_TOP * scale

        specs = [
            ("Играть", self.app.start_game),
            ("Настройки", self.app.open_settings),
            ("Статистика", self.app.open_leaderboard),
            ("Выход", self.app.quit),
        ]

        regions: list[ButtonRegion] = []
        for index, (text, command) in enumerate(specs):
            y1 = first_y + step * index
            y2 = y1 + BUTTON_HEIGHT * scale
            regions.append(ButtonRegion(text=text, command=command, bounds=(x1, y1, x2, y2)))
        return regions

    def _set_cursor(self, value: str) -> None:
        if self.canvas.cget("cursor") != value:
            self.canvas.configure(cursor=value)

    def _on_leave(self, _event: tk.Event) -> None:
        self.hover_index = None
        self._set_cursor("arrow")

    def _on_motion(self, event: tk.Event) -> None:
        hovered = self._hit_test(event.x, event.y)
        self.hover_index = hovered
        self._set_cursor("hand2" if hovered is not None else "arrow")

    def _on_click(self, event: tk.Event) -> None:
        hovered = self._hit_test(event.x, event.y)
        if hovered is None:
            return
        self.button_regions[hovered].command()

    def _hit_test(self, x: float, y: float) -> int | None:
        for index, region in enumerate(self.button_regions):
            if region.contains(x, y):
                return index
        return None

    def on_resize(self, width: int, height: int) -> None:
        scale, left, top, stage_width, stage_height = self._cover_stage(width, height)
        self.button_regions = self._build_regions(scale, left, top)

        if self.layout_source is None:
            self.canvas.itemconfigure(self.layout_id, state="hidden")
            self.canvas.itemconfigure(self.fallback_text_id, state="normal")
            self.canvas.coords(self.fallback_text_id, width // 2, height // 2)
            return

        self.canvas.itemconfigure(self.fallback_text_id, state="hidden")

        if Image is not None and hasattr(self.layout_source, "resize"):
            resample = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
            resized = self.layout_source.resize((stage_width, stage_height), resample)
            self.layout_image = ImageTk.PhotoImage(resized)
        else:
            self.layout_image = self.layout_source

        self.canvas.itemconfigure(self.layout_id, image=self.layout_image, state="normal")
        self.canvas.coords(self.layout_id, left, top)
        self._set_cursor("arrow")


class MenuApp:
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
