# Ozon CSV Parser (без Telegram, без pandas)

Версия парсера Ozon, которая **не использует pandas**, чтобы не страдать с несовместимостью Python 3.13 и сборкой C-расширений.

## Возможности

- Поисковый запрос по Ozon (`text=...`)
- Сбор ссылок на товары с первой страницы
- Парсинг:
  - ID товара (артикул, из URL)
  - Название
  - Цена
  - Рейтинг
  - Количество отзывов
  - Ссылка
- Сохранение в CSV локально (через стандартный модуль `csv`)
- Никакого Telegram, ботов и внешних сервисов

## Установка

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

## Запуск

```bash
python ozon_csv_parser.py -q "игровая мышь" -o ozon_mice.csv -m 20
python ozon_csv_parser.py -s "https://www.ozon.ru/seller/dareu-2265016/" -p 5 -m 100 -o dareu_mice.csv 
python ozon_parser.py -u "https://www.ozon.ru/product/logitech-g-g502-hero-..." -o one_mouse.csv

```

Параметры:

- `-q / --query` — текст поискового запроса (обязательно)
- `-o / --output` — путь к CSV файлу (по умолчанию `ozon_results.csv`)
- `-p / --pages` — количество страниц (пока что используется 1, но параметр оставлен для будущего)
- `-m / --max-products` — максимальное количество товаров для парсинга
- `-u / --url` — ссылка на один конкретно товар
- `-s / --seller` — ссылка на один конкретно дилера
