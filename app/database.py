"""Работа с базой данных."""
from asyncio import current_task
from contextlib import asynccontextmanager
from types import TracebackType
from typing import Any, AsyncIterator, Dict, Optional, Tuple

from sqlalchemy import Connection, Dialect, Executable, StaticPool, event
from sqlalchemy.dialects.sqlite.aiosqlite import AsyncAdapt_aiosqlite_connection
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncConnection,
    AsyncEngine,
    AsyncMappingResult,
    AsyncSession,
    AsyncSessionTransaction,
    async_scoped_session,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import ConnectionPoolEntry


class Base(AsyncAttrs, DeclarativeBase):  # DeclarativeBase
    """Создаем метод описания БД (Создаем базовый класс для декларативных определений классов)."""


class DatabaseNotInitError(Exception):
    """Ошибка DatabaseSessionManager не инициализирован."""

    def __init__(self) -> None:
        super().__init__('DatabaseSessionManager is not initialized')


class DatabaseSessionManager:
    """Менеджер для работы с сессией базы данных."""

    _engine: Optional[AsyncEngine]
    _sessionmaker: Optional[async_sessionmaker[AsyncSession]]
    _scoped_factory: Optional[async_scoped_session[AsyncSession]]

    __slots__ = ['_engine', '_scoped_factory', '_sessionmaker']

    def __init__(self) -> None:
        """Инициализация класса для загрузки данных."""
        self._engine: Optional[AsyncEngine] = None
        self._sessionmaker: Optional[async_sessionmaker[AsyncSession]] = None
        self._scoped_factory: Optional[async_scoped_session[AsyncSession]] = None

    def init(self, url: str, **config_engine: Any) -> None:
        """Создаем движок.

        :param url: Подключение к базе данных
        :param config_engine: Конфигурация движка базы данных
        """
        if not url:
            raise ValueError('Не задано подключение к базе данных.')  # noqa: TRY003
        self._engine = create_async_engine(
            url,
            **config_engine,
        )
        if self._engine.dialect.name == 'sqlite':
            self._sqlite_post_configure_engine(1, self._engine, 1)
        self._sessionmaker = async_sessionmaker(
            autocommit=False,  # для обратной совместимости, но должно оставаться со значением по умолчанию False
            bind=self._engine,
            expire_on_commit=False,  # По умолчанию True завершить при фиксации. Установим False т.к. мы не хотим,
            # чтобы SQLAlchemy выдавал новые SQL-запросы к базе данных при обращении к уже закоммиченным объектам.
            # При этом возможно повторное использование данных из предыдущей транзакции
            autoflush=False,  # По умолчанию True. Когда True все операции запроса будут вызывать Session.flush()
            # этой Session перед продолжением. Это удобная функция, поэтому ее Session.flush() не нужно вызывать
            # повторно, чтобы запросами к базе данных получили результаты.
        )
        self._scoped_factory: async_scoped_session = async_scoped_session(
            self._sessionmaker,
            scopefunc=current_task,
        )

    async def __aexit__(self,
                        exc_type: type[BaseException] | None,
                        exc_value: BaseException | None,
                        traceback: TracebackType | None) -> None:
        """Выход из асинхронного менеджера контекста."""
        await self.close()

    async def __aenter__(self) -> 'DatabaseSessionManager':
        """Вход в асинхронный контекст-менеджер."""
        return self

    async def close(self) -> None:
        """Закрыть соединение с базой данных."""
        try:
            if self._engine is not None:
                await self._engine.dispose()
        finally:
            self._engine = None
            self._sessionmaker = None
            self._scoped_factory = None

    @staticmethod
    def _sqlite_post_configure_engine(url: int, engine: AsyncEngine, follower_ident: int) -> None:  # noqa: ARG004
        """События для конфигурации SQlite.

        :param url: Строка подключения к базе данных
        :param engine: Обеспечение работы с базой данных
        :param follower_ident: Порядковый номер базы
        """

        @event.listens_for(engine.sync_engine, 'do_connect')
        def do_connect(
                dialect: Dialect,  # noqa: ARG001
                conn_rec: ConnectionPoolEntry,  # noqa: ARG001
                cargs: Tuple[Any, ...],  # noqa: ARG001
                cparams: Dict[str, Any]) -> Optional[DBAPIConnection]:  # noqa: ARG001
            """Получить аргументы соединения до того, как соединение будет установлено."""

        @event.listens_for(engine.sync_engine, 'engine_connect')
        def engine_connect(conn: Connection) -> None:  # noqa: ARG001
            """Перехватить создание нового соединения.

            :param conn: Соединение с базой данных
            """
            # print("engine_connect", conn.exec_driver_sql("select 1").scalar())  # noqa: ERA001

        @event.listens_for(engine.sync_engine, 'connect')
        def connect(dbapi_connection: AsyncAdapt_aiosqlite_connection,
                    connection_record: ConnectionPoolEntry) -> None:  # noqa: ARG001
            """Перехватить подключение к базе данных.

            :param dbapi_connection: Соединение с базой данных
            :param connection_record: Менеджер соединение с базой данных
            """
            # Полностью отключает aiosqlite выдачу оператора BEGIN.
            # Также не позволяет ему выдавать COMMIT перед любым DDL.
            dbapi_connection.isolation_level = None
            # if not follower_ident:
            #     dbapi_connection.execute(
            #         'ATTACH DATABASE "test_schema.db" AS test_schema')
            # else:  # noqa: ERA001
            #     dbapi_connection.execute(
            #         'ATTACH DATABASE "%s_test_schema.db" AS test_schema'  # noqa: ERA001
            #         % follower_ident)

        @event.listens_for(engine.sync_engine, 'begin')
        def do_begin(conn: Connection) -> None:
            """Отправить в драйвер BEGIN.

            :param conn: Соединение с базой данных
            """
            conn.exec_driver_sql('BEGIN')

    @asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        """Соединение с базой данных."""
        if self._engine is None:
            raise DatabaseNotInitError

        connection: AsyncConnection
        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    @asynccontextmanager
    async def scoped_session(self) -> AsyncIterator[AsyncSession]:
        """Получить асинхронную сессию из хранилища уже созданных сессий."""
        if self._scoped_factory is None:
            raise DatabaseNotInitError
        async with self._scoped_factory() as session:
            try:
                yield session
            finally:
                await self._scoped_factory.remove()

    @asynccontextmanager
    async def get_session(self) -> AsyncIterator[AsyncSession]:
        """Получить асинхронную сессию."""
        if self._sessionmaker is None:
            raise DatabaseNotInitError
        async with self._sessionmaker() as session:
            yield session

    @asynccontextmanager
    async def get_test(self) -> AsyncIterator[AsyncSession]:
        """Получить асинхронную тестовую сессию."""
        if self._sessionmaker is None:
            raise DatabaseNotInitError
        connection = await self._engine.connect()
        trans = await connection.begin()
        nested = await connection.begin_nested()
        try:
            session: AsyncSession
            async with self._sessionmaker() as session:
                @event.listens_for(session.sync_session, 'after_transaction_end')
                def end_savepoint(session: AsyncSession, transaction: AsyncSessionTransaction) -> None:  # noqa: ARG001
                    nonlocal nested

                    if not nested.is_active:
                        nested = connection.sync_connection.begin_nested()

                yield session
        except:  # noqa: E722, RUF100
            await trans.rollback()
            raise
        finally:
            await trans.rollback()
            await session.close()
            await connection.close()

    async def created_db_tables(self) -> None:
        """Сделать DROP TABLE, CREATE TABLE в БД."""
        if self._engine is None:
            raise DatabaseNotInitError
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    async def get_db(self) -> AsyncSession:
        """Получить сессию."""
        async with self.get_session() as session:
            yield session

    @staticmethod
    async def get_stream(session: AsyncSession, stmt: Executable) -> list[dict]:
        """Получить список значений."""
        mr:  AsyncMappingResult = (await session.stream(stmt)).mappings()
        res = [dict(x) for x in await mr.all()]
        await mr.close()

        await session.commit()
        return res
