from flask import Flask, request, jsonify
from flask_cors import CORS
from flasgger import Swagger
import pymysql
import subprocess
import tempfile
import csv
import json
import os
import re
import sys
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import jwt  # Для JWT токенов
import time
import random

app = Flask(__name__)
CORS(app)

# Секретный ключ для JWT (в продакшене должен быть сложным и храниться в env)
app.config['SECRET_KEY'] = 'your-super-secret-jwt-key-change-in-production'

# Настройка Swagger
app.config['SWAGGER'] = {
    'title': 'Ozon & Wildberries Parser API',
    'uiversion': 3,
    'specs_route': '/apidocs/',
    'headers': [],
    'specs': [
        {
            'endpoint': 'apispec_1',
            'route': '/apispec_1.json',
            'rule_filter': lambda rule: True,
            'model_filter': lambda tag: True,
        }
    ],
    'static_url_path': '/flasgger_static',
    'swagger_ui': True,
    'swagger_ui_bundle_js': '//unpkg.com/swagger-ui-dist@3/swagger-ui-bundle.js',
    'swagger_ui_standalone_preset_js': '//unpkg.com/swagger-ui-dist@3/swagger-ui-standalone-preset.js',
    'swagger_ui_css': '//unpkg.com/swagger-ui-dist@3/swagger-ui.css',
    'favicon': 'https://flask.palletsprojects.com/en/2.3.x/_static/flask-icon.png'
}

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_1.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Ozon & Wildberries Parser API with Auth",
        "description": "API для парсинга продавцов Ozon и Wildberries с аутентификацией пользователей.",
        "version": "1.0.0",
        "contact": {
            "name": "API Support",
            "email": "support@example.com"
        }
    },
    "host": "localhost:5000",
    "basePath": "/",
    "schemes": ["http"],
    "tags": [
        {
            "name": "Аутентификация",
            "description": "Эндпоинты для регистрации и авторизации пользователей"
        },
        {
            "name": "Парсинг",
            "description": "Эндпоинты для парсинга маркетплейсов"
        },
        {
            "name": "Данные",
            "description": "Эндпоинты для работы с данными"
        },
        {
            "name": "Отладка",
            "description": "Эндпоинты для отладки системы"
        }
    ],
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "Введите: Bearer {ваш_токен}"
        }
    }
}

# Инициализация Swagger
swagger = Swagger(app, config=swagger_config, template=swagger_template)

# Конфигурация БД
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'marketplace_db',
    'port': 3306,
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}


def get_db():
    """Подключение к БД"""
    return pymysql.connect(**DB_CONFIG)


def check_and_fix_table_structure():
    """Проверяет и исправляет структуру таблицы users"""
    try:
        conn = get_db()
        with conn.cursor() as cursor:
            # Проверяем, существует ли таблица users
            cursor.execute("SHOW TABLES LIKE 'users'")
            table_exists = cursor.fetchone()

            if not table_exists:
                print("❌ Таблица 'users' не существует, создаю...")
                cursor.execute("""
                    CREATE TABLE users (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        email VARCHAR(100) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP NULL,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                """)
                conn.commit()
                print("✅ Таблица 'users' создана")
                return True

            # Проверяем структуру существующей таблицы
            cursor.execute("DESCRIBE users")
            columns = cursor.fetchall()
            column_names = [col['Field'] for col in columns]

            print(f"📊 Структура таблицы users: {column_names}")

            # Проверяем наличие обязательных колонок
            required_columns = ['username', 'email', 'password_hash']
            missing_columns = []

            for req_col in required_columns:
                if req_col not in column_names:
                    missing_columns.append(req_col)

            if missing_columns:
                print(f"⚠️ В таблице users отсутствуют колонки: {missing_columns}")
                print("🔄 Пробую пересоздать таблицу...")

                # Сначала делаем backup если есть данные
                cursor.execute("SELECT COUNT(*) as count FROM users")
                count_result = cursor.fetchone()
                has_data = count_result['count'] > 0 if count_result else False

                if has_data:
                    print("⚠️ В таблице есть данные! Создаю новую таблицу users_new")

                    # Создаем новую таблицу с правильной структурой
                    cursor.execute("""
                        CREATE TABLE users_new (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            username VARCHAR(50) UNIQUE NOT NULL,
                            email VARCHAR(100) UNIQUE NOT NULL,
                            password_hash VARCHAR(255) NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            last_login TIMESTAMP NULL,
                            is_active BOOLEAN DEFAULT TRUE
                        )
                    """)

                    # Переименовываем таблицы
                    cursor.execute("DROP TABLE IF EXISTS users_old")
                    cursor.execute("RENAME TABLE users TO users_old, users_new TO users")
                    print("✅ Таблица пересоздана, старые данные в users_old")
                else:
                    # Если данных нет, просто пересоздаем
                    cursor.execute("DROP TABLE users")
                    cursor.execute("""
                        CREATE TABLE users (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            username VARCHAR(50) UNIQUE NOT NULL,
                            email VARCHAR(100) UNIQUE NOT NULL,
                            password_hash VARCHAR(255) NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            last_login TIMESTAMP NULL,
                            is_active BOOLEAN DEFAULT TRUE
                        )
                    """)
                    print("✅ Таблица пересоздана")

                conn.commit()

            return True

    except Exception as e:
        print(f"❌ Ошибка при проверке структуры таблицы: {e}")
        return False
    finally:
        if conn:
            conn.close()


def init_database():
    """Инициализация таблиц products и users"""
    try:
        conn = get_db()
        with conn.cursor() as cursor:
            # Таблица для товаров
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    seller_id VARCHAR(255),
                    title TEXT,
                    brand VARCHAR(255),
                    category VARCHAR(255),
                    price DECIMAL(12, 2),
                    platform VARCHAR(20) DEFAULT 'ozon',
                    rating DECIMAL(3, 2),
                    image_url TEXT,
                    product_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_seller_platform (seller_id, platform),
                    INDEX idx_platform (platform)
                )
            """)

            conn.commit()

        # Проверяем и исправляем структуру таблицы users
        check_and_fix_table_structure()

        print("✅ Таблицы 'products' и 'users' готовы")
        return True
    except Exception as e:
        print(f"❌ Ошибка БД: {e}")
        return False


def extract_seller_id(url):
    """Извлекает ID продавца из URL"""
    if not url:
        return "unknown"

    patterns = [
        r'/seller/([^/]+)',
        r'seller-(\d+)',
        r'seller/([^/?]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return "unknown"


def extract_wb_entity_info(url):
    """Извлекает информацию о сущности Wildberries из URL."""
    patterns = [
        {'type': 'seller', 'pattern': r'/seller/(\d+)', 'name': None},
        {'type': 'seller', 'pattern': r'seller=(\d+)', 'name': None},
        {'type': 'brand', 'pattern': r'/brands/([^/?]+)', 'name': None},
        {'type': 'brand', 'pattern': r'wildberries\.ru/brands/([^/?]+)', 'name': None},
        {'type': 'brand', 'pattern': r'/brand/([^/?]+)', 'name': None},
        {'type': 'brand', 'pattern': r'wildberries\.ru/brand/([^/?]+)', 'name': None}
    ]

    for pattern_info in patterns:
        match = re.search(pattern_info['pattern'], url)
        if match:
            entity_id = match.group(1)

            if pattern_info['type'] == 'brand':
                entity_name = entity_id.replace('-', ' ').title()
                return {
                    'type': pattern_info['type'],
                    'id': entity_id,
                    'name': entity_name
                }
            else:
                return {
                    'type': pattern_info['type'],
                    'id': entity_id,
                    'name': f"Продавец {entity_id}"
                }

    return None


def save_to_database(products, seller_id, platform='ozon'):
    """Сохраняет товары в БД"""
    saved_count = 0

    try:
        conn = get_db()
        with conn.cursor() as cursor:
            for product in products:
                try:
                    price = None
                    if product.get('PRICE') or product.get('price'):
                        price_str = product.get('PRICE') or product.get('price') or ''
                        price_clean = re.sub(r'[^\d.]', '', str(price_str))
                        if price_clean:
                            try:
                                price = float(price_clean)
                            except:
                                price = None

                    title = product.get('NAME') or product.get('title') or product.get('name') or ''
                    brand = product.get('BRAND') or product.get('brand') or ''
                    category = product.get('SUBCATEGORY') or product.get('category') or product.get('subcategory') or ''

                    # Для Wildberries получаем дополнительные поля
                    rating = product.get('rating') or product.get('RATING')
                    if rating:
                        try:
                            rating = float(rating)
                        except:
                            rating = None

                    image_url = product.get('image') or product.get('IMAGE') or product.get('image_url') or ''
                    product_url = product.get('url') or product.get('URL') or ''

                    cursor.execute("""
                        INSERT INTO products (seller_id, title, brand, category, price, platform, rating, image_url, product_url)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        seller_id,
                        title[:500] if title else '',
                        brand[:255] if brand else '',
                        category[:255] if category else '',
                        price,
                        platform,
                        rating,
                        image_url[:500] if image_url else '',
                        product_url[:500] if product_url else ''
                    ))
                    saved_count += 1
                except Exception as e:
                    print(f"⚠️ Ошибка сохранения товара: {e}")
                    continue

        conn.commit()
        conn.close()
        return saved_count

    except Exception as e:
        print(f"❌ Ошибка БД при сохранении: {e}")
        return 0


