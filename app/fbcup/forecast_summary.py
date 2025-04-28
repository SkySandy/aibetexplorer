"""Итоги предсказания матчей."""
from typing import TypedDict

from app.betexplorer.schemas import MatchBetexplorer
from app.fbcup.forecast import MatchForecast
from app.fbcup.statistic import calc_avg_percent


class ForecastSummaryDetailed(TypedDict):
    """Подробная расшифровка прогнозов."""

    count: int
    """Количество угаданных прогнозов."""
    percent: int
    """Процент угаданных прогнозов."""


class ForecastGoalsDetailed(TypedDict):
    """Подробная расшифровка прогнозов."""

    goals_scored: int
    """Всего забито голов домашней командой."""
    goals_conceded: int
    """Всего забито голов командой гостей."""
    goal_difference: int
    """Разница между забитыми и пропущенными голами."""
    goal_total: int
    """Всего голов забитых обеими командами."""


class ForecastTotalDetailed(TypedDict):
    """Подробная расшифровка тотала в прогнозе."""

    count: int
    """Предсказано всего."""
    under_percent: int
    """Процент предсказанного тотала меньше реального."""
    equals_percent: int
    """Процент предсказанного тотала равного реальному."""
    over_percent: int
    """Процент предсказанного тотала больше реального."""


class ForecastResultDetailed(TypedDict):
    """Подробно о результатах в прогнозе."""

    count: int
    """Предсказано всего."""
    count_correct: int
    """Количество угаданных прогнозов."""
    correct_percent: int
    """Процент угаданных прогнозов."""


class ForecastSummary(TypedDict):
    """Итоги предсказания матчей."""

    match_count: int
    """Всего матчей."""
    goals: ForecastGoalsDetailed
    """Суммарная информация о голах."""
    goals_forecast: ForecastGoalsDetailed
    """Суммарная информация о предсказанных голах."""
    exact_score: ForecastSummaryDetailed
    """Точный счет футбольного матча."""
    differences: ForecastSummaryDetailed
    """Предсказанные разницы."""
    outcomes: ForecastSummaryDetailed
    """Предсказанные исходы."""
    sum_forecast: ForecastSummaryDetailed
    """Итого предсказано."""
    win: ForecastResultDetailed
    """Предсказанные победы."""
    draw: ForecastResultDetailed
    """Предсказанные ничьи."""
    defeat: ForecastResultDetailed
    """Предсказанные поражения."""
    total: ForecastTotalDetailed
    """Итого предсказано."""
    total_home: ForecastTotalDetailed
    """Предсказано тотал домашней команды."""
    total_away: ForecastTotalDetailed
    """Итого тотал команды гостей."""


def calc_total_percent(under: int, equals: int, over: int) -> dict[str, int]:
    """Рассчитывает процентное распределение «меньше», «равно» и «больше» по количеству каждого случая.

    :param under:Количество случаев «меньше».
    :param equals: Количество случаев «равно».
    :param over: Количество случаев «больше».
    """
    count = under + equals + over
    return {
        'under_percent': calc_avg_percent(under, count),
        'equals_percent': calc_avg_percent(equals, count),
        'over_percent': calc_avg_percent(over, count),
    }


