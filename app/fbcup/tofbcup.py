"""Функции выгрузки данных в формате FBcup."""
import datetime  # noqa: I001
import os

from sqlalchemy.ext.asyncio import AsyncSession

from app.betexplorer.crud import DATABASE_NOT_USE, CRUDbetexplorer, DatabaseUsage, DATABASE_WRITE_DATA
from app.betexplorer.schemas import SportType, CountryBetexplorer, MatchBetexplorer
from app.database import DatabaseSessionManager
from app.fbcup.bet import MatchBet
from app.fbcup.forecast import MatchForecast, create_team_chances
from app.fbcup.statistic import MatchId, MatchStatistics, calculate_league_prematch_stats
from app.fbcup.rating import MatchRating, calc_rating
from app.fbcup.utils import odds_to_prob, calc_margin, calc_prob, calc_double_odds
from app.utils import save_list


async def save_championship(crd: CRUDbetexplorer, session: AsyncSession| None,
                            root_dir: str, championship_id: int) -> None:
    """Сохраняет данные о чемпионатах в формате FBcup.

    :param crd: Класс для сохранения данных
    :param session: Текущая сессия базы данных
    :param root_dir: Путь для сохранения данных на диске
    :param championship_id: Идентификатор чемпионата
    """
    dir_adr: str = os.path.join(root_dir, str(championship_id))
    file_name_teams: str = str(championship_id) + '.txt'
    file_name_matches: str = str(championship_id) + '.fix'

    team_strings: list[str] = await print_championship_teams(crd, session, championship_id, file_name_matches)
    match_strings: list[str] = await print_championship_matches(crd, session, championship_id)

    await save_list(os.path.join(dir_adr, file_name_teams), team_strings, datetime.datetime.now())
    await save_list(os.path.join(dir_adr, file_name_matches), match_strings, datetime.datetime.now())


BLACK = 0
RED = 16711680
GREEN = 65280
BLUE = 255
YELLOW = 16776960
MAGENTA = 16711935
CYAN = 65535
WHITE = 16777215
GRAY = 8421504
DARK_RED = 8388608
DARK_GREEN = 32768
DARK_BLUE = 128
DARK_YELLOW = 32896
DARK_MAGENTA = 8388736
DARK_CYAN = 12632256


async def print_championship_teams(
        crd: CRUDbetexplorer, session: AsyncSession| None,
        championship_id: int,
        file_name_matches: str) -> list[str]:
    """Выводит на экран информацию о матчах указанного чемпионата.

    :param crd: Класс для сохранения данных
    :param session: Текущая сессия базы данных
    :param championship_id: Идентификатор чемпионата
    :param file_name_matches: Имя файла с результатами матчей
    """
    championship_info = await crd.championship_find(
        session, championship_id)

    team_details: list[CRUDbetexplorer.ChampionshipTeamsResult] = await crd.championship_teams(
        session, championship_id)
    team_strings: list[str] = []
    team_strings.append('[TOURNAMENT]')
    championship_description = (
        f'{championship_info["sport_name"]}'
        f' {championship_info["country_name"]}'
        f' {championship_info["championship_name"]}'
        f' {championship_info["championship_years"]}'
    )
    team_strings.append(championship_description)

    team_strings.append('[HOME/AWAY]')
    order_home_away = '1'
    order_away_home = '2'
    team_strings.append(order_home_away)

    team_strings.append('[ANALIZ]')
    team_strings.append('0 0 0 0 0 0 0 0')

    odds_goals = '1'
    wins_odds_goals = '2'
    personal_points_odds_goals_away = '3'
    percent_goals = '3'
    team_strings.append('[POSITION]')
    team_strings.append(f'{odds_goals}')

    team_strings.append('[LEGS]')
    team_strings.append('0')

    points_win = 3
    points_draw = 1
    points_defeat = 0
    points_win_ot = 0
    points_defeat_ot = 0
    time_win = 2
    time_draw = 1
    time_defeat = 0
    home_win = 0
    home_draw = 0
    home_defeat = 0
    away_win = 0
    away_draw = 0
    away_defeat = 0
    count_time = 0

    team_strings.append('[POINTS]')
    team_strings.append(f'{points_win} {points_draw} {points_defeat} {points_win_ot} {points_defeat_ot}'
                        f' {count_time}'
                        f' {time_win} {time_draw} {time_defeat}'
                        f' {home_win} {home_draw} {home_defeat} {away_win} {away_draw} {away_defeat}')

    count_win = 0
    count_win2 = 0
    count_lost2 = 0
    count_lost = 0
    team_strings.append('[EUROCUPS]')
    team_strings.append(f'{count_win} {count_win2} {count_lost2} {count_lost}')

    team_strings.append('[FONT]')
    font_size = 8
    font_name = 'Times New Roman'
    line_height = 30
    result_width = 45
    command_width = 110
    team_strings.append(f'{font_size} {result_width} {line_height} {command_width} "{font_name}" {DARK_CYAN} {WHITE} 1174 789')

    team_strings.append('[TEAMS]')
    pattern = [
        BLUE,
        DARK_GREEN,
        RED,
        YELLOW,
        MAGENTA,
        GREEN,
        GRAY,
        DARK_BLUE,
        DARK_RED,
        DARK_YELLOW,
        DARK_MAGENTA,
        CYAN,
        DARK_CYAN,
        BLACK,
    ]
    colors = pattern * 4

    for cnt, team in enumerate(team_details):
        team_string = f'{team["team_name"]} v:[{team["team_name"]}]={colors[cnt]}'
        team_strings.append(team_string)

    team_strings.append('[CALENDAR]')
    team_strings.append(f'<{file_name_matches}>')

    team_strings.append('[END]')
    return team_strings


