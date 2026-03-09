from __future__ import annotations

import math
from pathlib import Path

import tkinter as tk

try:
    from PIL import Image, ImageEnhance, ImageTk
except Exception:  # pragma: no cover - optional dependency
    Image = None
    ImageEnhance = None
    ImageTk = None


class AnimatedBackground:
    def __init__(
        self,
        canvas: tk.Canvas,
        image_path: Path,
        *,
        darken_alpha: int = 120,
        drift_x: int = 2,
        drift_y: int = 1,
        show_scanline: bool = False,
    ) -> None:
        self.canvas = canvas
        self.image_path = image_path
        self.darken_alpha = max(0, min(220, darken_alpha))
        self.max_drift_x = max(0, drift_x)
        self.max_drift_y = max(0, drift_y)
        self.show_scanline = show_scanline

        self.width = 1
        self.height = 1
        self.time = 0.0
        self.running = False

        self.source_image = self._load_source_image()
        self.tk_image: ImageTk.PhotoImage | tk.PhotoImage | None = None

        self.bg_id: int | None = None
        self.overlay_id: int | None = None
        self.scan_id: int | None = None
        self._using_pil_image = False

        self.canvas.bind("<Configure>", self._on_configure)

    def _load_source_image(self):
        if not self.image_path.exists():
            return None

        if Image is not None:
            try:
                return Image.open(self.image_path).convert("RGB")
            except Exception:
                return None

        try:
            return tk.PhotoImage(file=str(self.image_path))
        except tk.TclError:
            return None

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        self._render_static()
        self._tick()

    def stop(self) -> None:
        self.running = False

    def _on_configure(self, event: tk.Event) -> None:
        self.width = max(1, int(event.width))
        self.height = max(1, int(event.height))
        self._render_static()

    def _render_static(self) -> None:
        self.canvas.delete("bg")

        if self.source_image is None:
            self._draw_gradient_fallback()
        else:
            self._draw_image_background(0, 0)

        if self.source_image is None:
            self._draw_darken_overlay()

        if self.show_scanline:
            self.scan_id = self.canvas.create_rectangle(
                0,
                -60,
                self.width,
                -10,
                fill="#9ec5ff",
                stipple="gray25",
                outline="",
                tags="bg",
            )

    def _draw_darken_overlay(self) -> None:
        if self.darken_alpha <= 0:
            return

        # Tkinter Canvas has no true per-item alpha for fill, so layer multiple stippled overlays.
        layers = max(1, min(6, self.darken_alpha // 35))
        for index in range(layers):
            stipple = "gray50" if index % 2 == 0 else "gray25"
            self.overlay_id = self.canvas.create_rectangle(
                0,
                0,
                self.width,
                self.height,
                fill="#000000",
                stipple=stipple,
                outline="",
                tags="bg",
            )

    def _draw_gradient_fallback(self) -> None:
        top = (9, 17, 31)
        bottom = (20, 11, 20)
        for y in range(self.height):
            t = y / max(1, self.height - 1)
            r = int(top[0] + (bottom[0] - top[0]) * t)
            g = int(top[1] + (bottom[1] - top[1]) * t)
            b = int(top[2] + (bottom[2] - top[2]) * t)
            self.canvas.create_line(0, y, self.width, y, fill=f"#{r:02x}{g:02x}{b:02x}", tags="bg")

    def _draw_image_background(self, dx: int, dy: int) -> None:
        if self.source_image is None:
            return

        if Image is not None and hasattr(self.source_image, "size"):
            self._using_pil_image = True
            target_w = self.width + self.max_drift_x * 2
            target_h = self.height + self.max_drift_y * 2
            src_w, src_h = self.source_image.size
            scale = max(target_w / src_w, target_h / src_h)
            resample = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
            resized = self.source_image.resize(
                (max(1, int(src_w * scale)), max(1, int(src_h * scale))),
                resample,
            )
            crop_x = (resized.size[0] - target_w) // 2
            crop_y = (resized.size[1] - target_h) // 2
            cropped = resized.crop((crop_x, crop_y, crop_x + target_w, crop_y + target_h))
            if self.darken_alpha > 0 and ImageEnhance is not None:
                # Darken directly in image pipeline (reliable on macOS Tk where canvas stipple may render solid black).
                factor = max(0.25, 1.0 - (self.darken_alpha / 255.0) * 0.65)
                cropped = ImageEnhance.Brightness(cropped).enhance(factor)
            self.tk_image = ImageTk.PhotoImage(cropped)
        else:
            self._using_pil_image = False
            self.tk_image = self.source_image

        self.bg_id = self.canvas.create_image(
            -self.max_drift_x + dx,
            -self.max_drift_y + dy,
            image=self.tk_image,
            anchor="nw",
            tags="bg",
        )

    def _tick(self) -> None:
        if not self.running:
            return

        self.time += 0.05

        if self.bg_id is not None:
            dx = int(self.max_drift_x * math.sin(self.time * 0.9))
            dy = int(self.max_drift_y * math.cos(self.time * 1.1))
            self.canvas.coords(self.bg_id, -self.max_drift_x + dx, -self.max_drift_y + dy)

        if self.scan_id is not None:
            y = int((self.time * 90) % (self.height + 80)) - 60
            self.canvas.coords(self.scan_id, 0, y, self.width, y + 42)

        self.canvas.after(33, self._tick)
