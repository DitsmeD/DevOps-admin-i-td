"""
🚀 DevOps Панель с модулем регистрации
Запуск: python devops_app.py
Открыть: http://localhost:5000
Логин: admin / admin123
"""

import os
import random
import re
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, flash, jsonify, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "devops-secret-key-2024")
app.config['TEMPLATES_AUTO_RELOAD'] = True

def get_db_connection():
    """Создание соединения с базой данных MySQL"""
    try:
        connection = pymysql.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "theatre"),
            port=int(os.getenv("DB_PORT", "3306")),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        return None

def init_database():
    """Инициализация базы данных - создание таблиц если их нет"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                    login VARCHAR(64) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    full_name VARCHAR(200) NOT NULL,
                    phone VARCHAR(20) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    role_id INT UNSIGNED DEFAULT 1,
                    is_active TINYINT(1) DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_users_email (email)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auth_log (
                    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT UNSIGNED DEFAULT NULL,
                    attempted_login VARCHAR(64) NOT NULL,
                    ip VARCHAR(45) DEFAULT NULL,
                    user_agent VARCHAR(255) DEFAULT NULL,
                    is_success TINYINT(1) NOT NULL,
                    reason VARCHAR(255) DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
                    INDEX idx_auth_log_login (attempted_login),
                    INDEX idx_auth_log_created (created_at),
                    INDEX idx_auth_log_user (user_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS roles (
                    id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(50) NOT NULL UNIQUE,
                    description VARCHAR(200)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            

            cursor.execute("INSERT IGNORE INTO roles (id, name, description) VALUES (1, 'user', 'Обычный пользователь')")
            cursor.execute("INSERT IGNORE INTO roles (id, name, description) VALUES (2, 'admin', 'Администратор системы')")
            

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS email_queue (
                    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                    recipient VARCHAR(255) NOT NULL,
                    subject VARCHAR(255) NOT NULL,
                    body_text TEXT NOT NULL,
                    is_sent TINYINT(1) DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sent_at TIMESTAMP NULL DEFAULT NULL,
                    INDEX idx_email_queue_recipient (recipient),
                    INDEX idx_email_queue_sent (is_sent)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS servers (
                    id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    ip_address VARCHAR(45) NOT NULL,
                    description TEXT,
                    status VARCHAR(20) DEFAULT 'offline',
                    last_check TIMESTAMP NULL DEFAULT NULL,
                    created_by BIGINT UNSIGNED DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            cursor.execute("SELECT id FROM users WHERE login = 'admin'")
            admin_exists = cursor.fetchone()
            
            if not admin_exists:
                password_hash = generate_password_hash('admin123')
                cursor.execute("""
                    INSERT INTO users (login, password_hash, full_name, phone, email, role_id, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, ('admin', password_hash, 'Администратор Системы', '8(999)123-45-67', 'admin@example.com', 2, 1))
            
            cursor.execute("SELECT COUNT(*) as count FROM servers")
            servers_count = cursor.fetchone()['count']
            
            if servers_count == 0:
                test_servers = [
                    ('Основной сервер', '192.168.1.100', 'Основной сервер для веб-приложений', 'online'),
                    ('Резервный сервер', '192.168.1.101', 'Резервная копия основного сервера', 'offline'),
                    ('База данных', '192.168.1.102', 'Сервер баз данных PostgreSQL', 'online'),
                    ('Файловое хранилище', '192.168.1.103', 'NAS хранилище для резервных копий', 'warning'),
                ]
                
                for server in test_servers:
                    cursor.execute("""
                        INSERT INTO servers (name, ip_address, description, status)
                        VALUES (%s, %s, %s, %s)
                    """, server)
            
            conn.commit()
            print("✅ База данных инициализирована успешно!")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка при инициализации БД: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def write_auth_log(user_id, attempted_login, is_success, reason=None):
    """Запись в журнал авторизации"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            ip = request.remote_addr if request else None
            user_agent = request.user_agent.string[:255] if request and request.user_agent else None
            
            cursor.execute("""
                INSERT INTO auth_log (user_id, attempted_login, ip, user_agent, is_success, reason)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, attempted_login, ip, user_agent, 1 if is_success else 0, reason))
            
            conn.commit()
            return True
    except Exception as e:
        print(f"❌ Ошибка записи в auth_log: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def add_to_email_queue(recipient, subject, body_text):
    """Добавление email в очередь"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO email_queue (recipient, subject, body_text)
                VALUES (%s, %s, %s)
            """, (recipient, subject, body_text))
            
            conn.commit()
            return True
    except Exception as e:
        print(f"❌ Ошибка добавления в email_queue: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

BASE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        /* ОСНОВНЫЕ СТИЛИ */
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        /* КОНТЕЙНЕР */
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }
        
        /* НАВИГАЦИЯ */
        .navbar {
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 15px 0;
            position: sticky;
            top: 0;
            z-index: 1000;
            backdrop-filter: blur(10px);
        }
        
        .navbar .container {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            color: white;
            font-size: 24px;
            font-weight: bold;
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .nav-links {
            display: flex;
            gap: 20px;
            align-items: center;
        }
        
        .nav-links a {
            color: white;
            text-decoration: none;
            padding: 8px 15px;
            border-radius: 4px;
            transition: all 0.3s;
        }
        
        .nav-links a:hover {
            background: rgba(255, 255, 255, 0.1);
            transform: translateY(-2px);
        }
        
        /* СООБЩЕНИЯ */
        .alert {
            padding: 15px;
            margin: 20px 0;
            border-radius: 8px;
            font-weight: 500;
            animation: slideIn 0.3s ease;
        }
        
        @keyframes slideIn {
            from { transform: translateY(-20px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .alert-info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        
        /* КАРТОЧКИ */
        .card {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin: 20px 0;
            transition: transform 0.3s, box-shadow 0.3s;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.15);
        }
        
        /* ФОРМЫ */
        .auth-container {
            max-width: 450px;
            margin: 60px auto;
        }
        
        .auth-card {
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: #495057;
        }
        
        .form-group input {
            width: 100%;
            padding: 14px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 16px;
            transition: border 0.3s;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        /* КНОПКИ */
        .btn {
            display: inline-block;
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 500;
            transition: all 0.3s;
            text-align: center;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        
        .btn-success {
            background: linear-gradient(135deg, #28a745 0%, #218838 100%);
        }
        
        /* ОТЗЫВЧИВОСТЬ */
        @media (max-width: 768px) {
            .navbar .container {
                flex-direction: column;
                gap: 15px;
            }
            
            .nav-links {
                flex-wrap: wrap;
                justify-content: center;
            }
            
            .auth-container {
                margin: 20px auto;
                padding: 0 15px;
            }
            
            .auth-card {
                padding: 25px;
            }
        }
        
        /* ОШИБКИ В ФОРМЕ */
        .error-list {
            color: #dc3545;
            font-size: 14px;
            margin-top: 5px;
            padding-left: 15px;
        }
        
        .error-list li {
            margin: 3px 0;
        }
        
        .field-error {
            border-color: #dc3545 !important;
            background: #fff5f5;
        }
    </style>
</head>
<body>
    <!-- НАВИГАЦИЯ -->
    <nav class="navbar">
        <div class="container">
            <a href="/" class="logo">🚀 DevOps Панель</a>
            <div class="nav-links">
                {% if session.user %}
                    <a href="/dashboard">📊 Дашборд</a>
                    <a href="/servers">🖥️ Серверы</a>
                    {% if session.role == 'admin' %}
                        <a href="/admin">👑 Админ</a>
                    {% endif %}
                    <a href="/profile">👤 {{ session.user }}</a>
                    <a href="/logout" style="background: #dc3545;">🚪 Выйти</a>
                {% else %}
                    <a href="/login">🔐 Вход</a>
                    <a href="/register">📝 Регистрация</a>
                {% endif %}
            </div>
        </div>
    </nav>

    <div class="container">
        {% if messages %}
            {% for category, message in messages %}
                <div class="alert alert-{{ category }}">{{ message }}</div>
            {% endfor %}
        {% endif %}
        
        {% block content %}{% endblock %}
    </div>
</body>
</html>
'''

LOGIN_TEMPLATE = '''
{% extends "base" %}
{% block content %}
<div class="auth-container">
    <div class="auth-card">
        <h2 style="text-align: center; margin-bottom: 30px; color: #333;">🔐 Вход в систему</h2>
        <form method="POST" action="/login">
            <div class="form-group">
                <label>👤 Логин</label>
                <input type="text" name="login" placeholder="Введите логин" required>
            </div>
            <div class="form-group">
                <label>🔒 Пароль</label>
                <input type="password" name="password" placeholder="Введите пароль" required>
            </div>
            <button type="submit" class="btn" style="width: 100%; margin-top: 10px;">
                📥 Войти в систему
            </button>
        </form>
        <p style="text-align: center; margin-top: 25px; color: #666;">
            Нет аккаунта? <a href="/register" style="color: #667eea;">Зарегистрируйтесь</a><br>
            <small style="color: #888;">Тестовый аккаунт: <b>admin</b> / <b>admin123</b></small>
        </p>
    </div>
</div>
{% endblock %}
'''

REGISTER_TEMPLATE = '''
{% extends "base" %}
{% block content %}
<div class="auth-container">
    <div class="auth-card">
        <h2 style="text-align: center; margin-bottom: 30px; color: #333;">📝 Регистрация</h2>
        
        {% if errors %}
        <div class="alert alert-error" style="margin-bottom: 20px;">
            <strong>Обнаружены ошибки:</strong>
            <ul class="error-list">
                {% for error in errors %}
                <li>{{ error }}</li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}
        
        <form method="POST" action="/register">
            <div class="form-group">
                <label>👤 Логин *</label>
                <input type="text" name="login" 
                       value="{{ form_data.login if form_data }}" 
                       placeholder="Только латиница и цифры, ≥6 символов" 
                       pattern="^[A-Za-z0-9]{6,}$"
                       title="Только латиница и цифры, не менее 6 символов"
                       required
                       {% if errors and 'login' in errors|map(attribute='field')|list %}class="field-error"{% endif %}>
                <small style="color: #666; display: block; margin-top: 5px;">Только латинские буквы и цифры, минимум 6 символов</small>
            </div>
            
            <div class="form-group">
                <label>🔒 Пароль *</label>
                <input type="password" name="password" 
                       placeholder="Минимум 8 символов" 
                       minlength="8"
                       required
                       {% if errors and 'password' in errors|map(attribute='field')|list %}class="field-error"{% endif %}>
                <small style="color: #666; display: block; margin-top: 5px;">Минимум 8 символов</small>
            </div>
            
            <div class="form-group">
                <label>👤 ФИО *</label>
                <input type="text" name="full_name" 
                       value="{{ form_data.full_name if form_data }}" 
                       placeholder="Иванов Иван Иванович" 
                       maxlength="200"
                       required
                       {% if errors and 'full_name' in errors|map(attribute='field')|list %}class="field-error"{% endif %}>
            </div>
            
            <div class="form-group">
                <label>📱 Телефон *</label>
                <input type="text" name="phone" 
                       value="{{ form_data.phone if form_data }}" 
                       placeholder="8(999)123-45-67" 
                       pattern="^8\([0-9]{3}\)[0-9]{3}-[0-9]{2}-[0-9]{2}$"
                       title="Формат: 8(XXX)XXX-XX-XX"
                       required
                       {% if errors and 'phone' in errors|map(attribute='field')|list %}class="field-error"{% endif %}>
                <small style="color: #666; display: block; margin-top: 5px;">Формат: 8(XXX)XXX-XX-XX</small>
            </div>
            
            <div class="form-group">
                <label>📧 E-mail *</label>
                <input type="email" name="email" 
                       value="{{ form_data.email if form_data }}" 
                       placeholder="example@mail.ru" 
                       maxlength="255"
                       required
                       {% if errors and 'email' in errors|map(attribute='field')|list %}class="field-error"{% endif %}>
            </div>
            
            <button type="submit" class="btn btn-success" style="width: 100%; margin-top: 10px;">
                📝 Зарегистрироваться
            </button>
        </form>
        
        <p style="text-align: center; margin-top: 25px; color: #666;">
            Уже есть аккаунт? <a href="/login" style="color: #667eea;">Войдите</a>
        </p>
    </div>
</div>
{% endblock %}
'''

DASHBOARD_TEMPLATE = '''
{% extends "base" %}
{% block content %}
<!-- ЗАГОЛОВОК -->
<div class="card">
    <h1>📊 Панель управления</h1>
    <p style="color: #666; margin-top: 10px; font-size: 18px;">
        Добро пожаловать, <strong>{{ session.user }}</strong>! 👋
    </p>
</div>


<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 30px 0;">
    <div class="card">
        <div style="font-size: 14px; color: #666; margin-bottom: 10px;">🖥️ Всего серверов</div>
        <h3 style="font-size: 32px;">{{ stats.total_servers }}</h3>
    </div>
    <div class="card">
        <div style="font-size: 14px; color: #666; margin-bottom: 10px;">✅ Серверов онлайн</div>
        <h3 style="font-size: 32px; color: #28a745;">{{ stats.online_servers }}</h3>
    </div>
    <div class="card">
        <div style="font-size: 14px; color: #666; margin-bottom: 10px;">👥 Пользователей</div>
        <h3 style="font-size: 32px;">{{ stats.total_users }}</h3>
    </div>
</div>


<div class="card">
    <h2>🖥️ Последние серверы</h2>
    <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
        <thead>
            <tr>
                <th style="padding: 12px; text-align: left; background: #f8f9fa;">Название</th>
                <th style="padding: 12px; text-align: left; background: #f8f9fa;">IP адрес</th>
                <th style="padding: 12px; text-align: left; background: #f8f9fa;">Статус</th>
                <th style="padding: 12px; text-align: left; background: #f8f9fa;">Действия</th>
            </tr>
        </thead>
        <tbody>
            {% for server in servers %}
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 12px;"><strong>{{ server.name }}</strong></td>
                <td style="padding: 12px;"><code>{{ server.ip_address }}</code></td>
                <td style="padding: 12px;">
                    {% if server.status == 'online' %}
                        <span style="background: #d4edda; color: #155724; padding: 4px 8px; border-radius: 12px; font-size: 14px;">
                            ✅ Онлайн
                        </span>
                    {% elif server.status == 'warning' %}
                        <span style="background: #fff3cd; color: #856404; padding: 4px 8px; border-radius: 12px; font-size: 14px;">
                            ⚠️ Предупреждение
                        </span>
                    {% else %}
                        <span style="background: #f8d7da; color: #721c24; padding: 4px 8px; border-radius: 12px; font-size: 14px;">
                            ❌ Оффлайн
                        </span>
                    {% endif %}
                </td>
                <td style="padding: 12px;">
                    <button onclick="checkServer({{ server.id }})" style="
                        background: #17a2b8;
                        color: white;
                        border: none;
                        padding: 6px 12px;
                        border-radius: 4px;
                        cursor: pointer;
                    ">
                        🔄 Проверить
                    </button>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}

<script>
function checkServer(serverId) {
    fetch('/api/check/' + serverId)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('✅ Статус сервера обновлен: ' + data.status);
                location.reload();
            }
        });
}
</script>
'''

PROFILE_TEMPLATE = '''
{% extends "base" %}
{% block content %}
<div class="card">
    <h1>👤 Профиль пользователя</h1>
    
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 20px;">
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
            <div style="color: #666; font-size: 14px;">👤 Логин</div>
            <div style="font-size: 24px; margin-top: 5px;"><strong>{{ user.login }}</strong></div>
        </div>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
            <div style="color: #666; font-size: 14px;">📧 Email</div>
            <div style="font-size: 20px; margin-top: 5px;">{{ user.email }}</div>
        </div>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
            <div style="color: #666; font-size: 14px;">👤 ФИО</div>
            <div style="font-size: 20px; margin-top: 5px;">{{ user.full_name }}</div>
        </div>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
            <div style="color: #666; font-size: 14px;">📱 Телефон</div>
            <div style="font-size: 20px; margin-top: 5px;">{{ user.phone }}</div>
        </div>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
            <div style="color: #666; font-size: 14px;">👑 Роль</div>
            <div style="font-size: 20px; margin-top: 5px;">
                <span style="display: inline-block; padding: 8px 16px; background: {{ 'linear-gradient(135deg, #dc3545 0%, #c82333 100%)' if user.role_id == 2 else 'linear-gradient(135deg, #17a2b8 0%, #138496 100%)' }}; color: white; border-radius: 12px; font-weight: bold;">
                    {{ '👑 Администратор' if user.role_id == 2 else '👤 Пользователь' }}
                </span>
            </div>
        </div>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
            <div style="color: #666; font-size: 14px;">📅 Дата регистрации</div>
            <div style="font-size: 20px; margin-top: 5px;">{{ user.created_at }}</div>
        </div>
    </div>
</div>
{% endblock %}
'''

INDEX_TEMPLATE = '''
{% extends "base" %}
{% block content %}
<div style="text-align: center; padding: 100px 0; color: white;">
    <h1 style="font-size: 48px; margin-bottom: 20px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">🚀 DevOps Панель Управления</h1>
    <p style="font-size: 20px; max-width: 600px; margin: 0 auto 40px auto; opacity: 0.9;">
        Профессиональная система для мониторинга и управления серверами
    </p>
    
    {% if not session.user %}
    <div style="display: flex; gap: 20px; justify-content: center; margin-top: 30px;">
        <a href="/login" class="btn" style="padding: 15px 40px; font-size: 18px;">
            🔐 Войти в систему
        </a>
        <a href="/register" class="btn btn-success" style="padding: 15px 40px; font-size: 18px;">
            📝 Зарегистрироваться
        </a>
    </div>
    {% else %}
    <div style="margin-top: 30px;">
        <a href="/dashboard" class="btn" style="padding: 15px 40px; font-size: 18px;">
            📊 Перейти в панель
        </a>
    </div>
    {% endif %}
</div>
{% endblock %}
'''

def render_template(template, **context):
    """Рендерит шаблон из строки с базовым шаблоном"""
    from flask import render_template_string
    full_template = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', template)
    return render_template_string(full_template, **context)

def get_flashed_messages():
    """Получает сообщения из сессии"""
    return session.pop('_flashes', [])

def flash(message, category='info'):
    """Добавляет flash-сообщение"""
    if '_flashes' not in session:
        session['_flashes'] = []
    session['_flashes'].append((category, message))
    session.modified = True

@app.route('/')
def index():
    messages = get_flashed_messages()
    return render_template(
        INDEX_TEMPLATE,
        title='DevOps Панель',
        messages=messages
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user'):
        return redirect('/dashboard')
    
    messages = get_flashed_messages()
    
    if request.method == 'POST':
        login_name = request.form.get('login')
        password = request.form.get('password')
        
        conn = get_db_connection()
        if not conn:
            flash('❌ Ошибка подключения к базе данных', 'error')
            return render_template(LOGIN_TEMPLATE, title='Вход в систему', messages=get_flashed_messages())
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE login = %s", (login_name,))
                user = cursor.fetchone()
                
                if user and check_password_hash(user['password_hash'], password):
                    if user['is_active']:
                        session['user'] = user['login']
                        session['user_id'] = user['id']
                        session['role'] = 'admin' if user['role_id'] == 2 else 'user'
                        
                        write_auth_log(user['id'], login_name, True, 'login')
                        
                        flash('✅ Вход выполнен успешно!', 'success')
                        return redirect('/dashboard')
                    else:
                        write_auth_log(user['id'] if user else None, login_name, False, 'user_inactive')
                        flash('❌ Аккаунт заблокирован', 'error')
                else:
                    write_auth_log(user['id'] if user else None, login_name, False, 'invalid_credentials')
                    flash('❌ Неверный логин или пароль', 'error')
        
        except Exception as e:
            flash(f'❌ Ошибка при входе: {str(e)}', 'error')
        finally:
            conn.close()
    
    return render_template(LOGIN_TEMPLATE, title='Вход в систему', messages=messages)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user'):
        return redirect('/dashboard')
    
    messages = get_flashed_messages()
    errors = []
    form_data = {}
    
    if request.method == 'POST':

        login_name = request.form.get('login', '').strip()
        password = request.form.get('password', '').strip()
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip().lower()
        
        form_data = {
            'login': login_name,
            'full_name': full_name,
            'phone': phone,
            'email': email
        }

        if not login_name:
            errors.append({'field': 'login', 'message': 'Логин обязателен'})
        elif len(login_name) < 6:
            errors.append({'field': 'login', 'message': 'Логин должен быть не менее 6 символов'})
        elif len(login_name) > 64:
            errors.append({'field': 'login', 'message': 'Логин должен быть не более 64 символов'})
        elif not re.match(r'^[A-Za-z0-9]{6,}$', login_name):
            errors.append({'field': 'login', 'message': 'Логин должен содержать только латинские буквы и цифры'})

        if not password:
            errors.append({'field': 'password', 'message': 'Пароль обязателен'})
        elif len(password) < 8:
            errors.append({'field': 'password', 'message': 'Пароль должен быть не менее 8 символов'})
        elif len(password) > 128:
            errors.append({'field': 'password', 'message': 'Пароль должен быть не более 128 символов'})
        
        if not full_name:
            errors.append({'field': 'full_name', 'message': 'ФИО обязательно'})
        elif len(full_name) > 200:
            errors.append({'field': 'full_name', 'message': 'ФИО должно быть не более 200 символов'})
 
        if not phone:
            errors.append({'field': 'phone', 'message': 'Телефон обязателен'})
        elif not re.match(r'^8\([0-9]{3}\)[0-9]{3}-[0-9]{2}-[0-9]{2}$', phone):
            errors.append({'field': 'phone', 'message': 'Формат телефона: 8(XXX)XXX-XX-XX'})
                if not email:
            errors.append({'field': 'email', 'message': 'Email обязателен'})
        elif len(email) > 255:
            errors.append({'field': 'email', 'message': 'Email должен быть не более 255 символов'})
        elif not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            errors.append({'field': 'email', 'message': 'Введите корректный email адрес'})

        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cursor:

                    cursor.execute("SELECT id FROM users WHERE login = %s", (login_name,))
                    if cursor.fetchone():
                        errors.append({'field': 'login', 'message': 'Этот логин уже занят'})
                    

                    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                    if cursor.fetchone():
                        errors.append({'field': 'email', 'message': 'Этот email уже зарегистрирован'})
                    

                    cursor.execute("SELECT id FROM users WHERE phone = %s", (phone,))
                    if cursor.fetchone():
                        errors.append({'field': 'phone', 'message': 'Этот телефон уже зарегистрирован'})
            except Exception as e:
                errors.append({'message': f'Ошибка проверки данных: {str(e)}'})
            finally:
                conn.close()
        

        if errors:
            return render_template(
                REGISTER_TEMPLATE,
                title='Регистрация',
                messages=messages,
                errors=errors,
                form_data=form_data
            )
        

        conn = get_db_connection()
        if not conn:
            flash('❌ Ошибка подключения к базе данных', 'error')
            return render_template(
                REGISTER_TEMPLATE,
                title='Регистрация',
                messages=get_flashed_messages(),
                errors=errors,
                form_data=form_data
            )
        
        try:
            with conn.cursor() as cursor:

                password_hash = generate_password_hash(password)
                

                cursor.execute("""
                    INSERT INTO users (login, password_hash, full_name, phone, email, role_id, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (login_name, password_hash, full_name, phone, email, 1, 1))
                
                user_id = cursor.lastrowid
                

                write_auth_log(user_id, login_name, True, 'registration')
                

                email_subject = "🎉 Добро пожаловать в DevOps Панель!"
                email_body = f"""Здравствуйте, {full_name}!

Благодарим Вас за регистрацию в DevOps Панели управления.

Ваши данные для входа:
👤 Логин: {login_name}
📧 Email: {email}
📱 Телефон: {phone}

Для начала работы перейдите по ссылке: {request.host_url}login

С наилучшими пожеланиями,
Команда DevOps Панели
"""
                add_to_email_queue(email, email_subject, email_body)
                
                conn.commit()
                
                flash(f'✅ Регистрация успешно завершена, {full_name}! Проверьте вашу почту.', 'success')
                return redirect('/login')
                
        except Exception as e:
            conn.rollback()
            error_msg = str(e)
            if "Duplicate entry" in error_msg:
                if "login" in error_msg:
                    errors.append({'field': 'login', 'message': 'Этот логин уже занят'})
                elif "email" in error_msg:
                    errors.append({'field': 'email', 'message': 'Этот email уже зарегистрирован'})
                elif "phone" in error_msg:
                    errors.append({'field': 'phone', 'message': 'Этот телефон уже зарегистрирован'})
            else:
                flash(f'❌ Ошибка при регистрации: {error_msg}', 'error')
        finally:
            conn.close()
    return render_template(
        REGISTER_TEMPLATE,
        title='Регистрация',
        messages=messages,
        errors=errors,
        form_data=form_data
    )

@app.route('/dashboard')
def dashboard():
    if not session.get('user'):
        return redirect('/login')
    
    messages = get_flashed_messages()
    conn = get_db_connection()
    
    if not conn:
        flash('❌ Ошибка подключения к базе данных', 'error')
        return render_template(
            DASHBOARD_TEMPLATE,
            title='Панель управления',
            messages=messages,
            stats={'total_servers': 0, 'online_servers': 0, 'total_users': 0},
            servers=[]
        )
    
    try:
        with conn.cursor() as cursor:

            cursor.execute("SELECT COUNT(*) as count FROM servers")
            total_servers = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM servers WHERE status = 'online'")
            online_servers = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM users")
            total_users = cursor.fetchone()['count']
            

            cursor.execute("SELECT * FROM servers ORDER BY created_at DESC LIMIT 5")
            servers = cursor.fetchall()
            
            stats = {
                'total_servers': total_servers,
                'online_servers': online_servers,
                'total_users': total_users
            }
            
            return render_template(
                DASHBOARD_TEMPLATE,
                title='Панель управления',
                messages=messages,
                stats=stats,
                servers=servers
            )
            
    except Exception as e:
        flash(f'❌ Ошибка загрузки данных: {str(e)}', 'error')
        return render_template(
            DASHBOARD_TEMPLATE,
            title='Панель управления',
            messages=messages,
            stats={'total_servers': 0, 'online_servers': 0, 'total_users': 0},
            servers=[]
        )
    finally:
        conn.close()

@app.route('/profile')
def profile():
    if not session.get('user'):
        return redirect('/login')
    
    messages = get_flashed_messages()
    conn = get_db_connection()
    
    if not conn:
        flash('❌ Ошибка подключения к базе данных', 'error')
        return redirect('/dashboard')
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE login = %s", (session['user'],))
            user = cursor.fetchone()
            
            if not user:
                flash('❌ Пользователь не найден', 'error')
                return redirect('/logout')
            
            return render_template(
                PROFILE_TEMPLATE,
                title='Профиль',
                messages=messages,
                user=user
            )
            
    except Exception as e:
        flash(f'❌ Ошибка загрузки профиля: {str(e)}', 'error')
        return redirect('/dashboard')
    finally:
        conn.close()

@app.route('/logout')
def logout():
    if session.get('user'):

        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT id FROM users WHERE login = %s", (session['user'],))
                    user = cursor.fetchone()
                    if user:
                        write_auth_log(user['id'], session['user'], True, 'logout')
            except Exception as e:
                print(f"Ошибка при логировании выхода: {e}")
            finally:
                conn.close()

        session.clear()
        flash('✅ Вы успешно вышли из системы', 'info')
    
    return redirect('/')

@app.route('/api/check/<int:server_id>')
def check_server(server_id):
    if not session.get('user'):
        return jsonify({'success': False, 'error': 'Не авторизован'})
    

    statuses = ['online', 'offline', 'warning']
    new_status = random.choice(statuses)
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Ошибка БД'})
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE servers 
                SET status = %s, last_check = NOW() 
                WHERE id = %s
            """, (new_status, server_id))
            conn.commit()
            
            return jsonify({'success': True, 'status': new_status})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()


if __name__ == '__main__':

    if init_database():
        print("🚀 Запуск DevOps Панели...")
        print("🌐 Откройте в браузере: http://localhost:5000")
        print("👤 Тестовый аккаунт: admin / admin123")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("❌ Не удалось инициализировать базу данных")


SALES_TEMPLATE = '''
{% extends "base" %}
{% block content %}
<style>
    /* Дополнительные стили для страницы учёта продаж */
    .filters-card {
        margin-bottom: 30px;
    }
    
    .filter-row {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 20px;
        margin-bottom: 20px;
    }
    
    .filter-group {
        margin-bottom: 15px;
    }
    
    .filter-group label {
        display: block;
        margin-bottom: 8px;
        font-weight: 500;
        color: #495057;
    }
    
    .filter-group select,
    .filter-group input {
        width: 100%;
        padding: 12px;
        border: 2px solid #e9ecef;
        border-radius: 8px;
        font-size: 16px;
        transition: border 0.3s;
    }
    
    .filter-group select:focus,
    .filter-group input:focus {
        outline: none;
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    .filter-actions {
        display: flex;
        gap: 10px;
        margin-top: 20px;
    }
    
    .statistics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 20px;
        margin: 20px 0;
    }
    
    .stat-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.05);
        text-align: center;
    }
    
    .stat-card h3 {
        font-size: 24px;
        color: #333;
        margin-bottom: 10px;
    }
    
    .stat-card p {
        color: #666;
        font-size: 14px;
    }
    
    .sales-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 20px;
        background: white;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 5px 15px rgba(0,0,0,0.05);
    }
    
    .sales-table th {
        background: #f8f9fa;
        padding: 15px;
        text-align: left;
        font-weight: 600;
        color: #495057;
        border-bottom: 2px solid #e9ecef;
    }
    
    .sales-table td {
        padding: 15px;
        border-bottom: 1px solid #e9ecef;
    }
    
    .sales-table tr:hover {
        background: #f8f9fa;
    }
    
    .status-badge {
        padding: 5px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 500;
    }
    
    .status-paid {
        background: #d4edda;
        color: #155724;
    }
    
    .status-pending {
        background: #fff3cd;
        color: #856404;
    }
    
    .status-cancelled {
        background: #f8d7da;
        color: #721c24;
    }
    
    .export-buttons {
        margin-top: 20px;
        display: flex;
        gap: 10px;
        justify-content: flex-end;
    }
