"""Тесты для класса DatabaseSessionManager."""
import asyncio
from typing import AsyncGenerator, AsyncIterator

from _pytest.fixtures import SubRequest
from _pytest.monkeypatch import MonkeyPatch
import pytest
import pytest_asyncio
from pytest_mock import MockerFixture
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.betexplorer.models import Sport
from app.config import settings
from app.database import DatabaseNotInitError, DatabaseSessionManager


@pytest_asyncio.fixture(params=settings.SQLALCHEMY_TEST_DATABASE_URI)
async def database_manager(request: SubRequest) -> DatabaseSessionManager:
    """Создание класса DatabaseSessionManager для тестов."""
    database: DatabaseSessionManager
    async with DatabaseSessionManager() as database:
        database.init(request.param, echo=False)
        yield database


@pytest_asyncio.fixture(autouse=True)
async def create_tables(database_manager: DatabaseSessionManager) -> None:
    """Создание таблиц в базе данных для тестов."""
    await database_manager.created_db_tables()


@pytest_asyncio.fixture
async def session(database_manager: DatabaseSessionManager) -> AsyncIterator[AsyncSession]:
    """Создание сессии для тестов."""
    # noinspection PyArgumentList
    async with database_manager.get_session() as session_test:
        yield session_test


class TestGetSession:
    """Тест менеджера сессий."""

    @pytest.mark.asyncio()
    async def test_get_session_invalid_sessionmaker(self, database_manager: DatabaseSessionManager) -> None:
        """Сессия не инициализированная."""
        database_manager._sessionmaker = None  # noqa: SLF001
        with pytest.raises(DatabaseNotInitError):
            # noinspection PyArgumentList
            async with database_manager.get_session() as session:  # noqa: F841
                pass

    @pytest.mark.asyncio()
    async def test_properly_releases_transaction_after_use(self,
                                                           database_manager: DatabaseSessionManager) -> None:
        """Транзакция закрыта после выхода из сессии."""
        # noinspection PyArgumentList
        async with database_manager.get_session() as session_test:
            assert not session_test.in_transaction()
            await session_test.execute(text('SELECT * FROM sport'))
            assert session_test.in_transaction()
        assert not session_test.in_transaction()

    @pytest.mark.asyncio()
    async def test_raises_exception_if_error_during_session_creation(self,
                                                                     database_manager: DatabaseSessionManager) -> None:
        """Вызывает ли метод get_session исключение, если во время создания сеанса возникает ошибка."""
        with pytest.raises(Exception, match='Error during session creation'):
            # noinspection PyArgumentList
            async with database_manager.get_session() as session:  # noqa: F841
                raise Exception('Error during session creation')  # noqa: TRY002, TRY003

    @pytest.mark.asyncio()
    async def test_handles_multiple_concurrent_requests(self, database_manager: DatabaseSessionManager) -> None:
        """Может ли метод обрабатывать несколько одновременных запросов на сеансы."""
        # noinspection PyArgumentList
        async with database_manager.get_session() as session1:  # noqa: SIM117
            # noinspection PyArgumentList
            async with database_manager.get_session() as session2:
                # Assert
                assert isinstance(session1, AsyncSession)
                assert session1.bind == database_manager._engine  # noqa: SLF001
                assert isinstance(session2, AsyncSession)
                assert session2.bind == database_manager._engine  # noqa: SLF001
                assert session1 != session2

    @pytest.mark.asyncio()
    async def test_can_handle_large_amounts_of_data(self, database_manager: DatabaseSessionManager) -> None:
        """Может ли метод обрабатывать большие объемы данных в сеансе."""
        # noinspection PyArgumentList
        async with database_manager.get_session() as session_test:
            # Add large amounts of data to the session
            for i in range(10000):
                session_test.add(Sport(sport_id=i, sport_name=f'Sport {i}', sport_url=f'/sport/{i}'))

            assert isinstance(session_test, AsyncSession)
            assert session_test.bind == database_manager._engine  # noqa: SLF001
            assert len(session_test.new) == 10000

    @pytest.mark.asyncio()
    async def test_get_session_success(self, database_manager: DatabaseSessionManager) -> None:
        """Правильный возврат."""
        # noinspection PyArgumentList
        async with database_manager.get_session() as session_test:
            assert isinstance(session_test, AsyncSession)
            assert session_test.bind == database_manager._engine  # noqa: SLF001

    @pytest.mark.asyncio()
    async def test_get_session_yield(self, database_manager: DatabaseSessionManager) -> None:
        """Сессией можно пользоваться."""
        # noinspection PyArgumentList
        async with database_manager.get_session() as session_test:
            result = await session_test.execute(text('SELECT * FROM sport'))
            assert result.fetchall() == []

    @pytest.mark.asyncio()
    async def test_large_number_of_concurrent_requests(self, database_manager: DatabaseSessionManager) -> None:
        """Выполнить параллельно много запросов к базе данных."""
        # Количество одновременных запросов
        num_requests = 100

        # Список для хранения результатов одновременных запросов.
        results = []

        # Асинхронная функция для имитации запроса
        async def simulate_request() -> None:
            # noinspection PyArgumentList
            async with database_manager.get_session() as session:
                # Выполним запрос
                result = await session.execute(text('SELECT * FROM sport'))
                results.append(result)

        # Список задач для одновременных запросов.
        tasks = [simulate_request() for _ in range(num_requests)]

        # Запуск задач одновременно
        await asyncio.gather(*tasks)

        # Проверяем, что все запросы были успешными
        assert len(results) == num_requests

    def mock_sessionmaker(self) -> AsyncGenerator[AsyncSession, None]:
        """Ошибка в генераторе сессий."""
        raise Exception('Mocked exception')  # noqa: TRY002, TRY003

    @pytest.mark.asyncio()
    async def test_sessionmaker_raises_exception(self,
                                                 monkeypatch: MonkeyPatch,
                                                 database_manager: DatabaseSessionManager) -> None:
        """Создатель сеанса вызывает исключение."""
        monkeypatch.setattr(database_manager, '_sessionmaker', self.mock_sessionmaker)

        with pytest.raises(Exception, match='Mocked exception'):
            # noinspection PyArgumentList
            async with database_manager.get_session() as session:  # noqa: F841
                pass