class WildberriesSellerParser:
    def __init__(self, headless=True, delay_range=(3, 7)):
        self.delay_range = delay_range
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
        ]
        print("🚀 Инициализация браузера Wildberries...")
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager

            self.driver = self._init_driver(headless)
            from selenium.webdriver.support.ui import WebDriverWait
            self.wait = WebDriverWait(self.driver, 30)
            print("✅ Браузер Wildberries готов.")
        except ImportError as e:
            print(f"❌ Ошибка импорта Selenium: {e}")
            print("📦 Установите зависимости: pip install selenium webdriver-manager")
            self.driver = None
        except Exception as e:
            print(f"❌ Ошибка инициализации браузера: {e}")
            self.driver = None

    def _init_driver(self, headless):
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager

        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")

        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(f"--user-agent={random.choice(self.user_agents)}")
        chrome_options.add_argument("--lang=ru-RU,ru;q=0.9")
        chrome_options.add_argument("--accept-lang=ru-RU,ru;q=0.9")

        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-notifications")

        chrome_options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.cookies": 1,
            "profile.block_third_party_cookies": False,
        })

        try:
            # Пробуем автоматическую установку драйвера
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)

            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                    window.chrome = { runtime: {} };
                '''
            })

            return driver
        except Exception as e:
            print(f"❌ Ошибка при автоматической установке драйвера: {e}")
            print("🔄 Пробую ручной путь к Chrome...")
            try:
                # Пробуем найти Chrome в стандартных путях
                chrome_paths = [
                    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
                    os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe"),
                    "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
                ]

                for chrome_path in chrome_paths:
                    if os.path.exists(chrome_path):
                        print(f"✅ Найден Chrome по пути: {chrome_path}")
                        chrome_options.binary_location = chrome_path
                        break

                # Используем драйвер без Service
                driver = webdriver.Chrome(options=chrome_options)
                return driver
            except Exception as e2:
                print(f"❌ Ошибка при ручной настройке: {e2}")
                print("📋 Инструкция по установке:")
                print("1. Установите Google Chrome: https://www.google.com/chrome/")
                print("2. Или установите Microsoft Edge")
                print("3. Убедитесь, что браузер установлен в одной из стандартных папок")
                raise Exception(f"Не удалось инициализировать браузер. Установите Chrome или Edge. Ошибка: {str(e2)}")

    def _smart_delay(self, custom_range=None):
        min_d, max_d = custom_range if custom_range else self.delay_range
        delay = random.uniform(min_d, max_d)
        print(f"   ⏳ Ожидание {delay:.1f} сек...")
        time.sleep(delay)
        return delay

    def parse_seller_products(self, seller_url, max_products=50):
        """
        Парсит все товары продавца или бренда по ссылке.
        Пример ссылки: https://www.wildberries.ru/seller/42582
        Или: https://www.wildberries.ru/brands/fashion-lines
        """
        if not self.driver:
            print("❌ Браузер не инициализирован")
            return []

        print(f"\n🏪 Начинаю парсинг Wildberries...")
        print(f"📡 URL: {seller_url}")

        # Определяем тип ссылки и извлекаем идентификатор
        entity_info = extract_wb_entity_info(seller_url)
        if not entity_info:
            print("❌ Не удалось определить тип страницы Wildberries")
            return []

        entity_id = entity_info['id']
        entity_type = entity_info['type']
        entity_name = entity_info['name']

        if entity_type == "seller":
            print(f"🆔 ID продавца: {entity_id}")
            seller_id = f"wb_seller_{entity_id}"
        else:
            print(f"🏷️ Бренд: {entity_name or entity_id}")
            seller_id = f"wb_brand_{entity_id}"

        all_products = []

        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support import expected_conditions as EC

            # 1. Загружаем страницу
            print(f"\n📥 Загружаю страницу...")
            self.driver.get(seller_url)
            self._smart_delay((4, 6))

            # 2. Ждем загрузки товаров и прокручиваем
            print(f"\n⬇ Загружаю товары...")
            loaded_count = self._wait_and_load_products(max_products)
            print(f"📦 Загружено товаров: {loaded_count}")

            if loaded_count == 0:
                print("❌ Не удалось загрузить товары")
                return []

            # 3. Получаем HTML
            page_source = self.driver.page_source

            # 4. Парсим товары
            print(f"\n🔄 Начинаю парсинг товаров...")
            all_products = self._parse_products_page_html(page_source, entity_info, max_products)

            # Форматируем для API
            formatted_products = []
            for product in all_products:
                formatted_product = {
                    "ID": product.get('id', ''),
                    "NAME": product.get('name', ''),
                    "BRAND": product.get('brand', ''),
                    "PRICE": product.get('price', 0),
                    "RATING": product.get('rating', 0.0),
                    "CATEGORY": product.get('category', ''),
                    "URL": product.get('url', ''),
                    "IMAGE": product.get('image', ''),
                    "PLATFORM": "wildberries",
                    "SELLER_ID": seller_id,
                    "ENTITY_TYPE": entity_type,
                    "ENTITY_NAME": entity_name
                }
                formatted_products.append(formatted_product)

            return formatted_products

        except Exception as e:
            print(f"\n❌ Ошибка при парсинге Wildberries: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _wait_and_load_products(self, max_products):
        """Ожидает загрузки товаров и прокручивает страницу."""
        print("   ⏳ Ожидаю загрузки товаров...")

        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support import expected_conditions as EC

            # Ожидаем появления товаров
            self.wait.until(
                EC.presence_element_located((By.CSS_SELECTOR,
                                             "article.product-card, div.product-card, [data-nm-id], .card, .product-card"))
            )
        except Exception as e:
            print(f"   ⚠ Товары не появились, пробую продолжить: {e}")

        # Даем время для полной загрузки
        self._smart_delay((2, 3))

        # Считаем начальное количество товаров
        try:
            from selenium.webdriver.common.by import By

            products = self.driver.find_elements(By.CSS_SELECTOR,
                                                 "article.product-card, div.product-card, [data-nm-id], .card, .product-card, article[class*='card'], div[class*='card']")
            last_count = len(products)
            print(f"   📦 Начальное количество товаров: {last_count}")
        except Exception as e:
            print(f"   ⚠ Ошибка при подсчете товаров: {e}")
            last_count = 0

        same_count = 0
        scroll_attempts = 0
        max_scrolls = 10

        while scroll_attempts < max_scrolls and last_count < max_products:
            scroll_attempts += 1

            # Прокручиваем
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self._smart_delay((2, 3))

            # Считаем товары
            try:
                from selenium.webdriver.common.by import By

                products = self.driver.find_elements(By.CSS_SELECTOR,
                                                     "article.product-card, div.product-card, [data-nm-id], .card, .product-card, article[class*='card'], div[class*='card']")
                current_count = len(products)
                print(f"   📍 Прокрутка {scroll_attempts}: {current_count} товаров")

                if current_count == last_count:
                    same_count += 1
                    if same_count >= 2:
                        print("   ✅ Загрузка товаров завершена")
                        return min(current_count, max_products)
                else:
                    same_count = 0
                    last_count = current_count

                if current_count >= max_products:
                    print(f"   ✅ Достигнуто максимальное количество: {max_products}")
                    return max_products

            except Exception as e:
                print(f"   ⚠ Ошибка при подсчете: {e}")

        return min(last_count, max_products)

    def _parse_products_page_html(self, html_content, entity_info, max_products):
        """Парсит товары со страницы."""
        from bs4 import BeautifulSoup

        products_data = []
        soup = BeautifulSoup(html_content, 'html.parser')

        print(f"   🔎 Поиск товаров...")

        # Находим все карточки товаров
        all_cards = soup.select('article.product-card, div.product-card, [data-nm-id]')

        if not all_cards:
            all_cards = soup.select('.product-card, .card, [class*="card"]')

        if not all_cards:
            print("   ❌ Товары не найдены")
            return products_data

        # Ограничиваем количество
        cards_to_process = all_cards[:max_products]
        print(f"   Найдено карточек: {len(all_cards)}")
        print(f"   Обрабатываю: {len(cards_to_process)} товаров\n")

        for idx, card in enumerate(cards_to_process, 1):
            try:
                product_data = self._parse_product_card(card, idx, entity_info)
                if product_data:
                    # Получаем категорию с отдельной страницы товара
                    print(f"   [{idx:3}] 🌐 Перехожу на страницу товара для определения категории...")
                    category = self._get_category_from_product_page(product_data['url'])
                    product_data['category'] = category

                    products_data.append(product_data)

            except Exception as e:
                print(f"   [{idx}] ⚠ Ошибка: {e}")
                continue

        print(f"\n📊 Успешно обработано: {len(products_data)} товаров")
        return products_data

    def _parse_product_card(self, card, card_number, entity_info):
        """Парсит карточку товара."""

        # Извлекаем ID
        product_id = card.get('data-nm-id', '')

        if not product_id:
            link_elem = card.select_one('a[href*="/catalog/"]')
            if link_elem:
                href = link_elem.get('href', '')
                match = re.search(r'/catalog/(\d+)/', href)
                if match:
                    product_id = match.group(1)

        if not product_id:
            return None

        # Базовые данные товара
        product_data = {
            'id': product_id,
            'url': f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx",
            'name': '',
            'brand': '',
            'price': 0,
            'rating': 0.0,
            'image': '',
            'category': '',
            'entity_id': entity_info.get('id', ''),
            'entity_type': entity_info.get('type', ''),
            'entity_name': entity_info.get('name', '')
        }

        try:
            # 1. НАЗВАНИЕ ТОВАРА
            name_selectors = [
                'span.goods-name',
                'a.goods-name',
                '.product-card__name',
                '.card__name',
                '[class*="name"]',
                '.goods-card__name',
                '.j-card-name'
            ]

            for selector in name_selectors:
                name_element = card.select_one(selector)
                if name_element:
                    name_text = name_element.get_text(strip=True)
                    if name_text and len(name_text) > 2:
                        product_data['name'] = name_text
                        break

            # 2. БРЕНД
            brand_selectors = [
                'span.brand-name',
                'a.brand-name',
                '.product-card__brand',
                '.card__brand',
                '[class*="brand"]',
                '.goods-card__brand',
                '.j-card-brand'
            ]

            for selector in brand_selectors:
                brand_element = card.select_one(selector)
                if brand_element:
                    brand_text = brand_element.get_text(strip=True)
                    if brand_text:
                        brand_text = re.sub(r'^[^a-zA-Zа-яА-Я]+', '', brand_text)
                        brand_text = re.sub(r'[^a-zA-Zа-яА-Я0-9\s&]+$', '', brand_text)
                        product_data['brand'] = brand_text.strip()
                        break

            # 3. ЦЕНА
            price_selectors = [
                'ins.price-block__final-price',
                'span.price-block__final-price',
                '.price__lower-price',
                '.lower-price',
                '.final-price',
                '[class*="price__final"]',
                '.j-final-price'
            ]

            for selector in price_selectors:
                price_element = card.select_one(selector)
                if price_element:
                    price_text = price_element.get_text(strip=True)
                    price_value = self._extract_price(price_text)
                    if price_value:
                        product_data['price'] = price_value
                        break

            # 4. РЕЙТИНГ
            rating_selectors = [
                'span.rating',
                '.product-card__rating',
                '.card__rating',
                '[class*="rating"]',
                '.goods-card__rating'
            ]

            for selector in rating_selectors:
                rating_element = card.select_one(selector)
                if rating_element:
                    rating_text = rating_element.get_text(strip=True)
                    match = re.search(r'[\d,\.]+', rating_text)
                    if match:
                        try:
                            product_data['rating'] = float(match.group().replace(',', '.'))
                        except:
                            pass
                    break

            # 5. ИЗОБРАЖЕНИЕ
            img_selectors = [
                'img[src*="images"]',
                'img[src*="wbxcontent"]',
                '.product-card__img img',
                '.card__img img',
                'img'
            ]

            for selector in img_selectors:
                img_element = card.select_one(selector)
                if img_element:
                    src = img_element.get('src') or img_element.get('data-src')
                    if src:
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif src.startswith('/'):
                            src = 'https://www.wildberries.ru' + src
                        product_data['image'] = src
                        break

            # Выводим результат
            name_display = product_data['name'][:25] if product_data['name'] else 'Без названия'
            brand_display = product_data.get('brand', 'Нет')[:12]
            price_indicator = "✅" if product_data['price'] > 0 else "⚠"

            price_display = f"{product_data['price']:,} ₽"

            print(f"   [{card_number:3}] {price_indicator} {name_display:25} | "
                  f"Бр: {brand_display:12} | "
                  f"Ц: {price_display:20} | "
                  f"⭐ {product_data['rating']:.1f}")

            return product_data

        except Exception as e:
            print(f"   [{card_number}] ❌ Ошибка парсинга: {e}")
            return None

    def _get_category_from_product_page(self, product_url):
        """Переходит на страницу товара и извлекает категорию."""
        category = "Не определена"

        try:
            # Открываем новую вкладку для товара
            original_window = self.driver.current_window_handle
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[-1])

            # Загружаем страницу товара
            self.driver.get(product_url)
            self._smart_delay((2, 4))

            # Получаем HTML страницы
            page_source = self.driver.page_source
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')

            # Ищем хлебные крошки
            breadcrumb_selectors = [
                '.breadcrumbs',
                '.breadcrumb',
                '.nav-breadcrumbs',
                '.breadcrumbs__container',
                '.bread-crumbs',
                '.catalog-breadcrumbs',
                '[class*="breadcrumb"]',
                '[class*="breadcrumbs"]'
            ]

            breadcrumb_found = False
            breadcrumb_items = []

            # Пробуем найти список элементов хлебных крошек
            for selector in ['.breadcrumbs__list', '.catalog-breadcrumbs__list', '.breadcrumbs ul', '.breadcrumbs li']:
                list_items = soup.select(f'{selector} li, {selector} > *')
                if list_items:
                    for item in list_items:
                        text = item.get_text(strip=True)
                        if text and len(text) > 1:
                            breadcrumb_items.append(text)
                    if breadcrumb_items:
                        breadcrumb_found = True
                        break

            # Если не нашли список, ищем просто текст хлебных крошек
            if not breadcrumb_found:
                for selector in breadcrumb_selectors:
                    breadcrumb_elem = soup.select_one(selector)
                    if breadcrumb_elem:
                        breadcrumb_text = breadcrumb_elem.get_text(strip=True, separator='>')
                        if breadcrumb_text:
                            items = [item.strip() for item in breadcrumb_text.split('>') if item.strip()]
                            breadcrumb_items = items
                            breadcrumb_found = True
                            break

            # Если нашли хлебные крошки, обрабатываем их
            if breadcrumb_items:
                # Фильтруем элементы
                filtered_items = []
                for item in breadcrumb_items:
                    excluded_words = [
                        'Главная', 'Главное', 'Home', 'Каталог', 'Catalog',
                        'Все товары', 'Все', 'Все категории', 'Поиск',
                        'реклама', 'промо', 'акция', 'скидка', 'распродажа',
                        'Wildberries', 'WB', 'Корзина', 'Избранное'
                    ]

                    item_lower = item.lower()
                    should_exclude = False

                    for word in excluded_words:
                        if word.lower() in item_lower:
                            should_exclude = True
                            break

                    if len(item) < 2 or len(item) > 50:
                        should_exclude = True

                    if not should_exclude:
                        filtered_items.append(item)

                # Определяем категорию
                if filtered_items:
                    candidates = filtered_items[1:-1] if len(filtered_items) > 2 else filtered_items
                    if candidates:
                        for candidate in reversed(candidates):
                            if 3 <= len(candidate) <= 40:
                                category = candidate
                                break

            # Закрываем вкладку и возвращаемся к основной
            self.driver.close()
            self.driver.switch_to.window(original_window)

            return category

        except Exception as e:
            print(f"       ⚠ Ошибка при получении категории: {e}")
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
            return category

    def _extract_price(self, text):
        """Извлекает цену из текста."""
        if not text:
            return 0

        cleaned = re.sub(r'[^\d]', '', text)
        if cleaned:
            try:
                return int(cleaned)
            except:
                return 0
        return 0

    def close(self):
        """Закрытие браузера."""
        try:
            if self.driver:
                self.driver.quit()
                print("✅ Браузер Wildberries закрыт.")
        except:
            pass


def create_user(username, email, password):
    """Создает нового пользователя с хешированным паролем"""
    try:
        # Проверяем, что таблица users существует и имеет правильную структуру
        check_and_fix_table_structure()

        # Хешируем пароль с помощью Werkzeug
        password_hash = generate_password_hash(password)

        conn = get_db()
        with conn.cursor() as cursor:
            # Проверяем структуру таблицы перед вставкой
            cursor.execute("DESCRIBE users")
            columns = cursor.fetchall()
            print(f"📋 Колонки в таблице users перед вставкой: {[col['Field'] for col in columns]}")

            cursor.execute("""
                INSERT INTO users (username, email, password_hash)
                VALUES (%s, %s, %s)
            """, (username, email, password_hash))
            user_id = cursor.lastrowid
            conn.commit()

        conn.close()
        return user_id
    except pymysql.err.IntegrityError as e:
        if 'Duplicate entry' in str(e):
            if 'username' in str(e):
                raise Exception("Пользователь с таким именем уже существует")
            elif 'email' in str(e):
                raise Exception("Пользователь с таким email уже существует")
        raise e
    except Exception as e:
        raise Exception(f"Ошибка при создании пользователя: {str(e)}")


def authenticate_user(username, password):
    """Аутентифицирует пользователя по логину и паролю"""
    try:
        conn = get_db()
        with conn.cursor() as cursor:
            # Ищем пользователя по username или email
            cursor.execute("""
                SELECT id, username, email, password_hash, is_active 
                FROM users 
                WHERE username = %s OR email = %s
            """, (username, username))

            user = cursor.fetchone()

            if not user:
                return None, "Пользователь не найден"

            if not user['is_active']:
                return None, "Аккаунт заблокирован"

            # Проверяем пароль с помощью check_password_hash
            if not check_password_hash(user['password_hash'], password):
                return None, "Неверный пароль"

            # Обновляем время последнего входа
            cursor.execute("""
                UPDATE users 
                SET last_login = CURRENT_TIMESTAMP 
                WHERE id = %s
            """, (user['id'],))
            conn.commit()

        conn.close()

        # Возвращаем пользователя без хеша пароля
        user_data = {
            'id': user['id'],
            'username': user['username'],
            'email': user['email']
        }

        return user_data, None
    except Exception as e:
        return None, f"Ошибка аутентификации: {str(e)}"


def generate_token(user_id, username):
    """Генерирует JWT токен для пользователя"""
    try:
        payload = {
            'user_id': user_id,
            'username': username,
            'exp': datetime.utcnow() + timedelta(days=7)  # Токен на 7 дней
        }
        token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
        return token
    except Exception as e:
        raise Exception(f"Ошибка генерации токена: {str(e)}")


def verify_token(token):
    """Проверяет JWT токен"""
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, "Токен истек"
    except jwt.InvalidTokenError:
        return None, "Неверный токен"
    except Exception as e:
        return None, f"Ошибка проверки токена: {str(e)}"


def token_required(f):
    """Декоратор для защиты эндпоинтов требующих аутентификации"""
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Проверяем заголовок Authorization
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

        if not token:
            return jsonify({
                'success': False,
                'error': 'Требуется токен аутентификации'
            }), 401

        payload, error = verify_token(token)
        if error:
            return jsonify({
                'success': False,
                'error': error
            }), 401

        # Добавляем данные пользователя в контекст запроса
        request.user_id = payload['user_id']
        request.username = payload['username']

        return f(*args, **kwargs)

    return decorated


# ============================================
# ЭНДПОИНТЫ АУТЕНТИФИКАЦИИ
# ============================================

@app.route('/register', methods=['POST'])
def register():
    """
    Регистрация нового пользователя
    ---
    tags:
      - Аутентификация
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - username
            - email
            - password
          properties:
            username:
              type: string
              example: "john_doe"
            email:
              type: string
              example: "john@example.com"
            password:
              type: string
              example: "secure_password123"
    responses:
      201:
        description: Пользователь успешно зарегистрирован
      400:
        description: Ошибка валидации
      409:
        description: Пользователь уже существует
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'Требуется JSON тело запроса'
            }), 400

        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        # Валидация
        if not username or not email or not password:
            return jsonify({
                'success': False,
                'error': 'Все поля (username, email, password) обязательны'
            }), 400

        if len(password) < 6:
            return jsonify({
                'success': False,
                'error': 'Пароль должен содержать минимум 6 символов'
            }), 400

        if not re.match(r'^[a-zA-Z0-9._-]+$', username):
            return jsonify({
                'success': False,
                'error': 'Имя пользователя может содержать только буквы, цифры, точку, подчеркивание и дефис'
            }), 400

        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            return jsonify({
                'success': False,
                'error': 'Неверный формат email'
            }), 400

        # Создаем пользователя
        user_id = create_user(username, email, password)

        # Генерируем токен
        token = generate_token(user_id, username)

        return jsonify({
            'success': True,
            'message': 'Пользователь успешно зарегистрирован',
            'user_id': user_id,
            'username': username,
            'email': email,
            'token': token
        }), 201

    except Exception as e:
        error_msg = str(e)
        status = 400

        if "уже существует" in error_msg:
            status = 409

        return jsonify({
            'success': False,
            'error': error_msg
        }), status


@app.route('/login', methods=['POST'])
def login():
    """
    Вход пользователя в систему
    ---
    tags:
      - Аутентификация
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
              example: "john_doe"
            password:
              type: string
              example: "secure_password123"
    responses:
      200:
        description: Успешный вход
      401:
        description: Неверные учетные данные
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'Требуется JSON тело запроса'
            }), 400

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'Username и password обязательны'
            }), 400

        # Аутентифицируем пользователя
        user_data, error = authenticate_user(username, password)

        if error:
            return jsonify({
                'success': False,
                'error': error
            }), 401

        # Генерируем токен
        token = generate_token(user_data['id'], user_data['username'])

        return jsonify({
            'success': True,
            'message': 'Вход выполнен успешно',
            'user': user_data,
            'token': token
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================
# ЭНДПОИНТЫ ПАРСИНГА
# ============================================

@app.route('/parse', methods=['GET'])
def parse_seller():
    """
    Парсинг продавца Ozon
    ---
    tags:
      - Парсинг
    parameters:
      - name: url
        in: query
        type: string
        required: true
        description: URL продавца Ozon
        example: "https://www.ozon.ru/seller/dareu-2265016/"
    responses:
      200:
        description: Результат парсинга в JSON формате
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            seller_url:
              type: string
            seller_id:
              type: string
            platform:
              type: string
            total_products:
              type: integer
            saved_to_db:
              type: integer
            products:
              type: array
              items:
                type: object
                properties:
                  ID:
                    type: string
                  NAME:
                    type: string
                  BRAND:
                    type: string
                  PRICE:
                    type: string
                  SUBCATEGORY:
                    type: string
                  URL:
                    type: string
                  RATING:
                    type: string
                  FEEDBACKS:
                    type: string
                  PLATFORM:
                    type: string
                  SELLER_ID:
                    type: string
        examples:
          application/json:
            success: true
            message: "✅ Парсинг Ozon завершен успешно!"
            seller_url: "https://www.ozon.ru/seller/dareu-2265016/"
            seller_id: "dareu-2265016"
            platform: "ozon"
            total_products: 150
            saved_to_db: 150
      400:
        description: Отсутствует URL
      500:
        description: Ошибка парсинга
    """
    try:
        # Получаем URL из query параметра
        seller_url = request.args.get('url')

        if not seller_url:
            return jsonify({
                'success': False,
                'error': 'Параметр "url" обязателен. Пример: /parse?url=https://www.ozon.ru/seller/dareu-2265016/'
            }), 400

        print(f"🚀 Начинаю парсинг продавца Ozon: {seller_url}")

        # Извлекаем seller_id
        seller_id = extract_seller_id(seller_url)
        print(f"📋 Seller ID: {seller_id}")

        # Шаг 1: Запускаем твой парсер для создания CSV
        temp_csv = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.csv',
            delete=False,
            encoding='utf-8-sig'
        )
        temp_csv.close()

        print(f"📁 Создаю временный CSV: {temp_csv.name}")

        # Запускаем ozon_csv_parser.py
        cmd = [
            'python', 'ozon_csv_parser.py',
            '-s', seller_url,
            '-o', temp_csv.name
        ]

        print(f"⚡ Запускаю парсер: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=300  # 5 минут таймаут
        )

        print(f"📊 Статус парсера: {result.returncode}")
        if result.stdout:
            print(f"📝 Вывод парсера: {result.stdout[:500]}...")
        if result.stderr:
            print(f"⚠️ Ошибки парсера: {result.stderr[:500]}...")

        # Проверяем, создался ли CSV файл
        if not os.path.exists(temp_csv.name) or os.path.getsize(temp_csv.name) == 0:
            return jsonify({
                'success': False,
                'error': 'Парсер не создал CSV файл',
                'parser_output': result.stdout,
                'parser_error': result.stderr
            }), 500

        # Шаг 2: Конвертируем CSV в JSON (как в process_products.py)
        print("🔄 Конвертирую CSV в JSON...")

        # Читаем CSV и создаем JSON структуру
        products_json = []
        with open(temp_csv.name, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            # Авто-поиск колонки ID
            columns = reader.fieldnames
            id_col = None

            for col in columns:
                if "id" in col.lower():
                    id_col = col
                    break

            if id_col is None:
                id_col = columns[0] if columns else 'id'

            for row in reader:
                product = {
                    "ID": row.get(id_col, ''),
                    "NAME": row.get("name", row.get("title", "")),
                    "BRAND": row.get("brand", ""),
                    "PRICE": row.get("price", ""),
                    "SUBCATEGORY": row.get("subcategory", row.get("category", "")),
                    "URL": row.get("url", ""),
                    "RATING": row.get("rating", ""),
                    "FEEDBACKS": row.get("feedbacks", ""),
                    "PLATFORM": "ozon",
                    "SELLER_ID": seller_id
                }
                products_json.append(product)

        print(f"✅ Спарсено товаров: {len(products_json)}")

        # Шаг 3: Сохраняем в БД
        print("💾 Сохраняю в базу данных...")
        saved_count = save_to_database(products_json, seller_id, 'ozon')

        # Шаг 4: Очищаем временные файлы
        try:
            os.unlink(temp_csv.name)
        except:
            pass

        # Возвращаем результат
        return jsonify({
            'success': True,
            'message': f'✅ Парсинг Ozon завершен успешно!',
            'seller_url': seller_url,
            'seller_id': seller_id,
            'platform': 'ozon',
            'total_products': len(products_json),
            'saved_to_db': saved_count,
            'products': products_json[:50]  # Возвращаем первые 50 товаров
        })

    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Таймаут парсинга (слишком долго)'
        }), 500
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Критическая ошибка: {error_details}")

        return jsonify({
            'success': False,
            'error': str(e),
            'details': error_details[-500:] if error_details else ''
        }), 500


@app.route('/parse-wb', methods=['GET'])
def parse_wildberries():
    """
    Парсинг продавца или бренда Wildberries
    ---
    tags:
      - Парсинг
    parameters:
      - name: url
        in: query
        type: string
        required: true
        description: URL продавца или бренда Wildberries
        example: "https://www.wildberries.ru/seller/42582"
      - name: max_products
        in: query
        type: integer
        required: false
        default: 50
        description: Максимальное количество товаров для парсинга
    responses:
      200:
        description: Результат парсинга в JSON формате
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            seller_url:
              type: string
            seller_id:
              type: string
            platform:
              type: string
            entity_type:
              type: string
            entity_id:
              type: string
            entity_name:
              type: string
            total_products:
              type: integer
            saved_to_db:
              type: integer
            products:
              type: array
              items:
                type: object
                properties:
                  ID:
                    type: string
                  NAME:
                    type: string
                  BRAND:
                    type: string
                  PRICE:
                    type: integer
                  RATING:
                    type: number
                  CATEGORY:
                    type: string
                  URL:
                    type: string
                  IMAGE:
                    type: string
                  PLATFORM:
                    type: string
                  SELLER_ID:
                    type: string
                  ENTITY_TYPE:
                    type: string
                  ENTITY_NAME:
                    type: string
            price_stats:
              type: object
              properties:
                min:
                  type: number
                max:
                  type: number
                avg:
                  type: number
                count:
                  type: integer
            rating_stats:
              type: object
              properties:
                min:
                  type: number
                max:
                  type: number
                avg:
                  type: number
                count:
                  type: integer
        examples:
          application/json:
            success: true
            message: "✅ Парсинг Wildberries завершен успешно!"
            seller_url: "https://www.wildberries.ru/seller/42582"
            seller_id: "wb_seller_42582"
            platform: "wildberries"
            entity_type: "seller"
            entity_id: "42582"
            entity_name: "Продавец 42582"
            total_products: 50
            saved_to_db: 50
      400:
        description: Отсутствует URL
      500:
        description: Ошибка парсинга или Chrome не установлен
    """
    try:
        # Получаем параметры из запроса
        seller_url = request.args.get('url')
        max_products = request.args.get('max_products', 50, type=int)

        if not seller_url:
            return jsonify({
                'success': False,
                'error': 'Параметр "url" обязателен. Пример: /parse-wb?url=https://www.wildberries.ru/seller/42582'
            }), 400

        print(f"🚀 Начинаю парсинг Wildberries: {seller_url}")

        # Извлекаем информацию о сущности
        entity_info = extract_wb_entity_info(seller_url)
        if not entity_info:
            return jsonify({
                'success': False,
                'error': 'Не удалось распознать URL Wildberries. Проверьте формат ссылки.'
            }), 400

        entity_type = entity_info['type']
        entity_id = entity_info['id']
        entity_name = entity_info['name']

        # Формируем seller_id для БД
        if entity_type == "seller":
            seller_id = f"wb_seller_{entity_id}"
        else:
            seller_id = f"wb_brand_{entity_id}"

        print(f"📋 Entity ID: {entity_id}")
        print(f"📋 Entity Type: {entity_type}")
        print(f"📋 Entity Name: {entity_name}")
        print(f"📋 Seller ID для БД: {seller_id}")
        print(f"📊 Максимальное количество товаров: {max_products}")

        # Проверяем, установлен ли Chrome
        try:
            # Создаем парсер Wildberries
            print("🔄 Инициализирую парсер Wildberries...")
            parser = WildberriesSellerParser(headless=True)

            if not parser.driver:
                return jsonify({
                    'success': False,
                    'error': 'Не удалось инициализировать браузер. Установите Google Chrome или Microsoft Edge.',
                    'installation_guide': {
                        'chrome': 'https://www.google.com/chrome/',
                        'edge': 'https://www.microsoft.com/edge',
                        'instructions': 'Установите браузер в одну из стандартных папок или укажите путь к нему'
                    }
                }), 500

            try:
                # Парсим товары
                print("🔄 Начинаю парсинг...")
                products_data = parser.parse_seller_products(seller_url, max_products)

                if not products_data:
                    return jsonify({
                        'success': False,
                        'error': 'Не удалось получить данные товаров'
                    }), 500

                print(f"✅ Спарсено товаров: {len(products_data)}")

                # Сохраняем в БД
                print("💾 Сохраняю в базу данных...")
                saved_count = save_to_database(products_data, seller_id, 'wildberries')

                # Форматируем ответ
                response_data = {
                    'success': True,
                    'message': f'✅ Парсинг Wildberries завершен успешно!',
                    'seller_url': seller_url,
                    'seller_id': seller_id,
                    'platform': 'wildberries',
                    'entity_type': entity_type,
                    'entity_id': entity_id,
                    'entity_name': entity_name,
                    'total_products': len(products_data),
                    'saved_to_db': saved_count,
                    'products': products_data[:50]  # Возвращаем первые 50 товаров
                }

                # Добавляем статистику
                if products_data:
                    prices = []
                    for p in products_data:
                        price = p.get('PRICE')
                        if isinstance(price, (int, float)):
                            prices.append(price)
                        elif isinstance(price, str):
                            try:
                                prices.append(float(price))
                            except:
                                pass

                    ratings = []
                    for p in products_data:
                        rating = p.get('RATING')
                        if isinstance(rating, (int, float)):
                            ratings.append(rating)
                        elif isinstance(rating, str):
                            try:
                                ratings.append(float(rating))
                            except:
                                pass

                    if prices:
                        response_data['price_stats'] = {
                            'min': min(prices),
                            'max': max(prices),
                            'avg': sum(prices) / len(prices),
                            'count': len(prices)
                        }

                    if ratings:
                        response_data['rating_stats'] = {
                            'min': min(ratings),
                            'max': max(ratings),
                            'avg': sum(ratings) / len(ratings),
                            'count': len(ratings)
                        }

                return jsonify(response_data)

            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"❌ Ошибка при парсинге Wildberries: {error_details}")

                return jsonify({
                    'success': False,
                    'error': str(e),
                    'details': error_details[-500:] if error_details else ''
                }), 500

            finally:
                # Закрываем парсер
                parser.close()

        except ImportError as e:
            return jsonify({
                'success': False,
                'error': 'Не установлены зависимости для парсинга Wildberries',
                'instructions': 'Установите зависимости: pip install selenium webdriver-manager beautifulsoup4'
            }), 500
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Ошибка инициализации парсера: {str(e)}',
                'chrome_install_guide': 'Установите Google Chrome: https://www.google.com/chrome/'
            }), 500

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Критическая ошибка в эндпоинте /parse-wb: {error_details}")

        return jsonify({
            'success': False,
            'error': str(e),
            'details': error_details[-500:] if error_details else ''
        }), 500


# ============================================
# ЗАЩИЩЕННЫЕ ЭНДПОИНТЫ ПРОФИЛЯ
# ============================================

@app.route('/profile', methods=['GET'])
@token_required
def get_profile():
    """
    Получить профиль текущего пользователя
    ---
    tags:
      - Аутентификация
    security:
      - Bearer: []
    responses:
      200:
        description: Профиль пользователя
        schema:
          type: object
          properties:
            success:
              type: boolean
            user:
              type: object
              properties:
                id:
                  type: integer
                username:
                  type: string
                email:
                  type: string
                created_at:
                  type: string
                last_login:
                  type: string
                is_active:
                  type: boolean
      401:
        description: Неавторизован
    """
    try:
        conn = get_db()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, username, email, created_at, last_login, is_active
                FROM users 
                WHERE id = %s
            """, (request.user_id,))

            user = cursor.fetchone()

        conn.close()

        if not user:
            return jsonify({
                'success': False,
                'error': 'Пользователь не найден'
            }), 404

        return jsonify({
            'success': True,
            'user': user
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/change-password', methods=['POST'])
@token_required
def change_password():
    """
    Изменить пароль пользователя
    ---
    tags:
      - Аутентификация
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - current_password
            - new_password
          properties:
            current_password:
              type: string
            new_password:
              type: string
    responses:
      200:
        description: Пароль успешно изменен
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
      401:
        description: Неверный текущий пароль
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'Требуется JSON тело запроса'
            }), 400

        current_password = data.get('current_password')
        new_password = data.get('new_password')

        if not current_password or not new_password:
            return jsonify({
                'success': False,
                'error': 'Все поля обязательны'
            }), 400

        if len(new_password) < 6:
            return jsonify({
                'success': False,
                'error': 'Новый пароль должен содержать минимум 6 символов'
            }), 400

        # Проверяем текущий пароль
        conn = get_db()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT password_hash 
                FROM users 
                WHERE id = %s
            """, (request.user_id,))

            result = cursor.fetchone()

            if not result:
                conn.close()
                return jsonify({
                    'success': False,
                    'error': 'Пользователь не найден'
                }), 404

            # Проверяем текущий пароль
            if not check_password_hash(result['password_hash'], current_password):
                conn.close()
                return jsonify({
                    'success': False,
                    'error': 'Неверный текущий пароль'
                }), 401

            # Хешируем и сохраняем новый пароль
            new_password_hash = generate_password_hash(new_password)

            cursor.execute("""
                UPDATE users 
                SET password_hash = %s 
                WHERE id = %s
            """, (new_password_hash, request.user_id))

            conn.commit()

        conn.close()

        return jsonify({
            'success': True,
            'message': 'Пароль успешно изменен'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================
# ОБЩИЕ ЭНДПОИНТЫ
# ============================================

@app.route('/products', methods=['GET'])
def get_products():
    """
    Получить все товары из базы данных
    ---
    tags:
      - Данные
    parameters:
      - name: seller_id
        in: query
        type: string
        required: false
        description: ID продавца
      - name: platform
        in: query
        type: string
        required: false
        description: Платформа (ozon, wildberries)
      - name: limit
        in: query
        type: integer
        required: false
        default: 100
        description: Максимальное количество товаров
    responses:
      200:
        description: Список товаров
        schema:
          type: object
          properties:
            success:
              type: boolean
            total:
              type: integer
            count:
              type: integer
            products:
              type: array
              items:
                type: object
      500:
        description: Ошибка сервера
    """
    try:
        seller_id = request.args.get('seller_id')
        platform = request.args.get('platform')
        limit = request.args.get('limit', 100, type=int)

        conn = get_db()
        with conn.cursor() as cursor:
            # Строим запрос в зависимости от параметров
            query = "SELECT * FROM products WHERE 1=1"
            params = []

            if seller_id:
                query += " AND seller_id = %s"
                params.append(seller_id)

            if platform:
                query += " AND platform = %s"
                params.append(platform)

            query += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)

            cursor.execute(query, params)
            products = cursor.fetchall()

            # Получаем общее количество
            count_query = "SELECT COUNT(*) as total FROM products WHERE 1=1"
            count_params = []

            if seller_id:
                count_query += " AND seller_id = %s"
                count_params.append(seller_id)

            if platform:
                count_query += " AND platform = %s"
                count_params.append(platform)

            cursor.execute(count_query, count_params)
            total = cursor.fetchone()['total']

        conn.close()

        return jsonify({
            'success': True,
            'total': total,
            'count': len(products),
            'products': products
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/stats', methods=['GET'])
def get_stats():
    """
    Статистика по БД
    ---
    tags:
      - Данные
    responses:
      200:
        description: Статистика
        schema:
          type: object
          properties:
            success:
              type: boolean
            stats:
              type: object
            platforms:
              type: array
            top_sellers:
              type: array
      500:
        description: Ошибка сервера
    """
    try:
        conn = get_db()
        with conn.cursor() as cursor:
            # Общая статистика
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_products,
                    COUNT(DISTINCT seller_id) as total_sellers,
                    COUNT(DISTINCT platform) as total_platforms,
                    AVG(price) as avg_price,
                    MIN(created_at) as first_parse,
                    MAX(created_at) as last_parse
                FROM products
            """)
            stats = cursor.fetchone()

            # Статистика по платформам
            cursor.execute("""
                SELECT 
                    platform,
                    COUNT(*) as product_count,
                    COUNT(DISTINCT seller_id) as seller_count,
                    AVG(price) as avg_price,
                    AVG(rating) as avg_rating
                FROM products
                GROUP BY platform
                ORDER BY product_count DESC
            """)
            platforms = cursor.fetchall()

            # Топ продавцов
            cursor.execute("""
                SELECT seller_id, platform, COUNT(*) as product_count
                FROM products
                GROUP BY seller_id, platform
                ORDER BY product_count DESC
                LIMIT 20
            """)
            sellers = cursor.fetchall()

        conn.close()

        return jsonify({
            'success': True,
            'stats': stats,
            'platforms': platforms,
            'top_sellers': sellers
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/db-fix', methods=['POST'])
def fix_database():
    """
    Исправить структуру БД вручную
    ---
    tags:
      - Отладка
    responses:
      200:
        description: Структура БД исправлена
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
      500:
        description: Ошибка исправления БД
    """
    try:
        print("🔧 Запускаю ручное исправление структуры БД...")

        result = check_and_fix_table_structure()

        if result:
            return jsonify({
                'success': True,
                'message': 'Структура БД проверена и исправлена'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Не удалось исправить структуру БД'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/check-users-table', methods=['GET'])
def check_users_table():
    """
    Проверить структуру таблицы users
    ---
    tags:
      - Отладка
    responses:
      200:
        description: Структура таблицы users
        schema:
          type: object
          properties:
            success:
              type: boolean
            table_exists:
              type: boolean
            columns:
              type: array
            create_statement:
              type: string
      404:
        description: Таблица не существует
    """
    try:
        conn = get_db()
        with conn.cursor() as cursor:
            # Проверяем, существует ли таблица
            cursor.execute("SHOW TABLES LIKE 'users'")
            table_exists = cursor.fetchone()

            if not table_exists:
                return jsonify({
                    'success': False,
                    'error': 'Таблица users не существует'
                }), 404

            # Получаем структуру таблицы
            cursor.execute("DESCRIBE users")
            columns = cursor.fetchall()

            # Получаем информацию о таблице
            cursor.execute("SHOW CREATE TABLE users")
            create_stmt = cursor.fetchone()

        conn.close()

        return jsonify({
            'success': True,
            'table_exists': True,
            'columns': columns,
            'create_statement': create_stmt['Create Table'] if create_stmt else None
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================
# ТЕСТОВЫЕ ЭНДПОИНТЫ ДЛЯ SWAGGER
# ============================================

@app.route('/test-swagger', methods=['GET'])
def test_swagger():
    """
    Тестовый эндпоинт для проверки Swagger
    ---
    tags:
      - Отладка
    responses:
      200:
        description: Тестовый ответ
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            timestamp:
              type: string
    """
    return jsonify({
        'success': True,
        'message': 'Swagger работает корректно!',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/test-chrome', methods=['GET'])
def test_chrome():
    """
    Проверить установку Chrome для парсинга Wildberries
    ---
    tags:
      - Отладка
    responses:
      200:
        description: Проверка Chrome
        schema:
          type: object
          properties:
            success:
              type: boolean
            chrome_installed:
              type: boolean
            message:
              type: string
            installation_paths:
              type: array
              items:
                type: string
      500:
        description: Chrome не установлен
    """
    try:
        chrome_paths = [
            "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
            os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe"),
            "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
        ]

        found_paths = []
        for chrome_path in chrome_paths:
            if os.path.exists(chrome_path):
                found_paths.append(chrome_path)

        if found_paths:
            return jsonify({
                'success': True,
                'chrome_installed': True,
                'message': 'Chrome или Edge найден',
                'installation_paths': found_paths
            })
        else:
            return jsonify({
                'success': False,
                'chrome_installed': False,
                'message': 'Chrome или Edge не найден в стандартных путях',
                'installation_guide': {
                    'chrome': 'https://www.google.com/chrome/',
                    'edge': 'https://www.microsoft.com/edge',
                    'instructions': 'Установите браузер и перезапустите приложение'
                }
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/install-dependencies', methods=['GET'])
def install_dependencies():
    """
    Установить зависимости для парсинга
    ---
    tags:
      - Отладка
    responses:
      200:
        description: Результат установки зависимостей
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            dependencies:
              type: array
              items:
                type: string
      500:
        description: Ошибка установки
    """
    try:
        dependencies = [
            'selenium',
            'webdriver-manager',
            'beautifulsoup4',
            'flask-cors',
            'flasgger',
            'pymysql',
            'PyJWT'
        ]

        import subprocess
        import sys

        result = subprocess.run([
                                    sys.executable, '-m', 'pip', 'install'
                                ] + dependencies, capture_output=True, text=True)

        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': 'Зависимости успешно установлены',
                'dependencies': dependencies,
                'output': result.stdout
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Ошибка установки зависимостей',
                'error': result.stderr
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/apidocs/')
def apidocs_redirect():
    """Редирект на Swagger UI"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta http-equiv="refresh" content="0; url=/apidocs/index.html">
    </head>
    <body>
        <p>Перенаправление на <a href="/apidocs/index.html">Swagger UI</a>...</p>
    </body>
    </html>
    '''


