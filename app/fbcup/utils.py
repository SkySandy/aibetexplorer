"""Вспомогательные функции для математических операций и расчетов в системе ставок.

Модуль предоставляет набор утилит для выполнения вычислений, связанных с
анализом спортивных ставок: округление чисел, расчет средних значений,
процентных соотношений, вероятностей на основе коэффициентов букмекеров
и маржи. Все функции обеспечивают точность вычислений и корректное
округление результатов.
"""

from decimal import ROUND_HALF_DOWN, ROUND_HALF_UP, Decimal

# Точность округления до двух знаков после запятой
PRECISION = Decimal('.01')
# Константа для процентных вычислений
HUNDRED = Decimal(100)
# Константа для единицы в десятичном формате
ONE = Decimal(1)


def calc_avg(sum_value: float, count: int) -> float:
    """Вычисляет среднее значение с округлением до двух знаков после запятой.

    Функция делит сумму значений на количество элементов и округляет результат
    до двух знаков после запятой с использованием банковского округления.

    :param sum_value: Сумма значений для вычисления среднего
    :param count: Количество элементов в выборке
    :return: Среднее значение, округленное до двух знаков после запятой
    """
    if count == 0:
        return 0.0
    return float((Decimal(sum_value) / Decimal(count)).quantize(PRECISION, ROUND_HALF_UP))


def calc_avg_percent(sum_value: float, count: int) -> int:
    """Вычисляет среднее значение в процентах с округлением до целого числа.

    Функция рассчитывает процентное отношение суммы к общему количеству
    и округляет результат до целого числа.

    :param sum_value: Сумма значений для вычисления среднего процента
    :param count: Общее количество элементов в выборке
    :return: Среднее значение в процентах, округленное до целого числа
    """
    if count == 0:
        return 0
    return int((HUNDRED * Decimal(sum_value) / Decimal(count)).quantize(ONE, ROUND_HALF_UP))


def calc_total_percent(under: int, equals: int, over: int) -> dict[str, int]:
    """Рассчитывает процентное распределение категорий «меньше», «равно» и «больше».

    Функция вычисляет процентное соотношение каждой категории относительно
    общего количества случаев.

    :param under: Количество случаев в категории «меньше»
    :param equals: Количество случаев в категории «равно»
    :param over: Количество случаев в категории «больше»
    :return: Словарь с процентными значениями для каждой категории
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
    """Округляет среднее значение до целого числа с использованием банковского округления.

    Функция делит сумму на количество и округляет результат до целого числа
    по правилам математического округления (0.5 округляется вверх).

    :param sum_value: Сумма значений для вычисления среднего
    :param count: Количество элементов в выборке
    :return: Среднее значение, округленное до целого числа
    """
    if count == 0:
        return 0
    return int((Decimal(sum_value) / Decimal(count)).quantize(ONE, ROUND_HALF_UP))


def rounds_goal(sum_value: float, count: int) -> int:
    """Округляет среднее значение до целого числа с округлением 0.5 в меньшую сторону.

    Функция делит сумму на количество и округляет результат до целого числа
    с использованием правила ROUND_HALF_DOWN, при котором 0.5 округляется вниз.

    :param sum_value: Сумма значений для вычисления среднего
    :param count: Количество элементов в выборке
    :return: Среднее значение, округленное до целого числа
    """
    if count == 0:
        return 0
    return int((Decimal(sum_value) / Decimal(count)).quantize(ONE, ROUND_HALF_DOWN))


def odds_to_prob(odds: float) -> float:
    """Вычисляет вероятность события в процентах на основе букмекерского коэффициента.

    Функция преобразует коэффициент букмекера в вероятность без учета маржи.
    Вероятность рассчитывается как обратное значение коэффициента, умноженное на 100.

    :param odds: Букмекерский коэффициент
    :return: Вероятность события в процентах, округленная до двух знаков
    """
    return float((HUNDRED / Decimal(odds)).quantize(PRECISION, ROUND_HALF_UP))


def calc_margin(odds_1: float, odds_2: float, odds_x: float | None = None) -> float:
    """Вычисляет маржу букмекера в процентах на основе коэффициентов.

    Маржа представляет собой разницу между суммой вероятностей всех исходов
    и 100%. Функция поддерживает как двухсторонние ставки, так и трехсторонние
    (с учетом ничьей).

    :param odds_1: Букмекерский коэффициент на первый исход
    :param odds_2: Букмекерский коэффициент на второй исход
    :param odds_x: Букмекерский коэффициент на ничью, если применимо
    :return: Маржа букмекера в процентах, округленная до двух знаков
    """
    if odds_x is None:
        # Двухсторонняя ставка
        return float(((HUNDRED / Decimal(odds_1)) + (HUNDRED / Decimal(odds_2)) - HUNDRED).quantize(PRECISION, ROUND_HALF_UP))  # noqa: E501
    # Трехсторонняя ставка
    return float((HUNDRED / Decimal(odds_1) + HUNDRED / Decimal(odds_2) + HUNDRED / Decimal(odds_x) - HUNDRED).quantize(PRECISION, ROUND_HALF_UP))  # noqa: E501


def calc_prob(odds: float, odds_1: float, odds_2: float | None = None) -> float:
    """Вычисляет истинную вероятность события с учетом маржи букмекера.

    Функция корректирует вероятность события, полученную из коэффициента,
    с учетом маржи букмекера. Для этого используется формула нормализации
    вероятностей: истинная вероятность = вероятность события / сумму вероятностей всех исходов.

    :param odds: Букмекерский коэффициент для расчета вероятности
    :param odds_1: Букмекерский коэффициент первого исхода
    :param odds_2: Букмекерский коэффициент второго исхода, если применимо
    :return: Истинная вероятность в процентах, округленная до двух знаков
    """
    if odds_2 is None:
        # Двухсторонняя ставка: нормализация вероятностей двух исходов
        prob_odds = HUNDRED / Decimal(odds)
        prob_odds_1 = HUNDRED / Decimal(odds_1)
        total_prob = prob_odds + prob_odds_1
        return float((prob_odds / total_prob * HUNDRED).quantize(PRECISION, ROUND_HALF_UP))

    # Трехсторонняя ставка: нормализация вероятностей трех исходов
    prob_odds = HUNDRED / Decimal(odds)
    prob_odds_1 = HUNDRED / Decimal(odds_1)
    prob_odds_2 = HUNDRED / Decimal(odds_2)
    total_prob = prob_odds + prob_odds_1 + prob_odds_2
    return float((prob_odds / total_prob * HUNDRED).quantize(PRECISION, ROUND_HALF_UP))


def calc_double_odds(odds_1: float, odds_2: float) -> float:
    """Вычисляет коэффициент для двойного события (например: 1X).

    Функция рассчитывает коэффициент для ставки, которая выигрывает при
    наступлении любого из двух исходов. Формула основана на сложении
    вероятностей исходов.

    :param odds_1: Букмекерский коэффициент первого исхода
    :param odds_2: Букмекерский коэффициент второго исхода
    :return: Коэффициент для двойного события, округленный до двух знаков
    """
    return float((HUNDRED / (HUNDRED / Decimal(odds_1) + HUNDRED / Decimal(odds_2))).quantize(PRECISION, ROUND_HALF_UP))  # noqa: E501
