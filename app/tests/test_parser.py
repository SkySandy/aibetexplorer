"""Тестирование функции разбора страницы BetExplorer."""
import datetime
from typing import List, Optional

from deepdiff import DeepDiff
import pytest
import pytest_asyncio
from selectolax.lexbor import LexborHTMLParser, LexborNode
from selectolax.parser import HTMLParser, Node

from app.betexplorer.betexplorer import (
    COLUMN_GAME_DATE,
    COLUMN_ODDS_1,
    COLUMN_ODDS_2,
    COLUMN_ODDS_X,
    COLUMN_SCORE,
    COLUMN_TEAMS,
    CSS_COUNTRIES,
    CSS_PAGE_TEAM,
    CSS_RESULTS,
    CSS_SHOOTERS,
    IS_FIXTURE,
    IS_RESULT,
    get_column_type,
    get_results,
    get_results_fixtures,
    get_team,
    match_init,
    parsing_championships,
    parsing_countries,
    parsing_date_fixtures,
    parsing_date_match,
    parsing_date_results,
    parsing_match_time,
    parsing_odds,
    parsing_results,
    parsing_round,
    parsing_score,
    parsing_score_halves,
    parsing_score_stage,
    parsing_shooters,
    parsing_stages,
    parsing_team,
    parsing_team_data,
    parsing_team_match,
    update_match_time,
)
from app.betexplorer.crud import DATABASE_NOT_USE, CRUDbetexplorer
from app.betexplorer.schemas import (
    ChampionshipBetexplorer,
    ChampionshipStageBetexplorer,
    CountryBetexplorer,
    MatchBetexplorer,
    ScoreHalvesBetexplorer,
    ShooterBetexplorer,
    SportType,
    TeamBetexplorer,
)
from app.config import settings
from app.utilbase import LoadSave, ReceivedData

_PARSERS_PARAMETRIZER = ('parser', (HTMLParser, LexborHTMLParser))


class TestParsingCountries:
    """Тест разбора страницы стран."""

    def test_returns_empty_list_when_input_is_none(self):
        """Возвращает пустой список, если передано None."""
        result = parsing_countries(None)
        assert result == []

    @pytest.mark.asyncio()
    @pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
    async def test_parsing_countries(self, parser):
        pars: List[CountryBetexplorer] = [
            {
                'country_id': None,
                'country_url': '/football/england/',
                'country_name': 'England',
                'country_order': 0,
                'country_flag_url': '/res/images/flags/4x3/198.svg',
            },
            {
                'country_id': None,
                'country_url': '/football/spain/',
                'country_name': 'Spain',
                'country_order': 1,
                'country_flag_url': '/res/images/flags/4x3/es.svg',
            },
        ]
        html = """
            <div class="box-aside__section__in">
                <ul class="list-events list-events--secondary js-divlinks" id="countries-select">
                    <li class="list-events__item"><div class="list-events__item__in"><i><img src="/res/images/flags/4x3/198.svg" alt="England"></i>
                        <a class="list-events__item__title" href="/football/england/">England</a></div></li>
                    <li class="list-events__item"><div class="list-events__item__in"><i><img src="/res/images/flags/4x3/es.svg" alt="Spain"></i>
                        <a class="list-events__item__title" href="/football/spain/">Spain</a></div></li>
                </ul>
            </div>
        """
        node = parser(html).css_first(CSS_COUNTRIES)
        soap: ReceivedData = ReceivedData(node, datetime.datetime(2020, 1, 1, 10, 30))
        res = parsing_countries(soap)
        assert not DeepDiff(pars, res)


class TestParsingChampionships:
    """Тест разбора страницы чемпионатов по стране."""

    def test_empty_input(self):
        """Возвращает пустой список, если передано None."""
        country_id = 0
        sport_id = SportType.FOOTBALL.value
        result = parsing_championships(None, sport_id, country_id)
        assert result == []

    @pytest.mark.asyncio()
    @pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
    async def test_parsing_championships(self, parser):
        country_id = 0
        sport_id = SportType.FOOTBALL.value
        pars: List[ChampionshipBetexplorer] = [
            {
                'championship_id': None,
                'sport_id': sport_id,
                'country_id': country_id,
                'championship_url': '/football/england/premier-league/',
                'championship_name': 'Premier League',
                'championship_order': 0,
                'championship_years': '2023/2024',
            },
            {
                'championship_id': None,
                'sport_id': sport_id,
                'country_id': country_id,
                'championship_url': '/football/england/championship/',
                'championship_name': 'Championship',
                'championship_order': 1,
                'championship_years': '2023/2024',
            },
            {
                'championship_id': None,
                'sport_id': sport_id,
                'country_id': country_id,
                'championship_url': '/football/england/fa-community-shield/',
                'championship_name': 'FA Community Shield',
                'championship_order': 0,
                'championship_years': '2023',
            },
        ]
        html = """
            <table class="table-main js-tablebanner-t">
                <tbody>
                    <tr><th class="h-text-left">2023/2024</th></tr>
                    <tr><td><a href="/football/england/premier-league/">Premier League</a></td></tr>
                    <tr><td><a href="/football/england/championship/">Championship</a></td></tr>
                </tbody>
                <tbody>
                    <tr><th class="h-text-left">2023</th></tr>
                    <tr><td><a href="/football/england/fa-community-shield/">FA Community Shield</a></td></tr>
                </tbody>
            </table>
        """
        node = parser(html).css_first('.table-main.js-tablebanner-t,.nodata')
        soap: ReceivedData = ReceivedData(node, datetime.datetime(2020, 1, 1, 10, 30))
        res = parsing_championships(soap, sport_id, country_id)
        assert not DeepDiff(pars, res)


class TestParsingStages:
    """Тест стадий чемпионата."""

    @pytest.mark.asyncio()
    @pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
    async def test_parsing_stages(self, parser):
        pars: List[ChampionshipStageBetexplorer] = [
            {
                'stage_id': None,
                'stage_url': '?stage=Q1agpwdd',
                'stage_name': 'Qualification',
                'stage_order': 0,
                'stage_current': False
            },
            {
                'stage_id': None,
                'stage_url': '?stage=nB0koJtj',
                'stage_name': 'Main',
                'stage_order': 1,
                'stage_current': True
            },
        ]
        html = """
            <div id="home-page-left-column" class=" columns__item columns__item--68 columns__item--tab-100">
                <div class="h-mb15">
                    <div class="box-overflow" id="sm-0-0">
                        <div class="box-overflow__in">
                            <ul class="list-tabs list-tabs--secondary">
                                <li class="list-tabs__item">
                                    <a href="?stage=Q1agpwdd" title="" class="list-tabs__item__in">Qualification</a>
                                </li>
                                <li class="list-tabs__item">
                                    <a href="?stage=nB0koJtj" title="Main season game statistics" class="list-tabs__item__in current">Main</a>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        """
        node = parser(html).css_first(CSS_RESULTS)
        soap: ReceivedData = ReceivedData(node, datetime.datetime(2020, 1, 1, 10, 30))
        res = parsing_stages(soap)
        assert not DeepDiff(pars, res)