</style>

<div class="card">
    <h1>📊 Учёт продаж и отчётность</h1>
    <p style="color: #666; margin-top: 10px;">
        Фильтры применяются на стороне сервера при отправке формы.
    </p>
</div>

<!-- ФИЛЬТРЫ -->
<div class="card filters-card">
    <h2>🔍 Фильтр данных</h2>
    
    <form method="GET" action="/sales">
        <div class="filter-row">
            <div class="filter-group">
                <label>📅 Период с</label>
                <input type="date" name="date_from" 
                       value="{{ filters.date_from if filters.date_from else '' }}">
            </div>
            
            <div class="filter-group">
                <label>📅 Период по</label>
                <input type="date" name="date_to" 
                       value="{{ filters.date_to if filters.date_to else '' }}">
            </div>
            
            <div class="filter-group">
                <label>🎭 Спектакль</label>
                <select name="performance">
                    <option value="">Все спектакли</option>
                    {% for perf in performances %}
                    <option value="{{ perf.id }}" 
                            {% if filters.performance == perf.id|string %}selected{% endif %}>
                        {{ perf.name }}
                    </option>
                    {% endfor %}
                </select>
            </div>
        </div>
        
        <div class="filter-actions">
            <button type="submit" class="btn" style="padding: 10px 30px;">
                🔍 Применить фильтры
            </button>
            <a href="/sales" class="btn" style="background: #6c757d; padding: 10px 30px;">
                🗑️ Сбросить фильтры
            </a>
        </div>
    </form>
