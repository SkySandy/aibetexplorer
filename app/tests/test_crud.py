"""Тестирование функции работы ч базой данных."""
import datetime
from typing import AsyncIterator

from _pytest.fixtures import SubRequest
from deepdiff import DeepDiff
import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.betexplorer.crud import (
    DATABASE_NOT_USE,
    DATABASE_READ_ONLY,
    DATABASE_WRITE_DATA,
    PARAMNATIVE,
    CRUDbetexplorer,
)
from app.betexplorer.models import Championship, Country, CountrySport, Match, Sport, Team
from app.betexplorer.schemas import (
    SPORTS,
    ChampionshipBetexplorer,
    ChampionshipStageBetexplorer,
    CountryBetexplorer,
    MatchBetexplorer,
    SportBetexplorer,
    SportType,
    TeamBetexplorer,
)
from app.config import settings
from app.database import DatabaseSessionManager


@pytest_asyncio.fixture(params=settings.SQLALCHEMY_TEST_DATABASE_URI)
async def database_manager(request: SubRequest) -> DatabaseSessionManager:
    """Создание класса DatabaseSessionManager для тестов."""
    database: DatabaseSessionManager
    async with DatabaseSessionManager() as database:
        database.init(request.param, echo=True)
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


@pytest_asyncio.fixture
async def crud(session: AsyncSession) -> CRUDbetexplorer:
    """Создание класса CRUDbetexplorer для тестов."""
    crd: CRUDbetexplorer = CRUDbetexplorer(DATABASE_WRITE_DATA)
    await crd.sports_insert_all(session, SPORTS)
    crd.save_database = DATABASE_NOT_USE
    return crd


@pytest.fixture()
def country_data_england() -> CountryBetexplorer:
    """Return answer to ultimate question."""
    return {
        'country_id': None,
        'country_url': '/football/england/',
        'country_name': 'England',
        'country_order': 0,
        'country_flag_url': '/res/images/flags/4x3/198.svg',
    }


@pytest.fixture()
def country_data_spain() -> CountryBetexplorer:
    """Return answer to ultimate question."""
    return {
        'country_id': None,
        'country_url': '/football/spain/',
        'country_name': 'Spain',
        'country_order': 1,
        'country_flag_url': '/res/images/flags/4x3/es.svg',
    }


@pytest.fixture()
def championship_data_england_1() -> ChampionshipBetexplorer:
    """Return answer to ultimate question."""
    return {
        'championship_id': None,
        'championship_url': '/football/england/premier-league/',
        'championship_name': 'Premier League',
        'championship_order': 0,
        'championship_years': '2023/2024',
    }


@pytest.fixture()
def team_data_england_1() -> TeamBetexplorer:
    """Return answer to ultimate question."""
    return {
        'team_id': None,
        'sport_id': SportType.FOOTBALL.value,
        'team_name': 'Alsenal',
        'team_full': 'Alsenal best',
        'team_url': '/football/england/team/',
        'team_country': 'England',
        'country_id': 1,
        'team_emblem': '/football/england/emblem/',
    }


@pytest.fixture()
def team_data_england_2() -> TeamBetexplorer:
    """Return answer to ultimate question."""
    return {
        'team_id': None,
        'sport_id': SportType.FOOTBALL.value,
        'team_name': 'Chelse',
        'team_full': 'Chelse free',
        'team_url': '/football/england/team/chell',
        'team_country': 'England',
        'country_id': 1,
        'team_emblem': '/football/england/emblem/chell',
    }


@pytest.fixture()
def match_data_1() -> MatchBetexplorer:
    """Return answer to ultimate question."""
    return {
        'match_id': None,
        'match_url': '/football/england/team/chell',
        'home_team_id': None,
        'home_team_name': '',
        'home_team_full': '',
        'home_team_url': '',
        'home_team_country': '',
        'home_team_emblem': '',
        'away_team_id': None,
        'away_team_name': '',
        'away_team_full': '',
        'away_team_url': '',
        'away_team_country': '',
        'away_team_emblem': '',
        'home_score': 3,
        'away_score': 1,
        'odds_1': 1.20,
        'odds_x': 3,
        'odds_2': 8,
        'game_date': datetime.datetime(2024, 1, 1, 19, 0),
        'score_stage': 'as',
        'score_stage_short': 'bs',
        'is_fixture': 0,
        'stage_name': 'First',
        'round_name': '12. Round',
        'round_number': 12,
        'score_halves': [
            {
                'half_number': 0,
                'home_score': 1,
                'away_score': 0,
            },
            {
                'half_number': 2,
                'home_score': 2,
                'away_score': 1,
            },
        ],
        'home_shooters': [
            {
                'event_time': '10',
                'overtime': 0,
                'player_name': 'Ivanov',
                'penalty_kick': '',
                'event_order': 0,
            },
            {
                'event_time': '50',
                'overtime': 1,
                'player_name': 'Petrov',
                'penalty_kick': '',
                'event_order': 1,
            },
        ],
        'away_shooters': [
            #     {
            #         'event_time': '51',
            #         'overtime': 0,
            #         'player_name': 'Sidorov',
            #         'penalty_kick': '',
            #         'event_order': 0,
            #     },
            #     {
            #         'event_time': '52',
            #         'overtime': 1,
            #         'player_name': 'Pronko',
            #         'penalty_kick': '',
            #         'event_order': 1,
            #     },
        ],
        'save_date': datetime.datetime(2024, 1, 1, 9, 0),
    }


@pytest.fixture()
def championship_stage_data() -> ChampionshipStageBetexplorer:
    """Return answer to ultimate question."""
    return {
        'stage_id': None,
        'stage_url': '/football/england/emblem/chell',
        'stage_name': 'First name',
        'stage_order': 0,
        'stage_current': True,
    }


@pytest.fixture()
def country_object() -> Country:
    """Return answer to ultimate question."""
    return Country(
        country_name='England',
        country_flag_url='/res/images/flags/4x3/198.svg',
        country_sport=[
            CountrySport(
                sport_id=SportType.FOOTBALL,
                country_url='/football/england/',
                country_order=0,
            ),
        ],
    )


class TestInit:
    """Тест инициализации."""

    def test_initialization_with_default_value(self) -> None:
        """Инициализирует класс со значением по умолчанию для параметра save_database."""
        crud = CRUDbetexplorer()
        assert crud.save_database == DATABASE_NOT_USE

    def test_initialization_with_provided_value(self) -> None:
        """Инициализирует класс с указанным значением для параметра save_database."""
        save_database = DATABASE_WRITE_DATA
        crud = CRUDbetexplorer(save_database)
        assert crud.save_database == DATABASE_WRITE_DATA


class TestPARAMNATIVE:
    """Тест нативного типа."""

    def test_literal_processor_returns_callable(self, database_manager: DatabaseSessionManager) -> None:
        """Тестируем с разными параметрами функции."""
        param_native = PARAMNATIVE()
        assert param_native.cache_ok is True
        assert param_native.should_evaluate_none is True

        literal_processor = param_native.literal_processor(database_manager._engine.dialect)  # noqa: SLF001

        assert callable(literal_processor)
        assert isinstance(literal_processor('test'), str)

        result = literal_processor(None)
        assert result == ''

        input_string = 'test'
        result = literal_processor(input_string)
        assert result == input_string

        result = literal_processor(['test1', 'test2', 'test3'])
        assert result == 'test1, test2, test3'

        with pytest.raises(TypeError):
            literal_processor(123)

        result = literal_processor(['test1', 123, 'test2', True, 'test3'])
        assert result == 'test1, test2, test3'


