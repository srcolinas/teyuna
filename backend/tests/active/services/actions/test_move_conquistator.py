import collections
import random
from typing import Any

import pytest

from src.active import entities
from src.active.services import actions


def test_moves_conquistator_to_target_hex(multi_hex_game: entities.ActiveGame) -> None:
    target = multi_hex_game.map[1]
    actions.move_conquistator(
        multi_hex_game, multi_hex_game.active_player, q=target.q, r=target.r
    )
    assert multi_hex_game.conquistator_location == target


def test_steals_one_random_resource_from_victim(
    multi_hex_game: entities.ActiveGame,
) -> None:
    active = multi_hex_game.active_player
    victim = multi_hex_game.turn_order[1]
    target = multi_hex_game.map[1]
    vertex = entities.canonical_vertex(target.q, target.r, 0)
    multi_hex_game.players[victim].settlements[vertex] = entities.SettlementType.TERRACE
    multi_hex_game.players[victim].resources = collections.Counter(
        {
            entities.ResourceCard.GOLD: 1,
            entities.ResourceCard.STONE: 1,
        }
    )
    multi_hex_game.players[active].resources = collections.Counter()

    actions.move_conquistator(
        multi_hex_game,
        active,
        q=target.q,
        r=target.r,
        from_player=victim,
        rnd=_FixedChoiceRandom(0),
    )

    assert multi_hex_game.conquistator_location == target
    assert multi_hex_game.players[victim].resources[entities.ResourceCard.GOLD] == 0
    assert multi_hex_game.players[victim].resources[entities.ResourceCard.STONE] == 1
    assert multi_hex_game.players[active].resources[entities.ResourceCard.GOLD] == 1


def test_no_steal_when_from_player_is_none(
    multi_hex_game: entities.ActiveGame,
) -> None:
    active = multi_hex_game.active_player
    other = multi_hex_game.turn_order[1]
    target = multi_hex_game.map[1]
    multi_hex_game.players[other].resources = collections.Counter(
        {entities.ResourceCard.GOLD: 3}
    )
    multi_hex_game.players[active].resources = collections.Counter()

    actions.move_conquistator(multi_hex_game, active, q=target.q, r=target.r)

    assert multi_hex_game.players[other].resources[entities.ResourceCard.GOLD] == 3
    assert sum(multi_hex_game.players[active].resources.values()) == 0


def test_rejects_hex_not_on_map(multi_hex_game: entities.ActiveGame) -> None:
    with pytest.raises(actions.InvalidConquistatorLocation):
        actions.move_conquistator(
            multi_hex_game, multi_hex_game.active_player, q=99, r=99
        )


def test_rejects_current_hex(multi_hex_game: entities.ActiveGame) -> None:
    current = multi_hex_game.conquistator_location
    with pytest.raises(actions.InvalidConquistatorLocation):
        actions.move_conquistator(
            multi_hex_game, multi_hex_game.active_player, q=current.q, r=current.r
        )


def test_rejects_steal_without_settlement_on_hex(
    multi_hex_game: entities.ActiveGame,
) -> None:
    victim = multi_hex_game.turn_order[1]
    target = multi_hex_game.map[1]
    with pytest.raises(actions.InvalidStealTarget):
        actions.move_conquistator(
            multi_hex_game,
            multi_hex_game.active_player,
            q=target.q,
            r=target.r,
            from_player=victim,
        )


def test_empty_victim_hand_moves_without_transfer(
    multi_hex_game: entities.ActiveGame,
) -> None:
    active = multi_hex_game.active_player
    victim = multi_hex_game.turn_order[1]
    target = multi_hex_game.map[1]
    vertex = entities.canonical_vertex(target.q, target.r, 0)
    multi_hex_game.players[victim].settlements[vertex] = (
        entities.SettlementType.GREAT_TERRACE
    )
    multi_hex_game.players[victim].resources = collections.Counter()
    multi_hex_game.players[active].resources = collections.Counter()

    actions.move_conquistator(
        multi_hex_game,
        active,
        q=target.q,
        r=target.r,
        from_player=victim,
    )

    assert multi_hex_game.conquistator_location == target
    assert sum(multi_hex_game.players[active].resources.values()) == 0
    assert sum(multi_hex_game.players[victim].resources.values()) == 0


def test_move_conquistator_randomly_excludes_current(
    multi_hex_game: entities.ActiveGame,
) -> None:
    current = multi_hex_game.conquistator_location
    other = multi_hex_game.map[1]
    actions.move_conquistator_randomly(multi_hex_game, rnd=_FixedChoiceRandom(0))
    assert multi_hex_game.conquistator_location == other
    assert multi_hex_game.conquistator_location != current


@pytest.fixture
def multi_hex_game(game: entities.ActiveGame) -> entities.ActiveGame:
    jungle = entities.Hex(q=1, r=0, type=entities.HexType.JUNGLE, number=6)
    desert = entities.Hex(q=0, r=1, type=entities.HexType.DESERT, number=0)
    game.map = (game.map[0], jungle, desert)
    game.conquistator_location = game.map[0]
    return game


class _FixedChoiceRandom(random.Random):
    def __init__(self, index: int) -> None:
        super().__init__()
        self._index = index

    def choice(self, seq: Any) -> Any:
        return seq[self._index]
