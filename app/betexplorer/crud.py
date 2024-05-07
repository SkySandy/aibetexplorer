"""Работа с базой данных."""
import collections.abc
from typing import TYPE_CHECKING, Callable, Final, Optional, Union

from sqlalchemy import Dialect, Select, TextClause, bindparam, inspect, select, text, types
from sqlalchemy.dialects.postgresql import insert as postgresql_upsert
from sqlalchemy.dialects.sqlite import insert as sqlite_upsert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.decl_api import DeclarativeAttributeIntercept

from app.betexplorer.models import (
    Championship,
    ChampionshipStage,
    Country,
    CountrySport,
    Match,
    Shooter,
    Sport,
    Team,
    TimeScore,
)
from app.betexplorer.schemas import (
    ChampionshipBetexplorer,
    ChampionshipStageBetexplorer,
    CountryBetexplorer,
    MatchBetexplorer,
    SportBetexplorer,
    SportType,
    TeamBetexplorer,
)

if TYPE_CHECKING:
    import datetime


upsert_mapping = {
    'postgresql': postgresql_upsert,
    'sqlite': sqlite_upsert,
}


class PARAMNATIVE(types.UserDefinedType):
    """Тип параметра запросов значения которых не заключается в кавычки, а передается в запрос как есть."""

    cache_ok: bool = True
    should_evaluate_none: bool = True

    def literal_processor(self, dialect: Dialect) -> Callable[  # noqa: ARG002, PLR6301, RUF100
        [Optional[str | collections.abc.Iterable]], str]:
        """Вернуть функцию преобразования, для literal_execute=True."""

        def process(value: Optional[str | collections.abc.Iterable]) -> str:
            if value is None:
                return ''
            if isinstance(value, str):
                return value
            if isinstance(value, collections.abc.Iterable):
                return ', '.join(str(v) for v in value if isinstance(v, str))
            raise TypeError(f'Unsupported type: {type(value)}')  # noqa: TRY003

        return process


DATABASE_NOT_USE: Final = 0
"""База не используется."""
DATABASE_READ_ONLY: Final = 1
"""Только чтение из базы данных."""
DATABASE_WRITE_DATA: Final = 2
"""Чтение и запись в базу данных."""

DatabaseUsage = Union[DATABASE_NOT_USE, DATABASE_READ_ONLY, DATABASE_WRITE_DATA]
"""Разрешенные операции с базой данных."""