class TestGetList:
    """Тест выполнения команды и возврата значения в виде списка."""

    @pytest.mark.asyncio()
    async def test_returns_list_of_dictionaries(self, crud: CRUDbetexplorer, session: AsyncSession) -> None:
        """Возврат списка."""
        crud.save_database = DATABASE_WRITE_DATA
        result = await crud.get_list(session, select(Sport))
        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, dict)

    @pytest.mark.asyncio()
    async def test_returns_empty_list(self, crud: CRUDbetexplorer, session: AsyncSession) -> None:
        """Возвращает пустой список."""
        crud.save_database = DATABASE_WRITE_DATA
        command = select(Country).where(Country.country_id == -1)
        result = await crud.get_list(session, command)
        assert result == []

    @pytest.mark.asyncio()
    async def test_returns_none_when_save_database_not_use(self, crud: CRUDbetexplorer, session: AsyncSession) -> None:
        """Возвращает None, если для save_database установлено значение DATABASE_NOT_USE."""
        command = select(Country)
        result = await crud.get_list(session, command)
        assert result is None

    @pytest.mark.asyncio()
    async def test_contains_all_selected_columns(self, crud: CRUDbetexplorer, session: AsyncSession) -> None:
        """Проверка названия колонок."""
        crud.save_database = DATABASE_WRITE_DATA
        command = select(Sport)
        result = await crud.get_list(session, command)
        columns = [str(column) for column in command.columns.keys()]  # noqa: SIM118
        for item in result:
            assert all(column in item for column in columns)


class TestGetDict:
    """Класс для тестирования возврата словарем."""

    @pytest.mark.asyncio()
    async def test_returns_dictionary_when_row_found(self, crud: CRUDbetexplorer, session: AsyncSession) -> None:
        """Возвращает словарь, когда в базе данных найдена строка."""
        crud.save_database = DATABASE_WRITE_DATA
        command = select(Sport).where(Sport.sport_id == 1)
        result = await crud.get_dict(session, command)
        assert isinstance(result, dict)

    @pytest.mark.asyncio()
    async def test_returns_none_when_no_row_found(self, crud: CRUDbetexplorer, session: AsyncSession) -> None:
        """Возвращает None, если в базе данных не найдена строка."""
        crud.save_database = DATABASE_WRITE_DATA
        command = select(Sport).where(Sport.sport_id == -1)
        result = await crud.get_dict(session, command)
        assert result is None

    @pytest.mark.asyncio()
    async def test_returns_none_when_save_database_not_use(self, crud: CRUDbetexplorer, session: AsyncSession) -> None:
        """Возвращает None, если для save_database установлено значение DATABASE_NOT_USE."""
        crud.save_database = DATABASE_NOT_USE
        command = select(Sport).where(Sport.sport_id == 1)
        result = await crud.get_dict(session, command)
        assert result is None

    @pytest.mark.asyncio()
    async def test_returns_dictionary_with_correct_keys_and_values_multiple_columns(self, crud: CRUDbetexplorer,
                                                                                    session: AsyncSession) -> None:
        """Возвращает словарь с правильными ключами и значениями, когда запрос возвращает несколько столбцов."""
        crud.save_database = DATABASE_WRITE_DATA
        command = select(Sport).where(Sport.sport_id == 1)
        result = await crud.get_dict(session, command)
        assert isinstance(result, dict)
        assert 'sport_id' in result
        assert 'sport_name' in result
        assert 'sport_url' in result
        assert result['sport_id'] == 1
        assert result['sport_name'] == 'Football'
        assert result['sport_url'] == '/football/'


class TestAnalyzeTables:
    """Тест оператора ANALYZE."""

    @pytest.mark.asyncio()
    async def test_analyze_tables(self, crud: CRUDbetexplorer, session: AsyncSession) -> None:
        """Тест обновления статистики."""
        crud.save_database = DATABASE_WRITE_DATA
        await crud.analyze_tables(session, (Country, CountrySport))
        assert not session.in_transaction()

        await crud.analyze_tables(session)
        assert not session.in_transaction()

        await crud.analyze_tables(session, Country)
        assert not session.in_transaction()

        await crud.analyze_tables(session, [])
        assert not session.in_transaction()

        await crud.analyze_tables(session, '')
        assert not session.in_transaction()


class TestHasUncommittedChanges:
    """Тест класса проверки измененных объектов в сессии."""

    @pytest.mark.asyncio()
    async def test_no_uncommitted_changes(self, crud: CRUDbetexplorer, session: AsyncSession) -> None:
        """Возвращает False, если в сеансе нет незафиксированных изменений."""
        result = crud.has_uncommitted_changes(session)
        assert result == False  # noqa: E712

    @pytest.mark.asyncio()
    async def test_new_objects_in_session(self, session: AsyncSession) -> None:
        """Возвращает True, когда в сеансе появляются новые объекты."""
        crud: CRUDbetexplorer = CRUDbetexplorer(DATABASE_WRITE_DATA)
        session.add(Sport(sport_id=1, sport_name='Football', sport_url='football.com'))
        result = crud.has_uncommitted_changes(session)
        assert result == True  # noqa: E712

    @pytest.mark.asyncio()
    async def test_deleted_objects_in_session(self, crud: CRUDbetexplorer, session: AsyncSession) -> None:
        """Возвращает True, если в сеансе есть удаленные объекты."""
        crud.save_database = DATABASE_WRITE_DATA
        result = (await session.get(Sport, 1))
        await session.delete(result)
        result = crud.has_uncommitted_changes(session)
        assert result == True  # noqa: E712

    @pytest.mark.asyncio()
    async def test_modified_objects_in_session(self, session: AsyncSession) -> None:
        """Возвращает True, если в сеансе есть измененные объекты."""
        crud: CRUDbetexplorer = CRUDbetexplorer(DATABASE_WRITE_DATA)
        sport = Sport(sport_id=1, sport_name='Football', sport_url='football.com')
        session.add(sport)
        await session.commit()
        sport.sport_name = 'Soccer'
        result = crud.has_uncommitted_changes(session)
        assert result == True  # noqa: E712

    @pytest.mark.asyncio()
    async def test_save_database_not_use(self, session: AsyncSession) -> None:
        """Возвращает False, когда save_database имеет значение DATABASE_NOT_USE."""
        crud = CRUDbetexplorer(save_database=DATABASE_NOT_USE)
        sport = Sport(sport_id=1, sport_name='Football', sport_url='football.com')
        session.add(sport)
        result = crud.has_uncommitted_changes(session)
        assert result == False  # noqa: E712


