# 📚 Система управления учебниками

Система управления учебниками для классного руководителя средней школы с автоматизацией процессов выдачи, возврата, контроля состояния и отслеживания утерянных экземпляров.

## 🎯 Основные возможности

- ✅ **Веб-интерфейс**: современный интерфейс для учителя с панелью управления
- ✅ **Управление учебниками**: создание, редактирование, массовое создание с QR-кодами
- ✅ **Управление учениками**: добавление, редактирование, группировка по классам
- ✅ **Транзакции**: выдача и возврат учебников с фото
- ✅ **Контроль состояния**: отчеты о повреждениях с фото
- ✅ **Отслеживание находок**: система поиска утерянных учебников
- ✅ **Аутентификация**: JWT токены с ролями (учитель/ученик)
- ✅ **Интеграция с МАКС**: уведомления родителей и учеников
- ✅ **API документация**: автоматическая генерация Swagger UI

## 🛠️ Технический стек

- **Backend**: Python 3.8+, FastAPI
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **База данных**: SQLite (с возможностью перехода на PostgreSQL)
- **Аутентификация**: JWT токены
- **Файлы**: локальное хранение изображений
- **QR-коды**: автоматическая генерация для каждого учебника
- **Интеграция**: MAX Messenger Bot API

## 🚀 Быстрый старт

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd textbook-management
```

### 2. Создание виртуального окружения

```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\activate     # Windows
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Инициализация базы данных

```bash
python init_db.py
```

Это создаст:
- Все необходимые таблицы
- Первого пользователя-учителя (admin/admin123)

### 5. Запуск сервера

```bash
python main.py
```

Сервер будет доступен по адресу: http://localhost:8000

### 6. Доступ к системе

- **Веб-интерфейс**: http://localhost:8000
- **API документация**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🖥️ Веб-интерфейс

Система включает современный веб-интерфейс для учителя с функциями:

- **Панель управления**: статистика и быстрые действия
- **Управление учениками**: добавление, редактирование, поиск
- **Управление учебниками**: создание, QR-коды, статусы
- **Транзакции**: история выдачи и возврата
- **Отчеты**: генерация различных отчетов
- **Управление ботом**: тестирование подключения к МАКС

### Вход в систему
- **Логин**: admin
- **Пароль**: admin123

## 📋 API Endpoints

### Аутентификация
- `POST /api/auth/register` - Регистрация пользователя
- `POST /api/auth/token` - Получение JWT токена
- `GET /api/auth/me` - Информация о текущем пользователе

### Учебники
- `GET /api/textbooks/` - Список учебников
- `POST /api/textbooks/` - Создание учебника
- `POST /api/textbooks/bulk` - Массовое создание учебников
- `GET /api/textbooks/{id}` - Получение учебника
- `GET /api/textbooks/qr/{qr_code}` - Поиск по QR-коду
- `PUT /api/textbooks/{id}` - Обновление учебника
- `DELETE /api/textbooks/{id}` - Удаление учебника
- `GET /api/textbooks/{id}/qr-image` - QR-код изображение

### Ученики
- `GET /api/students/` - Список учеников
- `POST /api/students/` - Создание ученика
- `POST /api/students/bulk` - Массовое создание учеников
- `GET /api/students/{id}` - Получение ученика
- `PUT /api/students/{id}` - Обновление ученика
- `DELETE /api/students/{id}` - Удаление ученика
- `GET /api/students/grade/{grade}` - Ученики по классу

### Транзакции
- `POST /api/transactions/issue` - Выдача учебника
- `POST /api/transactions/return` - Возврат учебника
- `POST /api/transactions/bulk-issue` - Массовая выдача
- `POST /api/transactions/bulk-return` - Массовый возврат
- `GET /api/transactions/` - История транзакций
- `GET /api/transactions/{id}` - Детали транзакции
- `GET /api/transactions/student/{student_id}/active` - Активные учебники ученика

