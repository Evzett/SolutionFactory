import asyncio
import logging
import random
import os
import re
import csv
import json
from dataclasses import dataclass
from typing import List, Tuple, Optional

from urllib.parse import quote, urlparse, parse_qsl, urlencode, urlunparse
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
)

logger = logging.getLogger(__name__)


@dataclass
class Product:
    # товар
    id: Optional[str]
    name: str
    brand: Optional[str]
    price: Optional[str]
    rating: Optional[str]
    feedbacks: Optional[str]
    images: List[str]
    description: Optional[str]
    seller: Optional[str]
    category: Optional[str]
    subcategory: Optional[str]
    url: str

    # продавец (из шапки seller-страницы)
    seller_rating: Optional[str] = None
    seller_feedback: Optional[str] = None
    seller_orders: Optional[str] = None


class OzonParser:
    def __init__(self) -> None:
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def human_delay(self, min_sec: float = 1.0, max_sec: float = 3.0) -> None:
        await asyncio.sleep(random.uniform(min_sec, max_sec))

    async def setup_browser(self) -> None:
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--proxy-server=direct://",   # <-- ДОБАВЬ ЭТО
            ],
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.15; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            ),
            java_script_enabled=True,
            ignore_https_errors=True,
        ) 

        await self.context.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            """
        )

        self.page = await self.context.new_page()
        self.page.set_default_timeout(20000)
        self.page.set_default_navigation_timeout(25000)

    async def close_browser(self) -> None:
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    # ============================================================
    #   ПОИСКОВЫЙ РЕЖИМ: сбор ссылок по текстовому запросу
    # ============================================================
    async def fetch_product_links(self, query: str, pages: int = 1) -> List[str]:
        encoded_query = quote(query)
        search_url = f"https://www.ozon.ru/search/?text={encoded_query}&from_global=true"

        logger.info(f"Поиск по запросу: {query}")
        await self.page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
        await self.human_delay(2, 3)

        current_url = self.page.url
        if "category" in current_url and "text=" not in current_url:
            logger.warning("Перенаправление на категорию, пробуем без from_global")
            search_url = f"https://www.ozon.ru/search/?text={encoded_query}"
            await self.page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
            await self.human_delay(2, 3)

        selectors_to_wait = [
            "[data-widget='searchResults']",
            ".widget-search-result-container",
            ".search-container",
            ".tile-root",
            "div[data-widget*='search']",
            ".a0c6",
        ]
        for selector in selectors_to_wait:
            try:
                await self.page.wait_for_selector(selector, timeout=7000)
                break
            except PlaywrightTimeoutError:
                continue

        product_selectors = [
            "a[href*='/product/']",
            ".tile-root a[href*='/product/']",
            "[data-widget*='searchResults'] a[href*='/product/']",
            "div a[href*='/product/']",
        ]

        elements = []
        for selector in product_selectors:
            try:
                found = await self.page.query_selector_all(selector)
                elements.extend(found)
                if found:
                    break
            except Exception:
                continue

        seen = set()
        links: List[str] = []
        for el in elements:
            href = await el.get_attribute("href")
            if not href:
                continue
            if href in seen:
                continue
            seen.add(href)
            if href.startswith("http"):
                links.append(href)
            else:
                links.append("https://www.ozon.ru" + href)

        logger.info(f"Найдено ссылок на товары: {len(links)}")
        # параметр pages пока по факту не используем, т.к. Ozon лениво подгружает
        return links

    # ============================================================
    #   РЕЖИМ SELLER: сбор ссылок со страницы продавца
    # ============================================================
    async def fetch_product_links_from_seller(self, seller_url: str, pages: int = 1) -> List[str]:
        logger.info(f"Парсим страницу продавца: {seller_url}")

        parsed = urlparse(seller_url)
        base_query = dict(parse_qsl(parsed.query))

        all_links: List[str] = []
        seen: set = set()

        for page_num in range(1, max(1, pages) + 1):
            q = base_query.copy()
            q["page"] = str(page_num)
            url_with_page = urlunparse(parsed._replace(query=urlencode(q, doseq=True)))

            logger.info(f"Открываем страницу продавца: {url_with_page}")
            await self.page.goto(url_with_page, wait_until="domcontentloaded", timeout=25000)
            try:
                await self.page.wait_for_load_state("networkidle", timeout=8000)
            except PlaywrightTimeoutError:
                pass

            await self.human_delay(1, 2)

            selectors_to_wait = [
                "[data-widget='searchResults']",
                ".widget-search-result-container",
                ".search-container",
                ".tile-root",
                "div[data-widget*='search']",
            ]
            for selector in selectors_to_wait:
                try:
                    await self.page.wait_for_selector(selector, timeout=7000)
                    break
                except PlaywrightTimeoutError:
                    continue

            product_selectors = [
                "a[href*='/product/']",
                ".tile-root a[href*='/product/']",
                "[data-widget*='searchResults'] a[href*='/product/']",
                "div a[href*='/product/']",
            ]

            page_elements = []
            for selector in product_selectors:
                try:
                    found = await self.page.query_selector_all(selector)
                    page_elements.extend(found)
                    if found:
                        break
                except Exception:
                    continue

            page_links_count_before = len(all_links)

            for el in page_elements:
                href = await el.get_attribute("href")
                if not href:
                    continue
                if href in seen:
                    continue
                seen.add(href)
                if href.startswith("http"):
                    all_links.append(href)
                else:
                    all_links.append("https://www.ozon.ru" + href)

            page_links_count_after = len(all_links)
            added = page_links_count_after - page_links_count_before
            logger.info(f"Страница {page_num}: добавлено {added} ссылок")

            if added == 0:
                logger.info("Похоже, товаров больше нет, останавливаемся.")
                break

        logger.info(f"Всего уникальных ссылок с продавца: {len(all_links)}")
        return all_links

    # ============================================================
    #   ПАРСИНГ ШАПКИ ПРОДАВЦА (SELLER RATING / FEEDBACK / ORDERS)
    # ============================================================
    async def parse_seller_header(self, seller_url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Переходим на seller_url и вытаскиваем:
        - рейтинг магазина (4.9)
        - кол-во отзывов (6701)
        - кол-во заказов (19100)
        """
        logger.info(f"Читаем шапку продавца: {seller_url}")
        try:
            await self.page.goto(seller_url, wait_until="domcontentloaded", timeout=25000)
            try:
                await self.page.wait_for_load_state("networkidle", timeout=8000)
            except PlaywrightTimeoutError:
                pass
            await self.human_delay(1, 2)

            body = await self.page.inner_text("body")
        except Exception as e:
            logger.warning(f"Не удалось прочитать шапку продавца: {e}")
            return None, None, None

        body = body.replace("\u00a0", " ")

        seller_rating = None
        seller_feedback = None
        seller_orders = None

        # рейтинг вида "4,9" или "4.9"
        m = re.search(r"(\d+[.,]\d+)\s*/\s*5", body)
        if not m:
            m = re.search(r"(\d+[.,]\d+)\s+из\s+5", body, re.IGNORECASE)
        if m:
            seller_rating = m.group(1).replace(",", ".")

        # отзывы: "6701 отзыв", "6 701 отзывов"
        m = re.search(r"([\d\s]+)\s+отзыв", body, re.IGNORECASE)
        if m:
            digits = re.findall(r"\d+", m.group(1))
            if digits:
                seller_feedback = "".join(digits)

        # заказы: "19,1К заказов", "19100 заказов"
        # сначала пробуем форматы с К / k
        m = re.search(r"([\d\s.,]+)\s*к\s+заказ", body, re.IGNORECASE)
        if m:
            val = m.group(1).strip().replace(" ", "").replace("\u00a0", "")
            val = val.replace(",", ".")
            try:
                num = float(val)
                seller_orders = str(int(num * 1000))
            except ValueError:
                pass
        if seller_orders is None:
            m = re.search(r"([\d\s]+)\s+заказ", body, re.IGNORECASE)
            if m:
                digits = re.findall(r"\d+", m.group(1))
                if digits:
                    seller_orders = "".join(digits)

        logger.info(
            f"Шапка продавца: rating={seller_rating}, feedback={seller_feedback}, orders={seller_orders}"
        )
        return seller_rating, seller_feedback, seller_orders

    # ============================================================
    #   ВСПОМОГАТЕЛЬНЫЙ СКРОЛЛ
    # ============================================================
    async def _scroll_page(self) -> None:
        try:
            for _ in range(6):
                await self.page.mouse.wheel(0, 800)
                await self.page.wait_for_timeout(500)
        except Exception:
            pass

    # ============================================================
    #   ПАРСИНГ ОДНОЙ КАРТОЧКИ ТОВАРА
    # ============================================================
    async def parse_product(
        self,
        url: str,
        seller_rating: Optional[str] = None,
        seller_feedback: Optional[str] = None,
        seller_orders: Optional[str] = None,
    ) -> Product:
        logger.info(f"Парсим товар: {url}")
        await self.page.goto(url, wait_until="domcontentloaded", timeout=25000)
        try:
            await self.page.wait_for_load_state("networkidle", timeout=8000)
        except PlaywrightTimeoutError:
            pass

        await self._scroll_page()
        await self.page.wait_for_timeout(1000)

        # ---------- Название ----------
        name = ""
        try:
            el = await self.page.query_selector("h1")
            if el:
                name = (await el.text_content() or "").strip()
        except Exception:
            pass

        brand: Optional[str] = None
        rating: Optional[str] = None
        feedbacks: Optional[str] = None
        images: List[str] = []
        description: Optional[str] = None
        seller: Optional[str] = None
        category: Optional[str] = None
        subcategory: Optional[str] = None

        # ---------- JSON-LD ----------
        try:
            scripts = await self.page.query_selector_all("script[type='application/ld+json']")
            for s in scripts:
                raw = await s.text_content()
                if not raw:
                    continue
                try:
                    data = json.loads(raw)
                except Exception:
                    continue

                objs = []
                if isinstance(data, dict):
                    objs = [data]
                elif isinstance(data, list):
                    objs = data

                for obj in objs:
                    if not isinstance(obj, dict):
                        continue

                    if obj.get("@type") == "Product" or "offers" in obj:
                        # бренд
                        if brand is None and "brand" in obj:
                            b = obj["brand"]
                            if isinstance(b, dict):
                                brand = (b.get("name") or "").strip() or None
                            elif isinstance(b, str):
                                brand = b.strip() or None

                        # описание
                        if description is None and "description" in obj:
                            d = obj["description"]
                            if isinstance(d, str) and d.strip():
                                description = d.strip()

                        # продавец
                        if seller is None and "seller" in obj:
                            sdata = obj["seller"]
                            if isinstance(sdata, dict):
                                nm = sdata.get("name")
                                if isinstance(nm, str) and nm.strip():
                                    seller = nm.strip()
                            elif isinstance(sdata, str) and sdata.strip():
                                seller = sdata.strip()

                        # рейтинг / отзывы
                        aggr = obj.get("aggregateRating") or obj.get("aggregate_rating")
                        if isinstance(aggr, dict):
                            if rating is None:
                                rv = aggr.get("ratingValue") or aggr.get("rating_value")
                                if isinstance(rv, (int, float)):
                                    rating = str(rv)
                                elif isinstance(rv, str) and rv.strip():
                                    rating = rv.strip().replace(",", ".")
                            if feedbacks is None:
                                rc = aggr.get("reviewCount") or aggr.get("review_count")
                                if isinstance(rc, (int, float)):
                                    feedbacks = str(int(rc))
                                elif isinstance(rc, str) and rc.strip():
                                    digits = re.findall(r"\d+", rc)
                                    if digits:
                                        feedbacks = "".join(digits)

                        # картинки
                        if "image" in obj:
                            imgs = obj["image"]
                            if isinstance(imgs, str):
                                images.append(imgs)
                            elif isinstance(imgs, list):
                                for x in imgs:
                                    if isinstance(x, str):
                                        images.append(x)
        except Exception as e:
            logger.debug(f"Ошибка JSON-LD: {e}")

        # ---------- бренд: fallback ----------
        if brand is None:
            sels = [
                "[itemprop='brand'] [itemprop='name']",
                "[itemprop='brand']",
                "a[slot='brand'] span",
                "a[slot='brand']",
                "a[href*='/brand/'] span",
                "a[href*='/brand/']",
            ]
            for sel in sels:
                try:
                    el = await self.page.query_selector(sel)
                    if not el:
                        continue
                    txt = (await el.text_content() or "").strip()
                    if not txt:
                        txt = (await el.get_attribute("content") or "").strip()
                    if txt:
                        brand = txt
                        break
                except Exception:
                    continue

        # ---------- цена ----------
        price: Optional[str] = None
        price_selectors = [
            "[data-widget='webPrice'] span",
            "div[style*='price'] span",
            "span[slot='price']",
        ]
        for sel in price_selectors:
            try:
                el = await self.page.query_selector(sel)
                if el:
                    text = (await el.text_content() or "").strip()
                    text = text.replace("\u00a0", " ")
                    digits = re.findall(r"\d+", text)
                    if digits:
                        price = "".join(digits)
                        break
            except Exception:
                continue

        # ---------- рейтинг / отзывы: fallback ----------
        if rating is None or feedbacks is None:
            try:
                link = await self.page.query_selector("a[href*='#section-reviews']")
                if link:
                    txt = (await link.text_content() or "").strip()
                    txt = txt.replace("\u00a0", " ")
                    if rating is None:
                        m = re.search(r"(\d+[.,]\d+)", txt)
                        if m:
                            rating = m.group(1).replace(",", ".")
                    if feedbacks is None:
                        m = re.search(r"(\d[\d\s]*)\s+отзыв", txt)
                        if m:
                            feedbacks = re.sub(r"\s+", "", m.group(1))
            except Exception:
                pass

        if rating is None:
            try:
                el = await self.page.query_selector("[itemprop='ratingValue']")
                if el:
                    t = (await el.text_content() or "") or (await el.get_attribute("content") or "")
                    t = t.strip()
                    if t:
                        rating = t.replace(",", ".")
            except Exception:
                pass

        if feedbacks is None:
            try:
                el = await self.page.query_selector("[itemprop='reviewCount']")
                if el:
                    t = (await el.text_content() or "") or (await el.get_attribute("content") or "")
                    t = t.strip()
                    if t:
                        digits = re.findall(r"\d+", t)
                        if digits:
                            feedbacks = "".join(digits)
            except Exception:
                pass

        # ---------- описание: fallback ----------
        if description is None:
            try:
                el = await self.page.query_selector("[itemprop='description']")
                if el:
                    txt = (await el.text_content() or "").strip()
                    if txt:
                        description = txt
            except Exception:
                pass

        if description is None:
            try:
                el = await self.page.query_selector("div[data-widget='webDescription']")
                if el:
                    txt = (await el.text_content() or "").strip()
                    if txt:
                        description = txt
            except Exception:
                pass

        # ---------- картинки из галереи ----------
        try:
            seen = dict.fromkeys(images or [])

            try:
                await self.page.wait_for_selector("[data-widget='webGallery']", timeout=8000)
            except PlaywrightTimeoutError:
                pass

            gallery = await self.page.query_selector("[data-widget='webGallery']")
            if gallery:
                els = await gallery.query_selector_all("img")
                for el in els:
                    src = await el.get_attribute("src")
                    if not src:
                        srcset = await el.get_attribute("srcset")
                        if srcset:
                            src = srcset.split()[0]
                    if not src:
                        src = await el.get_attribute("data-src")
                    if not src:
                        continue

                    base = src.split("?", 1)[0]
                    if "/wc50/" in base or "/wc75/" in base:
                        hd = base.replace("/wc50/", "/wc1000/").replace("/wc75/", "/wc1000/")
                    else:
                        hd = base
                    if not hd.startswith("http"):
                        continue
                    if hd not in seen:
                        seen[hd] = None

            images = list(seen.keys())
            if len(images) > 20:
                images = images[:20]
        except Exception:
            pass

        # ---------- seller / category / subcategory из текста ----------
        try:
            body_text = await self.page.inner_text("body")
        except Exception:
            body_text = ""

        body_text = body_text.replace("\u00a0", " ")
        lines = [l.strip() for l in body_text.splitlines() if l.strip()]

        # seller fallback
        if seller is None and lines:
            for i, l in enumerate(lines):
                if re.search(r"\bМагазин\b", l, re.IGNORECASE):
                    for j in range(i + 1, min(i + 8, len(lines))):
                        cand = lines[j]
                        if re.search(r"(перейти|подписаться|подтвержд[ёе]нн|бренд)", cand, re.IGNORECASE):
                            continue
                        if re.search(r"\d", cand):
                            continue
                        if len(cand) < 2:
                            continue
                        seller = cand
                        break
                    if seller:
                        break

        # хлебные крошки
        try:
            crumbs_texts: List[str] = []

            crumb_selectors = [
                "[data-widget='breadCrumbs'] a",
                "nav[aria-label*='крошк'] a",
                "nav[aria-label*='Хлебн'] a",
                "nav a[href*='/category/']",
            ]

            for sel in crumb_selectors:
                els = await self.page.query_selector_all(sel)
                if not els:
                    continue

                tmp = []
                for el in els:
                    t = (await el.text_content() or "").strip()
                    if not t:
                        continue
                    if t.lower().startswith("главная"):
                        continue
                    tmp.append(t)

                if tmp:
                    crumbs_texts = tmp
                    break

            if crumbs_texts:
                category = crumbs_texts[0]
                if len(crumbs_texts) > 1:
                    subcategory = " > ".join(crumbs_texts[1:])
        except Exception:
            pass

        # ---------- ID товара ----------
        product_id: Optional[str] = None
        m = re.search(r"/product/[^/]*?(\d+)(?:/|\?|$)", url)
        if m:
            product_id = m.group(1)

        return Product(
            id=product_id,
            name=name or "Без названия",
            brand=brand,
            price=price,
            rating=rating,
            feedbacks=feedbacks,
            images=images,
            description=description,
            seller=seller,
            category=category,
            subcategory=subcategory,
            url=url,
            seller_rating=seller_rating,
            seller_feedback=seller_feedback,
            seller_orders=seller_orders,
        )

    # ============================================================
    #   РЕЖИМ: ПОИСКОВЫЙ
    # ============================================================
    async def search_products(
        self,
        query: str,
        pages: int = 1,
        max_products: int = 15,
    ) -> Tuple[List[Product], str]:
        results: List[Product] = []
        try:
            await self.setup_browser()
            links = await self.fetch_product_links(query, pages)

            if not links:
                return [], "Не найдено товаров по запросу"

            max_products = min(max_products, len(links))
            for i, url in enumerate(links[:max_products], 1):
                logger.info(f"[{i}/{max_products}] Обработка товара")
                product = await self.parse_product(url)
                results.append(product)
                if i < max_products:
                    await self.human_delay(1, 2)

            total = len(results)
            with_prices = sum(1 for p in results if p.price)
            with_ratings = sum(1 for p in results if p.rating)
            with_fb = sum(1 for p in results if p.feedbacks)

            stats = (
                f"Статистика парсинга:\n"
                f"• Всего товаров: {total}\n"
                f"• С ценами: {with_prices}\n"
                f"• С рейтингами: {with_ratings}\n"
                f"• С отзывами: {with_fb}\n"
                f"• Запрос: '{query}'"
            )
            return results, stats

        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
            return [], f"Ошибка при парсинге: {e}"
        finally:
            await self.close_browser()