class TestParsingTeamData:
    """Разбор названия команды."""

    @pytest.mark.asyncio()
    @pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
    async def test_parsing_team_data(self, parser):
        html = """
            <table>
                <tbody>
                    <tr>
                        <td>
                            <ul>
                                <li class="list-details__item">
                                    <a href="/football/team/nottingham/UsushcZr/">
                                        <figure class="list-details__item__team">
                                            <div>
                                                <img src=" /res/images/team-logo/6uyUuh7n-ImKwLTtA.png" alt="Nottingham Forest Football Club"/>
                                            </div>
                                        </figure>
                                        <h2 class="list-details__item__title teamsLink">Nottingham</h2>
                                        <input type="hidden" value="285" id="homeParticipantIdHeader"/>
                                    </a>
                                </li>
                            </ul>
                        </td>
                        <td>
                            <ul>
                                <li class="list-details__item">
                                    <a href="/football/team/bristol-city/MahqU27I/">
                                        <figure class="list-details__item__team">
                                            <div>
                                                <img src=" /res/images/team-logo/p2UIZ8nh-OdaWmcNh.png" alt=" Bristol City Football Club "/>
                                            </div>
                                        </figure>
                                    <h2 class="list-details__item__title teamsLink">Bristol City</h2>
                                    <input type="hidden" value="248" id="awayParticipantIdHeader"/></a>
                                </li>
                            </ul>
                        </td>
                        <td>
                            <ul class="list-details">
                                <li class="list-details__item">
                                    <figure class="list-details__item__team">
                                        <div>
                                            <a href="/football/team/accrington/6ZvdGuYf/">
                                                <img alt="Accrington Stanley FC" src="/res/images/team-logo/nTg51oUc-QqdgCtqL.png"/>
                                            </a>
                                        </div>
                                    </figure>
                                    <h2 class="list-details__item__title">
                                        <a href="/football/team/accrington/6ZvdGuYf/">
                                            Accrington
                                        </a>
                                    </h2>
                                </li>
                            </ul>
                        </td>
                        <td>
                            <ul class="list-details">
                                <li class="list-details__item">
                                    <figure class="list-details__item__team">
                                        <div>
                                            <a href="/football/team/accrington/6ZvdGuYf/">
                                                <img1 alt="Accrington Stanley FC" src="/res/images/team-logo/nTg51oUc-QqdgCtqL.png"/>
                                            </a>
                                        </div>
                                    </figure>
                                    <h2 class="list-details__item__title">
                                        <a href="/football/team/accrington/6ZvdGuYf/">
                                            Accrington
                                        </a>
                                    </h2>
                                </li>
                            </ul>
                        </td>
                    </tr>
                </tbody>
            </table>
        """
        node = parser(html).css_first('table tbody')
        for season_table in node.iter(False):
            for index, item in enumerate(season_table.iter(False)):
                team_url, team_name, team_emblem, team_full = parsing_team_data(item)
                if index == 0:
                    assert team_url == '/football/team/nottingham/UsushcZr/'
                    assert team_name == 'Nottingham'
                    assert team_emblem == ' /res/images/team-logo/6uyUuh7n-ImKwLTtA.png'
                    assert team_full == 'Nottingham Forest Football Club'
                if index == 1:
                    assert team_url == '/football/team/bristol-city/MahqU27I/'
                    assert team_name == 'Bristol City'
                    assert team_emblem == ' /res/images/team-logo/p2UIZ8nh-OdaWmcNh.png'
                    assert team_full == ' Bristol City Football Club '
                if index == 2:
                    assert team_url == '/football/team/accrington/6ZvdGuYf/'
                    assert team_name == 'Accrington'
                    assert team_emblem == '/res/images/team-logo/nTg51oUc-QqdgCtqL.png'
                    assert team_full == 'Accrington Stanley FC'
                if index == 3:
                    assert team_url == '/football/team/accrington/6ZvdGuYf/'
                    assert team_name == 'Accrington'
                    assert team_emblem is None
                    assert team_full is None


class TestParsingRound:
    """Тест разбора тура чемпионата."""

    @pytest.mark.asyncio()
    @pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
    async def test_parsing_round(self, parser):
        html = """
            <table>
                <tbody>
                    <tr>
                        <th class="h-text-left" colspan="2">25. Round</th>
                        <th class="h-text-left" colspan="2">1/16-finals - 2nd leg</th>
                        <th class="h-text-left" colspan="2">Final</th>
                    </tr>
                </tbody>
            </table>
        """
        node = parser(html).css_first('table tbody')
        for season_table in node.iter(False):
            for index, item in enumerate(season_table.iter(False)):
                round_name, round_number = parsing_round(item)
                if index == 0:
                    assert round_name == '25. Round'
                    assert round_number == 25
                if index == 1:
                    assert round_name == '1/16-finals - 2nd leg'
                    assert round_number is None


class TestParsingTeamMatch:
    """Разбор информации о матче."""

    @pytest.mark.asyncio()
    @pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
    async def test_parsing_team_match(self, parser):
        html = """
            <table>
                <tbody>
                    <tr>
                        <td class="h-text-left"><a href="/football/england/fa-cup/aston-villa-chelsea/bTRJf3RS/" class="in-match"><span>Aston Villa</span> - <span><strong>Chelsea</strong></span></a></td>
                    </tr>
                </tbody>
            </table>
        """
        node = parser(html).css_first('table tbody')
        for season_table in node.iter(False):
            for index, item in enumerate(season_table.iter(False)):
                match_url, home_team_name, away_team_name = parsing_team_match(item)
                if index == 0:
                    assert match_url == '/football/england/fa-cup/aston-villa-chelsea/bTRJf3RS/'
                    assert home_team_name == 'Aston Villa'
                    assert away_team_name == 'Chelsea'


@pytest.mark.asyncio
@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
async def test_parsing_score(parser):
    html = """
        <table>
            <tbody>
                <tr>
                    <a href="/football/england/premier-league/brentford-liverpool/feRqWiiN/">1:4</a>
                    <p class="list-details__item__score" id="js-score">2:1</p>
                </tr>
            </tbody>
        </table>
    """
    node = parser(html).css_first('table tbody')
    for season_table in node.iter(False):
        for index, item in enumerate(season_table.iter(False)):
            home_score, away_score = parsing_score(item)
            if index == 0:
                assert home_score == 1
                assert away_score == 4
            if index == 1:
                assert home_score == 2
                assert away_score == 1


class TestParsingScoreStage:
    """Разбор счета и в какой стадии счет."""

    @pytest.mark.asyncio()
    @pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
    async def test_parsing_score_stage(self, parser):
        html = """
            <table>
                <tbody>
                    <tr>
                        <td class="h-text-center"><a href="/football/england/premier-league/brentford-liverpool/feRqWiiN/">1:4</a></td>
                        <td class="h-text-center"><a href="/football/england/fa-cup/nottingham-bristol-city/pQJU6X3O/">2:1 <span title="After Penalties">PEN.</span></a></td>
                    </tr>
                </tbody>
            </table>
        """
        node = parser(html).css_first('table tbody')
        for season_table in node.iter(False):
            for index, item in enumerate(season_table.iter(False)):
                home_score, away_score, score_stage_short, score_stage = parsing_score_stage(item)
                if index == 0:
                    assert home_score == 1
                    assert away_score == 4
                    assert score_stage_short is None
                    assert score_stage is None
                if index == 1:
                    assert home_score == 2
                    assert away_score == 1
                    assert score_stage_short == 'PEN.'
                    assert score_stage == 'After Penalties'


class TestParsingOdds:
    """Тест разбора коэффициента."""

    @pytest.mark.asyncio()
    @pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
    async def test_parsing_odds(self, parser):
        html = """
            <table>
                <tbody>
                    <tr>
                        <td class="table-main__odds" data-oid="6b3pjxv498x0x0" data-odd="4.07"></td>
                        <td class="table-main__odds colored" data-oid="6e0hoxv464x0xh8p85"><span><span><span data-odd="1.65"></span></span></span></td>
                        <td class="table-main__detail-odds" data-odd=""></td>
                    </tr>
                </tbody>
            </table>
        """
        node = parser(html).css_first('table tbody')
        for season_table in node.iter(False):
            for index, item in enumerate(season_table.iter(False)):
                res = parsing_odds(item)
                if index == 0:
                    assert res == 4.07
                if index == 1:
                    assert res == 1.65
                if index == 2:
                    assert res is None

    @pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
    def test_empty_attributes(self, parser):
        html = "<div><p id=''>text</p></div>"
        selector = "p"
        for node in parser(html).css(selector):
            assert 'id' in node.attributes
            assert node.attributes['id'] == ''


class TestParsingDateResults:
    """Тест разбора даты результата."""

    @pytest.mark.asyncio()
    @pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
    async def test_parsing_date_results(self, parser):
        html = """
            <table>
                <tbody>
                    <tr>
                        <td class="h-text-right h-text-no-wrap">Yesterday</td>
                        <td class="h-text-right h-text-no-wrap">Today</td>
                        <td class="h-text-right h-text-no-wrap">10.02.</td>
                        <td class="h-text-right h-text-no-wrap">31.12.2023</td>
                        <td class="h-text-right h-text-no-wrap">Invalid Date</td>
                    </tr>
                </tbody>
            </table>
        """
        node = parser(html).css_first('table tbody')
        for season_table in node.iter(False):
            for index, item in enumerate(season_table.iter(False)):
                res = parsing_date_results(item, datetime.datetime(2024, 2, 18))
                if index == 0:
                    assert res == datetime.datetime(year=2024, month=2, day=17)
                elif index == 1:
                    assert res == datetime.datetime(year=2024, month=2, day=18)
                elif index == 2:
                    assert res == datetime.datetime(year=2024, month=2, day=10)
                elif index == 3:
                    assert res == datetime.datetime(year=2023, month=12, day=31)
                elif index == 4:
                    assert res is None


class TestParsingTeam:

    @pytest.mark.asyncio()
    @pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
    async def test_parsing_team(self, parser):
        sport_id = SportType.FOOTBALL.value
        team: TeamBetexplorer = {
            'team_id': None,
            'sport_id': sport_id,
            'team_name': None,
            'team_full': 'ADO Den Haag',
            'team_url': None,
            'team_country': 'Netherlands',
            'country_id': None,
            'team_emblem': '/res/images/team-logo/GWBsuej9-vuxu3x67.png',
            'download_date': None,
            'save_date': None,
        }
        html = """
            <table>
                <tbody>
                    <tr>
                        <header class="wrap-section__header">
                        <figure class="wrap-section__header__teamlogo"><img src="/res/images/team-logo/GWBsuej9-vuxu3x67.png" alt="ADO Den Haag">
                        </figure>
                        <h1 class="wrap-section__header__title">ADO Den Haag (Netherlands)</h1>
                        </header>
                    </tr>
                </tbody>
            </table>
        """
        node = parser(html).css_first(CSS_PAGE_TEAM)
        soap: ReceivedData = ReceivedData(node, datetime.datetime(2020, 1, 1, 10, 30))
        res = parsing_team(soap, sport_id)
        assert not DeepDiff(res, team, exclude_paths=["root['download_date']", "root['save_date']"])