def calc_forecast_summary(
        match_details: list[MatchBetexplorer],
        match_forecasts: list[MatchForecast],
) -> ForecastSummary:
    """Рассчитать итого прогнозирования матчей.

    :param match_details: Список результатов матчей
    :param match_forecasts: Список матчей с предсказанными результатами
    """
    goals_scored = 0
    goals_conceded = 0
    goals_scored_forecast = 0
    goals_conceded_forecast = 0
    match_count = 0
    exact_score_count = 0
    differences_count = 0
    outcomes_count = 0
    total_count = 0
    total_under = 0
    total_over = 0
    total_home_count = 0
    total_home_under = 0
    total_home_over = 0
    total_away_count = 0
    total_away_under = 0
    total_away_over = 0
    win_count = 0
    win_count_correct = 0
    draw_count = 0
    draw_count_correct = 0
    defeat_count = 0
    defeat_count_correct = 0

    forecast_map = {f['match_id']: f for f in match_forecasts}
    for detail in match_details:
        home_score = detail['home_score']
        away_score = detail['away_score']
        if home_score is None or away_score is None:
            continue
        forecast = forecast_map[detail['match_id']]

        match_count += 1
        goals_scored += home_score
        goals_conceded += away_score

        home_score_forecast = forecast['forecast']['home_forecast']
        away_score_forecast = forecast['forecast']['away_forecast']
        goals_scored_forecast += home_score_forecast
        goals_conceded_forecast += away_score_forecast

        # Точный счет
        if home_score == home_score_forecast and away_score == away_score_forecast:
            exact_score_count += 1

        # Предсказанная разница
        elif (home_score - away_score) == (home_score_forecast - away_score_forecast):
            differences_count += 1

        # Предсказанный исход
        elif (
                ((home_score > away_score) and (home_score_forecast > away_score_forecast))
                or ((home_score == away_score) and (home_score_forecast == away_score_forecast))
                or ((home_score < away_score) and (home_score_forecast < away_score_forecast))):
            outcomes_count += 1

        # Предсказано общий тотал
        if home_score + away_score == home_score_forecast + away_score_forecast:
            total_count += 1
        elif home_score + away_score < home_score_forecast + away_score_forecast:
            total_under += 1
        else:
            total_over += 1

        # Предсказано тотал домашней команды
        if home_score == home_score_forecast:
            total_home_count += 1
        elif home_score < home_score_forecast:
            total_home_under += 1
        else:
            total_home_over += 1

        # Предсказано тотал гостевой команды
        if away_score == away_score_forecast:
            total_away_count += 1
        elif away_score < away_score_forecast:
            total_away_under += 1
        else:
            total_away_over += 1

        if home_score_forecast > away_score_forecast:
            win_count += 1
            if home_score > away_score:
                win_count_correct += 1
        elif home_score_forecast == away_score_forecast:
            draw_count += 1
            if home_score == away_score:
                draw_count_correct += 1
        else:
            defeat_count += 1
            if home_score < away_score:
                defeat_count_correct += 1

    goal_difference = goals_scored - goals_conceded
    goal_total = goals_scored + goals_conceded
    goal_difference_forecast = goals_scored_forecast - goals_conceded_forecast
    goal_total_forecast = goals_scored_forecast + goals_conceded_forecast

    total_percents = calc_total_percent(total_under, total_count, total_over)
    total_home_percents = calc_total_percent(total_home_under, total_home_count, total_home_over)
    total_away_percents = calc_total_percent(total_away_under, total_away_count, total_away_over)

    win_correct_percent = calc_avg_percent(win_count_correct, win_count)
    draw_correct_percent = calc_avg_percent(draw_count_correct, draw_count)
    defeat_correct_percent = calc_avg_percent(defeat_count_correct, defeat_count)

    m_f: ForecastSummary = {
        'match_count': match_count,
        'goals': {
            'goals_scored': goals_scored,
            'goals_conceded': goals_conceded,
            'goal_difference': goal_difference,
            'goal_total': goal_total,

        },
        'goals_forecast': {
            'goals_scored': goals_scored_forecast,
            'goals_conceded': goals_conceded_forecast,
            'goal_difference': goal_difference_forecast,
            'goal_total': goal_total_forecast,

        },
        'exact_score': {
            'count': exact_score_count,
            'percent': calc_avg_percent(exact_score_count, match_count),
        },
        'differences': {
            'count': differences_count,
            'percent': calc_avg_percent(differences_count, match_count),
        },
        'outcomes': {
            'count': outcomes_count,
            'percent': calc_avg_percent(outcomes_count, match_count),
        },
        'sum_forecast': {
            'count': exact_score_count + differences_count + outcomes_count,
            'percent': calc_avg_percent(exact_score_count + differences_count + outcomes_count, match_count),
        },
        'win': {
            'count': win_count,
            'count_correct': win_count_correct,
            'correct_percent': win_correct_percent,
        },
        'draw': {
            'count': draw_count,
            'count_correct': draw_count_correct,
            'correct_percent': draw_correct_percent,
        },
        'defeat': {
            'count': defeat_count,
            'count_correct': defeat_count_correct,
            'correct_percent': defeat_correct_percent,
        },
        'total': {
            'count': total_count,
            'under_percent': total_percents['under_percent'],
            'equals_percent': total_percents['equals_percent'],
            'over_percent':  total_percents['over_percent'],
        },
        'total_home': {
            'count': total_home_count,
            'under_percent': total_home_percents['under_percent'],
            'equals_percent': total_home_percents['equals_percent'],
            'over_percent':  total_home_percents['over_percent'],
        },
        'total_away': {
            'count': total_away_count,
            'under_percent': total_away_percents['under_percent'],
            'equals_percent': total_away_percents['equals_percent'],
            'over_percent':  total_away_percents['over_percent'],
        },
    }
    return m_f