# ================================================================
#   ОБЁРТКИ ДЛЯ ЗАПУСКА
# ================================================================
async def run_parser_query(query: str, output: str, pages: int = 1, max_products: int = 15) -> None:
    parser = OzonParser()
    products, stats = await parser.search_products(query, pages=pages, max_products=max_products)

    if not products:
        logger.warning("Ничего не спарсилось.")
        print(stats)
        return

    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)

    fieldnames = [
        "id", "name", "brand", "price", "rating", "feedbacks",
        "image", "description",
        "seller", "category", "subcategory",
        "sellerrating", "sellerfeedback", "sellerordes",
        "url",
    ]
    with open(output, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=",")
        writer.writeheader()
        for p in products:
            writer.writerow(
                {
                    "id": p.id or "",
                    "name": p.name,
                    "brand": p.brand or "",
                    "price": p.price or "",
                    "rating": p.rating or "",
                    "feedbacks": p.feedbacks or "",
                    "image": ",".join(p.images) if p.images else "",
                    "description": (p.description or "").replace("\n", " ").strip(),
                    "seller": p.seller or "",
                    "category": p.category or "",
                    "subcategory": p.subcategory or "",
                    "sellerrating": p.seller_rating or "",
                    "sellerfeedback": p.seller_feedback or "",
                    "sellerordes": p.seller_orders or "",
                    "url": p.url,
                }
            )

    logger.info(f"CSV сохранён: {output}")
    print(stats)
    print(f"\nФайл сохранён: {output}")


