import pytest


from src.active import entities, services

from ... import utils
from . import helpers


def test_cannot_build_great_terrace_if_terrace_not_placed_before(
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[0]
    services.add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    helpers.fund_path_purchase(game, nickname, count=2)
    helpers.setup_construction_phase(game)
    services.build_path(game, nickname, q=0, r=0, direction=0)
    services.build_path(game, nickname, q=0, r=0, direction=1)
    game.players[nickname].resources.update(
        {
            entities.ResourceCard.GOLD: 3,
            entities.ResourceCard.MAIZE: 2,
        }
    )
    with pytest.raises(
        services.InvalidSettlementLocation,
        match="You must first build a terrace at specified location.",
    ):
        services.build_great_terrace(game, nickname, q=0, r=0, direction=2)


def test_can_build_terrace_with_sufficient_resources(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    services.add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    helpers.fund_path_purchase(game, nickname, count=2)
    helpers.setup_construction_phase(game)
    services.build_path(game, nickname, q=0, r=0, direction=0)
    services.build_path(game, nickname, q=0, r=0, direction=1)
    game.players[nickname].resources.update(
        {
            entities.ResourceCard.GOLD: 3,
            entities.ResourceCard.MAIZE: 2,
        }
    )
    with utils.assert_not_raises(services.InsufficientResources):
        services.build_great_terrace(game, nickname, q=0, r=0, direction=0)


@pytest.mark.parametrize(
    "resources",
    [
        {
            entities.ResourceCard.GOLD: 3,
            entities.ResourceCard.MAIZE: 1,
        },
        {
            entities.ResourceCard.GOLD: 2,
            entities.ResourceCard.MAIZE: 2,
        },
    ],
)
def test_cannot_build_great_terrace_with_insufficient_resources(
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
        services.build_great_terrace(game, nickname, q=0, r=0, direction=0)


def test_great_terrace_is_added_to_game_object(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    services.add_initial_terrace(game, nickname, q=0, r=0, direction=2)
    helpers.fund_path_purchase(game, nickname, count=2)
    helpers.setup_construction_phase(game)
    services.build_path(game, nickname, q=0, r=0, direction=1)
    services.build_path(game, nickname, q=0, r=0, direction=0)
    game.players[nickname].resources.update(
        {
            entities.ResourceCard.GOLD: 3,
            entities.ResourceCard.MAIZE: 2,
        }
    )
    services.build_great_terrace(game, nickname, q=0, r=0, direction=2)
    assert (
        game.players[nickname].settlements[entities.Coordinate(q=0, r=0, d=2)]
        is entities.SettlementType.GREAT_TERRACE
    )


def test_resources_are_removed_from_player(game: entities.ActiveGame) -> None:
    nickname = game.turn_order[0]
    services.add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    helpers.fund_path_purchase(game, nickname, count=2)
    helpers.setup_construction_phase(game)
    services.build_path(game, nickname, q=0, r=0, direction=0)
    services.build_path(game, nickname, q=0, r=0, direction=1)
    game.players[nickname].resources.update(
        {
            entities.ResourceCard.GOLD: 3,
            entities.ResourceCard.MAIZE: 2,
        }
    )
    services.build_great_terrace(game, nickname, q=0, r=0, direction=0)
    assert game.players[nickname].resources[entities.ResourceCard.GOLD] == 0
    assert game.players[nickname].resources[entities.ResourceCard.MAIZE] == 0


def test_player_not_in_turn_cannot_build_great_terrace(
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[0]
    services.add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    helpers.fund_path_purchase(game, nickname, count=2)
    helpers.setup_construction_phase(game)
    services.build_path(game, nickname, q=0, r=0, direction=0)
    services.build_path(game, nickname, q=0, r=0, direction=1)
    game.players[nickname].resources.update(
        {
            entities.ResourceCard.GOLD: 3,
            entities.ResourceCard.MAIZE: 2,
        }
    )
    game.set_turn_order((game.turn_order[1], game.turn_order[0], game.turn_order[2]))
    with pytest.raises(services.PlayerNotInTurn):
        services.build_great_terrace(game, nickname, q=0, r=0, direction=0)


def test_cannot_build_great_terrace_if_not_enough_great_terraces_available(
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[0]
    game.players[nickname].resources.update(
        {
            entities.ResourceCard.GOLD: 300,
            entities.ResourceCard.MAIZE: 200,
            entities.ResourceCard.STONE: 20,
            entities.ResourceCard.WOOD: 20,
            entities.ResourceCard.COTTON: 10,
        }
    )
    services.add_initial_terrace(game, nickname, q=0, r=-2, direction=0)
    helpers.setup_construction_phase(game)
    services.build_great_terrace(game, nickname, q=0, r=-2, direction=0)
    services.build_path(game, nickname, q=0, r=-2, direction=0)
    services.build_path(game, nickname, q=1, r=-2, direction=5)
    services.build_terrace(game, nickname, q=1, r=-2, direction=0)
    services.build_great_terrace(game, nickname, q=1, r=-2, direction=0)
    services.build_path(game, nickname, q=1, r=-2, direction=0)
    services.build_path(game, nickname, q=2, r=-2, direction=5)
    services.build_terrace(game, nickname, q=2, r=-2, direction=0)
    services.build_great_terrace(game, nickname, q=2, r=-2, direction=0)
    services.build_path(game, nickname, q=2, r=-2, direction=0)
    services.build_path(game, nickname, q=2, r=-2, direction=1)
    services.build_terrace(game, nickname, q=2, r=-2, direction=2)
    services.build_great_terrace(game, nickname, q=2, r=-2, direction=2)
    services.build_path(game, nickname, q=2, r=-1, direction=0)
    services.build_path(game, nickname, q=2, r=-1, direction=1)
    services.build_terrace(game, nickname, q=2, r=-1, direction=2)
    with pytest.raises(services.InsufficientResources):
        services.build_great_terrace(game, nickname, q=2, r=-1, direction=2)


@pytest.mark.parametrize(
    "phase",
    [
        entities.GamePhase.INITIAL,
        entities.GamePhase.FINISHED,
    ],
)
def test_cannot_build_great_terrace_if_game_is_not_in_main_phase(
    phase: entities.GamePhase,
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[0]
    services.add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    helpers.fund_path_purchase(game, nickname, count=2)
    helpers.setup_construction_phase(game)
    services.build_path(game, nickname, q=0, r=0, direction=0)
    services.build_path(game, nickname, q=0, r=0, direction=1)
    game.players[nickname].resources.update(
        {
            entities.ResourceCard.GOLD: 3,
            entities.ResourceCard.MAIZE: 2,
        }
    )
    game.set_game_phase(phase)
    with pytest.raises(services.InvalidGamePhase):
        services.build_great_terrace(game, nickname, q=0, r=0, direction=0)


@pytest.mark.parametrize(
    "turn_phase",
    [
        entities.TurnPhase.PRODUCTION,
        entities.TurnPhase.TRADE,
    ],
)
def test_cannot_build_great_terrace_if_turn_is_not_in_construction_phase(
    turn_phase: entities.TurnPhase,
    game: entities.ActiveGame,
) -> None:
    nickname = game.turn_order[0]
    services.add_initial_terrace(game, nickname, q=0, r=0, direction=0)
    helpers.fund_path_purchase(game, nickname, count=2)
    helpers.setup_construction_phase(game)
    services.build_path(game, nickname, q=0, r=0, direction=0)
    services.build_path(game, nickname, q=0, r=0, direction=1)
    game.players[nickname].resources.update(
        {
            entities.ResourceCard.GOLD: 3,
            entities.ResourceCard.MAIZE: 2,
        }
    )
    game.set_turn_phase(turn_phase)
    with pytest.raises(services.InvalidGamePhase):
        services.build_great_terrace(game, nickname, q=0, r=0, direction=0)
