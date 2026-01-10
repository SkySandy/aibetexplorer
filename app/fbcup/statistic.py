"""Расчет статистики перед матчем."""
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING

from app.fbcup.utils import calc_avg, calc_avg_percent

if TYPE_CHECKING:
    from app.betexplorer.schemas import MatchBetexplorer

type MatchId = int
"""Тип для идентификатора матча."""


@dataclass
class GoalStatistics:
    """Статистика голов."""

    count_matches: int = 0
    """Количество матчей."""
    goals_scored: int = 0
    """Забито голов."""
    goals_conceded: int = 0
    """Пропущено голов."""
    goals_scored_avg: float = 0.00
    """Среднее количество забитых голов за матч."""
    goals_conceded_avg: float = 0.00
    """Среднее количество пропущенных голов за матч."""
    goals_total_avg: float = 0.00
    """Средний тотал за матч."""
    win: int = 0
    """Количество выигранных матчей."""
    draw: int = 0
    """Количество ничейных матчей."""
    defeat: int = 0
    """Количество проигранных матчей."""
    win_percent: int = 33
    """Процент выигранных матчей."""
    draw_percent: int = 33
    """Процент ничейных матчей."""
    defeat_percent: int = 33
    """Процент проигранных матчей."""
    goals_scored_win: int = 0
    """Забито голов при победе."""
    goals_conceded_win: int = 0
    """Пропущено голов при победе."""
    goals_scored_draw: int = 0
    """Забито голов при ничьи."""
    goals_conceded_draw: int = 0
    """Пропущено голов при ничьи."""
    goals_scored_defeat: int = 0
    """Забито голов при поражении."""
    goals_conceded_defeat: int = 0
    """Пропущено голов при поражении."""
    goals_scored_win_avg: float = 0.00
    """Среднее количество забитых голов при победе."""
    goals_conceded_win_avg: float = 0.00
    """Среднее количество пропущенных голов при победе."""
    goals_scored_draw_avg: float = 0.00
    """Среднее количество забитых голов при ничьи."""
    goals_conceded_draw_avg: float = 0.00
    """Среднее количество пропущенных голов при ничьи."""
    goals_scored_defeat_avg: float = 0.00
    """Среднее количество забитых голов при поражении."""
    goals_conceded_defeat_avg: float = 0.00
    """Среднее количество пропущенных голов при поражении."""


@dataclass
class FieldTypeTotals:
    """Статистика при игре На нейтральном поле, дома, в гостях."""

    all: GoalStatistics = field(default_factory=GoalStatistics)
    """Все матчи (поле не важно)."""
    home: GoalStatistics = field(default_factory=GoalStatistics)
    """Матчи дома."""
    away: GoalStatistics = field(default_factory=GoalStatistics)
    """Матчи в гостях."""


@dataclass
class MatchStatistics:
    """Статистика перед матчем для домашней и гостевой команды."""

    home_prematch: FieldTypeTotals
    """"Статистика для домашней команды перед матчем."""
    away_prematch: FieldTypeTotals
    """"Статистика для гостевой команды перед матчем."""


PERCENT_TOTAL = 100


def _update_stats(
        stats: GoalStatistics,
        team_score: int,
        opp_score: int,
) -> None:
    """Обновляет статистику и вычисляет средние значения.

    :param stats: Раздел статистики
    :param team_score: Количество голов забитых командой
    :param opp_score: Количество голов пропущенных командой
    """
    stats.count_matches += 1
    stats.goals_scored += team_score
    stats.goals_conceded += opp_score

    if team_score > opp_score:
        stats.win += 1
        stats.goals_scored_win += team_score
        stats.goals_conceded_win += opp_score
    elif team_score == opp_score:
        stats.draw += 1
        stats.goals_scored_draw += team_score
        stats.goals_conceded_draw += opp_score
    else:
        stats.defeat += 1
        stats.goals_scored_defeat += team_score
        stats.goals_conceded_defeat += opp_score

    matches_count = stats.count_matches

    stats.goals_scored_avg = calc_avg(stats.goals_scored, matches_count)
    stats.goals_conceded_avg = calc_avg(stats.goals_conceded, matches_count)
    stats.goals_total_avg = float(
        Decimal(stats.goals_scored_avg) + Decimal(stats.goals_conceded_avg),
    )

    # Расчет процентов исходов
    if matches_count != 0:
        stats.win_percent = calc_avg_percent(stats.win, matches_count)
        stats.defeat_percent = calc_avg_percent(stats.defeat, matches_count)
        stats.draw_percent = PERCENT_TOTAL - (
            stats.win_percent + stats.defeat_percent
        )
    else:
        # Если матчей не было, то вероятность результата одинакова и равна 33 процентов
        stats.win_percent = 33
        stats.defeat_percent = 33
        stats.draw_percent = 33

    # Расчет средних по исходам
    stats.goals_scored_win_avg = calc_avg(stats.goals_scored_win, stats.win)
    stats.goals_conceded_win_avg = calc_avg(
        stats.goals_conceded_win, stats.win,
    )
    stats.goals_scored_draw_avg = calc_avg(stats.goals_scored_draw, stats.draw)
    stats.goals_conceded_draw_avg = calc_avg(
        stats.goals_conceded_draw, stats.draw,
    )
    stats.goals_scored_defeat_avg = calc_avg(
        stats.goals_scored_defeat, stats.defeat,
    )
    stats.goals_conceded_defeat_avg = calc_avg(
        stats.goals_conceded_defeat, stats.defeat,
    )


def _update_team_stat(team_stats: FieldTypeTotals, match_info: MatchBetexplorer, is_home: bool) -> None:
    """Обновляет статистику команды для всех разделов.

    :param team_stats: Статистика команды
    :param match_info: Данные матча
    :param is_home: Флаг домашней команды
    """
    team_score: int = match_info['home_score'] if is_home else match_info['away_score']
    opp_score: int = match_info['away_score'] if is_home else match_info['home_score']

    # Обновляем общую статистику и статистику по типу поля
    _update_stats(team_stats.all, team_score, opp_score)
    _update_stats(team_stats.home if is_home else team_stats.away, team_score, opp_score)


def calculate_league_prematch_stats(
        championship_matches: list[MatchBetexplorer],
) -> dict[MatchId, MatchStatistics]:
    """Рассчитывает предматчевую статистику для всех матчей чемпионата.

    :param championship_matches: Список матчей чемпионата (должны быть отсортированы в хронологическом порядке)
    :return: Словарь статистических показателей перед матчами, где ключ - match_id
    """
    # Инициализация хранилища статистики для команд
    team_stats: dict[int, FieldTypeTotals] = defaultdict(FieldTypeTotals)
    match_statistics: dict[MatchId, MatchStatistics] = {}

    for match_detail in championship_matches:
        # Извлекаем идентификаторы команд
        home_team_id: int = match_detail['home_team_id']
        away_team_id: int = match_detail['away_team_id']

        # Сохраняем статистику для текущего матча
        match_id: MatchId = match_detail['match_id']
        match_statistics[match_id] = MatchStatistics(
            home_prematch=deepcopy(team_stats[home_team_id]),
            away_prematch=deepcopy(team_stats[away_team_id]),
        )
        # Пропускаем обновление статистики матча без счета
        if match_detail['home_score'] is None or match_detail['away_score'] is None:
            continue

        # Обновляем статистику команд после матча
        _update_team_stat(team_stats[home_team_id], match_detail, is_home=True)
        _update_team_stat(team_stats[away_team_id], match_detail, is_home=False)

    return match_statistics
