from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass

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
ACCENT = "#62BDD0"
BUTTON_FILL = "#070534"
LIGHT_TRACK = "#A4ABC4"
DARK_TRACK = "#4A4A4A"
TEXT_PRIMARY = "#FFFFFF"
TEXT_ACCENT = "#2EBECD"
TOGGLE_OFF = "#7A7A7A"

MENU_BUTTON = (-126, 34, 412, 122, 61)
LOGO_RECT = (1257, 11, 172, 171)
SPECIAL_BUTTON = (178, 828, 336, 126, 32)
EXPORT_BUTTON = (552, 828, 336, 126, 32)
LANGUAGE_LABEL_POS = (197, 686)
LANGUAGE_BUTTON_SPECS = {
    "ru": (706, 694, 152, 76, 26),
    "en": (886, 694, 152, 76, 26),
    "ky": (1066, 694, 184, 76, 26),
}

SFX_LABEL_POS = (197, 219)
MUSIC_LABEL_POS = (197, 404)
VIBRATION_LABEL_POS = (197, 593)

SLIDER_TRACK_X = 632
SLIDER_TRACK_WIDTH = 740
SLIDER_DARK_WIDTH = 275
SLIDER_LIGHT_WIDTH = 414
SLIDER_TRACK_HEIGHT = 68
SLIDER_ONE_Y = 248
SLIDER_TWO_Y = 433
SLIDER_THUMB_WIDTH = 135
SLIDER_THUMB_HEIGHT = 141
SLIDER_THUMB_OFFSET_Y = -29

TOGGLE_X = 799
TOGGLE_Y = 611
TOGGLE_WIDTH = 160
TOGGLE_HEIGHT = 80

TK_FONT_SCALE = 0.78
MAIN_SECTION_SHIFT_X = -8
LOGO_RIGHT_MARGIN = -220


@dataclass
class SliderGeometry:
    name: str
    track_x1: float
    track_y1: float
    track_x2: float
    track_y2: float
    thumb_x1: float
    thumb_y1: float
    thumb_x2: float
    thumb_y2: float

    def hit_track(self, x: float, y: float) -> bool:
        return self.track_x1 <= x <= self.track_x2 and self.thumb_y1 <= y <= self.thumb_y2


