from typing import Any

from src import player
from src.active import entities

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
        tuple[player.Nickname, entities.SettlementType, entities.Coordinate]
    ],
) -> None:
    expected_buildings = []
    for owner, t, (q, r, d) in expected:
        building = {
            "owner": owner,
            "location": {"hex_coord": {"q": q, "r": r}, "direction": d},
            "type": t,
        }
        expected_buildings.append(building)

    def key(x: dict[str, Any]) -> tuple[str, int, int, int]:
        return (
            x["owner"],
            x["location"]["hex_coord"]["q"],
            x["location"]["hex_coord"]["r"],
            x["location"]["direction"],
        )

    assert sorted(buildings, key=key) == sorted(expected_buildings, key=key)


def assert_paths(
    buildings: list[dict[str, Any]],
    expected: list[tuple[player.Nickname, entities.Coordinate]],
) -> None:
    expected_buildings = []
    for owner, (q, r, d) in expected:
        building = {
            "owner": owner,
            "location": {"hex_coord": {"q": q, "r": r}, "direction": d},
        }
        expected_buildings.append(building)

    def key(x: dict[str, Any]) -> tuple[str, int, int]:
        return (
            x["owner"],
            x["location"]["hex_coord"]["q"],
            x["location"]["hex_coord"]["r"],
        )

    assert sorted(buildings, key=key) == sorted(expected_buildings, key=key)
