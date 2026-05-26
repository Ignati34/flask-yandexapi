# Flask YandexART Logo Generator

Учебное Flask-приложение для генерации логотипов через Yandex Art API.

## Что доработано

- Удобный UI для ввода названия компании, выбора стиля и формы логотипа.
- AJAX-генерация без перезагрузки страницы.
- Loader во время ожидания результата.
- Доработка существующего логотипа через тот же `seed`.
- Сохранение PNG в `static/generated/`.
- Кнопка скачивания готового логотипа.
- `/health` endpoint для проверки сервиса.
- Demo mode: приложение работает без API-ключа и создает учебный PNG-логотип локально.

## Быстрый запуск

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
pip install -r requirements.txt
cp env.example .env
python app.py
```

Откройте в браузере:

```text
http://127.0.0.1:5000
```

## Подключение Yandex Art API

Заполните `.env`:

```env
YANDEX_API_KEY=ваш_api_key
FOLDER_ID=ваш_folder_id
DEMO_MODE=auto
```

Если ключи не указаны, приложение автоматически использует demo mode.