async def print_championship_matches(crd: CRUDbetexplorer, session: AsyncSession | None,
                                     championship_id: int) -> list[str]:
    """Выводит на экран информацию о матчах указанного чемпионата.

    :param crd: Класс для сохранения данных
    :param session: Текущая сессия базы данных
    :param championship_id: Идентификатор чемпионата
    """
    countries: list[CountryBetexplorer] = await crd.get_countries_by_sport(session, SportType.FOOTBALL)
    match_details: list[MatchBetexplorer] = await crd.get_matches_by_sport(session, championship_id)
    # match_details: list[CRUDbetexplorer.ChampionshipMatchResult] = await crd.championship_matches(
    #     session, championship_id)
    match_ratings: list[MatchRating] = []
    match_statistics: dict[MatchId, MatchStatistics] = calculate_league_prematch_stats(match_details)
    """Статистика перед матчем для домашней и гостевой команды"""

    match_forecasts: list[MatchForecast] = []
    match_bets: list[MatchBet] = []
    match_strings: list[str] = []
    match_strings_forecast: list[str] = []
    for detail in match_details:
        match_statistic = match_statistics[detail['match_id']]
        match_rating = calc_rating(match_ratings, detail)
        match_chance = create_team_chances(match_forecasts, match_statistic, match_rating)

        game_date_str = detail['game_date'].strftime('%d.%m.%Y') if detail['game_date'] else ' ' * 10
        score_str = f' {detail['home_score']}:{detail['away_score']}' if detail['home_score'] is not None else ''
        time_score_str = ''
        if detail['score_halves'] is not None:
            time_score_str = (
                ' ('
                + ','.join(str(i['home_score']) + ':' + str(i['away_score']) for i in detail['score_halves'])
                + ')'
            )

        odds_str = ''
        if detail['odds_1'] is not None:
            # Вероятность с учетом маржи (%)
            prob_margin_1: float = odds_to_prob(detail['odds_1'])
            prob_margin_x: float = odds_to_prob(detail['odds_x'])
            prob_margin_2: float = odds_to_prob(detail['odds_2'])

            margin: float = calc_margin(detail['odds_1'], detail['odds_x'], detail['odds_2'])

            # Вероятность чистая (%)
            prob_1: float = calc_prob(detail['odds_1'], detail['odds_2'], detail['odds_x'])
            prob_x: float = calc_prob(detail['odds_x'], detail['odds_1'], detail['odds_2'])
            prob_2: float = calc_prob(detail['odds_2'], detail['odds_1'], detail['odds_x'])

            odds_1x: float = calc_double_odds(detail['odds_1'], detail['odds_x'])
            odds_x2: float = calc_double_odds(detail['odds_x'], detail['odds_2'])
            odds_12: float = calc_double_odds(detail['odds_1'], detail['odds_2'])

            odds_str = f' b:[{detail['odds_1']} {detail['odds_x']} {detail['odds_2']} {odds_1x} {odds_12} {odds_x2}]'

        match_string = (
            f'{game_date_str} {detail['home_team']['team_name']} - {detail['away_team']['team_name']}{score_str}{time_score_str}{odds_str}'
        )
        match_strings.append(match_string)

        game_date_str_2 = detail['game_date'].strftime('%d.%m.%y') if detail['game_date'] else ' ' * 8
        command_names = f'{detail['home_team']['team_name']} - {detail['away_team']['team_name']}'
        percent_1 = f'({match_chance["forecast"]["win_prob"]}-{match_chance["forecast"]["draw_prob"]}-{match_chance["forecast"]["defeat_prob"]})'
        time_score_str_2 = ''
        if detail['score_halves'] is not None:
            time_score_str_2 = (
                '('
                + ';'.join(str(i['home_score']) + ':' + str(i['away_score']) for i in detail['score_halves'])
                + ')'
            )
        schet_1 = f'{match_chance['forecast']['home_forecast']}:{match_chance['forecast']['away_forecast']}'
        score_str_2 = f'{detail["home_score"]}:{detail["away_score"]}' if detail['home_score'] is not None else ''

        match_chance_str = f'       {command_names: <40}{game_date_str_2} =={score_str_2} {time_score_str_2}==               {schet_1: <4}{percent_1: <4}'
        match_strings_forecast.append(match_chance_str)

    match_strings.append('[END]')
    return match_strings


async def to_fbcup(
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
        await save_championship(crd, session, root_dir, 11202)
    await db.close()
