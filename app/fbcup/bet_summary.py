"""Итоги ставок на матчи."""
import copy
from dataclasses import dataclass

from analys_config import AnalysConfig
from app.betexplorer.schemas import MatchBetexplorer
from app.fbcup.bet import KellyStake, MatchBet


@dataclass
class BetSummary:
    """Итоги ставок на матчи."""

    calc_params: AnalysConfig
    """Параметры для расчета ставок."""
    total_bet: float
    """Сумма поставлено всего."""
    total_win: float
    """Сумма выиграно всего."""
    total_roi: float
    """Процент возврата инвестиций."""
    count_stake: int
    """Количество ставок."""


def calc_roi(
    total_bet: float,
    total_win: float,
) -> float:
    """Рассчитывает процент возврата инвестиций (ROI) на основе общего выигрыша и оборота.

    :param total_bet: Суммарный оборот (общая сумма всех сделанных ставок)
    :param total_win: Суммарный выигрыш по всем ставкам (включая возвраты)
    """
    profit = total_win - total_bet
    roi_percentage = (profit / total_bet) * 100 if total_bet != 0 else 0.0

    return round(roi_percentage, 2)

def calc_bet_summary(
        match_details: list[MatchBetexplorer],
        match_bets: list[MatchBet],
        calc_params: AnalysConfig,
) -> BetSummary:
    """Рассчитать итого прогнозирования матчей.

    :param match_details: Список результатов матчей
    :param match_bets: Список ставок на матч
    :param calc_params: Параметры для расчета ставок
    """
    bets_map = {f.match_id: f for f in match_bets}
    total_bet = 0.00
    total_win = 0.00
    count_stake = 0
    for detail in match_details:
        home_score = detail['home_score']
        away_score = detail['away_score']
        round_number = detail['round_number']
        if home_score is None or away_score is None:
            continue
        if round_number <= calc_params.round_number:
            continue

        bet = bets_map[detail['match_id']]
        win_bet: KellyStake = bet.forecast['win_bet']
        draw_bet: KellyStake = bet.forecast['draw_bet']
        defeat_bet: KellyStake = bet.forecast['defeat_bet']

        if win_bet.stake is not None and win_bet.stake != 0.00:
            total_bet += win_bet.stake
            count_stake += 1
            if home_score > away_score:
                total_win += win_bet.potential_win
        if draw_bet.stake is not None and draw_bet.stake != 0.00:
            total_bet += draw_bet.stake
            count_stake += 1
            if home_score == away_score:
                total_win += draw_bet.potential_win
        if defeat_bet.stake is not None and defeat_bet.stake != 0.00:
            total_bet += defeat_bet.stake
            count_stake += 1
            if home_score < away_score:
                total_win += defeat_bet.potential_win
    ret = BetSummary(
        total_bet = total_bet,
        total_win = total_win,
        total_roi = calc_roi(total_bet, total_win),
        count_stake = count_stake,
        calc_params = copy.deepcopy(calc_params),
    )
    return ret
