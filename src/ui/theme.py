from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    window_bg: str = "#0b1220"
    panel_bg: str = "#12243d"
    panel_border: str = "#6a92c8"
    text_primary: str = "#eaf4ff"
    text_secondary: str = "#9db4d2"
    button_bg: str = "#1d3a5f"
    button_hover: str = "#2a5387"
    button_border: str = "#78abeb"
    button_text: str = "#f4f9ff"
    button_disabled_bg: str = "#17304f"
    button_disabled_text: str = "#8ca0bb"
    success: str = "#4fbd72"
    danger: str = "#d25d5d"