async def run_parser_url(url: str, output: str) -> None:
    """Режим: один товар по URL."""
    parser = OzonParser()
    products: List[Product] = []
    stats: str

    try:
        await parser.setup_browser()
        product = await parser.parse_product(url)
        products.append(product)

        stats = (
            "Статистика парсинга (режим URL):\n"
            f"• Всего товаров: 1\n"
            f"• С ценой: {'1' if product.price else '0'}\n"
            f"• С рейтингом: {'1' if product.rating else '0'}\n"
            f"• С отзывами: {'1' if product.feedbacks else '0'}\n"
            f"• URL: {url}"
        )
    except Exception as e:
        logger.error(f"Ошибка при парсинге URL: {e}")
        print(f"Ошибка при парсинге URL: {e}")
        return
    finally:
        await parser.close_browser()

    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)

    fieldnames = [
        "id", "name", "brand", "price", "rating", "feedbacks",
        "image", "description",
        "seller", "category", "subcategory",
        "sellerrating", "sellerfeedback", "sellerordes",
        "url",
    ]
    with open(output, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=",")
        writer.writeheader()
        for p in products:
            writer.writerow(
                {
                    "id": p.id or "",
                    "name": p.name,
                    "brand": p.brand or "",
                    "price": p.price or "",
                    "rating": p.rating or "",
                    "feedbacks": p.feedbacks or "",
                    "image": ",".join(p.images) if p.images else "",
                    "description": (p.description or "").replace("\n", " ").strip(),
                    "seller": p.seller or "",
                    "category": p.category or "",
                    "subcategory": p.subcategory or "",
                    "sellerrating": p.seller_rating or "",
                    "sellerfeedback": p.seller_feedback or "",
                    "sellerordes": p.seller_orders or "",
                    "url": p.url,
                }
            )

    logger.info(f"CSV сохранён: {output}")
    print(stats)
    print(f"\nФайл сохранён: {output}")


