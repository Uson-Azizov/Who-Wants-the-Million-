# Game Architecture

- `main.py`: entrypoint.
- `src/config.py`: app constants, fullscreen, and file paths.
- `src/models.py`: domain models (`Question`, `Difficulty`, `GameSession`).
- `src/repository.py`: loading/validating questions from JSON files.
- `src/services.py`: game logic (`GameService`).
- `src/ui/components.py`: reusable Tkinter UI widgets (`GlassButton`).
- `src/ui/theme.py`: colors and layout constants.
- `src/ui/animated_background.py`: animated background renderer for Tkinter Canvas.
- `src/screens/base.py`: base screen interface.
- `src/screens/menu.py`: main menu.
- `src/screens/game.py`: gameplay screen.
- `src/screens/settings.py`: settings placeholder.
- `src/app.py`: app loop and screen switching.

## Expected JSON format

Supported JSON root formats:

```json
[
  {
    "question": "Столица Франции?",
    "options": ["Париж", "Рим", "Берлин", "Мадрид"],
    "answer": 0
  }
]
```

or

```json
{
  "quiz": [
    {
      "question": "Столица Франции?",
      "options": ["Париж", "Рим", "Берлин", "Мадрид"],
      "correct_answer": "Париж"
    }
  ]
}
```

- `question`: string
- `options`: array of 4 strings or object with `A/B/C/D`
- `answer`: index (`0..3`), letter (`A..D`) or exact option string
- also supported key: `correct_answer`
