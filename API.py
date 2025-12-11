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

app = Flask(__name__)
CORS(app)

# Секретный ключ для JWT (в продакшене должен быть сложным и храниться в env)
app.config['SECRET_KEY'] = 'your-super-secret-jwt-key-change-in-production'

# Настройка Swagger
swagger = Swagger(app, template={
    "info": {
        "title": "Ozon Parser API with Auth",
        "description": "API для парсинга продавцов Ozon с аутентификацией пользователей.",
        "version": "1.0.0"
    },
    "host": "localhost:5000",
    "basePath": "/",
    "schemes": ["http"]
})

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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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


def save_to_database(products, seller_id):
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

                    cursor.execute("""
                        INSERT INTO products (seller_id, title, brand, category, price)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        seller_id,
                        title[:500] if title else '',
                        brand[:255] if brand else '',
                        category[:255] if category else '',
                        price
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
# ЗАЩИЩЕННЫЕ ЭНДПОИНТЫ ПАРСИНГА
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
              example: true
            seller_url:
              type: string
            seller_id:
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

        print(f"🚀 Начинаю парсинг продавца: {seller_url}")

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
                    "FEEDBACKS": row.get("feedbacks", "")
                }
                products_json.append(product)

        print(f"✅ Спарсено товаров: {len(products_json)}")

        # Шаг 3: Сохраняем в БД
        print("💾 Сохраняю в базу данных...")
        saved_count = save_to_database(products_json, seller_id)

        # Шаг 4: Очищаем временные файлы
        try:
            os.unlink(temp_csv.name)
        except:
            pass

        # Возвращаем результат
        return jsonify({
            'success': True,
            'message': f'✅ Парсинг завершен успешно!',
            'seller_url': seller_url,
            'seller_id': seller_id,
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


# ============================================
# ОСТАЛЬНЫЕ ЭНДПОИНТЫ (можно оставить публичными)
# ============================================

@app.route('/products', methods=['GET'])
def get_products():
    """Получить все товары из базы данных"""
    try:
        seller_id = request.args.get('seller_id')
        limit = request.args.get('limit', 100, type=int)

        conn = get_db()
        with conn.cursor() as cursor:
            if seller_id:
                cursor.execute("""
                    SELECT * FROM products 
                    WHERE seller_id = %s 
                    ORDER BY created_at DESC 
                    LIMIT %s
                """, (seller_id, limit))
            else:
                cursor.execute("""
                    SELECT * FROM products 
                    ORDER BY created_at DESC 
                    LIMIT %s
                """, (limit,))

            products = cursor.fetchall()

            if seller_id:
                cursor.execute("SELECT COUNT(*) as total FROM products WHERE seller_id = %s", (seller_id,))
            else:
                cursor.execute("SELECT COUNT(*) as total FROM products")

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
    """Статистика по БД"""
    try:
        conn = get_db()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_products,
                    COUNT(DISTINCT seller_id) as total_sellers,
                    AVG(price) as avg_price,
                    MIN(created_at) as first_parse,
                    MAX(created_at) as last_parse
                FROM products
            """)
            stats = cursor.fetchone()

            cursor.execute("""
                SELECT seller_id, COUNT(*) as product_count
                FROM products
                GROUP BY seller_id
                ORDER BY product_count DESC
            """)
            sellers = cursor.fetchall()

        conn.close()

        return jsonify({
            'success': True,
            'stats': stats,
            'sellers': sellers
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/db-fix', methods=['POST'])
def fix_database():
    """Исправить структуру БД вручную"""
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
    """Проверить структуру таблицы users"""
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


@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ozon Parser API with Auth</title>
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
            .protected-endpoint {
                border-left-color: #e53e3e;
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
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Ozon Parser API with Authentication</h1>

            <a href="/apidocs" class="swagger-btn" target="_blank">
                📚 Открыть Swagger UI
            </a>

            <div class="debug-info">
                <h3>🔧 Отладка базы данных</h3>
                <p>Если есть ошибки с таблицей users:</p>
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

            <div class="endpoint protected-endpoint">
                <h3>🛡️ GET /parse</h3>
                <p><strong>Парсинг продавца Ozon (защищено)</strong></p>
                <p>Требуется JWT токен в заголовке Authorization</p>
                <code>curl "http://localhost:5000/parse?url=..." \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN"</code>
            </div>

            <div class="endpoint debug-endpoint">
                <h3>🔍 GET /check-users-table</h3>
                <p>Проверить структуру таблицы users</p>
                <code>curl http://localhost:5000/check-users-table</code>
            </div>

            <div class="endpoint debug-endpoint">
                <h3>🔧 POST /db-fix</h3>
                <p>Исправить структуру базы данных</p>
                <code>curl -X POST http://localhost:5000/db-fix</code>
            </div>
        </div>

        <script>
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
    print("🔧 Установите недостающие зависимости если нужно:")
    print("   pip install PyJWT")

    print("=" * 70)
    print("🔧 Инициализация Ozon Parser API с аутентификацией...")

    if init_database():
        print("✅ База данных готова")
    else:
        print("⚠️  Проблемы с БД, но API продолжит работу")

    print("\n" + "=" * 70)
    print("🚀 Ozon Parser API with Auth ЗАПУЩЕН!")
    print("=" * 70)
    print("📌 Главная страница:  http://localhost:5000")
    print("📚 Swagger UI:        http://localhost:5000/apidocs")
    print("🔧 Отладка БД:")
    print("   GET  /check-users-table - проверить таблицу")
    print("   POST /db-fix            - исправить структуру")
    print("=" * 70)
    print("\n🔐 Первые шаги:")
    print("1. Проверьте структуру таблицы: http://localhost:5000/check-users-table")
    print("2. Если нужно, исправьте: POST http://localhost:5000/db-fix")
    print("3. Зарегистрируйте пользователя через /register")
    print("=" * 70)

    app.run(debug=True, port=5000, host='0.0.0.0')