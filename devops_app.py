"""
🚀 DevOps Панель - ВСЁ В ОДНОМ ФАЙЛЕ
Запуск: python devops_app.py
Открыть: http://localhost:5000
Логин: admin / admin123
"""

import os
import random
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, flash, jsonify, session

# ==================== СОЗДАНИЕ ПРИЛОЖЕНИЯ ====================
app = Flask(__name__)
app.secret_key = 'devops-secret-key-2024'
app.config['TEMPLATES_AUTO_RELOAD'] = True

# ==================== БАЗА ДАННЫХ В ПАМЯТИ ====================
users_db = {
    'admin': {
        'password': 'admin123',
        'email': 'admin@example.com',
        'role': 'admin',
        'full_name': 'Администратор Системы',
        'created_at': '2024-01-01'
    }
}

servers_db = [
    {'id': 1, 'name': 'Основной сервер', 'ip': '192.168.1.100', 'status': 'online', 'last_check': '2024-01-15 10:30'},
    {'id': 2, 'name': 'Резервный сервер', 'ip': '192.168.1.101', 'status': 'offline', 'last_check': '2024-01-15 09:15'},
    {'id': 3, 'name': 'База данных', 'ip': '192.168.1.102', 'status': 'online', 'last_check': '2024-01-15 11:45'},
]

