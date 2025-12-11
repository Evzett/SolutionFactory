from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity
)
from datetime import timedelta
import datetime
import json
import uuid
import re
from sqlalchemy import text, func
from flask_cors import CORS
import os
from typing import Dict, List, Optional

# Для Swagger нужно использовать правильный импорт
try:
    from flasgger import Swagger

    SWAGGER_AVAILABLE = True
except ImportError:
    SWAGGER_AVAILABLE = False
    print("⚠️ Flasgger не установлен. Swagger UI будет недоступен.")

app = Flask(__name__)
CORS(app)

# Конфигурация
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/marketplace_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

# Конфигурация Swagger
if SWAGGER_AVAILABLE:
    app.config['SWAGGER'] = {
        'title': 'Marketplace API',
        'uiversion': 3,
        'specs_route': '/swagger/',
        'version': '1.0.0',
        'description': 'API для управления интернет-магазином',
        'tags': [
            {'name': 'Auth', 'description': 'Аутентификация и авторизация'},
            {'name': 'Seller', 'description': 'Операции с продавцами'},
            {'name': 'Import', 'description': 'Импорт товаров'},
            {'name': 'Products', 'description': 'Управление товарами'},
            {'name': 'Reviews', 'description': 'Отзывы и анализ'},
            {'name': 'Segments', 'description': 'Сегменты товаров'},
            {'name': 'Storefront', 'description': 'Управление магазином'},
            {'name': 'System', 'description': 'Системные функции'}
        ],
        'specs': [{
            'endpoint': 'apispec',
            'route': '/apispec.json',
            'rule_filter': lambda rule: True,
            'model_filter': lambda tag: True,
        }],
        'static_url_path': '/flasgger_static',
        'swagger_ui': True,
        'specs_route': '/swagger/'
    }

# Инициализация расширений
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Инициализация Swagger
if SWAGGER_AVAILABLE:
    swagger = Swagger(app)
else:
    # Если flasgger не установлен, создаем заглушку
    @app.route('/swagger/')
    def swagger_stub():
        return '''
        <html>
            <head>
                <title>Swagger UI не доступен</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                    .container { max-width: 800px; margin: 0 auto; text-align: center; }
                    .error { background: #ffebee; border: 2px solid #f44336; padding: 30px; border-radius: 10px; }
                    .btn { display: inline-block; padding: 12px 24px; background: #4CAF50; color: white; text-decoration: none; border-radius: 6px; margin: 20px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="error">
                        <h2>⚠️ Swagger UI не доступен</h2>
                        <p>Для использования Swagger UI необходимо установить flasgger:</p>
                        <code style="background: #333; color: #fff; padding: 10px; display: block; margin: 20px;">
                            pip install flasgger
                        </code>
                        <a href="/" class="btn">Вернуться на главную</a>
                    </div>
                </div>
            </body>
        </html>
        '''


# ==================== МОДЕЛИ ====================

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)