</div>

<!-- СТАТИСТИКА -->
{% if statistics %}
<div class="statistics-grid">
    <div class="stat-card">
        <h3>{{ statistics.total_sales }} ₽</h3>
        <p>Общая сумма продаж</p>
    </div>
    
    <div class="stat-card">
        <h3>{{ statistics.total_tickets }}</h3>
        <p>Количество билетов</p>
    </div>
    
    <div class="stat-card">
        <h3>{{ statistics.avg_ticket_price }} ₽</h3>
        <p>Средняя цена билета</p>
    </div>
    
    <div class="stat-card">
        <h3>{{ statistics.sales_count }}</h3>
        <p>Количество продаж</p>
    </div>
</div>
{% endif %}

<!-- ТАБЛИЦА ПРОДАЖ -->
<div class="card">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <h2>📈 История продаж</h2>
        
        {% if sales_data %}
        <div class="export-buttons">
            <button onclick="exportToExcel()" class="btn" style="background: #28a745;">
                📊 Excel
            </button>
            <button onclick="printReport()" class="btn" style="background: #17a2b8;">
                🖨️ Печать
            </button>
        </div>
        {% endif %}
    </div>
    
    {% if sales_data %}
    <table class="sales-table">
        <thead>
            <tr>
                <th>ID</th>
                <th>Дата</th>
                <th>Спектакль</th>
                <th>Билетов</th>
                <th>Сумма</th>
                <th>Покупатель</th>
                <th>Статус</th>
                <th>Метод оплаты</th>
            </tr>
        </thead>
        <tbody>
            {% for sale in sales_data %}
            <tr>
                <td><strong>#{{ sale.id }}</strong></td>
                <td>{{ sale.sale_date }}</td>
                <td>{{ sale.performance_name }}</td>
                <td>{{ sale.tickets_count }}</td>
                <td><strong>{{ sale.total_amount }} ₽</strong></td>
                <td>{{ sale.customer_name }}</td>
                <td>
                    {% if sale.status == 'paid' %}
                        <span class="status-badge status-paid">✅ Оплачено</span>
                    {% elif sale.status == 'pending' %}
                        <span class="status-badge status-pending">⏳ Ожидание</span>
                    {% else %}
                        <span class="status-badge status-cancelled">❌ Отмена</span>
                    {% endif %}
                </td>
                <td>{{ sale.payment_method }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    
    {% if total_pages > 1 %}
    <div style="display: flex; justify-content: center; margin-top: 30px; gap: 10px;">
        {% if current_page > 1 %}
        <a href="/sales?page={{ current_page-1 }}{% if filters.date_from %}&date_from={{ filters.date_from }}{% endif %}{% if filters.date_to %}&date_to={{ filters.date_to }}{% endif %}{% if filters.performance %}&performance={{ filters.performance }}{% endif %}" 
           class="btn" style="padding: 8px 16px;">← Назад</a>
        {% endif %}
        
        <span style="display: flex; align-items: center; padding: 0 15px;">
            Страница {{ current_page }} из {{ total_pages }}
        </span>
        
        {% if current_page < total_pages %}
        <a href="/sales?page={{ current_page+1 }}{% if filters.date_from %}&date_from={{ filters.date_from }}{% endif %}{% if filters.date_to %}&date_to={{ filters.date_to }}{% endif %}{% if filters.performance %}&performance={{ filters.performance }}{% endif %}" 
           class="btn" style="padding: 8px 16px;">Вперед →</a>
        {% endif %}
    </div>
    {% endif %}
    
    {% else %}
    <div style="text-align: center; padding: 50px; color: #666;">
        <p style="font-size: 18px;">📭 Данные не найдены</p>
        <p>Измените параметры фильтров или попробуйте другой период</p>
    </div>
    {% endif %}
</div>

<script>
function exportToExcel() {
    alert('Функция экспорта в Excel будет реализована в следующем обновлении!');
    // В реальном приложении здесь будет запрос на сервер для генерации Excel
}

function printReport() {
    window.print();
}
</script>
{% endblock %}
'''


@app.route('/sales')
def sales():
    if not session.get('user'):
        return redirect('/login')
    
    messages = get_flashed_messages()
    

    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    performance = request.args.get('performance', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10  
    
    filters = {
        'date_from': date_from,
        'date_to': date_to,
        'performance': performance
    }
    
    conn = get_db_connection()
    if not conn:
        flash('❌ Ошибка подключения к базе данных', 'error')
        return render_template(
            SALES_TEMPLATE,
            title='Учёт продаж',
            messages=messages,
            filters=filters,
            performances=[],
            sales_data=[],
            statistics=None
        )
    
    try:
        with conn.cursor() as cursor:

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sales (
                    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                    sale_date DATE NOT NULL,
                    performance_id INT UNSIGNED,
                    performance_name VARCHAR(200) NOT NULL,
                    tickets_count INT NOT NULL DEFAULT 1,
                    total_amount DECIMAL(10, 2) NOT NULL,
                    customer_name VARCHAR(200) NOT NULL,
                    customer_email VARCHAR(255),
                    customer_phone VARCHAR(20),
                    status VARCHAR(20) DEFAULT 'paid',
                    payment_method VARCHAR(50) DEFAULT 'online',
                    created_by BIGINT UNSIGNED DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
                    INDEX idx_sales_date (sale_date),
                    INDEX idx_sales_performance (performance_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performances (
                    id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    base_price DECIMAL(10, 2) NOT NULL,
                    is_active TINYINT(1) DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            cursor.execute("SELECT COUNT(*) as count FROM performances")
            performances_count = cursor.fetchone()['count']
            
            if performances_count == 0:
                test_performances = [
                    ('Лебединое озеро', 'Классический балет П.И. Чайковского', 2500.00),
                    ('Щелкунчик', 'Новогодняя сказка-балет', 2000.00),
                    ('Спящая красавица', 'Волшебный балет', 2200.00),
                    ('Кармен', 'Опера Жоржа Бизе', 1800.00),
                    ('Евгений Онегин', 'Опера П.И. Чайковского', 2100.00),
                ]
                
                for perf in test_performances:
                    cursor.execute("""
                        INSERT INTO performances (name, description, base_price)
                        VALUES (%s, %s, %s)
                    """, perf)
            
            cursor.execute("SELECT COUNT(*) as count FROM sales")
            sales_count = cursor.fetchone()['count']
            
            if sales_count == 0:
 
                from datetime import datetime, timedelta
                
                performance_names = ['Лебединое озеро', 'Щелкунчик', 'Спящая красавица', 'Кармен', 'Евгений Онегин']
                customer_names = ['Иванов Иван', 'Петрова Мария', 'Сидоров Алексей', 'Кузнецова Анна', 'Смирнов Дмитрий']
                payment_methods = ['online', 'cash', 'card', 'terminal']
                statuses = ['paid', 'paid', 'paid', 'pending', 'cancelled']
                
                for i in range(100):
                    sale_date = datetime.now() - timedelta(days=random.randint(0, 30))
                    performance_name = random.choice(performance_names)
                    tickets = random.randint(1, 5)
                    base_price = 2000 if 'Щелкунчик' in performance_name else random.randint(1500, 2500)
                    total = tickets * base_price * random.uniform(0.8, 1.2)
                    
                    cursor.execute("""
                        INSERT INTO sales (
                            sale_date, performance_name, tickets_count, total_amount,
                            customer_name, status, payment_method
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        sale_date.date(),
                        performance_name,
                        tickets,
                        round(total, 2),
                        random.choice(customer_names),
                        random.choice(statuses),
                        random.choice(payment_methods)
                    ))
            
            conn.commit()

            cursor.execute("SELECT id, name FROM performances WHERE is_active = 1 ORDER BY name")
            performances = cursor.fetchall()
            

            sql_conditions = []
            sql_params = []
            
            if date_from:
                sql_conditions.append("sale_date >= %s")
                sql_params.append(date_from)
            
            if date_to:
                sql_conditions.append("sale_date <= %s")
                sql_params.append(date_to)
            
            if performance:
                sql_conditions.append("performance_name = (SELECT name FROM performances WHERE id = %s)")
                sql_params.append(performance)
            
            where_clause = " AND ".join(sql_conditions) if sql_conditions else "1=1"
            
            count_sql = f"SELECT COUNT(*) as total FROM sales WHERE {where_clause}"
            cursor.execute(count_sql, sql_params)
            total_records = cursor.fetchone()['total']
            total_pages = (total_records + per_page - 1) // per_page
            
            offset = (page - 1) * per_page
            sales_sql = f"""
                SELECT * FROM sales 
                WHERE {where_clause}
                ORDER BY sale_date DESC, id DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(sales_sql, sql_params + [per_page, offset])
            sales_data = cursor.fetchall()
            
            # Получаем статистику
            stats_sql = f"""
                SELECT 
                    COUNT(*) as sales_count,
                    SUM(total_amount) as total_sales,
                    SUM(tickets_count) as total_tickets,
                    AVG(total_amount / tickets_count) as avg_ticket_price
                FROM sales 
                WHERE {where_clause}
            """
            cursor.execute(stats_sql, sql_params)
            statistics = cursor.fetchone()

            if statistics:
                statistics = {
                    'sales_count': statistics['sales_count'] or 0,
                    'total_sales': round(statistics['total_sales'] or 0, 2),
                    'total_tickets': statistics['total_tickets'] or 0,
                    'avg_ticket_price': round(statistics['avg_ticket_price'] or 0, 2)
                }
            
            return render_template(
                SALES_TEMPLATE,
                title='Учёт продаж',
                messages=messages,
                filters=filters,
                performances=performances,
                sales_data=sales_data,
                statistics=statistics,
                current_page=page,
                total_pages=total_pages
            )
            
    except Exception as e:
        flash(f'❌ Ошибка загрузки данных продаж: {str(e)}', 'error')
        return render_template(
            SALES_TEMPLATE,
            title='Учёт продаж',
            messages=get_flashed_messages(),
            filters=filters,
            performances=[],
            sales_data=[],
            statistics=None
        )
    finally:
        conn.close()

"""
<div class="nav-links">
    {% if session.user %}
        <a href="/dashboard">📊 Дашборд</a>
        <a href="/sales">💰 Учёт продаж</a>
        <a href="/servers">🖥️ Серверы</a>
        {% if session.role == 'admin' %}
            <a href="/admin">👑 Админ</a>
        {% endif %}
        <a href="/profile">👤 {{ session.user }}</a>
        <a href="/logout" style="background: #dc3545;">🚪 Выйти</a>
    {% else %}
        <a href="/login">🔐 Вход</a>
        <a href="/register">📝 Регистрация</a>
    {% endif %}
</div>
"""
