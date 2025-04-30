"""Расчет статистики перед матчем."""

from decimal import Decimal
from typing import TypedDict

from app.betexplorer.schemas import MatchBetexplorer
from app.fbcup.utils import calc_avg, calc_avg_percent


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


class MatchStatistics(TypedDict):
    """Статистика перед матчем для домашней и гостевой команды."""

    match_id: int
    """Идентификатор матча."""
    home_statistics: FieldTypeTotals
    """"Статистика для домашней команды."""
    away_statistics: FieldTypeTotals
    """"Статистика для гостевой команды."""


def get_team_matches_before_match(
        championship_matches: list[MatchBetexplorer], team_id: int, match_id: int) -> list[MatchBetexplorer]:
    """Находим все матчи команды до указанного матча.

    :param championship_matches: Список матчей чемпионата (должны быть отсортированы в хронологическом порядке)
    :param team_id: Идентификатор команды для которой выбираем матчи
    :param match_id: Идентификатор анализируемого матча
    """
    team_matches = []
    for match in championship_matches:
        if match['match_id'] == match_id:
            break
        if match['home_score'] is None or match['away_score'] is None:
            continue
        if match['home_team']['team_id'] == team_id or match['away_team']['team_id'] == team_id:
            team_matches.append(match)
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


def update_team_stats(
        team_stats: GoalStatistics,
        match_info: MatchBetexplorer,
        playing_at_home: bool,  # noqa: FBT001
) -> None:
    """Пересчитать статистику.

    :param team_stats: Раздел статистики
    :param match_info: Информация о матче
    :param playing_at_home: Команда для которой считаем играет дома (True) или в гостях (False)
    """
    team_stats['count_matches'] += 1

    team_score: int = match_info['home_score'] if playing_at_home else match_info['away_score']
    opp_score: int = match_info['away_score'] if playing_at_home else match_info['home_score']

    team_stats['goals_scored'] += team_score
    team_stats['goals_conceded'] += opp_score

    if team_score > opp_score:
        team_stats['win'] += 1
        team_stats['goals_scored_win'] += team_score
        team_stats['goals_conceded_win'] += opp_score
    elif team_score == opp_score:
        team_stats['draw'] += 1
        team_stats['goals_scored_draw'] += team_score
        team_stats['goals_conceded_draw'] += opp_score
    else:
        team_stats['defeat'] += 1
        team_stats['goals_scored_defeat'] += team_score
        team_stats['goals_conceded_defeat'] += opp_score


def scan_matches(matches: list[MatchBetexplorer], team_statistics: FieldTypeTotals, team_id: int) -> None:
    """Обновляет статистику по результатам матчей команды с учетом домашнего или гостевого статуса.

    :param matches: Список матчей команды.
    :param team_statistics: Структура для накопления статистики по типу поля и исходу
    :param team_id: Идентификатор команды для которой рассчитываем статистику
    """
    for match_info in matches:
        if team_id == match_info['home_team']['team_id']:
            team_stats = team_statistics['home']
            playing_at_home = True
        else:
            team_stats = team_statistics['away']
            playing_at_home = False

        update_team_stats(team_statistics['all'], match_info, playing_at_home)
        update_team_stats(team_stats, match_info, playing_at_home)


PERCENT_TOTAL = 100


def update_goal_statistics_averages(statistics: GoalStatistics) -> None:
    """Вычисляет и обновляет средние значения и проценты в разделе статистики голов.

    :param statistics: Раздел статистики (будет изменён)
    """
    count_matches = statistics['count_matches']

    statistics['goals_scored_avg'] = calc_avg(statistics['goals_scored'], count_matches)
    statistics['goals_conceded_avg'] = calc_avg(statistics['goals_conceded'], count_matches)
    statistics['goals_total_avg'] = float(
        Decimal(statistics['goals_scored_avg']) + Decimal(statistics['goals_conceded_avg']),
    )

    if statistics['win'] == 0 and statistics['draw'] == 0 and statistics['defeat'] == 0:
        statistics['win_percent'] = 33
        statistics['defeat_percent'] = 33
        statistics['draw_percent'] = 33
    else:
        statistics['win_percent'] = calc_avg_percent(statistics['win'], count_matches)
        statistics['defeat_percent'] = calc_avg_percent(statistics['defeat'], count_matches)
        statistics['draw_percent'] = PERCENT_TOTAL - (statistics['win_percent'] + statistics['defeat_percent'])

    statistics['goals_scored_win_avg'] = calc_avg(statistics['goals_scored_win'], statistics['win'])
    statistics['goals_conceded_win_avg'] = calc_avg(statistics['goals_conceded_win'], statistics['win'])
    statistics['goals_scored_draw_avg'] = calc_avg(statistics['goals_scored_draw'], statistics['draw'])
    statistics['goals_conceded_draw_avg'] = calc_avg(statistics['goals_conceded_draw'], statistics['draw'])
    statistics['goals_scored_defeat_avg'] = calc_avg(statistics['goals_scored_defeat'], statistics['defeat'])
    statistics['goals_conceded_defeat_avg'] = calc_avg(statistics['goals_conceded_defeat'], statistics['defeat'])


def update_all_field_statistics(total: FieldTypeTotals) -> None:
    """Вычисляет и обновляет средние значения и проценты для всех типов поля.

    :params total: Структура для накопления статистики
    """
    update_goal_statistics_averages(total['all'])
    update_goal_statistics_averages(total['home'])
    update_goal_statistics_averages(total['away'])


def calc_teams_statistics_before_match(
        championship_matches: list[MatchBetexplorer],
        detail: MatchBetexplorer,
) -> tuple[FieldTypeTotals, FieldTypeTotals]:
    """Расчет статистики для команд участвующих в матче на основе предыдущих игр.

    :param championship_matches: Список матчей чемпионата (должны быть отсортированы в хронологическом порядке)
    :param detail: Информация о матче, для которого рассчитывается статистика
    """
    home_team_id: int = detail['home_team']['team_id']
    away_team_id: int = detail['away_team']['team_id']
    match_id: int = detail['match_id']

    home_matches: list[MatchBetexplorer] = get_team_matches_before_match(championship_matches, home_team_id, match_id)
    away_matches: list[MatchBetexplorer] = get_team_matches_before_match(championship_matches, away_team_id, match_id)

    home_statistics: FieldTypeTotals = init_statistic()
    away_statistics: FieldTypeTotals = init_statistic()

    scan_matches(home_matches, home_statistics, home_team_id)
    scan_matches(away_matches, away_statistics, away_team_id)

    update_all_field_statistics(home_statistics)
    update_all_field_statistics(away_statistics)

    return home_statistics, away_statistics


def create_match_statistics(
        match_statistics: list[MatchStatistics],
        championship_matches: list[MatchBetexplorer],
        detail: MatchBetexplorer,
) -> MatchStatistics:
    """Рассчитывает статистику перед матчем и добавляет в список статистических показателей матчей.

    Мутирует входной список `match_statistics`, добавляя в него новый элемент.

    :param match_statistics: Список статистических показателей перед матчами
    :param championship_matches: Список матчей чемпионата (должны быть отсортированы в хронологическом порядке)
    :param detail: Информация о матче
    """
    if detail['match_id'] == 1627053:
        pass
    home_statistics, away_statistics = calc_teams_statistics_before_match(championship_matches, detail)
    match_stat: MatchStatistics = {
        'match_id': detail['match_id'],
        'home_statistics': home_statistics,
        'away_statistics': away_statistics,
    }
    match_statistics.append(match_stat)
    return match_stat