async def run_parser_seller(seller_url: str, output: str, pages: int = 1, max_products: int = 100) -> None:
    """Режим: все товары продавца по URL seller."""
    parser = OzonParser()
    products: List[Product] = []

    try:
        await parser.setup_browser()

        # сперва вытащим данные продавца из шапки
        seller_rating, seller_feedback, seller_orders = await parser.parse_seller_header(seller_url)

        # затем соберём ссылки на товары
        links = await parser.fetch_product_links_from_seller(seller_url, pages=pages)

        if not links:
            print("Не удалось найти товары на странице продавца.")
            return

        if max_products:
            links = links[:max_products]

        total_links = len(links)
        logger.info(f"Будет обработано товаров: {total_links}")

        for i, url in enumerate(links, 1):
            logger.info(f"[{i}/{total_links}] Парсим товар продавца")
            product = await parser.parse_product(
                url,
                seller_rating=seller_rating,
                seller_feedback=seller_feedback,
                seller_orders=seller_orders,
            )
            products.append(product)
            if i < total_links:
                await parser.human_delay(1, 2)

    except Exception as e:
        logger.error(f"Ошибка при парсинге продавца: {e}")
        print(f"Ошибка при парсинге продавца: {e}")
        return
    finally:
        await parser.close_browser()

    if not products:
        print("После парсинга продавца не получено ни одного товара.")
        return

    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)

    fieldnames = [
        "id", "name", "brand", "price", "rating", "feedbacks",
        "image", "description",
        "seller", "category", "subcategory",
        "sellerrating", "sellerfeedback", "sellerordes",
        "url",
    ]
    with open(output, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=",")
        writer.writeheader()
        for p in products:
            writer.writerow(
                {
                    "id": p.id or "",
                    "name": p.name,
                    "brand": p.brand or "",
                    "price": p.price or "",
                    "rating": p.rating or "",
                    "feedbacks": p.feedbacks or "",
                    "image": ",".join(p.images) if p.images else "",
                    "description": (p.description or "").replace("\n", " ").strip(),
                    "seller": p.seller or "",
                    "category": p.category or "",
                    "subcategory": p.subcategory or "",
                    "sellerrating": p.seller_rating or "",
                    "sellerfeedback": p.seller_feedback or "",
                    "sellerordes": p.seller_orders or "",
                    "url": p.url,
                }
            )

    total = len(products)
    with_prices = sum(1 for p in products if p.price)
    with_ratings = sum(1 for p in products if p.rating)
    with_fb = sum(1 for p in products if p.feedbacks)

    stats = (
        "Статистика парсинга (режим SELLER):\n"
        f"• Всего товаров: {total}\n"
        f"• С ценами: {with_prices}\n"
        f"• С рейтингами: {with_ratings}\n"
        f"• С отзывами: {with_fb}\n"
        f"• URL продавца: {seller_url}\n"
        f"• Рейтинг магазина: {products[0].seller_rating or ''}\n"
        f"• Отзывы о магазине: {products[0].seller_feedback or ''}\n"
        f"• Заказы магазина: {products[0].seller_orders or ''}"
    )

    logger.info(f"CSV сохранён: {output}")
    print(stats)
    print(f"\nФайл сохранён: {output}")