class TestSportsInsertAll:
    """Тестирование добавления видов спорта."""

    @pytest.mark.asyncio()
    async def test_adds_new_sports_to_database(self, session: AsyncSession) -> None:
        """Добавляет новые виды спорта в базу данных."""
        crud: CRUDbetexplorer = CRUDbetexplorer(DATABASE_WRITE_DATA)
        await crud.sports_insert_all(session, SPORTS)
        sport_res: list[SportBetexplorer] = await crud.get_list(session, select(Sport).order_by(Sport.sport_id))
        assert not DeepDiff(SPORTS, sport_res)

    @pytest.mark.asyncio()
    async def test_updates_existing_sports_in_database(self, session: AsyncSession) -> None:
        """Обновляет существующие виды спорта в базе данных."""
        crud: CRUDbetexplorer = CRUDbetexplorer(DATABASE_WRITE_DATA)
        existing_sports = [
            Sport(
                sport_id=1,
                sport_name='Football',
                sport_url='https://www.example.com/football',
            ),
            Sport(
                sport_id=2,
                sport_name='Basketball',
                sport_url='https://www.example.com/basketball',
            ),
            Sport(
                sport_id=3,
                sport_name='Tennis',
                sport_url='https://www.example.com/tennis',
            )
        ]
        session.add_all(existing_sports)
        await session.commit()
        sports = [
            {
                'sport_id': 1,
                'sport_name': 'Soccer',
                'sport_url': 'https://www.example.com/soccer',
            },
            {
                'sport_id': 2,
                'sport_name': 'Basketball',
                'sport_url': 'https://www.example.com/basketball',
            },
            {
                'sport_id': 3,
                'sport_name': 'Tennis',
                'sport_url': 'https://www.example.com/tennis',
            }
        ]
        await crud.sports_insert_all(session, sports)
        sport_res: list[SportBetexplorer] = await crud.get_list(session, select(Sport).order_by(Sport.sport_id))
        assert not DeepDiff(sports, sport_res)

    @pytest.mark.asyncio()
    async def test_does_nothing_if_save_database_not_use(self, session: AsyncSession) -> None:
        """Ничего не делает, если для save_database установлено значение DATABASE_NOT_USE."""
        sports = [
            {
                'sport_id': 1,
                'sport_name': 'Football',
                'sport_url': 'https://www.example.com/football',
            },
            {
                'sport_id': 2,
                'sport_name': 'Basketball',
                'sport_url': 'https://www.example.com/basketball',
            },
            {
                'sport_id': 3,
                'sport_name': 'Tennis',
                'sport_url': 'https://www.example.com/tennis',
            }
        ]
        crud = CRUDbetexplorer(save_database=DATABASE_NOT_USE)
        await crud.sports_insert_all(session, sports)
        result = await session.execute(select(Sport).order_by(Sport.sport_id))
        inserted_sports = result.scalars().all()
        assert len(inserted_sports) == 0

    @pytest.mark.asyncio()
    async def test_does_not_modify_database_if_no_new_sports_provided(self, session: AsyncSession) -> None:
        """Не изменяет базу данных, если не указаны новые виды спорта."""
        existing_sports = [
            {
                'sport_id': 1,
                'sport_name': 'Football',
                'sport_url': 'https://www.example.com/football',
            },
            {
                'sport_id': 2,
                'sport_name': 'Basketball',
                'sport_url': 'https://www.example.com/basketball',
            },
            {
                'sport_id': 3,
                'sport_name': 'Tennis',
                'sport_url': 'https://www.example.com/tennis',
            }
        ]
        crud = CRUDbetexplorer(DATABASE_WRITE_DATA)
        await crud.sports_insert_all(session, existing_sports)
        sports = []
        await crud.sports_insert_all(session, sports)

        # Then
        sport_res: list[SportBetexplorer] = await crud.get_list(session, select(Sport).order_by(Sport.sport_id))
        assert not DeepDiff(existing_sports, sport_res)

    @pytest.mark.asyncio()
    async def test_does_not_modify_database_if_no_sports_provided(self, session: AsyncSession) -> None:
        """Не изменяет базу данных, если виды спорта не указаны."""
        sports = []
        crud = CRUDbetexplorer(DATABASE_WRITE_DATA)
        await crud.sports_insert_all(session, sports)
        result = await session.execute(select(Sport).order_by(Sport.sport_id))
        inserted_sports = result.scalars().all()
        assert len(inserted_sports) == 0

    @pytest.mark.asyncio()
    async def test_does_not_add_duplicate_sports(self, session: AsyncSession) -> None:
        """Не добавляет дубликаты видов спорта в базу данных."""
        existing_sports = [
            {
                'sport_id': 1,
                'sport_name': 'Football',
                'sport_url': 'https://www.example.com/football',
            },
            {
                'sport_id': 2,
                'sport_name': 'Basketball',
                'sport_url': 'https://www.example.com/basketball',
            },
            {
                'sport_id': 3,
                'sport_name': 'Tennis',
                'sport_url': 'https://www.example.com/tennis',
            }
        ]
        crud = CRUDbetexplorer(DATABASE_WRITE_DATA)
        await crud.sports_insert_all(session, existing_sports)

        sports = [
            {
                'sport_id': 1,
                'sport_name': 'Football',
                'sport_url': 'https://www.example.com/football',
            },
            {
                'sport_id': 4,
                'sport_name': 'Volleyball',
                'sport_url': 'https://www.example.com/volleyball',
            },
            {
                'sport_id': 5,
                'sport_name': 'Hockey',
                'sport_url': 'https://www.example.com/hockey',
            }
        ]

        await crud.sports_insert_all(session, sports)

        sports_all = [
            {
                'sport_id': 1,
                'sport_name': 'Football',
                'sport_url': 'https://www.example.com/football',
            },
            {
                'sport_id': 2,
                'sport_name': 'Basketball',
                'sport_url': 'https://www.example.com/basketball',
            },
            {
                'sport_id': 3,
                'sport_name': 'Tennis',
                'sport_url': 'https://www.example.com/tennis',
            },
            {
                'sport_id': 4,
                'sport_name': 'Volleyball',
                'sport_url': 'https://www.example.com/volleyball',
            },
            {
                'sport_id': 5,
                'sport_name': 'Hockey',
                'sport_url': 'https://www.example.com/hockey',
            }
        ]

        sport_res: list[SportBetexplorer] = await crud.get_list(session, select(Sport).order_by(Sport.sport_id))
        assert not DeepDiff(sports_all, sport_res)

    @pytest.mark.asyncio()
    async def test_does_not_add_duplicate_all_sports(self, session: AsyncSession) -> None:
        """Не добавляет дубликаты видов спорта в базу данных второй раз."""
        existing_sports = [
            {
                'sport_id': 1,
                'sport_name': 'Football',
                'sport_url': 'https://www.example.com/football',
            },
            {
                'sport_id': 2,
                'sport_name': 'Basketball',
                'sport_url': 'https://www.example.com/basketball',
            },
            {
                'sport_id': 3,
                'sport_name': 'Tennis',
                'sport_url': 'https://www.example.com/tennis',
            }
        ]
        crud = CRUDbetexplorer(DATABASE_WRITE_DATA)
        await crud.sports_insert_all(session, existing_sports)
        await crud.sports_insert_all(session, existing_sports)
        sport_res: list[SportBetexplorer] = await crud.get_list(session, select(Sport).order_by(Sport.sport_id))
        assert not DeepDiff(existing_sports, sport_res)


