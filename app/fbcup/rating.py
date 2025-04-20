"""Расчет рейтингов команд."""

from typing import Optional, TypedDict

from app.betexplorer.schemas import MatchBetexplorer


class MatchRating(TypedDict):
    """Рейтинги команд на матч."""

    match_id: int
    """Идентификатор матча."""
    home_team_id: Optional[int]
    """"Идентификатор домашней команды."""
    away_team_id: Optional[int]
    """"Идентификатор команды гостей команды."""
    home_team_rating_before: int
    """"Рейтинг домашней команды перед матчем."""
    away_team_rating_before: int
    """"Рейтинг команды гостей перед матчем."""
    home_team_rating_after: int
    """"Рейтинг домашней команды после матча."""
    away_team_rating_after: int
    """"Рейтинг команды гостей после матча."""


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


GOAL_DIFFERENCE_MULTIPLIER: int = 3
HOME_FIELD_PENALTY: int = -5
AWAY_FIELD_BONUS: int = 5
DRAW_PROBABILITY_BASE: int = 50


def new_rating(home_team_rating_before: int, away_team_rating_before: int,
               home_score: Optional[int], away_score: Optional[int]) -> tuple[int, int]:
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
    home_team_rating_before: int = old_rating(match_ratings, detail['home_team']['team_id'])
    away_team_rating_before: int = old_rating(match_ratings, detail['away_team']['team_id'])
    home_team_rating_after, away_team_rating_after = new_rating(
        home_team_rating_before, away_team_rating_before, detail['home_score'], detail['away_score'],
    )
    match_rating: MatchRating = {
        'match_id': detail['match_id'],
        'home_team_id': detail['home_team']['team_id'],
        'away_team_id': detail['away_team']['team_id'],
        'home_team_rating_before': home_team_rating_before,
        'away_team_rating_before': away_team_rating_before,
        'home_team_rating_after': home_team_rating_after,
        'away_team_rating_after': away_team_rating_after,
    }
    match_ratings.append(match_rating)
    return match_rating
