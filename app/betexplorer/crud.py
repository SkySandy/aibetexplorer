"""Работа с базой данных."""
import collections.abc
import datetime
from typing import TYPE_CHECKING, Callable, Final, Optional, TypedDict, Union

from sqlalchemy import (
    Dialect,
    Row,
    Select,
    TextClause,
    bindparam,
    func,
    inspect,
    literal_column,
    select,
    text,
    types,
    union,
)
from sqlalchemy.dialects.postgresql import aggregate_order_by, insert as postgresql_upsert
from sqlalchemy.dialects.sqlite import insert as sqlite_upsert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, joinedload
from sqlalchemy.orm.decl_api import DeclarativeAttributeIntercept
from sqlalchemy.sql.expression import literal

from app.betexplorer.models import (
    Championship,
    ChampionshipStage,
    Country,
    CountrySport,
    Match,
    MatchEvent,
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

# if TYPE_CHECKING:
#     import datetime

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
        match_insert = [
            ChampionshipStage(
                championship_id=championship_id,
                stage_url=championship_stage['stage_url'],
                stage_name=championship_stage['stage_name'],
                stage_order=championship_stage['stage_order'],
                stage_current=championship_stage['stage_current'],
            )
            for championship_stage in championship_stages
        ]
        session.add_all(match_insert)
        # await session.flush()
        # championship_stage['stage_id'] = match_insert.stage_id
        # return match_insert.stage_id

    class ChampionshipResult(TypedDict):
        """Информация об чемпионате."""

        championship_id: Optional[int]
        sport_name: Optional[str]
        country_name: Optional[str]
        championship_name: Optional[str]
        championship_years: Optional[str]

    async def championship_find(self,
                                session: AsyncSession,
                                championship_id: int) -> Optional[ChampionshipResult]:
        """Поиск чемпионата.

            :param session: Текущая сессия
            :param championship_id: Идентификатор чемпионата

        SELECT
          championship.championship_id,
          sport.sport_name,
          country.country_name,
          championship.championship_name,
          championship.championship_years
        FROM
          public.championship
          JOIN public.sport ON sport.sport_id = championship.sport_id
          JOIN public.country ON country.country_id = championship.country_id
        WHERE
          championship.championship_id = 10818;
        """
        if self.save_database == DATABASE_NOT_USE:
            return None
        async with session.begin():
            championship_rec: Row = (await session.execute(
                select(
                    Championship.championship_id,
                    Sport.sport_name,
                    Country.country_name,
                    Championship.championship_name,
                    Championship.championship_years,
                )
                .join(Sport, Sport.sport_id == Championship.sport_id)
                .join(Country, Country.country_id == Championship.country_id)
                .where(Championship.championship_id == championship_id),
            )).one_or_none()
        return championship_rec._asdict()  # noqa: SLF001, RUF100


    class ChampionshipTeamsResult(TypedDict):
        """Информация о командах-участницах чемпионата."""

        team_id: Optional[int]
        team_name: Optional[str]

    async def championship_teams(self,
                                 session: AsyncSession,
                                 championship_id: int) -> list[ChampionshipTeamsResult]:
        """Поиск всех команд играющих в чемпионате.

                :param session: Текущая сессия
                :param championship_id: Идентификатор чемпионата

        SELECT
          t_home.team_id,
          t_home.team_name
        FROM public."match"
          LEFT JOIN team t_home ON
            public."match".home_team_id = t_home.team_id
        WHERE
          public."match".championship_id = 10818
        UNION
        SELECT
          t_away.team_id,
          t_away.team_name
        FROM public."match"
          LEFT JOIN team t_away ON
            public."match".away_team_id = t_away.team_id
        WHERE
          public."match".championship_id = 10818
        ORDER BY
          2;
        """
        if self.save_database == DATABASE_NOT_USE:
            return []

        t_home = aliased(Team, name='t_home')
        t_away = aliased(Team, name='t_away')

        stmt = (
            union(
                select(t_home.team_id, t_home.team_name)
                .select_from(Match)
                .outerjoin(t_home, Match.home_team_id == t_home.team_id)
                .where(Match.championship_id == championship_id),
                select(t_away.team_id, t_away.team_name)
                .select_from(Match)
                .outerjoin(t_away, Match.away_team_id == t_away.team_id)
                .where(Match.championship_id == championship_id),
            )
            .order_by(t_home.team_name)
        )

        async with session.begin():
            teams_rec = await session.execute(
                stmt,
            )
        return [dict(row) for row in teams_rec.mappings()]


    class ChampionshipMatchResult(TypedDict):
        """Информация о результате матча."""

        match_id: Optional[int]
        game_date: Optional[datetime.datetime]
        home_team_name: Optional[str]
        away_team_name: Optional[str]
        home_score: Optional[int]
        away_score: Optional[int]
        time_score_home: Optional[int]
        time_score_away: Optional[int]

    async def championship_matches(self,
                                   session: AsyncSession,
                                   championship_id: int) -> list[ChampionshipMatchResult]:
        """Поиск всех матчей чемпионата.

        :param session: Текущая сессия
        :param championship_id: Идентификатор чемпионата

        SELECT match_id, game_date, t_home.team_name, t_away.team_name, match.home_score, match.away_score,
          time_score.home_score, time_score.away_score
        FROM public."match"
        LEFT JOIN team t_home ON public."match".home_team_id = t_home.team_id
        LEFT JOIN team t_away ON public."match".away_team_id = t_away.team_id
        LEFT JOIN public.time_score ON time_score.match_id = match.match_id AND time_score.half_number = 1
        where public."match".championship_id = 10818
        order by game_date ASC;
        """
        if self.save_database == DATABASE_NOT_USE:
            return []
        t_home = aliased(Team)
        t_away = aliased(Team)

        async with session.begin():
            championship_rec = await session.execute(
                select(
                    Match.match_id,
                    Match.game_date,
                    t_home.team_name.label('home_team_name'),
                    t_away.team_name.label('away_team_name'),
                    Match.home_score,
                    Match.away_score,
                    TimeScore.home_score.label('time_score_home'),
                    TimeScore.away_score.label('time_score_away'),
                )
                .outerjoin(t_home, Match.home_team_id == t_home.team_id)
                .outerjoin(t_away, Match.away_team_id == t_away.team_id)
                .outerjoin(TimeScore, (TimeScore.match_id == Match.match_id) & (TimeScore.half_number == 1))
                .where(Match.championship_id == championship_id)
                .order_by(Match.game_date),
            )
        return [dict(row) for row in championship_rec.mappings()]

    async def get_countries_by_sport(self, session: AsyncSession, sport_id: SportType) -> list[CountryBetexplorer]:
        """Получить все страны для указанного вида спорта.

        :param session: Текущая сессия
        :param sport_id: Вид спорта, для которого выбираются страны
        """
        if self.save_database == DATABASE_NOT_USE:
            return []

        query = (
            select(
                Country.country_id,
                Country.country_name,
                Country.country_flag_url,
                CountrySport.country_url,
                CountrySport.country_order,
            )
            .join(Country, CountrySport.country_id == Country.country_id)
            .where(CountrySport.sport_id == sport_id.value)
        )
        async with session.begin():
            result = await session.execute(query)
        return [dict(row) for row in result.mappings()]

    async def get_matches_by_sport(self, session: AsyncSession, championship_id: int) -> list[MatchBetexplorer]:
        """Получить все матчи для указанного вида спорта.

                :param session: Текущая сессия
                :param championship_id: Идентификатор чемпионата
        SELECT
          match.match_id,
          ( SELECT
            to_json (item)
          FROM ( SELECT
            team.team_name AS team_name,
            team.team_full AS team_full,
            country.country_name AS country_name
          FROM public.team
          JOIN public.country ON team.country_id = country.country_id
          WHERE
            (public.match.home_team_id = public.team.team_id) ) item ) AS items
        FROM public.match
        WHERE
          match.match_id = 1000;

        SELECT
          match.match_id,
          (SELECT
            json_agg(json_build_object('time_id', time_score.time_id, 'half_number', time_score.half_number,
                                       'home_score', time_score.home_score, 'away_score', time_score.away_score)
                                        ORDER BY half_number) AS json_agg_1
          FROM time_score
          WHERE
            time_score.match_id = match.match_id) AS score_halves
        FROM match
        WHERE
          match.match_id = 315;
        """
        if self.save_database == DATABASE_NOT_USE:
            return []

        query = (
            select(
                Match.match_id,
                Match.championship_id,
                Match.match_url,
                Match.home_team_id,
                select(
                    func.to_json(
                        func.json_build_object(
                            text("'team_id'"), Team.team_id,
                            text("'sport_id'"), Team.sport_id,
                            text("'team_name'"), Team.team_name,
                            text("'team_full'"), Team.team_full,
                            text("'team_url'"), Team.team_url,
                            text("'team_country'"), Country.country_name,
                            text("'country_id'"), Team.country_id,
                            text("'team_emblem'"), Team.team_emblem,
                            text("'download_date'"), Team.download_date,
                            text("'save_date'"), Team.save_date,
                        ),
                    ),
                )
                .outerjoin(Country, Team.country_id == Country.country_id)
                .where(Team.team_id == Match.home_team_id)
                .scalar_subquery()
                .label('home_team'),
                Match.home_team_emblem,
                Match.away_team_id,
                select(
                    func.to_json(
                        func.json_build_object(
                            text("'team_id'"), Team.team_id,
                            text("'sport_id'"), Team.sport_id,
                            text("'team_name'"), Team.team_name,
                            text("'team_full'"), Team.team_full,
                            text("'team_url'"), Team.team_url,
                            text("'team_country'"), Country.country_name,
                            text("'country_id'"), Team.country_id,
                            text("'team_emblem'"), Team.team_emblem,
                            text("'download_date'"), Team.download_date,
                            text("'save_date'"), Team.save_date,
                        ),
                    ),
                )
                .outerjoin(Country, Team.country_id == Country.country_id)
                .where(Team.team_id == Match.away_team_id)
                .scalar_subquery()
                .label('away_team'),
                Match.away_team_emblem,
                Match.home_score,
                Match.away_score,
                Match.odds_1,
                Match.odds_x,
                Match.odds_2,
                Match.game_date,
                Match.score_stage,
                Match.score_stage_short,
                Match.stage_name,
                Match.round_number,
                select(
                    func.json_agg(aggregate_order_by(
                        func.json_build_object(
                            text("'time_id'"), TimeScore.time_id,
                            text("'half_number'"), TimeScore.half_number,
                            text("'home_score'"), TimeScore.home_score,
                            text("'away_score'"), TimeScore.away_score,
                        ), TimeScore.half_number),
                    ),
                )
                .where(TimeScore.match_id == Match.match_id)
                .scalar_subquery()
                .label('score_halves'),
                select(
                    func.json_agg(aggregate_order_by(
                        func.json_build_object(
                            text("'shooter_id'"), Shooter.shooter_id,
                            text("'home_away'"), Shooter.home_away,
                            text("'event_time'"), Shooter.event_time,
                            text("'overtime'"), Shooter.overtime,
                            text("'player_name'"), Shooter.player_name,
                            text("'penalty_kick'"), Shooter.penalty_kick,
                            text("'event_order'"), Shooter.event_order,
                        ), Shooter.event_time),
                    ),
                )
                .where(Shooter.match_id == Match.match_id)
                .scalar_subquery()
                .label('shooters'),
                select(
                    func.json_agg(aggregate_order_by(
                        func.json_build_object(
                            text("'match_event_id'"), MatchEvent.match_event_id,
                            text("'match_id'"), MatchEvent.match_id,
                            text("'event_type_id'"), MatchEvent.event_type_id,
                            text("'indicator'"), MatchEvent.indicator,
                            text("'odds_less'"), MatchEvent.odds_less,
                            text("'odds_greater'"), MatchEvent.odds_greater,
                        ), MatchEvent.event_type_id),
                    ),
                )
                .where(MatchEvent.match_id == Match.match_id)
                .scalar_subquery()
                .label('match_event'),
                Match.download_date,
                Match.save_date,
                Match.round_name,
                Match.round_number,
                Match.is_fixture,
            )
            .where(Match.championship_id == championship_id)
            .order_by(Match.game_date)
        )

        async with session.begin():
            result = await session.execute(query)
        return [dict(row) for row in result.mappings()]