class TestScopedSession:
    """Тест менеджера сессий для асинхронных запросов."""

    @pytest.mark.asyncio()
    async def test_scoped_session_invalid_sessionmaker(self, database_manager: DatabaseSessionManager) -> None:
        """Сессия не инициализированная."""
        database_manager._scoped_factory = None  # noqa: SLF001
        with pytest.raises(DatabaseNotInitError):
            # noinspection PyArgumentList
            async with database_manager.scoped_session() as session:  # noqa: F841
                pass

    @pytest.mark.asyncio()
    async def test_properly_releases_transaction_after_use(self,
                                                           database_manager: DatabaseSessionManager) -> None:
        """Транзакция закрыта после выхода из сессии."""
        # noinspection PyArgumentList
        async with database_manager.scoped_session() as session_test:
            assert not session_test.in_transaction()
            await session_test.execute(text('SELECT * FROM sport'))
            assert session_test.in_transaction()
        assert not session_test.in_transaction()

    @pytest.mark.asyncio()
    async def test_raises_exception_if_error_during_session_creation(self,
                                                                     database_manager: DatabaseSessionManager) -> None:
        """Вызывает ли метод get_session исключение, если во время создания сеанса возникает ошибка."""
        with pytest.raises(Exception, match='Error during session creation'):
            # noinspection PyArgumentList
            async with database_manager.scoped_session() as session:  # noqa: F841
                raise Exception('Error during session creation')  # noqa: TRY002, TRY003

    @pytest.mark.asyncio()
    async def test_handles_multiple_concurrent_requests(self, database_manager: DatabaseSessionManager) -> None:
        """Может ли метод обрабатывать несколько одновременных запросов на сеансы."""
        # noinspection PyArgumentList
        async with database_manager.scoped_session() as session1:  # noqa: SIM117
            # noinspection PyArgumentList
            async with database_manager.scoped_session() as session2:
                # Assert
                assert isinstance(session1, AsyncSession)
                assert session1.bind == database_manager._engine  # noqa: SLF001
                assert isinstance(session2, AsyncSession)
                assert session2.bind == database_manager._engine  # noqa: SLF001
                assert session1 == session2

    @pytest.mark.asyncio()
    async def test_can_handle_large_amounts_of_data(self, database_manager: DatabaseSessionManager) -> None:
        """Может ли метод обрабатывать большие объемы данных в сеансе."""
        # noinspection PyArgumentList
        async with database_manager.scoped_session() as session_test:
            # Add large amounts of data to the session
            for i in range(10000):
                session_test.add(Sport(sport_id=i, sport_name=f'Sport {i}', sport_url=f'/sport/{i}'))

            assert isinstance(session_test, AsyncSession)
            assert session_test.bind == database_manager._engine  # noqa: SLF001
            assert len(session_test.new) == 10000

    @pytest.mark.asyncio()
    async def test_scoped_session_success(self, database_manager: DatabaseSessionManager) -> None:
        """Правильный возврат."""
        # noinspection PyArgumentList
        async with database_manager.scoped_session() as session_test:
            assert isinstance(session_test, AsyncSession)
            assert session_test.bind == database_manager._engine  # noqa: SLF001

    @pytest.mark.asyncio()
    async def test_scoped_session_yield(self, database_manager: DatabaseSessionManager) -> None:
        """Сессией можно пользоваться."""
        # noinspection PyArgumentList
        async with database_manager.scoped_session() as session_test:
            result = await session_test.execute(text('SELECT * FROM sport'))
            assert result.fetchall() == []

    @pytest.mark.asyncio()
    async def test_large_number_of_concurrent_requests(self, database_manager: DatabaseSessionManager) -> None:
        """Выполнить параллельно много запросов к базе данных."""
        # Количество одновременных запросов
        num_requests = 100

        # Список для хранения результатов одновременных запросов.
        results = []

        # Асинхронная функция для имитации запроса
        async def simulate_request() -> None:
            # noinspection PyArgumentList
            async with database_manager.scoped_session() as session:
                # Выполним запрос
                result = await session.execute(text('SELECT * FROM sport'))
                results.append(result)

        # Список задач для одновременных запросов.
        tasks = [simulate_request() for _ in range(num_requests)]

        # Запуск задач одновременно
        await asyncio.gather(*tasks)

        # Проверяем, что все запросы были успешными
        assert len(results) == num_requests

    def mock_sessionmaker(self) -> AsyncGenerator[AsyncSession, None]:
        """Ошибка в генераторе сессий."""
        raise Exception('Mocked exception')  # noqa: TRY002, TRY003

    @pytest.mark.asyncio()
    async def test_sessionmaker_raises_exception(self,
                                                 monkeypatch: MonkeyPatch,
                                                 database_manager: DatabaseSessionManager) -> None:
        """Создатель сеанса вызывает исключение."""
        monkeypatch.setattr(database_manager, '_scoped_factory', self.mock_sessionmaker)

        with pytest.raises(Exception, match='Mocked exception'):
            # noinspection PyArgumentList
            async with database_manager.scoped_session() as session:  # noqa: F841
                pass


