"""Букмекерская ставка."""
from dataclasses import dataclass, field
import math
from typing import TypedDict

from app.betexplorer.schemas import MatchBetexplorer
from app.fbcup.forecast import MatchForecast


class HistoryKellyStake(TypedDict):
    """Ставка рассчитана по критерию Келли."""

    initial_kelly: float
    """Вычисленное значение."""
    after_fraction: float
    """Доля от банкролла."""
    after_min_stake: float
    """Минимальная ставка."""
    after_rounding: float
    """После округления."""

@dataclass
class KellyStake:
    """Ставка рассчитана по критерию Келли."""

    stake: float | None = None
    """Абсолютная сумма ставки."""
    fraction: float | None = None
    """Доля от банкролла."""
    is_profitable: bool | None = None
    """Ставка выгодна."""
    expected_value: float | None = None
    """Матожидание."""
    variance: float | None = None
    """Дисперсия."""
    sharpe_ratio: float | None = None
    """Коэффициент Шарпа."""
    kelly_fraction: float | None = None
    """Исходная доля Келли."""
    applied_min_stake: bool | None = None
    """Минимальная ставка не применялась."""
    applied_max_stake: bool | None = None
    """Максимальная ставка не применялась."""
    rounded: bool | None = None
    """Ставка была округлена."""
    adjusted_by_fraction: float | None = None
    """Дробный Келли (50% от исходной)."""
    bankroll: float | None = None
    """Текущий банкролл."""
    odds: float | None = None
    """Коэффициент букмекера."""
    probability: float | None = None
    """Вероятность исхода."""
    is_arbitrage: float | None = None
    """Арбитражная ставка."""
    msg_error: list[str] | None = field(default_factory=list)
    """Сообщение об ошибке."""

    max_possible_loss:	float | None = None
    """Максимальный убыток"""
    potential_win:	float | None = None
    """Потенциальный выигрыш"""
    bankroll_after_win:	float | None = None
    """Банкролл после выигрыша"""
    bankroll_after_loss:	float | None = None
    """Банкролл после проигрыша"""

    volatility: float | None = None
    """Волатильность ставки (стандартное отклонение)."""
    risk_of_ruin: float | None = None
    """Вероятность потери всего банка (упрощенная модель)."""

    history: HistoryKellyStake | None = None
    """История изменений"""


@dataclass
class BookmakerBet(TypedDict):
    """Информация о ставке на матч."""

    win_bet: KellyStake | None
    """Ставка на победу."""
    draw_bet: KellyStake | None
    """Ставка на ничью."""
    defeat_bet: KellyStake | None
    """Ставка на поражение."""

@dataclass
class MatchBet:
    """Ставки на матч на основе разных алгоритмов."""

    match_id: int
    """Идентификатор матча."""
    forecast: BookmakerBet | None
    """"Прогноз."""
    forecast_rating: BookmakerBet | None
    """"Прогноз (рейтинг)."""
    forecast_all: BookmakerBet | None
    """"Прогноз (все игры)."""
    forecast_all_rating: BookmakerBet | None
    """"Прогноз (все игры + рейтинг)."""
    forecast_average: BookmakerBet | None
    """"Прогноз (среднее)."""


@dataclass
class KellyParams:
    """Информация о ставке на матч."""

    min_stake: float | None = None
    """Минимальная допустимая ставка (если None — нет ограничения)"""
    max_stake: float | None = None
    """Максимальная допустимая ставка (если None — нет ограничения)"""
    allow_zero: bool = False
    """Если True, допускается возврат нулевой ставки. Если False, при отрицательной/нулевой ставке:
                          - если задан min_stake, возвращается min_stake;
                          - иначе выбрасывается ValueError."""
    check_arbitrage: bool = False
    """Разрешить арбитражные ставки (probability * odds > 1)? Если False, вызовет ошибку."""
    eps: float = 1e-6
    """Погрешность для проверки на арбитраж (по умолчанию 1e-6)"""
    round_step: float | None = None
    """Округление ставки"""
    rounding_method: str = 'nearest'
    """Метод округления"""
    risk_factor: float = 1.0
    """Доля от рекомендуемой ставки Келли (для снижения рисков) (0 < risk_factor <= 1)."""
    commission: float = 0.0
    """Учитывает комиссию букмекера или налоги"""
    max_bankroll_fraction: float | None = None
    """Для ограничения максимальной ставки (в процентах от банкролла)"""
    max_probability: float = 0.99
    """Автоматическое ограничение вероятности (чтобы избежать неадекватных ставок из-за ошибок в оценке)"""


