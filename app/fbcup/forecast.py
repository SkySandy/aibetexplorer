"""Расчет предсказаний результатов матчей."""
from typing import TypedDict

from app.betexplorer.schemas import MatchBetexplorer
from app.fbcup.rating import MatchRating
from app.fbcup.statistic import MatchStatistics


class ForecastInfo(TypedDict):
    """Информация о прогнозе."""

    win_prob: int
    """Вероятность победы."""
    draw_prob: int
    """Вероятность ничьи."""
    defeat_prob: int
    """Вероятность поражения."""
    home_score: int
    """Количество голов забитых домашней командой."""
    away_score: int
    """Количество голов забитых командой гостей."""
    match_total: float | None
    """Тотал матча."""


class MatchForecast(TypedDict):
    """Предсказание результатов команд на матч."""

    match_id: int
    """Идентификатор матча."""
    forecast: ForecastInfo | None
    """"Прогноз."""
    forecast_rating: ForecastInfo | None
    """"Прогноз (рейтинг)."""
    forecast_all: ForecastInfo | None
    """"Прогноз (все игры)."""
    forecast_all_rating: ForecastInfo | None
    """"Прогноз (все игры + рейтинг)."""
    forecast_average: ForecastInfo | None
    """"Прогноз (среднее)."""


def create_team_chances(
    match_forecasts: list[MatchForecast],
    match_statistic: MatchStatistics,
    match_rating: MatchRating,
    detail: MatchBetexplorer,
) -> MatchForecast:
    """Рассчитывает шансы команд и добавляет в список всех шансов на все матчи.

    Мутирует входной список `match_forecasts`, добавляя в него новый элемент.

    :param match_forecasts: Список предсказаний результатов матчей
    :param match_statistic: Список статистических показателей перед матчем
    :param match_rating: Рейтинги команд перед матчами
    :param detail: Информация о матче
    """

