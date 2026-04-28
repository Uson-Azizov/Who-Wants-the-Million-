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
        self.bg_base_x = 0
        self.bg_base_y = 0
        self.overlay_id: int | None = None
        self.scan_id: int | None = None
        self._using_pil_image = False

        self.canvas.bind("<Configure>", self._on_configure)

    @staticmethod
    def _cover_bleed(width: int, height: int) -> int:
        return max(24, int(max(width, height) * 0.03))

    def _load_source_image(self):
        if not self.image_path.exists():
            return None

        if Image is not None:
            try:
                image = Image.open(self.image_path)
                # Avoid black artifacts from transparent PNG areas by flattening alpha
                # onto the app's dark base color before converting to RGB.
                if image.mode in ("RGBA", "LA") or ("transparency" in image.info):
                    image = image.convert("RGBA")
                    base = Image.new("RGBA", image.size, "#0b1220")
                    image = Image.alpha_composite(base, image)
                return image.convert("RGB")
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

        # Always paint a full-canvas base first so uncovered pixels never look black.
        self.canvas.create_rectangle(0, 0, self.width, self.height, fill="#0b1220", outline="", tags="bg")

        if Image is not None and hasattr(self.source_image, "size"):
            self._using_pil_image = True
            bleed = self._cover_bleed(self.width, self.height)
            target_w = self.width + bleed * 2 + self.max_drift_x * 2
            target_h = self.height + bleed * 2 + self.max_drift_y * 2
            src_w, src_h = self.source_image.size
            scale = max(target_w / src_w, target_h / src_h)
            resample = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
            resized = self.source_image.resize(
                (max(1, math.ceil(src_w * scale)), max(1, math.ceil(src_h * scale))),
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
            src = self.source_image
            src_w = max(1, int(src.width()))
            src_h = max(1, int(src.height()))
            bleed = self._cover_bleed(self.width, self.height)
            target_w = self.width + bleed * 2 + self.max_drift_x * 2
            target_h = self.height + bleed * 2 + self.max_drift_y * 2

            scale = max(target_w / src_w, target_h / src_h)
            if scale >= 1:
                zoom_n = max(1, math.ceil(scale))
                scaled = src.zoom(zoom_n, zoom_n)
            else:
                sub_n = max(1, math.ceil(1 / scale))
                scaled = src.subsample(sub_n, sub_n)

            scaled_w = max(1, int(scaled.width()))
            scaled_h = max(1, int(scaled.height()))

            self.tk_image = scaled
            x = -((scaled_w - target_w) // 2) - bleed - self.max_drift_x + dx
            y = -((scaled_h - target_h) // 2) - bleed - self.max_drift_y + dy
            self.bg_base_x = x
            self.bg_base_y = y
            self.bg_id = self.canvas.create_image(self.bg_base_x, self.bg_base_y, image=self.tk_image, anchor="nw", tags="bg")
            return

        self.bg_base_x = -self._cover_bleed(self.width, self.height) - self.max_drift_x
        self.bg_base_y = -self._cover_bleed(self.width, self.height) - self.max_drift_y
        self.bg_id = self.canvas.create_image(
            self.bg_base_x + dx,
            self.bg_base_y + dy,
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
            self.canvas.coords(
                self.bg_id,
                self.bg_base_x + dx,
                self.bg_base_y + dy,
            )

        if self.scan_id is not None:
            y = int((self.time * 90) % (self.height + 80)) - 60
            self.canvas.coords(self.scan_id, 0, y, self.width, y + 42)

        self.canvas.after(33, self._tick)