# ================================================================
#   CLI
# ================================================================
if __name__ == "__main__":
    import argparse

    cli_parser = argparse.ArgumentParser(
        description=(
            "Парсер Ozon -> CSV\n"
            "Режимы:\n"
            " 1) Поиск по запросу: -q \"игровая мышь\"\n"
            " 2) Один товар по URL: -u \"https://www.ozon.ru/product/...\"\n"
            " 3) Все товары продавца: -s \"https://www.ozon.ru/seller/...\""
        )
    )

    group = cli_parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-q", "--query",
        help="Поисковый запрос (например: 'игровая мышь')",
    )
    group.add_argument(
        "-u", "--url",
        help="URL карточки товара Ozon (например: 'https://www.ozon.ru/product/...')",
    )
    group.add_argument(
        "-s", "--seller-url",
        help="URL страницы продавца Ozon (например: 'https://www.ozon.ru/seller/dareu-2265016/')",
    )

    cli_parser.add_argument(
        "-o", "--output",
        default="ozon_results.csv",
        help="Путь к выходному CSV файлу",
    )
    cli_parser.add_argument(
        "-p", "--pages",
        type=int,
        default=1,
        help="Сколько страниц обходить (для --query и --seller-url)",
    )
    cli_parser.add_argument(
        "-m", "--max-products",
        type=int,
        default=15,
        help="Максимальное число товаров (для --query и --seller-url)",
    )

    args = cli_parser.parse_args()

    if args.url:
        asyncio.run(
            run_parser_url(
                url=args.url,
                output=args.output,
            )
        )
    elif args.seller_url:
        asyncio.run(
            run_parser_seller(
                seller_url=args.seller_url,
                output=args.output,
                pages=args.pages,
                max_products=args.max_products,
            )
        )
    else:
        asyncio.run(
            run_parser_query(
                query=args.query,
                output=args.output,
                pages=args.pages,
                max_products=args.max_products,
            )
        )
