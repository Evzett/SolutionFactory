
## Описание MVP
MVP представляет собой сервис для селлеров маркетплейсов, который по ссылке на профиль продавца автоматически импортирует товары, анализирует отзывы с помощью ML, формирует портрет целевой аудитории и генерирует персональный интернет-магазин.

---

## Основные функции MVP

### 1. Импорт товаров по ссылке
Селлер загружает ссылку на свой профиль в Wildberries или Ozon.  
Система автоматически:
- парсит товары,
- выгружает фотографии и характеристики,
- собирает и структурирует отзывы,
- сохраняет данные в MySQL.

---

### 2. NLP-анализ отзывов
ML-модуль выполняет:
- sentiment analysis (тональность),
- topic modeling (ключевые темы),
- выделение триггеров и барьеров покупателей.

Результатом является отчёт: что нравится покупателям и что мешает покупке.

---

### 3. Формирование портрета целевой аудитории (ЦА)
На основе отзывов, характеристик товаров и поведения пользователей сервис определяет:
- ключевые сегменты ЦА,
- мотивации покупателей,
- барьеры и сомнения,
- триггеры, влияющие на решение о покупке.

---

### 4. Рекомендации по улучшению карточек товаров
Система автоматически предлагает:
- улучшения в описании,
- идеи для новых фотографий,
- улучшения характеристик,
- факторы, повышающие конверсию.

---

### 5. Генерация персонального интернет-магазина
Система создает статический сайт, который включает:
- карточки товаров,
- автоматически улучшенные описания,
- рекомендации для покупателей,
- целевую структуру, оптимизированную под сегменты ЦА.

Сайт рендерится автоматически и используется как внешняя витрина продавца.

---

# Целевая аудитория (ЦА)


# Краткое резюме ЦА
Наш сервис нужен всем селлерам, которым важно:
- понять свою аудиторию,
- улучшить карточки товаров,
- анализировать отзывы автоматически,
- быстро создавать собственную витрину,
- увеличивать продажи.



# User Stories для двух сервисов (Сервис 1 и Сервис 2)

## СЕРВИС 1

## User Story 1. Авторизация / регистрация
Как селлер
я хочу зарегистрироваться и авторизоваться в сервисе,  
чтобы получить доступ к аналитике и инструментам.

## User Story 2. Загрузить ссылку на свой профиль
Как селлер  
я хочу загрузить ссылку на свой магазин на Wildberries/Ozon,  
чтобы сервис смог автоматически импортировать мои товары.

## User Story 3. Выгрузить товары по ссылке
Как селлер  
я хочу, чтобы система автоматически выгрузила товары по ссылке,  
чтобы мне не пришлось переносить карточки вручную.

## User Story 4. Просмотреть NLP анализ отзывов
Как селлер  
я хочу просматривать анализ отзывов на товары,  
чтобы понимать, что нравится и не нравится покупателям.

## User Story 5. Сформировать портрет целевой аудитории
Как селлер  
я хочу получить автоматически сформированный портрет ЦА,  
чтобы понимать, кто является моим покупателем и зачем он делает покупку.

## User Story 6. Просмотреть анализ ЦА
Как селлер  
я хочу видеть сегменты аудитории, их мотивации, барьеры и триггеры,  
чтобы оптимизировать карточки под реальных покупателей.

## User Story 7. Просмотреть рекомендации по улучшению карточки товара
Как селлер  
я хочу получать рекомендации по улучшению фото, описания и характеристик,  
чтобы повышать конверсию моего товара.

## User Story 8. Генерация собственного интернет-магазина
Как селлер  
я хочу сгенерировать собственный интернет-магазин,  
чтобы размещать свои товары вне маркетплейсов и привлекать трафик.

## User Story 9. Просмотреть статистику по товарам
Как селлер  
я хочу видеть статистику по товарам (динамику рейтинга, негатива, характеристик),  
чтобы отслеживать эффективность и вовремя видеть проблемы.


### Итоговые эпики 

