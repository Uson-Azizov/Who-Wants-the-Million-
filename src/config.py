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
    candidates = sorted(
        path
        for path in IMAGES_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
    ) if IMAGES_DIR.exists() else []
    if candidates:
        return candidates[0]
    return BACKGROUND_IMAGE_PATH


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

DATABASE_URL = os.getenv("DATABASE_URL", "")
DATABASE_CONNECT_TIMEOUT = int(os.getenv("DATABASE_CONNECT_TIMEOUT", "8"))
PLAYER_NAME = os.getenv("PLAYER_NAME", "Player")