class TestParsingDateFixtures:

    @pytest.mark.asyncio()
    @pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
    async def test_parsing_date_fixtures(self, parser):
        html = """
            <table>
                <tbody>
                    <tr>
                        <td class="table-main__datetime">13.03. 20:30</td>
                        <td class="table-main__datetime">Today 15:00</td>
                        <td class="table-main__datetime">13.11.2023 20:30</td>
                        <td class="table-main__datetime">Tomorrow 15:00</td>
                        <td class="table-main__datetime">Yesterday 15:00</td>
                        <td class="table-main__datetime">&nbsp;</td>
                    </tr>
                </tbody>
            </table>
        """
        node = parser(html).css_first('table tbody')
        for season_table in node.iter(False):
            for index, item in enumerate(season_table.iter(False)):
                res = parsing_date_fixtures(item,
                                            datetime.datetime(2024, 2, 18, 16, 10),
                                            datetime.datetime(2024, 2, 20, 19, 20))
                if index == 0:
                    assert res == datetime.datetime(year=2024, month=3, day=13, hour=20, minute=30)
                elif index == 1:
                    assert res == datetime.datetime(year=2024, month=2, day=18, hour=15, minute=00)
                elif index == 2:
                    assert res == datetime.datetime(year=2023, month=11, day=13, hour=20, minute=30)
                elif index == 3:
                    assert res == datetime.datetime(year=2024, month=2, day=19, hour=15, minute=00)
                elif index == 4:
                    assert res == datetime.datetime(year=2024, month=2, day=17, hour=15, minute=00)
                elif index == 5:
                    assert res == datetime.datetime(year=2024, month=2, day=20, hour=19, minute=20)


class TestParsingDateMatch:

    @pytest.mark.asyncio()
    @pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
    async def test_parsing_date_match(self, parser):
        html = """
            <ul class="list-details borderTop0">
                <li class="list-details__item">
                    <p class="list-details__item__date headerTournamentDate" id="match-date" data-dt="26,2,2024,20,45"></p>
                </li>
            </ul>
        """
        node = parser(html).css_first('ul.list-details')
        for season_table in node.iter(False):
            for index, item in enumerate(season_table.iter(False)):
                res = parsing_date_match(item)
                if index == 0:
                    assert res == datetime.datetime(year=2024, month=2, day=26, hour=20, minute=45)


class TestParsingScoreHalves:
    """Тест парсинга колонки счет по таймам."""

    @pytest.mark.asyncio()
    @pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
    async def test_parsing_score_halves(self, parser):
        pars: List[ScoreHalvesBetexplorer] = [
            {
                'time_id': None,
                'half_number': 0,
                'home_score': 1,
                'away_score': 1,
            },
            {
                'time_id': None,
                'half_number': 1,
                'home_score': 0,
                'away_score': 0,
            },
            {
                'time_id': None,
                'half_number': 2,
                'home_score': 0,
                'away_score': 0,
            },
            {
                'time_id': None,
                'half_number': 3,
                'home_score': 5,
                'away_score': 3,
            },
        ]
        html = """
            <ul class="list-details borderTop0">
                <li class="list-details__item">
                    <h2 class="list-details__item__partial" id="js-partial">(1:1, 0:0, 0:0, 5:3)</h2>
                </li>
            </ul>
        """
        # html = '<h2 class="list-details__item__partial" id="js-partial">(1:1, 0:0, 0:0, 5:3)</h2>'
        # selector = "h2.list-details__item__partial"
        # find_first = parser(html).css_first(selector)
        # assert find_first.css_first(selector) is not None

        node = parser(html).css_first('ul.list-details')
        for season_table in node.iter(False):
            for index, item in enumerate(season_table.iter(False)):
                res = parsing_score_halves(item)
                if index == 0:
                    assert not DeepDiff(pars, res)


class TestParsingShooters:
    """Разбор кто забивал голы."""

    @pytest.mark.asyncio()
    @pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
    async def test_parsing_shooters(self, parser):
        pars: List[ShooterBetexplorer] = [
            {
                'shooter_id': None,
                'home_away': 0,
                'event_order': 0,
                'event_time': '22',
                'overtime': None,
                'player_name': 'Tuncer Ali Han',
                'penalty_kick': None,
            },
            {
                'shooter_id': None,
                'home_away': 0,
                'event_order': 1,
                'event_time': '78',
                'overtime': None,
                'player_name': 'Ntcham Olivier',
                'penalty_kick': '(penalty kick)',
            },
        ]
        pars2: List[ShooterBetexplorer] = [
            {
                'event_order': 0,
                'home_away': 1,
                'event_time': '76',
                'overtime': None,
                'penalty_kick': None,
                'player_name': 'Basev Selim',
                'shooter_id': None,
            },
            {
                'event_order': 1,
                'home_away': 1,
                'event_time': '90',
                'overtime': '7',
                'penalty_kick': None,
                'player_name': 'Sari Yusuf',
                'shooter_id': None,
            },
        ]
        pars_21: List[ShooterBetexplorer] = [
            {
                'shooter_id': None,
                'home_away': 0,
                'event_order': 0,
                'event_time': '00:31',
                'overtime': None,
                'player_name': 'Kawashima Makoto',
                'penalty_kick': None,
            },
            {
                'shooter_id': None,
                'home_away': 0,
                'event_order': 1,
                'event_time': '02:50',
                'overtime': None,
                'player_name': 'Saito Takeshi',
                'penalty_kick': None,
            },
        ]
        pars_22: List[ShooterBetexplorer] = [
            {
                'shooter_id': None,
                'home_away': 1,
                'event_order': 0,
                'event_time': '48:34',
                'overtime': None,
                'player_name': 'Zhang Hao',
                'penalty_kick': None,
            },
            {
                'shooter_id': None,
                'home_away': 1,
                'event_order': 1,
                'event_time': '55:06',
                'overtime': None,
                'player_name': 'Kondo Katsumasa',
                'penalty_kick': None,
            },
        ]

        html = """
            <ul class="list-details list-details--shooters">
                <li class="list-details__item">
                    <table class="table-main">
                        <tr><td></td><td style="width: 4ex; text-align: right;">22.</td><td>Tuncer Ali Han</td></tr>
                        <tr><td>(penalty kick) </td><td style="width: 4ex; text-align: right;">78.</td><td>Ntcham Olivier</td></tr>
                    </table>
                </li>
                <li class="list-details__item">
                    <table class="table-main">
                        <tr><td style="width: 4ex; text-align: right;">76.</td><td>Basev Selim</td><td></td></tr>
                        <tr><td style="width: 4ex; text-align: right;">90+7.</td><td>Sari Yusuf</td><td></td></tr>
                    </table>
                </li>
            </ul>
        """
        html_2 = """
            <ul class="list-details list-details--shooters">
                <li class="list-details__item">
                    <table class="table-main">
                        <tr><td></td><td style="width: 4ex; text-align: right;">00:31</td><td>Kawashima Makoto</td></tr>
                        <tr><td></td><td style="width: 4ex; text-align: right;">02:50</td><td>Saito Takeshi</td></tr>
                    </table>
                </li>
                <li class="list-details__item">
                    <table class="table-main">
                        <tr><td style="width: 4ex; text-align: right;">48:34</td><td>Zhang Hao</td><td></td></tr>
                        <tr><td style="width: 4ex; text-align: right;">55:06</td><td>Kondo Katsumasa</td><td></td></tr>
                    </table>
                </li>
            </ul>
        """
        node = parser(html).css_first(CSS_SHOOTERS)
        for tab_index, tab_item in enumerate(node.iter(False)):
            table_data = tab_item.css_first('table tbody')
            res: List[ShooterBetexplorer] = parsing_shooters(SportType.FOOTBALL, table_data, tab_index)
            if tab_index == 0:
                assert not DeepDiff(pars, res)
            if tab_index == 1:
                assert not DeepDiff(pars2, res)

        node = parser(html_2).css_first(CSS_SHOOTERS)
        for tab_index, tab_item in enumerate(node.iter(False)):
            table_data = tab_item.css_first('table tbody')
            res: List[ShooterBetexplorer] = parsing_shooters(SportType.FOOTBALL, table_data, tab_index)
            if tab_index == 0:
                assert not DeepDiff(pars_21, res)
            if tab_index == 1:
                assert not DeepDiff(pars_22, res)

