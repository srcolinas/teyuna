import collections
import math
from typing import cast

import pytest

from src import active

from .... import utils


def test_active_game_exists_after_all_players_joined(
    repository: active.InMemoryActiveGameRepository,
) -> None:
    game_id = utils.create_game_and_add_players(active_repository=repository)

    game = repository.retrieve(game_id)
    assert game is not None


@pytest.mark.flaky(reruns=3)
def test_turn_order_is_random(repository: active.InMemoryActiveGameRepository) -> None:
    frequency: collections.Counter[tuple[str, ...]] = collections.Counter()
    nicknames = ["srcolinas-1", "srcolinas-2", "srcolinas-3"]
    permutations = math.perm(len(nicknames), len(nicknames))
    trials = 1000 * permutations
    for _ in range(trials):
        game_id = utils.create_game_and_add_players(
            active_repository=repository,
            nicknames=nicknames,
        )
        game = cast(active.entities.ActiveGame, repository.retrieve(game_id))
        frequency.update([game.turn_order])

    expected = pytest.approx(trials // permutations, rel=0.1)
    assert all(v == expected for v in frequency.values()), frequency


def test_conquistator_is_located_in_desert_when_game_starts(
    repository: active.InMemoryActiveGameRepository,
) -> None:
    game_id = utils.create_game_and_add_players(active_repository=repository)
    game = cast(active.entities.ActiveGame, repository.retrieve(game_id))
    deserts = [
        hex.coordinate for hex in game.map if hex.type == active.entities.HexType.DESERT
    ]
    assert game.conquistator_location in deserts


def test_map_has_correct_number_distribution(
    repository: active.InMemoryActiveGameRepository,
) -> None:
    game_id = utils.create_game_and_add_players(active_repository=repository)

    game = cast(active.entities.ActiveGame, repository.retrieve(game_id))
    counts = collections.Counter(hex.number for hex in game.map)
    assert counts == {
        2: 1,
        3: 2,
        4: 2,
        5: 2,
        6: 2,
        7: 1,
        8: 2,
        9: 2,
        10: 2,
        11: 2,
        12: 1,
    }


def test_map_has_correct_resource_quantities(
    repository: active.InMemoryActiveGameRepository,
) -> None:
    game_id = utils.create_game_and_add_players(active_repository=repository)

    game = cast(active.entities.ActiveGame, repository.retrieve(game_id))
    counts = collections.Counter(hex.type for hex in game.map)
    assert counts == {
        active.entities.HexType.MOUNTAINS: 3,
        active.entities.HexType.QUARRIES: 3,
        active.entities.HexType.HIGHLANDS: 4,
        active.entities.HexType.VALLEYS: 4,
        active.entities.HexType.JUNGLE: 4,
        active.entities.HexType.DESERT: 1,
    }


def test_active_game_correctly_initialize_players(
    repository: active.InMemoryActiveGameRepository,
) -> None:
    game_id = utils.create_game_and_add_players(
        active_repository=repository,
        nicknames=[
            "srcolinas-0",
            "srcolinas-1",
            "srcolinas-2",
        ],
    )

    game = cast(active.entities.ActiveGame, repository.retrieve(game_id))
    assert len(game.players) == 3
    for i in range(3):
        assert f"srcolinas-{i}" in game.players
        assert game.players[f"srcolinas-{i}"] == active.entities.Player(
            cards=collections.Counter(),
            played_cards=collections.Counter(),
            resources=collections.Counter(),
            settlements=dict(),
            paths=set(),
        )
