from __future__ import annotations

import tkinter as tk
from typing import Callable

from src.ui.theme import Theme


class GlassButton(tk.Canvas):
    def __init__(
        self,
        master: tk.Misc,
        text: str,
        command: Callable[[], None],
        theme: Theme,
        font: tuple[str, int, str] = ("Arial", 16, "bold"),
        width: int = 28,
        height: int = 52,
        radius: int = 13,
        bg_color: str | None = None,
        hover_color: str | None = None,
        border_color: str | None = None,
        text_color: str | None = None,
        canvas_bg: str | None = None,
    ) -> None:
        self.theme = theme
        self.command = command
        self.text = text
        self.font = font
        self._state = "normal"
        self._base_bg = bg_color or theme.button_bg
        self._hover_bg = hover_color or theme.button_hover
        self._border_color = border_color or theme.button_border
        self._text_color = text_color or theme.button_text

        self._hover_target = 0.0
        self._hover_value = 0.0
        self._press_value = 0.0
        self._pressed_inside = False

        self._min_width = max(180, width * 12)
        self._height = max(40, int(height))
        self._radius = max(8, int(radius))
        self._job_id: str | None = None

        super().__init__(
            master,
            width=self._min_width,
            height=self._height,
            highlightthickness=0,
            bd=0,
            relief="flat",
            bg=canvas_bg or master.cget("bg"),
            cursor="hand2",
        )

        self.bind("<Configure>", self._on_configure)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

        self._draw_button()
        self._schedule_animation()

    def _schedule_animation(self) -> None:
        if self._job_id is None:
            self._job_id = self.after(16, self._animate)

    def _animate(self) -> None:
        self._job_id = None

        self._hover_value += (self._hover_target - self._hover_value) * 0.25
        self._press_value *= 0.70

        self._draw_button()
        if abs(self._hover_target - self._hover_value) > 0.01 or self._press_value > 0.01:
            self._schedule_animation()

    def _on_configure(self, _event: tk.Event) -> None:
        self._draw_button()

    def _on_enter(self, _event: tk.Event) -> None:
        if self._state == "disabled":
            return
        self._hover_target = 1.0
        self._schedule_animation()

    def _on_leave(self, _event: tk.Event) -> None:
        self._hover_target = 0.0
        self._pressed_inside = False
        self._schedule_animation()

    def _on_press(self, _event: tk.Event) -> None:
        if self._state == "disabled":
            return
        self._pressed_inside = True
        self._press_value = 1.0
        self._schedule_animation()

    def _on_release(self, event: tk.Event) -> None:
        if self._state == "disabled":
            return

        is_inside = 0 <= event.x <= self.winfo_width() and 0 <= event.y <= self.winfo_height()
        should_run = self._pressed_inside and is_inside

        self._pressed_inside = False
        self._press_value = 0.8
        self._schedule_animation()

        if should_run:
            self.command()

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        value = hex_color.lstrip("#")
        return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)

    @staticmethod
    def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

    def _blend(self, a: str, b: str, t: float) -> str:
        ra, ga, ba = self._hex_to_rgb(a)
        rb, gb, bb = self._hex_to_rgb(b)
        r = int(ra + (rb - ra) * t)
        g = int(ga + (gb - ga) * t)
        b_v = int(ba + (bb - ba) * t)
        return self._rgb_to_hex((r, g, b_v))

    def _create_rounded_rect(self, x1: int, y1: int, x2: int, y2: int, r: int, **kwargs: object) -> int:
        points = [
            x1 + r,
            y1,
            x2 - r,
            y1,
            x2,
            y1,
            x2,
            y1 + r,
            x2,
            y2 - r,
            x2,
            y2,
            x2 - r,
            y2,
            x1 + r,
            y2,
            x1,
            y2,
            x1,
            y2 - r,
            x1,
            y1 + r,
            x1,
            y1,
        ]
        return self.create_polygon(points, smooth=True, splinesteps=24, **kwargs)

    def _draw_button(self) -> None:
        self.delete("all")

        width = max(self._min_width, self.winfo_width())
        height = self.winfo_height() if self.winfo_height() > 1 else self._height

        super().configure(width=width, height=height)

        press_offset = int(2 * self._press_value)
        x1, y1 = 2, 2 + press_offset
        x2, y2 = width - 2, height - 2 + press_offset

        if self._state == "disabled":
            fill = self.theme.button_disabled_bg
            border = self._blend(self.theme.button_disabled_bg, self._border_color, 0.25)
            text_color = self.theme.button_disabled_text
        else:
            fill = self._blend(self._base_bg, self._hover_bg, self._hover_value)
            border = self._blend(self._border_color, self.theme.text_primary, self._hover_value * 0.35)
            text_color = self._text_color

        self._create_rounded_rect(x1, y1, x2, y2, self._radius, fill=fill, outline=border, width=2)

        center_x = width // 2
        center_y = (y1 + y2) // 2
        self.create_text(
            center_x + 1,
            center_y + 1,
            text=self.text,
            font=self.font,
            fill="#0c1a30",
        )
        self.create_text(
            center_x,
            center_y,
            text=self.text,
            font=self.font,
            fill=text_color,
        )

    def configure(self, cnf: dict | None = None, **kwargs: object) -> object:  # type: ignore[override]
        state = kwargs.pop("state", None)
        text = kwargs.pop("text", None)
        font = kwargs.pop("font", None)
        width = kwargs.pop("width", None)
        height = kwargs.pop("height", None)

        if text is not None:
            self.text = str(text)

        if font is not None:
            self.font = font  # type: ignore[assignment]

        if width is not None:
            self._min_width = max(1, int(width))

        if height is not None:
            self._height = max(1, int(height))

        if state is not None:
            self._state = str(state)
            if self._state == "disabled":
                self._hover_target = 0.0
                self._pressed_inside = False
                super().configure(cursor="arrow")
            else:
                super().configure(cursor="hand2")

        if text is not None or font is not None or width is not None or height is not None or state is not None:
            self._draw_button()

        if cnf is not None or kwargs:
            return super().configure(cnf or {}, **kwargs)
        return None

    config = configure

    def destroy(self) -> None:
        if self._job_id is not None:
            self.after_cancel(self._job_id)
            self._job_id = None
        super().destroy()