class TestClose:
    """Тест закрытия соединения с базой."""

    @pytest.mark.asyncio()
    async def test_closes_connection_to_database(self, database_manager: DatabaseSessionManager) -> None:
        """Закрывает соединение с базой данных."""
        await database_manager.close()

        assert database_manager._engine is None  # noqa: SLF001
        assert database_manager._sessionmaker is None  # noqa: SLF001

    @pytest.mark.asyncio()
    async def test_can_be_called_multiple_times_without_exceptions(self,
                                                                   database_manager: DatabaseSessionManager) -> None:
        """Может быть вызван несколько раз без каких-либо исключений."""
        # noinspection PyBroadException
        try:
            await database_manager.close()
            await database_manager.close()
            await database_manager.close()
        except Exception:  # noqa: BLE001
            pytest.fail('Unexpected exception raised')

    @pytest.mark.asyncio()
    async def test_does_not_raise_exceptions_when_engine_is_none(self) -> None:
        """Когда engine имеет значение «Нет», не вызывает никаких исключений."""
        manager = DatabaseSessionManager()
        # noinspection PyBroadException
        try:
            await manager.close()
        except Exception:  # noqa: BLE001
            pytest.fail('Unexpected exception raised')


class TestCreatedDbTables:
    """Проверка удаления и создания таблиц."""

    @pytest.mark.asyncio()
    async def test_successfully_drop_and_create_tables(self,
                                                       database_manager: DatabaseSessionManager,
                                                       session: AsyncSession) -> None:
        """Успешно удалить все таблицы и создать новые."""
        session.add(Sport(sport_id=1, sport_name='Sport 1', sport_url='/sport/'))
        await database_manager.created_db_tables()
        assert len((await session.execute(text('SELECT * FROM sport'))).fetchall()) == 0
        await session.commit()

    @pytest.mark.asyncio()
    async def test_engine_not_initialized(self) -> None:
        """Если engine не инициализирован, вызовите ошибку DatabaseNotInitError."""
        database_manager = DatabaseSessionManager()

        with pytest.raises(DatabaseNotInitError):
            await database_manager.created_db_tables()

    @pytest.mark.asyncio()
    async def test_dropping_tables_fails(self, mocker: MockerFixture,
                                         database_manager: DatabaseSessionManager,
                                         session: AsyncSession) -> None:
        """Если удаление таблиц не удалось, откат и исключение."""
        session.add(Sport(sport_id=1, sport_name='Sport 1', sport_url='/sport/'))
        await session.commit()
        mocker.patch('app.database.Base.metadata.drop_all', side_effect=Exception('Mock failure when dropping tables'))
        with pytest.raises(Exception, match='Mock failure when dropping tables'):
            await database_manager.created_db_tables()
        assert len((await session.execute(text('SELECT * FROM sport'))).fetchall()) == 1
        await session.commit()
