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
    """Статистика голов команды.

    Содержит исчерпывающую информацию о результативности
    команды на основе исторических данных о проведенных матчах.
    Статистика включает общие показатели, а также детализированные
    данные в зависимости от исхода матча (победа, ничья, поражение).
    """

    count_matches: int = 0
    """Количество матчей, учтенных в статистике."""
    goals_scored: int = 0
    """Количество голов, забитых командой во всех матчах."""
    goals_conceded: int = 0
    """Количество голов, пропущенных командой во всех матчах."""
    goals_scored_avg: float = 0.00
    """Среднее количество забитых голов за матч."""
    goals_conceded_avg: float = 0.00
    """Среднее количество пропущенных голов за матч."""
    goals_total_avg: float = 0.00
    """Средний тотал голов за матч (забитые + пропущенные)."""
    win: int = 0
    """Количество матчей, завершившихся победой команды."""
    draw: int = 0
    """Количество матчей, завершившихся ничьей."""
    defeat: int = 0
    """Количество матчей, завершившихся поражением команды."""
    win_percent: int = 33
    """Процент матчей, завершившихся победой команды."""
    draw_percent: int = 33
    """Процент матчей, завершившихся ничьей."""
    defeat_percent: int = 33
    """Процент матчей, завершившихся поражением команды."""
    goals_scored_win: int = 0
    """Количество голов, забитых в победных матчах."""
    goals_conceded_win: int = 0
    """Количество голов, пропущенных в победных матчах."""
    goals_scored_draw: int = 0
    """Количество голов, забитых в ничейных матчах."""
    goals_conceded_draw: int = 0
    """Количество голов, пропущенных в ничейных матчах."""
    goals_scored_defeat: int = 0
    """Количество голов, забитых в проигранных матчах."""
    goals_conceded_defeat: int = 0
    """Количество голов, пропущенных в проигранных матчах."""
    goals_scored_win_avg: float = 0.00
    """Среднее количество забитых голов в победных матчах."""
    goals_conceded_win_avg: float = 0.00
    """Среднее количество пропущенных голов в победных матчах."""
    goals_scored_draw_avg: float = 0.00
    """Среднее количество забитых голов в ничейных матчах."""
    goals_conceded_draw_avg: float = 0.00
    """Среднее количество пропущенных голов в ничейных матчах."""
    goals_scored_defeat_avg: float = 0.00
    """Среднее количество забитых голов в проигранных матчах."""
    goals_conceded_defeat_avg: float = 0.00
    """Среднее количество пропущенных голов в проигранных матчах."""


@dataclass
class FieldTypeTotals:
    """Статистика команды при игре на разных типах поля.

    Агрегирует статистику команды в трех разрезах: все матчи, домашние матчи и выездные матчи.
    Это позволяет учитывать фактор домашнего поля при анализе и прогнозировании.
    """

    all: GoalStatistics = field(default_factory=GoalStatistics)
    """Статистика по всем матчам команды, независимо от того, где проводился матч."""
    home: GoalStatistics = field(default_factory=GoalStatistics)
    """Статистика только по домашним матчам команды."""
    away: GoalStatistics = field(default_factory=GoalStatistics)
    """Статистика только по выездным матчам команды."""


@dataclass
class MatchStatistics:
    """Полная предматчевая статистика для обеих команд.

    Объединяет предматчевую статистику для домашней и гостевой команды.
    Статистика рассчитывается на основе всех предыдущих матчей команд
    в рамках чемпионата до текущего момента.
    """

    home_prematch: FieldTypeTotals
    """Предматчевая статистика домашней команды."""
    away_prematch: FieldTypeTotals
    """Предматчевая статистика гостевой команды."""


PERCENT_TOTAL = 100
"""Константа, представляющая 100 процентов для расчетов."""


