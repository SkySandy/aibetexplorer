"""Работа с сайтом Betexplorer."""
import asyncio
from asyncio import ProactorEventLoop
from concurrent.futures import Future, ProcessPoolExecutor
from contextlib import nullcontext
import datetime
from multiprocessing import Manager
from multiprocessing.synchronize import Lock as MultiLock
import re
import signal
from typing import TYPE_CHECKING, Any, Callable, Final, Optional
from urllib.parse import urljoin, urlparse

from selectolax.parser import Node
from sqlalchemy.ext.asyncio import AsyncSession

from app.betexplorer.crud import DATABASE_NOT_USE, CRUDbetexplorer, DatabaseUsage
from app.betexplorer.schemas import (
    SPORTS,
    ChampionshipBetexplorer,
    ChampionshipStageBetexplorer,
    CountryBetexplorer,
    MatchBetexplorer,
    ResultsBetexplorer,
    ScoreHalvesBetexplorer,
    ShooterBetexplorer,
    SportType,
    TeamBetexplorer,
    sports_url,
)
from app.database import DatabaseSessionManager
from app.utilbase import LoadSave, ReceivedData

if TYPE_CHECKING:
    from multiprocessing.managers import SyncManager

# from line_profiler_pycharm import profile

COLUMN_SCORE: Final[int] = 0
COLUMN_TEAMS: Final[int] = 1
COLUMN_ODDS_1: Final[int] = 2
COLUMN_ODDS_X: Final[int] = 3
COLUMN_ODDS_2: Final[int] = 4
COLUMN_GAME_DATE: Final[int] = 5

IS_RESULT: Final[int] = 0
IS_FIXTURE: Final[int] = 1

SPORTS_3: Final[set] = {SportType.FOOTBALL, SportType.HOCKEY, SportType.HANDBALL}

COLUMN_MAPPING: Final[dict] = {
    (IS_RESULT, 0, True): COLUMN_TEAMS,
    (IS_RESULT, 0, False): COLUMN_TEAMS,
    (IS_FIXTURE, 0, True): COLUMN_GAME_DATE,
    (IS_FIXTURE, 0, False): COLUMN_GAME_DATE,
    (IS_RESULT, 1, True): COLUMN_SCORE,
    (IS_RESULT, 1, False): COLUMN_SCORE,
    (IS_FIXTURE, 1, True): COLUMN_TEAMS,
    (IS_FIXTURE, 1, False): COLUMN_TEAMS,
    (IS_RESULT, 2, True): COLUMN_ODDS_1,
    (IS_RESULT, 2, False): COLUMN_ODDS_1,
    (IS_FIXTURE, 4, True): COLUMN_ODDS_1,
    (IS_FIXTURE, 4, False): COLUMN_ODDS_1,
    (IS_RESULT, 3, True): COLUMN_ODDS_X,
    (IS_RESULT, 4, True): COLUMN_ODDS_2,
    (IS_RESULT, 5, True): COLUMN_GAME_DATE,
    (IS_FIXTURE, 5, True): COLUMN_ODDS_X,
    (IS_FIXTURE, 6, True): COLUMN_ODDS_2,
    (IS_RESULT, 3, False): COLUMN_ODDS_2,
    (IS_RESULT, 4, False): COLUMN_GAME_DATE,
    (IS_FIXTURE, 5, False): COLUMN_ODDS_2,
}

COLUMN_PENALTY_KICK: Final[int] = 0
COLUMN_EVENT_TIME: Final[int] = 1
COLUMN_PLAYER_NAME: Final[int] = 2

SPORTS_SHOOTERS_3: Final[set] = {SportType.FOOTBALL, SportType.BASKETBALL, SportType.TENNIS, SportType.BASEBALL,
                                 SportType.VOLLEYBALL, SportType.HANDBALL, SportType.HOCKEY}

COLUMN_MAPPING_SHOOTER: Final[dict] = {
    (0, 0, True): COLUMN_PENALTY_KICK,
    (1, 2, True): COLUMN_PENALTY_KICK,
    (0, 1, True): COLUMN_EVENT_TIME,
    (1, 0, True): COLUMN_EVENT_TIME,
    (0, 2, True): COLUMN_PLAYER_NAME,
    (1, 1, True): COLUMN_PLAYER_NAME,
}

REG_ROUND: re.Pattern = re.compile(r'^\d+?(?=. Round)')

REG_DATE: re.Pattern = re.compile(r'^(\d{2})[/.-](\d{2})[/.-](\d{4})')
REG_DATE_SHORT: re.Pattern = re.compile(r'(\d{2})[/.-](\d{2})[/.-]')
REG_TODAY: re.Pattern = re.compile(r'Today')
REG_YESTERDAY: re.Pattern = re.compile(r'Yesterday')

REG_DATE_FIXTURES: re.Pattern = re.compile(r'(\d{2})[.](\d{2})[.](\d{4}) (\d{2}):(\d{2})')
REG_DATE_SHORT_FIXTURES: re.Pattern = re.compile(r'(\d{2})[.](\d{2})[.] (\d{2}):(\d{2})')
REG_TODAY_FIXTURES: re.Pattern = re.compile(r'Today (\d{1,2}):(\d{2})')
REG_TOMORROW_FIXTURES: re.Pattern = re.compile(r'Tomorrow (\d{1,2}):(\d{2})')
REG_YESTERDAY_FIXTURES: re.Pattern = re.compile(r'Yesterday (\d{1,2}):(\d{2})')

REG_SCORE_HALVES: re.Pattern = re.compile(r'((?:(\d{1,3}):(\d{1,3}))+),?', re.MULTILINE)
REG_DATE_MATCH: re.Pattern = re.compile(r'(\d{1,2}),(\d{1,2}),(\d{4}),(\d{1,2}),(\d{1,2})')

