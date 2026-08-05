from typing import Any

from src.game import player
import teyuna_core

type Json = dict[str, Any]


def assert_players_attributes_equal(players: list[Json], expected: Json) -> None:
    for player_ in players:
        for k, v in expected.items():
            assert player_[k] == v


def assert_players_attributes(
    players: list[Json], expected: dict[player.Nickname, Json]
) -> None:
    for player_ in players:
        nickname = player_["nickname"]
        for key, value in expected[nickname].items():
            assert player_[key] == value


def assert_settlements(
    buildings: list[dict[str, Any]],
    expected: list[
        tuple[player.Nickname, teyuna_core.SettlementType, teyuna_core.Coordinate]
    ],
) -> None:
    expected_buildings = []
    for owner, t, location in expected:
        building = {
            "owner": owner,
            "location": {"q": location.q, "r": location.r, "d": location.d},
            "type": t,
        }
        expected_buildings.append(building)

    def key(x: dict[str, Any]) -> tuple[str, int, int, int]:
        return (
            x["owner"],
            x["location"]["q"],
            x["location"]["r"],
            x["location"]["d"],
        )

    assert sorted(buildings, key=key) == sorted(expected_buildings, key=key)


def assert_paths(
    buildings: list[dict[str, Any]],
    expected: list[tuple[player.Nickname, teyuna_core.Coordinate]],
) -> None:
    expected_buildings = []
    for owner, location in expected:
        building = {
            "owner": owner,
            "location": {"q": location.q, "r": location.r, "d": location.d},
        }
        expected_buildings.append(building)

    def key(x: dict[str, Any]) -> tuple[str, int, int]:
        return (
            x["owner"],
            x["location"]["q"],
            x["location"]["r"],
        )

    assert sorted(buildings, key=key) == sorted(expected_buildings, key=key)


def assert_num_resources(
    players: list[dict[str, Any]],
    expected: list[tuple[player.Nickname, int]],
) -> None:
    real = ((player["nickname"], player["num_resources"]) for player in players)
    assert sorted(real) == sorted(expected)


def count_adjacent_producing_hexes(
    game_map: list[dict[str, Any]], terrace: teyuna_core.Coordinate
) -> int:
    """Count non-desert hexes adjacent to a terrace (second-placement grants)."""
    types_by_hex = {
        (tile["coordinate"]["q"], tile["coordinate"]["r"]): tile["type"]
        for tile in game_map
    }
    return sum(
        1
        for loc in teyuna_core.hex_locations_at_vertex(terrace.q, terrace.r, terrace.d)
        if types_by_hex.get((loc.q, loc.r)) not in (None, teyuna_core.HexType.DESERT)
    )
