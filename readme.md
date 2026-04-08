# Mindset

## SQLite integration

The project uses SQLite for storing finished game results and the question bank.

### Environment setup

Create `.env` in project root:

```env
SQLITE_DB_PATH=./millionaire.db
PLAYER_NAME=Player
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Stored table

On startup, the app creates table `game_results` automatically:

- `id`
- `player_name`
- `difficulty`
- `score`
- `asked_questions`
- `is_win`
- `created_at`

### Notes

- If SQLite is unavailable, the game still runs only until database-dependent functionality is reached.
- Database status is shown in Settings screen.

## Leaderboard

- Main menu now has a `Рекорды` page.
- It shows top game results from `game_results`.
- Sorting: `score DESC`, then `created_at ASC`.
- Questions are imported from the `questions/` folder into the `questions` SQL table on startup.
- Records are loaded from SQLite and can be refreshed with `Обновить`.