@pytest.mark.asyncio()
@pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
async def test_parsing_match_time(parser):
    sport_id = SportType.FOOTBALL.value
    championship_id = 1
    pars: MatchBetexplorer = {
        'match_id': None,
        'championship_id': championship_id,
        'match_url': None,
        'home_team':
            {
                'team_id': None,
                'sport_id': sport_id,
                'team_name': 'Betis',
                'team_full': 'Real Betis Balompie',
                'team_url': '/football/team/betis/vJbTeCGP/',
                'team_country': None,
                'country_id': None,
                'team_emblem': ' /res/images/team-logo/W4K4TTmh-zkU5wiAr.png',
                'download_date': None,
                'save_date': None,
            },
        'home_team_emblem': ' /res/images/team-logo/W4K4TTmh-zkU5wiAr.png',
        'away_team':
            {
                'team_id': None,
                'sport_id': sport_id,
                'team_name': 'Barcelona',
                'team_full': ' Futbol Club Barcelona ',
                'team_url': '/football/team/barcelona/SKbpVP5K/',
                'team_country': None,
                'country_id': None,
                'team_emblem': ' /res/images/team-logo/hxEqh383-fcDVLdrL.png',
                'download_date': None,
                'save_date': None,
            },
        'away_team_emblem': ' /res/images/team-logo/hxEqh383-fcDVLdrL.png',
        'home_score': 2,
        'away_score': 3,
        'odds_1': None,
        'odds_x': None,
        'odds_2': None,
        'game_date': datetime.datetime(2023, 1, 12, 20, 0),
        'score_stage': 'After Penalties',
        'score_stage_short': None,
        'score_halves': [
            {'time_id': None,
             'half_number': 0,
             'home_score': 0,
             'away_score': 1
             },
            {'time_id': None,
             'half_number': 1,
             'home_score': 1,
             'away_score': 0},
            {'time_id': None,
             'half_number': 2,
             'home_score': 1,
             'away_score': 1
             },
            {'time_id': None,
             'half_number': 3,
             'home_score': 2,
             'away_score': 4
             }
        ],
        'shooters': [
            {'shooter_id': None, 'home_away': 0, 'event_order': 0, 'event_time': '77', 'overtime': None, 'player_name': 'Fekir Nabil', 'penalty_kick': None},
            {'shooter_id': None, 'home_away': 0, 'event_order': 1, 'event_time': '101', 'overtime': None, 'player_name': 'Moron Loren', 'penalty_kick': None},
            {'shooter_id': None, 'home_away': 0, 'event_order': 2, 'event_time': None, 'overtime': None, 'player_name': 'Willian Jose', 'penalty_kick': '(penalty kick)'},
            {'shooter_id': None, 'home_away': 0, 'event_order': 3, 'event_time': None, 'overtime': None, 'player_name': 'Moron Loren', 'penalty_kick': '(penalty kick)'},
            {'shooter_id': None, 'home_away': 1, 'event_order': 0, 'event_time': '40', 'overtime': None, 'player_name': 'Lewandowski Robert', 'penalty_kick': None},
            {'shooter_id': None, 'home_away': 1, 'event_order': 1, 'event_time': '93', 'overtime': None, 'player_name': 'Fati Ansu', 'penalty_kick': None},
            {'shooter_id': None, 'home_away': 1, 'event_order': 2, 'event_time': None, 'overtime': None, 'player_name': 'Lewandowski Robert', 'penalty_kick': '(penalty kick)'},
            {'shooter_id': None, 'home_away': 1, 'event_order': 3, 'event_time': None, 'overtime': None, 'player_name': 'Kessie Franck', 'penalty_kick': '(penalty kick)'},
            {'shooter_id': None, 'home_away': 1, 'event_order': 4, 'event_time': None, 'overtime': None, 'player_name': 'Fati Ansu', 'penalty_kick': '(penalty kick)'},
            {'shooter_id': None, 'home_away': 1, 'event_order': 5, 'event_time': None, 'overtime': None, 'player_name': 'Pedri', 'penalty_kick': '(penalty kick)'}
        ],
        'stage_name': 'stage_name',
        'round_name': 'round_name',
        'round_number': 10,
        'is_fixture': 1,
        'save_date': datetime.datetime.now(),
        'download_date': datetime.datetime(year=1, month=1, day=1, hour=0, minute=0, second=0),
    }
    html = """
        <div>
            <ul class="list-details borderTop0">
                <li class="list-details__item">
                    <a href="/football/team/betis/vJbTeCGP/">
                        <figure class="list-details__item__team">
                            <div>
                                <img src=" /res/images/team-logo/W4K4TTmh-zkU5wiAr.png" alt="Real Betis Balompie"/>
                            </div>
                        </figure>
                        <h2 class="list-details__item__title teamsLink">Betis</h2>
                        <input type="hidden" value="1101" id="homeParticipantIdHeader"/>
                    </a>
                </li>
                <li class="list-details__item">
                    <p class="list-details__item__date headerTournamentDate" id="match-date" data-dt="12,1,2023,20,00"></p>
                    <p class="list-details__item__score" id="js-score">2:3</p>
                    <h2 class="list-details__item__eventstage" id="js-eventstage">After Penalties</h2>
                    <h2 class="list-details__item__partial" id="js-partial">(0:1, 1:0, 1:1, 2:4)</h2>
                </li>
                <li class="list-details__item">
                    <a href="/football/team/barcelona/SKbpVP5K/">
                        <figure class="list-details__item__team">
                            <div>
                                <img src=" /res/images/team-logo/hxEqh383-fcDVLdrL.png" alt=" Futbol Club Barcelona "/>
                            </div>
                        </figure>
                        <h2 class="list-details__item__title teamsLink">Barcelona</h2>
                        <input type="hidden" value="1091" id="awayParticipantIdHeader"/>
                    </a>
                </li>
            </ul>
            <ul class="list-details list-details--shooters">
                <li class="list-details__item">
                    <table class="table-main">
                        <tr>
                            <td></td>
                            <td style="width: 4ex; text-align: right;">77.</td>
                            <td>Fekir Nabil</td>
                        </tr>
                        <tr>
                            <td></td>
                            <td style="width: 4ex; text-align: right;">101.</td>
                            <td>Moron Loren</td>
                        </tr>
                        <tr>
                            <td>(penalty kick) </td>
                            <td style="width: 4ex; text-align: right;">&nbsp;</td>
                            <td>Willian Jose</td>
                        </tr>
                        <tr>
                            <td>(penalty kick) </td>
                            <td style="width: 4ex; text-align: right;">&nbsp;</td>
                            <td>Moron Loren</td>
                        </tr>
                    </table>
                </li>
                <li class="list-details__item">
                    <table class="table-main">
                        <tr>
                            <td style="width: 4ex; text-align: right;">40.</td>
                            <td>Lewandowski Robert</td>
                            <td></td>
                        </tr>
                        <tr>
                            <td style="width: 4ex; text-align: right;">93.</td>
                            <td>Fati Ansu</td>
                            <td></td>
                        </tr>
                        <tr>
                            <td style="width: 4ex; text-align: right;">&nbsp;</td>
                            <td>Lewandowski Robert</td>
                            <td>(penalty kick) </td>
                        </tr>
                        <tr>
                            <td style="width: 4ex; text-align: right;">&nbsp;</td>
                            <td>Kessie Franck</td>
                            <td>(penalty kick) </td>
                        </tr>
                        <tr>
                            <td style="width: 4ex; text-align: right;">&nbsp;</td>
                            <td>Fati Ansu</td>
                            <td>(penalty kick) </td>
                        </tr>
                        <tr>
                            <td style="width: 4ex; text-align: right;">&nbsp;</td>
                            <td>Pedri</td>
                            <td>(penalty kick) </td>
                        </tr>
                    </table>
                </li>
            </ul>
        </div>
    """
    node = parser(html).css_first('div')
    soap: ReceivedData = ReceivedData(node, datetime.datetime(2020, 1, 1, 10, 30))
    match: Optional[MatchBetexplorer] = parsing_match_time(soap, SportType.FOOTBALL, championship_id, 'stage_name', 'round_name', 10, IS_FIXTURE)
    assert not DeepDiff(pars, match, exclude_paths=["root['save_date']", "root['download_date']", "root['home_team']['download_date']", "root['home_team']['save_date']", "root['away_team']['download_date']", "root['away_team']['save_date']"])


