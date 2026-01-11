"""Вспомогательные функции."""

from decimal import ROUND_HALF_DOWN, ROUND_HALF_UP, Decimal

PRECISION = Decimal('.01')
HUNDRED = Decimal(100)
ONE = Decimal(1)

def calc_avg(sum_value: float, count: int) -> float:
    """Посчитывает среднее с округлением до двух знаков.

    :param sum_value: Итого
    :param count: Количество
    """
    if count == 0:
        return 0.0
    return float((Decimal(sum_value) / Decimal(count)).quantize(PRECISION, ROUND_HALF_UP))


def calc_avg_percent(sum_value: float, count: int) -> int:
    """Вычисляет среднее значение в процентах с округлением до целого числа.

    :param sum_value: Итого
    :param count: Количество
    """
    if count == 0:
        return 0
    return int((HUNDRED * Decimal(sum_value) / Decimal(count)).quantize(ONE, ROUND_HALF_UP))


def calc_total_percent(under: int, equals: int, over: int) -> dict[str, int]:
    """Рассчитывает процентное распределение «меньше», «равно» и «больше» по количеству каждого случая.

    :param under:Количество случаев «меньше».
    :param equals: Количество случаев «равно».
    :param over: Количество случаев «больше».
    """
    count = under + equals + over
    if count == 0:
        return {'under_percent': 0, 'equals_percent': 0, 'over_percent': 0}
    return {
        'under_percent': calc_avg_percent(under, count),
        'equals_percent': calc_avg_percent(equals, count),
        'over_percent': calc_avg_percent(over, count),
    }


def rounds_whole(sum_value: float, count: int) -> int:
    """Округляет до целого числа.

    :param sum_value: Итого
    :param count: Количество
    """
    if count == 0:
        return 0
    return int((Decimal(sum_value) / Decimal(count)).quantize(ONE, ROUND_HALF_UP))


def rounds_goal(sum_value: float, count: int) -> int:
    """Округляет до целого числа с учетом, что 0.5 округляется в меньшую сторону.

    :param sum_value: Итого
    :param count: Количество
    """
    if count == 0:
        return 0
    return int((Decimal(sum_value) / Decimal(count)).quantize(ONE, ROUND_HALF_DOWN))


def odds_to_prob(odds: float) -> float:
    """Вычисляет вероятность события на основе коэффициента, с учетом маржи, с округлением до двух десятичных знаков.

    :param odds: Букмекерский коэффициент ставку
    """
    return float((HUNDRED / Decimal(odds)).quantize(PRECISION, ROUND_HALF_UP))


def calc_margin(odds_1: float, odds_2: float, odds_x: float | None = None) -> float:
    """Вычисляет маржу в процентах на основе коэффициентов с округлением до двух десятичных знаков.

    :param odds_1: Букмекерский коэффициент за победу
    :param odds_2: Букмекерский коэффициент за поражение
    :param odds_x: Букмекерский коэффициент за ничью. Если None, функция рассчитывает маржу только для двух исходов
    :return: Маржа букмекера в процентах

    Если `odds_x` не указан или равен None, функция поддерживает двухсторонние ставки.
    """
    if odds_x is None:
        return float(((HUNDRED / Decimal(odds_1)) + (HUNDRED / Decimal(odds_2)) - HUNDRED).quantize(PRECISION, ROUND_HALF_UP))
    return float((HUNDRED / Decimal(odds_1) + HUNDRED / Decimal(odds_2) + HUNDRED / Decimal(odds_x) - HUNDRED).quantize(PRECISION, ROUND_HALF_UP))


def calc_prob(odds: float, odds_1: float, odds_2: float | None = None) -> float:
    """Вычисляет вероятность события на основе коэффициента, с округлением до двух десятичных знаков.

    :param odds: Букмекерский коэффициент ставку
    :param odds_1: Букмекерский коэффициент 1
    :param odds_2: Букмекерский коэффициент 2. Если None, функция рассчитывает вероятность только для двух исходов
    """
    if odds_2 is None:
        return float((HUNDRED / Decimal(odds) / (ONE + (HUNDRED / Decimal(odds) + HUNDRED / Decimal(odds_1) + HUNDRED - HUNDRED) / HUNDRED)).quantize(PRECISION, ROUND_HALF_UP))
    return float((HUNDRED / Decimal(odds) / (ONE + (HUNDRED / Decimal(odds) + HUNDRED / Decimal(odds_1) + HUNDRED / Decimal(odds_2) - HUNDRED) / HUNDRED)).quantize(PRECISION, ROUND_HALF_UP))


def calc_double_odds(odds_1: float, odds_2: float) -> float:
    """Вычисляет вероятность двойного события на основе коэффициента, с округлением до двух десятичных знаков.

    :param odds_1: Букмекерский коэффициент 1
    :param odds_2: Букмекерский коэффициент 2
    """
    return float((HUNDRED / (HUNDRED / Decimal(odds_1) + HUNDRED / Decimal(odds_2))).quantize(PRECISION, ROUND_HALF_UP))
