# AIBetExplorer - Технологии и настройки

## Технологический стек

### Язык программирования
- **Python 3.14** - основной язык проекта (требуется только эта версия)
- Полная типизация функций и структур данных

### Асинхронность
- **asyncio** - стандартная библиотека для асинхронного программирования
- **aiohttp** - асинхронный HTTP клиент для загрузки данных
- **aiofiles** - асинхронная работа с файловой системой
- **asyncpg** - асинхронный драйвер PostgreSQL
- **aiosqlite** - асинхронный драйвер SQLite (для тестов)

### База данных
- **SQLAlchemy 2.0** - ORM для работы с базой данных (async)
- **PostgreSQL 15+** - основная база данных (asyncpg драйвер)
- **SQLite** - для тестов (aiosqlite драйвер)

### Парсинг
- **selectolax** - быстрый HTML парсер (на базе Lexbor)

### Анализ данных
- **polars-lts-cpu** - библиотека для анализа данных (CPU версия)
- **pandera** - валидация данных

### Тестирование
- **pytest** - фреймворк для тестирования
- **pytest-asyncio** - поддержка асинхронных тестов
- **pytest-mock** - мокирование в тестах

### Линтинг и форматирование
- **ruff** - линтер и форматтер (замена Flake8, Black, isort)
- Настроен в `pyproject.toml`

### Утилиты
- **deepdiff** - сравнение данных

## Конфигурация проекта

### pyproject.toml

Основные настройки Ruff:
- **line-length**: 119 символов
- **target-version**: py314
- **src**: ["app"]
- **quote-style**: single (одинарные кавычки)
- **indent-style**: space (пробелы)

Правила линтинга:
- Включены все основные правила (E, F, W, B, Q, I, RUF, N, D, YTT, ANN, ASYNC, S, BLE, FBT, A, COM, C4, DTZ, EXE, FA, ISC, ICN, G, INP, PIE, PYI, PT, RSE, RET, SLF, SLOT, SIM, TID, TCH, INT, ARG, PTH, TD, FIX, ERA, PD, PGH, PL, TRY, FLY, NPY, AIR, PERF, FURB, LOG, T10, EM, T20, TC, DOC, UP)
- Игнорируются: D203, D213, D107, ANN401, DOC201, FURB113

### app/config_new.py

Основные параметры конфигурации:

#### База данных
```python
SQLALCHEMY_DATABASE_URI = 'postgresql+asyncpg://postgres:11111@localhost:5432/test44'
```

#### Каталоги
```python
DOWNLOAD_DIRECTORY = 'F:/download/betexplorer'  # для загрузки данных
FBCUP_DIRECTORY = 'D:/FBcup'  # для вывода результатов
DOWNLOAD_TEST_DIRECTORY = 'app/tests/download/betexplorer'  # для тестов
```

#### Виды спорта
```python
SPORT_TYPE = [
    SportType.FOOTBALL,
    SportType.BASKETBALL,
    SportType.HOCKEY,
    SportType.TENNIS,
    SportType.BASEBALL,
    SportType.VOLLEYBALL,
    SportType.HANDBALL
]
```

#### Параметры загрузки
```python
LOAD_NET = False  # загружать из сети или использовать кэш
LOAD_DETAIL = True  # загружать подробную информацию о матчах
LOAD_DETAIL_COEFFICIENTS = False  # загружать коэффициенты (тотал, фора)
```

#### Режим работы с базой данных
```python
SAVE_DATABASE = DATABASE_WRITE_DATA  # 0 - не использовать, 1 - только чтение, 2 - чтение и запись
```

#### Создание таблиц
```python
CREATE_TABLES = 1  # 0 - не создавать, 1 - создать
```

#### Обновление данных
```python
START_UPDATING = datetime.datetime(2129, 1, 1)  # обновлять данные после этой даты
EXCLUDE_COUNTRIES = ()  # список стран которые не загружать
```

