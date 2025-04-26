"""Расчет предсказаний результатов матчей."""

from decimal import ROUND_HALF_DOWN, ROUND_HALF_UP, Decimal
from typing import TypedDict

from app.betexplorer.schemas import MatchBetexplorer
from app.fbcup.rating import MatchRating
from app.fbcup.statistic import MatchStatistics, calc_avg


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
    home_forecast: int
    """Прогноз количества голов забитых домашней командой."""
    away_forecast: int
    """Прогноз количества голов забитых командой гостей."""


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

def rounds_whole(sum_value: float, count: int) -> int:
    """Округляет до целого числа.

    :param sum_value: Итого
    :param count: Количество
    """
    if count == 0:
        return 0
    return int((Decimal(sum_value) / Decimal(count)).quantize(Decimal(1), ROUND_HALF_UP))


def rounds_goal(sum_value: float, count: int) -> int:
    """Округляет до целого числа с учетом, что 0.5 округляется в меньшую сторону.

    :param sum_value: Итого
    :param count: Количество
    """
    if count == 0:
        return 0
    return int((Decimal(sum_value) / Decimal(count)).quantize(Decimal(1), ROUND_HALF_DOWN))


def create_forecast(
        match_statistic: MatchStatistics,
) -> ForecastInfo:
    """Рассчитывает шансы команд.

    :param match_statistic: Список статистических показателей перед матчем
    """
    home = match_statistic['home_statistics']['home']
    away = match_statistic['away_statistics']['away']

    mean_divisor = 1 if home['win'] == 0 or away['defeat'] == 0 else 2

    win = {
        'percent': rounds_whole((home['win_percent'] + away['defeat_percent']), 2),
        'goals_scored': home['goals_scored_win'] + away['goals_scored_defeat'],
        'goals_conceded': home['goals_conceded_win'] + away['goals_conceded_defeat'],
        'goals_scored_avg': calc_avg(home['goals_scored_win_avg'] + away['goals_conceded_defeat_avg'], mean_divisor),
        'goals_conceded_avg': calc_avg(home['goals_conceded_win_avg'] + away['goals_scored_defeat_avg'], mean_divisor),
        'forecast_goals_home': rounds_goal(home['goals_scored_win_avg'] + away['goals_conceded_defeat_avg'], mean_divisor),
        'forecast_goals_away': rounds_goal(home['goals_conceded_win_avg'] + away['goals_scored_defeat_avg'], mean_divisor),
    }

    mean_divisor = 1 if home['draw'] == 0 or away['draw'] == 0 else 2

    draw = {
        'percent': rounds_whole((home['draw_percent'] + away['draw_percent']), 2),
        'goals_scored': home['goals_scored_draw'] + away['goals_scored_draw'],
        'goals_conceded': home['goals_conceded_draw'] + away['goals_conceded_draw'],
        'goals_scored_avg': calc_avg(home['goals_scored_draw_avg'] + away['goals_conceded_draw_avg'], mean_divisor),
        'goals_conceded_avg': calc_avg(home['goals_conceded_draw_avg'] + away['goals_scored_draw_avg'], mean_divisor),
        'forecast_goals_home': rounds_goal(home['goals_scored_draw_avg'] + away['goals_conceded_draw_avg'], mean_divisor),
        'forecast_goals_away': rounds_goal(home['goals_conceded_draw_avg'] + away['goals_scored_draw_avg'], mean_divisor),
    }

    mean_divisor = 1 if home['defeat'] == 0 or away['win'] == 0 else 2
    defeat = {
        'percent': rounds_whole((home['defeat_percent'] + away['win_percent']), 2),
        'goals_scored': home['goals_conceded_defeat'] + away['goals_scored_win'],
        'goals_conceded': home['goals_conceded_defeat'] + away['goals_scored_win'],
        'goals_scored_avg': calc_avg(home['goals_scored_defeat_avg'] + away['goals_conceded_win_avg'], mean_divisor),
        'goals_conceded_avg': calc_avg(home['goals_conceded_defeat_avg'] + away['goals_scored_win_avg'], mean_divisor),
        'forecast_goals_home': rounds_goal(home['goals_scored_defeat_avg'] + away['goals_conceded_win_avg'], mean_divisor),
        'forecast_goals_away': rounds_goal(home['goals_conceded_defeat_avg'] + away['goals_scored_win_avg'], mean_divisor),
    }

    if win['percent'] == defeat['percent']:
        goals_forecast = draw
    elif win['percent'] >= draw['percent'] and win['percent'] > defeat['percent']:
        goals_forecast = win
    elif draw['percent'] > defeat['percent']:
        goals_forecast = draw
    else:
        goals_forecast = defeat

    fi: ForecastInfo = {
        'win_prob': win['percent'],
        'draw_prob': draw['percent'],
        'defeat_prob': defeat['percent'],
        'home_score': goals_forecast['goals_scored_avg'],
        'away_score': goals_forecast['goals_conceded_avg'],
        'match_total': goals_forecast['goals_scored_avg'] + goals_forecast['goals_conceded_avg'],
        'home_forecast': goals_forecast['forecast_goals_home'],
        'away_forecast': goals_forecast['forecast_goals_away'],
    }
    return fi


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
    if detail['match_id'] == 1627199:
        pass
    forecast = create_forecast(match_statistic)

    m_f: MatchForecast = {
        'match_id': detail['match_id'],
        'forecast': forecast,
        'forecast_rating': None,
        'forecast_all': None,
        'forecast_all_rating': None,
        'forecast_average': None,
    }
    match_forecasts.append(m_f)
    return m_f