class CRUDbetexplorer:
    """Операции с таблицами в базе данных."""

    __slots__ = ['save_database']

    def __init__(self, save_database: DatabaseUsage = DATABASE_NOT_USE) -> None:
        """Инициализировать класс для загрузки данных.

        :param save_database: Сохранять ли информацию в БД
        """
        self.save_database = save_database

    async def get_list(self,
                       session: AsyncSession,
                       command: Select | TextClause) -> Optional[list[dict]]:
        """Выполнение переданного запроса и получение ответа в виде списка.

        :param session: Текущая сессия
        :param command: Запрос для выполнения
        """
        if self.save_database == DATABASE_NOT_USE:
            return None
        async with session.begin():
            # noinspection PyProtectedMember
            return [row._asdict() for row in (await (await session.connection()).execute(command))]

    async def get_dict(self,
                       session: AsyncSession,
                       command: Select | TextClause) -> Optional[dict]:
        """Выполнение переданного запроса и получение ответа в виде словаря.

        :param session: Текущая сессия
        :param command: Запрос для выполнения
        """
        if self.save_database == DATABASE_NOT_USE:
            return None
        async with (session.begin()):
            # noinspection PyProtectedMember
            return None if (result := (await (await session.connection()).execute(command))
                            .one_or_none()) is None else result._asdict()

    async def analyze_tables(
            self,
            session: AsyncSession,
            tables: Optional[DeclarativeAttributeIntercept | collections.abc.Sequence[
                DeclarativeAttributeIntercept]] = None) -> None:
        """Обновляет статистику для выбранных таблиц.

        :param session: Текущая сессия
        :param tables: Список таблиц доя обновления статистки
        """

        async def execute_analyze(values: Optional[str | collections.abc.Iterable]) -> None:
            await session.execute(
                text('ANALYZE :tables').bindparams(
                    bindparam(
                        'tables',
                        value=values,
                        type_=PARAMNATIVE,
                        literal_execute=True,
                    ),
                ),
            )

        if self.save_database in {DATABASE_NOT_USE, DATABASE_READ_ONLY}:
            return
        value: Optional[str | collections.abc.Sequence]
        if isinstance(tables, collections.abc.Sequence) and not isinstance(tables, DeclarativeAttributeIntercept):
            value = [inspect(table).local_table.fullname for table in tables]
        elif isinstance(tables, DeclarativeAttributeIntercept):
            value = inspect(tables).local_table.fullname
        else:
            value = None
        async with session.begin():
            if session.bind.dialect.name == 'sqlite' and isinstance(value, list):
                for table in value:
                    await execute_analyze(table)
            else:
                await execute_analyze(value)

    def has_uncommitted_changes(self, session: AsyncSession) -> bool:
        """Определить есть ли измененные объекты в сессии."""
        if self.save_database == DATABASE_NOT_USE:
            return False

        return any(
            session.new
            or session.deleted
            or (x for x in session.dirty if session.is_modified(x)),
        )

    async def sports_insert_all(self,
                                session: AsyncSession,
                                sports: Optional[list[SportBetexplorer]]) -> None:
        """Добавить виды спорта.

        :param session: Текущая сессия
        :param sports: Список видов спорта
        """
        if self.save_database in {DATABASE_NOT_USE, DATABASE_READ_ONLY}:
            return

        async with session.begin():
            sport_unused = {sport['sport_id']: sport for sport in sports}
            for row in (await session.execute(select(Sport))).scalars():
                if (sport := sport_unused.pop(row.sport_id, None)) is not None:
                    row.sport_name, row.sport_url = sport['sport_name'], sport['sport_url']

            sport_insert = [Sport(
                sport_id=sport['sport_id'],
                sport_name=sport['sport_name'],
                sport_url=sport['sport_url'],
            ) for sport in sport_unused.values()]
            session.add_all(sport_insert)
            modified: bool = self.has_uncommitted_changes(session)

        if modified:
            await self.analyze_tables(session, [Sport])

    async def country_insert_all(self,
                                 session: AsyncSession,
                                 sport_id: SportType,
                                 countries: Optional[list[CountryBetexplorer]]) -> None:
        """Добавить или обновить список стран по виду спорта, возвращает присвоенные country_id.

        :param session: Текущая сессия
        :param sport_id: Вид спорта, для которого добавляются страны
        :param countries: Информация о списке стране
        """
        if self.save_database == DATABASE_NOT_USE:
            return

        country_unused = {country['country_name']: country for country in countries}
        if self.save_database == DATABASE_READ_ONLY:

            async with session.begin():
                for row in (await session.scalars(select(Country))):
                    if (country := country_unused.get(row.country_name, None)) is not None:
                        country['country_id'] = row.country_id
            return

        async with session.begin():
            for row in (await session.scalars(
                    select(Country)
                            .options(joinedload(Country.country_sport.and_(CountrySport.sport_id == sport_id.value)))
                            .execution_options(populate_existing=True))).unique():
                if (country := country_unused.pop(row.country_name, None)) is not None:
                    row.country_flag_url = country['country_flag_url']
                    if not row.country_sport:
                        row.country_sport.append(
                            CountrySport(
                                sport_id=sport_id.value,
                                country_url=country['country_url'],
                                country_order=country['country_order'],
                            ),
                        )
                    else:
                        row.country_sport[0].country_url = country['country_url']
                        row.country_sport[0].country_order = country['country_order']
                    country['country_id'] = row.country_id

            country_insert = [Country(
                country_name=country['country_name'],
                country_flag_url=country['country_flag_url'],
                country_sport=[
                    CountrySport(
                        sport_id=sport_id.value,
                        country_url=country['country_url'],
                        country_order=country['country_order'],
                    ),
                ],
            ) for country in country_unused.values()]
            session.add_all(country_insert)
            modified: bool = self.has_uncommitted_changes(session)
            await session.flush()
            for row in country_insert:
                country_unused[row.country_name]['country_id'] = row.country_id

        if modified:
            await self.analyze_tables(session, [Country, CountrySport])

    async def analyze_match(self, session: AsyncSession) -> None:
        """Обновить статистику после добавления матчей.

        :param session: Текущая сессия
        """
        await self.analyze_tables(session, [Championship, Match, TimeScore, Shooter, Team, ChampionshipStage])

    async def insert_championship(self,
                                  session: AsyncSession,
                                  sport_id: SportType,
                                  country_id: int,
                                  championships: Optional[list[ChampionshipBetexplorer]]) -> None:
        """Вставить или обновить информацию о чемпионатах.

        :param session: Текущая сессия
        :param sport_id: Вид спорта
        :param country_id: Идентификатор страны
        :param championships: Информация о чемпионатах
        :return: Идентификатор чемпионата
        """
        if self.save_database == DATABASE_NOT_USE:
            return

        championship_unused: dict[tuple[str, str, str, int], ChampionshipBetexplorer] = {
            (championship['championship_name'],
             championship['championship_years'],
             championship['championship_url'],
             championship['championship_order']): championship
            for championship in championships
        }
        if self.save_database == DATABASE_READ_ONLY:
            async with session.begin():
                for row in (await session.scalars(select(Championship).where(
                        Championship.country_id == country_id,
                        Championship.sport_id == sport_id.value))):
                    if (championship := championship_unused.get(
                            (row.championship_name, row.championship_years,
                             row.championship_url, row.championship_order), None)) is not None:
                        championship['championship_id'] = row.championship_id
            return
        async with session.begin():
            # for row in (await session.scalars(
            #         select(Championship).where(
            #             Championship.country_id == country_id,
            #             Championship.sport_id == sport_id.value))).unique():
            #     if (championship := championship_unused.pop(
            #             (row.championship_name, row.championship_years,
            #              row.championship_url, row.championship_order), None)) is not None:
            #         row.championship_order = championship['championship_order']
            #         championship['championship_id'] = row.championship_id

            championship_insert = [Championship(
                sport_id=sport_id.value,
                country_id=country_id,
                championship_name=championship['championship_name'],
                championship_url=championship['championship_url'],
                championship_order=championship['championship_order'],
                championship_years=championship['championship_years'],
            ) for championship in championship_unused.values()]
            session.add_all(championship_insert)
            modified: bool = self.has_uncommitted_changes(session)
            await session.flush()
            for row in championship_insert:
                championship_unused[
                    (row.championship_name, row.championship_years,
                     row.championship_url, row.championship_order)]['championship_id'] = row.championship_id

        # if modified:
        #     await self.analyze_tables(session, [Championship])

    async def team_merge(self,
                         session: AsyncSession,
                         team: TeamBetexplorer) -> Optional[int]:
        """Вставить или обновить информацию о команде.

        :param session: Текущая сессия
        :param team: Информация о команде
        :return: Идентификатор команды
        """
        if self.save_database == DATABASE_NOT_USE:
            return None
        if self.save_database == DATABASE_READ_ONLY:
            async with session.begin():
                return (await session.scalar(
                    select(Team.team_id).where(
                        Team.team_url == team['team_url'],
                    ),
                ))

        async with session.begin():
            if (upsert_func := upsert_mapping.get(session.get_bind().dialect.name)) is not None:
                team_rec = (await session.scalars(
                    upsert_func(Team).values(
                        sport_id=team['sport_id'],
                        country_id=team['country_id'],
                        team_name=team['team_name'],
                        team_full=team['team_full'],
                        team_url=team['team_url'],
                        team_emblem=team['team_emblem'],
                        download_date=team['download_date'],
                        save_date=team['save_date'],
                    ).on_conflict_do_update(
                        index_elements=['team_url'],
                        set_={
                            'country_id': team['country_id'],
                            'team_name': team['team_name'],
                            'team_full': team['team_full'],
                            'team_emblem': team['team_emblem'],
                            'download_date': team['download_date'],
                            'save_date': team['save_date'],
                        }).returning(Team),
                    execution_options={'populate_existing': True})).one_or_none()
            elif (team_rec := (await session.scalars(
                    select(Team).where(
                        Team.team_url == team['team_url'],
                    ))).one_or_none()) is not None:
                team_rec.country_id = team['country_id']
                team_rec.team_name = team['team_name']
                team_rec.team_full = team['team_full']
                team_rec.team_emblem = team['team_emblem']
                team_rec.download_date = team['download_date']
                team_rec.save_date = team['save_date']
            else:
                team_rec = Team(
                    sport_id=team['sport_id'],
                    country_id=team['country_id'],
                    team_name=team['team_name'],
                    team_full=team['team_full'],
                    team_url=team['team_url'],
                    team_emblem=team['team_emblem'],
                    download_date=team['download_date'],
                    save_date=team['save_date'],
                )
                session.add(team_rec)
            await session.flush()
            if team_rec is None:
                team_rec = (await session.scalars(
                    select(Team).where(
                        Team.team_url == team['team_url'],
                    ))).one_or_none()
            team['team_id'] = team_rec.team_id
            return team_rec.team_id

    async def add_matches(
            self,
            session: AsyncSession,
            championship_id: int,
            matches: list[MatchBetexplorer],
            ) -> None:
        """Добавить информацию о результатах матчей в базу данных.

        :param session: Текущая сессия
        :param championship_id: Идентификатор чемпионата
        :param matches: Информация о результатах матчей

        :return: Обновление идентификаторов матчей во входной структуре
        """
        if self.save_database == DATABASE_NOT_USE:
            return
        match_unused: dict[
            tuple[int, str, int, int, datetime.datetime, int, int, float, float, float], MatchBetexplorer,
        ] = {
            (match['championship_id'],
             match['round_name'],
             match['home_team']['team_id'],
             match['away_team']['team_id'],
             match['game_date'],
             match['home_score'],
             match['away_score'],
             match['odds_1'],
             match['odds_x'],
             match['odds_2'],
             ): match
            for match in matches
        }

        if self.save_database == DATABASE_READ_ONLY:
            async with session.begin():
                for row in (await session.scalars(select(Match).where(
                        Match.championship_id == championship_id))):
                    if (match := match_unused.get(
                            (row.championship_id, row.round_name, row.home_team_id, row.away_team_id,
                             row.game_date, row.home_score, row.away_score,
                             row.odds_1, row.odds_x, row.odds_2), None)) is not None:
                        match['match_id'] = row.match_id
            return

        # for row in (await session.scalars(
        #         select(Match).where(
        #             Match.championship_id == championship_id))).unique():
        #     if (match := match_unused.pop(
        #             (row.championship_id, row.round_name, row.home_team_id, row.away_team_id,
        #              row.game_date, row.home_score, row.away_score,
        #              row.odds_1, row.odds_x, row.odds_2), None)) is not None:
        #         match['match_id'] = row.match_id

        match_insert = [Match(
            championship_id=championship_id,
            match_url=match['match_url'],
            home_team_id=match['home_team']['team_id'],
            home_team_emblem=match['home_team_emblem'],
            away_team_id=match['away_team']['team_id'],
            away_team_emblem=match['away_team_emblem'],
            home_score=match['home_score'],
            away_score=match['away_score'],

            odds_1=match['odds_1'],
            odds_x=match['odds_x'],
            odds_2=match['odds_2'],

            game_date=match['game_date'],
            score_stage=match['score_stage'],
            score_stage_short=match['score_stage_short'],

            is_fixture=match['is_fixture'],
            stage_name=match['stage_name'],
            round_name=match['round_name'],
            round_number=match['round_number'],
            download_date=match['download_date'],
            save_date=match['save_date'],
            time_score=[
                TimeScore(
                    half_number=score_halves['half_number'],
                    home_score=score_halves['home_score'],
                    away_score=score_halves['away_score'],
                ) for score_halves in match['score_halves']
            ],
            shooter=[
                Shooter(
                    home_away=shooter['home_away'],
                    event_time=shooter['event_time'],
                    overtime=shooter['overtime'],
                    player_name=shooter['player_name'],
                    penalty_kick=shooter['penalty_kick'],
                    event_order=shooter['event_order'],
                ) for shooter in match['shooters']
            ],
        ) for match in match_unused.values()]

        session.add_all(match_insert)
        # modified: bool = self.has_uncommitted_changes(session)
        # await session.flush()
        # for row in match_insert:
        #     match = match_unused[
        #         (row.championship_id, row.round_name, row.home_team_id, row.away_team_id,
        #          row.game_date, row.home_score, row.away_score,
        #          row.odds_1, row.odds_x, row.odds_2)]
        #     match['match_id'] = row.match_id
        #     for index, item in enumerate(row.time_score):
        #         match['score_halves'][index].update({'time_id': item.time_id})
        #     for index, item in enumerate(row.shooter):
        #         match['shooters'][index].update({'shooter_id': item.shooter_id})

    # if modified:
    #     await self.analyze_tables(session, [Match, TimeScore, Shooter])

    async def add_championship_stages(
            self,
            session: AsyncSession,
            championship_id: int,
            championship_stages: list[ChampionshipStageBetexplorer],
        ) -> Optional[int]:
        """Вставить стадию чемпионата в базу данных.

        :param session: Текущая сессия
        :param championship_id: Идентификатор чемпионата
        :param championship_stages: Информация о стадии чемпионата

        :return: Идентификатор матча
        """
        if self.save_database == DATABASE_NOT_USE:
            return None
        # if self.save_database == DATABASE_READ_ONLY:
        #     async with session.begin():
        #         stage_id: int = await session.scalar(
        #             select(ChampionshipStage.stage_id).where(
        #                 ChampionshipStage.championship_id == championship_id,
        #                 ChampionshipStage.stage_name == championship_stage['stage_name'],
        #             ),
        #         )
        #         championship_stage['stage_id'] = stage_id
        #         return stage_id
        match_insert = [ChampionshipStage(
            championship_id=championship_id,
            stage_url=championship_stage['stage_url'],
            stage_name=championship_stage['stage_name'],
            stage_order=championship_stage['stage_order'],
            stage_current=championship_stage['stage_current'],
        ) for championship_stage in championship_stages]
        session.add_all(match_insert)
        # await session.flush()
        # championship_stage['stage_id'] = match_insert.stage_id
        # return match_insert.stage_id