Импорт данных: загрузка ссылки, выгрузка товаров  
Аналитика: анализ отзывов, статистика товаров  
ML: портрет ЦА, сегменты ЦА  
Рекомендации: улучшение карточки  
Генерация магазина: создание собственной витрины  
Управление доступом: авторизация


## СЕРВИС 2 - Интернет-магазин (витрина для покупателей)


## User Story 1. Найти интересующий товар
Как покупатель  
я хочу находить интересующие товары,  
чтобы быстро подобрать нужный продукт.

## User Story 2. Просмотреть карточку товара
Как покупатель  
я хочу открывать карточку товара,  
чтобы увидеть фотографии, описание и характеристики.

## User Story 3. Добавить товар в избранное
Как покупатель  
я хочу добавлять товары в избранное,  
чтобы вернуться к ним позже.

## User Story 4. Добавить товар в корзину
Как покупатель  
я хочу добавить товар в корзину,  
чтобы оформить заказ позже.

## User Story 5. Найти и отфильтровать товары
Как покупатель  
я хочу фильтровать товары по цене, категории и параметрам,  
чтобы быстрее находить нужный вариант.

## User Story 6. Купить товар
Как покупатель  
я хочу перейти на карточку товара на Wildberries/Ozon,  
чтобы оформить покупку на привычной платформе.

## User Story 7. Редактировать карточки товара (для селлера)
Как селлер  
я хочу редактировать описания, фотографии и текст карточек магазина с помощью ии,  
чтобы витрина выглядела корректно и профессионально.

## User Story 8. Просматривать карточки товаров в витрине (для селлера)
Как селлер  
я хочу видеть, как мои товары отображаются покупателям,  
чтобы убедиться в корректности генерации магазина.

**Итоговые эпики**<br>
Покупательские функции: поиск, просмотр товара, избранное, корзина, покупка, фильтры  
Управление витриной (селлер): просмотр карточек, редактирование

## Схема архитектуры

```mermaid
flowchart LR
    Seller[[Селлер]]
    Buyer[[Покупатель]]

    subgraph CoreService[Сервис A: Аналитика и импорт]
        Backend[Backend API
        Analytics + Import + ML]
        Parser[Parser Service
        WB/Ozon Scraper]
        ML[ML Service
        NLP + Segmentation]
        CoreDB[(Core MySQL DB)]
    end

    subgraph StoreService[Сервис B: Интернет-магазин]
        StoreBackend[Storefront Backend
        Редактор магазина]
        StoreDB[(Storefront MySQL DB)]
        Generator[Store Generator
        HTML Renderer]
        Storefront[Static Storefront
        Nginx + S3]
    end

    Seller --> Backend

    Backend --> Parser
    Backend --> ML
    Backend --> CoreDB

    Parser --> CoreDB
    ML --> CoreDB

    Backend -->|экспорт товаров и аналитики| StoreBackend
    StoreBackend --> StoreDB

    Seller -->|редактирование карточек и страниц| StoreBackend
    StoreBackend --> StoreDB

    StoreBackend --> Generator
    Generator --> Storefront

    Buyer --> Storefront
    Storefront --> Buyer
```    

### Use case диаграммы

```mermaid
flowchart LR

    %% Actors
    User([Юзер])
    Seller([Селлер])

    %% Use cases for User
    UC1((Добавить товар в избранное))
    UC2((Добавить товар в корзину))
    UC3((Найти и отфильтровать товары))
    UC4((Найти интересующий товар))
    UC5((Просмотреть карточку товара))
    UC6((Купить товар))
    UC7((Регистрация / Авторизация))

    %% Use cases for Seller
    UC8((Редактирование карточки товара))
    UC9((Редактирование фото и описания с помощью ИИ))
    UC10((Просмотр карточек товаров))

    %% System container
    subgraph SYSTEM [Интернет-магазин]
        UC1
        UC2
        UC3
        UC4
        UC5
        UC6
        UC7
        UC8
        UC9
        UC10
    end

    %% Relations
    User --> UC1
    User --> UC2
    User --> UC3
    User --> UC4
    User --> UC5
    User --> UC6
    User --> UC7

    Seller --> UC8
    Seller --> UC9
    Seller --> UC10
```

