# """Общие тестовые функции для pytest."""
# from typing import TYPE_CHECKING
#
# from _pytest.nodes import Item
# import pytest
# from pytest_asyncio import is_async_test
#
# if TYPE_CHECKING:
#     from _pytest.mark import MarkDecorator
#
#
# def pytest_collection_modifyitems(items: list[Item]) -> None:
#     """Запуск всех тестовых функций в одном event loop."""
#     pytest_asyncio_tests = (item for item in items if is_async_test(item))
#     session_scope_marker: MarkDecorator = pytest.mark.asyncio(scope='session')
#     async_test: Item
#     for async_test in pytest_asyncio_tests:
#         async_test.add_marker(session_scope_marker, append=False)

# from typing import AsyncIterator
#
# import pytest
# from sqlalchemy.ext.asyncio import AsyncSession
#
# from app.betexplorer.crud import CRUDbetexplorer
# from app.config import settings
# from app.database import DatabaseSessionManager
#
#
# @pytest.mark.asyncio
# @pytest.fixture(scope="session", autouse=True)
# async def database_test() -> DatabaseSessionManager:
#     database: DatabaseSessionManager
#     async with DatabaseSessionManager() as database:
#         database.init(settings.SQLALCHEMY_TEST_DATABASE_URI, True)
#         await database.created_db_tables()
#         yield database
#
#
# @pytest.mark.asyncio
# @pytest.fixture(scope="function", autouse=True)
# async def create_tables(database_test: DatabaseSessionManager):
#     await database_test.created_db_tables()
#
#
# @pytest.mark.asyncio
# @pytest.fixture(scope="function", autouse=True)
# async def db_test():
#     return CRUDbetexplorer()
#
#
# @pytest.mark.asyncio
# @pytest.fixture(scope="function", autouse=True)
# async def session_test(database_test: DatabaseSessionManager) -> AsyncIterator[AsyncSession]:
#     async with database_test.get_session() as session:
#         yield session
