# Telegram-бот для Polymarket Temperature

Цей інструмент шукає в Polymarket картки з категорії `Temperature`, де сума `best ask` усіх кошиків в одній картці більша за `100¢`.

Бот нічого не купує і не торгує. Він лише знаходить такі картки та показує їх у Telegram за командою `/scan`.

## Що потрібно для роботи

- Windows-комп'ютер
- Telegram-акаунт
- Створений Telegram-бот через `@BotFather`
- Python 3.12

## Що отримаєте

- команду `/start` з коротким поясненням;
- команду `/help` з підказкою;
- команду `/scan`, яка перевіряє активні ринки `Temperature` і повертає короткий список знайдених карток.

## Як бот працює

1. Знаходить категорію `temperature` через Polymarket API.
2. Отримує всі активні події цієї категорії.
3. Для кожної картки дивиться всі її кошики.
4. Бере `best ask` для кожного кошика.
5. Якщо прямого `best ask` у картці немає, намагається добрати його через order book.
6. Складає ціни всіх кошиків.
7. Якщо сума більша за `100¢`, показує цю картку у відповіді.

## Простий запуск на Windows

### Крок 1. Встановіть Python 3.12

1. Відкрийте сайт [python.org](https://www.python.org/downloads/).
2. Встановіть Python 3.12.
3. Під час встановлення поставте галочку `Add Python to PATH`, якщо вона з'явиться.

### Крок 2. Створіть Telegram-бота

1. Відкрийте Telegram.
2. Знайдіть `@BotFather`.
3. Надішліть команду `/newbot`.
4. Дайте ім'я боту.
5. Дайте унікальне username для бота.
6. `@BotFather` надішле вам токен. Скопіюйте його.

### Крок 3. Підготуйте файл налаштувань

1. У папці проєкту знайдіть файл `env-example.txt`.
2. Зробіть його копію з назвою `.env`.
3. Відкрийте `.env` у Блокноті.
4. Вставте свій токен після знака `=`.

Приклад:

```env
TELEGRAM_BOT_TOKEN=123456:ABC-your-real-token
ALLOWED_CHAT_ID=
```

Поле `ALLOWED_CHAT_ID` можна поки залишити порожнім. Тоді бот відповідатиме в будь-якому чаті, де ви з ним спілкуєтесь.

### Крок 4. Запустіть бота

Найпростіший спосіб:

1. Двічі натисніть на файл [run_bot.bat](C:\Users\Admin\Documents\New project\run_bot.bat).
2. Зачекайте, поки відкриється чорне вікно.
3. Перший запуск може тривати довше, бо програма встановить потрібні пакети.
4. Не закривайте це вікно, поки хочете, щоб бот працював.

Альтернатива через PowerShell:

```powershell
cd "C:\Users\Admin\Documents\New project"
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python bot.py
```

## Як почати користуватися

1. Знайдіть свого бота в Telegram.
2. Натисніть `Start` або надішліть `/start`.
3. Для перевірки ринків надішліть `/scan`.

## Як виглядає відповідь

Бот надсилає:

- назву картки;
- загальну суму `best ask`;
- короткий список кошиків з цінами;
- посилання на Polymarket.

Якщо нічого не знайдено, бот напише, що зараз таких карток немає.

## Як зробити бота тільки для себе

Це опційно.

1. Напишіть боту будь-яке повідомлення.
2. Дізнайтесь свій Telegram chat id через будь-який зручний сервіс або окремого info-бота.
3. Вставте це число у `.env` після `ALLOWED_CHAT_ID=`.
4. Перезапустіть бота.

Після цього бот відповідатиме лише у вашому чаті.

## Якщо бот не відповідає

Перевірте по черзі:

1. Чи запущене вікно з програмою.
2. Чи правильно вставлений токен у `.env`.
3. Чи є інтернет.
4. Чи не повертає Polymarket тимчасову помилку.
5. Чи не обмежили ви доступ через `ALLOWED_CHAT_ID`.

## Запуск у хмарі

### Railway

Найзручніший варіант для постійної роботи.

1. Створіть акаунт на [Railway](https://railway.app/).
2. Завантажте цей проєкт у GitHub.
3. Створіть новий проєкт у Railway з цього репозиторію.
4. У змінні середовища Railway додайте:
   - `TELEGRAM_BOT_TOKEN`
   - `ALLOWED_CHAT_ID` за бажанням
5. Команда запуску:

```text
python bot.py
```

### Render

1. Створіть акаунт на [Render](https://render.com/).
2. Підключіть GitHub-репозиторій.
3. Створіть `Background Worker`.
4. Додайте ті самі змінні середовища.
5. Для старту використайте:

```text
pip install -r requirements.txt && python bot.py
```

## Для розробника або перевірки

Запуск тестів:

```powershell
python -m unittest discover -s tests -v
```

## Структура файлів

- [bot.py](C:\Users\Admin\Documents\New project\bot.py) — точка запуску
- [polymarket_bot\telegram_bot.py](C:\Users\Admin\Documents\New project\polymarket_bot\telegram_bot.py) — Telegram-команди
- [polymarket_bot\polymarket.py](C:\Users\Admin\Documents\New project\polymarket_bot\polymarket.py) — запити до Polymarket
- [polymarket_bot\scanner.py](C:\Users\Admin\Documents\New project\polymarket_bot\scanner.py) — логіка пошуку
- [run_bot.bat](C:\Users\Admin\Documents\New project\run_bot.bat) — простий запуск у Windows