### Отчеты о повреждениях
- `POST /api/damage-reports/` - Создание отчета
- `GET /api/damage-reports/` - Список отчетов
- `GET /api/damage-reports/{id}` - Детали отчета
- `PUT /api/damage-reports/{id}` - Обновление отчета
- `POST /api/damage-reports/{id}/check` - Проверка отчета
- `GET /api/damage-reports/textbook/{textbook_id}/history` - История повреждений
- `GET /api/damage-reports/pending` - Ожидающие проверки

### Отчеты о находках
- `POST /api/found-reports/` - Создание отчета
- `GET /api/found-reports/` - Список отчетов
- `GET /api/found-reports/{id}` - Детали отчета
- `PUT /api/found-reports/{id}` - Обновление отчета
- `POST /api/found-reports/{id}/return` - Отметить как возвращенный
- `GET /api/found-reports/textbook/{textbook_id}/history` - История находок
- `GET /api/found-reports/active` - Активные находки

### Аккаунты учеников
- `POST /api/student-accounts/` - Создание аккаунта
- `POST /api/student-accounts/bulk` - Массовое создание
- `PUT /api/student-accounts/{student_id}/link-max` - Привязка к МАКС
- `GET /api/student-accounts/` - Список с информацией об аккаунтах

### Действия учеников
- `GET /api/student-actions/my-textbooks` - Мои учебники
- `GET /api/student-actions/textbook/{qr_code}` - Информация об учебнике
- `POST /api/student-actions/report-damage` - Сообщить о повреждении
- `POST /api/student-actions/report-lost` - Сообщить об утере
- `POST /api/student-actions/report-found` - Сообщить о находке
- `GET /api/student-actions/damage-check-reminder` - Напоминание о проверке

### Отчеты
- `GET /api/reports/issue-summary` - Отчет по выданным
- `GET /api/reports/not-issued` - Кто не получил учебники
- `GET /api/reports/not-returned` - Кто не сдал учебники
- `GET /api/reports/damage-summary` - Отчет по повреждениям
- `GET /api/reports/textbook-history/{textbook_id}` - История учебника
- `POST /api/reports/send-bulk-notifications` - Массовые уведомления

### Управление ботом
- `GET /api/bot/info` - Информация о боте
- `PUT /api/bot/info` - Обновление информации
- `POST /api/bot/send-message` - Отправить сообщение
- `POST /api/bot/send-message-to-user` - Сообщение пользователю
- `GET /api/bot/chat/{chat_id}` - Информация о чате
- `GET /api/bot/chat/{chat_id}/members` - Участники чата
- `POST /api/bot/chat/{chat_id}/add-member` - Добавить участника
- `POST /api/bot/chat/{chat_id}/remove-member` - Удалить участника
- `GET /api/bot/chat/{chat_id}/messages` - Сообщения чата
- `PUT /api/bot/message/{message_id}` - Редактировать сообщение
- `DELETE /api/bot/message/{message_id}` - Удалить сообщение
- `GET /api/bot/test-connection` - Тест подключения

## 🔧 Конфигурация

Основные настройки находятся в `app/core/config.py`:

```python
# База данных
DATABASE_URL = "sqlite:///./textbook_management.db"

# JWT токены
SECRET_KEY = "your-secret-key"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# МАКС бот
MAX_BOT_TOKEN = "your-max-bot-token"
MAX_API_URL = "https://api.max.ru"

# Файлы
UPLOAD_DIR = "static/uploads"
QR_CODES_DIR = "static/qr_codes"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Система
DAMAGE_CHECK_DAYS = 7
```

## 📁 Структура проекта