REG_EVENT_TIME: re.Pattern = re.compile(r'(\d{1,3})\.')
REG_EVENT_TIME_OVERTIME: re.Pattern = re.compile(r'(\d{1,3})[+](\d{1,2})\.')
REG_EVENT_TIME_MIN_SEC: re.Pattern = re.compile(r'(\d{1,3}):(\d{2})')

REG_COMMAND_COUNTRY: re.Pattern = re.compile(r'(.*) \((.*)\)')

CSS_COUNTRIES: Final[str] = '.box-aside__section__in'
CSS_CHAMPIONSHIPS: Final[str] = '.table-main.js-tablebanner-t,.nodata'
CSS_RESULTS: Final[str] = 'div.columns__item.columns__item--68.columns__item--tab-100'
CSS_RESULT: Final[str] = 'table.table-main.js-tablebanner-t.js-tablebanner-ntb tbody'
CSS_FIXTURE: Final[str] = \
    'table.table-main.table-main--leaguefixtures.h-mb15.js-tablebanner-t.js-tablebanner-ntb tbody'
CSS_MATCH: Final[str] = '.wrap-page__in'
CSS_SHOOTERS: Final[str] = 'ul.list-details.list-details--shooters'
CSS_PAGE_TEAM: Final[str] = 'header.wrap-section__header'
CSS_PAGE_TEAM_BEG: Final[str] = 'h1.wrap-section__header__title'
CSS_PAGE_STANDING: Final[str] = 'section.wrap-section'

CSS_COUNTRIES_ITEMS: Final[str] = 'div.list-events__item__in'
CSS_CHAMPIONSHIPS_ITEMS: Final[str] = 'tbody'
CSS_STAGES_ITEMS: Final[str] = 'ul.list-tabs.list-tabs--secondary'
CSS_STAGES_SHORT_ITEMS: Final[str] = 'ul.list-tabs.list-tabs--secondary.list-tabs--short'
CSS_SCORE_HALVES_ITEMS: Final[str] = 'h2.list-details__item__partial'

JAVASCRIPT_VOID = 'javascript:void(0);'


def parsing_countries(soup: Optional[ReceivedData]) -> list[CountryBetexplorer]:
    """Разбор страницы списка всех стран.

    :param soup: Данные для разбора
    """
    return [
        {
            'country_id': None,
            'country_url': item.css_first('a[href]').attrs['href'],
            'country_name': item.text(strip=True),
            'country_order': index,
            'country_flag_url': flg.attrs['src'] if (flg := item.css_first('img[src]')) is not None else None,
        } for index, item in enumerate(soup.node.css(CSS_COUNTRIES_ITEMS))
    ] if soup is not None else []


async def get_countries(ls: LoadSave, url: str, need_refresh: bool = False) -> Optional[
    list[CountryBetexplorer]]:  # noqa: FBT001, FBT002
    """Загрузка страницы стран.

    :param ls: Класс для работы с файлами
    :param url: Адрес страницы для разборы
    :param need_refresh: Необходимо обновить данные
    """
    load_countries: Optional[ReceivedData]
    if (load_countries := await ls.get_read(url, CSS_COUNTRIES, need_refresh)) is not None:
        return parsing_countries(load_countries)
    return None


def parsing_championships(
        soup: Optional[ReceivedData], sport_id: int, country_id: int) -> list[ChampionshipBetexplorer]:
    """Разбор страницы списка сезонов чемпионатов по стране.

    :param soup: Данные для разбора
    :param sport_id: Вид спорта
    :param country_id: Идентификатор страны
    """
    ret: list[ChampionshipBetexplorer] = []
    if soup is not None:
        for season in soup.node.css(CSS_CHAMPIONSHIPS_ITEMS):
            championship_years = season.css_first('th.h-text-left').text(deep=False, strip=True)
            ret += [
                {
                    'championship_id': None,
                    'sport_id': sport_id,
                    'country_id': country_id,
                    'championship_url': item.attrs['href'],
                    'championship_name': item.text(deep=False, strip=True),
                    'championship_order': index,
                    'championship_years': championship_years,
                } for index, item in enumerate(season.css('a[href]'))
            ]
    return ret


def parsing_odds(item: Node) -> Optional[float]:
    """Разбор колонки коэффициент.

    :param item: Колонка с коэффициентом
    """
    if (f_kef := item.attrs.get('data-odd')) is not None:
        return float(f_kef)
    return float(odds.attrs['data-odd']) if (odds := item.child.css_first(
        '[data-odd]')) is not None else None


def parsing_stages(soup: ReceivedData) -> list[ChampionshipStageBetexplorer]:
    """Разбор стадий чемпионата.

    :param soup: Страница для разбора
    """
    if soup is None:
        return []
    ret_main: list[ChampionshipStageBetexplorer] = []
    if (block := soup.node.css_first('div.h-mb15')) is not None:
        stage_group: dict[int, str] = {
            index: item.text(deep=False, strip=True) + '. '
            for stages_beg in block.css(CSS_STAGES_ITEMS)
            for index, item in enumerate(stages_beg.css('a[href]')) if item.attrs['href'] == JAVASCRIPT_VOID
        }
        ret_main = [
                {'stage_id': None,
                 'stage_url': item.attrs['href'],
                 'stage_name': stage_group.get(i - 1, '') + item.text(deep=False, strip=True),
                 'stage_order': index,
                 'stage_current': 'current' in item.attrs.get('class', ''),
                 } for i, stages_beg in enumerate(block.css(CSS_STAGES_ITEMS))
                for index, item in enumerate(stages_beg.css('a[href]')) if item.attrs['href'] != JAVASCRIPT_VOID
            ]
        if stage_group:
            return ret_main

    ret_short: list[ChampionshipStageBetexplorer] = []
    if (block := soup.node.css_first(CSS_STAGES_SHORT_ITEMS)) is not None:
        ret_short = [
                {'stage_id': None,
                 'stage_url': item.attrs['href'],
                 'stage_name': item.text(deep=False, strip=True),
                 'stage_order': index,
                 'stage_current': 'current' in item.attrs.get('class', ''),
                 } for index, item in enumerate(block.css('a[href]'))
            ]
        if ret_short[-1]['stage_name'] == 'All results' or ret_short[-1]['stage_name'] == 'All fixtures':
            ret_short = [ret_short[-1]]

    if not ret_short:
        return ret_main

    if not ret_main:
        return ret_short

    index = next((i for i, item in enumerate(ret_main) if item['stage_current']), None)
    if index is not None:
        old = ret_main.pop(index)
        if len(ret_short) == 1:
            ret_short[0]['stage_name'] = old['stage_name']

    ret_main.extend(ret_short)
    return ret_main


