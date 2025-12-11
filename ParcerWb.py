import time
import json
import random
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import os


class WildberriesSellerParser:
    def __init__(self, headless=True, delay_range=(3, 7)):
        self.delay_range = delay_range
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
        ]
        print("🚀 Инициализация браузера...")
        self.driver = self._init_driver(headless)
        self.wait = WebDriverWait(self.driver, 30)
        print("✅ Браузер готов.")

    def _init_driver(self, headless):
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
            print(f"❌ Ошибка инициализации драйвера: {e}")
            raise

    def _smart_delay(self, custom_range=None):
        min_d, max_d = custom_range if custom_range else self.delay_range
        delay = random.uniform(min_d, max_d)
        print(f"   ⏳ Ожидание {delay:.1f} сек...")
        time.sleep(delay)
        return delay

    def parse_seller_products(self, seller_url, max_products=200):
        """
        Парсит все товары продавца или бренда по ссылке.
        Пример ссылки: https://www.wildberries.ru/seller/42582
        Или: https://www.wildberries.ru/brands/fashion-lines
        """
        print(f"\n🏪 Начинаю парсинг...")
        print(f"📡 URL: {seller_url}")

        # Определяем тип ссылки и извлекаем идентификатор
        entity_info = self._extract_entity_info(seller_url)
        if not entity_info:
            print("❌ Не удалось определить тип страницы")
            return []

        entity_id = entity_info['id']
        entity_type = entity_info['type']
        entity_name = entity_info['name']

        if entity_type == "seller":
            print(f"🆔 ID продавца: {entity_id}")
        else:
            print(f"🏷️ Бренд: {entity_name or entity_id}")

        all_products = []

        try:
            # 1. Загружаем страницу
            print(f"\n📥 Загружаю страницу...")
            self.driver.get(seller_url)
            self._smart_delay((4, 6))

            # 2. Получаем информацию о продавце/бренде
            seller_info = self._parse_entity_info()
            seller_info['entity_id'] = entity_id
            seller_info['entity_type'] = entity_type
            seller_info['entity_name'] = entity_name
            seller_info['seller_id'] = entity_id

            # 3. Ждем загрузки товаров и прокручиваем
            print(f"\n⬇ Загружаю товары...")
            loaded_count = self._wait_and_load_products(max_products)
            print(f"📦 Загружено товаров: {loaded_count}")

            if loaded_count == 0:
                print("❌ Не удалось загрузить товары")
                return []

            # 4. Получаем HTML
            page_source = self.driver.page_source
            debug_filename = f"debug_{entity_type.upper()}_{entity_id}_{datetime.now().strftime('%H%M%S')}.html"
            with open(debug_filename, 'w', encoding='utf-8') as f:
                f.write(page_source)
            print(f"💾 HTML сохранен: {debug_filename}")

            # 5. Парсим товары
            print(f"\n🔄 Начинаю парсинг товаров...")
            all_products = self._parse_products_page_html(page_source, seller_info, max_products)

            return all_products

        except Exception as e:
            print(f"\n❌ Ошибка при парсинге: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _extract_entity_info(self, url):
        """Извлекает информацию о сущности (продавец или бренд) из URL."""
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

    def _parse_entity_info(self):
        """Парсит информацию о продавце или бренде."""
        entity_info = {
            'seller_name': '',
            'seller_rating': 0.0,
            'seller_feedback': 0,
            'seller_orders': 0,
            'description': '',
            'followers': 0
        }

        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            # Имя продавца/бренда
            name_selectors = [
                'h1.seller-details__title',
                'div.seller-info__name',
                'span.seller-name',
                'h1.brand-page__title',
                'div.brand-header__title',
                'h1.title',
                'h1',
                '.seller-info__name',
                '.brand-title'
            ]

            for selector in name_selectors:
                name_elem = soup.select_one(selector)
                if name_elem:
                    entity_info['seller_name'] = name_elem.get_text(strip=True)
                    if entity_info['seller_name']:
                        break

            # Выводим информацию
            print(f"\n📋 ИНФОРМАЦИЯ:")
            print(f"   Имя: {entity_info['seller_name']}")

        except Exception as e:
            print(f"   ⚠ Ошибка при парсинге информации: {e}")

        return entity_info

    def _wait_and_load_products(self, max_products):
        """Ожидает загрузки товаров и прокручивает страницу."""
        print("   ⏳ Ожидаю загрузки товаров...")

        try:
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
            products = self.driver.find_elements(By.CSS_SELECTOR,
                                                 "article.product-card, div.product-card, [data-nm-id], .card, .product-card, article[class*='card'], div[class*='card']")
            last_count = len(products)
            print(f"   📦 Начальное количество товаров: {last_count}")
        except Exception as e:
            print(f"   ⚠ Ошибка при подсчете товаров: {e}")
            last_count = 0

        same_count = 0
        scroll_attempts = 0
        max_scrolls = 15

        while scroll_attempts < max_scrolls and last_count < max_products:
            scroll_attempts += 1

            # Прокручиваем
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self._smart_delay((2, 3))

            # Считаем товары
            try:
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
            'parsed_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'name': '',
            'brand': '',
            'price': 0,
            'old_price': 0,
            'discount': 0,
            'rating': 0.0,
            'reviews': 0,
            'image': '',
            'category': '',  # Будем заполнять отдельно
            'entity_id': entity_info.get('entity_id', ''),
            'entity_type': entity_info.get('entity_type', ''),
            'entity_name': entity_info.get('entity_name', ''),
            'seller_name': entity_info.get('seller_name', ''),
            'seller_rating': entity_info.get('seller_rating', 0.0),
            'seller_feedback': entity_info.get('seller_feedback', 0),
            'seller_orders': entity_info.get('seller_orders', 0)
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

            # Старая цена
            old_price_selectors = [
                'del.price-block__old-price',
                'span.price-block__old-price',
                '.old-price',
                '[class*="price__old"]',
                '.j-old-price'
            ]

            for selector in old_price_selectors:
                old_price_element = card.select_one(selector)
                if old_price_element:
                    old_price_text = old_price_element.get_text(strip=True)
                    old_price_value = self._extract_price(old_price_text)
                    if old_price_value:
                        product_data['old_price'] = old_price_value
                        if old_price_value > 0 and product_data['price'] > 0:
                            discount = ((old_price_value - product_data['price']) / old_price_value) * 100
                            product_data['discount'] = round(discount)
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

            # Выводим результат (без категории - она будет добавлена позже)
            name_display = product_data['name'][:25] if product_data['name'] else 'Без названия'
            brand_display = product_data.get('brand', 'Нет')[:12]
            price_indicator = "✅" if product_data['price'] > 0 else "⚠"

            price_display = f"{product_data['price']:,} ₽"
            if product_data['old_price'] > 0:
                price_display = f"{price_display} (-{product_data['discount']}%)"

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
            soup = BeautifulSoup(page_source, 'html.parser')

            # СПОСОБ 1: Ищем хлебные крошки (самый надежный способ)
            breadcrumb_selectors = [
                '.breadcrumbs',
                '.breadcrumb',
                '.nav-breadcrumbs',
                '.breadcrumbs__container',
                '.bread-crumbs',
                '.catalog-breadcrumbs',
                '[class*="breadcrumb"]',
                '[class*="breadcrumbs"]',
                '.product-page__breadcrumbs',
                '.product-breadcrumbs',
                '.breadcrumbs__list',
                '.catalog-breadcrumbs__list',
                'nav[aria-label="Хлебные крошки"]',
                'nav[aria-label="breadcrumb"]',
                '.product-page-breadcrumbs'
            ]

            # Сначала ищем структурированные хлебные крошки со списком
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
                            # Разделяем текст
                            items = [item.strip() for item in breadcrumb_text.split('>') if item.strip()]
                            breadcrumb_items = items
                            breadcrumb_found = True
                            break

            # Если нашли хлебные крошки, обрабатываем их
            if breadcrumb_items:
                # Фильтруем элементы
                filtered_items = []
                for item in breadcrumb_items:
                    # Исключаем общие слова и рекламные тексты
                    excluded_words = [
                        'Главная', 'Главное', 'Home', 'Каталог', 'Catalog',
                        'Все товары', 'Все', 'Все категории', 'Поиск',
                        'реклама', 'промо', 'акция', 'скидка', 'распродажа',
                        'НГ', 'Новый год', 'новогодн', 'Wildberries', 'WB',
                        'Корзина', 'Избранное', 'Сравнение', 'Личный кабинет',
                        'Магазины', 'Бренды', 'Акции', 'Скидки', 'Распродажи',
                        'Помощь', 'Доставка', 'Оплата', 'Контакты',
                        'О компании', 'Партнерам', 'Прессе', 'Вакансии'
                    ]

                    item_lower = item.lower()
                    should_exclude = False

                    # Проверяем на исключенные слова
                    for word in excluded_words:
                        if word.lower() in item_lower or item_lower in [w.lower() for w in excluded_words]:
                            should_exclude = True
                            break

                    # Исключаем слишком короткие или слишком длинные элементы
                    if len(item) < 2 or len(item) > 50:
                        should_exclude = True

                    # Исключаем элементы с цифрами (обычно это ID или коды)
                    if re.search(r'\d{3,}', item):
                        should_exclude = True

                    # Исключаем элементы, которые являются брендами (если можем определить)
                    if not should_exclude:
                        # Проверяем, не является ли элемент названием бренда
                        # Обычно бренды пишутся заглавными буквами или имеют специфическое написание
                        if item.isupper() or re.search(r'[A-Z][a-z]+', item):
                            # Но это может быть и категория, поэтому дополнительная проверка
                            if len(item.split()) <= 2:  # Короткие названия чаще бренды
                                should_exclude = True

                    if not should_exclude:
                        filtered_items.append(item)

                # Определяем категорию
                if filtered_items:
                    # Обычно категория находится где-то в середине или конце хлебных крошек
                    # Исключаем первый и последний элементы (часто это "Главная" и название товара)
                    candidates = filtered_items[1:-1] if len(filtered_items) > 2 else filtered_items

                    if candidates:
                        # Берем последний подходящий элемент как категорию
                        for candidate in reversed(candidates):
                            if 3 <= len(candidate) <= 40:
                                category = candidate
                                break

            # СПОСОБ 2: Ищем категорию в JSON-LD структурированных данных
            if category == "Не определена":
                json_ld_scripts = soup.select('script[type="application/ld+json"]')
                for script in json_ld_scripts:
                    try:
                        data = json.loads(script.string)
                        if isinstance(data, dict):
                            # Проверяем различные возможные места для категории
                            possible_keys = ['category', 'productCategory', 'genre', 'keywords']
                            for key in possible_keys:
                                if key in data:
                                    cat_value = data[key]
                                    if isinstance(cat_value, str) and 3 <= len(cat_value) <= 50:
                                        category = cat_value
                                        break
                            if category != "Не определена":
                                break
                    except:
                        continue

            # СПОСОБ 3: Ищем в скрытых мета-данных
            if category == "Не определена":
                meta_selectors = [
                    'meta[property="product:category"]',
                    'meta[name="category"]',
                    'meta[itemprop="category"]',
                    'meta[name="parsely-section"]',
                    'meta[property="article:section"]'
                ]

                for selector in meta_selectors:
                    meta_elem = soup.select_one(selector)
                    if meta_elem and meta_elem.get('content'):
                        content = meta_elem.get('content')
                        if content and 3 <= len(content) <= 50:
                            # Проверяем, что это похоже на категорию
                            if not re.search(r'\d{3,}', content):  # Не содержит много цифр
                                category = content
                                break

            # СПОСОБ 4: Ищем в структурированных данных на странице
            if category == "Не определена":
                # Ищем элементы с атрибутами данных
                data_elements = soup.select('[data-category], [data-product-category], [data-cat]')
                for elem in data_elements:
                    for attr in ['data-category', 'data-product-category', 'data-cat']:
                        cat_value = elem.get(attr)
                        if cat_value and 3 <= len(cat_value) <= 50:
                            category = cat_value
                            break
                    if category != "Не определена":
                        break

            # СПОСОБ 5: Анализ пути URL (последний резервный вариант)
            if category == "Не определена":
                # Парсим URL для поиска категории в пути
                url_path = product_url.split('/')
                for i, part in enumerate(url_path):
                    if 'catalog' in part.lower() and i + 1 < len(url_path):
                        # Следующая часть после catalog может быть категорией
                        next_part = url_path[i + 1]
                        if next_part and not next_part.isdigit() and len(next_part) > 2:
                            # Декодируем URL-encoded символы
                            decoded = re.sub(r'[^\w\s-]', ' ', next_part)
                            decoded = ' '.join(decoded.split('-')).strip()
                            if 3 <= len(decoded) <= 30:
                                category = decoded.title()
                                break

            # Очистка и валидация категории
            if category != "Не определена":
                # Удаляем лишние символы
                category = re.sub(r'[^\w\s\-&/()]', '', category)
                # Удаляем лишние пробелы
                category = ' '.join(category.split())

                # Проверяем на мусорные значения
                excluded_patterns = [
                    r'^[A-Z]{2,10}$',  # Слишком много заглавных букв (возможно, бренд)
                    r'^\d+$',  # Только цифры
                    r'.*\d{4,}.*',  # Содержит много цифр
                    r'^[^a-zA-Zа-яА-Я]*$',  # Нет букв
                ]

                for pattern in excluded_patterns:
                    if re.match(pattern, category):
                        category = "Не определена"
                        break

                # Проверяем на рекламные тексты
                ad_keywords = ['реклама', 'промо', 'акция', 'скидка', 'распродажа',
                               'новинка', 'бестселлер', 'хит', 'топ', 'выбор',
                               'купить', 'цена', 'руб', 'доставка', 'отзыв']

                category_lower = category.lower()
                for keyword in ad_keywords:
                    if keyword in category_lower:
                        if len(category.split()) <= 3:  # Короткий текст с рекламой
                            category = "Не определена"
                        break

                # Обрезаем длину
                if len(category) > 50:
                    category = category[:50]

            # Закрываем вкладку и возвращаемся к основной
            self.driver.close()
            self.driver.switch_to.window(original_window)

            print(f"       🏷️ Категория: {category}")
            return category

        except Exception as e:
            print(f"       ⚠ Ошибка при получении категории: {e}")
            try:
                # Закрываем вкладку если открыта
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

        # Удаляем все нецифровые символы
        cleaned = re.sub(r'[^\d]', '', text)

        if cleaned:
            try:
                return int(cleaned)
            except:
                return 0
        return 0

    def save_results(self, products_data, entity_info):
        """Сохраняет результаты парсинга в указанном формате JSON."""
        if not products_data:
            print("⚠ Нет данных для сохранения.")
            return

        entity_id = entity_info.get('entity_id', 'unknown')
        entity_name = entity_info.get('entity_name', 'unknown')
        entity_type = entity_info.get('entity_type', 'unknown')

        safe_name = re.sub(r'[^\w]', '_', entity_name)[:30]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        folder = f'results/{entity_type}s'
        os.makedirs(folder, exist_ok=True)
        json_filename = f"{folder}/{entity_type}_{entity_id}_{safe_name}_{timestamp}.json"

        try:
            # Преобразуем данные в нужный формат
            formatted_products = []
            for product in products_data:
                formatted_product = {
                    "id": product.get('id', ''),
                    "url": product.get('url', ''),
                    "name": product.get('name', ''),
                    "brand": product.get('brand', ''),
                    "price": product.get('price', 0),
                    "rating": product.get('rating', 0.0),
                    "image": product.get('image', ''),
                    "category": product.get('category', ''),
                }
                formatted_products.append(formatted_product)

            # Сохраняем в формате массива объектов
            with open(json_filename, 'w', encoding='utf-8') as jsonfile:
                json.dump(formatted_products, jsonfile, ensure_ascii=False, indent=2)

            print(f"\n✅ Результаты сохранены: {json_filename}")
            print(f"📦 Количество сохраненных товаров: {len(formatted_products)}")

            # Выводим пример первых товаров для проверки формата
            if formatted_products:
                print(f"\n📋 ПРИМЕР СОХРАНЕННЫХ ДАННЫХ:")
                for i, product in enumerate(formatted_products[:3], 1):
                    print(f"   Товар {i}:")
                    print(f"      ID: {product.get('id')}")
                    print(f"      Название: {product.get('name')[:50]}...")
                    print(f"      Бренд: {product.get('brand')}")
                    print(f"      Цена: {product.get('price')} ₽")
                    print(f"      Категория: {product.get('category')}")
                    print()

        except Exception as e:
            print(f"❌ Ошибка при сохранении: {e}")

    def _print_category_statistics(self, products_data):
        """Выводит статистику по категориям."""
        if not products_data:
            return

        # Собираем все категории
        all_categories = []
        valid_categories = []

        for p in products_data:
            category = p.get('category', '')
            if category:
                all_categories.append(category)
                # Проверяем на валидность
                if (category != "Не определена" and
                        len(category) > 2 and
                        not any(word in category.lower() for word in
                                ['реклама', 'промо', 'акция', 'распродажа', 'скидка', 'новая'])):
                    valid_categories.append(category)

        from collections import Counter

        if all_categories:
            category_counts = Counter(all_categories)
            valid_counts = Counter(valid_categories)

            print(f"\n📂 СТАТИСТИКА ПО КАТЕГОРИЯМ:")
            print(f"   Всего товаров: {len(products_data)}")
            print(f"   Уникальных категорий: {len(category_counts)}")
            print(f"   Валидных категорий: {len(valid_counts)}")
            print(
                f"   Товаров с валидной категорией: {len(valid_categories)}/{len(products_data)} ({len(valid_categories) / len(products_data) * 100:.1f}%)")

            if valid_counts:
                print(f"\n   📊 Топ-10 категорий:")
                for i, (category, count) in enumerate(valid_counts.most_common(10), 1):
                    if category and category != "Не определена":
                        percentage = (count / len(products_data)) * 100
                        print(f"     {i:2}. {category:40} - {count:3} товаров ({percentage:.1f}%)")

            # Товары без категории
            undefined_count = category_counts.get("Не определена", 0)
            if undefined_count > 0:
                percentage_undefined = (undefined_count / len(products_data)) * 100
                print(f"\n   ⚠ Товары без категории: {undefined_count} ({percentage_undefined:.1f}%)")

            # Топ категорий по продавцу/бренду
            if valid_counts:
                print(f"\n   🎯 Основные категории продавца/бренда:")
                categories_list = list(valid_counts.most_common(5))
                for cat, count in categories_list:
                    percentage = (count / len(valid_categories)) * 100 if valid_categories else 0
                    print(f"     • {cat:40} - {count:3} товаров ({percentage:.1f}% от категоризированных)")
        else:
            print(f"\n📂 КАТЕГОРИИ:")
            print(f"   ❌ Категории не найдены")

    def close(self):
        """Закрытие браузера."""
        try:
            self.driver.quit()
            print("✅ Браузер закрыт.")
        except:
            pass


def main():
    print("=" * 70)
    print("🏪 ПАРСЕР WILDBERRIES - ТОВАРЫ ПРОДАВЦА И БРЕНДА")
    print("=" * 70)
    print("Парсит все товары конкретного продавца или бренда")
    print("Пример ссылки продавца: https://www.wildberries.ru/seller/42582")
    print("Пример ссылки бренда: https://www.wildberries.ru/brands/fashion-lines")
    print("=" * 70)
    print("⚠ Парсинг начнется автоматически через 3 секунды...")
    print("=" * 70)

    # Автоматически переходим в невидимый режим для ускорения
    time.sleep(3)

    # Создаем парсер с невидимым режимом по умолчанию
    parser = WildberriesSellerParser(headless=True)

    try:
        # Получаем ссылку из аргументов командной строки или запрашиваем
        import sys
        if len(sys.argv) > 1:
            seller_url = sys.argv[1]
        else:
            seller_url = input("\n🔗 Введите ссылку на продавца или бренд: ").strip()

        if not seller_url:
            print("❌ Ссылка не может быть пустой")
            parser.close()
            return

        max_products = 200
        print(f"\n📊 Максимальное количество товаров для парсинга: {max_products}")
        print(f"⏰ Примерное время: {max_products * 5} секунд (~{max_products * 5 / 60:.1f} минут)")

        print(f"\n{'=' * 70}")
        print(f"🚀 ЗАПУСК ПАРСИНГА")
        print(f"   Ссылка: {seller_url}")
        print(f"   Цель: до {max_products} товаров")
        print(f"   Метод: парсинг с переходом на каждую страницу товара")
        print(f"{'=' * 70}")

        # Автоматически начинаем парсинг без подтверждения
        print(f"\n▶ Начинаю парсинг...")

        products_data = parser.parse_seller_products(seller_url, max_products)

        if products_data:
            # Формируем информацию о сущности для сохранения
            if products_data:
                entity_info = {
                    'entity_id': products_data[0].get('entity_id', ''),
                    'entity_type': products_data[0].get('entity_type', ''),
                    'entity_name': products_data[0].get('entity_name', ''),
                    'seller_name': products_data[0].get('seller_name', ''),
                }

                parser.save_results(products_data, entity_info)

                # Дополнительная статистика
                print(f"\n{'=' * 70}")
                print(f"📈 ИТОГОВАЯ СТАТИСТИКА")
                print(f"   Обработано товаров: {len(products_data)}")

                # Средняя цена
                prices = [p['price'] for p in products_data if p['price'] > 0]
                if prices:
                    avg_price = sum(prices) / len(prices)
                    print(f"   Средняя цена: {avg_price:,.0f} ₽")

                # Товары со скидкой
                discounted = [p for p in products_data if p.get('discount', 0) > 0]
                if discounted:
                    print(
                        f"   Товары со скидкой: {len(discounted)} ({len(discounted) / len(products_data) * 100:.1f}%)")

                print(f"{'=' * 70}")

        else:
            print("\n❌ Не удалось собрать данные.")

    except KeyboardInterrupt:
        print("\n\n⚠ Программа прервана пользователем.")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        parser.close()
        print("\n✅ Парсинг завершен. Нажмите Enter для выхода...")
        input()


def run_parser(seller_url, max_products=200):
    """
    Функция для запуска парсера напрямую без интерфейса.
    Используйте эту функцию, если хотите интегрировать парсер в другой код.

    Пример использования:
        from parser import run_parser
        results = run_parser("https://www.wildberries.ru/seller/42582", 100)
    """
    parser = WildberriesSellerParser(headless=True)

    try:
        print(f"🚀 Начинаю парсинг {seller_url}...")
        products_data = parser.parse_seller_products(seller_url, max_products)

        if products_data:
            entity_info = {
                'entity_id': products_data[0].get('entity_id', ''),
                'entity_type': products_data[0].get('entity_type', ''),
                'entity_name': products_data[0].get('entity_name', ''),
                'seller_name': products_data[0].get('seller_name', ''),
            }

            # Форматируем результаты
            formatted_results = []
            for product in products_data:
                formatted_product = {
                    "id": product.get('id', ''),
                    "url": product.get('url', ''),
                    "name": product.get('name', ''),
                    "brand": product.get('brand', ''),
                    "price": product.get('price', 0),
                    "rating": product.get('rating', 0.0),
                    "image": product.get('image', ''),
                    "category": product.get('category', ''),
                }
                formatted_results.append(formatted_product)

            return formatted_results
        else:
            return []

    finally:
        parser.close()


if __name__ == "__main__":
    os.makedirs('results/sellers', exist_ok=True)
    os.makedirs('results/brands', exist_ok=True)

    # Проверяем, есть ли аргументы командной строки
    import sys

    if len(sys.argv) > 1:
        # Если есть аргументы, запускаем напрямую
        url = sys.argv[1]
        max_products = int(sys.argv[2]) if len(sys.argv) > 2 else 200
        print(f"⚡ Автоматический запуск парсера для: {url}")
        results = run_parser(url, max_products)
        if results:
            print(f"✅ Парсинг завершен. Получено товаров: {len(results)}")
        else:
            print("❌ Парсинг не дал результатов")
    else:
        # Если нет аргументов, запускаем интерфейс
        main()