@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ozon & Wildberries Parser API with Auth</title>
        <meta charset="UTF-8">
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 30px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                background: rgba(255, 255, 255, 0.95);
                padding: 40px;
                border-radius: 20px;
                color: #333;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }
            h1 {
                color: #4a5568;
                font-size: 2.8em;
                margin-bottom: 30px;
                text-align: center;
            }
            .swagger-btn {
                display: block;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-decoration: none;
                padding: 20px 40px;
                font-size: 1.5em;
                font-weight: bold;
                border-radius: 12px;
                text-align: center;
                margin: 30px auto;
                width: 300px;
                transition: transform 0.3s, box-shadow 0.3s;
            }
            .swagger-btn:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            }
            .endpoint {
                background: #f7fafc;
                padding: 25px;
                margin: 25px 0;
                border-left: 6px solid #4fd1c7;
                border-radius: 10px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            }
            .auth-endpoint {
                border-left-color: #4299e1;
            }
            .parse-endpoint {
                border-left-color: #38a169;
            }
            .wb-endpoint {
                border-left-color: #9f7aea;
            }
            .debug-endpoint {
                border-left-color: #d69e2e;
            }
            code {
                background: #e2e8f0;
                padding: 8px 12px;
                border-radius: 6px;
                font-family: 'Courier New', monospace;
                display: block;
                margin: 10px 0;
                overflow-x: auto;
            }
            .debug-info {
                background: #fef3c7;
                padding: 15px;
                border-radius: 8px;
                margin: 15px 0;
                font-size: 14px;
            }
            .btn {
                display: inline-block;
                padding: 10px 20px;
                margin: 5px;
                border-radius: 5px;
                text-decoration: none;
                color: white;
                font-weight: bold;
                cursor: pointer;
                border: none;
            }
            .btn-primary {
                background: #4299e1;
            }
            .btn-warning {
                background: #d69e2e;
            }
            .btn-danger {
                background: #e53e3e;
            }
            .platform-badge {
                display: inline-block;
                padding: 3px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                margin-left: 10px;
            }
            .ozon-badge {
                background: #005bff;
                color: white;
            }
            .wb-badge {
                background: #7100ff;
                color: white;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Ozon & Wildberries Parser API with Authentication</h1>

            <a href="/apidocs" class="swagger-btn" target="_blank">
                📚 Открыть Swagger UI
            </a>

            <div class="debug-info">
                <h3>🔧 Отладка и настройка</h3>
                <p>Для работы парсера Wildberries требуется:</p>
                <button class="btn btn-primary" onclick="checkChrome()">Проверить Chrome</button>
                <button class="btn btn-warning" onclick="installDeps()">Установить зависимости</button>
                <button class="btn btn-warning" onclick="fixDatabase()">Исправить структуру БД</button>
                <button class="btn btn-primary" onclick="checkUsersTable()">Проверить таблицу users</button>
                <div id="debugResult" style="margin-top: 10px;"></div>
            </div>

            <div class="endpoint auth-endpoint">
                <h3>🔐 POST /register</h3>
                <p><strong>Регистрация нового пользователя</strong></p>
                <p>Пароли автоматически хэшируются с использованием Werkzeug</p>
                <code>curl -X POST http://localhost:5000/register \\
  -H "Content-Type: application/json" \\
  -d '{"username": "john", "email": "john@example.com", "password": "secret123"}'</code>
            </div>

            <div class="endpoint auth-endpoint">
                <h3>🔑 POST /login</h3>
                <p><strong>Вход в систему</strong></p>
                <p>Возвращает JWT токен для доступа к защищенным эндпоинтам</p>
                <code>curl -X POST http://localhost:5000/login \\
  -H "Content-Type: application/json" \\
  -d '{"username": "john", "password": "secret123"}'</code>
            </div>

            <div class="endpoint parse-endpoint">
                <h3>🛒 GET /parse <span class="platform-badge ozon-badge">OZON</span></h3>
                <p><strong>Парсинг продавца Ozon</strong></p>
                <p>Запускает ozon_csv_parser.py для парсинга продавца</p>
                <code>curl "http://localhost:5000/parse?url=https://www.ozon.ru/seller/dareu-2265016/"</code>
            </div>

            <div class="endpoint wb-endpoint">
                <h3>🛒 GET /parse-wb <span class="platform-badge wb-badge">WILDBERRIES</span></h3>
                <p><strong>Парсинг продавца или бренда Wildberries</strong></p>
                <p>Использует Selenium для парсинга Wildberries</p>
                <code>curl "http://localhost:5000/parse-wb?url=https://www.wildberries.ru/seller/42582&max_products=50"</code>
                <p><strong>Примеры URL:</strong></p>
                <ul>
                    <li>Продавец: https://www.wildberries.ru/seller/42582</li>
                    <li>Бренд: https://www.wildberries.ru/brands/fashion-lines</li>
                </ul>
            </div>

            <div class="endpoint">
                <h3>📊 GET /stats</h3>
                <p><strong>Статистика по БД</strong></p>
                <p>Показывает статистику по всем платформам</p>
                <code>curl "http://localhost:5000/stats"</code>
            </div>

            <div class="endpoint">
                <h3>📦 GET /products</h3>
                <p><strong>Получить товары из БД</strong></p>
                <p>Можно фильтровать по продавцу и платформе</p>
                <code>curl "http://localhost:5000/products?platform=wildberries&limit=50"</code>
            </div>

            <div class="endpoint debug-endpoint">
                <h3>🔍 GET /test-swagger</h3>
                <p>Тестовый эндпоинт для проверки Swagger</p>
                <code>curl "http://localhost:5000/test-swagger"</code>
            </div>

            <div class="endpoint debug-endpoint">
                <h3>🔍 GET /test-chrome</h3>
                <p>Проверить установку Chrome для парсинга Wildberries</p>
                <code>curl "http://localhost:5000/test-chrome"</code>
            </div>

            <div class="endpoint debug-endpoint">
                <h3>📦 GET /install-dependencies</h3>
                <p>Установить зависимости для парсинга</p>
                <code>curl "http://localhost:5000/install-dependencies"</code>
            </div>

            <div class="endpoint debug-endpoint">
                <h3>🔍 GET /check-users-table</h3>
                <p>Проверить структуру таблицы users</p>
                <code>curl "http://localhost:5000/check-users-table"</code>
            </div>

            <div class="endpoint debug-endpoint">
                <h3>🔧 POST /db-fix</h3>
                <p>Исправить структуру базы данных</p>
                <code>curl -X POST http://localhost:5000/db-fix</code>
            </div>
        </div>

        <script>
            async function checkChrome() {
                const resultDiv = document.getElementById('debugResult');
                resultDiv.innerHTML = '<p>🔍 Проверяю установку Chrome...</p>';

                try {
                    const response = await fetch('/test-chrome');

                    const data = await response.json();

                    if (data.success) {
                        let html = '<p style="color: green;">✅ Chrome/Edge найден!</p>';
                        if (data.installation_paths && data.installation_paths.length > 0) {
                            html += '<p>Найденные пути:</p><ul>';
                            data.installation_paths.forEach(path => {
                                html += `<li>${path}</li>`;
                            });
                            html += '</ul>';
                        }
                        resultDiv.innerHTML = html;
                    } else {
                        let html = '<p style="color: red;">❌ Chrome/Edge не найден</p>';
                        if (data.installation_guide) {
                            html += '<p>Инструкция по установке:</p>';
                            html += `<p><a href="${data.installation_guide.chrome}" target="_blank">Установить Google Chrome</a></p>`;
                            html += `<p><a href="${data.installation_guide.edge}" target="_blank">Установить Microsoft Edge</a></p>`;
                        }
                        resultDiv.innerHTML = html;
                    }
                } catch (error) {
                    resultDiv.innerHTML = '<p style="color: red;">❌ Ошибка сети: ' + error.message + '</p>';
                }
            }

            async function installDeps() {
                const resultDiv = document.getElementById('debugResult');
                resultDiv.innerHTML = '<p>📦 Устанавливаю зависимости...</p>';

                try {
                    const response = await fetch('/install-dependencies');

                    const data = await response.json();

                    if (data.success) {
                        let html = '<p style="color: green;">✅ Зависимости успешно установлены</p>';
                        html += '<p>Установленные пакеты:</p><ul>';
                        data.dependencies.forEach(dep => {
                            html += `<li>${dep}</li>`;
                        });
                        html += '</ul>';
                        resultDiv.innerHTML = html;
                    } else {
                        resultDiv.innerHTML = '<p style="color: red;">❌ Ошибка установки: ' + data.error + '</p>';
                    }
                } catch (error) {
                    resultDiv.innerHTML = '<p style="color: red;">❌ Ошибка сети: ' + error.message + '</p>';
                }
            }

            async function fixDatabase() {
                const resultDiv = document.getElementById('debugResult');
                resultDiv.innerHTML = '<p>🔧 Исправляю структуру БД...</p>';

                try {
                    const response = await fetch('/db-fix', {
                        method: 'POST'
                    });

                    const data = await response.json();

                    if (data.success) {
                        resultDiv.innerHTML = '<p style="color: green;">✅ ' + data.message + '</p>';
                    } else {
                        resultDiv.innerHTML = '<p style="color: red;">❌ ' + data.error + '</p>';
                    }
                } catch (error) {
                    resultDiv.innerHTML = '<p style="color: red;">❌ Ошибка сети: ' + error.message + '</p>';
                }
            }

            async function checkUsersTable() {
                const resultDiv = document.getElementById('debugResult');
                resultDiv.innerHTML = '<p>🔍 Проверяю таблицу users...</p>';

                try {
                    const response = await fetch('/check-users-table');

                    const data = await response.json();

                    if (data.success) {
                        let html = '<p style="color: green;">✅ Таблица users существует</p>';
                        html += '<p>Колонки:</p><ul>';

                        data.columns.forEach(col => {
                            html += `<li><strong>${col.Field}</strong> - ${col.Type} ${col.Null === 'NO' ? 'NOT NULL' : ''}</li>`;
                        });

                        html += '</ul>';
                        resultDiv.innerHTML = html;
                    } else {
                        resultDiv.innerHTML = '<p style="color: red;">❌ ' + data.error + '</p>';
                    }
                } catch (error) {
                    resultDiv.innerHTML = '<p style="color: red;">❌ Ошибка сети: ' + error.message + '</p>';
                }
            }
        </script>
    </body>
    </html>
    '''


if __name__ == '__main__':
    # Устанавливаем дополнительные зависимости
    print("🔧 Проверка зависимостей...")
    print("Для парсинга Wildberries требуется:")
    print("1. Google Chrome или Microsoft Edge")
    print("2. Установить зависимости: pip install selenium webdriver-manager beautifulsoup4")
    print("3. Установить основные зависимости: pip install flask flask-cors flasgger pymysql PyJWT")

    print("=" * 70)
    print("🔧 Инициализация Ozon & Wildberries Parser API с аутентификацией...")

    if init_database():
        print("✅ База данных готова")
    else:
        print("⚠️  Проблемы с БД, но API продолжит работу")

    print("\n" + "=" * 70)
    print("🚀 Ozon & Wildberries Parser API with Auth ЗАПУЩЕН!")
    print("=" * 70)
    print("📌 Главная страница:  http://localhost:5000")
    print("📚 Swagger UI:        http://localhost:5000/apidocs")
    print("🔍 Тест Swagger:      http://localhost:5000/test-swagger")
    print("🔍 Тест Chrome:       http://localhost:5000/test-chrome")
    print("\n🎯 Эндпоинты парсинга:")
    print("   GET /parse    - Парсинг Ozon (требуется ozon_csv_parser.py)")
    print("   GET /parse-wb - Парсинг Wildberries (требуется Chrome/Edge)")
    print("\n🔧 Отладка и настройка:")
    print("   GET  /test-chrome        - проверить установку Chrome")
    print("   GET  /install-dependencies - установить зависимости")
    print("   GET  /check-users-table  - проверить таблицу users")
    print("   POST /db-fix             - исправить структуру БД")
    print("=" * 70)
    print("\n🔐 Первые шаги:")
    print("1. Проверьте Swagger: http://localhost:5000/apidocs")
    print("2. Проверьте Chrome: http://localhost:5000/test-chrome")
    print("3. Если Chrome не найден, установите: https://www.google.com/chrome/")
    print("4. Проверьте структуру таблицы: http://localhost:5000/check-users-table")
    print("5. Если нужно, исправьте: POST http://localhost:5000/db-fix")
    print("6. Зарегистрируйте пользователя через /register")
    print("7. Протестируйте парсинг:")
    print("   - Ozon: /parse?url=https://www.ozon.ru/seller/dareu-2265016/")
    print("   - Wildberries: /parse-wb?url=https://www.wildberries.ru/seller/42582")
    print("=" * 70)

    app.run(debug=True, port=5000, host='0.0.0.0')