class Seller(db.Model):
    __tablename__ = 'sellers'
    id = db.Column(db.String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(255), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    store_name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    seller_id = db.Column(db.String(255), db.ForeignKey('sellers.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    brand = db.Column(db.String(100))
    category = db.Column(db.String(100))
    price = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = db.Column(db.String(255), db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text)
    author = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class ReviewNLP(db.Model):
    __tablename__ = 'review_nlp'
    review_id = db.Column(db.String(255), db.ForeignKey('reviews.id', ondelete='CASCADE'), primary_key=True)
    sentiment = db.Column(db.Numeric(3, 2), nullable=False)
    topics = db.Column(db.Text)
    keywords = db.Column(db.Text)
    analyzed_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class Segment(db.Model):
    __tablename__ = 'segments'
    id = db.Column(db.String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    seller_id = db.Column(db.String(255), db.ForeignKey('sellers.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class ProductSegment(db.Model):
    __tablename__ = 'product_segments'
    product_id = db.Column(db.String(255), db.ForeignKey('products.id', ondelete='CASCADE'), primary_key=True)
    segment_id = db.Column(db.String(255), db.ForeignKey('segments.id', ondelete='CASCADE'), primary_key=True)
    score = db.Column(db.Numeric(5, 4), nullable=False)


class Storefront(db.Model):
    __tablename__ = 'storefronts'
    id = db.Column(db.String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    seller_id = db.Column(db.String(255), db.ForeignKey('sellers.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(50), default='generating')
    store_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class ImportJob(db.Model):
    __tablename__ = 'import_jobs'
    id = db.Column(db.String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    seller_id = db.Column(db.String(255), db.ForeignKey('sellers.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(50), default='pending')
    source_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


# ==================== УТИЛИТЫ ====================

def validate_email(email):
    """Валидация email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    """Валидация пароля"""
    if len(password) < 8:
        return False, "Пароль должен содержать минимум 8 символов"
    if not re.search(r'[A-Z]', password):
        return False, "Пароль должен содержать хотя бы одну заглавную букву"
    if not re.search(r'[a-z]', password):
        return False, "Пароль должен содержать хотя бы одну строчную букву"
    if not re.search(r'[0-9]', password):
        return False, "Пароль должен содержать хотя бы одну цифру"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Пароль должен содержать хотя бы один специальный символ"
    return True, "Пароль валиден"


# ==================== ЭНДПОИНТЫ АУТЕНТИФИКАЦИИ ====================

@app.route('/auth/register', methods=['POST'])
def register():
    """
    Регистрация нового пользователя и продавца
    ---
    tags:
      - Auth
    summary: Регистрация пользователя
    description: Создание нового пользователя и связанного продавца
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
            - store_name
          properties:
            email:
              type: string
              example: "seller@example.com"
              description: Email пользователя
            password:
              type: string
              example: "SecurePass123!"
              description: Пароль (минимум 8 символов, заглавные, строчные, цифры, спецсимволы)
            store_name:
              type: string
              example: "Мой магазин"
              description: Название магазина
    responses:
      201:
        description: Пользователь успешно зарегистрирован
        schema:
          type: object
          properties:
            message:
              type: string
            access_token:
              type: string
            user_id:
              type: string
            seller_id:
              type: string
            store_name:
              type: string
      400:
        description: Ошибка валидации или пользователь уже существует
    """
    try:
        data = request.get_json()

        # Валидация email
        if not validate_email(data.get('email', '')):
            return jsonify({'error': 'Неверный формат email'}), 400

        # Валидация пароля
        is_valid, message = validate_password(data.get('password', ''))
        if not is_valid:
            return jsonify({'error': message}), 400

        # Проверка существования пользователя
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({'error': 'Пользователь с таким email уже существует'}), 400

        # Создание пользователя
        user = User(email=data['email'])
        user.set_password(data['password'])
        db.session.add(user)
        db.session.flush()  # Получаем ID пользователя

        # Создание продавца
        seller = Seller(
            user_id=user.id,
            store_name=data['store_name']
        )
        db.session.add(seller)

        # Создание токена
        access_token = create_access_token(identity=user.id)

        db.session.commit()

        return jsonify({
            'message': 'Регистрация успешна',
            'access_token': access_token,
            'user_id': user.id,
            'seller_id': seller.id,
            'store_name': seller.store_name
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/auth/login', methods=['POST'])
def login():
    """
    Аутентификация пользователя
    ---
    tags:
      - Auth
    summary: Вход в систему
    description: Аутентификация пользователя по email и паролю
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              example: "seller@example.com"
            password:
              type: string
              example: "SecurePass123!"
    responses:
      200:
        description: Успешный вход
        schema:
          type: object
          properties:
            message:
              type: string
            access_token:
              type: string
            user_id:
              type: string
            seller_id:
              type: string
            store_name:
              type: string
      401:
        description: Неверные учетные данные
    """
    try:
        data = request.get_json()

        # Поиск пользователя
        user = User.query.filter_by(email=data['email']).first()

        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Неверный email или пароль'}), 401

        # Получение информации о продавце
        seller = Seller.query.filter_by(user_id=user.id).first()

        # Создание токена
        access_token = create_access_token(identity=user.id)

        return jsonify({
            'message': 'Вход выполнен успешно',
            'access_token': access_token,
            'user_id': user.id,
            'seller_id': seller.id if seller else None,
            'store_name': seller.store_name if seller else None
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ==================== ЭНДПОИНТЫ ПРОДАВЦА ====================

@app.route('/seller/profile', methods=['GET'])
@jwt_required()
def get_seller_profile():
    """
    Получение профиля продавца
    ---
    tags:
      - Seller
    summary: Получить информацию о продавце
    description: Возвращает профиль продавца и статистику
    security:
      - BearerAuth: []
    produces:
      - application/json
    responses:
      200:
        description: Профиль продавца
        schema:
          type: object
          properties:
            seller_id:
              type: string
            store_name:
              type: string
            created_at:
              type: string
            statistics:
              type: object
              properties:
                product_count:
                  type: integer
      404:
        description: Продавец не найден
    """
    try:
        user_id = get_jwt_identity()
        seller = Seller.query.filter_by(user_id=user_id).first()

        if not seller:
            return jsonify({'error': 'Продавец не найден'}), 404

        # Получение статистики
        product_count = Product.query.filter_by(seller_id=seller.id).count()

        return jsonify({
            'seller_id': seller.id,
            'store_name': seller.store_name,
            'created_at': seller.created_at.isoformat(),
            'statistics': {
                'product_count': product_count
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ==================== ЭНДПОИНТЫ ИМПОРТА ====================

@app.route('/import/start', methods=['POST'])
@jwt_required()
def start_import():
    """
    Запуск импорта товаров
    ---
    tags:
      - Import
    summary: Запустить импорт товаров из внешнего источника
    security:
      - BearerAuth: []
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - source_url
          properties:
            source_url:
              type: string
              example: "https://example.com/products.csv"
              description: URL источника данных
    responses:
      202:
        description: Импорт запущен
        schema:
          type: object
          properties:
            message:
              type: string
            job_id:
              type: string
            status:
              type: string
      400:
        description: Ошибка валидации
    """
    try:
        user_id = get_jwt_identity()
        seller = Seller.query.filter_by(user_id=user_id).first()

        if not seller:
            return jsonify({'error': 'Продавец не найден'}), 404

        data = request.get_json()
        source_url = data.get('source_url')

        if not source_url:
            return jsonify({'error': 'Не указан source_url'}), 400

        # Создание задачи импорта
        import_job = ImportJob(
            seller_id=seller.id,
            source_url=source_url,
            status='processing'
        )

        db.session.add(import_job)
        db.session.commit()

        return jsonify({
            'message': 'Импорт запущен',
            'job_id': import_job.id,
            'status': 'processing'
        }), 202

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/import/status/<job_id>', methods=['GET'])
@jwt_required()
def get_import_status(job_id):
    """
    Получение статуса импорта
    ---
    tags:
      - Import
    summary: Получить статус задачи импорта
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: job_id
        required: true
        type: string
        description: ID задачи импорта
    produces:
      - application/json
    responses:
      200:
        description: Статус импорта
        schema:
          type: object
          properties:
            job_id:
              type: string
            status:
              type: string
            source_url:
              type: string
            created_at:
              type: string
            updated_at:
              type: string
      404:
        description: Задача не найдена
    """
    try:
        user_id = get_jwt_identity()
        seller = Seller.query.filter_by(user_id=user_id).first()

        if not seller:
            return jsonify({'error': 'Продавец не найден'}), 404

        import_job = ImportJob.query.filter_by(id=job_id, seller_id=seller.id).first()

        if not import_job:
            return jsonify({'error': 'Задача импорта не найдена'}), 404

        return jsonify({
            'job_id': import_job.id,
            'status': import_job.status,
            'source_url': import_job.source_url,
            'created_at': import_job.created_at.isoformat(),
            'updated_at': import_job.updated_at.isoformat()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ==================== ЭНДПОИНТЫ ТОВАРОВ ====================

@app.route('/products', methods=['GET'])
@jwt_required()
def get_products():
    """
    Получение списка товаров
    ---
    tags:
      - Products
    summary: Получить все товары продавца
    security:
      - BearerAuth: []
    parameters:
      - in: query
        name: category
        type: string
        description: Фильтр по категории
      - in: query
        name: page
        type: integer
        default: 1
        description: Номер страницы
      - in: query
        name: per_page
        type: integer
        default: 20
        description: Количество товаров на странице
    produces:
      - application/json
    responses:
      200:
        description: Список товаров
        schema:
          type: object
          properties:
            products:
              type: array
              items:
                type: object
            total:
              type: integer
            page:
              type: integer
            per_page:
              type: integer
            total_pages:
              type: integer
    """
    try:
        user_id = get_jwt_identity()
        seller = Seller.query.filter_by(user_id=user_id).first()

        if not seller:
            return jsonify({'error': 'Продавец не найден'}), 404

        # Параметры пагинации
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        category = request.args.get('category', None)

        # Базовый запрос
        query = Product.query.filter_by(seller_id=seller.id)

        # Фильтр по категории
        if category:
            query = query.filter_by(category=category)

        # Пагинация
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        products = pagination.items

        products_data = []
        for product in products:
            products_data.append({
                'id': product.id,
                'title': product.title,
                'brand': product.brand,
                'category': product.category,
                'price': float(product.price) if product.price else 0,
                'description': product.description[:100] + '...' if product.description and len(
                    product.description) > 100 else product.description,
                'created_at': product.created_at.isoformat()
            })

        return jsonify({
            'products': products_data,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'total_pages': pagination.pages
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/products/<product_id>', methods=['GET'])
@jwt_required()
def get_product(product_id):
    """
    Получение информации о товаре
    ---
    tags:
      - Products
    summary: Получить детальную информацию о товаре
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: product_id
        required: true
        type: string
        description: ID товара
    produces:
      - application/json
    responses:
      200:
        description: Информация о товаре
        schema:
          type: object
          properties:
            id:
              type: string
            title:
              type: string
            brand:
              type: string
            category:
              type: string
            price:
              type: number
            description:
              type: string
            created_at:
              type: string
            statistics:
              type: object
              properties:
                average_rating:
                  type: number
      404:
        description: Товар не найден
    """
    try:
        user_id = get_jwt_identity()
        seller = Seller.query.filter_by(user_id=user_id).first()

        if not seller:
            return jsonify({'error': 'Продавец не найден'}), 404

        product = Product.query.filter_by(id=product_id, seller_id=seller.id).first()

        if not product:
            return jsonify({'error': 'Товар не найден'}), 404

        # Получение среднего рейтинга
        avg_rating = db.session.query(func.avg(Review.rating)) \
                         .filter_by(product_id=product_id) \
                         .scalar() or 0

        return jsonify({
            'id': product.id,
            'title': product.title,
            'brand': product.brand,
            'category': product.category,
            'price': float(product.price) if product.price else 0,
            'description': product.description,
            'created_at': product.created_at.isoformat(),
            'statistics': {
                'average_rating': round(float(avg_rating), 2)
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ==================== ЭНДПОИНТЫ ОТЗЫВОВ ====================

@app.route('/products/<product_id>/reviews', methods=['GET'])
@jwt_required()
def get_product_reviews(product_id):
    """
    Получение отзывов о товаре
    ---
    tags:
      - Reviews
    summary: Получить отзывы о товаре
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: product_id
        required: true
        type: string
        description: ID товара
      - in: query
        name: page
        type: integer
        default: 1
      - in: query
        name: per_page
        type: integer
        default: 10
    produces:
      - application/json
    responses:
      200:
        description: Список отзывов
        schema:
          type: object
          properties:
            product_id:
              type: string
            reviews:
              type: array
              items:
                type: object
            statistics:
              type: object
      404:
        description: Товар не найден
    """
    try:
        user_id = get_jwt_identity()
        seller = Seller.query.filter_by(user_id=user_id).first()

        if not seller:
            return jsonify({'error': 'Продавец не найден'}), 404

        # Проверка, что товар принадлежит продавцу
        product = Product.query.filter_by(id=product_id, seller_id=seller.id).first()
        if not product:
            return jsonify({'error': 'Товар не найден'}), 404

        # Параметры пагинации
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        # Получение отзывов
        reviews = Review.query.filter_by(product_id=product_id) \
            .order_by(Review.created_at.desc()) \
            .paginate(page=page, per_page=per_page, error_out=False)

        reviews_data = []
        for review in reviews.items:
            # Получение NLP анализа если есть
            nlp_analysis = ReviewNLP.query.filter_by(review_id=review.id).first()

            review_data = {
                'id': review.id,
                'rating': review.rating,
                'text': review.text,
                'author': review.author,
                'created_at': review.created_at.isoformat()
            }

            if nlp_analysis:
                review_data['nlp_analysis'] = {
                    'sentiment': float(nlp_analysis.sentiment) if nlp_analysis.sentiment else None,
                    'topics': json.loads(nlp_analysis.topics) if nlp_analysis.topics else [],
                    'keywords': json.loads(nlp_analysis.keywords) if nlp_analysis.keywords else []
                }

            reviews_data.append(review_data)

        # Статистика отзывов
        total_reviews = Review.query.filter_by(product_id=product_id).count()
        avg_rating = db.session.query(func.avg(Review.rating)) \
                         .filter_by(product_id=product_id) \
                         .scalar() or 0

        return jsonify({
            'product_id': product_id,
            'reviews': reviews_data,
            'statistics': {
                'total_reviews': total_reviews,
                'average_rating': round(float(avg_rating), 2),
                'current_page': page,
                'total_pages': reviews.pages,
                'per_page': per_page
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/reviews/<review_id>', methods=['GET'])
@jwt_required()
def get_review(review_id):
    """
    Получение детальной информации об отзыве
    ---
    tags:
      - Reviews
    summary: Получить информацию об отзыве
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: review_id
        required: true
        type: string
        description: ID отзыва
    produces:
      - application/json
    responses:
      200:
        description: Информация об отзыве
        schema:
          type: object
      404:
        description: Отзыв не найден
    """
    try:
        user_id = get_jwt_identity()
        seller = Seller.query.filter_by(user_id=user_id).first()

        if not seller:
            return jsonify({'error': 'Продавец не найден'}), 404

        # Получение отзыва
        review = Review.query.filter_by(id=review_id).first()

        if not review:
            return jsonify({'error': 'Отзыв не найден'}), 404

        # Проверка, что товар принадлежит продавцу
        product = Product.query.filter_by(id=review.product_id, seller_id=seller.id).first()
        if not product:
            return jsonify({'error': 'Отзыв не найден'}), 404

        # Получение NLP анализа
        nlp_analysis = ReviewNLP.query.filter_by(review_id=review.id).first()

        response_data = {
            'id': review.id,
            'product_id': review.product_id,
            'product_title': product.title,
            'rating': review.rating,
            'text': review.text,
            'author': review.author,
            'created_at': review.created_at.isoformat()
        }

        if nlp_analysis:
            response_data['nlp_analysis'] = {
                'sentiment': float(nlp_analysis.sentiment) if nlp_analysis.sentiment else None,
                'topics': json.loads(nlp_analysis.topics) if nlp_analysis.topics else [],
                'keywords': json.loads(nlp_analysis.keywords) if nlp_analysis.keywords else [],
                'analyzed_at': nlp_analysis.analyzed_at.isoformat() if nlp_analysis.analyzed_at else None
            }

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ==================== ЭНДПОИНТЫ СЕГМЕНТОВ ====================

@app.route('/segments', methods=['GET'])
@jwt_required()
def get_segments():
    """
    Получение сегментов
    ---
    tags:
      - Segments
    summary: Получить все сегменты продавца
    security:
      - BearerAuth: []
    parameters:
      - in: query
        name: include_products
        type: boolean
        default: false
        description: Включить информацию о товарах в сегменте
    produces:
      - application/json
    responses:
      200:
        description: Список сегментов
        schema:
          type: object
          properties:
            segments:
              type: array
              items:
                type: object
            total:
              type: integer
    """
    try:
        user_id = get_jwt_identity()
        seller = Seller.query.filter_by(user_id=user_id).first()

        if not seller:
            return jsonify({'error': 'Продавец не найден'}), 404

        include_products = request.args.get('include_products', 'false').lower() == 'true'

        segments = Segment.query.filter_by(seller_id=seller.id).all()

        segments_data = []
        for segment in segments:
            segment_data = {
                'id': segment.id,
                'name': segment.name,
                'description': segment.description,
                'created_at': segment.created_at.isoformat()
            }

            if include_products:
                # Получение товаров в сегменте
                product_segments = ProductSegment.query.filter_by(segment_id=segment.id).all()

                products_info = []
                for ps in product_segments:
                    product = Product.query.get(ps.product_id)
                    if product:
                        products_info.append({
                            'product_id': product.id,
                            'title': product.title,
                            'score': float(ps.score) if ps.score else 0
                        })

                segment_data['products'] = products_info
                segment_data['product_count'] = len(products_info)

            segments_data.append(segment_data)

        return jsonify({
            'segments': segments_data,
            'total': len(segments_data)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/segments/<segment_id>', methods=['GET'])
@jwt_required()
def get_segment(segment_id):
    """
    Получение информации о сегменте
    ---
    tags:
      - Segments
    summary: Получить детальную информацию о сегменте
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: segment_id
        required: true
        type: string
        description: ID сегмента
    produces:
      - application/json
    responses:
      200:
        description: Информация о сегменте
        schema:
          type: object
      404:
        description: Сегмент не найден
    """
    try:
        user_id = get_jwt_identity()
        seller = Seller.query.filter_by(user_id=user_id).first()

        if not seller:
            return jsonify({'error': 'Продавец не найден'}), 404

        segment = Segment.query.filter_by(id=segment_id, seller_id=seller.id).first()

        if not segment:
            return jsonify({'error': 'Сегмент не найден'}), 404

        # Получение товаров в сегменте
        product_segments = ProductSegment.query.filter_by(segment_id=segment.id).all()

        products_info = []
        for ps in product_segments:
            product = Product.query.get(ps.product_id)
            if product:
                products_info.append({
                    'product_id': product.id,
                    'title': product.title,
                    'category': product.category,
                    'price': float(product.price) if product.price else 0,
                    'score': float(ps.score) if ps.score else 0
                })

        # Статистика по ценам
        if products_info:
            prices = [p['price'] for p in products_info if p['price']]
            avg_price = sum(prices) / len(prices) if prices else 0
            min_price = min(prices) if prices else 0
            max_price = max(prices) if prices else 0
        else:
            avg_price = min_price = max_price = 0

        return jsonify({
            'id': segment.id,
            'name': segment.name,
            'description': segment.description,
            'created_at': segment.created_at.isoformat(),
            'products': products_info,
            'statistics': {
                'total_products': len(products_info),
                'average_price': round(avg_price, 2),
                'min_price': round(min_price, 2),
                'max_price': round(max_price, 2)
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/products/<product_id>/segments', methods=['GET'])
@jwt_required()
def get_product_segments(product_id):
    """
    Получение сегментов товара
    ---
    tags:
      - Segments
    summary: Получить сегменты, к которым принадлежит товар
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: product_id
        required: true
        type: string
        description: ID товара
    produces:
      - application/json
    responses:
      200:
        description: Список сегментов товара
        schema:
          type: object
          properties:
            product_id:
              type: string
            product_title:
              type: string
            segments:
              type: array
              items:
                type: object
            total_segments:
              type: integer
      404:
        description: Товар не найден
    """
    try:
        user_id = get_jwt_identity()
        seller = Seller.query.filter_by(user_id=user_id).first()

        if not seller:
            return jsonify({'error': 'Продавец не найден'}), 404

        # Проверка, что товар принадлежит продавцу
        product = Product.query.filter_by(id=product_id, seller_id=seller.id).first()
        if not product:
            return jsonify({'error': 'Товар не найден'}), 404

        # Получение сегментов товара
        product_segments = ProductSegment.query.filter_by(product_id=product_id).all()

        segments_info = []
        for ps in product_segments:
            segment = Segment.query.get(ps.segment_id)
            if segment:
                segments_info.append({
                    'segment_id': segment.id,
                    'segment_name': segment.name,
                    'score': float(ps.score) if ps.score else 0,
                    'segment_description': segment.description
                })

        return jsonify({
            'product_id': product_id,
            'product_title': product.title,
            'segments': segments_info,
            'total_segments': len(segments_info)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ==================== ЭНДПОИНТЫ МАГАЗИНА ====================

@app.route('/storefront/generate', methods=['POST'])
@jwt_required()
def generate_storefront():
    """
    Генерация магазина
    ---
    tags:
      - Storefront
    summary: Создать магазин на основе товаров
    security:
      - BearerAuth: []
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: false
        schema:
          type: object
          properties:
            theme:
              type: string
              description: Тема магазина
    responses:
      202:
        description: Магазин создается
        schema:
          type: object
          properties:
            message:
              type: string
            storefront_id:
              type: string
            status:
              type: string
            estimated_completion:
              type: string
      404:
        description: Продавец не найден
    """
    try:
        user_id = get_jwt_identity()
        seller = Seller.query.filter_by(user_id=user_id).first()

        if not seller:
            return jsonify({'error': 'Продавец не найден'}), 404

        data = request.get_json() or {}
        theme = data.get('theme', 'default')

        # Проверка существующего магазина
        existing_storefront = Storefront.query.filter_by(seller_id=seller.id).first()

        if existing_storefront:
            # Обновление существующего магазина
            existing_storefront.status = 'updating'
            existing_storefront.updated_at = datetime.datetime.utcnow()
            storefront = existing_storefront
        else:
            # Создание нового магазина
            storefront = Storefront(
                seller_id=seller.id,
                status='generating'
            )
            db.session.add(storefront)

        db.session.commit()

        # Имитация генерации магазина
        store_url = f"https://storefront-service.example.com/store/{seller.id}"
        storefront.store_url = store_url
        storefront.status = 'completed'
        db.session.commit()

        return jsonify({
            'message': 'Магазин создается',
            'storefront_id': storefront.id,
            'status': storefront.status,
            'estimated_completion': 'Несколько минут'
        }), 202

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/storefront/status', methods=['GET'])
@jwt_required()
def get_storefront_status():
    """
    Получение статуса магазина
    ---
    tags:
      - Storefront
    summary: Получить статус генерации магазина
    security:
      - BearerAuth: []
    produces:
      - application/json
    responses:
      200:
        description: Статус магазина
        schema:
          type: object
          properties:
            storefront_id:
              type: string
            status:
              type: string
            store_url:
              type: string
            created_at:
              type: string
            updated_at:
              type: string
            has_storefront:
              type: boolean
    """
    try:
        user_id = get_jwt_identity()
        seller = Seller.query.filter_by(user_id=user_id).first()

        if not seller:
            return jsonify({'error': 'Продавец не найден'}), 404

        storefront = Storefront.query.filter_by(seller_id=seller.id).first()

        if not storefront:
            return jsonify({
                'message': 'Магазин еще не создан',
                'has_storefront': False
            }), 200

        return jsonify({
            'storefront_id': storefront.id,
            'status': storefront.status,
            'store_url': storefront.store_url,
            'created_at': storefront.created_at.isoformat(),
            'updated_at': storefront.updated_at.isoformat(),
            'has_storefront': True
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/storefront/link', methods=['GET'])
@jwt_required()
def get_storefront_link():
    """
    Получение ссылки на магазин
    ---
    tags:
      - Storefront
    summary: Получить ссылку на созданный магазин
    security:
      - BearerAuth: []
    produces:
      - application/json
    responses:
      200:
        description: Ссылка на магазин
        schema:
          type: object
          properties:
            store_url:
              type: string
            store_name:
              type: string
            status:
              type: string
            last_updated:
              type: string
      404:
        description: Магазин не найден или не готов
    """
    try:
        user_id = get_jwt_identity()
        seller = Seller.query.filter_by(user_id=user_id).first()

        if not seller:
            return jsonify({'error': 'Продавец не найден'}), 404

        storefront = Storefront.query.filter_by(seller_id=seller.id).first()

        if not storefront:
            return jsonify({'error': 'Магазин не создан'}), 404

        if storefront.status != 'completed':
            return jsonify({
                'error': 'Магазин еще не готов',
                'status': storefront.status,
                'estimated_completion': 'Попробуйте позже'
            }), 400

        return jsonify({
            'store_url': storefront.store_url,
            'store_name': seller.store_name,
            'status': storefront.status,
            'last_updated': storefront.updated_at.isoformat()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ==================== СИСТЕМНЫЕ ЭНДПОИНТЫ ====================

@app.route('/health', methods=['GET'])
def health_check():
    """
    Проверка здоровья API
    ---
    tags:
      - System
    summary: Проверка работоспособности API
    produces:
      - application/json
    responses:
      200:
        description: API работает
        schema:
          type: object
          properties:
            status:
              type: string
            timestamp:
              type: string
            database:
              type: string
            version:
              type: string
    """
    try:
        # Проверка подключения к БД
        db.session.execute(text('SELECT 1'))
        db_status = 'connected'
    except:
        db_status = 'disconnected'

    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'database': db_status,
        'version': '1.0.0'
    }), 200


@app.route('/')
def index():
    """Главная страница API"""
    return '''
    <html>
        <head>
            <title>Marketplace API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { max-width: 1000px; margin: 0 auto; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 30px; }
                .card { background: white; border-radius: 10px; padding: 25px; margin: 20px 0; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
                .btn { display: inline-block; padding: 12px 24px; background: #4CAF50; color: white; text-decoration: none; border-radius: 6px; margin: 8px; font-weight: bold; }
                .btn:hover { background: #45a049; }
                .btn-primary { background: #3498db; }
                .btn-primary:hover { background: #2980b9; }
                .endpoint { background: #f8f9fa; padding: 10px; margin: 5px 0; border-left: 4px solid #3498db; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏪 Marketplace API</h1>
                    <p>API для управления интернет-магазином</p>
                    <div style="margin-top: 20px;">
                        <a href="/swagger" class="btn" target="_blank">📚 Swagger UI</a>
                        <a href="/health" class="btn btn-primary">🏥 Health Check</a>
                    </div>
                </div>

                <div class="card">
                    <h2>🔑 Аутентификация</h2>
                    <div class="endpoint">
                        <strong>POST /auth/register</strong> - Регистрация
                    </div>
                    <div class="endpoint">
                        <strong>POST /auth/login</strong> - Вход в систему
                    </div>
                    <div class="endpoint">
                        <strong>GET /seller/profile</strong> - Профиль продавца
                    </div>
                </div>

                <div class="card">
                    <h2>📦 Импорт товаров</h2>
                    <div class="endpoint">
                        <strong>POST /import/start</strong> - Запуск импорта
                    </div>
                    <div class="endpoint">
                        <strong>GET /import/status/{job_id}</strong> - Статус импорта
                    </div>
                </div>

                <div class="card">
                    <h2>🛒 Товары</h2>
                    <div class="endpoint">
                        <strong>GET /products</strong> - Список товаров
                    </div>
                    <div class="endpoint">
                        <strong>GET /products/{id}</strong> - Информация о товаре
                    </div>
                </div>

                <div class="card">
                    <h2>⭐ Отзывы</h2>
                    <div class="endpoint">
                        <strong>GET /products/{id}/reviews</strong> - Отзывы о товаре
                    </div>
                    <div class="endpoint">
                        <strong>GET /reviews/{id}</strong> - Детали отзыва
                    </div>
                </div>

                <div class="card">
                    <h2>🎯 Сегменты</h2>
                    <div class="endpoint">
                        <strong>GET /segments</strong> - Все сегменты
                    </div>
                    <div class="endpoint">
                        <strong>GET /segments/{id}</strong> - Информация о сегменте
                    </div>
                    <div class="endpoint">
                        <strong>GET /products/{id}/segments</strong> - Сегменты товара
                    </div>
                </div>

                <div class="card">
                    <h2>🏪 Магазин</h2>
                    <div class="endpoint">
                        <strong>POST /storefront/generate</strong> - Генерация магазина
                    </div>
                    <div class="endpoint">
                        <strong>GET /storefront/status</strong> - Статус магазина
                    </div>
                    <div class="endpoint">
                        <strong>GET /storefront/link</strong> - Ссылка на магазин
                    </div>
                </div>
            </div>
        </body>
    </html>
    '''


if __name__ == '__main__':
    with app.app_context():
        try:
            # Проверка подключения к БД
            db.session.execute(text('SELECT 1'))
            print("✅ База данных подключена")
        except Exception as e:
            print(f"❌ Ошибка подключения к БД: {e}")
            print("💡 Убедитесь, что MySQL запущен и база данных 'marketplace_db' существует")

        try:
            db.create_all()
            print("✅ Таблицы созданы/проверены")
        except Exception as e:
            print(f"❌ Ошибка создания таблиц: {e}")

    print("=" * 70)
    print("🚀 Marketplace API Server")
    print("=" * 70)
    print("🌐 Главная страница:  http://127.0.0.1:5000")

    if SWAGGER_AVAILABLE:
        print("📚 Swagger UI:       http://127.0.0.1:5000/swagger")
    else:
        print("⚠️  Swagger UI:       НЕ ДОСТУПЕН (установите flasgger)")

    print("🏥 Health Check:     http://127.0.0.1:5000/health")
    print("=" * 70)
    print("🎯 Основные эндпоинты:")
    print("  POST /auth/register       - Регистрация")
    print("  GET /products             - Товары")
    print("  POST /import/start        - Импорт")
    print("  POST /storefront/generate - Создание магазина")
    print("=" * 70)

    app.run(debug=True, host='0.0.0.0', port=5000)