def parsing_date_results(item: Node, creation_date: datetime.datetime) -> Optional[datetime.datetime]:
    """Расшифровать колонку дата в результатах.

    :param item: Колонка с датой
    :param creation_date: Дата создания страницы
    """
    date_game: str = item.text(deep=False, strip=True)
    if (reg := REG_DATE.match(date_game)) is not None:
        return datetime.datetime(int(reg[3]), int(reg[2]), int(reg[1]))
    if (reg := REG_DATE_SHORT.match(date_game)) is not None:
        return datetime.datetime(int(creation_date.year), int(reg[2]), int(reg[1]))
    if date_game == 'Today':
        return datetime.datetime(creation_date.year, creation_date.month, creation_date.day)
    if date_game == 'Yesterday':
        tmp: datetime.datetime = creation_date - datetime.timedelta(days=1)
        return datetime.datetime(tmp.year, tmp.month, tmp.day)
    print(f'Не могу определить дату сыгранной игры {date_game}', flush=True)
    return None


def parsing_date_fixtures(item: Node,  # noqa: PLR0911
                          creation_date: datetime.datetime,
                          default: datetime.datetime) -> Optional[datetime.datetime]:
    """Расшифровать колонку дата в расписании.

    :param item: Колонка с датой
    :param creation_date: Дата создания страницы
    :param default: Дата по умолчанию для случая когда колонка пустая
    """
    date_game: str = item.text(deep=False, strip=True)
    if (reg := REG_DATE_SHORT_FIXTURES.match(date_game)) is not None:
        return datetime.datetime(int(creation_date.year), int(reg[2]), int(reg[1]), int(reg[3]), int(reg[4]))
    if (reg := REG_DATE_FIXTURES.match(date_game)) is not None:
        return datetime.datetime(int(reg[3]), int(reg[2]), int(reg[1]), int(reg[4]), int(reg[5]))
    if (reg := REG_TODAY_FIXTURES.match(date_game)) is not None:
        return datetime.datetime(creation_date.year, creation_date.month, creation_date.day, int(reg[1]),
                                 int(reg[2]))
    if (reg := REG_TOMORROW_FIXTURES.match(date_game)) is not None:
        tmp: datetime.datetime = creation_date + datetime.timedelta(days=1)
        return datetime.datetime(tmp.year, tmp.month, tmp.day, int(reg[1]), int(reg[2]))
    if (reg := REG_YESTERDAY_FIXTURES.match(date_game)) is not None:
        tmp: datetime.datetime = creation_date - datetime.timedelta(days=1)
        return datetime.datetime(tmp.year, tmp.month, tmp.day, int(reg[1]), int(reg[2]))
    if not date_game:
        return default
    print(f'Не могу определить дату в расписании {date_game}', flush=True)
    return None


def parsing_date_match(item: Node) -> Optional[datetime.datetime]:
    """Расшифровать колонку дата в полной информации о матче (с таймами).

    :param item: Колонка с датой
    """
    if (((link := item.css_first('p.list-details__item__date')) is not None)
            and (reg := REG_DATE_MATCH.match(link.attrs.get('data-dt'))) is not None):
        return datetime.datetime(int(reg[3]), int(reg[2]), int(reg[1]), int(reg[4]), int(reg[5]))
    print(f'Не могу определить дату в полной информации о матче (с таймами) {item.html}', flush=True)
    return None


def parsing_round(item: Node) -> tuple[Optional[str], Optional[int]]:
    """Расшифровать колонку дата в результатах.

    :param item: Колонка с датой
    """
    round_name: str = item.child.text(deep=False, strip=True)
    round_number: int = int(rnd[0]) if (rnd := REG_ROUND.match(
        round_name)) is not None else None
    return round_name, round_number


def get_column_type(sport_id: SportType, is_fixture: int, column_number: int) -> Optional[int]:
    """Определить тип колонки.

    :param sport_id: Вид спорта
    :param is_fixture: Строка это результат (0) или расписание (1)
    :param column_number: Номер колонки (от 0)
    """
    return COLUMN_MAPPING.get(
        (is_fixture, column_number, sport_id in SPORTS_3),
    )


def parsing_score_halves(item: Node) -> list[ScoreHalvesBetexplorer]:
    """Расшифровать колонку счет по таймам.

    :param item: Колонка со счетами
    """
    if (((link := item.css_first(CSS_SCORE_HALVES_ITEMS)) is not None)
            and (reg := REG_SCORE_HALVES.findall(link.text(deep=False, strip=True)))):
        return [
            {
                'time_id': None,
                'half_number': number,
                'home_score': int(score[1]),
                'away_score': int(score[2]),
            } for number, score in enumerate(reg)
        ]
    return []