class SettingsScreen(Screen):
    def __init__(self, app: "SettingsApp") -> None:
        super().__init__(app)

        self.canvas = tk.Canvas(
            self.container,
            highlightthickness=0,
            bd=0,
            bg=BACKGROUND_COLOR,
            cursor="arrow",
        )
        self.canvas.pack(fill="both", expand=True)

        self.logo_source = self._load_logo_source()
        self.logo_image: ImageTk.PhotoImage | tk.PhotoImage | None = None

        self.scale = 1.0
        self.stage_left = 0
        self.stage_top = 0
        self.dragging_slider: str | None = None
        self.hover_target: str | None = None
        self.slider_geometries: dict[str, SliderGeometry] = {}
        self.menu_bounds: tuple[float, float, float, float] | None = None
        self.special_bounds: tuple[float, float, float, float] | None = None
        self.export_bounds: tuple[float, float, float, float] | None = None
        self.toggle_bounds: tuple[float, float, float, float] | None = None
        self.language_bounds: dict[str, tuple[float, float, float, float]] = {}
        self.export_window: tk.Toplevel | None = None
        self.export_status_var = tk.StringVar(value="")

        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.bind("<Button-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

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

    @staticmethod
    def _hex_to_rgb(color: str) -> tuple[int, int, int]:
        value = color.lstrip("#")
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

    def _font(self, size: int, weight: str = "bold") -> tuple[str, int, str]:
        return ("Arial", max(12, int(size * self.scale * TK_FONT_SCALE)), weight)

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
    ) -> None:
        r = max(0.0, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))

        if r == 0:
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline=outline, width=width)
            return

        self.canvas.create_rectangle(x1 + r, y1, x2 - r, y2, fill=fill, outline="")
        self.canvas.create_rectangle(x1, y1 + r, x2, y2 - r, fill=fill, outline="")

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
            )

        if outline:
            self.canvas.create_line(x1 + r, y1, x2 - r, y1, fill=outline, width=width)
            self.canvas.create_line(x2, y1 + r, x2, y2 - r, fill=outline, width=width)
            self.canvas.create_line(x1 + r, y2, x2 - r, y2, fill=outline, width=width)
            self.canvas.create_line(x1, y1 + r, x1, y2 - r, fill=outline, width=width)

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
                )

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

        self.canvas.create_image(self._sx(x), self._sy(y), image=self.logo_image, anchor="nw")

    def _draw_menu_button(self) -> None:
        x, y, w, h, radius = MENU_BUTTON
        x1 = self._sx(x)
        y1 = self._sy(y)
        x2 = x1 + w * self.scale
        y2 = y1 + h * self.scale
        hover = self.hover_target == "menu"

        fill = self._blend(BUTTON_FILL, "#10105D", 0.35 if hover else 0.0)
        border = self._blend(ACCENT, "#88D7E4", 0.4 if hover else 0.0)
        self._create_round_rect(
            x1,
            y1,
            x2,
            y2,
            radius * self.scale,
            fill=fill,
            outline=border,
            width=max(4, int(8 * self.scale * 0.65)),
        )
        self.canvas.create_text(
            (x1 + x2) / 2,
            (y1 + y2) / 2,
            text=self.app.tr("common.menu"),
            fill=TEXT_PRIMARY,
            font=self._font(50),
            anchor="center",
        )
        self.menu_bounds = (x1, y1, x2, y2)

    def _draw_label(self, text: str, x: int, y: int) -> None:
        self.canvas.create_text(
            self._sx(x + MAIN_SECTION_SHIFT_X),
            self._sy(y),
            text=text,
            fill=TEXT_PRIMARY,
            font=self._font(96),
            anchor="nw",
        )

    def _draw_language_selector(self) -> None:
        self.canvas.create_text(
            self._sx(LANGUAGE_LABEL_POS[0] + MAIN_SECTION_SHIFT_X),
            self._sy(LANGUAGE_LABEL_POS[1]),
            text=self.app.tr("settings.language"),
            fill=TEXT_PRIMARY,
            font=self._font(84),
            anchor="nw",
        )
        self.language_bounds = {}

        for language, spec in LANGUAGE_BUTTON_SPECS.items():
            x, y, w, h, radius = spec
            x1 = self._sx(x + MAIN_SECTION_SHIFT_X)
            y1 = self._sy(y)
            x2 = self._sx(x + MAIN_SECTION_SHIFT_X + w)
            y2 = self._sy(y + h)
            active = self.app.language == language
            hover = self.hover_target == f"lang:{language}"

            fill = ACCENT if active else self._blend(BUTTON_FILL, "#10105D", 0.35 if hover else 0.0)
            border = "#8EDDE8" if active else ACCENT
            text_color = BUTTON_FILL if active else TEXT_PRIMARY

            self._create_round_rect(
                x1,
                y1,
                x2,
                y2,
                radius * self.scale,
                fill=fill,
                outline=border,
                width=max(2, int(3 * self.scale)),
            )
            self.canvas.create_text(
                (x1 + x2) / 2,
                (y1 + y2) / 2,
                text=self.app.tr(f"settings.language.{language}"),
                fill=text_color,
                font=self._font(30),
                anchor="center",
            )
            self.language_bounds[language] = (x1, y1, x2, y2)

    def _slider_value(self, name: str) -> float:
        return float(self.app.sfx_level_var.get() if name == "sfx" else self.app.music_level_var.get())

    def _set_slider_value(self, name: str, value: float) -> None:
        clamped = max(0.0, min(1.0, value))
        if name == "sfx":
            self.app.sfx_level_var.set(clamped)
        else:
            self.app.music_level_var.set(clamped)

    def _draw_slider(self, name: str, y: int) -> None:
        x1 = self._sx(SLIDER_TRACK_X + MAIN_SECTION_SHIFT_X)
        y1 = self._sy(y)
        x2 = self._sx(SLIDER_TRACK_X + MAIN_SECTION_SHIFT_X + SLIDER_TRACK_WIDTH)
        y2 = self._sy(y + SLIDER_TRACK_HEIGHT)
        border = max(2, int(3 * self.scale))

        value = self._slider_value(name)
        thumb_center_x = x1 + (x2 - x1) * value
        split_x = min(max(thumb_center_x, x1), x2)

        self.canvas.create_rectangle(x1, y1, x2, y2, fill=LIGHT_TRACK, outline="#111111", width=border)
        self.canvas.create_rectangle(x1, y1, split_x, y2, fill=DARK_TRACK, outline="")

        thumb_w = SLIDER_THUMB_WIDTH * self.scale
        thumb_h = SLIDER_THUMB_HEIGHT * self.scale
        thumb_x1 = thumb_center_x - thumb_w / 2
        thumb_y1 = self._sy(y + SLIDER_THUMB_OFFSET_Y)
        thumb_x2 = thumb_x1 + thumb_w
        thumb_y2 = thumb_y1 + thumb_h

        thumb_fill = self._blend(ACCENT, "#7CD6E4", 0.3 if self.hover_target == name else 0.0)
        self.canvas.create_rectangle(
            thumb_x1,
            thumb_y1,
            thumb_x2,
            thumb_y2,
            fill=thumb_fill,
            outline="#111111",
            width=border,
        )

        arrow_gap = 8 * self.scale
        arrow_w = 34 * self.scale
        arrow_h = 28 * self.scale
        cx = (thumb_x1 + thumb_x2) / 2
        cy = (thumb_y1 + thumb_y2) / 2

        self.canvas.create_polygon(
            cx - arrow_gap,
            cy,
            cx - arrow_gap - arrow_w,
            cy - arrow_h,
            cx - arrow_gap - arrow_w,
            cy + arrow_h,
            fill="#1E1E1E",
            outline="#1E1E1E",
        )
        self.canvas.create_polygon(
            cx + arrow_gap,
            cy,
            cx + arrow_gap + arrow_w,
            cy - arrow_h,
            cx + arrow_gap + arrow_w,
            cy + arrow_h,
            fill="#1E1E1E",
            outline="#1E1E1E",
        )

        self.slider_geometries[name] = SliderGeometry(
            name=name,
            track_x1=x1,
            track_y1=y1,
            track_x2=x2,
            track_y2=y2,
            thumb_x1=thumb_x1,
            thumb_y1=thumb_y1,
            thumb_x2=thumb_x2,
            thumb_y2=thumb_y2,
        )

    def _draw_toggle(self) -> None:
        x1 = self._sx(TOGGLE_X + MAIN_SECTION_SHIFT_X)
        y1 = self._sy(TOGGLE_Y)
        x2 = self._sx(TOGGLE_X + MAIN_SECTION_SHIFT_X + TOGGLE_WIDTH)
        y2 = self._sy(TOGGLE_Y + TOGGLE_HEIGHT)
        radius = TOGGLE_HEIGHT * self.scale / 2

        hover = self.hover_target == "vibration"
        enabled = bool(self.app.vibration_enabled_var.get())
        base_fill = ACCENT if enabled else TOGGLE_OFF
        hover_fill = "#75D1DC" if enabled else "#9A9A9A"
        fill = self._blend(base_fill, hover_fill, 0.25 if hover else 0.0)
        self._create_round_rect(
            x1,
            y1,
            x2,
            y2,
            radius,
            fill=fill,
            outline="",
        )

        knob_size = 48 * self.scale
        knob_margin = 11 * self.scale
        knob_x = x2 - knob_margin - knob_size if enabled else x1 + knob_margin
        self.canvas.create_oval(
            knob_x,
            y1 + knob_margin,
            knob_x + knob_size,
            y1 + knob_margin + knob_size,
            fill="#E0E0E0",
            outline="",
        )
        self.toggle_bounds = (x1, y1, x2, y2)

    def _draw_special_button(self) -> None:
        self._draw_action_button(self.app.tr("common.special"), SPECIAL_BUTTON, "special")

    def _draw_export_button(self) -> None:
        self._draw_action_button(self.app.tr("common.export"), EXPORT_BUTTON, "export")

    def _draw_action_button(self, label: str, spec: tuple[int, int, int, int, int], target: str) -> None:
        x, y, w, h, radius = spec
        x1 = self._sx(x + MAIN_SECTION_SHIFT_X)
        y1 = self._sy(y)
        x2 = self._sx(x + MAIN_SECTION_SHIFT_X + w)
        y2 = self._sy(y + h)
        hover = self.hover_target == target

        fill = self._blend(BUTTON_FILL, "#10105D", 0.35 if hover else 0.0)
        self._create_round_rect(
            x1,
            y1,
            x2,
            y2,
            radius * self.scale,
            fill=fill,
            outline=ACCENT,
            width=max(2, int(2 * self.scale)),
        )
        self.canvas.create_text(
            (x1 + x2) / 2,
            (y1 + y2) / 2,
            text=label,
            fill=TEXT_ACCENT,
            font=self._font(66),
            anchor="center",
        )
        if target == "special":
            self.special_bounds = (x1, y1, x2, y2)
        else:
            self.export_bounds = (x1, y1, x2, y2)

    def _draw_screen(self) -> None:
        self.canvas.delete("all")
        self.menu_bounds = None
        self.special_bounds = None
        self.export_bounds = None
        self.toggle_bounds = None
        self.language_bounds = {}
        self.slider_geometries = {}

        self._draw_menu_button()
        self._draw_logo()
        self._draw_label(self.app.tr("settings.sfx"), *SFX_LABEL_POS)
        self._draw_label(self.app.tr("settings.music"), *MUSIC_LABEL_POS)
        self._draw_label(self.app.tr("settings.vibration"), *VIBRATION_LABEL_POS)
        self._draw_slider("sfx", SLIDER_ONE_Y)
        self._draw_slider("music", SLIDER_TWO_Y)
        self._draw_toggle()
        self._draw_language_selector()
        self._draw_special_button()
        self._draw_export_button()

    def _hit_test(self, x: float, y: float) -> str | None:
        if self.menu_bounds is not None:
            x1, y1, x2, y2 = self.menu_bounds
            if x1 <= x <= x2 and y1 <= y <= y2:
                return "menu"

        for name, geometry in self.slider_geometries.items():
            if geometry.hit_track(x, y):
                return name

        if self.toggle_bounds is not None:
            x1, y1, x2, y2 = self.toggle_bounds
            if x1 <= x <= x2 and y1 <= y <= y2:
                return "vibration"

        if self.special_bounds is not None:
            x1, y1, x2, y2 = self.special_bounds
            if x1 <= x <= x2 and y1 <= y <= y2:
                return "special"

        if self.export_bounds is not None:
            x1, y1, x2, y2 = self.export_bounds
            if x1 <= x <= x2 and y1 <= y <= y2:
                return "export"

        for language, bounds in self.language_bounds.items():
            x1, y1, x2, y2 = bounds
            if x1 <= x <= x2 and y1 <= y <= y2:
                return f"lang:{language}"

        return None

    def _set_cursor(self, name: str | None) -> None:
        self.canvas.configure(cursor="hand2" if name is not None else "arrow")

    def _slider_from_pointer(self, name: str, x: float) -> None:
        geometry = self.slider_geometries.get(name)
        if geometry is None:
            return
        value = (x - geometry.track_x1) / max(1.0, geometry.track_x2 - geometry.track_x1)
        self._set_slider_value(name, value)

    def _on_leave(self, _event: tk.Event) -> None:
        if self.dragging_slider is None:
            self.hover_target = None
            self._set_cursor(None)
            self._draw_screen()

    def _on_motion(self, event: tk.Event) -> None:
        if self.dragging_slider is not None:
            return
        self.hover_target = self._hit_test(event.x, event.y)
        self._set_cursor(self.hover_target)
        self._draw_screen()

    def _on_press(self, event: tk.Event) -> None:
        target = self._hit_test(event.x, event.y)
        self.hover_target = target

        if target in {"sfx", "music"}:
            self.dragging_slider = target
            self._slider_from_pointer(target, event.x)
            self._draw_screen()
            return

        if target == "menu":
            self.app.open_menu()
            return

        if target == "vibration":
            self.app.vibration_enabled_var.set(not bool(self.app.vibration_enabled_var.get()))
            self._draw_screen()
            return

        if target == "special":
            self.app.open_admin_login()
            return

        if target == "export":
            self._open_export_dialog()
            return

        if target is not None and target.startswith("lang:"):
            self.app.set_language(target.split(":", 1)[1])
            self._draw_screen()
            return

        self._set_cursor(target)
        self._draw_screen()

    def _on_drag(self, event: tk.Event) -> None:
        if self.dragging_slider is None:
            return
        self._slider_from_pointer(self.dragging_slider, event.x)
        self._draw_screen()

    def _on_release(self, _event: tk.Event) -> None:
        self.dragging_slider = None

    def on_resize(self, width: int, height: int) -> None:
        self.scale, self.stage_left, self.stage_top = self._fit_stage(width, height)
        self._draw_screen()

    def _open_export_dialog(self) -> None:
        if self.export_window is not None and self.export_window.winfo_exists():
            self.export_window.lift()
            self.export_window.focus_force()
            return

        self.export_status_var.set("")
        window = tk.Toplevel(self.root)
        window.title(self.app.tr("settings.export_title"))
        window.configure(bg=BACKGROUND_COLOR)
        window.transient(self.root)
        window.grab_set()
        window.resizable(False, False)
        self.export_window = window

        frame = tk.Frame(window, bg="#34107D", bd=0, highlightthickness=2, highlightbackground=ACCENT)
        frame.pack(padx=26, pady=26)

        tk.Label(
            frame,
            text=self.app.tr("settings.export_title"),
            bg="#34107D",
            fg=TEXT_PRIMARY,
            font=("Arial", 24, "bold"),
        ).pack(pady=(18, 8))
        tk.Label(
            frame,
            text=self.app.tr("settings.export_subtitle"),
            bg="#34107D",
            fg="#D9D6E8",
            font=("Arial", 12),
        ).pack(pady=(0, 18))

        buttons = tk.Frame(frame, bg="#34107D")
        buttons.pack(padx=22, pady=(0, 18))

        for format_name in ("json", "csv", "txt"):
            tk.Button(
                buttons,
                text=self.app.tr(f"settings.export.{format_name}"),
                command=lambda fmt=format_name: self._run_export(fmt),
                relief="flat",
                bd=0,
                bg=BUTTON_FILL,
                fg=TEXT_ACCENT,
                activebackground="#10105D",
                activeforeground=TEXT_ACCENT,
                cursor="hand2",
                font=("Arial", 16, "bold"),
                width=10,
                pady=10,
            ).pack(side="left", padx=8)

        tk.Label(
            frame,
            textvariable=self.export_status_var,
            bg="#34107D",
            fg=TEXT_PRIMARY,
            font=("Arial", 11),
            wraplength=420,
            justify="center",
        ).pack(padx=20, pady=(0, 18))

        tk.Button(
            frame,
            text=self.app.tr("common.close"),
            command=self._close_export_dialog,
            relief="flat",
            bd=0,
            bg="#24104F",
            fg="#F4F4F4",
            activebackground="#2D1563",
            activeforeground="#F4F4F4",
            cursor="hand2",
            font=("Arial", 14, "bold"),
            width=12,
            pady=8,
        ).pack(pady=(0, 18))

        window.protocol("WM_DELETE_WINDOW", self._close_export_dialog)
        window.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - window.winfo_width()) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - window.winfo_height()) // 2
        window.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def _run_export(self, format_name: str) -> None:
        success, message = self.app.export_game_data(format_name)
        self.export_status_var.set(message)
        if success:
            self.after_export_close()

    def after_export_close(self) -> None:
        if self.export_window is None or not self.export_window.winfo_exists():
            return
        self.export_window.after(1200, self._close_export_dialog)

    def _close_export_dialog(self) -> None:
        if self.export_window is not None and self.export_window.winfo_exists():
            self.export_window.grab_release()
            self.export_window.destroy()
        self.export_window = None

    def on_escape(self) -> None:
        self.app.open_menu()

    def on_language_changed(self) -> None:
        self._draw_screen()


class SettingsApp:
    width: int
    height: int
    language: str
    sfx_level_var: tk.DoubleVar
    music_level_var: tk.DoubleVar
    vibration_enabled_var: tk.BooleanVar

    def open_menu(self) -> None:
        raise NotImplementedError

    def toggle_fullscreen(self) -> None:
        raise NotImplementedError

    def open_admin_login(self) -> None:
        raise NotImplementedError

    def export_game_data(self, format_name: str) -> tuple[bool, str]:
        raise NotImplementedError

    def tr(self, key: str, **kwargs) -> str:
        raise NotImplementedError

    def set_language(self, language: str) -> None:
        raise NotImplementedError