# ==================== HTML ШАБЛОНЫ В КОДЕ ====================
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
        
        /* СТАТИСТИКА */
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        }
        
        .stat-card h3 {
            font-size: 36px;
            color: #2c3e50;
            margin: 10px 0;
        }
        
        .stat-card p {
            color: #666;
            font-size: 16px;
        }
        
        /* ТАБЛИЦЫ */
        .table-container {
            overflow-x: auto;
            margin: 20px 0;
        }
        
        table {
            width: 100%;
            background: white;
            border-collapse: collapse;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        }
        
        th {
            background: #f8f9fa;
            padding: 16px;
            text-align: left;
            font-weight: 600;
            color: #495057;
            border-bottom: 2px solid #dee2e6;
        }
        
        td {
            padding: 14px 16px;
            border-bottom: 1px solid #eee;
        }
        
        tr:hover {
            background: #f8f9fa;
        }
        
        /* БЕЙДЖИ */
        .badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 600;
        }
        
        .badge-success {
            background: #d4edda;
            color: #155724;
        }
        
        .badge-danger {
            background: #f8d7da;
            color: #721c24;
        }
        
        .badge-warning {
            background: #fff3cd;
            color: #856404;
        }
        
        .badge-info {
            background: #d1ecf1;
            color: #0c5460;
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
        
        .btn-sm {
            padding: 8px 16px;
            font-size: 14px;
        }
        
        .btn-danger {
            background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
        }
        
        .btn-success {
            background: linear-gradient(135deg, #28a745 0%, #218838 100%);
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
        
        /* ГЛАВНАЯ СТРАНИЦА */
        .hero {
            text-align: center;
            padding: 100px 0;
            color: white;
        }
        
        .hero h1 {
            font-size: 48px;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .hero-buttons {
            display: flex;
            gap: 20px;
            justify-content: center;
            margin-top: 30px;
        }
        
        /* ПРОФИЛЬ */
        .profile-info {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .info-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
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
            
            .hero h1 {
                font-size: 32px;
            }
            
            .hero-buttons {
                flex-direction: column;
                align-items: center;
            }
            
            .stats {
                grid-template-columns: 1fr;
            }
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
                        <a href="#">👑 Админ</a>
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

    <!-- ОСНОВНОЙ КОНТЕНТ -->
    <div class="container">
        {% if messages %}
            {% for category, message in messages %}
                <div class="alert alert-{{ category }}">{{ message }}</div>
            {% endfor %}
        {% endif %}
        
        {% block content %}{% endblock %}
    </div>

    <!-- СКРИПТЫ -->
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
    
    // Анимация появления
    document.addEventListener('DOMContentLoaded', function() {
        const cards = document.querySelectorAll('.card');
        cards.forEach((card, index) => {
            card.style.animationDelay = (index * 0.1) + 's';
            card.classList.add('animate');
        });
    });
    </script>
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
                <label>👤 Имя пользователя</label>
                <input type="text" name="username" placeholder="Введите логин" required>
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
        <form method="POST" action="/register">
            <div class="form-group">
                <label>👤 Имя пользователя</label>
                <input type="text" name="username" placeholder="Придумайте логин" required>
            </div>
            <div class="form-group">
                <label>📧 Email</label>
                <input type="email" name="email" placeholder="Ваш email" required>
            </div>
            <div class="form-group">
                <label>🔒 Пароль</label>
                <input type="password" name="password" placeholder="Минимум 6 символов" required>
            </div>
            <div class="form-group">
                <label>🔒 Подтвердите пароль</label>
                <input type="password" name="confirm_password" placeholder="Повторите пароль" required>
            </div>
            <button type="submit" class="btn" style="width: 100%; margin-top: 10px;">
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

<!-- СТАТИСТИКА -->
<div class="stats">
    <div class="stat-card">
        <div style="font-size: 14px; color: #666; margin-bottom: 10px;">🖥️ Всего серверов</div>
        <h3>{{ total_servers }}</h3>
    </div>
    <div class="stat-card">
        <div style="font-size: 14px; color: #666; margin-bottom: 10px;">✅ Серверов онлайн</div>
        <h3 style="color: #28a745;">{{ online_servers }}</h3>
    </div>
    <div class="stat-card">
        <div style="font-size: 14px; color: #666; margin-bottom: 10px;">👥 Пользователей</div>
        <h3>{{ total_users }}</h3>
    </div>
    <div class="stat-card">
        <div style="font-size: 14px; color: #666; margin-bottom: 10px;">⚠️ Проблемных</div>
        <h3 style="color: #dc3545;">{{ problem_servers }}</h3>
    </div>
</div>

<!-- ПОСЛЕДНИЕ СЕРВЕРЫ -->
<div class="card">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <h2>🖥️ Последние серверы</h2>
        <a href="/servers" class="btn btn-sm">📋 Все серверы</a>
    </div>
    
    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th>Название</th>
                    <th>IP адрес</th>
                    <th>Статус</th>
                    <th>Последняя проверка</th>
                    <th>Действия</th>
                </tr>
            </thead>
            <tbody>
                {% for server in servers %}
                <tr>
                    <td><strong>{{ server.name }}</strong></td>
                    <td><code>{{ server.ip }}</code></td>
                    <td>
                        {% if server.status == 'online' %}
                            <span class="badge badge-success">✅ Онлайн</span>
                        {% elif server.status == 'warning' %}
                            <span class="badge badge-warning">⚠️ Предупреждение</span>
                        {% else %}
                            <span class="badge badge-danger">❌ Оффлайн</span>
                        {% endif %}
                    </td>
                    <td>{{ server.last_check or 'Не проверялся' }}</td>
                    <td>
                        <button onclick="checkServer({{ server.id }})" class="btn btn-sm" style="margin-right: 5px;">
                            🔄 Проверить
                        </button>
                        {% if session.role == 'admin' %}
                        <a href="/servers/delete/{{ server.id }}" 
                           onclick="return confirm('Удалить сервер {{ server.name }}?')" 
                           class="btn btn-sm btn-danger">
                            🗑️ Удалить
                        </a>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>

<!-- ПРОФИЛЬ -->
<div class="card">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <h2>👤 Ваш профиль</h2>
        <a href="/profile" class="btn btn-sm">✏️ Редактировать</a>
    </div>
    
    <div class="profile-info">
        <div class="info-card">
            <div style="color: #666; font-size: 14px;">👤 Имя пользователя</div>
            <div style="font-size: 18px; margin-top: 5px;"><strong>{{ session.user }}</strong></div>
        </div>
        <div class="info-card">
            <div style="color: #666; font-size: 14px;">📧 Email</div>
            <div style="font-size: 18px; margin-top: 5px;">{{ user_info.email }}</div>
        </div>
        <div class="info-card">
            <div style="color: #666; font-size: 14px;">👑 Роль</div>
            <div style="font-size: 18px; margin-top: 5px;">
                {% if session.role == 'admin' %}
                    <span class="badge badge-danger">Администратор</span>
                {% else %}
                    <span class="badge badge-info">Пользователь</span>
                {% endif %}
            </div>
        </div>
    </div>
</div>
{% endblock %}
'''

SERVERS_TEMPLATE = '''
{% extends "base" %}
{% block content %}
<div class="card">
    <h1>🖥️ Управление серверами</h1>
    
    <!-- ФОРМА ДОБАВЛЕНИЯ -->
    {% if session.role == 'admin' %}
    <div style="background: #f8f9fa; padding: 25px; border-radius: 10px; margin: 25px 0;">
        <h3 style="margin-bottom: 20px;">➕ Добавить новый сервер</h3>
        <form method="POST" action="/servers/add">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                <div class="form-group">
                    <label>Название сервера</label>
                    <input type="text" name="name" placeholder="Например: Основной сервер" required>
                </div>
                <div class="form-group">
                    <label>IP адрес</label>
                    <input type="text" name="ip" placeholder="Например: 192.168.1.100" required>
                </div>
            </div>
            <div class="form-group">
                <label>Описание (необязательно)</label>
                <textarea name="description" rows="3" placeholder="Описание сервера..." style="width: 100%; padding: 14px; border: 2px solid #e9ecef; border-radius: 8px;"></textarea>
            </div>
            <button type="submit" class="btn btn-success">➕ Добавить сервер</button>
        </form>
    </div>
    {% endif %}
    
    <!-- СПИСОК СЕРВЕРОВ -->
    <h2 style="margin: 30px 0 20px 0;">📋 Список серверов</h2>
    
    {% if servers %}
    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Название</th>
                    <th>IP адрес</th>
                    <th>Статус</th>
                    <th>Описание</th>
                    <th>Действия</th>
                </tr>
            </thead>
            <tbody>
                {% for server in servers %}
                <tr>
                    <td><strong>#{{ server.id }}</strong></td>
                    <td><strong>{{ server.name }}</strong></td>
                    <td><code>{{ server.ip }}</code></td>
                    <td>
                        {% if server.status == 'online' %}
                            <span class="badge badge-success">✅ Онлайн</span>
                        {% elif server.status == 'warning' %}
                            <span class="badge badge-warning">⚠️ Предупреждение</span>
                        {% else %}
                            <span class="badge badge-danger">❌ Оффлайн</span>
                        {% endif %}
                    </td>
                    <td>{{ server.description or '-' }}</td>
                    <td>
                        <button onclick="checkServer({{ server.id }})" class="btn btn-sm" style="margin-right: 5px;">
                            🔄 Проверить
                        </button>
                        {% if session.role == 'admin' %}
                        <a href="/servers/delete/{{ server.id }}" 
                           onclick="return confirm('Удалить сервер {{ server.name }}?')" 
                           class="btn btn-sm btn-danger">
                            🗑️ Удалить
                        </a>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% else %}
    <div style="text-align: center; padding: 40px; color: #666;">
        <div style="font-size: 48px; margin-bottom: 20px;">🖥️</div>
        <h3>Серверы не найдены</h3>
        <p>Добавьте первый сервер для начала мониторинга</p>
    </div>
    {% endif %}
</div>
{% endblock %}
'''

PROFILE_TEMPLATE = '''
{% extends "base" %}
{% block content %}
<div class="card">
    <h1>👤 Профиль пользователя</h1>
    
    <div class="profile-info" style="margin-top: 30px;">
        <div class="info-card">
            <div style="color: #666; font-size: 14px;">👤 Имя пользователя</div>
            <div style="font-size: 24px; margin-top: 10px;"><strong>{{ session.user }}</strong></div>
        </div>
        
        <div class="info-card">
            <div style="color: #666; font-size: 14px;">📧 Email</div>
            <div style="font-size: 20px; margin-top: 10px;">{{ user_info.email }}</div>
        </div>
        
        <div class="info-card">
            <div style="color: #666; font-size: 14px;">👤 Полное имя</div>
            <div style="font-size: 20px; margin-top: 10px;">{{ user_info.full_name or 'Не указано' }}</div>
        </div>
        
        <div class="info-card">
            <div style="color: #666; font-size: 14px;">👑 Роль</div>
            <div style="font-size: 20px; margin-top: 10px;">
                {% if session.role == 'admin' %}
                    <span class="badge badge-danger" style="font-size: 16px;">Администратор</span>
                {% else %}
                    <span class="badge badge-info" style="font-size: 16px;">Пользователь</span>
                {% endif %}
            </div>
        </div>
        
        <div class="info-card">
            <div style="color: #666; font-size: 14px;">📅 Дата регистрации</div>
            <div style="font-size: 20px; margin-top: 10px;">{{ user_info.created_at }}</div>
        </div>
        
        <div class="info-card">
            <div style="color: #666; font-size: 14px;">✅ Статус аккаунта</div>
            <div style="font-size: 20px; margin-top: 10px;">
                <span class="badge badge-success" style="font-size: 16px;">Активен</span>
            </div>
        </div>
    </div>
    
    <div style="margin-top: 40px; padding-top: 30px; border-top: 2px solid #f0f0f0;">
        <h3 style="margin-bottom: 20px;">✏️ Редактирование профиля</h3>
        <form method="POST" action="/profile/update">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                <div class="form-group">
                    <label>Полное имя</label>
                    <input type="text" name="full_name" value="{{ user_info.full_name or '' }}">
                </div>
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" name="email" value="{{ user_info.email }}" required>
                </div>
            </div>
            <button type="submit" class="btn">💾 Сохранить изменения</button>
        </form>
    </div>
</div>
{% endblock %}
'''

INDEX_TEMPLATE = '''
{% extends "base" %}
{% block content %}
<div class="hero">
    <h1>🚀 DevOps Панель Управления</h1>
    <p style="font-size: 20px; max-width: 600px; margin: 20px auto; opacity: 0.9;">
        Профессиональная система для мониторинга и управления серверами
    </p>
    
    {% if not session.user %}
    <div class="hero-buttons">
        <a href="/login" class="btn" style="padding: 15px 40px; font-size: 18px;">
            🔐 Войти в систему
        </a>
        <a href="/register" class="btn btn-success" style="padding: 15px 40px; font-size: 18px;">
            📝 Зарегистрироваться
        </a>
    </div>
    
    <div style="margin-top: 50px; display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 30px;">
        <div style="background: rgba(255,255,255,0.1); padding: 25px; border-radius: 10px; backdrop-filter: blur(10px);">
            <div style="font-size: 36px; margin-bottom: 15px;">🖥️</div>
            <h3>Мониторинг серверов</h3>
            <p>Отслеживание состояния серверов в реальном времени</p>
        </div>
        <div style="background: rgba(255,255,255,0.1); padding: 25px; border-radius: 10px; backdrop-filter: blur(10px);">
            <div style="font-size: 36px; margin-bottom: 15px;">👥</div>
            <h3>Управление пользователями</h3>
            <p>Гибкая система ролей и прав доступа</p>
        </div>
        <div style="background: rgba(255,255,255,0.1); padding: 25px; border-radius: 10px; backdrop-filter: blur(10px);">
            <div style="font-size: 36px; margin-bottom: 15px;">📊</div>
            <h3>Аналитика и отчеты</h3>
            <p>Детальная статистика и графики производительности</p>
        </div>
    </div>
    {% else %}
    <div class="hero-buttons">
        <a href="/dashboard" class="btn" style="padding: 15px 40px; font-size: 18px;">
            📊 Перейти в панель
        </a>
    </div>
    {% endif %}
</div>
{% endblock %}
'''

# ==================== ФУНКЦИИ РЕНДЕРИНГА ====================
def render_template(template, **context):
    """Рендерит шаблон из строки"""
    from flask import render_template_string
    return render_template_string(template, **context)

def get_messages():
    """Получает сообщения из сессии"""
    messages = session.pop('_flashes', [])
    return messages

# ==================== МАРШРУТЫ ====================
@app.route('/')
def index():
    messages = get_messages()
    return render_template(
        BASE_TEMPLATE.replace('{% block content %}{% endblock %}', INDEX_TEMPLATE),
        title='DevOps Панель',
        messages=messages,
        session=session
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user'):
        return redirect('/dashboard')
    
    messages = get_messages()
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = users_db.get(username)
        
        if user and user['password'] == password:
            session['user'] = username
            session['role'] = user['role']
            session['_flashes'] = [('success', '✅ Вход выполнен успешно!')]
            return redirect('/dashboard')
        else:
            session['_flashes'] = [('error', '❌ Неверный логин или пароль')]
            return redirect('/login')
    
    return render_template(
        BASE_TEMPLATE.replace('{% block content %}{% endblock %}', LOGIN_TEMPLATE),
        title='Вход в систему',
        messages=messages,
        session=session
    )

@app.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user'):
        return redirect('/dashboard')
    
    messages = get_messages()
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            session['_flashes'] = [('error', '❌ Пароли не совпадают')]
            return redirect('/register')
        
        if username in users_db:
            session['_flashes'] = [('error', '❌ Пользователь уже существует')]
            return redirect('/register')
        
        users_db[username] = {
            'password': password,
            'email': email,
            'role': 'user',
            'full_name': username,
            'created_at': datetime.now().strftime('%d.%m.%Y %H:%M')
        }
        
        session['_flashes'] = [('success', '✅ Регистрация успешна! Теперь войдите в систему.')]
        return redirect('/login')
    
    return render_template(
        BASE_TEMPLATE.replace('{% block content %}{% endblock %}', REGISTER_TEMPLATE),
        title='Регистрация',
        messages=messages,
        session=session
    )

@app.route('/logout')
def logout():
    session.clear()
    session['_flashes'] = [('info', '👋 Вы вышли из системы')]
    return redirect('/')

@app.route('/dashboard')
def dashboard():
    if not session.get('user'):
        return redirect('/login')
    
    messages = get_messages()
    
    # Статистика
    total_servers = len(servers_db)
    online_servers = len([s for s in servers_db if s['status'] == 'online'])
    total_users = len(users_db)
    problem_servers = len([s for s in servers_db if s['status'] != 'online'])
    
    return render_template(
        BASE_TEMPLATE.replace('{% block content %}{% endblock %}', DASHBOARD_TEMPLATE),
        title='Панель управления',
        messages=messages,
        session=session,
        user_info=users_db.get(session['user'], {}),
        total_servers=total_servers,
        online_servers=online_servers,
        total_users=total_users,
        problem_servers=problem_servers,
        servers=servers_db[:5]  # Только 5 последних
    )

@app.route('/servers')
def servers():
    if not session.get('user'):
        return redirect('/login')
    
    messages = get_messages()
    
    return render_template(
        BASE_TEMPLATE.replace('{% block content %}{% endblock %}', SERVERS_TEMPLATE),
        title='Управление серверами',
        messages=messages,
        session=session,
        servers=servers_db
    )

@app.route('/servers/add', methods=['POST'])
def add_server():
    if not session.get('user') or session.get('role') != 'admin':
        session['_flashes'] = [('error', '❌ Нет прав для добавления серверов')]
        return redirect('/servers')
    
    name = request.form.get('name')
    ip = request.form.get('ip')
    description = request.form.get('description')
    
    if name and ip:
        new_id = max([s['id'] for s in servers_db], default=0) + 1
        servers_db.append({
            'id': new_id,
            'name': name,
            'ip': ip,
            'description': description,
            'status': 'online',
            'last_check': datetime.now().strftime('%d.%m.%Y %H:%M')
        })
        session['_flashes'] = [('success', f'✅ Сервер "{name}" добавлен')]
    
    return redirect('/servers')

@app.route('/servers/delete/<int:server_id>')
def delete_server(server_id):
    if not session.get('user') or session.get('role') != 'admin':
        session['_flashes'] = [('error', '❌ Нет прав для удаления серверов')]
        return redirect('/servers')
    
    global servers_db
    server = next((s for s in servers_db if s['id'] == server_id), None)
    if server:
        servers_db = [s for s in servers_db if s['id'] != server_id]
        session['_flashes'] = [('info', f'🗑️ Сервер "{server["name"]}" удален')]
    
    return redirect('/servers')

@app.route('/api/check/<int:server_id>')
def check_server_api(server_id):
    if not session.get('user'):
        return jsonify({'success': False})
    
    server = next((s for s in servers_db if s['id'] == server_id), None)
    if server:
        status = random.choice(['online', 'offline', 'warning'])
        server['status'] = status
        server['last_check'] = datetime.now().strftime('%d.%m.%Y %H:%M')
        return jsonify({'success': True, 'status': status})
    
    return jsonify({'success': False})

@app.route('/profile')
def profile():
    if not session.get('user'):
        return redirect('/login')
    
    messages = get_messages()
    
    return render_template(
        BASE_TEMPLATE.replace('{% block content %}{% endblock %}', PROFILE_TEMPLATE),
        title='Профиль пользователя',
        messages=messages,
        session=session,
        user_info=users_db.get(session['user'], {})
    )

@app.route('/profile/update', methods=['POST'])
def update_profile():
    if not session.get('user'):
        return redirect('/login')
    
    username = session['user']
    user = users_db.get(username)
    
    if user:
        user['email'] = request.form.get('email', user['email'])
        user['full_name'] = request.form.get('full_name', user['full_name'])
        session['_flashes'] = [('success', '✅ Профиль обновлен')]
    
    return redirect('/profile')

# ==================== ЗАПУСК ====================
if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 DevOps Панель - Все в одном файле!")
    print("="*60)
    print("📌 Запуск сервера...")
    print("🌐 Откройте в браузере: http://localhost:5000")
    print("👤 Тестовый аккаунт:")
    print("   Логин: admin")
    print("   Пароль: admin123")
    print("="*60 + "\n")
    
    # Запуск с обработкой статики
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app)
    
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
        threaded=True
    )