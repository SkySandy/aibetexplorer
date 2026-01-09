"""Расчет рейтингов команд."""

from typing import TypedDict

from app.betexplorer.schemas import MatchBetexplorer
from app.fbcup.statistic import MatchId


class MatchRating(TypedDict):
    """Рейтинги команд на матч."""

    match_id: MatchId
    """Идентификатор матча."""
    home_team_id: int | None
    """"Идентификатор домашней команды."""
    away_team_id: int | None
    """"Идентификатор команды гостей команды."""
    home_team_rating_before: int
    """"Рейтинг домашней команды перед матчем."""
    away_team_rating_before: int
    """"Рейтинг команды гостей перед матчем."""
    home_team_rating_after: int
    """"Рейтинг домашней команды после матча."""
    away_team_rating_after: int
    """"Рейтинг команды гостей после матча."""
    win_prob: int
    """Вероятность победы."""
    draw_prob: int
    """Вероятность ничьи."""
    defeat_prob: int
    """Вероятность поражения."""


def old_rating(match_ratings: list[MatchRating], team_id: int) -> int:
    """Возвращает самый последний рейтинг для команды.

    :param match_ratings: Рейтинги матчей (должны быть отсортированы в хронологическом порядке, от старых к новым)
    :param team_id: Идентификатор команды

    :return: Последний рейтинг команды или 0, если рейтинг не найден
    """
    for match_rating in reversed(match_ratings):
        if match_rating['home_team_id'] == team_id:
            return match_rating['home_team_rating_after']
        if match_rating['away_team_id'] == team_id:
            return match_rating['away_team_rating_after']
    return 0


RATING_TO_PROBABILITY_SCALE: int = 20
"""Преобразует разницу рейтинга в процентные пункты"""
MAX_ADJUSTED_RATING_DIFFERENCE: int = 45
""""Максимально допустимая разница после корректировки рейтинга"""


def calc_win_prob(home_team_rating_before: int, away_team_rating_before: int) -> tuple[int, int]:
    """Вычисляет ожидаемые вероятности победы домашней команды и команды гостей.

    :param home_team_rating_before: Рейтинг домашней команды перед матчем.
    :param away_team_rating_before: Рейтинг команды гостей перед матчем.
    """
    rating_difference: int = round((home_team_rating_before - away_team_rating_before) / RATING_TO_PROBABILITY_SCALE)
    if rating_difference > MAX_ADJUSTED_RATING_DIFFERENCE:
        rating_difference = MAX_ADJUSTED_RATING_DIFFERENCE
    elif rating_difference < -MAX_ADJUSTED_RATING_DIFFERENCE:
        rating_difference = -MAX_ADJUSTED_RATING_DIFFERENCE

    home_team_win: int = 50 + rating_difference
    away_team_win: int = 50 - rating_difference

    return home_team_win, away_team_win