class TestUpdateMatchTime:

    @pytest.mark.asyncio()
    async def test_update_match_time(self):
        pars: MatchBetexplorer = {
            'match_id': None,
            'match_url': None,
            'home_team':
                {
                    'team_id': None,
                    'team_name': 'Betis',
                    'team_full': None,
                    'team_url': None,
                    'team_country': None,
                    'country_id': None,
                    'team_emblem': None,
                    'download_date': None,
                    'save_date': None,
                },
            'home_team_emblem': None,
            'away_team':
                {'team_id': None,
                 'team_name': 'Barcelona',
                 'team_full': None,
                 'team_url': None,
                 'team_country': None,
                 'country_id': None,
                 'team_emblem': None,
                 'download_date': None,
                 'save_date': None,
                 },
            'away_team_emblem': None,
            'home_score': 2,
            'away_score': 3,
            'odds_1': None,
            'odds_x': None,
            'odds_2': None,
            'game_date': datetime.datetime(2023, 1, 12),
            'score_stage': 'After Penalties',
            'score_stage_short': None,
            'score_halves': [],
            'shooters': [],
            'stage_name': 'stage_name',
            'round_name': 'round_name',
            'round_number': 10,
            'is_fixture': 1,
        }

        pars_2: MatchBetexplorer = {
            'match_id': None,
            'match_url': None,
            'home_team':
                {
                    'team_id': None,
                    'team_name': 'Betis',
                    'team_full': 'Real Betis Balompie',
                    'team_url': '/football/team/betis/vJbTeCGP/',
                    'team_country': None,
                    'country_id': None,
                    'team_emblem': ' /res/images/team-logo/W4K4TTmh-zkU5wiAr.png',
                    'download_date': None,
                    'save_date': None,
                },
            'home_team_emblem': '/sasdasd',
            'away_team':
                {'team_id': None,
                 'team_name': 'Barcelona',
                 'team_full': ' Futbol Club Barcelona ',
                 'team_url': '/football/team/barcelona/SKbpVP5K/',
                 'team_country': None,
                 'country_id': None,
                 'team_emblem': ' /res/images/team-logo/hxEqh383-fcDVLdrL.png',
                 'download_date': None,
                 'save_date': None,
                 },
            'away_team_emblem': 'savasvasav',
            'home_score': 2,
            'away_score': 3,
            'odds_1': None,
            'odds_x': None,
            'odds_2': None,
            'game_date': datetime.datetime(2023, 1, 12, 20, 0),
            'score_stage': 'After Penalties',
            'score_stage_short': None,
            'score_halves': [
                {'time_id': None,
                 'half_number': 0,
                 'home_score': 0,
                 'away_score': 1
                 },
                {'time_id': None,
                 'half_number': 1,
                 'home_score': 1,
                 'away_score': 0},
                {'time_id': None,
                 'half_number': 2,
                 'home_score': 1,
                 'away_score': 1
                 },
                {'time_id': None,
                 'half_number': 3,
                 'home_score': 2,
                 'away_score': 4
                 }
            ],
            'shooters': [
                {'shooter_id': None, 'home_away': 0, 'event_order': 0, 'event_time': '77', 'overtime': None, 'player_name': 'Fekir Nabil', 'penalty_kick': None},
                {'shooter_id': None, 'home_away': 0, 'event_order': 1, 'event_time': '101', 'overtime': None, 'player_name': 'Moron Loren', 'penalty_kick': None},
                {'shooter_id': None, 'home_away': 0, 'event_order': 2, 'event_time': None, 'overtime': None, 'player_name': 'Willian Jose', 'penalty_kick': '(penalty kick)'},
                {'shooter_id': None, 'home_away': 0, 'event_order': 3, 'event_time': None, 'overtime': None, 'player_name': 'Moron Loren', 'penalty_kick': '(penalty kick)'},
                {'shooter_id': None, 'home_away': 1, 'event_order': 0, 'event_time': '40', 'overtime': None, 'player_name': 'Lewandowski Robert', 'penalty_kick': None},
                {'shooter_id': None, 'home_away': 1, 'event_order': 1, 'event_time': '93', 'overtime': None, 'player_name': 'Fati Ansu', 'penalty_kick': None},
                {'shooter_id': None, 'home_away': 1, 'event_order': 2, 'event_time': None, 'overtime': None, 'player_name': 'Lewandowski Robert', 'penalty_kick': '(penalty kick)'},
                {'shooter_id': None, 'home_away': 1, 'event_order': 3, 'event_time': None, 'overtime': None, 'player_name': 'Kessie Franck', 'penalty_kick': '(penalty kick)'},
                {'shooter_id': None, 'home_away': 1, 'event_order': 4, 'event_time': None, 'overtime': None, 'player_name': 'Fati Ansu', 'penalty_kick': '(penalty kick)'},
                {'shooter_id': None, 'home_away': 1, 'event_order': 5, 'event_time': None, 'overtime': None, 'player_name': 'Pedri', 'penalty_kick': '(penalty kick)'},
            ],
            'stage_name': 'stage_name',
            'round_name': 'round_name',
            'round_number': 10,
            'is_fixture': 1,
        }

        pars_3: MatchBetexplorer = {
            'match_id': None,
            'match_url': None,
            'home_team':
                {
                    'team_id': None,
                    'team_name': 'Betis',
                    'team_full': 'Real Betis Balompie',
                    'team_url': '/football/team/betis/vJbTeCGP/',
                    'team_country': None,
                    'country_id': None,
                    'team_emblem': ' /res/images/team-logo/W4K4TTmh-zkU5wiAr.png',
                    'download_date': None,
                    'save_date': None,
                },
            'away_team':
                {'team_id': None,
                 'team_name': 'Barcelona',
                 'team_full': ' Futbol Club Barcelona ',
                 'team_url': '/football/team/barcelona/SKbpVP5K/',
                 'team_country': None,
                 'country_id': None,
                 'team_emblem': ' /res/images/team-logo/hxEqh383-fcDVLdrL.png',
                 'download_date': None,
                 'save_date': None,
                 },
            'home_score': 2,
            'away_score': 3,
            'odds_1': None,
            'odds_x': None,
            'odds_2': None,
            'game_date': datetime.datetime(2023, 1, 12, 20, 0),
            'score_stage': 'After Penalties',
            'score_stage_short': None,
            'score_halves': [
                {'time_id': None,
                 'half_number': 0,
                 'home_score': 0,
                 'away_score': 1
                 },
                {'time_id': None,
                 'half_number': 1,
                 'home_score': 1,
                 'away_score': 0},
                {'time_id': None,
                 'half_number': 2,
                 'home_score': 1,
                 'away_score': 1
                 },
                {'time_id': None,
                 'half_number': 3,
                 'home_score': 2,
                 'away_score': 4
                 }
            ],
            'home_shooters': [
                {'shooter_id': None, 'home_away': 0, 'event_order': 0, 'event_time': '77', 'overtime': None, 'player_name': 'Fekir Nabil', 'penalty_kick': None},
                {'shooter_id': None, 'home_away': 0, 'event_order': 1, 'event_time': '101', 'overtime': None, 'player_name': 'Moron Loren', 'penalty_kick': None},
                {'shooter_id': None, 'home_away': 0, 'event_order': 2, 'event_time': None, 'overtime': None, 'player_name': 'Willian Jose', 'penalty_kick': '(penalty kick)'},
                {'shooter_id': None, 'home_away': 0, 'event_order': 3, 'event_time': None, 'overtime': None, 'player_name': 'Moron Loren', 'penalty_kick': '(penalty kick)'},
                {'shooter_id': None, 'home_away': 1, 'event_order': 0, 'event_time': '40', 'overtime': None, 'player_name': 'Lewandowski Robert', 'penalty_kick': None},
                {'shooter_id': None, 'home_away': 1, 'event_order': 1, 'event_time': '93', 'overtime': None, 'player_name': 'Fati Ansu', 'penalty_kick': None},
                {'shooter_id': None, 'home_away': 1, 'event_order': 2, 'event_time': None, 'overtime': None, 'player_name': 'Lewandowski Robert', 'penalty_kick': '(penalty kick)'},
                {'shooter_id': None, 'home_away': 1, 'event_order': 3, 'event_time': None, 'overtime': None, 'player_name': 'Kessie Franck', 'penalty_kick': '(penalty kick)'},
                {'shooter_id': None, 'home_away': 1, 'event_order': 4, 'event_time': None, 'overtime': None, 'player_name': 'Fati Ansu', 'penalty_kick': '(penalty kick)'},
                {'shooter_id': None, 'home_away': 1, 'event_order': 5, 'event_time': None, 'overtime': None, 'player_name': 'Pedri', 'penalty_kick': '(penalty kick)'},
            ],
            'stage_name': 'stage_name',
            'round_name': 'round_name',
            'round_number': 10,
            'is_fixture': 1,
        }

        update_match_time(pars, pars_2)
        assert not DeepDiff(pars, pars_2)


