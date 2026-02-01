# ruff: noqa: I001
"""Описания таблиц системы."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKeyConstraint,
    Identity,
    Index,
    Integer,
    PrimaryKeyConstraint,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    import datetime

PrimaryKeyConstraint.argument_for('postgresql', 'fillfactor', None)


class Sport(Base):
    """Виды спорта."""

    __tablename__ = 'sport'
    # __table_args__ = {'schema': 'betexplorer'}  # noqa: ERA001
    __table_args__ = (
        PrimaryKeyConstraint('sport_id', name='sport_pkey'),
        Index('sport_name', 'sport_name', unique=True),
        Index('sport_url', 'sport_url', unique=True),
        {'comment': 'Виды спорта'},
    )

    sport_id: Mapped[int] = mapped_column(Integer, primary_key=True,
                                          comment='Идентификатор вида спорта')
    sport_name: Mapped[str] = mapped_column(String(255), nullable=False, comment='Название вида спорта')
    sport_url: Mapped[str] = mapped_column(String(255), nullable=False, comment='Ссылка на страницу вида спорта')

    country_sport: Mapped[list[CountrySport]] = relationship('CountrySport', uselist=True, back_populates='sport')
    championship: Mapped[list[Championship]] = relationship('Championship', uselist=True, back_populates='sport')
    team: Mapped[list[Team]] = relationship('Team', uselist=True, back_populates='sport')


class Country(Base):
    """Страны."""

    __tablename__ = 'country'
    # __table_args__ = {'schema': 'betexplorer'}  # noqa: ERA001
    __table_args__ = (
        PrimaryKeyConstraint('country_id', name='country_pkey'),
        Index('country_name', 'country_name', unique=True),
        {'comment': 'Страны'},
    )

    country_id: Mapped[int] = mapped_column(Integer, Identity(start=1), primary_key=True,
                                            autoincrement=True, comment='Идентификатор страны')
    country_name: Mapped[str] = mapped_column(String(255), nullable=False, comment='Название страны')
    country_flag_url: Mapped[str] = mapped_column(String(255), nullable=False, comment='Ссылка на флаг страны')

    country_sport: Mapped[list[CountrySport]] = relationship('CountrySport', uselist=True, back_populates='country')
    championship: Mapped[list[Championship]] = relationship('Championship', uselist=True, back_populates='country')
    team: Mapped[list[Team]] = relationship('Team', uselist=True, back_populates='country')


class CountrySport(Base):
    """Виды спорта по странам."""

    __tablename__ = 'country_sport'
    # __table_args__ = {'schema': 'betexplorer'}  # noqa: ERA001
    __table_args__ = (
        ForeignKeyConstraint(['country_id'], ['country.country_id'], name='fk_country_sport_country_id'),
        ForeignKeyConstraint(['sport_id'], ['sport.sport_id'], name='fk_country_sport_sport_id'),
        PrimaryKeyConstraint('sport_id', 'country_id', name='country_sport_pkey'),
        {'comment': 'Виды спорта по стране'},
    )

    sport_id: Mapped[int] = mapped_column(Integer, primary_key=True,
                                          comment='Идентификатор вида спорта')
    country_id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Идентификатор страны')
    country_url: Mapped[str] = mapped_column(String(255), nullable=False,
                                             comment='Ссылка на страницу всех чемпионатов для страны по виду спорта')
    country_order: Mapped[int] = mapped_column(Integer, nullable=False, comment='Номер по порядку вывода страны')

    country: Mapped[Country] = relationship('Country', back_populates='country_sport')
    sport: Mapped[Sport] = relationship('Sport', back_populates='country_sport')


class Championship(Base):
    """Чемпионаты."""

    __tablename__ = 'championship'
    # __table_args__ = {'schema': 'betexplorer'}  # noqa: ERA001
    __table_args__ = (
        ForeignKeyConstraint(['country_id'], ['country.country_id'], name='fk_championship_country'),
        ForeignKeyConstraint(['sport_id'], ['sport.sport_id'], name='fk_championship_sport_id'),
        PrimaryKeyConstraint('championship_id', name='championship_id_pkey'),
        Index('championship_sport_country_name_years_url', 'sport_id', 'country_id',
              'championship_name', 'championship_years', 'championship_url'),
        {'comment': 'Чемпионаты'},
    )

    championship_id: Mapped[int] = mapped_column(Integer, Identity(start=1), primary_key=True,
                                                  autoincrement=True, comment='Идентификатор чемпионата')
    sport_id: Mapped[int] = mapped_column(Integer, nullable=False, comment='Идентификатор вида спорта')
    country_id: Mapped[int] = mapped_column(Integer, nullable=False, comment='Идентификатор страны')
    championship_name: Mapped[str] = mapped_column(String(255), nullable=False,
                                                     comment='Название чемпионата')
    championship_url: Mapped[str] = mapped_column(String(255), nullable=False,
                                                    comment='Ссылка на страницу чемпионата для вида спорта')
    championship_order: Mapped[int] = mapped_column(Integer, nullable=False,
                                                      comment='Номер по порядку вывода чемпионата')
    championship_years: Mapped[str] = mapped_column(String(255), nullable=False, comment='Годы проведения')

    country: Mapped[Country] = relationship('Country', back_populates='championship')
    match: Mapped[list[Match]] = relationship('Match', uselist=True, back_populates='championship')
    championship_stage: Mapped[list[ChampionshipStage]] = relationship('ChampionshipStage', uselist=True,
                                                                         back_populates='championship')
    sport: Mapped[Sport] = relationship('Sport', back_populates='championship')


class Team(Base):
    """Команды."""

    __tablename__ = 'team'
    # __table_args__ = {'schema': 'betexplorer'}  # noqa: ERA001
    __table_args__ = (
        ForeignKeyConstraint(['country_id'], ['country.country_id'], name='fk_team_country'),
        ForeignKeyConstraint(['sport_id'], ['sport.sport_id'], name='fk_team_sport_id'),
        PrimaryKeyConstraint('team_id', name='team_id_pkey', postgresql_fillfactor=50),
        Index('team_url', 'team_url', unique=True),
        {'comment': 'Команды'},
    )

    team_id: Mapped[int] = mapped_column(Integer, Identity(start=1), primary_key=True,
                                          autoincrement=True, comment='Идентификатор команды')
    sport_id: Mapped[int] = mapped_column(Integer, nullable=False, comment='Идентификатор вида спорта')
    country_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment='Идентификатор страны')
    team_name: Mapped[str] = mapped_column(String(255), nullable=False, comment='Название команды')
    team_full: Mapped[str | None] = mapped_column(String(255), nullable=True, comment='Название команды (полное)')
    team_url: Mapped[str | None] = mapped_column(String(255), nullable=True,
                                                 comment='Ссылка на страницу команды')
    team_emblem: Mapped[str | None] = mapped_column(String(255), nullable=True,
                                                    comment='Ссылка на эмблему команды')
    download_date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, comment='Дата загрузки информации')  # noqa: E501
    save_date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, comment='Дата сохранения информации в базе данных')  # noqa: E501

    country: Mapped[Country | None] = relationship('Country', back_populates='team')
    sport: Mapped[Sport] = relationship('Sport', back_populates='team')
    match: Mapped[list[Match]] = relationship('Match', uselist=True, foreign_keys='[Match.away_team_id]',
                                                back_populates='away_team')
    match_: Mapped[list[Match]] = relationship('Match', uselist=True, foreign_keys='[Match.home_team_id]',
                                                 back_populates='home_team')


class Match(Base):
    """Матчи."""

    __tablename__ = 'match'
    # __table_args__ = {'schema': 'betexplorer'}  # noqa: ERA001
    __table_args__ = (
        ForeignKeyConstraint(['away_team_id'], ['team.team_id'], name='fk_match_away_team'),
        ForeignKeyConstraint(['championship_id'], ['championship.championship_id'], name='fk_match_championship'),
        ForeignKeyConstraint(['home_team_id'], ['team.team_id'], name='fk_match_home_team'),
        PrimaryKeyConstraint('match_id', name='match_pkey', postgresql_fillfactor=50),
        Index('match_championship_id', 'championship_id', unique=False),
        {'comment': 'Матчи'},
    )

    match_id: Mapped[int] = mapped_column(Integer, Identity(start=1), primary_key=True,
                                           autoincrement=True, comment='Идентификатор матча')
    championship_id: Mapped[int] = mapped_column(Integer, nullable=False, comment='Идентификатор чемпионата')
    match_url: Mapped[str] = mapped_column(String(255), nullable=False, comment='Ссылка на матч')

    home_team_id: Mapped[int] = mapped_column(Integer, nullable=False,
                                               comment='Идентификатор домашней команды')
    home_team_emblem: Mapped[str | None] = mapped_column(String(255), nullable=True,
                                                          comment='Ссылка на эмблему команды')
    away_team_id: Mapped[int] = mapped_column(Integer, nullable=False,
                                               comment='Идентификатор команды гостей')
    away_team_emblem: Mapped[str | None] = mapped_column(String(255), nullable=True,
                                                          comment='Ссылка на эмблему команды')
    home_score: Mapped[int | None] = mapped_column(Integer, nullable=True,
                                                    comment='Количество голов забитых домашней командой')
    away_score: Mapped[int | None] = mapped_column(Integer, nullable=True,
                                                    comment='Количество голов забитых командой гостей')

    odds_1: Mapped[float | None] = mapped_column(Float, nullable=True, comment='Коэффициент на победу хозяев')
    odds_x: Mapped[float | None] = mapped_column(Float, nullable=True, comment='Коэффициент на ничью')
    odds_2: Mapped[float | None] = mapped_column(Float, nullable=True, comment='Коэффициент на победу гостей')

    game_date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, comment='Дата игры')
    score_stage: Mapped[str | None] = mapped_column(String(255), nullable=True,
                                                     comment='Примечания к результату матча (победа по пенальти, игра прервалась и прочие)')  # noqa: E501
    score_stage_short: Mapped[str | None] = mapped_column(String(255), nullable=True,
                                                          comment='Примечание к результату в кратком виде')

    is_fixture: Mapped[int] = mapped_column(Integer, nullable=False,
                                              comment='Строка это результат (0) или расписание (1)')
    stage_name: Mapped[str | None] = mapped_column(String(255), nullable=True,
                                                    comment='Стадия чемпионата (квалификация, групповой этап и прочие)')  # noqa: E501
    round_name: Mapped[str | None] = mapped_column(String(255), nullable=True, comment='Название тура')
    round_number: Mapped[int | None] = mapped_column(Integer, nullable=True, comment='Номер тура')

    download_date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, comment='Дата загрузки информации')  # noqa: E501
    save_date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, comment='Дата обновления информации')  # noqa: E501

    championship: Mapped[Championship] = relationship('Championship', back_populates='match')
    home_team: Mapped[Team] = relationship('Team', foreign_keys=[home_team_id], back_populates='match_')
    away_team: Mapped[Team] = relationship('Team', foreign_keys=[away_team_id], back_populates='match')
    time_score: Mapped[list[TimeScore]] = relationship('TimeScore', uselist=True, back_populates='match')
    shooter: Mapped[list[Shooter]] = relationship('Shooter', uselist=True, back_populates='match')
    match_event: Mapped[list[MatchEvent]] = relationship('MatchEvent', uselist=True, back_populates='match')


class TimeScore(Base):
    """Результаты по таймам."""

    __tablename__ = 'time_score'
    # __table_args__ = {'schema': 'betexplorer'}  # noqa: ERA001
    __table_args__ = (
        PrimaryKeyConstraint('time_id', name='time_pkey', postgresql_fillfactor=50),
        ForeignKeyConstraint(['match_id'], ['match.match_id'], name='fk_time_match'),
        Index('time_match_id', 'match_id', unique=False),
        {'comment': 'Результаты по таймам'},
    )

    time_id: Mapped[int] = mapped_column(Integer, Identity(start=1), primary_key=True,
                                          autoincrement=True, comment='Идентификатор тайма')
    match_id: Mapped[int] = mapped_column(Integer, nullable=False, comment='Идентификатор матча')
    half_number: Mapped[int] = mapped_column(Integer, nullable=False, comment='Номер тайма')
    home_score: Mapped[int] = mapped_column(Integer, nullable=False,
                                             comment='Количество голов забитых домашней командой')
    away_score: Mapped[int] = mapped_column(Integer, nullable=False,
                                             comment='Количество голов забитых командой гостей')

    match: Mapped[Match] = relationship('Match', back_populates='time_score')


class Shooter(Base):
    """Информация о голах, заброшенных шайбах."""

    __tablename__ = 'shooter'
    # __table_args__ = {'schema': 'betexplorer'}  # noqa: ERA001
    __table_args__ = (
        PrimaryKeyConstraint('shooter_id', name='shooter_pkey', postgresql_fillfactor=50),
        ForeignKeyConstraint(['match_id'], ['match.match_id'], name='fk_shooter_match'),
        Index('shooter_match_id', 'match_id', unique=False),
        {'comment': 'Голы и минуты'},
    )

    shooter_id: Mapped[int] = mapped_column(Integer, Identity(start=1), primary_key=True,
                                             autoincrement=True, comment='Идентификатор гола')
    match_id: Mapped[int] = mapped_column(Integer, nullable=False, comment='Идентификатор матча')
    home_away: Mapped[int] = mapped_column(Integer, nullable=False,
                                           comment='Событие домашней (0) или гостевой (1) команды')
    event_time: Mapped[str | None] = mapped_column(String(255), nullable=True, comment='Время гола')
    overtime: Mapped[str | None] = mapped_column(String(255), nullable=True, comment='Дополнительное время')
    player_name: Mapped[str | None] = mapped_column(String(255), nullable=True, comment='Фамилия игрока')
    penalty_kick: Mapped[str | None] = mapped_column(String(255), nullable=True, comment='Гол забит с пенальти')
    event_order: Mapped[int | None] = mapped_column(Integer, nullable=True, comment='Порядковый номер события')

    match: Mapped[Match] = relationship('Match', back_populates='shooter')


class ChampionshipStage(Base):
    """Стадии чемпионатов."""

    __tablename__ = 'championship_stage'
    # __table_args__ = {'schema': 'betexplorer'}  # noqa: ERA001
    __table_args__ = (
        PrimaryKeyConstraint('stage_id', name='stage_pkey'),
        ForeignKeyConstraint(['championship_id'], ['championship.championship_id'], name='fk_stage_championship'),
        {'comment': 'Стадии чемпионата'},
    )

    stage_id: Mapped[int] = mapped_column(Integer, Identity(start=1), primary_key=True,
                                           autoincrement=True, comment='Идентификатор стадии чемпионата')
    championship_id: Mapped[int] = mapped_column(Integer, nullable=False, comment='Идентификатор чемпионата')
    stage_url: Mapped[str] = mapped_column(String(255), nullable=False,
                                             comment='Ссылка на страницу стадии чемпионата')
    stage_name: Mapped[str] = mapped_column(String(255), nullable=False,
                                              comment='Название стадии чемпионата')
    stage_order: Mapped[int] = mapped_column(Integer, nullable=False,
                                               comment='Номер по порядку стадии чемпионата')
    stage_current: Mapped[int] = mapped_column(Integer, nullable=False, comment='Текущая стадия')

    championship: Mapped[Championship] = relationship('Championship', back_populates='championship_stage')


class MatchEvent(Base):
    """События в матче."""

    __tablename__ = 'match_event'
    # __table_args__ = {'schema': 'betexplorer'}  # noqa: ERA001
    __table_args__ = (
        PrimaryKeyConstraint('match_event_id', name='match_event_pkey'),
        ForeignKeyConstraint(['match_id'], ['match.match_id'], name='fk_event_match'),
        Index('event_match_id', 'match_id', unique=False),
        {'comment': 'События в матче'},
    )

    match_event_id: Mapped[int] = mapped_column(Integer, Identity(start=1), primary_key=True,
                                                 autoincrement=True, comment='Идентификатор события в матче')
    match_id: Mapped[int] = mapped_column(Integer, nullable=False, comment='Идентификатор матча')
    event_type_id: Mapped[int] = mapped_column(Integer, nullable=False, comment='Идентификатор типа события')
    indicator: Mapped[str | None] = mapped_column(String(255), nullable=True,
                                                   comment='Значение показателя (тотала, форы)')
    odds_less: Mapped[float | None] = mapped_column(Float, nullable=True, comment='Коэффициент на меньше')
    odds_greater: Mapped[float | None] = mapped_column(Float, nullable=True, comment='Коэффициент на больше')

    match: Mapped[Match] = relationship('Match', back_populates='match_event')
