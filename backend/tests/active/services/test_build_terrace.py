import itertools

import pytest

from src.active import entities, services

from ... import utils
from . import helpers


@pytest.mark.parametrize(
    "resources",
    [
        {
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.WOOD: 1,
            entities.ResourceCard.COTTON: 1,
            entities.ResourceCard.MAIZE: 0,
        },
        {
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.WOOD: 1,
            entities.ResourceCard.COTTON: 0,
            entities.ResourceCard.MAIZE: 1,
        },
        {
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.WOOD: 0,
            entities.ResourceCard.COTTON: 1,
            entities.ResourceCard.MAIZE: 1,
        },
        {
            entities.ResourceCard.STONE: 0,
            entities.ResourceCard.WOOD: 1,
            entities.ResourceCard.COTTON: 1,
            entities.ResourceCard.MAIZE: 1,
        },
    ],
)
def test_cannot_build_terrace_with_insufficient_resources(
    resources: dict[entities.ResourceCard, int], game: entities.ActiveGame
) -> None:
    nickname = game.turn_order[0]
    services.add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    helpers.fund_path_purchase(game, nickname, count=2)
    helpers.setup_construction_phase(game)
    services.build_path(game, nickname, q=0, r=0, direction=0)
    services.build_path(game, nickname, q=0, r=0, direction=1)
    game.players[nickname].resources.update(resources)
    with pytest.raises(services.InsufficientResources):
        services.build_terrace(game, nickname, q=0, r=0, direction=2)