#### Многопроцессорная обработка
```python
PROCESSES = 7  # количество процессов для параллельной загрузки
```

#### Конфигурация движка базы данных
```python
CONFIG_DATABASE = {
    'echo': False,
    'pool_recycle': 1800,  # перезапускать соединения каждые 30 минут
    'pool_size': 5,  # только PostgreSQL
    'max_overflow': 5,  # только PostgreSQL
    'pool_use_lifo': False,  # только PostgreSQL
    'connect_args': {
        'server_settings': {
            'application_name': 'bet_loader'
        }
    },
}
```

## Структура базы данных

### Основные таблицы

1. **sport** - виды спорта
   - sport_id (PK)
   - sport_name
   - sport_url

2. **country** - страны
   - country_id (PK, Identity)
   - country_name
   - country_flag_url

3. **country_sport** - связь стран и видов спорта
   - sport_id (FK)
   - country_id (FK)
   - country_url
   - country_order

4. **championship** - чемпионаты
   - championship_id (PK, Identity)
   - sport_id (FK)
   - country_id (FK)
   - championship_name
   - championship_url
   - championship_order
   - championship_years

5. **championship_stage** - стадии чемпионатов
   - stage_id (PK, Identity)
   - championship_id (FK)
   - stage_url
   - stage_name
   - stage_order
   - stage_current

6. **team** - команды
   - team_id (PK, Identity)
   - sport_id (FK)
   - country_id (FK)
   - team_name
   - team_full
   - team_url
   - team_emblem
   - download_date
   - save_date

7. **match** - матчи
   - match_id (PK, Identity)
   - championship_id (FK)
   - match_url
   - home_team_id (FK)
   - home_team_emblem
   - away_team_id (FK)
   - away_team_emblem
   - home_score
   - away_score
   - odds_1
   - odds_x
   - odds_2
   - game_date
   - score_stage
   - score_stage_short
   - is_fixture
   - stage_name
   - round_name
   - round_number
   - download_date
   - save_date

8. **time_score** - результаты по таймам
   - time_id (PK, Identity)
   - match_id (FK)
   - half_number
   - home_score
   - away_score

9. **shooter** - информация о голах
   - shooter_id (PK, Identity)
   - match_id (FK)
   - home_away
   - event_time
   - overtime
   - player_name
   - penalty_kick
   - event_order

10. **match_event** - события в матче
    - match_event_id (PK, Identity)
    - match_id (FK)
    - event_type_id
    - indicator
    - odds_less
    - odds_greater

### Индексы

- Уникальные индексы на: sport_name, sport_url, country_name, team_url
- Составные индексы на: championship (sport_id, country_id, championship_name, championship_years, championship_url)
- Индексы для производительности на: match_championship_id, time_match_id, shooter_match_id, event_match_id

## Запуск проекта

### Установка зависимостей
```bash
pip install -r requirements.txt
```

### Загрузка данных
```bash
python app/main.py
```

### Анализ данных
```bash
python app/analysis.py
```

### Запуск тестов
```bash
pytest app/tests/
```

### Линтинг
```bash
ruff check app/
ruff format app/
```

## Особенности реализации

### Асинхронная архитектура
- Все операции ввода-вывода асинхронные
- Использование async/await синтаксиса
- Эффективное использование ресурсов

### Многопроцессорная обработка
- Использование ProcessPoolExecutor
- Параллельная загрузка данных для разных стран
- Синхронизация через multiprocessing.Manager

### Кэширование
- Данные сохраняются на диск в формате HTTP
- Проверка даты модификации файла
- Возможность принудительного обновления

### Типизация
- Полная типизация всех функций
- Использование TypedDict для структур данных
- Проверка типов статическими анализаторами

## Требования к окружению

- Python 3.14 (требуется только эта версия)
- PostgreSQL 15+ (для основной базы)
- Windows 10+ (текущая среда разработки)
- Интернет-соединение (для загрузки данных с BetExplorer)