```
textbook-management/
├── app/
│   ├── api/                 # API роуты
│   │   ├── auth.py         # Аутентификация
│   │   ├── students.py     # Управление учениками
│   │   ├── textbooks.py    # Управление учебниками
│   │   ├── transactions.py # Транзакции
│   │   ├── damage_reports.py # Отчеты о повреждениях
│   │   ├── found_reports.py  # Отчеты о находках
│   │   ├── student_accounts.py # Аккаунты учеников
│   │   ├── student_actions.py  # Действия учеников
│   │   ├── reports.py      # Отчеты
│   │   └── bot_management.py   # Управление ботом
│   ├── core/               # Конфигурация и БД
│   │   ├── config.py       # Настройки
│   │   ├── database.py     # Подключение к БД
│   │   └── security.py     # Безопасность
│   ├── models/             # SQLAlchemy модели
│   │   ├── user.py         # Пользователи
│   │   ├── student.py      # Ученики
│   │   ├── textbook.py     # Учебники
│   │   ├── transaction.py  # Транзакции
│   │   ├── damage_report.py # Повреждения
│   │   └── found_report.py  # Находки
│   ├── schemas/            # Pydantic схемы
│   │   ├── user.py         # Схемы пользователей
│   │   ├── student.py      # Схемы учеников
│   │   ├── textbook.py     # Схемы учебников
│   │   ├── transaction.py  # Схемы транзакций
│   │   ├── damage_report.py # Схемы повреждений
│   │   └── found_report.py  # Схемы находок
│   └── services/           # Бизнес-логика
│       ├── image_storage.py # Хранение изображений
│       ├── qr_generator.py  # Генерация QR-кодов
│       ├── max_bot_client.py # Клиент МАКС API
│       └── parent_notifications.py # Уведомления
├── static/                 # Статические файлы
│   ├── css/               # Стили
│   │   └── style.css      # Основные стили
│   ├── js/                # JavaScript
│   │   └── app.js         # Основная логика
│   ├── qr_codes/          # QR-коды (генерируются)
│   └── index.html         # Главная страница
├── migrations/            # Миграции БД
├── main.py               # Точка входа
├── init_db.py            # Инициализация БД
├── requirements.txt      # Зависимости
├── README.md            # Документация
├── BOT_SETUP.md         # Настройка бота
└── LICENSE              # Лицензия
```

## 🔐 Безопасность

- Все эндпоинты (кроме аутентификации) требуют JWT токен
- Пароли хешируются с помощью bcrypt
- Файлы валидируются по типу и размеру
- SQL инъекции предотвращаются через SQLAlchemy ORM
- CORS настройки для веб-интерфейса

## 🤖 Интеграция с МАКС

Система интегрирована с MAX Messenger для:
- Уведомления родителей о выдаче/возврате учебников
- Уведомления о повреждениях и утерях
- Взаимодействие учеников с системой через бота
- Массовые уведомления

Подробная инструкция по настройке бота в файле `BOT_SETUP.md`.

## 🚧 Планы развития

- [x] Веб-интерфейс для учителя
- [x] Интеграция с МАКС мессенджером
- [x] Система уведомлений родителей
- [x] QR-коды для учебников
- [ ] Мобильное приложение
- [ ] Миграция на PostgreSQL
- [ ] Облачное хранение файлов
- [ ] Расширенная аналитика и графики
- [ ] Система резервного копирования
- [ ] Многоязычность

## 🐛 Устранение неполадок

### Проблемы с установкой
```bash
# Обновить pip
python -m pip install --upgrade pip

# Установить зависимости с обновленными версиями
pip install -r requirements.txt --upgrade
```

### Проблемы с базой данных
```bash
# Удалить старую БД и пересоздать
rm textbook_management.db
python init_db.py
```

### Проблемы с правами доступа
```bash
# Убедиться, что папки доступны для записи
chmod 755 static/qr_codes
chmod 755 static/uploads
```

## 📝 Лицензия

MIT License - см. файл [LICENSE](LICENSE)

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Создайте Pull Request

## 📞 Поддержка

При возникновении проблем создайте Issue в репозитории или обратитесь к документации API по адресу http://localhost:8000/docs 