class TestCountryInsertAll:
    """Тест добавления списка стран."""

    @pytest.mark.asyncio()
    async def test_add_countries_to_database(self, crud: CRUDbetexplorer, session: AsyncSession) -> None:
        """Добавляет страны в базу данных, если save_database отличается от DATABASE_NOT_USE."""
        crud.save_database = DATABASE_WRITE_DATA
        countries = [
            {
                'country_id': None,
                'country_url': 'https://www.example.com/england',
                'country_name': 'England',
                'country_order': 1,
                'country_flag_url': 'https://www.example.com/flags/england.png',
            },
            {
                'country_id': None,
                'country_url': 'https://www.example.com/spain',
                'country_name': 'Spain',
                'country_order': 2,
                'country_flag_url': 'https://www.example.com/flags/spain.png',
            },
        ]

        await crud.country_insert_all(session, SportType.FOOTBALL, countries)
        command = text("""
                SELECT country.country_id, country.country_name, country.country_flag_url,
                       country_sport.country_url, country_sport.country_order 
                FROM country
                   LEFT OUTER JOIN country_sport ON country.country_id = country_sport.country_id
                                                AND country_sport.sport_id = :sport_id
        """).bindparams(sport_id=SportType.FOOTBALL.value)
        result = await crud.get_list(session, command)
        assert not DeepDiff(countries, result)

    @pytest.mark.asyncio()
    async def test_update_existing_countries(self, crud: CRUDbetexplorer, session: AsyncSession) -> None:
        """Обновляет существующие страны в базе данных новой информацией."""
        crud.save_database = DATABASE_WRITE_DATA
        countries = [
            {
                'country_id': None,
                'country_url': 'https://www.example.com/england',
                'country_name': 'England',
                'country_order': 1,
                'country_flag_url': 'https://www.example.com/flags/england.png',
            },
            {
                'country_id': None,
                'country_url': 'https://www.example.com/spain',
                'country_name': 'Spain',
                'country_order': 2,
                'country_flag_url': 'https://www.example.com/flags/spain.png',
            },
        ]
        await crud.country_insert_all(session, SportType.FOOTBALL, countries)

        countries_update = [
            {
                'country_id': None,
                'country_url': 'https://www.example.com/england_update',
                'country_name': 'England',
                'country_order': 5,
                'country_flag_url': 'https://www.example.com/flags/england.png_2',
            },
            {
                'country_id': None,
                'country_url': 'https://www.example.com/spain_update',
                'country_name': 'Spain',
                'country_order': 9,
                'country_flag_url': 'https://www.example.com/flags/spain.png_4',
            },
        ]
        await crud.country_insert_all(session, SportType.FOOTBALL, countries_update)

        command = text("""
                SELECT country.country_id, country.country_name, country.country_flag_url,
                       country_sport.country_url, country_sport.country_order 
                FROM country
                   LEFT OUTER JOIN country_sport ON country.country_id = country_sport.country_id
                                                AND country_sport.sport_id = :sport_id
        """).bindparams(sport_id=SportType.FOOTBALL.value)
        result = await crud.get_list(session, command)
        assert not DeepDiff(countries_update, result)

    @pytest.mark.asyncio()
    async def test_populate_country_id_existing_countries(self, crud: CRUDbetexplorer, session: AsyncSession) -> None:
        """Заполняет Country_id для стран, которые уже есть в базе данных."""
        crud.save_database = DATABASE_WRITE_DATA
        countries = [
            {
                'country_id': None,
                'country_url': 'https://www.example.com/england',
                'country_name': 'England',
                'country_order': 1,
                'country_flag_url': 'https://www.example.com/flags/england.png',
            },
            {
                'country_id': None,
                'country_url': 'https://www.example.com/spain',
                'country_name': 'Spain',
                'country_order': 2,
                'country_flag_url': 'https://www.example.com/flags/spain.png',
            },
        ]
        await crud.country_insert_all(session, SportType.FOOTBALL, countries)
        countries_exists = [
            {
                'country_id': None,
                'country_url': 'https://www.example.com/england',
                'country_name': 'England',
                'country_order': 1,
                'country_flag_url': 'https://www.example.com/flags/england.png',
            },
            {
                'country_id': None,
                'country_url': 'https://www.example.com/spain',
                'country_name': 'Spain',
                'country_order': 2,
                'country_flag_url': 'https://www.example.com/flags/spain.png',
            },
        ]
        await crud.country_insert_all(session, SportType.FOOTBALL, countries_exists)
        assert not DeepDiff(countries, countries_exists)

    @pytest.mark.asyncio()
    async def test_does_nothing_when_save_database_is_not_use(self, crud: CRUDbetexplorer,
                                                              session: AsyncSession) -> None:
        """Ничего не делает, если save_database имеет значение DATABASE_NOT_USE."""
        sport_id = SportType.FOOTBALL
        countries = [
            {
                'country_id': None,
                'country_url': 'https://www.example.com/england',
                'country_name': 'England',
                'country_order': 1,
                'country_flag_url': 'https://www.example.com/flags/england.png',
            },
            {
                'country_id': None,
                'country_url': 'https://www.example.com/spain',
                'country_name': 'Spain',
                'country_order': 2,
                'country_flag_url': 'https://www.example.com/flags/spain.png',
            },
        ]
        await crud.country_insert_all(session, sport_id, countries)

        command = text("""
                SELECT country.country_id, country.country_name, country.country_flag_url,
                       country_sport.country_url, country_sport.country_order 
                FROM country
                   LEFT OUTER JOIN country_sport ON country.country_id = country_sport.country_id
                                                AND country_sport.sport_id = :sport_id
        """).bindparams(sport_id=SportType.FOOTBALL.value)
        crud.save_database = DATABASE_WRITE_DATA
        result = await crud.get_list(session, command)
        assert result == []

    @pytest.mark.asyncio()
    async def test_does_not_modify_database_when_read_only(self, crud: CRUDbetexplorer, session: AsyncSession) -> None:
        """Не изменяет базу данных, если save_database имеет значение DATABASE_READ_ONLY.."""
        crud.save_database = DATABASE_WRITE_DATA
        sport_id = SportType.FOOTBALL
        countries = [
            {
                'country_id': None,
                'country_name': 'Country1',
                'country_flag_url': 'flag1.png',
                'country_url': 'url1',
                'country_order': 1,
            },
            {
                'country_id': None,
                'country_name': 'Country2',
                'country_flag_url': 'flag2.png',
                'country_url': 'url2',
                'country_order': 2,
            },
        ]
        await crud.country_insert_all(session, sport_id, countries)
        crud.save_database = DATABASE_READ_ONLY
        countries_read = [
            {
                'country_id': None,
                'country_name': 'Country1',
                'country_flag_url': 'flag1.png',
                'country_url': 'url1',
                'country_order': 1,
            },
            {
                'country_id': None,
                'country_name': 'Country2',
                'country_flag_url': 'flag2.png',
                'country_url': 'url2',
                'country_order': 2,
            },
        ]
        await crud.country_insert_all(session, sport_id, countries_read)
        command = text("""
                SELECT country.country_id, country.country_name, country.country_flag_url,
                       country_sport.country_url, country_sport.country_order 
                FROM country
                   LEFT OUTER JOIN country_sport ON country.country_id = country_sport.country_id
                                                AND country_sport.sport_id = :sport_id
        """).bindparams(sport_id=SportType.FOOTBALL.value)
        crud.save_database = DATABASE_WRITE_DATA
        result = await crud.get_list(session, command)
        assert not DeepDiff(result, countries_read)


