import itertools

import pytest

from src.active import entities, services

from ... import utils
from . import helpers


@pytest.mark.parametrize(
    "resources",
    [
        {
            entities.ResourceCard.STONE: 0,
            entities.ResourceCard.WOOD: 1,
        },
        {
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.WOOD: 0,
        },
    ],
)
def test_cannot_build_path_with_insufficient_resources(
    resources: dict[entities.ResourceCard, int], game: entities.ActiveGame
) -> None:
    nickname = game.turn_order[0]
    services.add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    game.players[nickname].resources.update(resources)
    helpers.setup_construction_phase(game)
    with pytest.raises(services.InsufficientResources):
        services.build_path(game, nickname, q=0, r=0, direction=1)


def test_can_build_path_with_sufficient_resources(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    services.add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    helpers.fund_path_purchase(game, nickname)
    helpers.setup_construction_phase(game)
    with utils.assert_not_raises(services.InsufficientResources):
        services.build_path(game, nickname, q=0, r=0, direction=0)


def test_path_can_be_bought_by_player_in_turn(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    services.add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    helpers.fund_path_purchase(game, nickname)
    helpers.setup_construction_phase(game)
    with utils.assert_not_raises(Exception):
        services.build_path(game, nickname, q=0, r=0, direction=0)


def test_path_is_added_to_game_object(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    services.add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    helpers.fund_path_purchase(game, nickname)
    helpers.setup_construction_phase(game)
    services.build_path(game, nickname, q=0, r=0, direction=0)
    assert game.players[nickname].paths == {entities.Coordinate(q=0, r=0, d=0)}


def test_resources_are_removed_from_player(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    services.add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    helpers.fund_path_purchase(game, nickname)
    helpers.setup_construction_phase(game)
    services.build_path(game, nickname, q=0, r=0, direction=0)
    assert game.players[nickname].resources[entities.ResourceCard.STONE] == 0
    assert game.players[nickname].resources[entities.ResourceCard.WOOD] == 0


def test_player_not_in_turn_cannot_build_path(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    services.add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    helpers.fund_path_purchase(game, nickname)
    helpers.setup_construction_phase(game)
    game.set_turn_order((game.turn_order[1], game.turn_order[0], game.turn_order[2]))
    with pytest.raises(services.PlayerNotInTurn):
        services.build_path(game, nickname, q=0, r=0, direction=0)


@pytest.mark.parametrize(
    "valid,invalid",
    list(
        itertools.product(
            [(0, 0, 0)],
            [
                (0, 0, 0),
                (1, -1, 3),
            ],
        )
    ),
)
def test_path_cannot_be_bought_at_occupied_location(
    valid: tuple[int, int, int],
    invalid: tuple[int, int, int],
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[0]
    q, r, d = valid
    services.add_initial_terrace(game, nickname, q=q, r=r, direction=d)
    helpers.fund_path_purchase(game, nickname, count=2)
    helpers.setup_construction_phase(game)
    services.build_path(game, nickname, q=q, r=r, direction=d)
    nickname = game.turn_order[0]
    with pytest.raises(services.InvalidPathLocation):
        q, r, d = invalid
        services.build_path(game, nickname, q=q, r=r, direction=d)


def test_path_can_be_bought_next_to_path(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    services.add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    helpers.fund_path_purchase(game, nickname, count=2)
    helpers.setup_construction_phase(game)
    services.build_path(game, nickname, q=0, r=0, direction=0)
    with utils.assert_not_raises(Exception):
        services.build_path(game, nickname, q=0, r=0, direction=1)


def test_path_cannot_be_bought_without_path_or_terrace_next_to_it(
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[0]
    helpers.fund_path_purchase(game, nickname)
    helpers.setup_construction_phase(game)
    with pytest.raises(services.InvalidPathLocation):
        services.build_path(game, nickname, q=0, r=0, direction=0)


def test_path_cannot_be_bought_if_blocked_by_another_players_terrace(
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[0]
    services.add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    game.set_turn_order((game.turn_order[1], game.turn_order[0], game.turn_order[2]))
    nickname = game.turn_order[0]
    services.add_initial_terrace(game, nickname, q=0, r=0, direction=2)
    helpers.fund_path_purchase(game, nickname, count=3)
    helpers.setup_construction_phase(game)
    services.build_path(game, nickname, q=0, r=0, direction=1)
    services.build_path(game, nickname, q=0, r=0, direction=0)
    with pytest.raises(services.InvalidPathLocation):
        services.build_path(game, nickname, q=0, r=0, direction=5)


def test_cannot_build_path_if_not_enough_paths_available(
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[0]
    services.add_initial_terrace(game, nickname, q=0, r=-2, direction=0)
    helpers.fund_path_purchase(game, nickname, count=15)
    helpers.setup_construction_phase(game)
    services.build_path(game, nickname, q=0, r=-2, direction=0)
    services.build_path(game, nickname, q=1, r=-2, direction=5)
    services.build_path(game, nickname, q=1, r=-2, direction=0)
    services.build_path(game, nickname, q=2, r=-2, direction=5)
    services.build_path(game, nickname, q=2, r=-2, direction=0)
    services.build_path(game, nickname, q=2, r=-2, direction=1)
    services.build_path(game, nickname, q=2, r=-1, direction=0)
    services.build_path(game, nickname, q=2, r=-1, direction=1)
    services.build_path(game, nickname, q=2, r=0, direction=0)
    services.build_path(game, nickname, q=2, r=0, direction=1)
    services.build_path(game, nickname, q=2, r=0, direction=2)
    services.build_path(game, nickname, q=1, r=1, direction=1)
    services.build_path(game, nickname, q=1, r=1, direction=2)
    services.build_path(game, nickname, q=0, r=2, direction=1)
    services.build_path(game, nickname, q=0, r=2, direction=2)
    with pytest.raises(services.InsufficientResources):
        services.build_path(game, nickname, q=2, r=0, direction=2)


@pytest.mark.parametrize(
    "phase",
    [
        entities.GamePhase.INITIAL,
        entities.GamePhase.FINISHED,
    ],
)
def test_cannot_build_path_if_game_is_not_in_main_phase(
    phase: entities.GamePhase,
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[0]
    services.add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    helpers.fund_path_purchase(game, nickname)
    game.set_game_phase(phase)
    game.set_turn_phase(entities.TurnPhase.CONSTRUCTION)
    with pytest.raises(services.InvalidGamePhase):
        services.build_path(game, nickname, q=0, r=0, direction=0)


@pytest.mark.parametrize(
    "turn_phase",
    [
        entities.TurnPhase.PRODUCTION,
        entities.TurnPhase.TRADE,
    ],
)
def test_cannot_build_path_if_turn_is_not_in_construction_phase(
    turn_phase: entities.TurnPhase,
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[0]
    services.add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    helpers.fund_path_purchase(game, nickname)
    game.set_game_phase(entities.GamePhase.MAIN)
    game.set_turn_phase(turn_phase)
    with pytest.raises(services.InvalidGamePhase):
        services.build_path(game, nickname, q=0, r=0, direction=0)
