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