class TestInsertChampionship:
    """Тестирование чемпионата."""

    @pytest.mark.asyncio()
    async def test_insert_new_championship_valid_parameters(self, crud: CRUDbetexplorer, session: AsyncSession) -> None:
        """Добавить новый чемпионат с допустимыми параметрами и вернуть championship_id."""
        crud.save_database = DATABASE_WRITE_DATA
        sport_id = SportType.FOOTBALL
        countries = [
            {
                'country_id': None,
                'country_name': 'Country1',
                'country_flag_url': 'flag1.png',
                'country_url': 'url1',
                'country_order': 1,
            },
        ]
        await crud.country_insert_all(session, sport_id, countries)
        country_id: int = countries[0]['country_id']
        championships = [{
            'championship_id': None,
            'championship_url': 'https://example.com/championship',
            'championship_name': 'Example Championship',
            'championship_order': 1,
            'championship_years': '2022-2023',
        }]
        await crud.insert_championship(session, sport_id, country_id, championships)
        inserted_championship = select(Championship.championship_id, Championship.championship_url,
                                       Championship.championship_name, Championship.championship_order,
                                       Championship.championship_years).where(
            Championship.country_id == country_id,
            Championship.sport_id == sport_id.value,
            Championship.championship_name == championships[0]['championship_name'],
            Championship.championship_years == championships[0]['championship_years'],
        )
        result = await crud.get_dict(session, inserted_championship)
        assert not DeepDiff(result, championships[0])

    @pytest.mark.asyncio()
    async def test_return_existing_championship_id(self, crud: CRUDbetexplorer, session: AsyncSession) -> None:
        """Вернуть идентификатор существующего чемпионата."""
        crud.save_database = DATABASE_WRITE_DATA
        sport_id = SportType.FOOTBALL
        countries = [
            {
                'country_id': None,
                'country_name': 'Country1',
                'country_flag_url': 'flag1.png',
                'country_url': 'url1',
                'country_order': 1,
            },
        ]
        await crud.country_insert_all(session, sport_id, countries)
        country_id: int = countries[0]['country_id']
        championship = [{
            'championship_id': None,
            'championship_url': 'https://example.com/championship',
            'championship_name': 'Example Championship',
            'championship_order': 1,
            'championship_years': '2022-2023',
        }]
        await crud.insert_championship(session, sport_id, country_id, championship)
        championship_exist = [{
            'championship_id': None,
            'championship_url': 'https://example.com/championship',
            'championship_name': 'Example Championship',
            'championship_order': 1,
            'championship_years': '2022-2023',
        }]
        await crud.insert_championship(session, sport_id, country_id, championship_exist)
        assert championship[0]['championship_id'] == championship_exist[0]['championship_id']

    @pytest.mark.asyncio()
    async def test_return_none_save_database_not_use(self, crud: CRUDbetexplorer, session: AsyncSession) -> None:
        """Вернуть None, если для атрибута save_database установлено значение DATABASE_NOT_USE."""
        crud.save_database = DATABASE_NOT_USE
        sport_id = SportType.FOOTBALL
        countries = [
            {
                'country_id': None,
                'country_name': 'Country1',
                'country_flag_url': 'flag1.png',
                'country_url': 'url1',
                'country_order': 1,
            },
        ]
        await crud.country_insert_all(session, sport_id, countries)
        country_id = countries[0]['country_id']
        championship = [{
            'championship_id': None,
            'championship_url': 'https://example.com/championship',
            'championship_name': 'Example Championship',
            'championship_order': 1,
            'championship_years': '2022-2023',
        }]
        await crud.insert_championship(session, sport_id, country_id, championship)
        assert championship[0]['championship_id'] is None

    @pytest.mark.asyncio()
    async def test_update_existing_championship(self, crud: CRUDbetexplorer, session: AsyncSession) -> None:
        """Обновить существующий чемпионат для данной страны и вида спорта."""
        crud.save_database = DATABASE_WRITE_DATA

        sport_id = SportType.FOOTBALL
        countries = [
            {
                'country_id': None,
                'country_name': 'Country1',
                'country_flag_url': 'flag1.png',
                'country_url': 'url1',
                'country_order': 1,
            },
        ]
        await crud.country_insert_all(session, sport_id, countries)
        country_id: int = countries[0]['country_id']

        championships = [
            {
                'championship_id': None,
                'championship_name': 'Premier League',
                'championship_url': 'https://example.com/premier-league-updated',
                'championship_order': 1,
                'championship_years': '2021-2022',
            },
        ]

        # Insert an existing championship
        await crud.insert_championship(session, sport_id, country_id, championships)

        # Update the existing championship
        championships[0]['championship_url'] = 'https://example.com/premier-league-updated2'
        await crud.insert_championship(session, sport_id, country_id, championships)

        # Assert that the championship was updated correctly
        result = await crud.get_list(session, select(Championship).where(
            Championship.country_id == country_id,
            Championship.sport_id == sport_id.value,
        ))
        assert len(result) == 1
        assert result[0]['championship_name'] == 'Premier League'
        assert result[0]['championship_url'] == 'https://example.com/premier-league-updated2'
        assert result[0]['championship_order'] == 1
        assert result[0]['championship_years'] == '2021-2022'

    @pytest.mark.asyncio()
    async def test_insert_championship_existing_championships(self, crud: CRUDbetexplorer,
                                                              session: AsyncSession) -> None:
        """Вставить список чемпионатов, добавить еще чемпионаты в базу данных."""
        crud.save_database = DATABASE_WRITE_DATA

        sport_id = SportType.FOOTBALL
        countries = [
            {
                'country_id': None,
                'country_name': 'Country1',
                'country_flag_url': 'flag1.png',
                'country_url': 'url1',
                'country_order': 1,
            },
        ]
        await crud.country_insert_all(session, sport_id, countries)
        country_id: int = countries[0]['country_id']

        sport_id = SportType.FOOTBALL
        championships = [
            {
                'championship_id': None,
                'championship_name': 'Premier League',
                'championship_url': 'https://example.com/premier-league',
                'championship_order': 1,
                'championship_years': '2021-2022',
            },
            {
                'championship_id': None,
                'championship_name': 'La Liga',
                'championship_url': 'https://example.com/la-liga',
                'championship_order': 2,
                'championship_years': '2021-2022',
            },
        ]

        # Insert existing championships
        await crud.insert_championship(session, sport_id, country_id, championships)

        # Insert new championships
        new_championships = [
            {
                'championship_id': None,
                'championship_name': 'Bundesliga',
                'championship_url': 'https://example.com/bundesliga',
                'championship_order': 3,
                'championship_years': '2021-2022',
            },
            {
                'championship_id': None,
                'championship_name': 'Serie A',
                'championship_url': 'https://example.com/serie-a',
                'championship_order': 4,
                'championship_years': '2021-2022',
            },
        ]
        await crud.insert_championship(session, sport_id, country_id, new_championships)

        # Assert that all championships were inserted correctly
        result = await crud.get_list(session, select(Championship).where(
            Championship.country_id == country_id,
            Championship.sport_id == sport_id.value,
        ).order_by(Championship.championship_id))
        assert len(result) == 4
        assert result[0]['championship_name'] == 'Premier League'
        assert result[0]['championship_url'] == 'https://example.com/premier-league'
        assert result[0]['championship_order'] == 1
        assert result[0]['championship_years'] == '2021-2022'
        assert result[1]['championship_name'] == 'La Liga'
        assert result[1]['championship_url'] == 'https://example.com/la-liga'
        assert result[1]['championship_order'] == 2
        assert result[1]['championship_years'] == '2021-2022'
        assert result[2]['championship_name'] == 'Bundesliga'
        assert result[2]['championship_url'] == 'https://example.com/bundesliga'
        assert result[2]['championship_order'] == 3
        assert result[2]['championship_years'] == '2021-2022'
        assert result[3]['championship_name'] == 'Serie A'
        assert result[3]['championship_url'] == 'https://example.com/serie-a'
        assert result[3]['championship_order'] == 4
        assert result[3]['championship_years'] == '2021-2022'

    @pytest.mark.asyncio()
    async def test_get_championship_read_only(self, crud: CRUDbetexplorer, session: AsyncSession) -> None:
        """Получить идентификаторы чемпионатов, при базе данных только для чтения."""
        crud.save_database = DATABASE_WRITE_DATA
        sport_id = SportType.FOOTBALL
        countries = [
            {
                'country_id': None,
                'country_name': 'Country1',
                'country_flag_url': 'flag1.png',
                'country_url': 'url1',
                'country_order': 1,
            },
        ]
        await crud.country_insert_all(session, sport_id, countries)
        country_id: int = countries[0]['country_id']

        championships = [
            {
                'championship_id': None,
                'championship_name': 'Premier League',
                'championship_url': 'https://example.com/premier-league',
                'championship_order': 1,
                'championship_years': '2021-2022',
            },
            {
                'championship_id': None,
                'championship_name': 'La Liga',
                'championship_url': 'https://example.com/la-liga',
                'championship_order': 2,
                'championship_years': '2021-2022',
            },
        ]

        await crud.insert_championship(session, sport_id, country_id, championships)
        crud.save_database = DATABASE_READ_ONLY
        championships2 = [
            {
                'championship_id': None,
                'championship_name': 'Premier League',
                'championship_url': 'https://example.com/premier-league',
                'championship_order': 1,
                'championship_years': '2021-2022',
            },
            {
                'championship_id': None,
                'championship_name': 'La Liga',
                'championship_url': 'https://example.com/la-liga',
                'championship_order': 2,
                'championship_years': '2021-2022',
            },
        ]
        await crud.insert_championship(session, sport_id, country_id, championships2)

        # Assert that the championships were inserted correctly
        result = await crud.get_list(session, select(Championship).where(
            Championship.country_id == country_id,
            Championship.sport_id == sport_id.value,
        ).order_by(Championship.championship_id))
        assert len(result) == 2
        assert result[0]['championship_id'] == championships2[0]['championship_id']
        assert result[0]['championship_name'] == 'Premier League'
        assert result[0]['championship_url'] == 'https://example.com/premier-league'
        assert result[0]['championship_order'] == 1
        assert result[0]['championship_years'] == '2021-2022'
        assert result[1]['championship_id'] == championships2[1]['championship_id']
        assert result[1]['championship_name'] == 'La Liga'
        assert result[1]['championship_url'] == 'https://example.com/la-liga'
        assert result[1]['championship_order'] == 2
        assert result[1]['championship_years'] == '2021-2022'


