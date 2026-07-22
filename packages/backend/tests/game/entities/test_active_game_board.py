import collections
import datetime

import pytest

from src.game import entities
import teyuna_shared


def test_use_vertex_removes_settlement_vertex_from_free(
    game: entities.Game,
) -> None:
    target = teyuna_shared.canonical_vertex(0, 0, 0)
    game.use_vertex("player", target, teyuna_shared.SettlementType.TERRACE)

    assert target not in game.free_verticies


def test_use_vertex_assigns_to_player(
    game: entities.Game,
) -> None:
    target = teyuna_shared.canonical_vertex(0, 0, 0)
    game.use_vertex("player", target, teyuna_shared.SettlementType.TERRACE)
    assert (
        game.players["player"].settlements[target]
        is teyuna_shared.SettlementType.TERRACE
    )


def test_use_vertex_restricts_adjacent_vertices(
    game: entities.Game,
) -> None:
    target = teyuna_shared.canonical_vertex(0, 0, 0)
    game.use_vertex("player", target, teyuna_shared.SettlementType.TERRACE)

    assert game.restricted_verticies == {
        teyuna_shared.canonical_vertex(0, -1, 1),
        teyuna_shared.canonical_vertex(0, 0, 5),
        teyuna_shared.canonical_vertex(0, 0, 1),
    }


def test_use_vertex_keeps_adjacent_vertices_in_free(
    game: entities.Game,
) -> None:
    target = teyuna_shared.canonical_vertex(0, 0, 0)
    game.use_vertex("player", target, teyuna_shared.SettlementType.TERRACE)

    assert game.free_verticies & game.restricted_verticies == game.restricted_verticies


def test_use_edge_assigns_path_and_removes_free_edge(
    game: entities.Game,
) -> None:
    path = next(iter(teyuna_shared.edges_adjacent_to_vertex(0, 0, 0)))

    game.use_edge("player", path)

    assert path not in game.free_edges
    assert path in game.players["player"].paths


def test_use_card_moves_card_from_hand_to_played(
    game: entities.Game,
) -> None:
    game.players["player"].cards[teyuna_shared.WisdomCard.WARRIOR] = 2

    game.use_card("player", teyuna_shared.WisdomCard.WARRIOR)

    assert game.players["player"].cards[teyuna_shared.WisdomCard.WARRIOR] == 1
    assert game.players["player"].played_cards[teyuna_shared.WisdomCard.WARRIOR] == 1


def test_take_resources_moves_amount_between_players(
    two_player_game: entities.Game,
) -> None:
    two_player_game.players["player-a"].resources[teyuna_shared.ResourceCard.WOOD] = 3
    two_player_game.players["player-b"].resources[teyuna_shared.ResourceCard.WOOD] = 1
    amount = collections.Counter({teyuna_shared.ResourceCard.WOOD: 2})

    two_player_game.take_resources("player-a", "player-b", amount)

    assert (
        two_player_game.players["player-a"].resources[teyuna_shared.ResourceCard.WOOD]
        == 1
    )
    assert (
        two_player_game.players["player-b"].resources[teyuna_shared.ResourceCard.WOOD]
        == 3
    )


def test_monopoly_of_resource_takes_all_from_other_players(
    two_player_game: entities.Game,
) -> None:
    active = two_player_game.active_player
    other = next(n for n in two_player_game.turn_order if n != active)
    two_player_game.players[active].resources[teyuna_shared.ResourceCard.GOLD] = 1
    two_player_game.players[other].resources[teyuna_shared.ResourceCard.GOLD] = 4
    two_player_game.players[other].resources[teyuna_shared.ResourceCard.WOOD] = 2

    two_player_game.monopoly_of_resource(teyuna_shared.ResourceCard.GOLD)

    assert (
        two_player_game.players[active].resources[teyuna_shared.ResourceCard.GOLD] == 5
    )
    assert (
        two_player_game.players[other].resources[teyuna_shared.ResourceCard.GOLD] == 0
    )
    assert (
        two_player_game.players[other].resources[teyuna_shared.ResourceCard.WOOD] == 2
    )


def test_take_from_supply_credits_player_and_debits_supply(
    game: entities.Game,
) -> None:
    before_supply = game.resource_supply[teyuna_shared.ResourceCard.STONE]
    amount = collections.Counter(
        {teyuna_shared.ResourceCard.STONE: 1, teyuna_shared.ResourceCard.WOOD: 1}
    )

    game.take_from_supply("player", amount)

    assert game.players["player"].resources[teyuna_shared.ResourceCard.STONE] == 1
    assert game.players["player"].resources[teyuna_shared.ResourceCard.WOOD] == 1
    assert game.resource_supply[teyuna_shared.ResourceCard.STONE] == before_supply - 1
    assert game.resource_supply[teyuna_shared.ResourceCard.WOOD] == before_supply - 1


@pytest.fixture
def game() -> entities.Game:
    mountains = teyuna_shared.MapHex(
        q=0, r=0, type=teyuna_shared.HexType.MOUNTAINS, number=1
    )
    game_ = entities.Game(
        map=(mountains,),
        conquistator_location=teyuna_shared.HexLocation(q=0, r=0),
        players={"player": entities.Player()},
        available_slots=0,
    )
    game_.start(datetime.timedelta(seconds=60))
    return game_


@pytest.fixture
def two_player_game() -> entities.Game:
    mountains = teyuna_shared.MapHex(
        q=0, r=0, type=teyuna_shared.HexType.MOUNTAINS, number=1
    )
    game_ = entities.Game(
        map=(mountains,),
        conquistator_location=teyuna_shared.HexLocation(q=0, r=0),
        players={
            "player-a": entities.Player(),
            "player-b": entities.Player(),
        },
        available_slots=0,
    )
    game_.start(datetime.timedelta(seconds=60))
    return game_


def test_add_player_raises_when_no_slots_available() -> None:
    game = entities.Game(
        map=(),
        players={},
        conquistator_location=teyuna_shared.HexLocation(q=0, r=0),
        available_slots=0,
    )

    with pytest.raises(entities.GameAlreadyFullError):
        game.add_player("new-player")
