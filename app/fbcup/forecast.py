"""Расчет предсказаний результатов матчей."""

from decimal import ROUND_HALF_UP, Decimal
from typing import TypedDict

from app.betexplorer.schemas import MatchBetexplorer
from app.fbcup.rating import MatchRating


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


class GoalStatistics(TypedDict):
    """Статистика голов."""

    count_matches: int
    """Количество матчей."""
    goals_scored: int
    """Забито голов."""
    goals_conceded: int
    """Пропущено голов."""
    goals_scored_avg: float
    """Среднее количество забитых голов за матч."""
    goals_conceded_avg: float
    """Среднее количество пропущенных голов за матч."""
    goals_total_avg: float
    """Средний тотал за матч."""
    win: int
    """Количество выигранных матчей."""
    draw: int
    """Количество ничейных матчей."""
    defeat: int
    """Количество проигранных матчей."""
    win_percent: int
    """Процент выигранных матчей."""
    draw_percent: int
    """Процент ничейных матчей."""
    defeat_percent: int
    """Процент проигранных матчей."""
    goals_scored_win: int
    """Забито голов при победе."""
    goals_conceded_win: int
    """Пропущено голов при победе."""
    goals_scored_draw: int
    """Забито голов при ничьи."""
    goals_conceded_draw: int
    """Пропущено голов при ничьи."""
    goals_scored_defeat: int
    """Забито голов при поражении."""
    goals_conceded_defeat: int
    """Пропущено голов при поражении."""
    goals_scored_win_avg: float
    """Среднее количество забитых голов при победе."""
    goals_conceded_win_avg: float
    """Среднее количество пропущенных голов при победе."""
    goals_scored_draw_avg: float
    """Среднее количество забитых голов при ничьи."""
    goals_conceded_draw_avg: float
    """Среднее количество пропущенных голов при ничьи."""
    goals_scored_defeat_avg: float
    """Среднее количество забитых голов при поражении."""
    goals_conceded_defeat_avg: float
    """Среднее количество пропущенных голов при поражении."""


class FieldTypeTotals(TypedDict):
    """Статистика при игре На нейтральном поле, дома, в гостях."""

    all: GoalStatistics
    """Все матчи (поле не важно)."""
    home: GoalStatistics
    """Матчи дома."""
    away: GoalStatistics
    """Матчи в гостях."""

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
    home_total: FieldTypeTotals
    """"Статистика для домашней команды."""
    away_total: FieldTypeTotals
    """"Статистика для гостевой команды."""

def get_team_matches_before_match(
        match_details: list[MatchBetexplorer], team_id: int, match_id: int) -> list[MatchBetexplorer]:
    """Находим все матчи команды до указанного матча.

    :param match_details: Список матчей чемпионата (должны быть отсортированы в хронологическом порядке)
    :param team_id: Идентификатор команды
    :param match_id: Анализируемый матч
    """
    team_matches = []
    for m in match_details:
        if m['match_id'] == match_id:
            break
        if m['home_score'] is None or m['away_score'] is None:
            continue
        if m['home_team']['team_id'] == team_id or m['away_team']['team_id'] == team_id:
            team_matches.append(m)
    return team_matches


def init_goal_statistic() -> GoalStatistics:
    """Инициализация данных статистики."""
    return {
        'count_matches': 0,
        'goals_scored': 0,
        'goals_conceded': 0,
        'goals_scored_avg': 0,
        'goals_conceded_avg': 0,
        'goals_total_avg': 0,
        'win': 0,
        'draw': 0,
        'defeat': 0,
        'win_percent': 0,
        'draw_percent': 0,
        'defeat_percent': 0,
        'goals_scored_win': 0,
        'goals_conceded_win': 0,
        'goals_scored_draw': 0,
        'goals_conceded_draw': 0,
        'goals_scored_defeat': 0,
        'goals_conceded_defeat': 0,
        'goals_scored_win_avg': 0,
        'goals_conceded_win_avg': 0,
        'goals_scored_draw_avg': 0,
        'goals_conceded_draw_avg': 0,
        'goals_scored_defeat_avg': 0,
        'goals_conceded_defeat_avg': 0,
    }

