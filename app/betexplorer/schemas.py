"""Схемы описания структур системы."""
import datetime
import enum
from typing import Optional, TypedDict, Final


class SportType(enum.Enum):
    """Виды спорта."""

    FOOTBALL: int = 1
    BASKETBALL: int = 2
    HOCKEY: int = 3
    TENNIS: int = 4
    BASEBALL: int = 5
    VOLLEYBALL: int = 6
    HANDBALL: int = 7


sports_url = {
    SportType.FOOTBALL: '/football/',
    SportType.BASKETBALL: '/basketball/',
    SportType.HOCKEY: '/hockey/',
    SportType.TENNIS: '/tennis/',
    SportType.BASEBALL: '/baseball/',
    SportType.VOLLEYBALL: '/volleyball/',
    SportType.HANDBALL: '/handball/',
}


class SportBetexplorer(TypedDict):
    """Виды спорта."""

    sport_id: Optional[int]
    """Идентификатор вида спорта."""
    sport_name: str
    """Название вида спорта."""
    sport_url: str
    """Ссылка на страницу вида спорта."""


SPORTS: list[SportBetexplorer] = [
    {
        'sport_id': SportType.FOOTBALL.value,
        'sport_name': 'Football',
        'sport_url': sports_url[SportType.FOOTBALL],
    },
    {
        'sport_id': SportType.BASKETBALL.value,
        'sport_name': 'Basketball',
        'sport_url': sports_url[SportType.BASKETBALL],
    },
    {
        'sport_id': SportType.HOCKEY.value,
        'sport_name': 'Hockey',
        'sport_url': sports_url[SportType.HOCKEY],
    },
    {
        'sport_id': SportType.TENNIS.value,
        'sport_name': 'Tennis',
        'sport_url': sports_url[SportType.TENNIS],
    },
    {
        'sport_id': SportType.BASEBALL.value,
        'sport_name': 'Baseball',
        'sport_url': sports_url[SportType.BASEBALL],
    },
    {
        'sport_id': SportType.VOLLEYBALL.value,
        'sport_name': 'Volleyball',
        'sport_url': sports_url[SportType.VOLLEYBALL],
    },
    {
        'sport_id': SportType.HANDBALL.value,
        'sport_name': 'Handball',
        'sport_url': sports_url[SportType.HANDBALL],
    },
]


class CountryBetexplorer(TypedDict):
    """Страна."""

    country_id: Optional[int]
    """Идентификатор страны."""
    country_url: str
    """Ссылка на все чемпионаты проводимые в стране."""
    country_name: str
    """Название страны."""
    country_order: int
    """Порядковый номер страны."""
    country_flag_url: str
    """Ссылка на флаг страны."""


class ChampionshipBetexplorer(TypedDict):
    """Чемпионат."""

    championship_id: Optional[int]
    """Идентификатор чемпионата."""
    sport_id: Optional[int]
    """Вид спорта."""
    country_id: Optional[int]
    """Идентификатор страны."""
    championship_url: str
    """Ссылка на страницу чемпионата."""
    championship_name: str
    """Название чемпионата."""
    championship_order: int
    """Порядковый номер чемпионата."""
    championship_years: str
    """Годы проведения чемпионата."""


class TeamBetexplorer(TypedDict):
    """Команда."""

    team_id: Optional[int]
    """Идентификатор команды."""
    sport_id: Optional[int]
    """Вид спорта."""
    team_name: Optional[str]
    """Название команды."""
    team_full: Optional[str]
    """Название команды (полное)."""
    team_url: Optional[str]
    """Ссылка на страницу команды."""
    team_country: Optional[str]
    """Страна команды."""
    country_id: Optional[int]
    """Идентификатор страны."""
    team_emblem: Optional[str]
    """"Эмблема команды."""
    download_date: Optional[datetime.datetime]
    """"Дата загрузки информации."""
    save_date: Optional[datetime.datetime]
    """"Дата сохранения информации в базе данных."""