class TestTeamMerge:
    """Тест добавление и изменения команды."""

    @pytest.mark.asyncio()
    async def test_insert_new_team_successfully(self, crud: CRUDbetexplorer, session: AsyncSession) -> None:
        """Успешно вставьте новую команду."""
        crud.save_database = DATABASE_WRITE_DATA
        sport_id = SportType.FOOTBALL
        countries = [
            {
                'country_id': None,
                'country_name': 'Country1',
                'country_flag_url': 'flag1.png',
                'country_url': 'url1',
                'country_order': 1,
            },
        ]
        await crud.country_insert_all(session, sport_id, countries)
        country_id: int = countries[0]['country_id']

        team: TeamBetexplorer = {
            'team_id': None,
            'sport_id': sport_id.value,
            'country_id': country_id,
            'team_country': 'England',
            'team_name': 'Team A',
            'team_full': 'Team A FC',
            'team_url': 'https://www.teamA.com',
            'team_emblem': 'https://www.teamA.com/emblem.png',
            'download_date': datetime.datetime(year=2021, month=1, day=1),
            'save_date': datetime.datetime(year=2022, month=2, day=2),
        }
        team_id = await crud.team_merge(session, team)
        team_id = await crud.team_merge(session, team)
        assert team_id is not None
        assert team_id == team['team_id']
        async with session.begin():
            team_new = (await session.scalar(
                select(Team.team_id).where(
                    Team.team_url == team['team_url'],
                ),
            ))
            assert team_id == team_new

        team_2 = team['team_id']
        team['team_id'] = None
        team_id_2 = await crud.team_merge(session, team)
        assert team_2 == team['team_id']
        assert team_id_2 == team_id


    @pytest.mark.asyncio()
    async def test_update_existing_team_successfully(self, crud: CRUDbetexplorer, session: AsyncSession) -> None:
        """Успешно обновляет существующую команду."""
        crud.save_database = DATABASE_WRITE_DATA
        sport_id = SportType.FOOTBALL
        countries = [
            {
                'country_id': None,
                'country_name': 'Country1',
                'country_flag_url': 'flag1.png',
                'country_url': 'url1',
                'country_order': 1,
            },
        ]
        await crud.country_insert_all(session, sport_id, countries)
        country_id: int = countries[0]['country_id']

        team: TeamBetexplorer = {
            'team_id': None,
            'sport_id': sport_id.value,
            'country_id': country_id,
            'team_country': 'England',
            'team_name': 'Team A',
            'team_full': 'Team A FC',
            'team_url': 'https://www.teamA.com',
            'team_emblem': 'https://www.teamA.com/emblem.png',
            'download_date': datetime.datetime(year=2021, month=1, day=1),
            'save_date': datetime.datetime(year=2022, month=2, day=2),
        }

        team_id = await crud.team_merge(session, team)

        assert team_id is not None

        updated_team_info: TeamBetexplorer = {
            'team_id': None,
            'sport_id': sport_id.value,
            'country_id': country_id,
            'team_name': 'Team A',
            'team_country': 'England',
            'team_full': 'Team A FC',
            'team_url': 'https://www.teamA.com',
            'team_emblem': 'https://www.teamA.com/new_emblem.png',
            'download_date': datetime.datetime(year=2021, month=1, day=1),
            'save_date': datetime.datetime(year=2022, month=2, day=2),
        }

        updated_team_id = await crud.team_merge(session, updated_team_info)

        assert updated_team_id == team_id

    @pytest.mark.asyncio()
    async def test_save_database_not_use(self, crud: CRUDbetexplorer, session: AsyncSession) -> None:
        """Для Save_database установлено значение DATABASE_NOT_USE, возвратите None."""
        """Успешно обновляет существующую команду."""
        crud.save_database = DATABASE_WRITE_DATA
        sport_id = SportType.FOOTBALL
        countries = [
            {
                'country_id': None,
                'country_name': 'Country1',
                'country_flag_url': 'flag1.png',
                'country_url': 'url1',
                'country_order': 1,
            },
        ]
        await crud.country_insert_all(session, sport_id, countries)
        country_id: int = countries[0]['country_id']

        team_info = {
            'team_id': None,
            'sport_id': sport_id.value,
            'country_id': country_id,
            'team_name': 'Team A',
            'team_full': 'Team A FC',
            'team_country': 'England',
            'team_url': 'https://www.teamA.com',
            'team_emblem': 'https://www.teamA.com/emblem.png',
            'download_date': datetime.datetime(year=2021, month=1, day=1),
            'save_date': datetime.datetime(year=2022, month=2, day=2),
        }

        crud.save_database = DATABASE_NOT_USE
        team_id = await crud.team_merge(session, team_info)

        assert team_id is None

    @pytest.mark.asyncio()
    async def test_save_database_read_only(self, crud: CRUDbetexplorer, session: AsyncSession) -> None:
        """Для DATABASE_READ_ONLY, вернуть team_id, если команда существует, в противном случае — None."""
        crud.save_database = DATABASE_WRITE_DATA
        sport_id = SportType.FOOTBALL
        countries = [
            {
                'country_id': None,
                'country_name': 'Country1',
                'country_flag_url': 'flag1.png',
                'country_url': 'url1',
                'country_order': 1,
            },
        ]
        await crud.country_insert_all(session, sport_id, countries)
        country_id: int = countries[0]['country_id']

        team_info = {
            'team_id': None,
            'sport_id': sport_id.value,
            'country_id': country_id,
            'team_name': 'Team A',
            'team_full': 'Team A FC',
            'team_country': 'England',
            'team_url': 'https://www.teamA.com',
            'team_emblem': 'https://www.teamA.com/emblem.png',
            'download_date': datetime.datetime(year=2021, month=1, day=1),
            'save_date': datetime.datetime(year=2022, month=2, day=2),
        }
        team_id = await crud.team_merge(session, team_info)

        crud.save_database = DATABASE_READ_ONLY
        team_id_new = await crud.team_merge(session, team_info)

        assert team_id == team_id_new

        team_info_not_exists = {
            'team_id': None,
            'sport_id': sport_id.value,
            'country_id': country_id,
            'team_name': 'Team B',
            'team_full': 'Team A FC',
            'team_country': 'England',
            'team_url': 'https://www.teamA.com_mot',
            'team_emblem': 'https://www.teamA.com/emblem.png',
            'download_date': datetime.datetime(year=2021, month=1, day=1),
            'save_date': datetime.datetime(year=2022, month=2, day=2),
        }
        team_id_not_exists = await crud.team_merge(session, team_info_not_exists)

        assert team_id_not_exists is None