def init_statistic() -> FieldTypeTotals:
    """Инициализация данных для расчета статистики."""
    return {
        'all': init_goal_statistic(),
        'home': init_goal_statistic(),
        'away': init_goal_statistic(),
    }

def recalc_statistics(statistics_section: GoalStatistics, det: MatchBetexplorer, is_home: bool ) -> None:  # noqa: FBT001
    """Пересчитать статистику.

    :param statistics_section: Раздел статистики
    :param det: Информация о матче
    :param is_home: Команда для которой считаем играет дома (True) или в гостях (False)
    """
    statistics_section['count_matches'] += 1

    if is_home:
        statistics_section['goals_scored'] += det['home_score']
        statistics_section['goals_conceded'] += det['away_score']
        if det['home_score'] > det['away_score']:
            statistics_section['win'] += 1
            statistics_section['goals_scored_win'] += det['home_score']
            statistics_section['goals_conceded_win'] += det['away_score']
        if det['home_score'] == det['away_score']:
            statistics_section['draw'] += 1
            statistics_section['goals_scored_draw'] += det['home_score']
            statistics_section['goals_conceded_draw'] += det['away_score']
        if det['home_score'] < det['away_score']:
            statistics_section['defeat'] += 1
            statistics_section['goals_scored_defeat'] += det['home_score']
            statistics_section['goals_conceded_defeat'] += det['away_score']
    else:
        statistics_section['goals_scored'] += det['away_score']
        statistics_section['goals_conceded'] += det['home_score']
        if det['home_score'] < det['away_score']:
            statistics_section['win'] += 1
            statistics_section['goals_scored_win'] += det['away_score']
            statistics_section['goals_conceded_win'] += det['home_score']
        if det['home_score'] == det['away_score']:
            statistics_section['draw'] += 1
            statistics_section['goals_scored_draw'] += det['away_score']
            statistics_section['goals_conceded_draw'] += det['home_score']
        if det['home_score'] > det['away_score']:
            statistics_section['defeat'] += 1
            statistics_section['goals_scored_defeat'] += det['away_score']
            statistics_section['goals_conceded_defeat'] += det['home_score']


def scan_matches(matches: list[MatchBetexplorer], total: FieldTypeTotals, team_id:int) -> None:
    """Обновляет статистику по результатам матчей команды с учетом домашнего или гостевого статуса.

    :params matches: Список матчей команды.
    :params total: Структура для накопления статистики по типу поля и исходу
    :params team_id: Идентификатор команды для которой рассчитываем статистику
    """
    for det in matches:
        statistics_section = None
        is_home = None
        if team_id == det['home_team']['team_id']:
            statistics_section = total['home']
            is_home = True
        elif team_id == det['away_team']['team_id']:
            statistics_section = total['away']

        recalc_statistics(total['all'], det, is_home)
        if statistics_section is not None:
            recalc_statistics(statistics_section, det, is_home)

PRECISION = Decimal('.01')

def calc_avg_2(itog: int, count: int) -> float:
    """Посчитывает среднее с округлением до двух знаков."""
    if count != 0:
        return float((Decimal(itog) / Decimal(count)).quantize(PRECISION, ROUND_HALF_UP))
    return 0

def calc_avg_percent(itog: int, count: int) -> int:
    """Посчитывает среднее с округлением до целого.

    :param itog: Итого
    :param count: Количество
    """
    if count != 0:
        return int((Decimal(itog) / Decimal(count) * Decimal(100)).quantize(Decimal('1'), ROUND_HALF_UP))
    return 0