def calc_match_probs(home_team_rating_before: int, away_team_rating_before: int) -> tuple[int, int, int]:
    """Рассчитывает вероятности победы, ничьи и поражения для домашней команды на основе рейтингов.

    :param home_team_rating_before: Рейтинг домашней команды перед матчем.
    :param away_team_rating_before: Рейтинг команды гостей перед матчем.
    :return: Кортеж (win_prob, draw_prob, defeat_prob) в процентах (сумма = 100)
    """
    # Используем существующую функцию для расчета вероятностей победы
    home_win_prob, away_win_prob = calc_win_prob(home_team_rating_before, away_team_rating_before)

    # Базовая вероятность ничьи (можно скорректировать по желанию)
    # Чем ближе рейтинги, тем выше вероятность ничьи
    rating_diff = abs(home_team_rating_before - away_team_rating_before)
    # Максимальная вероятность ничьи при равных рейтингах, минимальная при большой разнице
    max_draw = 30
    min_draw = 15
    # Линейная интерполяция вероятности ничьи
    draw_prob = max_draw - int((max_draw - min_draw) * min(rating_diff, 100) / 100)

    # Корректируем вероятности победы, чтобы сумма была 100
    win_prob = max(0, home_win_prob - draw_prob // 2)
    defeat_prob = max(0, away_win_prob - draw_prob // 2)

    # Финальная корректировка, чтобы сумма была ровно 100
    total = win_prob + draw_prob + defeat_prob
    if total < 100:
        draw_prob += 100 - total
    elif total > 100:
        draw_prob -= total - 100

    return win_prob, draw_prob, defeat_prob


def calc_match_probabilities_fbcup(home_team_rating_before: int, away_team_rating_before: int) -> tuple[int, int, int]:
    """Вычисляет вероятности победы домашней команды, ничьи и победы гостей.

    :param home_team_rating_before: Рейтинг домашней команды перед матчем
    :param away_team_rating_before: Рейтинг команды гостей перед матчем
    :return: Кортеж (вероятность победы домашних, вероятность ничьи, вероятность победы гостей)
    """
    # Базовые вероятности победы без учета ничьей
    home_win_base, away_win_base = calc_win_prob(home_team_rating_before, away_team_rating_before)

    # Фиксированная вероятность ничьи и нормализация
    draw_prob = 25
    total_base = home_win_base + away_win_base  # Всегда 100

    home_win_prob = int((home_win_base / total_base) * (100 - draw_prob))
    away_win_prob = int((away_win_base / total_base) * (100 - draw_prob))

    # Добавляем 5 процентов за домашние игры
    home_win_prob = home_win_prob + 5
    away_win_prob = away_win_prob - 5

    # Корректировка округления
    total = home_win_prob + draw_prob + away_win_prob
    if total != 100:
        diff = 100 - total
        if home_win_prob >= away_win_prob:
            home_win_prob += diff
        else:
            away_win_prob += diff

    return home_win_prob, draw_prob, away_win_prob


GOAL_DIFFERENCE_MULTIPLIER: int = 3
HOME_FIELD_PENALTY: int = -5
AWAY_FIELD_BONUS: int = 5
DRAW_PROBABILITY_BASE: int = 50


def new_rating(home_team_rating_before: int, away_team_rating_before: int,
               home_score: int | None, away_score: int | None) -> tuple[int, int]:
    """Рассчитывает новые рейтинги для обеих команд после их матча.

    :param home_team_rating_before: Рейтинг домашней команды перед матчем.
    :param away_team_rating_before: Рейтинг команды гостей перед матчем.
    :param home_score: Количество голов, забитых домашней командой.
    :param away_score: Количество голов, забитых командой гостей.

    Корректировки рейтинга:
    - Корректировка на основе вероятности победы: учитывает ожидаемый результат матча согласно разнице рейтингов команд
    - Множитель разницы голов (3 * (home_score - away_score)): усиливает влияние разницы забитых и пропущенных мячей на итоговый рейтинг
    - Домашний штраф (-5): уменьшает рейтинг домашней команды после матча для учета преимущества своего поля
    - Гостевой бонус (+5): увеличивает рейтинг гостевой команды после матча для учета сложности игры на выезде
    """
    if home_score is None or away_score is None:
        return home_team_rating_before, away_team_rating_before

    # Рассчитать вероятность победы для обеих команд на основе их рейтингов перед матчем
    home_win_prob, away_win_prob = calc_win_prob(home_team_rating_before, away_team_rating_before)

    # Корректировка рейтинга на основе результата матча
    if home_score > away_score:  # Победа домашней команды
        home_team_rating_adjustment = away_win_prob
        away_team_rating_adjustment = -away_win_prob
    elif home_score == away_score:  # Ничья
        home_team_rating_adjustment = away_win_prob - DRAW_PROBABILITY_BASE
        away_team_rating_adjustment = home_win_prob - DRAW_PROBABILITY_BASE
    else:  # Победа гостевой команды
        home_team_rating_adjustment = -home_win_prob
        away_team_rating_adjustment = home_win_prob

    # Вычислить бонус за разницу забитых и пропущенных мячей
    goal_difference_adjustment: int = GOAL_DIFFERENCE_MULTIPLIER * (home_score - away_score)

    # Рассчитать рейтинг на основе результата матча, домашнего штрафа, гостевого бонуса и разницы количества голов
    home_team_rating_after = home_team_rating_before + home_team_rating_adjustment + HOME_FIELD_PENALTY + goal_difference_adjustment
    away_team_rating_after = away_team_rating_before + away_team_rating_adjustment + AWAY_FIELD_BONUS - goal_difference_adjustment

    return home_team_rating_after, away_team_rating_after


def calc_rating(match_ratings: list[MatchRating], detail: MatchBetexplorer) -> MatchRating:
    """Рассчитывает рейтинги команд для матча и добавляет их в список рейтингов.

    :param match_ratings: Список рейтингов матчей (должны быть отсортированы в хронологическом порядке)
    :param detail: Информация о матче
    """
    if detail['match_id'] == 1627190:
        pass
    home_team_rating_before: int = old_rating(match_ratings, detail['home_team']['team_id'])
    away_team_rating_before: int = old_rating(match_ratings, detail['away_team']['team_id'])
    home_team_rating_after, away_team_rating_after = new_rating(
        home_team_rating_before,
        away_team_rating_before,
        detail['home_score'],
        detail['away_score'],
    )
    win_prob, draw_prob, defeat_prob = calc_match_probabilities_fbcup(home_team_rating_before, away_team_rating_before)

    match_rating: MatchRating = {
        'match_id': detail['match_id'],
        'home_team_id': detail['home_team']['team_id'],
        'away_team_id': detail['away_team']['team_id'],
        'home_team_rating_before': home_team_rating_before,
        'away_team_rating_before': away_team_rating_before,
        'home_team_rating_after': home_team_rating_after,
        'away_team_rating_after': away_team_rating_after,
        'win_prob': win_prob,
        'draw_prob': draw_prob,
        'defeat_prob': defeat_prob,
    }
    match_ratings.append(match_rating)
    return match_rating