def _update_stats(
    stats: GoalStatistics,
    team_score: int,
    opp_score: int,
) -> None:
    """Обновляет статистику команды и вычисляет средние значения.

    Данная функция обновляет все поля статистики на основе результата одного матча.
    Выполняется пересчет всех средних значений и процентов,
    чтобы отражать актуальное состояние статистики после учета нового матча.

    :param stats: Объект статистики, который необходимо обновить. Функция модифицирует переданный объект.
    :param team_score: Количество голов, забитых анализируемой командой в матче.
    :param opp_score: Количество голов, забитых соперником в матче.

    Notes
    -----
    Функция выполняет следующие действия:
        1. Увеличивает счетчик матчей на единицу.
        2. Добавляет забитые и пропущенные голы к соответствующим суммам.
        3. Определяет исход матча (победа, ничья, поражение) и обновляет соответствующие счетчики.
        4. Пересчитывает все средние значения и проценты.

    Средние значения вычисляются как отношение суммы к количеству:
        - goals_scored_avg = goals_scored / count_matches
        - goals_conceded_avg = goals_conceded / count_matches
        - goals_total_avg = goals_scored_avg + goals_conceded_avg

    Проценты исходов вычисляются как отношение количества матчей с данным исходом
    к общему количеству матчей, умноженное на 100.
    Если матчей не было, все проценты устанавливаются в значение 33.

    """
    stats.count_matches += 1
    stats.goals_scored += team_score
    stats.goals_conceded += opp_score

    # Определение исхода матча и обновление соответствующих счетчиков
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

    # Вычисление средних значений голов
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

    # Расчет средних значений голов по исходам
    stats.goals_scored_win_avg = calc_avg(stats.goals_scored_win, stats.win)
    stats.goals_conceded_win_avg = calc_avg(stats.goals_conceded_win, stats.win)

    stats.goals_scored_draw_avg = calc_avg(stats.goals_scored_draw, stats.draw)
    stats.goals_conceded_draw_avg = calc_avg(stats.goals_conceded_draw, stats.draw)

    stats.goals_scored_defeat_avg = calc_avg(stats.goals_scored_defeat, stats.defeat)
    stats.goals_conceded_defeat_avg = calc_avg(stats.goals_conceded_defeat, stats.defeat)


def _update_team_stat(
    team_stats: FieldTypeTotals,
    match_info: MatchBetexplorer,
    is_home: bool,  # noqa: FBT001
) -> None:
    """Обновляет статистику команды для всех разделов статистики.

    Данная функция обновляет статистику команды сразу в трех разрезах:
    общая статистика (все матчи), домашние матчи и выездные матчи.
    Это позволяет поддерживать актуальную статистику для каждого типа
    выступлений команды.

    :param team_stats: Объект статистики команды, содержащий три раздела: all, home и away.
        Функция модифицирует переданный объект, обновляя соответствующие разделы статистики.
    :param match_info: Словарь с информацией о матче, содержащий данные о счете и командах.
    :param is_home: Флаг, указывающий, является ли анализируемая команда домашней.
        Если True, обновляется раздел home, иначе - раздел away.

    Notes
    -----
    Функция определяет количество забитых и пропущенных голов команды на основе флага is_home
    и счета матча. Затем обновляет общую статистику (раздел all) и статистику для соответствующего
    типа поля (home или away), вызывая функцию _update_stats для каждого раздела.

    """
    team_score: int = match_info['home_score'] if is_home else match_info['away_score']
    opp_score: int = match_info['away_score'] if is_home else match_info['home_score']

    # Обновляем общую статистику и статистику по типу поля
    _update_stats(
        team_stats.all,
        team_score,
        opp_score,
    )
    _update_stats(
        team_stats.home if is_home else team_stats.away,
        team_score,
        opp_score,
    )


def calculate_league_prematch_stats(
    championship_matches: list[MatchBetexplorer],
) -> dict[MatchId, MatchStatistics]:
    """Рассчитывает предматчевую статистику для всех матчей чемпионата.

    Данная функция выполняет последовательный проход по списку матчей
    и для каждого матча вычисляет предматчевую статистику для обеих команд.
    Предматчевая статистика формируется на основе всех предыдущих матчей
    команд в рамках данного чемпионата.

    :param championship_matches: Список матчей чемпионата в хронологическом порядке.
    :return: Словарь, где ключом является идентификатор матча, а значением - объект
        MatchStatistics с предматчевой статистикой для обеих команд.

    Notes
    -----
    Важно, чтобы список матчей был отсортирован в хронологическом порядке,
    так как предматчевая статистика для каждого матча рассчитывается на
    основе только предыдущих матчей. Матчи без счета (home_score или
    away_score равны None) не учитываются при обновлении статистики команд.

    Для сохранения предматчевой статистики используется глубокое копирование
    (deepcopy) объектов FieldTypeTotals, чтобы избежать изменения статистики
    при последующих обновлениях.

    """
    # Инициализация хранилища статистики для команд
    team_stats: dict[int, FieldTypeTotals] = defaultdict(FieldTypeTotals)
    match_statistics: dict[MatchId, MatchStatistics] = {}

    for match_detail in championship_matches:
        home_team_id = match_detail['home_team_id']
        away_team_id = match_detail['away_team_id']

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