def recalc_avg(statistics_section: GoalStatistics) -> None:
    """Подсчитать среднее и проценты.

    :param statistics_section: Раздел статистики (будет изменён)
    """
    count_matches = statistics_section['count_matches']

    statistics_section['goals_scored_avg'] = calc_avg_2(statistics_section['goals_scored'], count_matches)
    statistics_section['goals_conceded_avg'] = calc_avg_2(statistics_section['goals_conceded'], count_matches)
    statistics_section['goals_total_avg'] = float(Decimal(statistics_section['goals_scored_avg']) + Decimal(statistics_section['goals_conceded_avg']))

    statistics_section['win_percent'] = calc_avg_percent(statistics_section['win'], count_matches)
    statistics_section['defeat_percent'] = calc_avg_percent(statistics_section['defeat'], count_matches)
    statistics_section['draw_percent'] = 100 - (statistics_section['win_percent'] + statistics_section['defeat_percent'])

    statistics_section['goals_scored_win_avg'] = calc_avg_2(statistics_section['goals_scored_win'], statistics_section['win'])
    statistics_section['goals_conceded_win_avg'] = calc_avg_2(statistics_section['goals_conceded_win'], statistics_section['win'])
    statistics_section['goals_scored_draw_avg'] = calc_avg_2(statistics_section['goals_scored_draw'], statistics_section['draw'])
    statistics_section['goals_conceded_draw_avg'] = calc_avg_2(statistics_section['goals_conceded_draw'], statistics_section['draw'])
    statistics_section['goals_scored_defeat_avg'] = calc_avg_2(statistics_section['goals_scored_defeat'], statistics_section['defeat'])
    statistics_section['goals_conceded_defeat_avg'] = calc_avg_2(statistics_section['goals_conceded_defeat'], statistics_section['defeat'])

def calc_avg(total: FieldTypeTotals) -> None:
    """Подсчитать среднее и проценты.

    :params total: Структура для накопления статистики по типу поля и исходу
    """
    recalc_avg(total['all'])
    recalc_avg(total['home'])
    recalc_avg(total['away'])

def cals_forecast_all(
        match_details: list[MatchBetexplorer], detail: MatchBetexplorer) -> (FieldTypeTotals, FieldTypeTotals):
    """Расчет прогноза (все игры).

    :param match_details: Список матчей чемпионата (должны быть отсортированы в хронологическом порядке)
    :param detail: Информация о матче
    """
    home_matches: list[MatchBetexplorer] = get_team_matches_before_match(
        match_details, detail['home_team']['team_id'], detail['match_id'])
    away_matches: list[MatchBetexplorer] = get_team_matches_before_match(
        match_details, detail['away_team']['team_id'], detail['match_id'])
    home_total: FieldTypeTotals = init_statistic()
    away_total: FieldTypeTotals = init_statistic()
    scan_matches(home_matches, home_total, detail['home_team']['team_id'])
    scan_matches(away_matches, away_total, detail['away_team']['team_id'])
    calc_avg(home_total)
    calc_avg(away_total)
    return home_total, away_total


def calc_forecast(match_forecasts: list[MatchForecast], match_ratings: list[MatchRating],
                  match_details: list[MatchBetexplorer], detail: MatchBetexplorer) -> MatchForecast:
    """Рассчитывает прогноз на матч и добавляет в список прогнозов.

    :param match_forecasts: Список прогнозов на матчи (должны быть отсортированы в хронологическом порядке)
    :param match_ratings: Список рейтингов матчей (должны быть отсортированы в хронологическом порядке)
    :param match_details: Список матчей чемпионата (должны быть отсортированы в хронологическом порядке)
    :param detail: Информация о матче
    """
    home_total, away_total = cals_forecast_all(match_details, detail)
    m_f: MatchForecast = {
        'match_id': detail['match_id'],
        'forecast': None,
        'forecast_rating': None,
        'forecast_all': None,
        'forecast_all_rating': None,
        'forecast_average': None,
        'home_total': home_total,
        'away_total': away_total,
    }
    match_forecasts.append(m_f)
    return m_f
