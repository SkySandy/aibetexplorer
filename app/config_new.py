"""Конфигурация модуля загрузки."""
import datetime
import os
from typing import ClassVar

from sqlalchemy import StaticPool

from app.betexplorer.crud import DATABASE_NOT_USE, DATABASE_WRITE_DATA, DatabaseUsage
from app.betexplorer.schemas import SportType


class Settings:
    """Конфигурация модуля загрузки."""

    # SQLALCHEMY_DATABASE_URI: str = 'sqlite+aiosqlite:///C:\\sqlite\\full-database991.db'
    SQLALCHEMY_DATABASE_URI: str = 'postgresql+asyncpg://postgres:11111@localhost:5432/test44'
    """Подключение к базе данных."""

    # CONFIG_DATABASE: ClassVar[dict] = {
    #     'echo': False,
    #     'pool_recycle': 120, # перезапускать соединения по истечении заданного количества секунд
    #     'connect_args': {'check_same_thread': False, 'timeout': 120},
    #     'poolclass': StaticPool,
    # }
    CONFIG_DATABASE: ClassVar[dict] = {
        'echo': False,
        'pool_recycle': 1800,  # перезапускать соединения по истечении заданного количества секунд
        'pool_size': 5,  # Только Postgresql
        'max_overflow': 5,  # Только Postgresql
        'pool_use_lifo': False,  # Только Postgresql
        'connect_args': {'server_settings': {'application_name': 'bet_loader'}},
    }
    """Конфигурация движка базы данных."""

    DOWNLOAD_DIRECTORY: str = os.path.join('f:' + os.sep, 'download', 'betexplorer')
    """Каталог для загрузки страниц с сайта."""

    FBCUP_DIRECTORY: str = os.path.join('d:' + os.sep, 'FBcup')
    """Каталог для вывода данных в формате FBcup."""

    DOWNLOAD_TEST_DIRECTORY: str = os.path.join(os.path.abspath(os.getcwd()), 'download', 'betexplorer')
    """Каталог для загрузки страниц с сайта (для тестов)."""

    SQLALCHEMY_TEST_DATABASE_URI: ClassVar[list[str]] = [
        'postgresql+asyncpg://postgres:11111@localhost:5432/test22',
        'sqlite+aiosqlite://',
    ]
    """Подключение к базе данных (для тестов)."""

    SPORT_TYPE: ClassVar[list[SportType]] = [SportType.FOOTBALL, SportType.BASKETBALL, SportType.HOCKEY,
                                             SportType.TENNIS, SportType.BASEBALL, SportType.VOLLEYBALL,
                                             SportType.HANDBALL]
    """Виды спорта с которыми работаем."""

    LOAD_NET: bool = False
    """Загружать данные с сайта."""

    # SAVE_DATABASE: DatabaseUsage = DATABASE_NOT_USE
    SAVE_DATABASE: DatabaseUsage = DATABASE_WRITE_DATA
    """Не использовать базу данных, читать, записывать данные в базу данных."""

    CREATE_TABLES: int = 1
    """Создать таблицы перед работой."""

    START_UPDATING: datetime.datetime = datetime.datetime(2129, 1, 1)
    """Обновлять данные после этой даты."""
    # EXCLUDE_COUNTRIES: tuple = ('World', 'Africa', 'Asia', 'Europe', 'Australia & Oceania',
    #                             'North & Central America', 'South America')
    EXCLUDE_COUNTRIES: tuple = ()
    """Список стран который не загружать."""

    PROCESSES: int = 7
    """Одновременное количество запущенных процессов."""


settings = Settings()
