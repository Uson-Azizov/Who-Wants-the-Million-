import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
QUESTIONS_DIR = BASE_DIR / "questions"
ANIMATIONS_DIR = BASE_DIR / "animations"
IMAGES_DIR = BASE_DIR / "images"

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE = "Mindset"
START_FULLSCREEN = True
BACKGROUND_IMAGE_PATH = ANIMATIONS_DIR / "mindset_menu_bg.jpg"


def _resolve_menu_background_path() -> Path:
    if not IMAGES_DIR.exists():
        return BACKGROUND_IMAGE_PATH

    candidates = [
        path
        for path in IMAGES_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
    ]
    if not candidates:
        return BACKGROUND_IMAGE_PATH

    preferred_names = {
        "background",
        "menu_background",
        "mindset_background",
        "bg",
    }
    for candidate in candidates:
        if candidate.stem.lower() in preferred_names:
            return candidate

    try:
        from PIL import Image

        def image_area(path: Path) -> int:
            with Image.open(path) as image:
                w, h = image.size
                return int(w * h)

        return max(candidates, key=image_area)
    except Exception:
        # Fallback without Pillow: choose the largest file size.
        return max(candidates, key=lambda p: p.stat().st_size)


MENU_BACKGROUND_IMAGE_PATH = _resolve_menu_background_path()

QUESTIONS_FILES = {
    "easy": QUESTIONS_DIR / "easy.json",
    "medium": QUESTIONS_DIR / "meduim.json",  # Keep current file name for compatibility.
    "hard": QUESTIONS_DIR / "hard.json",
}


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue

        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv(BASE_DIR / ".env")

SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", str(BASE_DIR / "millionaire.db"))
PLAYER_NAME = os.getenv("PLAYER_NAME", "Player")