class TestInsertMatch:
    """Тест работы с матчем."""

    @pytest.mark.asyncio()
    async def test_insert_valid_matches_successfully_updates_database(self, crud: CRUDbetexplorer, session: AsyncSession) -> None:
        """Вставка списка матчей."""
        crud.save_database = DATABASE_WRITE_DATA
        sport_id = SportType.FOOTBALL
        countries = [
            {
                'country_id': None,
                'country_name': 'England',
                'country_flag_url': 'flag1.png',
                'country_url': 'url1',
                'country_order': 1,
            },
        ]
        await crud.country_insert_all(session, sport_id, countries)
        country_id: int = countries[0]['country_id']

        championships = [{
            'championship_id': None,
            'championship_url': 'https://example.com/championship',
            'championship_name': 'Example Championship',
            'championship_order': 1,
            'championship_years': '2022-2023',
        }]
        await crud.insert_championship(session, sport_id, country_id, championships)
        championship_id = championships[0]['championship_id']

        team_1: TeamBetexplorer = {
            'team_id': None,
            'sport_id': sport_id.value,
            'country_id': country_id,
            'team_country': 'England',
            'team_name': 'Team A',
            'team_full': 'Team A FC',
            'team_url': 'https://example.com/team/1',
            'team_emblem': 'https://www.teamA.com/emblem.png',
            'download_date': datetime.datetime(year=2021, month=1, day=1),
            'save_date': datetime.datetime(year=2022, month=2, day=2),
        }
        team_id_1 = await crud.team_merge(session, team_1)
        team_2: TeamBetexplorer = {
            'team_id': None,
            'sport_id': sport_id.value,
            'country_id': country_id,
            'team_country': 'England',
            'team_name': 'Team B',
            'team_full': 'Team B FC',
            'team_url': 'https://example.com/team/2',
            'team_emblem': 'https://www.teamB.com/emblem.png',
            'download_date': datetime.datetime(year=2021, month=1, day=1),
            'save_date': datetime.datetime(year=2022, month=2, day=2),
        }
        team_id_2 = await crud.team_merge(session, team_2)

        matches_test = [
            {
                'match_id': None,
                'championship_id': championship_id,
                'match_url': 'https://example.com/match/1',
                'home_team': team_1,
                'home_team_emblem': 'https://example.com/emblem/1',
                'away_team': team_2,
                'away_team_emblem': 'https://example.com/emblem/2',
                'home_score': 2,
                'away_score': 1,
                'odds_1': 1.5,
                'odds_x': 2.0,
                'odds_2': 3.0,
                'game_date': datetime.datetime(2022, 1, 1),
                'score_stage': 'Full Time',
                'score_stage_short': 'FT',
                'stage_name': 'Group Stage',
                'score_halves': [
                    {
                        'half_number': 1,
                        'home_score': 1,
                        'away_score': 0,
                    },
                    {
                        'half_number': 2,
                        'home_score': 1,
                        'away_score': 1,
                    },
                ],
                'shooters': [
                    {
                        'event_time': '10',
                        'home_away': 0,
                        'overtime': None,
                        'player_name': 'Player 1',
                        'penalty_kick': None,
                        'event_order': 1,
                    },
                    {
                        'event_time': '20',
                        'home_away': 1,
                        'overtime': None,
                        'player_name': 'Player 2',
                        'penalty_kick': None,
                        'event_order': 1,
                    },
                ],
                'download_date': datetime.datetime(year=2021, month=1, day=1),
                'save_date': datetime.datetime(2022, 1, 2),
                'round_name': 'Round 1',
                'round_number': 1,
                'is_fixture': 0,
            },
            {
                'match_id': None,
                'championship_id': championship_id,
                'match_url': 'https://example.com/match/2',
                'home_team': team_2,
                'home_team_emblem': 'https://example.com/emblem/1',
                'away_team': team_1,
                'away_team_emblem': 'https://example.com/emblem/2',
                'home_score': 3,
                'away_score': 2,
                'odds_1': 1.9,
                'odds_x': 2.1,
                'odds_2': 3.0,
                'game_date': datetime.datetime(2022, 2, 1),
                'score_stage': 'Full Time',
                'score_stage_short': 'FT',
                'stage_name': 'Group Stage',
                'score_halves': [
                    {
                        'half_number': 1,
                        'home_score': 0,
                        'away_score': 1,
                    },
                    {
                        'half_number': 2,
                        'home_score': 2,
                        'away_score': 1,
                    },
                ],
                'shooters': [
                    {
                        'event_time': '00',
                        'home_away': 0,
                        'overtime': None,
                        'player_name': 'Player 2',
                        'penalty_kick': None,
                        'event_order': 1,
                    },
                    {
                        'event_time': '20',
                        'home_away': 1,
                        'overtime': None,
                        'player_name': 'Player 3',
                        'penalty_kick': None,
                        'event_order': 1,
                    },
                ],
                'download_date': datetime.datetime(year=2021, month=1, day=1),
                'save_date': datetime.datetime(2022, 1, 3),
                'round_name': 'Round 2',
                'round_number': 2,
                'is_fixture': 0,
            },
        ]

        await crud.insert_match(session, championship_id, matches_test)

        async with session.begin():
            matches = (await session.scalars(
                select(Match).where(Match.championship_id == championship_id).order_by(Match.match_id)
                .options(selectinload(Match.time_score),
                         selectinload(Match.shooter),
                         selectinload(Match.home_team).joinedload(Team.country),
                         selectinload(Match.away_team).joinedload(Team.country))
                .execution_options(populate_existing=True)))
            res: list[MatchBetexplorer] = []
            for match in matches:
                m: MatchBetexplorer = {
                    'match_id': match.match_id,
                    'championship_id': match.championship_id,
                    'match_url': match.match_url,
                    'home_team': {
                        'team_id': match.home_team.team_id,
                        'sport_id': match.home_team.sport_id,
                        'team_name': match.home_team.team_name,
                        'team_full': match.home_team.team_full,
                        'team_url': match.home_team.team_url,
                        'team_country': match.home_team.country.country_name,
                        'country_id': match.home_team.country_id,
                        'team_emblem': match.home_team.team_emblem,
                        'download_date': match.home_team.download_date,
                        'save_date': match.home_team.save_date,
                    },
                    'home_team_emblem': match.home_team_emblem,
                    'away_team': {
                        'team_id': match.away_team.team_id,
                        'sport_id': match.away_team.sport_id,
                        'team_name': match.away_team.team_name,
                        'team_full': match.away_team.team_full,
                        'team_url': match.away_team.team_url,
                        'team_country': match.away_team.country.country_name,
                        'country_id': match.away_team.country_id,
                        'team_emblem': match.away_team.team_emblem,
                        'download_date': match.away_team.download_date,
                        'save_date': match.away_team.save_date,
                    },
                    'away_team_emblem': match.away_team_emblem,
                    'home_score': match.home_score,
                    'away_score': match.away_score,
                    'odds_1': match.odds_1,
                    'odds_x': match.odds_x,
                    'odds_2': match.odds_2,
                    'game_date': match.game_date,
                    'score_stage': match.score_stage,
                    'score_stage_short': match.score_stage_short,
                    'stage_name': match.stage_name,
                    'score_halves': [{
                        'time_id':  b.time_id,
                        'half_number': b.half_number,
                        'home_score':  b.home_score,
                        'away_score':  b.away_score,
                    } for b in match.time_score],
                    'shooters': [{
                        'shooter_id': b.shooter_id,
                        'home_away': b.home_away,
                        'event_time': b.event_time,
                        'overtime': b.overtime,
                        'player_name': b.player_name,
                        'penalty_kick': b.penalty_kick,
                        'event_order': b.event_order,
                    } for b in match.shooter],
                    'round_name': match.round_name,
                    'round_number': match.round_number,
                    'download_date': match.download_date,
                    'save_date': match.save_date,
                    'is_fixture': match.is_fixture,
                }
                res.append(m)
        assert not DeepDiff(matches_test, res,
                            exclude_paths=["root[0]['match_id']", "root[1]['match_id']"])

    @pytest.mark.asyncio()
    async def test_insert_empty_list_of_matches_does_not_update_database(self, crud: CRUDbetexplorer, session: AsyncSession) -> None:
        """Вставка пустого списка не обновляет базу данных."""
        crud.save_database = DATABASE_WRITE_DATA
        championship_id = 1
        matches = []

        await crud.insert_match(session, championship_id, matches)

        async with session.begin():
            inserted_matches = (await session.scalars(select(Match).where(Match.championship_id == championship_id))).all()
        assert len(inserted_matches) == 0

    @pytest.mark.asyncio()
    async def test_does_not_insert_or_update_matches_if_save_database_is_DATABASE_READ_ONLY_and_matches_already_exist_in_the_database(self, crud: CRUDbetexplorer, session: AsyncSession) -> None:
        """Не вставляет и не обновляет данные, если save_database имеет значение DATABASE_READ_ONLY и жанные уже существуют в базе."""
        crud.save_database = DATABASE_WRITE_DATA
        sport_id = SportType.FOOTBALL
        countries = [
            {
                'country_id': None,
                'country_name': 'England',
                'country_flag_url': 'flag1.png',
                'country_url': 'url1',
                'country_order': 1,
            },
        ]
        await crud.country_insert_all(session, sport_id, countries)
        country_id: int = countries[0]['country_id']

        championships = [{
            'championship_id': None,
            'championship_url': 'https://example.com/championship',
            'championship_name': 'Example Championship',
            'championship_order': 1,
            'championship_years': '2022-2023',
        }]
        await crud.insert_championship(session, sport_id, country_id, championships)
        championship_id = championships[0]['championship_id']

        team_1: TeamBetexplorer = {
            'team_id': None,
            'sport_id': sport_id.value,
            'country_id': country_id,
            'team_country': 'England',
            'team_name': 'Team A',
            'team_full': 'Team A FC',
            'team_url': 'https://example.com/team/1',
            'team_emblem': 'https://www.teamA.com/emblem.png',
        }
        team_id_1 = await crud.team_merge(session, team_1)
        team_2: TeamBetexplorer = {
            'team_id': None,
            'sport_id': sport_id.value,
            'country_id': country_id,
            'team_country': 'England',
            'team_name': 'Team B',
            'team_full': 'Team B FC',
            'team_url': 'https://example.com/team/2',
            'team_emblem': 'https://www.teamB.com/emblem.png',
        }
        team_id_2 = await crud.team_merge(session, team_2)

        matches_test = [
            {
                'match_id': None,
                'championship_id': championship_id,
                'match_url': 'https://example.com/match/1',
                'home_team': team_1,
                'home_team_emblem': 'https://example.com/emblem/1',
                'away_team': team_2,
                'away_team_emblem': 'https://example.com/emblem/2',
                'home_score': 2,
                'away_score': 1,
                'odds_1': 1.5,
                'odds_x': 2.0,
                'odds_2': 3.0,
                'game_date': datetime.datetime(2022, 1, 1),
                'score_stage': 'Full Time',
                'score_stage_short': 'FT',
                'stage_name': 'Group Stage',
                'score_halves': [
                    {
                        'half_number': 1,
                        'home_score': 1,
                        'away_score': 0,
                    },
                    {
                        'half_number': 2,
                        'home_score': 1,
                        'away_score': 1,
                    },
                ],
                'shooters': [
                    {
                        'event_time': '10',
                        'home_away': 0,
                        'overtime': None,
                        'player_name': 'Player 1',
                        'penalty_kick': None,
                        'event_order': 1,
                    },
                    {
                        'event_time': '20',
                        'home_away': 1,
                        'overtime': None,
                        'player_name': 'Player 2',
                        'penalty_kick': None,
                        'event_order': 1,
                    },
                ],
                'save_date': datetime.datetime(2022, 1, 2),
                'round_name': 'Round 1',
                'round_number': 1,
                'is_fixture': 0,
            },
            {
                'match_id': None,
                'championship_id': championship_id,
                'match_url': 'https://example.com/match/2',
                'home_team': team_2,
                'home_team_emblem': 'https://example.com/emblem/1',
                'away_team': team_1,
                'away_team_emblem': 'https://example.com/emblem/2',
                'home_score': 3,
                'away_score': 2,
                'odds_1': 1.9,
                'odds_x': 2.1,
                'odds_2': 3.0,
                'game_date': datetime.datetime(2022, 2, 1),
                'score_stage': 'Full Time',
                'score_stage_short': 'FT',
                'stage_name': 'Group Stage',
                'score_halves': [
                    {
                        'half_number': 1,
                        'home_score': 0,
                        'away_score': 1,
                    },
                    {
                        'half_number': 2,
                        'home_score': 2,
                        'away_score': 1,
                    },
                ],
                'shooters': [
                    {
                        'event_time': '00',
                        'home_away': 0,
                        'overtime': None,
                        'player_name': 'Player 2',
                        'penalty_kick': None,
                        'event_order': 1,
                    },
                    {
                        'event_time': '20',
                        'home_away': 1,
                        'overtime': None,
                        'player_name': 'Player 3',
                        'penalty_kick': None,
                        'event_order': 1,
                    },
                ],
                'save_date': datetime.datetime(2022, 1, 3),
                'round_name': 'Round 2',
                'round_number': 2,
                'is_fixture': 0,
            },
        ]

        await crud.insert_match(session, championship_id, matches_test)
        crud.save_database = DATABASE_READ_ONLY
        match_id_0 = matches_test[0]['match_id']
        match_id_1 = matches_test[1]['match_id']
        matches_test[0]['match_id'] = None
        matches_test[1]['match_id'] = None
        await crud.insert_match(session, championship_id, matches_test)
        assert match_id_0 == matches_test[0]['match_id']
        assert match_id_1 == matches_test[1]['match_id']

    @pytest.mark.asyncio()
    async def test_does_not_insert_or_update_matches_if_save_database_is_DATABASE_NOT_USE(self, crud: CRUDbetexplorer, session: AsyncSession) -> None:
        """Не вставляет и не обновляет данные, если save_database имеет значение DATABASE_NOT_USE."""
        """Вставка пустого списка не обновляет базу данных."""
        crud.save_database = DATABASE_NOT_USE
        championship_id = 1
        matches = []

        await crud.insert_match(session, championship_id, matches)

        async with session.begin():
            inserted_matches = (await session.scalars(select(Match).where(Match.championship_id == championship_id))).all()
        assert len(inserted_matches) == 0


