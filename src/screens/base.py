from __future__ import annotations

import tkinter as tk


class Screen:
    def __init__(self, app: "AppProtocol") -> None:
        self.app = app
        self.root = app.root
        self.container = tk.Frame(self.root, bg=app.theme.window_bg)

    def show(self) -> None:
        self.container.pack(fill="both", expand=True)

    def destroy(self) -> None:
        self.on_destroy()
        self.container.destroy()

    def on_resize(self, width: int, height: int) -> None:
        return

    def on_escape(self) -> None:
        return

    def on_destroy(self) -> None:
        return


class AppProtocol:
    root: tk.Tk
    width: int
    height: int
    theme: object
