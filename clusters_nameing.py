import os
from pathlib import Path
import logging
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ===============================
# НАСТРОЙКИ — МЕНЯЙ ТОЛЬКО ЭТО
# ===============================

FILE_PATH = ".xlsx"          # Excel-файл
COLUMN_NAME = "m"                 # Имя или индекс колонки
OUTPUT_TEXT_FILE = "результат.txt"

API_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = os.getenv("OPENROUTER_API_KEY") or "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"

BASE_PROMPT_PATH =  "baseNamingPrompt.txt"

with open("baseNamingPrompt.txt", "r", encoding="utf-8") as f:
    BASE_PROMPT = f.read()



logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)



def create_session():
    session = requests.Session()
    retry = Retry(total=5, connect=5, read=5, backoff_factor=0.4,
                  status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    return session


def read_column(file_path, column_name):
    file = Path(file_path)
    if not file.exists():
        raise FileNotFoundError(f"Файл не найден: {file_path}")

    df = pd.read_excel(file)

    # Имя колонки
    if isinstance(column_name, str) and column_name in df.columns:
        return df[column_name]

    # Строка -> число
    if isinstance(column_name, str) and column_name.isdigit():
        column_name = int(column_name)

    # Индекс колонки
    if isinstance(column_name, int):
        if column_name >= len(df.columns):
            raise IndexError(f"Колонка {column_name} вне диапазона.")
        return df.iloc[:, column_name]

    raise KeyError(f"Колонка '{column_name}' не найдена.")


def extract_content(response_json):
    """Безопасно достаём текст"""
    try:
        return response_json["choices"][0]["message"]["content"]
    except:
        raise ValueError("API вернул неожиданный формат.")


def main():
    if "ВСТАВЬ_СЮДА_СВОЙ_КЛЮЧ" in API_KEY:
        logger.warning("⚠ API ключ нужно указать в переменной API_KEY или OPENROUTER_API_KEY")

    try:
        col = read_column(FILE_PATH, COLUMN_NAME)
    except Exception as e:
        logger.error(f"Ошибка чтения Excel: {e}")
        return

    # Обработка колонки → строка
    values = col.dropna().astype(str).map(str.strip)
    values = values[values != ""]
    combined = "".join(values)

    logger.info(f"Объединено {len(combined)} символов.")

    with open("clusters_report.txt", "r", encoding="utf-8") as f:
        combined = f.read()



    # Подготовка промпта
    prompt = BASE_PROMPT + combined

    # HTTP-сессия
    session = create_session()

    logger.info("Отправляю запрос к API...")

    try:
        response = session.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "meta-llama/llama-3.3-70b-instruct:free",
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=20
        )
        response.raise_for_status()

        data = response.json()
        text = extract_content(data)

    except Exception as e:
        logger.error(f"Ошибка API: {e}")
        return

    # Сохраняем результат
    Path(OUTPUT_TEXT_FILE).write_text(text, encoding="utf-8")
    logger.info(f"Готово! Результат сохранён в: {OUTPUT_TEXT_FILE}")


main()