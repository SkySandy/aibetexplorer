"""Анализ ставок при различных параметрах."""
import datetime
import timeit

from analys_config import AnalysConfig
from bet import MatchBet, create_bet
from bet_summary import BetSummary, calc_bet_summary
from crud import DATABASE_NOT_USE, DATABASE_WRITE_DATA, CRUDbetexplorer, DatabaseUsage
from forecast import MatchForecast, create_team_chances
from forecast_summary import calc_forecast_summary
from rating import MatchRating, calc_rating
from schemas import MatchBetexplorer, SportType
from sqlalchemy.ext.asyncio import AsyncSession
from statistic import MatchStatistics, calculate_league_prematch_stats

from database import DatabaseSessionManager

async def analysis_championship(crd: CRUDbetexplorer, session: AsyncSession | None,
                                root_dir: str, championship_id: int) -> None:
    """Выводит на экран информацию о матчах указанного чемпионата.

    :param crd: Класс для сохранения данных
    :param session: Текущая сессия базы данных
    :param championship_id: Идентификатор чемпионата
    """
    calc_params: AnalysConfig = AnalysConfig()
    result_bet = []
    match_details: list[MatchBetexplorer] = await crd.get_matches_by_sport(session, championship_id)
    match_statistics: dict[int, MatchStatistics] = calculate_league_prematch_stats(match_details)
    """Статистика перед матчем для домашней и гостевой команды"""

    for round_number in range(1, 32):
        calc_params.round_number = round_number
        bs = await one_championship_matches(match_details, match_statistics, calc_params)
        result_bet.append(bs)
    pass


async def one_championship_matches(match_details: list[MatchBetexplorer], match_statistics: dict[int, MatchStatistics],
                                   calc_params: AnalysConfig) -> BetSummary:
    """Выполняет полный цикл анализа статистики всех матчей чемпионата для расчета ставок.

    :param match_details: Все матчи чемпионата
    :param match_statistics: Предматчевая статистика для каждого матча
    :param calc_params: Параметры для расчета ставок
    """
    match_ratings: list[MatchRating] = []
    match_forecasts: list[MatchForecast] = []
    match_bets: list[MatchBet] = []
    for detail in match_details:
        match_statistic = match_statistics[detail['match_id']]
        match_rating = calc_rating(match_ratings, detail)
        match_chance = create_team_chances(match_forecasts, match_statistic, match_rating)
        match_bet = create_bet(match_bets, detail, match_chance)

    f_s = calc_forecast_summary(match_details, match_forecasts)
    f_s1 = calc_bet_summary(match_details, match_bets, calc_params)
    return f_s1


async def to_analysis(
        root_dir: str,
        database: str | None = None,
        sport_type: list[SportType] | None = None,
        load_net: bool = False,
        save_database: DatabaseUsage = DATABASE_NOT_USE,
        create_tables: int = 0,
        config_engine: dict | None = None,
        start_updating: datetime.datetime | None = None,
        exclude_countries: tuple | None = None,
        processes: int = 1) -> None:
    """Первоначальная Загрузка данных спортивных состязаний всех чемпионатов во всех странах.

    :param root_dir: Путь для сохранения данных на диске
    :param database: Путь к базе данных
    :param sport_type: Виды спорта для загрузки
    :param load_net: Загрузка данных из интернета False - нет (использовать только сохраненные на диске), True - да
    :param save_database: Операции с базой данных 0 - без операций, 1 - только читать, 2 - читать и записывать
    :param create_tables: Создание базы данных если не существует 0 -не создавать, 1 - создать
    :param config_engine: Выводить команды SQL отправляемые на сервер
    :param start_updating: Дата начала обновления данных
    :param exclude_countries: Список стран которые не загружаем
    :param processes: Одновременное количество запущенных процессов
    """
    db = DatabaseSessionManager()
    save_database = DATABASE_WRITE_DATA
    db.init(database, **config_engine)
    crd: CRUDbetexplorer = CRUDbetexplorer(save_database=save_database)

    async with db.get_session() as session:
        await analysis_championship(crd, session, root_dir, 11202)
    await db.close()