class ScoreHalvesBetexplorer(TypedDict):
    """Результат тайма, периода, дополнительного времени."""

    time_id: Optional[int]
    """Идентификатор тайма."""
    half_number: int
    """Номер тайма."""
    home_score: int
    """Количество голов забитых домашней командой."""
    away_score: int
    """Количество голов забитых командой гостей."""


class ShooterBetexplorer(TypedDict):
    """Информация о голах, заброшенных шайбах."""

    shooter_id: Optional[int]
    """Идентификатор информации об голах."""
    home_away: Optional[int]
    """Событие домашней (0) или гостевой (1) команды."""
    event_time: Optional[str]
    """Время гола."""
    overtime: Optional[str]
    """Дополнительное время."""
    player_name: Optional[str]
    """Фамилия игрока."""
    penalty_kick: Optional[str]
    """Гол забит с пенальти."""
    event_order: int
    """Порядковый номер события."""


class ChampionshipStageBetexplorer(TypedDict):
    """Стадия чемпионата."""

    stage_id: Optional[int]
    """Идентификатор стадии чемпионата."""
    stage_url: str
    """Ссылка на стадию чемпионата."""
    stage_name: str
    """Название стадии чемпионата."""
    stage_order: int
    """Порядковый номер стадии чемпионата."""
    stage_current: bool
    """Текущая стадия чемпионата."""


EVENT_BTC: Final[int] = 0
"""Ставка: обе забьют"""
EVENT_OU: Final[int] = 1
"""Ставка: больше-меньше"""
EVENT_AH: Final[int] = 2
"""Ставка: фора"""


class MatchEventBetexplorer(TypedDict):
    """Статистика матча."""

    match_event_id: Optional[int]
    """Идентификатор события в матче."""
    match_id: Optional[int]
    """Идентификатор матча."""
    event_type_id: Optional[int]
    """Идентификатор типа события (обе забьют, тотал, фора)."""
    indicator: Optional[str]
    """Значение показателя (тотала, форы)."""
    odds_less: Optional[float]
    """Коэффициент на меньше."""
    odds_greater: Optional[float]
    """Коэффициент на больше."""


class MatchBetexplorer(TypedDict):
    """Результат матча."""

    match_id: int
    """Идентификатор матча."""
    championship_id: int
    """Идентификатор чемпионата."""
    match_url: str
    """Ссылка на матч."""
    home_team: TeamBetexplorer
    """Домашняя команда."""
    home_team_emblem: Optional[str]
    """"Эмблема домашней команды."""
    away_team: TeamBetexplorer
    """Команда гостей."""
    away_team_emblem: Optional[str]
    """"Эмблема команды гостей."""
    home_score: Optional[int]
    """Количество голов забитых домашней командой."""
    away_score: Optional[int]
    """Количество голов забитых командой гостей."""
    odds_1: Optional[float]
    """Коэффициент на победу хозяев."""
    odds_x: Optional[float]
    """Коэффициент на ничью."""
    odds_2: Optional[float]
    """Коэффициент на победу гостей."""
    game_date: Optional[datetime.datetime]
    """Дата игры."""
    score_stage: Optional[str]
    """Примечания к результату матча (победа по пенальти, игра прервалась и прочие)."""
    score_stage_short: Optional[str]
    """Примечание к результату в кратком виде."""
    stage_name: str
    """Стадия чемпионата (квалификация, групповой этап и прочие)."""
    score_halves: list[ScoreHalvesBetexplorer]
    """Таймы матча."""
    shooters: list[ShooterBetexplorer]
    """Кто забивал голы."""
    match_event: list[MatchEventBetexplorer]
    """Статистика матча."""
    download_date: Optional[datetime.datetime]
    """Дата-время загрузки информации."""
    save_date: Optional[datetime.datetime]
    """Дата-время последнего обновления."""
    round_name: Optional[str]
    """Название тура."""
    round_number: Optional[int]
    """Номер тура."""
    is_fixture: int
    """Строка это результат (0) или расписание (1)."""


class ResultsBetexplorer(TypedDict):
    """Стадии вместе с чемпионатами."""

    stages: list[ChampionshipStageBetexplorer]
    matches: list[MatchBetexplorer]