def calc_kelly_stake(
    probability: float,
    odds: float,
    bankroll: float,
    kp: KellyParams,
) -> KellyStake:
    """Расчет ставки по критерию Келли.

    :param probability: Вероятность выигрыша события (от 0 до 1)
    :param odds: Десятичный коэффициент букмекера (например, 2.0)
    :param bankroll: Текущий банкролл игрока. Если указан, функция возвращает абсолютную сумму ставки.
    :param kp: Параметры расчета по критерию Келли.
    """
    ret: KellyStake = KellyStake()

    # Проверка корректности входных данных
    if not (0 < probability < 1):
        ret.msg_error.append('Вероятность должна быть в диапазоне (0, 1).')
    if odds is None:
        ret.msg_error.append('Коэффициент должен быть не пустой.')
        return ret
    elif odds <= 1.0:
        ret.msg_error.append('Коэффициент должен быть больше 1.')
    if bankroll <= 0:
        ret.msg_error.append('Банкролл должен быть положительным.')
    if not (0 < kp.risk_factor <= 1.0):
        ret.msg_error.append('Доля ставки должна быть в диапазоне (0, 1].')
    if kp.min_stake is not None and kp.max_stake is not None and kp.min_stake > kp.max_stake:
        ret.msg_error.append('Минимальная ставка не может превышать максимальную.')

    if kp.min_stake is not None:
        if bankroll is None:
            if not (0 < kp.min_stake <= 1):
                ret.msg_error.append('min_stake должен быть в диапазоне (0, 1], если bankroll не указан.')
        else:
            if kp.min_stake <= 0:
                ret.msg_error.append('min_stake должен быть положительным числом.')

    if kp.max_stake is not None:
        if bankroll is None:
            if not (0 < kp.max_stake <= 1):
                ret.msg_error.append('max_stake должен быть в диапазоне (0, 1], если bankroll не указан.')
        else:
            if kp.max_stake <= 0:
                ret.msg_error.append('max_stake должен быть положительным числом.')

    if not (0 <= kp.commission < 1):
        ret.msg_error.append('Комиссия должна быть в диапазоне от 0 до 1.')

    # Автоматическое ограничение вероятности (например, max_probability=0.99), чтобы избежать неадекватных ставок из-за ошибок в оценке.
    probability = min(probability, kp.max_probability)

    # Проверка на арбитраж
    expected_value = probability * odds - 1 + kp.eps
    if kp.check_arbitrage and expected_value <= 0:
        if kp.allow_zero:
            return 0.0
        elif kp.min_stake is not None:
            return kp.min_stake if bankroll is None else kp.min_stake
        else:
            ret.msg_error.append('Ставка не является арбитражной. Математическое ожидание не положительное.')

    # Формула Келли
    b = (odds - 1) * (1 - kp.commission)
    q = 1 - probability
    kelly_fraction = (b * probability - q) / b

    if kelly_fraction <= 0:
        if not kp.allow_zero:
            if kp.min_stake is not None:
                return kp.min_stake if bankroll is None else kp.min_stake
            else:
                ret.msg_error.append('Ставка невыгодна и min_stake не задан. Нулевая ставка запрещена.')
        else:
            return 0.0

    # Рассчитываем ставку
    stake: float = kelly_fraction * bankroll * kp.risk_factor

    # Ограничение на отрицательные ставки
    stake = max(0.00, stake)

    # Запрет нулевых ставок (если allow_zero=False)
    if not kp.allow_zero and stake == 0:
        if kp.min_stake is not None:
            stake = kp.min_stake  # Возвращаем минимальную ставку вместо 0
        else:
            ret.msg_error.append('Расчётная ставка равна нулю, но allow_zero=False и min_bet не задан.')

    # Применяем ограничения
    if kp.min_stake is not None:
        stake = max(stake, kp.min_stake)

    # Проверка на перегрузку банкролла
    if kp.max_bankroll_fraction is not None:
        max_stake = bankroll * kp.max_bankroll_fraction
        stake = min(stake, max_stake)

    if kp.max_stake is not None:
        stake = min(stake, kp.max_stake)

    if kp.round_step is not None and kp.round_step > 0:
        if kp.rounding_method == 'up':
            stake = math.ceil(stake / kp.round_step) * kp.round_step
        elif kp.rounding_method == 'down':
            stake = math.floor(stake / kp.round_step) * kp.round_step
        else:  # nearest
            stake = round(stake / kp.round_step) * kp.round_step


    ret.stake = stake
    ret.potential_win = odds * stake
    return ret


def calc_bet(
    detail: MatchBetexplorer,
    match_chance: MatchForecast,
) -> BookmakerBet:
    """Вычисление возможной ставки.

    :param detail: Информация о матче
    :param match_chance: Шансы команд
    """
    bb = BookmakerBet(
        win_bet=None,
        draw_bet=None,
        defeat_bet=None,
    )
    kp = KellyParams()
    bankroll: float = 1000

    bb['win_bet'] = calc_kelly_stake(
        probability=match_chance['forecast']['win_prob']/100,
        odds=detail['odds_1'],
        bankroll=bankroll,
        kp=kp,
    )
    bb['draw_bet'] = calc_kelly_stake(
        probability=match_chance['forecast']['draw_prob']/100,
        odds=detail['odds_x'],
        bankroll=bankroll,
        kp=kp,
    )
    bb['defeat_bet'] = calc_kelly_stake(
        probability=match_chance['forecast']['defeat_prob']/100,
        odds=detail['odds_2'],
        bankroll=bankroll,
        kp=kp,
    )
    return bb

def create_bet(
    match_bets: list[MatchBet],
    detail: MatchBetexplorer,
    match_chance: MatchForecast,
) -> MatchBet:
    """Рассчитывает ставку на матч и добавляет в список всех ставок на все матчи.

    Мутирует входной список `match_bets`, добавляя в него новый элемент.

    :param match_bets: Информация о ставках
    :param detail: Информация о матче
    :param match_chance: Шансы команд
    """
    if detail['match_id'] == 1627190:
        pass
    forecast: BookmakerBet = calc_bet(detail, match_chance)

    m_f: MatchBet = MatchBet(
        match_id = detail['match_id'],
        forecast = forecast,
        forecast_rating = None,
        forecast_all = None,
        forecast_all_rating = None,
        forecast_average = None,
    )
    match_bets.append(m_f)
    return m_f