def parsing_team_data(node: Node) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """Разбор информации об команде.

    :param node: Данные для разбора
    """
    team_name: Optional[str] = link.text(deep=True, strip=True) if (
            (link := node.css_first('h2.list-details__item__title')) is not None) else None
    team_url: Optional[str] = link.attrs['href'] if ((link := node.css_first('a[href]')) is not None) else None
    team_emblem, team_full = (link.attrs.get('src'), link.attrs.get('alt')) if (
            (link := node.css_first('img')) is not None) else (None, None)
    return team_url, team_name, team_emblem, team_full


def parsing_team_match(item: Node) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Разбор результата игры.

    :param item: Данные для разбора
    """
    match_url: str = item.child.attrs['href']
    (home_team_name,
     away_team_name) = [
        el.text(strip=True) for el in item.child.iter(include_text=False)
    ]
    return match_url, home_team_name, away_team_name


def parsing_score(node: Node) -> tuple[Optional[int], Optional[int]]:
    """Разбор результата игры.

    :param node: Данные для разбора
    """
    home_score, away_score = [int(goals) if goals else None for goals in el.split(':')] if (
        el := node.text(deep=False, strip=True)) else (None, None)
    return home_score, away_score


def parsing_score_stage(item: Node) -> tuple[Optional[int], Optional[int], Optional[str], Optional[str]]:
    """Разбор результата игры с дополнительным временем.

    :param item: Данные для разбора
    :return ScoreStage: Разобранный результат
    """
    home_score, away_score = parsing_score(item.child)
    score_stage_short, score_stage = (link.text(deep=False, strip=True), link.attrs.get('title')) if (
            (link := next(item.child.iter(include_text=False), None)) is not None) else (
        None, None)
    return home_score, away_score, score_stage_short, score_stage


def get_column_type_shooters(sport_id: SportType, tab_index: int, column_number: int) -> Optional[int]:
    """Определить тип колонки для информации об голах.

    :param sport_id: Вид спорта
    :param tab_index: Строка это результат (0) или расписание (1)
    :param column_number: Номер колонки (от 0)
    """
    return COLUMN_MAPPING_SHOOTER.get(
        (tab_index, column_number, sport_id in SPORTS_SHOOTERS_3),
    )


def parsing_shooters(sport_id: SportType, table_data: Node, tab_index: int) -> list[ShooterBetexplorer]:
    """Разбор забивающих голы.

    :param sport_id: Вид спорта
    :param table_data: Данные для разбора
    :param tab_index: Номер колонки
    """
    shooters: list[ShooterBetexplorer] = []
    for event_order, event_item in enumerate(table_data.iter(include_text=False)):
        shooter: ShooterBetexplorer = {
            'shooter_id': None,
            'home_away': tab_index,
            'event_order': event_order,
            'event_time': None,
            'overtime': None,
            'player_name': None,
            'penalty_kick': None,
        }
        for index, item in enumerate(event_item.iter(include_text=False)):
            column_type: Optional[int] = get_column_type_shooters(sport_id, tab_index, index)
            if column_type == COLUMN_PENALTY_KICK:
                if pen := item.text(deep=True, strip=True):
                    shooter['penalty_kick'] = pen
            elif column_type == COLUMN_EVENT_TIME:
                event_time: str = item.text(deep=True, strip=True)
                if (reg := REG_EVENT_TIME.match(event_time)) is not None:
                    shooter['event_time'] = reg[1]
                elif (reg := REG_EVENT_TIME_OVERTIME.match(event_time)) is not None:
                    shooter['event_time'] = reg[1]
                    shooter['overtime'] = reg[2]
                elif (reg := REG_EVENT_TIME_MIN_SEC.match(event_time)) is not None:
                    shooter['event_time'] = event_time
                elif event_time and event_time not in ['.', '446226.', '446227.', '+2.']:
                    shooter['event_time'] = event_time
                    print(f'Не найдено время {event_time}')
            elif column_type == COLUMN_PLAYER_NAME:
                shooter['player_name'] = item.text(deep=True, strip=True)
        shooters.append(shooter)
    return shooters


# @profile
def parsing_results(
        soup: Optional[ReceivedData],
        sport_id: SportType,
        championship_id: int,
        stage_name: Optional[str],
        is_fixture: int) -> list[MatchBetexplorer]:
    """Разбор страницы результатов матчей чемпионата.

    :param soup: Данные для разбора
    :param sport_id: Вид спорта
    :param championship_id: Идентификатор чемпионата
    :param stage_name: Имя стадии чемпионата
    :param is_fixture: Строка это результат (0) или расписание (1)
    """
    if soup is not None:
        matches: list[MatchBetexplorer] = []
        if (table_result := soup.node.css_first(
                CSS_RESULT if is_fixture == IS_RESULT else CSS_FIXTURE)) is not None:
            round_name: Optional[str] = None
            round_number: Optional[int] = None
            saved_date: Optional[datetime.datetime] = None
            for season_table in table_result.iter(include_text=False):
                if season_table.child.tag == 'th':
                    round_name, round_number = parsing_round(season_table)
                else:
                    match: MatchBetexplorer = match_init(
                        sport_id.value, championship_id, stage_name, round_name, round_number, is_fixture,
                        soup.creation_date)
                    for index, item in enumerate(season_table.iter(include_text=False)):
                        column_type: Optional[int] = get_column_type(sport_id, is_fixture, index)

                        if column_type == COLUMN_TEAMS:
                            (match['match_url'],
                             match['home_team']['team_name'],
                             match['away_team']['team_name'],
                             ) = parsing_team_match(item)
                        elif column_type == COLUMN_SCORE:
                            (match['home_score'], match['away_score'],
                             match['score_stage_short'], match['score_stage']) = parsing_score_stage(item)
                        elif column_type == COLUMN_ODDS_1:
                            match['odds_1'] = parsing_odds(item)
                        elif column_type == COLUMN_ODDS_X:
                            match['odds_x'] = parsing_odds(item)
                        elif column_type == COLUMN_ODDS_2:
                            match['odds_2'] = parsing_odds(item)
                        elif column_type == COLUMN_GAME_DATE:
                            if is_fixture == IS_RESULT:
                                match['game_date'] = parsing_date_results(
                                    item, soup.creation_date)
                            else:
                                match['game_date'] = parsing_date_fixtures(
                                    item, soup.creation_date, saved_date)
                                saved_date = match['game_date']
                    matches.append(match)
        return matches
    return []


def match_init(
        sport_id: int,
        championship_id: int,
        stage_name: str,
        round_name: str,
        round_number: int,
        is_fixture: int,
        creation_date: datetime.datetime) -> MatchBetexplorer:
    """Инициализация информации об матче.

    :param sport_id: Вид спорта
    :param championship_id: Идентификатор чемпионата
    :param stage_name: Стадия чемпионата (квалификация, групповой этап и прочие)
    :param round_name: Название тура
    :param round_number: Номер тура
    :param is_fixture: Строка это результат (0) или расписание (1)
    :param creation_date: Дата загрузки информации
    """
    return {
        'match_id': None,
        'championship_id': championship_id,
        'match_url': None,
        'home_team': {
            'team_id': None,
            'sport_id': sport_id,
            'team_name': None,
            'team_full': None,
            'team_url': None,
            'team_country': None,
            'country_id': None,
            'team_emblem': None,
            'download_date': creation_date,
            'save_date': datetime.datetime.now(),
        },
        'home_team_emblem': None,
        'away_team': {
            'team_id': None,
            'sport_id': sport_id,
            'team_name': None,
            'team_full': None,
            'team_url': None,
            'team_country': None,
            'country_id': None,
            'team_emblem': None,
            'download_date': creation_date,
            'save_date': datetime.datetime.now(),
        },
        'away_team_emblem': None,
        'home_score': None, 'away_score': None,
        'odds_1': None, 'odds_x': None, 'odds_2': None,
        'game_date': None,
        'score_stage': None, 'score_stage_short': None,
        'score_halves': [],
        'shooters': [],
        'stage_name': stage_name,
        'round_name': round_name,
        'round_number': round_number,
        'is_fixture': is_fixture,
        'download_date': creation_date,
        'save_date': datetime.datetime.now(),
    }


async def get_results(ls: LoadSave,
                      championship_url: str,
                      sport_id: SportType,
                      championship_id: int,
                      is_fixture: int,
                      need_refresh: bool) -> Optional[ResultsBetexplorer]:
    """Загрузка и разбор результатов.

    :param ls: Класс для загрузки данных
    :param championship_url: Путь к странице чемпионата
    :param sport_id: Вид спорта
    :param championship_id: Идентификатор чемпионата
    :param is_fixture: Строка это результат (0) или расписание (1)
    :param need_refresh: Необходимо обновить данные по чемпионату
    """
    result_url: str = urljoin(urlparse(championship_url).path, 'results' if is_fixture == IS_RESULT else 'fixtures')
    load_results: Optional[ReceivedData]
    if (load_results := await ls.get_read(result_url, CSS_RESULTS, need_refresh)) is not None:
        stages: list[ChampionshipStageBetexplorer] = parsing_stages(load_results)
        if stages:
            main_stage: Optional[int] = next((i for i, item in enumerate(stages) if item['stage_name'] == 'Main'), None)
            if main_stage is not None:
                load_results = await ls.get_read(urljoin(result_url, stages[main_stage]['stage_url']), CSS_RESULTS, need_refresh)
                if load_results is None:
                    print(f'Закладка Main пустая {result_url} {stages[main_stage]["stage_url"]}', flush=True)
                stages = parsing_stages(load_results)
            matches = []
            for stage in stages:
                if (load_results := await ls.get_read(
                        urljoin(result_url, stage['stage_url']), CSS_RESULTS, need_refresh)) is not None:
                    matches.extend(parsing_results(load_results, sport_id, championship_id, stage['stage_name'], is_fixture))
            return {
                'stages': stages,
                'matches': matches,
            }
        return {
            'stages': [],
            'matches': parsing_results(load_results, sport_id, championship_id, None, is_fixture),
        }
    return None


async def get_results_fixtures(ls: LoadSave,
                               championship_url: str,
                               sport_id: SportType,
                               championship_id: int,
                               need_refresh: bool = False) -> Optional[ResultsBetexplorer]:
    """Получение результатов и расписания.

    :param ls: Класс для загрузки данных
    :param championship_url: Страница чемпионата
    :param sport_id: Вид спорта
    :param championship_id: Идентификатор чемпионата
    :param need_refresh: Данные по чемпионату необходимо обновить
    """
    results: Optional[ResultsBetexplorer]
    fixtures: Optional[ResultsBetexplorer]
    if ((results := await get_results(ls, championship_url, sport_id, championship_id, IS_RESULT,
                                      need_refresh)) is not None
            and (
                    fixtures := await get_results(ls, championship_url, sport_id, championship_id, IS_FIXTURE,
                                                  need_refresh)) is not None):
        matches: list[MatchBetexplorer] = results['matches'][:]
        matches.extend(fixtures['matches'])
        # await self.get_standing(championship['championship_url'], need_refresh)
        if not matches:
            print(f'No matches {championship_url}', flush=True)

        return ResultsBetexplorer(
            stages=fixtures['stages'],
            matches=matches,
        )
    print(f'results or fixtures is None {championship_url}', flush=True)
    return None


async def parsing_standings_stage(
        ls: LoadSave, soup: ReceivedData, need_refresh: bool = False) -> Optional[ReceivedData]:
    """Получить одну страницу стадии турнирной таблицы.

    :param ls: Класс для загрузки данных
    :param soup: Данные для разбора
    :param need_refresh: Необходимо обновить данные
    """
    if ((st := soup.node.css_first('div.glib-stats-content')) is not None) and (
            (link := st.css_first('a[href]')) is not None):
        pars_table = link.attrs.get('href')
        return await ls.get_read(pars_table, '', need_refresh)
    return None


async def get_standing(ls: LoadSave, championship_url: str, need_refresh: bool) -> Optional[ReceivedData]:
    """Получение таблицы текущего положения команд.

    :param ls: Класс для загрузки данных
    :param championship_url: Ссылка на таблицу чемпионата
    :param need_refresh: Необходимо обновить данные
    """
    stats_table: Optional[ReceivedData]
    if (stats_table := await ls.get_read(urlparse(championship_url).path,
                                         CSS_PAGE_STANDING), need_refresh) is not None:
        stages: list[ChampionshipStageBetexplorer] = parsing_stages(stats_table)
        if stages:
            for stage in stages:
                if (stats_table := await ls.get_read(urljoin(urlparse(championship_url).path, stage['stage_url']),
                                                     CSS_PAGE_STANDING)) is not None:
                    await parsing_standings_stage(ls, stats_table, need_refresh)
        else:
            await parsing_standings_stage(ls, stats_table, need_refresh)
    return None


def parsing_match_time(
        soup: ReceivedData,
        sport_id: SportType,
        championship_id: int,
        stage_name: str,
        round_name: str,
        round_number: int,
        is_fixture: int) -> Optional[MatchBetexplorer]:
    """Разбор страницы конкретного матча по таймам.

    :param soup: Данные для разбора
    :param sport_id: Вид спорта
    :param championship_id: Идентификатор чемпионата
    :param stage_name: Стадия чемпионата (квалификация, групповой этап и прочие)
    :param round_name: Название тура
    :param round_number: Номер тура
    :param is_fixture: Строка это результат (0) или расписание (1)
    """
    match: MatchBetexplorer = match_init(sport_id.value, championship_id, stage_name,
                                         round_name, round_number, is_fixture, soup.creation_date)
    data: Node
    if (data := soup.node.css_first('ul.list-details')) is not None:
        for index, item in enumerate(data.iter(include_text=False)):
            if index == 0:
                match['home_team']['team_url'], match['home_team']['team_name'], match['home_team']['team_emblem'], \
                    match['home_team']['team_full'] = parsing_team_data(item)
                match['home_team_emblem'] = match['home_team']['team_emblem']
            elif index == 1:
                match['game_date'] = parsing_date_match(item)
                if (link := item.css_first('p.list-details__item__score')) is not None:
                    match['home_score'], match['away_score'] = parsing_score(link)
                if (link := item.css_first('h2.list-details__item__eventstage')) is not None:
                    match['score_stage'] = link.text(deep=False, strip=True)
                match['score_halves'] = parsing_score_halves(item)
            else:
                match['away_team']['team_url'], match['away_team']['team_name'], match['away_team']['team_emblem'], \
                    match['away_team']['team_full'] = parsing_team_data(item)
                match['away_team_emblem'] = match['away_team']['team_emblem']

    if (data := soup.node.css_first(CSS_SHOOTERS)) is not None:
        for tab_index, tab_item in enumerate(data.iter(include_text=False)):
            if (table_data := tab_item.css_first('table tbody')) is not None:
                match['shooters'].extend(parsing_shooters(sport_id, table_data, tab_index))
    return match


def update_match_time(match: Optional[MatchBetexplorer], match_time: Optional[MatchBetexplorer]) -> None:
    """Обновление данных о матче на основании детальной информации.

    :param match: Текущая информация о матче из таблицы результатов
    :param match_time: Информация для обновления из детальной информации
    """
    if match_time is not None:
        if match_time['home_team']['team_name'] is not None:
            match['home_team']['team_name'] = match_time['home_team']['team_name']
        if match_time['home_team']['team_full'] is not None:
            match['home_team']['team_full'] = match_time['home_team']['team_full']
        if match_time['home_team']['team_url'] is not None:
            match['home_team']['team_url'] = match_time['home_team']['team_url']
        if match_time['home_team']['team_emblem'] is not None:
            match['home_team']['team_emblem'] = match_time['home_team']['team_emblem']
        if match_time['home_team']['download_date'] is not None:
            match['home_team']['download_date'] = match_time['home_team']['download_date']
        if match_time['home_team']['save_date'] is not None:
            match['home_team']['save_date'] = match_time['home_team']['save_date']

        if match_time['home_team_emblem'] is not None:
            match['home_team_emblem'] = match_time['home_team_emblem']

        if match_time['away_team']['team_name'] is not None:
            match['away_team']['team_name'] = match_time['away_team']['team_name']
        if match_time['away_team']['team_full'] is not None:
            match['away_team']['team_full'] = match_time['away_team']['team_full']
        if match_time['away_team']['team_url'] is not None:
            match['away_team']['team_url'] = match_time['away_team']['team_url']
        if match_time['away_team']['team_emblem'] is not None:
            match['away_team']['team_emblem'] = match_time['away_team']['team_emblem']
        if match_time['away_team']['download_date'] is not None:
            match['away_team']['download_date'] = match_time['away_team']['download_date']
        if match_time['away_team']['save_date'] is not None:
            match['away_team']['save_date'] = match_time['away_team']['save_date']

        if match_time['away_team_emblem'] is not None:
            match['away_team_emblem'] = match_time['away_team_emblem']

        if match_time['game_date'] is not None:
            match['game_date'] = match_time['game_date']
        if match_time['score_stage'] is not None:
            match['score_stage'] = match_time['score_stage']

        match['score_halves'] = match_time['score_halves']
        match['shooters'] = match_time['shooters']


def parsing_team(soup: ReceivedData, sport_id: int) -> Optional[TeamBetexplorer]:
    """Разбор страницы команды.

    :param soup: Данные для разбора
    :param sport_id: Вид спорта
    """
    if (item := soup.node.css_first(CSS_PAGE_TEAM_BEG)) is not None:
        team: TeamBetexplorer = {
            'team_id': None,
            'sport_id': sport_id,
            'team_name': None,
            'team_full': None,
            'team_url': None,
            'team_country': None,
            'country_id': None,
            'team_emblem': None,
            'download_date': None,
            'save_date': None,
        }
        if (reg := REG_COMMAND_COUNTRY.match(item.text(strip=True))) is not None:
            team['team_full'] = reg[1]
            team['team_country'] = reg[2]
            if (team_emblem := soup.node.css_first('img[src]')) is not None:
                team['team_emblem'] = team_emblem.attrs['src']
        team['download_date'] = soup.creation_date
        team['save_date'] = datetime.datetime.now()
        return team
    return None


async def get_team(ls: LoadSave,
                   crd: CRUDbetexplorer,
                   session: Optional[AsyncSession],
                   teams: list[TeamBetexplorer],
                   fast_country: dict[str, int],
                   fast_team: dict[(int, str, str, str), Optional[TeamBetexplorer]]) -> None:
    """Обновление данных о команде.

    :param ls: Класс для загрузки данных
    :param crd: Класс для сохранения данных
    :param session: Текущая сессия базы данных
    :param teams: Список команд для обновления
    :param fast_country: Справочник стран
    :param fast_team: Справочник закаченных команд
    """
    team: TeamBetexplorer
    for team in teams:
        if (team_update := fast_team.get(team['team_url'])) is None:
            if (team['team_url'] is not None) and ((load_team := await ls.get_read(team['team_url'],
                                                                                   CSS_PAGE_TEAM)) is not None) and (
                    (team_update := parsing_team(load_team, team['sport_id'])) is not None):
                if team_update['team_emblem'] is not None:
                    await ls.get_as_file(team_update['team_emblem'])
                team.update({
                    'download_date': team_update['download_date'],
                    'save_date': team_update['save_date'],
                    'team_full': team_update['team_full'],
                    'team_country': team_update['team_country'],
                    'team_emblem': team_update['team_emblem'],
                    'country_id': fast_country.get(team_update['team_country']),
                })
            await crd.team_merge(session, team)
            fast_team[team['team_url']] = team.copy()
        else:
            team.update({
                'download_date': team_update['download_date'],
                'save_date': team_update['save_date'],
                'team_id': team_update['team_id'],
                'team_full': team_update['team_full'],
                'team_country': team_update['team_country'],
                'team_emblem': team_update['team_emblem'],
                'country_id': team_update['country_id'],
            })


async def get_match_time(
        ls: LoadSave,
        sport_id: SportType,
        championship: ChampionshipBetexplorer,
        match: MatchBetexplorer,
        need_refresh: bool,  # noqa: FBT001
) -> Optional[MatchBetexplorer]:
    """Загрузка и разбор информации по тайм-матч.

    :param ls: Класс для загрузки данных
    :param sport_id: Вид спорта
    :param championship: Информация о чемпионате
    :param match: Информация о матче
    :param need_refresh: Необходимо обновить данные
    """
    if match['match_url'] is not None:
        load_match: Optional[ReceivedData]
        if (load_match := await ls.get_read(match['match_url'], CSS_MATCH, need_refresh)) is not None:
            match_time: Optional[MatchBetexplorer] = parsing_match_time(
                load_match, sport_id, championship['championship_id'], match['stage_name'],
                match['round_name'], match['round_number'], match['is_fixture'])
            if need_refresh and match_time['game_date'] + datetime.timedelta(days=1) > match_time['download_date']:
                return await get_match_time(ls, sport_id, championship, match, True)  # noqa: FBT003
            return match_time
    return None


async def get_match_line(
        ls: LoadSave,
        sport_id: SportType,
        championship: ChampionshipBetexplorer,
        match: MatchBetexplorer,
        need_refresh: bool,  # noqa: FBT001
) -> None:
    """Загрузка и разбор информации по линии.

    :param ls: Класс для загрузки данных
    :param sport_id: Вид спорта
    :param championship: Информация о чемпионате
    :param match: Информация о матче
    :param need_refresh: Необходимо обновить данные
    """
    if match['match_url'] is not None:
        await ls.get_read(urljoin('/match-odds-old/', [x for x in urlparse(match['match_url']).path.split('/') if x][-1] + '/1/ou/1/'), '')  # noqa: E501
        await ls.get_read(urljoin('/match-odds-old/', [x for x in urlparse(match['match_url']).path.split('/') if x][-1] + '/1/ah/1/'), '')  # noqa: E501
        await ls.get_read(urljoin('/match-odds-old/', [x for x in urlparse(match['match_url']).path.split('/') if x][-1] + '/1/bts/1/'), '')  # noqa: E501
    # await ls.get_read(
    #     self, urljoin('/match-odds/', [x for x in urlparse(match['match_url']).path.split('/') if x][-1] + '/1/ou/'),
    #     '',
    #     need_refresh)


async def get_championships(
        root_dir: str,
        database: Optional[str],
        config_engine: Optional[dict],
        load_net: bool,
        save_database: DatabaseUsage,
        sport_id: SportType,
        country: CountryBetexplorer,
        updated_years: list[str],
        fast_country: dict[str, int],
        lock: MultiLock,
) -> None:
    """Загрузка матчей.

    :param root_dir: Путь для сохранения данных на диске
    :param database: Путь к базе данных
    :param config_engine: Конфигурация движка базы данных
    :param load_net: Загрузка данных из интернета False - нет (использовать только сохраненные на диске), True - да
    :param save_database: Операции с базой данных 0 - без операций, 1 - только читать, 2 - читать и записывать
    :param sport_id: Вид спорта
    :param country: Информация о стране
    :param updated_years: Список годов чемпионатов для обновления
    :param fast_country: Массив идентификаторов-названий стран
    :param lock: Действия требующие монополизма
    """
    ls = LoadSave(
        root_url='https://www.betexplorer.com',
        root_dir=root_dir,
    )
    await ls.load_data(load_net=load_net, lock=lock)

    db = DatabaseSessionManager()
    if save_database != DATABASE_NOT_USE:
        db.init(database, **config_engine)
    crd = CRUDbetexplorer(save_database=save_database)

    async with db.get_session() if save_database != DATABASE_NOT_USE else nullcontext() as session:
        load_seasons: Optional[ReceivedData]
        if (load_seasons := await ls.get_read(country['country_url'], CSS_CHAMPIONSHIPS, True)) is not None:
            championships: list[ChampionshipBetexplorer] = parsing_championships(
                load_seasons, sport_id.value, country['country_id'])
            await crd.insert_championship(session, sport_id, country['country_id'], championships)

            fast_team: dict[(int, str, str, str), Optional[TeamBetexplorer]] = {}
            championship: ChampionshipBetexplorer
            for championship in championships:
                need_refresh: bool = any(year in championship['championship_years'] for year in updated_years)

                results: Optional[ResultsBetexplorer]
                if (results := await get_results_fixtures(
                        ls,
                        championship['championship_url'], sport_id,
                        championship['championship_id'], need_refresh)) is not None:
                    match: MatchBetexplorer
                    for match in results['matches']:
                        match_time: Optional[MatchBetexplorer]
                        if (match_time := await get_match_time(ls, sport_id, championship, match, False)) is not None:
                            update_match_time(match, match_time)
                            await get_team(
                                ls, crd, session,
                                [match['home_team'], match['away_team']], fast_country, fast_team)
                            await get_match_line(ls, sport_id, championship, match, False)
                    if save_database != DATABASE_NOT_USE:
                        async with session.begin():
                            await crd.add_championship_stages(session, championship['championship_id'], results['stages'])
                            await crd.add_matches(session, championship['championship_id'], results['matches'])
    await db.close()
    await ls.close_session()


def wrapper(async_func: Callable, *args: Any) -> None:
    """Обвертка для запуска асинхронной функции.

    :param async_func: Асинхронная функция для запуска
    :param args: Параметры функции
    """
    asyncio.run(async_func(*args))


def register_signal_handler() -> None:
    """Что бы не было ошибки по ctr+c в мультипоточном режиме."""
    signal.signal(signal.SIGINT, lambda _, __: None)


async def load_data(
        root_dir: str,
        database: Optional[str] = None,
        sport_type: Optional[list[SportType]] = None,
        load_net: bool = False,
        save_database: DatabaseUsage = DATABASE_NOT_USE,
        create_tables: int = 0,
        config_engine: Optional[dict] = None,
        start_updating: Optional[datetime.datetime] = None,
        exclude_countries: Optional[tuple] = None,
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
    if start_updating is None:
        updated_years = []
    else:
        updated_years = [str(x) for x in range(start_updating.year, start_updating.year + 6)]
    if exclude_countries is None:
        exclude_countries = ()
    if sport_type is None:
        sport_type = [SportType.FOOTBALL]

    ls = LoadSave(
        root_url='https://www.betexplorer.com',
        root_dir=root_dir,
    )
    manager: SyncManager = Manager()
    lock: MultiLock = manager.Lock()
    await ls.load_data(load_net=load_net, lock=lock)

    db = DatabaseSessionManager()
    if save_database != DATABASE_NOT_USE:
        db.init(database, **config_engine)
        if create_tables == 1:
            await db.created_db_tables()
    crd: CRUDbetexplorer = CRUDbetexplorer(save_database=save_database)
    pool: ProcessPoolExecutor = ProcessPoolExecutor(max_workers=processes, initializer=register_signal_handler)
    # noinspection PyTypeChecker
    loop: ProactorEventLoop = asyncio.get_running_loop()
    futures: list[Future] = []

    async with db.get_session() if save_database != DATABASE_NOT_USE else nullcontext() as session:
        await crd.sports_insert_all(session, SPORTS)
        sport_id: SportType
        for sport_id in sport_type:
            countries: list[CountryBetexplorer]
            if (countries := await get_countries(ls, sports_url[sport_id])) is not None:
                await crd.country_insert_all(session, sport_id, countries)
                fast_country: dict[str, int] = {country['country_name']: country['country_id'] for country in countries}
                country: CountryBetexplorer
                for country in list(filter(lambda x: x['country_name'] not in exclude_countries, countries)):
                    if processes == 1:
                        await get_championships(
                            root_dir, database, config_engine, load_net, save_database,
                            sport_id, country, updated_years, fast_country, lock
                        )
                    else:
                        futures.append(loop.run_in_executor(  # noqa: PERF401
                            pool, wrapper, get_championships,
                            root_dir, database, config_engine, load_net, save_database,
                            sport_id, country, updated_years, fast_country, lock)  # noqa: COM812
                        )
    if futures:
        await asyncio.wait(futures)
    await crd.analyze_match(session)

    pool.shutdown()
    manager.shutdown()
    await db.close()
    await ls.close_session()
# temp = timeit.timeit("soup.node.css_first('.table-main')", globals={'soup': soup}, number=200000)
