"""Схемы описания структур данных для парсинга и хранения информации с BetExplorer.

Модуль содержит типизированные структуры данных (TypedDict) для описания всех сущностей
системы: видов спорта, стран, чемпионатов, команд, матчей и связанных с ними событий.
Также включает перечисление видов спорта и константы для типов событий в матчах.
"""
import enum
from typing import TYPE_CHECKING, Final, TypedDict

if TYPE_CHECKING:
    import datetime


class SportType(enum.Enum):
    """Перечисление поддерживаемых видов спорта."""

    FOOTBALL = 1
    BASKETBALL = 2
    HOCKEY = 3
    TENNIS = 4
    BASEBALL = 5
    VOLLEYBALL = 6
    HANDBALL = 7


sports_url = {
    SportType.FOOTBALL: '/football/',
    SportType.BASKETBALL: '/basketball/',
    SportType.HOCKEY: '/hockey/',
    SportType.TENNIS: '/tennis/',
    SportType.BASEBALL: '/baseball/',
    SportType.VOLLEYBALL: '/volleyball/',
    SportType.HANDBALL: '/handball/',
}
"""Словарь URL-путей для каждого вида спорта на сайте BetExplorer."""


class SportBetexplorer(TypedDict):
    """Структура данных для описания вида спорта."""

    sport_id: int | None
    """Уникальный идентификатор вида спорта в базе данных."""
    sport_name: str
    """Наименование вида спорта на английском языке."""
    sport_url: str
    """URL-путь к странице вида спорта на сайте BetExplorer."""


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
"""Список всех поддерживаемых видов спорта с их идентификаторами и URL-путями."""


class CountryBetexplorer(TypedDict):
    """Структура данных для описания страны."""

    country_id: int | None
    """Уникальный идентификатор страны в базе данных."""
    country_url: str
    """URL-путь к странице со всеми чемпионатами страны на сайте BetExplorer."""
    country_name: str
    """Наименование страны на английском языке."""
    country_order: int
    """Порядковый номер страны в списке стран."""
    country_flag_url: str
    """URL-путь к изображению флага страны."""


class ChampionshipBetexplorer(TypedDict):
    """Структура данных для описания чемпионата."""

    championship_id: int | None
    """Уникальный идентификатор чемпионата в базе данных."""
    sport_id: int | None
    """Идентификатор вида спорта."""
    country_id: int | None
    """Идентификатор страны."""
    championship_url: str
    """URL-путь к странице чемпионата на сайте BetExplorer."""
    championship_name: str
    """Наименование чемпионата."""
    championship_order: int
    """Порядковый номер чемпионата в списке."""
    championship_years: str
    """Период проведения чемпионата."""


class TeamBetexplorer(TypedDict):
    """Структура данных для описания команды."""

    team_id: int | None
    """Уникальный идентификатор команды в базе данных."""
    sport_id: int | None
    """Идентификатор вида спорта."""
    team_name: str | None
    """Краткое наименование команды."""
    team_full: str | None
    """Полное наименование команды."""
    team_url: str | None
    """URL-путь к странице команды на сайте BetExplorer."""
    team_country: str | None
    """Наименование страны команды."""
    country_id: int | None
    """Идентификатор страны."""
    team_emblem: str | None
    """URL-путь к эмблеме команды."""
    download_date: datetime.datetime | None
    """Дата и время загрузки информации о команде."""
    save_date: datetime.datetime | None
    """Дата и время последнего обновления информации в базе данных."""


class ScoreHalvesBetexplorer(TypedDict):
    """Структура данных для описания результата по таймам или периодам."""

    time_id: int | None
    """Уникальный идентификатор записи в базе данных."""
    half_number: int
    """Номер тайма или периода."""
    home_score: int
    """Количество очков, забитых домашней командой."""
    away_score: int
    """Количество очков, забитых гостевой командой."""


