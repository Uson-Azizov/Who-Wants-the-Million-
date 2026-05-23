from __future__ import annotations

import json
from pathlib import Path

from src.models import Difficulty, Question

SUPPORTED_LANGUAGES = ("ru", "en", "ky")

LANGUAGE_NAMES = {
    "ru": "Русский",
    "en": "English",
    "ky": "Кыргызча",
}

UI_STRINGS: dict[str, dict[str, str]] = {
    "ru": {
        "menu.play": "Играть",
        "menu.settings": "Настройки",
        "menu.stats": "Статистика",
        "menu.exit": "Выход",
        "common.menu": "Меню",
        "common.close": "Закрыть",
        "common.back": "Назад",
        "common.update": "Обновить",
        "common.export": "Export",
        "common.special": "Special",
        "settings.sfx": "SFX",
        "settings.music": "MUSIC",
        "settings.vibration": "VIBRATION",
        "settings.language": "LANGUAGE",
        "settings.language.ru": "Рус",
        "settings.language.en": "Eng",
        "settings.language.ky": "Кырг",
        "settings.export_title": "Экспорт данных",
        "settings.export_subtitle": "Выберите формат для экспорта вопросов и результатов игры",
        "settings.export.json": "JSON",
        "settings.export.csv": "CSV",
        "settings.export.txt": "TXT",
        "status.menu": "Главное меню",
        "status.leaderboard": "Рекорды",
        "status.settings": "Настройки",
        "status.admin_login": "Вход в админку",
        "status.admin_panel": "Админка",
        "status.game_started": "Игра запущена",
        "status.language_switched": "Язык изменён: {language}",
        "game.round": "Раунд {current}/{total}",
        "game.question": "Вопрос:",
        "game.correct": "Верно!",
        "game.correct_2x": "Верно! 2X активен: переход на +2 уровня",
        "game.wrong_menu": "Неправильно. Возврат в главное меню...",
        "game.finish": "Игра завершена",
        "game.finish_title": "Итог:",
        "game.finish_text": "Поздравляем! Вы дошли до {amount}",
        "game.error_title": "Ошибка:",
        "game.error_questions": "Недостаточно вопросов ({difficulty})",
        "game.returning_menu": "Возврат в меню...",
        "game.lifeline.used_5050": "50/50 уже использован",
        "game.lifeline.used_2x": "2X уже использован",
        "game.lifeline.used_phoenix": "Феникс уже использован",
        "game.lifeline.active_phoenix": "Феникс уже активирован",
        "game.lifeline.applied_5050": "50/50: убраны два неверных варианта",
        "game.lifeline.applied_2x": "2X активирован: при верном ответе переход на +2 уровня",
        "game.lifeline.applied_phoenix": "Феникс активирован: одна ошибка будет прощена",
        "game.lifeline.saved_phoenix": "Феникс спасает вас. Новый вопрос того же уровня...",
        "game.leave.title": "Выйти в меню?",
        "game.leave.body": "Если выйти сейчас, текущий прогресс в раунде будет потерян.",
        "game.leave.stay": "Вернуться",
        "game.leave.menu": "В меню",
        "game.currency_suffix": "сом",
        "leaderboard.title": "Рекорды",
        "leaderboard.subtitle": "Топ результатов по количеству правильных ответов",
        "leaderboard.player": "Игрок",
        "leaderboard.difficulty": "Сложность",
        "leaderboard.correct": "Верных",
        "leaderboard.asked": "Вопросов",
        "leaderboard.win": "Победа",
        "leaderboard.date": "Дата",
        "leaderboard.refresh": "Обновить",
        "leaderboard.back": "Назад в меню",
        "leaderboard.empty": "Нет данных",
        "difficulty.easy": "Легкая",
        "difficulty.medium": "Нормальная",
        "difficulty.hard": "Сложная",
        "difficulty.mixed": "Смешанная",
        "yes": "Да",
        "no": "Нет",
        "admin.login.title": "Вход",
        "admin.login.subtitle": "Войдите и начните управлять вопросами!",
        "admin.login.remember": "Запомнить меня",
        "admin.login.forgot": "Забыли пароль?",
        "admin.login.submit": "Войти как админ",
        "admin.login.empty": "Введите login и admins code.",
        "admin.login.success": "Вход выполнен",
        "admin.panel.title": "Банк вопросов",
        "admin.panel.subtitle": "Все вопросы и ответы из вашей SQL базы",
        "admin.panel.add_title": "Добавить вопрос",
        "admin.panel.add_subtitle": "Создайте новый вопрос для игры прямо из админки",
        "admin.panel.level": "Уровень",
        "admin.panel.question": "Вопрос",
        "admin.panel.correct": "Правильный",
        "admin.panel.correct_answer": "Правильный ответ",
        "admin.panel.add": "Добавить вопрос",
        "admin.panel.loaded": "Загружено вопросов: {count}",
        "admin.panel.pick_left": "Выберите вопрос слева, чтобы увидеть правильный ответ и варианты.",
        "admin.panel.pick_details": "Выберите вопрос слева, чтобы увидеть варианты A/B/C/D и правильный ответ.",
        "admin.panel.option": "Вариант {key}",
        "admin.panel.correct_details": "Правильный ответ: {key}",
    },
    "en": {
        "menu.play": "Play",
        "menu.settings": "Settings",
        "menu.stats": "Statistics",
        "menu.exit": "Exit",
        "common.menu": "Menu",
        "common.close": "Close",
        "common.back": "Back",
        "common.update": "Refresh",
        "common.export": "Export",
        "common.special": "Special",
        "settings.sfx": "SFX",
        "settings.music": "MUSIC",
        "settings.vibration": "VIBRATION",
        "settings.language": "LANGUAGE",
        "settings.language.ru": "Rus",
        "settings.language.en": "Eng",
        "settings.language.ky": "Kyr",
        "settings.export_title": "Export Data",
        "settings.export_subtitle": "Choose a format for exporting questions and game results",
        "settings.export.json": "JSON",
        "settings.export.csv": "CSV",
        "settings.export.txt": "TXT",
        "status.menu": "Main menu",
        "status.leaderboard": "Leaderboard",
        "status.settings": "Settings",
        "status.admin_login": "Admin sign in",
        "status.admin_panel": "Admin panel",
        "status.game_started": "Game started",
        "status.language_switched": "Language changed: {language}",
        "game.round": "Round {current}/{total}",
        "game.question": "Question:",
        "game.correct": "Correct!",
        "game.correct_2x": "Correct! 2X is active: jump +2 levels",
        "game.wrong_menu": "Wrong answer. Returning to main menu...",
        "game.finish": "Game finished",
        "game.finish_title": "Result:",
        "game.finish_text": "Congratulations! You reached {amount}",
        "game.error_title": "Error:",
        "game.error_questions": "Not enough questions ({difficulty})",
        "game.returning_menu": "Returning to menu...",
        "game.lifeline.used_5050": "50/50 has already been used",
        "game.lifeline.used_2x": "2X has already been used",
        "game.lifeline.used_phoenix": "Phoenix has already been used",
        "game.lifeline.active_phoenix": "Phoenix is already active",
        "game.lifeline.applied_5050": "50/50: two wrong answers removed",
        "game.lifeline.applied_2x": "2X activated: on a correct answer you skip +2 levels",
        "game.lifeline.applied_phoenix": "Phoenix activated: one mistake will be forgiven",
        "game.lifeline.saved_phoenix": "Phoenix saves you. A new question of the same level is loading...",
        "game.leave.title": "Leave to menu?",
        "game.leave.body": "If you leave now, your current round progress will be lost.",
        "game.leave.stay": "Return",
        "game.leave.menu": "Menu",
        "game.currency_suffix": "som",
        "leaderboard.title": "Leaderboard",
        "leaderboard.subtitle": "Top results by number of correct answers",
        "leaderboard.player": "Player",
        "leaderboard.difficulty": "Difficulty",
        "leaderboard.correct": "Correct",
        "leaderboard.asked": "Questions",
        "leaderboard.win": "Win",
        "leaderboard.date": "Date",
        "leaderboard.refresh": "Refresh",
        "leaderboard.back": "Back to menu",
        "leaderboard.empty": "No data",
        "difficulty.easy": "Easy",
        "difficulty.medium": "Medium",
        "difficulty.hard": "Hard",
        "difficulty.mixed": "Mixed",
        "yes": "Yes",
        "no": "No",
        "admin.login.title": "Sign in",
        "admin.login.subtitle": "Sign in and start managing your questions!",
        "admin.login.remember": "Remember me",
        "admin.login.forgot": "Forgot password?",
        "admin.login.submit": "Start as Admin",
        "admin.login.empty": "Enter login and admin code.",
        "admin.login.success": "Signed in",
        "admin.panel.title": "Question Bank",
        "admin.panel.subtitle": "All questions and answers from your SQL database",
        "admin.panel.add_title": "Add Question",
        "admin.panel.add_subtitle": "Create a new question for the game right from admin mode",
        "admin.panel.level": "Level",
        "admin.panel.question": "Question",
        "admin.panel.correct": "Correct",
        "admin.panel.correct_answer": "Correct answer",
        "admin.panel.add": "Add Question",
        "admin.panel.loaded": "Loaded questions: {count}",
        "admin.panel.pick_left": "Select a question on the left to see the correct answer and all options.",
        "admin.panel.pick_details": "Select a question on the left to view options A/B/C/D and the correct answer.",
        "admin.panel.option": "Option {key}",
        "admin.panel.correct_details": "Correct answer: {key}",
    },
    "ky": {
        "menu.play": "Ойноо",
        "menu.settings": "Орнотуулар",
        "menu.stats": "Статистика",
        "menu.exit": "Чыгуу",
        "common.menu": "Меню",
        "common.close": "Жабуу",
        "common.back": "Артка",
        "common.update": "Жаңыртуу",
        "common.export": "Export",
        "common.special": "Special",
        "settings.sfx": "SFX",
        "settings.music": "MUSIC",
        "settings.vibration": "VIBRATION",
        "settings.language": "ТИЛ",
        "settings.language.ru": "Орус",
        "settings.language.en": "Англ",
        "settings.language.ky": "Кыргыз",
        "settings.export_title": "Маалыматты экспорттоо",
        "settings.export_subtitle": "Суроолор менен оюн жыйынтыктарын экспорттоо форматын тандаңыз",
        "settings.export.json": "JSON",
        "settings.export.csv": "CSV",
        "settings.export.txt": "TXT",
        "status.menu": "Башкы меню",
        "status.leaderboard": "Рекорддор",
        "status.settings": "Орнотуулар",
        "status.admin_login": "Админге кирүү",
        "status.admin_panel": "Админ панель",
        "status.game_started": "Оюн башталды",
        "status.language_switched": "Тил өзгөртүлдү: {language}",
        "game.round": "Раунд {current}/{total}",
        "game.question": "Суроо:",
        "game.correct": "Туура!",
        "game.correct_2x": "Туура! 2X активдүү: +2 деңгээл секирет",
        "game.wrong_menu": "Туура эмес. Башкы менюга кайтуу...",
        "game.finish": "Оюн аяктады",
        "game.finish_title": "Жыйынтык:",
        "game.finish_text": "Куттуктайбыз! Сиз {amount} деңгээлине жеттиңиз",
        "game.error_title": "Ката:",
        "game.error_questions": "Суроолор жетишсиз ({difficulty})",
        "game.returning_menu": "Менюга кайтуу...",
        "game.lifeline.used_5050": "50/50 буга чейин колдонулган",
        "game.lifeline.used_2x": "2X буга чейин колдонулган",
        "game.lifeline.used_phoenix": "Феникс буга чейин колдонулган",
        "game.lifeline.active_phoenix": "Феникс мурунтан активдүү",
        "game.lifeline.applied_5050": "50/50: эки туура эмес жооп алынды",
        "game.lifeline.applied_2x": "2X активдешти: туура жоопто +2 деңгээл өтөсүз",
        "game.lifeline.applied_phoenix": "Феникс активдешти: бир ката кечирилет",
        "game.lifeline.saved_phoenix": "Феникс сактап калды. Ушул эле деңгээлдеги жаңы суроо жүктөлүүдө...",
        "game.leave.title": "Менюга чыгасызбы?",
        "game.leave.body": "Азыр чыксаңыз, ушул раунддагы прогресс жоголот.",
        "game.leave.stay": "Кайтуу",
        "game.leave.menu": "Менюга",
        "game.currency_suffix": "сом",
        "leaderboard.title": "Рекорддор",
        "leaderboard.subtitle": "Туура жооптордун саны боюнча мыкты жыйынтыктар",
        "leaderboard.player": "Оюнчу",
        "leaderboard.difficulty": "Кыйынчылык",
        "leaderboard.correct": "Туура",
        "leaderboard.asked": "Суроолор",
        "leaderboard.win": "Жеңиш",
        "leaderboard.date": "Дата",
        "leaderboard.refresh": "Жаңыртуу",
        "leaderboard.back": "Менюга кайтуу",
        "leaderboard.empty": "Маалымат жок",
        "difficulty.easy": "Жеңил",
        "difficulty.medium": "Орто",
        "difficulty.hard": "Оор",
        "difficulty.mixed": "Аралаш",
        "yes": "Ооба",
        "no": "Жок",
        "admin.login.title": "Кирүү",
        "admin.login.subtitle": "Суроолорду башкаруу үчүн кириңиз!",
        "admin.login.remember": "Эсимде сакта",
        "admin.login.forgot": "Сырсөз унутулдубу?",
        "admin.login.submit": "Админ болуп кирүү",
        "admin.login.empty": "Login жана admin code киргизиңиз.",
        "admin.login.success": "Кирүү аткарылды",
        "admin.panel.title": "Суроолор банкы",
        "admin.panel.subtitle": "SQL базаңыздагы бардык суроолор жана жооптор",
        "admin.panel.add_title": "Суроо кошуу",
        "admin.panel.add_subtitle": "Админ режиминен эле оюнга жаңы суроо кошуңуз",
        "admin.panel.level": "Деңгээл",
        "admin.panel.question": "Суроо",
        "admin.panel.correct": "Туура",
        "admin.panel.correct_answer": "Туура жооп",
        "admin.panel.add": "Суроо кошуу",
        "admin.panel.loaded": "Жүктөлгөн суроолор: {count}",
        "admin.panel.pick_left": "Сол жактан суроо тандап, туура жооп менен варианттарды көрүңүз.",
        "admin.panel.pick_details": "Сол жактан суроо тандап, A/B/C/D варианттары менен туура жоопту көрүңүз.",
        "admin.panel.option": "Вариант {key}",
        "admin.panel.correct_details": "Туура жооп: {key}",
    },
}


