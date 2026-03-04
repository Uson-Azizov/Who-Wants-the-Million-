# Mindset

## PostgreSQL integration

The project now supports PostgreSQL for storing finished game results.

### Environment setup

Create `.env` in project root:

```env
DATABASE_URL=postgresql://user:password@host:5432/database
DATABASE_CONNECT_TIMEOUT=8
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

- If PostgreSQL is unavailable, the game still runs.
- Database status is shown in Settings screen.

## Leaderboard

- Main menu now has a `Рекорды` page.
- It shows top game results from `game_results`.
- Sorting: `score DESC`, then `created_at ASC`.
- Records are loaded from PostgreSQL and can be refreshed with `Обновить`.