class TestGetColumnType:
    """Тест определения типа колонки."""

    @pytest.mark.asyncio()
    async def test_get_column_type(self):
        for sport_id in [SportType.FOOTBALL, SportType.HOCKEY, SportType.HANDBALL]:
            res = get_column_type(sport_id, IS_RESULT, 0)
            assert res == COLUMN_TEAMS
            res = get_column_type(sport_id, IS_RESULT, 1)
            assert res == COLUMN_SCORE
            res = get_column_type(sport_id, IS_RESULT, 2)
            assert res == COLUMN_ODDS_1
            res = get_column_type(sport_id, IS_RESULT, 3)
            assert res == COLUMN_ODDS_X
            res = get_column_type(sport_id, IS_RESULT, 4)
            assert res == COLUMN_ODDS_2
            res = get_column_type(sport_id, IS_RESULT, 5)
            assert res == COLUMN_GAME_DATE
            res = get_column_type(sport_id, IS_RESULT, 6)
            assert res is None

        for sport_id in [SportType.BASEBALL, SportType.TENNIS, SportType.BASKETBALL, SportType.VOLLEYBALL]:
            res = get_column_type(sport_id, IS_RESULT, 0)
            assert res == COLUMN_TEAMS
            res = get_column_type(sport_id, IS_RESULT, 1)
            assert res == COLUMN_SCORE
            res = get_column_type(sport_id, IS_RESULT, 2)
            assert res == COLUMN_ODDS_1
            res = get_column_type(sport_id, IS_RESULT, 3)
            assert res == COLUMN_ODDS_2
            res = get_column_type(sport_id, IS_RESULT, 4)
            assert res == COLUMN_GAME_DATE
            res = get_column_type(sport_id, IS_RESULT, 5)
            assert res is None

        for sport_id in [SportType.FOOTBALL, SportType.HOCKEY, SportType.HANDBALL]:
            res = get_column_type(sport_id, IS_FIXTURE, 0)
            assert res == COLUMN_GAME_DATE
            res = get_column_type(sport_id, IS_FIXTURE, 1)
            assert res == COLUMN_TEAMS
            res = get_column_type(sport_id, IS_FIXTURE, 4)
            assert res == COLUMN_ODDS_1
            res = get_column_type(sport_id, IS_FIXTURE, 5)
            assert res == COLUMN_ODDS_X
            res = get_column_type(sport_id, IS_FIXTURE, 6)
            assert res == COLUMN_ODDS_2
            res = get_column_type(sport_id, IS_FIXTURE, 2)
            assert res is None
            res = get_column_type(sport_id, IS_FIXTURE, 3)
            assert res is None
            res = get_column_type(sport_id, IS_FIXTURE, 7)
            assert res is None

        for sport_id in [SportType.BASEBALL, SportType.TENNIS, SportType.BASKETBALL, SportType.VOLLEYBALL]:
            res = get_column_type(sport_id, IS_FIXTURE, 0)
            assert res == COLUMN_GAME_DATE
            res = get_column_type(sport_id, IS_FIXTURE, 1)
            assert res == COLUMN_TEAMS
            res = get_column_type(sport_id, IS_FIXTURE, 4)
            assert res == COLUMN_ODDS_1
            res = get_column_type(sport_id, IS_FIXTURE, 5)
            assert res == COLUMN_ODDS_2
            res = get_column_type(sport_id, IS_FIXTURE, 2)
            assert res is None
            res = get_column_type(sport_id, IS_FIXTURE, 3)
            assert res is None
            res = get_column_type(sport_id, IS_FIXTURE, 6)
            assert res is None

class TestMatchInit:

    @pytest.mark.asyncio()
    async def test_match_init(self):
        sport_id = SportType.FOOTBALL.value
        championship_id = 1
        stage_name = 'Qualification'
        round_name = '26. ROUND'
        round_number = 26
        is_fixture = 0

        pars: MatchBetexplorer = {
            'match_id': None, 'match_url': None,
            'championship_id': championship_id,
            'home_team': {
                'team_id': None,
                'sport_id': sport_id,
                'team_name': None,
                'team_full': None,
                'team_url': None,
                'team_country': None,
                'country_id': None,
                'team_emblem': None,
                'download_date': datetime.datetime(2023, 10, 17),
                'save_date': datetime.datetime(2023, 10, 17),
            },
            'home_team_emblem': None,
            'away_team': {
                'team_id': None,
                'sport_id': sport_id,
                'team_name': None,
                'team_full': None,
                'team_url': None,
                'team_country': None,
                'country_id': None,
                'team_emblem': None,
                'download_date': datetime.datetime(2023, 10, 17),
                'save_date': datetime.datetime(2023, 10, 17),
            },
            'away_team_emblem': None,
            'home_score': None, 'away_score': None,
            'odds_1': None, 'odds_x': None, 'odds_2': None,
            'game_date': None,
            'score_stage': None, 'score_stage_short': None,
            'score_halves': [],
            'shooters': [],
            'stage_name': 'Qualification',
            'round_name': '26. ROUND',
            'round_number': 26,
            'is_fixture': 0,
            'download_date': datetime.datetime(2023, 10, 17),
            'save_date': datetime.datetime.now(),
        }
        res = match_init(
            sport_id=sport_id,
            championship_id=championship_id,
            stage_name=stage_name,
            round_name=round_name,
            round_number=round_number,
            is_fixture=is_fixture,
            creation_date=datetime.datetime(2023, 10, 17),
        )
        assert not DeepDiff(pars, res, exclude_paths=["root['save_date']", "root['download_date']", "root['away_team']['save_date']", "root['home_team']['save_date']"])


class TestParsingResults:

    @pytest.mark.asyncio()
    @pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
    async def test_parsing_results(self, parser):
        championship_id = 1
        sport_id = SportType.FOOTBALL.value

        pars: List[ChampionshipStageBetexplorer] = [
            {
                'stage_id': None,
                'stage_url': '?stage=Q1agpwdd',
                'stage_name': 'Qualification',
                'stage_order': 0,
                'stage_current': False
            },
            {
                'stage_id': None,
                'stage_url': '?stage=nB0koJtj',
                'stage_name': 'Main',
                'stage_order': 1,
                'stage_current': True
            },
        ]
        pars_match: List[MatchBetexplorer] = [
            {
                'match_id': None,
                'championship_id': championship_id,
                'match_url': '/football/england/fa-cup/barnet-aveley/8xz3zfD8/',
                'home_team': {
                    'team_id': None,
                    'sport_id': sport_id,
                    'team_name': 'Barnet',
                    'team_full': None,
                    'team_url': None,
                    'team_country': None,
                    'country_id': None,
                    'team_emblem': None,
                    'download_date': None,
                    'save_date': None,
                },
                'home_team_emblem': None,
                'away_team': {
                    'team_id': None,
                    'sport_id': sport_id,
                    'team_name': 'Aveley',
                    'team_full': None,
                    'team_url': None,
                    'team_country': None,
                    'country_id': None,
                    'team_emblem': None,
                    'download_date': None,
                    'save_date': None,
                },
                'away_team_emblem': None,
                'home_score': 4,
                'away_score': 0,
                'odds_1': 1.30,
                'odds_x': 5.29,
                'odds_2': 8.03,
                'game_date': datetime.datetime(2023, 10, 17),
                'score_stage': None,
                'score_stage_short': None,
                'stage_name': 'Main',
                'score_halves': [],
                'shooters': [],
                'round_name': 'Final - 2nd leg',
                'round_number': None,
                'is_fixture': 0,
                'download_date': None,
                'save_date': None,
            },
            {
                'match_id': None,
                'championship_id': championship_id,
                'match_url': '/football/england/fa-cup/sheppey-united-billericay/MN61ILiN/',
                'home_team': {
                    'team_id': None,
                    'sport_id': sport_id,
                    'team_name': 'Sheppey United',
                    'team_full': None,
                    'team_url': None,
                    'team_country': None,
                    'country_id': None,
                    'team_emblem': None,
                    'download_date': None,
                    'save_date': None,
                },
                'home_team_emblem': None,
                'away_team': {
                    'team_id': None,
                    'sport_id': sport_id,
                    'team_name': 'Billericay',
                    'team_full': None,
                    'team_url': None,
                    'team_country': None,
                    'country_id': None,
                    'team_emblem': None,
                    'download_date': None,
                    'save_date': None,
                },
                'away_team_emblem': None,
                'home_score': 2,
                'away_score': 1,
                'odds_1': 3.22,
                'odds_x': 3.67,
                'odds_2': 1.98,
                'game_date': datetime.datetime(2023, 10, 17),
                'score_stage': 'After Penalties',
                'score_stage_short': 'PEN.',
                'stage_name': 'Main',
                'score_halves': [],
                'shooters': [],
                'round_name': 'Final - 1st leg',
                'round_number': None,
                'is_fixture': 0,
                'download_date': None,
                'save_date': None,
            },
        ]
        html = """
            <div id="home-page-left-column" class=" columns__item columns__item--68 columns__item--tab-100">
                <div class="h-mb15">
                    <div class="box-overflow" id="sm-0-0">
                        <div class="box-overflow__in">
                            <ul class="list-tabs list-tabs--secondary">
                                <li class="list-tabs__item">
                                    <a href="?stage=Q1agpwdd" title="" class="list-tabs__item__in">Qualification</a>
                                </li>
                                <li class="list-tabs__item">
                                    <a href="?stage=nB0koJtj" title="Main season game statistics" class="list-tabs__item__in current">Main</a>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
    
                <div class="box-overflow"><div class="box-overflow__in"><table class="table-main js-tablebanner-t js-tablebanner-ntb"><tr><th class="h-text-left" colspan="2">Final - 2nd leg</th><th class="h-text-center">1</th><th class="h-text-center">X</th><th class="h-text-center">2</th><th>&nbsp;</th></tr>
                <tr><td class="h-text-left"><a href="/football/england/fa-cup/barnet-aveley/8xz3zfD8/" class="in-match"><span><strong>Barnet</strong></span> - <span>Aveley</span></a></td><td class="h-text-center"><a href="/football/england/fa-cup/barnet-aveley/8xz3zfD8/">4:0</a></td><td class="table-main__odds colored" data-oid="6pdsqxv464x0xi6l9m"><span><span><span data-odd="1.30"></span></span></span></td><td class="table-main__odds" data-oid="6pdsqxv498x0x0" data-odd="5.29"></td><td class="table-main__odds" data-oid="6pdsqxv464x0xi6l9l" data-odd="8.03"></td><td class="h-text-right h-text-no-wrap">17.10.2023</td></tr>
                <tr><th class="h-text-left" colspan="2">Final - 1st leg</th><th class="h-text-center">1</th><th class="h-text-center">X</th><th class="h-text-center">2</th><th>&nbsp;</th></tr>
                <tr><td class="h-text-left"><a href="/football/england/fa-cup/sheppey-united-billericay/MN61ILiN/" class="in-match"><span>Sheppey United</span> - <span>Billericay</span></a></td><td class="h-text-center"><a href="/football/england/fa-cup/sheppey-united-billericay/MN61ILiN/">2:1 <span title="After Penalties">PEN.</span></a></td><td class="table-main__odds" data-oid="6pdscxv464x0xi6l8q" data-odd="3.22"></td><td class="table-main__odds colored" data-oid="6pdscxv498x0x0"><span><span><span data-odd="3.67"></span></span></span></td><td class="table-main__odds" data-oid="6pdscxv464x0xi6l8p" data-odd="1.98"></td><td class="h-text-right h-text-no-wrap">17.10.2023</td></tr>
                </table></div></div>
            </div>
        """
        node = parser(html).css_first(CSS_RESULTS)
        soap: ReceivedData = ReceivedData(node, datetime.datetime(2020, 1, 1, 10, 30))
        res = parsing_results(soap, SportType.FOOTBALL, championship_id, IS_RESULT)
        assert not DeepDiff(pars, res['stages'])
        assert not DeepDiff(pars_match, res['matches'],
                            exclude_paths=["root[0]['save_date']", "root[0]['download_date']",
                                           "root[1]['save_date']", "root[1]['download_date']",
                                           "root[0]['home_team']['download_date']",
                                           "root[0]['home_team']['save_date']",
                                           "root[0]['away_team']['download_date']",
                                           "root[0]['away_team']['save_date']",
                                           "root[1]['home_team']['download_date']",
                                           "root[1]['home_team']['save_date']",
                                           "root[1]['away_team']['download_date']",
                                           "root[1]['away_team']['save_date']",
                                           ])


