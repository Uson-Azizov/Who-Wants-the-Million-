from __future__ import annotations

from pathlib import Path

try:
    import pygame
except Exception:  # pragma: no cover - optional dependency
    pygame = None


class AudioManager:
    def __init__(self) -> None:
        self.available = False
        self.current_music_path: str | None = None
        self.sfx_volume = 0.4
        self.music_volume = 0.25
        self._sound_cache: dict[str, object] = {}

        if pygame is None:
            return

        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        except Exception:
            return

        self.available = True

    def set_music_volume(self, value: float) -> None:
        self.music_volume = max(0.0, min(1.0, float(value)))
        if self.available:
            pygame.mixer.music.set_volume(self.music_volume)

    def set_sfx_volume(self, value: float) -> None:
        self.sfx_volume = max(0.0, min(1.0, float(value)))

    def play_music(self, path: Path | str | None, *, loop: bool = True, restart: bool = False) -> None:
        if not self.available or path is None:
            return

        target = str(path)
        if not Path(target).exists():
            return

        if self.current_music_path == target and not restart:
            pygame.mixer.music.set_volume(self.music_volume)
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.play(-1 if loop else 0)
            return

        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(target)
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(-1 if loop else 0)
            self.current_music_path = target
        except Exception:
            self.current_music_path = None

    def stop_music(self) -> None:
        if not self.available:
            return
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        self.current_music_path = None

    def play_sfx(self, path: Path | str | None) -> None:
        if not self.available or path is None:
            return

        target = str(path)
        if not Path(target).exists():
            return

        try:
            sound = self._sound_cache.get(target)
            if sound is None:
                sound = pygame.mixer.Sound(target)
                self._sound_cache[target] = sound
            sound.set_volume(self.sfx_volume)
            sound.play()
        except Exception:
            return

    def shutdown(self) -> None:
        if not self.available:
            return
        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except Exception:
            pass
        self.available = False