class TestInsertChampionshipStage:
    """Тест вставки стадии чемпионата."""

    @pytest.mark.asyncio()
    async def test_insert_championship_stage_valid_input(self, crud: CRUDbetexplorer, session: AsyncSession) -> None:
        """Вставляет этап чемпионата с действительными входными данными."""
        crud.save_database = DATABASE_WRITE_DATA
        sport_id = SportType.FOOTBALL
        countries = [
            {
                'country_id': None,
                'country_name': 'England',
                'country_flag_url': 'flag1.png',
                'country_url': 'url1',
                'country_order': 1,
            },
        ]
        await crud.country_insert_all(session, sport_id, countries)
        country_id: int = countries[0]['country_id']

        championships = [{
            'championship_id': None,
            'championship_url': 'https://example.com/championship',
            'championship_name': 'Example Championship',
            'championship_order': 1,
            'championship_years': '2022-2023',
        }]
        await crud.insert_championship(session, sport_id, country_id, championships)
        championship_id = championships[0]['championship_id']
        championship_stage = {
            'stage_id': None,
            'stage_url': 'https://example.com/stage',
            'stage_name': 'Stage 1',
            'stage_order': 1,
            'stage_current': True
        }

        stage_id = await crud.insert_championship_stage(session, championship_id, championship_stage)

        assert isinstance(stage_id, int)
