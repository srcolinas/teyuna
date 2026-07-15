import random
from typing import Any

from src.active import entities
from src.active.services import actions


def test_adds_terrace_and_path_when_below_expected_terrace_count(
    game: entities.ActiveGame,
) -> None:
    nickname = game.active_player
    terrace = entities.canonical_vertex(0, 0, 0)
    path = entities.canonical_edge(0, 0, 0)
    game.free_verticies = {terrace}
    game.free_edges = {path}

    actions.maybe_add_random_placements(
        game, expected_count=1, rnd=_FixedChoiceRandom(0)
    )

    player_state = game.players[nickname]
    assert player_state.settlements[terrace] is entities.SettlementType.TERRACE
    assert path in player_state.paths


def test_adds_path_next_to_lonely_terrace_when_paths_below_expected_count(
    game: entities.ActiveGame,
) -> None:
    nickname = game.active_player
    terrace = entities.canonical_vertex(0, 0, 0)
    actions.add_free_terrace(game, nickname, q=0, r=0, direction=0)

    actions.maybe_add_random_placements(
        game, expected_count=1, rnd=_FixedChoiceRandom(0)
    )

    player_state = game.players[nickname]
    assert player_state.settlements.count(entities.SettlementType.TERRACE) == 1
    assert len(player_state.paths) == 1
    path = next(iter(player_state.paths))
    assert terrace in (
        entities.canonical_vertex(path.q, path.r, path.d),
        entities.canonical_vertex(path.q, path.r, (path.d + 1) % 6),
    )


def test_no_op_when_already_at_expected_counts(game: entities.ActiveGame) -> None:
    nickname = game.active_player
    actions.add_free_terrace(game, nickname, q=0, r=0, direction=0)
    actions.add_free_path(game, nickname, q=0, r=0, direction=0)

    actions.maybe_add_random_placements(
        game, expected_count=1, rnd=_FixedChoiceRandom(0)
    )

    player_state = game.players[nickname]
    assert player_state.settlements.count(entities.SettlementType.TERRACE) == 1
    assert len(player_state.paths) == 1


def test_selection_is_deterministic_with_fixed_random(
    game: entities.ActiveGame,
) -> None:
    nickname = game.active_player
    chosen = entities.canonical_vertex(0, 0, 0)
    other = entities.canonical_vertex(1, 0, 0)
    path = entities.canonical_edge(0, 0, 0)
    game.free_verticies = {chosen, other}
    game.free_edges = {
        path,
        entities.canonical_edge(1, 0, 0),
    }

    actions.maybe_add_random_placements(
        game, expected_count=1, rnd=_ReturnChoiceRandom(chosen, path)
    )

    player_state = game.players[nickname]
    assert chosen in player_state.settlements
    assert other not in player_state.settlements
    assert path in player_state.paths


class _FixedChoiceRandom(random.Random):
    def __init__(self, index: int) -> None:
        super().__init__()
        self._index = index

    def choice(self, seq: Any) -> Any:
        return seq[self._index]


class _ReturnChoiceRandom(random.Random):
    def __init__(self, *values: Any) -> None:
        super().__init__()
        self._values = iter(values)

    def choice(self, seq: Any) -> Any:
        value = next(self._values)
        assert value in seq
        return value