class TestGetResults:

    @pytest.mark.asyncio()
    @pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
    async def test_get_results(self, parser):
        sport_id = SportType.FOOTBALL.value
        championship_id = 1
        pars: List[ChampionshipStageBetexplorer] = [
            {
                'stage_id': None,
                'stage_url': '?stage=8z4wQG6n',
                'stage_name': 'Qualification',
                'stage_order': 0,
                'stage_current': False
            },
            {
                'stage_id': None,
                'stage_url': '?stage=ED4ZQdit',
                'stage_name': 'Main',
                'stage_order': 1,
                'stage_current': True
            }
        ]
        pars_match: List[MatchBetexplorer] = [
            {
                'match_id': None,
                'championship_id': championship_id,
                'match_url': '/football/england/fa-cup/port-vale-stevenage/KbYVJVpC/',
                'home_team': {
                    'team_id': None,
                    'sport_id': sport_id,
                    'team_name': 'Port Vale',
                    'team_full': None,
                    'team_url': None,
                    'team_country': None,
                    'country_id': None,
                    'team_emblem': None,
                    'download_date': datetime.datetime(year=2021, month=1, day=1),
                    'save_date': datetime.datetime(year=2022, month=2, day=2),
                },
                'home_team_emblem': None,
                'away_team': {
                    'team_id': None,
                    'sport_id': sport_id,
                    'team_name': 'Stevenage',
                    'team_full': None,
                    'team_url': None,
                    'team_country': None,
                    'country_id': None,
                    'team_emblem': None,
                    'download_date': datetime.datetime(year=2021, month=1, day=1),
                    'save_date': datetime.datetime(year=2022, month=2, day=2),
                },
                'away_team_emblem': None,
                'home_score': 3,
                'away_score': 4,
                'odds_1': 2.73,
                'odds_x': 3.21,
                'odds_2': 2.61,
                'game_date': datetime.datetime(2023, 12, 12),
                'score_stage': 'After Penalties',
                'score_stage_short': 'PEN.',
                'stage_name': 'Main',
                'score_halves': [],
                'shooters': [],
                'round_name': '1/16-finals - 1st leg',
                'round_number': None,
                'is_fixture': 0,
                'download_date': datetime.datetime(year=2021, month=1, day=1),
                'save_date': None,
            },
            {
                'match_id': None,
                'championship_id': championship_id,
                'match_url': '/football/england/fa-cup/barnet-aveley/8xz3zfD8/',
                'home_team': {
                    'team_id': None,
                    'sport_id': sport_id,
                    'team_name': 'Barnet',
                    'team_full': None,
                    'team_url': None,
                    'team_country': None,
                    'country_id': None,
                    'team_emblem': None,
                    'download_date': datetime.datetime(year=2021, month=1, day=1),
                    'save_date': datetime.datetime(year=2022, month=2, day=2),
                },
                'home_team_emblem': None,
                'away_team': {
                    'team_id': None,
                    'sport_id': sport_id,
                    'team_name': 'Aveley',
                    'team_full': None,
                    'team_url': None,
                    'team_country': None,
                    'country_id': None,
                    'team_emblem': None,
                    'download_date': datetime.datetime(year=2021, month=1, day=1),
                    'save_date': datetime.datetime(year=2022, month=2, day=2),
                },
                'away_team_emblem': None,
                'home_score': 4,
                'away_score': 0,
                'odds_1': 1.3,
                'odds_x': 5.29,
                'odds_2': 8.03,
                'game_date': datetime.datetime(2023, 10, 17),
                'score_stage': None,
                'score_stage_short': None,
                'stage_name': 'Qualification',
                'score_halves': [],
                'shooters': [],
                'round_name': 'Final - 2nd leg',
                'round_number': None,
                'is_fixture': 0,
                'save_date': None,
                'download_date': datetime.datetime(year=2021, month=1, day=1),
            },
        ]
        pars_match_fix: List[MatchBetexplorer] = [
            {
                'match_id': None,
                'championship_id': championship_id,
                'match_url': '/football/england/fa-cup/west-brom-wolves/0G4fwRU4/',
                'home_team': {
                    'team_id': None,
                    'sport_id': sport_id,
                    'team_name': 'West Brom',
                    'team_full': None,
                    'team_url': None,
                    'team_country': None,
                    'country_id': None,
                    'team_emblem': None,
                    'download_date': datetime.datetime(year=2021, month=1, day=1),
                    'save_date': datetime.datetime(year=2022, month=2, day=2),
                },
                'home_team_emblem': None,
                'away_team': {
                    'team_id': None,
                    'sport_id': sport_id,
                    'team_name': 'Wolves',
                    'team_full': None,
                    'team_url': None,
                    'team_country': None,
                    'country_id': None,
                    'team_emblem': None,
                    'download_date': datetime.datetime(year=2021, month=1, day=1),
                    'save_date': datetime.datetime(year=2022, month=2, day=2),
                },
                'away_team_emblem': None,
                'home_score': None,
                'away_score': None,
                'odds_1': 3.62,
                'odds_x': 3.46,
                'odds_2': 2.01,
                'game_date': datetime.datetime(2024, 2, 23, 12, 45),
                'score_stage': None,
                'score_stage_short': None,
                'stage_name': 'Main',
                'score_halves': [],
                'shooters': [],
                'round_name': '1/16-finals - 1st leg',
                'round_number': None,
                'is_fixture': 1,
                'save_date': None,
            },
        ]

        ls = LoadSave(
            root_url='https://www.betexplorer.com',
            root_dir=settings.DOWNLOAD_TEST_DIRECTORY,
        )

        ls.load_net = False
        res = await get_results('/football/england/fa-cup/', SportType.FOOTBALL, championship_id, IS_RESULT, False)
        assert not DeepDiff(pars, res['stages'])
        assert not DeepDiff(pars_match, res['matches'],
                            exclude_paths=["root[0]['save_date']", "root[0]['download_date']",
                                           "root[1]['save_date']", "root[1]['download_date']",
                                           "root[0]['home_team']['download_date']",
                                           "root[0]['home_team']['save_date']",
                                           "root[0]['away_team']['download_date']",
                                           "root[0]['away_team']['save_date']",
                                           "root[1]['home_team']['download_date']",
                                           "root[1]['home_team']['save_date']",
                                           "root[1]['away_team']['download_date']",
                                           "root[1]['away_team']['save_date']"])

        res = await get_results('/football/england/fa-cup/', SportType.FOOTBALL, championship_id, IS_FIXTURE, False)
        assert not DeepDiff(pars, res['stages'])
        assert not DeepDiff(pars_match_fix, res['matches'],
                            exclude_paths=["root[0]['save_date']", "root[0]['download_date']",
                                           "root[1]['save_date']", "root[1]['download_date']",
                                           "root[0]['home_team']['download_date']",
                                           "root[0]['home_team']['save_date']",
                                           "root[0]['away_team']['download_date']",
                                           "root[0]['away_team']['save_date']",
                                           "root[1]['home_team']['download_date']",
                                           "root[1]['home_team']['save_date']",
                                           "root[1]['away_team']['download_date']",
                                           "root[1]['away_team']['save_date']"])