### Use case диаграмма для нашего сервиса 

```mermaid
flowchart LR

    %% Actor
    Seller([Селлер])

    %% Use Cases
    UC1((Сформировать портрет ЦА))
    UC2((Загрузить ссылку на свой профиль))
    UC3((Выгрузить товары по ссылке))
    UC4((Посмотреть NLP анализ отзывов))
    UC5((Просмотреть статистику по товарам))
    UC6((Просмотреть анализ ЦА))
    UC7((Генерация собственного интернет-магазина))
    UC8((Авторизация / Аутентификация / Регистрация))
    UC9((Просмотреть рекомендации по улучшению карточек))

    %% System boundary
    subgraph SERVICE [Наш сервис]
        UC1
        UC2
        UC3
        UC4
        UC5
        UC6
        UC7
        UC8
        UC9
    end

    %% Connections
    Seller --> UC1
    Seller --> UC2
    Seller --> UC3
    Seller --> UC4
    Seller --> UC5
    Seller --> UC6
    Seller --> UC7
    Seller --> UC8
    Seller --> UC9
```
## ER-диаграмма
```mermaid
erDiagram
    USERS ||--o{ SELLERS : owns
    SELLERS ||--o{ PRODUCTS : has
    PRODUCTS ||--o{ PRODUCT_IMAGES : has
    PRODUCTS ||--o{ PRODUCT_CHARACTERISTICS : has
    PRODUCTS ||--o{ REVIEWS : has
    REVIEWS ||--|| REVIEW_NLP : analyzed
    PRODUCTS ||--|| PRODUCT_FEATURES : features
    SELLERS ||--o{ SEGMENTS : defines
    SEGMENTS ||--o{ PRODUCT_SEGMENTS : groups

    USERS {
        string id PK
        string email
        string passwordHash
    }

    SELLERS {
        string id PK
        string userId FK
        string storeName
    }

    PRODUCTS {
        string id PK
        string sellerId FK
        string title
        string brand
        string category
        float price
    }

    PRODUCT_IMAGES {
        string id PK
        string productId FK
        string url
    }

    PRODUCT_CHARACTERISTICS {
        string id PK
        string productId FK
        string name
        string value
    }

    REVIEWS {
        string id PK
        string productId FK
        int rating
        string reviewText
    }

    REVIEW_NLP {
        string reviewId PK
        float sentiment
        string topics
    }

    PRODUCT_FEATURES {
        string productId PK
        string features
        string embedding
    }

    SEGMENTS {
        string id PK
        string sellerId FK
        string name
    }

    PRODUCT_SEGMENTS {
        string productId FK
        string segmentId FK
        float score
    }

```

### Диаграмма №2 - STOREFRONT DATABASE (интернет-магазин + редактирование селлером)
```mermaid
erDiagram
    SELLERS ||--o{ STORE_PRODUCTS : publishes
    STORE_PRODUCTS ||--o{ STORE_PRODUCT_IMAGES : has
    STORE_PRODUCTS ||--o{ STORE_PRODUCT_DESCRIPTIONS : describes
    SELLERS ||--o{ STORE_PAGES : owns
    STORE_PAGES ||--o{ STORE_PRODUCTS : lists
    SELLERS ||--|| STOREFRONT_SETTINGS : config

    STOREFRONT_SETTINGS {
        string sellerId PK
        string theme
        string colorScheme
        string logoUrl
        string domain
    }

    STORE_PRODUCTS {
        string id PK
        string sellerId FK
        string originalProductId FK
        string customTitle
        float customPrice
        string isActive
        int displayOrder
    }

    STORE_PRODUCT_DESCRIPTIONS {
        string storeProductId FK
        string customDescription
        string seoText
    }

    STORE_PRODUCT_IMAGES {
        string id PK
        string storeProductId FK
        string url
        string isMain
    }

    STORE_PAGES {
        string id PK
        string sellerId FK
        string slug
        string title
        string layoutJson
    }
```