class ShooterBetexplorer(TypedDict):
    """Структура данных для описания информации о голах или заброшенных шайбах."""

    shooter_id: int | None
    """Уникальный идентификатор записи в базе данных."""
    home_away: int | None
    """Признак команды: 0 - домашняя, 1 - гостевая."""
    event_time: str | None
    """Время наступления события."""
    overtime: str | None
    """Дополнительное время."""
    player_name: str | None
    """Фамилия игрока, забившего гол."""
    penalty_kick: str | None
    """Признак гола с пенальти."""
    event_order: int
    """Порядковый номер события в матче."""


class ChampionshipStageBetexplorer(TypedDict):
    """Структура данных для описания стадии чемпионата."""

    stage_id: int | None
    """Уникальный идентификатор стадии в базе данных."""
    stage_url: str
    """URL-путь к странице стадии на сайте BetExplorer."""
    stage_name: str
    """Наименование стадии."""
    stage_order: int
    """Порядковый номер стадии."""
    stage_current: bool
    """Признак текущей стадии."""


EVENT_BTC: Final[int] = 0
"""Идентификатор типа события: обе команды забьют."""
EVENT_OU: Final[int] = 1
"""Идентификатор типа события: больше-меньше."""
EVENT_AH: Final[int] = 2
"""Идентификатор типа события: азиатская фора."""


class MatchEventBetexplorer(TypedDict):
    """Структура данных для описания статистических событий матча."""

    match_event_id: int | None
    """Уникальный идентификатор события в базе данных."""
    match_id: int | None
    """Идентификатор матча."""
    event_type_id: int | None
    """Идентификатор типа события (обе забьют, тотал, фора)."""
    indicator: str | None
    """Значение показателя (линия тотала, значение форы)."""
    odds_less: float | None
    """Коэффициент на исход меньше."""
    odds_greater: float | None
    """Коэффициент на исход больше."""


class MatchBetexplorer(TypedDict):
    """Структура данных для описания матча."""

    match_id: int
    """Уникальный идентификатор матча в базе данных."""
    championship_id: int
    """Идентификатор чемпионата."""
    match_url: str
    """URL-путь к странице матча на сайте BetExplorer."""
    home_team_id: int
    """Идентификатор домашней команды."""
    home_team: TeamBetexplorer
    """Информация о домашней команде."""
    home_team_emblem: str | None
    """URL-путь к эмблеме домашней команды."""
    away_team_id: int
    """Идентификатор гостевой команды."""
    away_team: TeamBetexplorer
    """Информация о гостевой команде."""
    away_team_emblem: str | None
    """URL-путь к эмблеме гостевой команды."""
    home_score: int | None
    """Количество очков, забитых домашней командой."""
    away_score: int | None
    """Количество очков, забитых гостевой командой."""
    odds_1: float | None
    """Коэффициент на победу домашней команды."""
    odds_x: float | None
    """Коэффициент на ничью."""
    odds_2: float | None
    """Коэффициент на победу гостевой команды."""
    game_date: datetime.datetime | None
    """Дата и время проведения матча."""
    score_stage: str | None
    """Примечания к результату матча (победа по пенальти, прерывание и т.д.)."""
    score_stage_short: str | None
    """Краткое примечание к результату."""
    stage_name: str
    """Наименование стадии чемпионата."""
    score_halves: list[ScoreHalvesBetexplorer]
    """Список результатов по таймам или периодам."""
    shooters: list[ShooterBetexplorer]
    """Список информации о голах или заброшенных шайбах."""
    match_event: list[MatchEventBetexplorer]
    """Список статистических событий матча."""
    download_date: datetime.datetime | None
    """Дата и время загрузки информации о матче."""
    save_date: datetime.datetime | None
    """Дата и время последнего обновления информации в базе данных."""
    round_name: str | None
    """Наименование тура."""
    round_number: int | None
    """Номер тура."""
    is_fixture: int
    """Признак типа записи: 0 - результат, 1 - расписание."""


class ResultsBetexplorer(TypedDict):
    """Структура данных для описания результатов чемпионата со стадиями."""

    stages: list[ChampionshipStageBetexplorer]
    """Список стадий чемпионата."""
    matches: list[MatchBetexplorer]
    """Список матчей."""