class TestGetTeam:

    @pytest.mark.asyncio()
    @pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
    async def test_get_team(self, parser):
        sport_id = SportType.FOOTBALL.value
        team: TeamBetexplorer = {
            'team_id': None,
            'sport_id': sport_id,
            'team_name': None,
            'team_full': None,
            'team_url': '/football/team/brighton/2XrRecc3',
            'team_country': None,
            'country_id': None,
            'team_emblem': None,
        }
        fast_country: dict[str, int] = {
            'England': 1,
            'country_id': 2,
        }
        fast_team: dict[(int, int, str, str, str), Optional[TeamBetexplorer]] = {}
        session = None

        ls = LoadSave(
            root_url='https://www.betexplorer.com',
            root_dir=settings.DOWNLOAD_TEST_DIRECTORY,
        )

        ls.load_net = False
        ls.save_database = DATABASE_NOT_USE
        crd = CRUDbetexplorer(save_database=DATABASE_NOT_USE)

        await get_team(ls, crd, session, [team], fast_country, fast_team)
        assert team['team_country'] == 'England'
        assert team['team_emblem'] == '/res/images/team-logo/MmmU7K6n-b92lfEJC.png'
        assert team['country_id'] == 1

        ft = fast_team.get(team['team_url'])
        assert ft is not None
        ft['team_id'] = 1
        await get_team(ls, crd, session, [team], fast_country, fast_team)
        assert team['team_id'] == 1


class TestGetResultsFixtures:

    @pytest.mark.asyncio()
    @pytest.mark.parametrize(*_PARSERS_PARAMETRIZER)
    async def test_get_results_fixtures(self, parser):
        championship_id = 1
        sport_id = SportType.FOOTBALL.value

        pars: List[ChampionshipStageBetexplorer] = [
            {
                'stage_id': None,
                'stage_url': '?stage=8z4wQG6n',
                'stage_name': 'Qualification',
                'stage_order': 0,
                'stage_current': False
            },
            {
                'stage_id': None,
                'stage_url': '?stage=ED4ZQdit',
                'stage_name': 'Main',
                'stage_order': 1,
                'stage_current': True
            }
        ]
        pars_match: List[MatchBetexplorer] = [
            {
                'match_id': None,
                'championship_id': championship_id,
                'match_url': '/football/england/fa-cup/port-vale-stevenage/KbYVJVpC/',
                'home_team': {
                    'team_id': None,
                    'sport_id': sport_id,
                    'team_name': 'Port Vale',
                    'team_full': None,
                    'team_url': None,
                    'team_country': None,
                    'country_id': None,
                    'team_emblem': None,
                    'download_date': datetime.datetime(year=2021, month=1, day=1),
                    'save_date': datetime.datetime(year=2022, month=2, day=2),
                },
                'home_team_emblem': None,
                'away_team': {
                    'team_id': None,
                    'sport_id': sport_id,
                    'team_name': 'Stevenage',
                    'team_full': None,
                    'team_url': None,
                    'team_country': None,
                    'country_id': None,
                    'team_emblem': None,
                    'download_date': datetime.datetime(year=2021, month=1, day=1),
                    'save_date': datetime.datetime(year=2022, month=2, day=2),
                },
                'away_team_emblem': None,
                'home_score': 3,
                'away_score': 4,
                'odds_1': 2.73,
                'odds_x': 3.21,
                'odds_2': 2.61,
                'game_date': datetime.datetime(2023, 12, 12),
                'score_stage': 'After Penalties',
                'score_stage_short': 'PEN.',
                'stage_name': 'Main',
                'score_halves': [],
                'shooters': [],
                'round_name': '1/16-finals - 1st leg',
                'round_number': None,
                'is_fixture': 0,
                'download_date': datetime.datetime(year=2021, month=1, day=1),
                'save_date': None,
            },
            {
                'match_id': None,
                'championship_id': championship_id,
                'match_url': '/football/england/fa-cup/barnet-aveley/8xz3zfD8/',
                'home_team': {
                    'team_id': None,
                    'sport_id': sport_id,
                    'team_name': 'Barnet',
                    'team_full': None,
                    'team_url': None,
                    'team_country': None,
                    'country_id': None,
                    'team_emblem': None,
                    'download_date': datetime.datetime(year=2021, month=1, day=1),
                    'save_date': datetime.datetime(year=2022, month=2, day=2),
                },
                'home_team_emblem': None,
                'away_team': {
                    'team_id': None,
                    'sport_id': sport_id,
                    'team_name': 'Aveley',
                    'team_full': None,
                    'team_url': None,
                    'team_country': None,
                    'country_id': None,
                    'team_emblem': None,
                    'download_date': datetime.datetime(year=2021, month=1, day=1),
                    'save_date': datetime.datetime(year=2022, month=2, day=2),
                },
                'away_team_emblem': None,
                'home_score': 4,
                'away_score': 0,
                'odds_1': 1.3,
                'odds_x': 5.29,
                'odds_2': 8.03,
                'game_date': datetime.datetime(2023, 10, 17),
                'score_stage': None,
                'score_stage_short': None,
                'stage_name': 'Qualification',
                'score_halves': [],
                'shooters': [],
                'round_name': 'Final - 2nd leg',
                'round_number': None,
                'is_fixture': 0,
                'download_date': datetime.datetime(year=2021, month=1, day=1),
                'save_date': None,
            },
        ]
        pars_match_fix: List[MatchBetexplorer] = [
            {
                'match_id': None,
                'championship_id': championship_id,
                'match_url': '/football/england/fa-cup/west-brom-wolves/0G4fwRU4/',
                'home_team': {
                    'team_id': None,
                    'sport_id': sport_id,
                    'team_name': 'West Brom',
                    'team_full': None,
                    'team_url': None,
                    'team_country': None,
                    'country_id': None,
                    'team_emblem': None,
                    'download_date': datetime.datetime(year=2021, month=1, day=1),
                    'save_date': datetime.datetime(year=2022, month=2, day=2),
                },
                'home_team_emblem': None,
                'away_team': {
                    'team_id': None,
                    'sport_id': sport_id,
                    'team_name': 'Wolves',
                    'team_full': None,
                    'team_url': None,
                    'team_country': None,
                    'country_id': None,
                    'team_emblem': None,
                    'download_date': datetime.datetime(year=2021, month=1, day=1),
                    'save_date': datetime.datetime(year=2022, month=2, day=2),
                },
                'away_team_emblem': None,
                'home_score': None,
                'away_score': None,
                'odds_1': 3.62,
                'odds_x': 3.46,
                'odds_2': 2.01,
                'game_date': datetime.datetime(2024, 2, 23, 12, 45),
                'score_stage': None,
                'score_stage_short': None,
                'stage_name': 'Main',
                'score_halves': [],
                'shooters': [],
                'round_name': '1/16-finals - 1st leg',
                'round_number': None,
                'is_fixture': 1,
                'download_date': datetime.datetime(year=2021, month=1, day=1),
                'save_date': None,
            },
        ]

        pars_match.extend(pars_match_fix)

        ls = LoadSave(
            root_url='https://www.betexplorer.com',
            root_dir=settings.DOWNLOAD_TEST_DIRECTORY,
        )

        ls.load_net = False
        res = await get_results_fixtures(ls, '/football/england/fa-cup/', SportType.FOOTBALL, championship_id, False)
        assert not DeepDiff(pars, res['stages'])
        assert not DeepDiff(pars_match, res['matches'], exclude_paths=[
            "root[0]['save_date']", "root[0]['download_date']",
            "root[1]['save_date']", "root[1]['download_date']",
            "root[2]['save_date']", "root[2]['download_date']",
            "root[0]['home_team']['download_date']",
            "root[0]['home_team']['save_date']",
            "root[0]['away_team']['download_date']",
            "root[0]['away_team']['save_date']",
            "root[1]['home_team']['download_date']",
            "root[1]['home_team']['save_date']",
            "root[1]['away_team']['download_date']",
            "root[1]['away_team']['save_date']",
            "root[2]['home_team']['download_date']",
            "root[2]['home_team']['save_date']",
            "root[2]['away_team']['download_date']",
            "root[2]['away_team']['save_date']",
            ])