class I18n:
    def __init__(self, translations_dir: Path) -> None:
        self.translations_dir = translations_dir
        self.question_maps: dict[str, dict[str, dict[str, dict[str, object]]]] = {}
        self._load_question_maps()

    def _load_question_maps(self) -> None:
        for language in SUPPORTED_LANGUAGES:
            if language == "ru":
                continue
            path = self.translations_dir / f"{language}.json"
            if not path.exists():
                continue
            raw = json.loads(path.read_text(encoding="utf-8"))
            mapping: dict[str, dict[str, dict[str, object]]] = {}
            for difficulty_key, items in raw.items():
                normalized = "medium" if difficulty_key == "meduim" else str(difficulty_key)
                per_question: dict[str, dict[str, object]] = {}
                for item in items:
                    source_question = str(item.get("source_question", "")).strip()
                    if not source_question:
                        continue
                    per_question[source_question] = {
                        "question": str(item.get("question", "")).strip() or source_question,
                        "options": [str(value).strip() for value in item.get("options", [])][:4],
                    }
                mapping[normalized] = per_question
            self.question_maps[language] = mapping

    def language_name(self, language: str) -> str:
        return LANGUAGE_NAMES.get(language, language)

    def tr(self, lang_code: str, message_key: str, **kwargs) -> str:
        catalog = UI_STRINGS.get(lang_code) or UI_STRINGS["ru"]
        text = catalog.get(message_key) or UI_STRINGS["ru"].get(message_key) or message_key
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text

    def localize_questions(
        self,
        base_questions: dict[Difficulty, list[Question]],
        language: str,
    ) -> dict[Difficulty, list[Question]]:
        if language == "ru":
            return {
                difficulty: [question for question in questions]
                for difficulty, questions in base_questions.items()
            }

        localized: dict[Difficulty, list[Question]] = {}
        language_map = self.question_maps.get(language, {})
        for difficulty, questions in base_questions.items():
            difficulty_map = language_map.get(difficulty.value, {})
            translated_questions: list[Question] = []
            for question in questions:
                translated = difficulty_map.get(question.text)
                if translated is None:
                    translated_questions.append(question)
                    continue
                options = translated.get("options", [])
                if not isinstance(options, list) or len(options) != 4:
                    translated_questions.append(question)
                    continue
                translated_questions.append(
                    Question(
                        text=str(translated.get("question", question.text)) or question.text,
                        options=[str(value) for value in options],
                        correct_index=question.correct_index,
                        difficulty=question.difficulty,
                    )
                )
            localized[difficulty] = translated_questions
        return localized
