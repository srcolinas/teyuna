import collections
import datetime

import pytest

from src.game import entities
import teyuna_core


def test_use_vertex_removes_settlement_vertex_from_free(
    game: entities.Game,
) -> None:
    target = teyuna_core.canonical_vertex(0, 0, 0)
    game.use_vertex("player", target, teyuna_core.SettlementType.TERRACE)

    assert target not in game.free_verticies


def test_use_vertex_assigns_to_player(
    game: entities.Game,
) -> None:
    target = teyuna_core.canonical_vertex(0, 0, 0)
    game.use_vertex("player", target, teyuna_core.SettlementType.TERRACE)
    assert (
        game.players["player"].settlements[target] is teyuna_core.SettlementType.TERRACE
    )


def test_use_vertex_restricts_adjacent_vertices(
    game: entities.Game,
) -> None:
    target = teyuna_core.canonical_vertex(0, 0, 0)
    game.use_vertex("player", target, teyuna_core.SettlementType.TERRACE)

    assert game.restricted_verticies == {
        teyuna_core.canonical_vertex(0, -1, 1),
        teyuna_core.canonical_vertex(0, 0, 5),
        teyuna_core.canonical_vertex(0, 0, 1),
    }


def test_use_vertex_keeps_adjacent_vertices_in_free(
    game: entities.Game,
) -> None:
    target = teyuna_core.canonical_vertex(0, 0, 0)
    game.use_vertex("player", target, teyuna_core.SettlementType.TERRACE)

    assert game.free_verticies & game.restricted_verticies == game.restricted_verticies


def test_use_edge_assigns_path_and_removes_free_edge(
    game: entities.Game,
) -> None:
    path = next(iter(teyuna_core.edges_adjacent_to_vertex(0, 0, 0)))

    game.use_edge("player", path)

    assert path not in game.free_edges
    assert path in game.players["player"].paths


def test_use_card_moves_card_from_hand_to_played(
    game: entities.Game,
) -> None:
    game.players["player"].cards[teyuna_core.WisdomCard.WARRIOR] = 2

    game.use_card("player", teyuna_core.WisdomCard.WARRIOR)

    assert game.players["player"].cards[teyuna_core.WisdomCard.WARRIOR] == 1
    assert game.players["player"].played_cards[teyuna_core.WisdomCard.WARRIOR] == 1


def test_take_resources_moves_amount_between_players(
    two_player_game: entities.Game,
) -> None:
    two_player_game.players["player-a"].resources[teyuna_core.ResourceCard.WOOD] = 3
    two_player_game.players["player-b"].resources[teyuna_core.ResourceCard.WOOD] = 1
    amount = collections.Counter({teyuna_core.ResourceCard.WOOD: 2})

    two_player_game.take_resources("player-a", "player-b", amount)

    assert (
        two_player_game.players["player-a"].resources[teyuna_core.ResourceCard.WOOD]
        == 1
    )
    assert (
        two_player_game.players["player-b"].resources[teyuna_core.ResourceCard.WOOD]
        == 3
    )


def test_monopoly_of_resource_takes_all_from_other_players(
    two_player_game: entities.Game,
) -> None:
    active = two_player_game.active_player
    other = next(n for n in two_player_game.turn_order if n != active)
    two_player_game.players[active].resources[teyuna_core.ResourceCard.GOLD] = 1
    two_player_game.players[other].resources[teyuna_core.ResourceCard.GOLD] = 4
    two_player_game.players[other].resources[teyuna_core.ResourceCard.WOOD] = 2

    two_player_game.monopoly_of_resource(teyuna_core.ResourceCard.GOLD)

    assert two_player_game.players[active].resources[teyuna_core.ResourceCard.GOLD] == 5
    assert two_player_game.players[other].resources[teyuna_core.ResourceCard.GOLD] == 0
    assert two_player_game.players[other].resources[teyuna_core.ResourceCard.WOOD] == 2


def test_take_from_supply_credits_player_and_debits_supply(
    game: entities.Game,
) -> None:
    before_supply = game.resource_supply[teyuna_core.ResourceCard.STONE]
    amount = collections.Counter(
        {teyuna_core.ResourceCard.STONE: 1, teyuna_core.ResourceCard.WOOD: 1}
    )

    game.take_from_supply("player", amount)

    assert game.players["player"].resources[teyuna_core.ResourceCard.STONE] == 1
    assert game.players["player"].resources[teyuna_core.ResourceCard.WOOD] == 1
    assert game.resource_supply[teyuna_core.ResourceCard.STONE] == before_supply - 1
    assert game.resource_supply[teyuna_core.ResourceCard.WOOD] == before_supply - 1


@pytest.fixture
def game() -> entities.Game:
    mountains = teyuna_core.MapHex(
        q=0, r=0, type=teyuna_core.HexType.MOUNTAINS, number=1
    )
    game_ = entities.Game(
        map=(mountains,),
        conquistator_location=teyuna_core.HexLocation(q=0, r=0),
        players={"player": entities.Player()},
        available_slots=0,
    )
    game_.start(datetime.timedelta(seconds=60))
    return game_


@pytest.fixture
def two_player_game() -> entities.Game:
    mountains = teyuna_core.MapHex(
        q=0, r=0, type=teyuna_core.HexType.MOUNTAINS, number=1
    )
    game_ = entities.Game(
        map=(mountains,),
        conquistator_location=teyuna_core.HexLocation(q=0, r=0),
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
        conquistator_location=teyuna_core.HexLocation(q=0, r=0),
        available_slots=0,
    )

    with pytest.raises(entities.GameAlreadyFullError):
        game.add_player("new-player")


def test_victory_points_calculates_correctly() -> None:
    game = entities.Game(
        map=(),
        players={
            # 2 great terraces (4) + longest road (2) + 1 legacy card (1) = 7
            "player-a": entities.Player(
                settlements=entities.SettlementsCollection(
                    {
                        teyuna_core.canonical_vertex(0, 0, 0): (
                            teyuna_core.SettlementType.GREAT_TERRACE
                        ),
                        teyuna_core.canonical_vertex(1, 0, 0): (
                            teyuna_core.SettlementType.GREAT_TERRACE
                        ),
                    }
                ),
                played_cards=collections.Counter(
                    {teyuna_core.WisdomCard.LEGACY_OF_THE_ELDERS: 1}
                ),
            ),
            # 1 great terrace (2) + 1 terrace (1) + biggest army (2) = 5
            "player-b": entities.Player(
                settlements=entities.SettlementsCollection(
                    {
                        teyuna_core.canonical_vertex(-1, 0, 0): (
                            teyuna_core.SettlementType.GREAT_TERRACE
                        ),
                        teyuna_core.canonical_vertex(2, 0, 0): (
                            teyuna_core.SettlementType.TERRACE
                        ),
                    }
                ),
            ),
        },
        conquistator_location=teyuna_core.HexLocation(q=0, r=0),
        available_slots=0,
        longest_road=("player-a", 5),
        biggest_army=("player-b", 3),
    )
    game.start(datetime.timedelta(seconds=60))
    assert game.victory_points == {"player-a": 7, "player-b": 5}