def test_terrace_needs_to_be_connected_to_a_path(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    helpers.fund_terrace_purchase(game, nickname)
    helpers.setup_construction_phase(game)
    with pytest.raises(services.InvalidSettlementLocation):
        services.build_terrace(game, nickname, q=0, r=0, direction=0)


def test_terrace_can_be_added_by_player_in_turn(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    services.add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    helpers.fund_path_purchase(game, nickname, count=2)
    helpers.setup_construction_phase(game)
    services.build_path(game, nickname, q=0, r=0, direction=0)
    services.build_path(game, nickname, q=0, r=0, direction=1)
    helpers.fund_terrace_purchase(game, nickname)
    with utils.assert_not_raises(Exception):
        services.build_terrace(game, nickname, q=0, r=0, direction=2)


def test_terrace_cannot_be_added_by_player_not_in_turn(
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[0]
    services.add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    helpers.fund_path_purchase(game, nickname, count=2)
    helpers.setup_construction_phase(game)
    services.build_path(game, nickname, q=0, r=0, direction=0)
    services.build_path(game, nickname, q=0, r=0, direction=1)
    helpers.fund_terrace_purchase(game, nickname)
    game.set_turn_order((game.turn_order[1], game.turn_order[0], game.turn_order[2]))
    with pytest.raises(services.PlayerNotInTurn):
        services.build_terrace(game, nickname, q=0, r=0, direction=2)


def test_can_build_terrace_with_sufficient_resources(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    services.add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    helpers.fund_path_purchase(game, nickname, count=2)
    helpers.setup_construction_phase(game)
    services.build_path(game, nickname, q=0, r=0, direction=0)
    services.build_path(game, nickname, q=0, r=0, direction=1)
    helpers.fund_terrace_purchase(game, nickname)
    with utils.assert_not_raises(services.InsufficientResources):
        services.build_terrace(game, nickname, q=0, r=0, direction=2)


def test_terrace_is_added_to_game_object(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    services.add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    helpers.fund_path_purchase(game, nickname, count=2)
    helpers.setup_construction_phase(game)
    services.build_path(game, nickname, q=0, r=0, direction=0)
    services.build_path(game, nickname, q=0, r=0, direction=1)
    helpers.fund_terrace_purchase(game, nickname)
    services.build_terrace(game, nickname, q=0, r=0, direction=2)
    assert (
        game.players[nickname].settlements[entities.Coordinate(q=0, r=0, d=2)]
        is entities.SettlementType.TERRACE
    )


@pytest.mark.parametrize(
    "valid,invalid",
    list(
        itertools.product(
            [(0, 0, 0)],
            [
                (0, 0, 0),
                (0, 0, 1),
                (0, 0, 5),
                (1, -1, 3),
                (1, -1, 4),
                (1, -1, 5),
                (0, -1, 1),
                (0, -1, 2),
                (0, -1, 3),
            ],
        )
    ),
)
def test_terrace_cannot_be_added_to_restricted_location(
    valid: tuple[int, int, int],
    invalid: tuple[int, int, int],
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[0]
    services.add_initial_terrace(
        game, nickname, q=valid[0], r=valid[1], direction=valid[2]
    )
    helpers.fund_path_purchase(game, nickname, count=3)
    helpers.setup_construction_phase(game)
    services.build_path(game, nickname, q=0, r=0, direction=0)
    services.build_path(game, nickname, q=0, r=0, direction=5)
    services.build_path(game, nickname, q=1, r=-1, direction=4)
    helpers.fund_terrace_purchase(game, nickname)
    with pytest.raises(services.InvalidSettlementLocation):
        services.build_terrace(
            game, nickname, q=invalid[0], r=invalid[1], direction=invalid[2]
        )


def test_resources_are_removed_from_player(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    services.add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    helpers.fund_path_purchase(game, nickname, count=2)
    helpers.setup_construction_phase(game)
    services.build_path(game, nickname, q=0, r=0, direction=0)
    services.build_path(game, nickname, q=0, r=0, direction=1)
    helpers.fund_terrace_purchase(game, nickname)
    services.build_terrace(game, nickname, q=0, r=0, direction=2)
    assert game.players[nickname].resources[entities.ResourceCard.STONE] == 0
    assert game.players[nickname].resources[entities.ResourceCard.WOOD] == 0
    assert game.players[nickname].resources[entities.ResourceCard.COTTON] == 0
    assert game.players[nickname].resources[entities.ResourceCard.MAIZE] == 0


def test_player_not_in_turn_cannot_build_terrace(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    services.add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    helpers.fund_path_purchase(game, nickname, count=2)
    helpers.setup_construction_phase(game)
    services.build_path(game, nickname, q=0, r=0, direction=0)
    services.build_path(game, nickname, q=0, r=0, direction=1)
    helpers.fund_terrace_purchase(game, nickname)
    game.set_turn_order((game.turn_order[1], game.turn_order[0], game.turn_order[2]))
    with pytest.raises(services.PlayerNotInTurn):
        services.build_terrace(game, nickname, q=0, r=0, direction=2)


def test_cannot_build_terrace_if_not_enough_terraces_available(
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[0]
    helpers.fund_terrace_purchase(game, nickname, count=5)
    helpers.fund_path_purchase(game, nickname, count=10)
    services.add_initial_terrace(game, nickname, q=0, r=-2, direction=0)
    helpers.setup_construction_phase(game)
    services.build_path(game, nickname, q=0, r=-2, direction=0)
    services.build_path(game, nickname, q=1, r=-2, direction=5)
    services.build_terrace(game, nickname, q=1, r=-2, direction=0)
    services.build_path(game, nickname, q=1, r=-2, direction=0)
    services.build_path(game, nickname, q=2, r=-2, direction=5)
    services.build_terrace(game, nickname, q=2, r=-2, direction=0)
    services.build_path(game, nickname, q=2, r=-2, direction=0)
    services.build_path(game, nickname, q=2, r=-2, direction=1)
    services.build_terrace(game, nickname, q=2, r=-2, direction=2)
    services.build_path(game, nickname, q=2, r=-1, direction=0)
    services.build_path(game, nickname, q=2, r=-1, direction=1)
    services.build_terrace(game, nickname, q=2, r=-1, direction=2)
    services.build_path(game, nickname, q=2, r=0, direction=0)
    services.build_path(game, nickname, q=2, r=0, direction=1)
    with pytest.raises(services.InsufficientResources):
        services.build_terrace(game, nickname, q=2, r=0, direction=2)


@pytest.mark.parametrize(
    "phase",
    [
        entities.GamePhase.INITIAL,
        entities.GamePhase.FINISHED,
    ],
)
def test_cannot_build_terrace_if_game_is_not_in_main_phase(
    phase: entities.GamePhase,
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[0]
    services.add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    helpers.fund_path_purchase(game, nickname, count=2)
    helpers.setup_construction_phase(game)
    services.build_path(game, nickname, q=0, r=0, direction=0)
    services.build_path(game, nickname, q=0, r=0, direction=1)
    helpers.fund_terrace_purchase(game, nickname)
    game.set_game_phase(phase)
    with pytest.raises(services.InvalidGamePhase):
        services.build_terrace(game, nickname, q=0, r=0, direction=2)


@pytest.mark.parametrize(
    "turn_phase",
    [
        entities.TurnPhase.PRODUCTION,
        entities.TurnPhase.TRADE,
    ],
)
def test_cannot_build_terrace_if_turn_is_not_in_construction_phase(
    turn_phase: entities.TurnPhase,
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[0]
    services.add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    helpers.fund_path_purchase(game, nickname, count=2)
    helpers.setup_construction_phase(game)
    services.build_path(game, nickname, q=0, r=0, direction=0)
    services.build_path(game, nickname, q=0, r=0, direction=1)
    helpers.fund_terrace_purchase(game, nickname)
    game.set_turn_phase(turn_phase)
    with pytest.raises(services.InvalidGamePhase):
        services.build_terrace(game, nickname, q=0, r=0, direction=2)
