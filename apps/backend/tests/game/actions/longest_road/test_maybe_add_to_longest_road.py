from typing import Iterable, Sequence

import pytest

from src.game import actions, entities
import teyuna_core

from . import helpers


def test_first_award_at_five_consecutive_paths(game: entities.Game) -> None:
    builder = game.active_player
    edge = helpers.place_buildings(
        game, builder, edges=[(0, 0, d) for d in range(5)], vertices=[(0, 0, 0)]
    )

    actions.maybe_add_to_longest_road(game, builder, edge=edge)

    assert game.longest_road == (builder, 5)


def test_below_threshold_does_not_award(game: entities.Game) -> None:
    builder = game.active_player
    edge = helpers.place_buildings(
        game, builder, edges=[(0, 0, d) for d in range(4)], vertices=[(0, 0, 0)]
    )

    actions.maybe_add_to_longest_road(game, builder, edge=edge)

    assert game.longest_road == (None, 0)


def test_steal_when_strictly_longer(game: entities.Game) -> None:
    holder = game.turn_order[1]
    stealer = game.active_player
    game.longest_road = (holder, 5)
    edge = helpers.place_buildings(
        game, stealer, edges=[(0, 0, d) for d in range(6)], vertices=[(0, 0, 0)]
    )

    actions.maybe_add_to_longest_road(game, stealer, edge=edge)

    assert game.longest_road == (stealer, 6)


def test_equal_length_does_not_steal(game: entities.Game) -> None:
    holder = game.turn_order[1]
    challenger = game.active_player
    game.longest_road = (holder, 5)
    edge = helpers.place_buildings(
        game, challenger, edges=[(0, 0, d) for d in range(5)], vertices=[(0, 0, 0)]
    )

    actions.maybe_add_to_longest_road(game, challenger, edge=edge)

    assert game.longest_road == (holder, 5)


def test_opponent_settlement_breaks_road(game: entities.Game) -> None:
    builder = game.active_player
    opponent = game.turn_order[1]
    # Linear chain of 6 (not a cycle): longest would be 6 without a break.
    edge = helpers.place_buildings(
        game,
        builder,
        edges=[(0, 0, 0), (0, 0, 1), (0, 0, 2), (0, 0, 3), (0, 0, 4), (-1, 0, 0)],
        vertices=[(0, 0, 0)],
    )
    # Opponent terrace at the midpoint splits into two length-3 segments.
    game.use_vertex(
        opponent,
        teyuna_core.canonical_vertex(0, 0, 3),
        teyuna_core.SettlementType.TERRACE,
    )

    actions.maybe_add_to_longest_road(game, builder, edge=edge)

    # The longest road is unassigned because no player has a road
    # that is longer or equal to 5
    assert game.longest_road == (None, 0)


def test_uses_longest_branch(
    game: entities.Game,
) -> None:
    builder = game.active_player
    # Chain of 4 around the hex plus a side branch at vertex (0, 0, 1).
    # Six edges total, but longest continuous path is 5.
    edge = helpers.place_buildings(
        game,
        builder,
        edges=[(0, 0, 0), (0, 0, 1), (0, 0, 2), (0, 0, 3), (0, 0, 4), (1, -1, 2)],
        vertices=[(0, 0, 0)],
    )

    actions.maybe_add_to_longest_road(game, builder, edge=edge)

    assert game.longest_road == (builder, 5)


def _subsequences[T](iterable: Iterable[T]) -> Iterable[Sequence[T]]:
    seq = []
    for item in iterable:
        seq.append(item)
        yield seq


@pytest.mark.parametrize(
    "tail",
    list(_subsequences([(0, -1, 1), (0, -1, 0), (0, -1, 5), (0, -1, 4), (0, -1, 3)])),
)
@pytest.mark.parametrize("last_added", [(0, 0, 1), (0, -1, 1)])
def test_single_loop_with_tail_branch(
    tail: list[tuple[int, int, int]],
    last_added: tuple[int, int, int],
    game: entities.Game,
) -> None:
    loop = [
        (0, 0, 0),
        (0, 0, 1),
        (0, 0, 2),
        (0, 0, 3),
        (0, 0, 4),
        (0, 0, 5),
    ]
    helpers.place_buildings(
        game,
        game.active_player,
        edges=loop + tail,
        vertices=[(0, 0, 0), (0, 0, 4)],
    )
    actions.maybe_add_to_longest_road(
        game, game.active_player, edge=teyuna_core.canonical_edge(*last_added)
    )

    assert game.longest_road == (game.active_player, len(loop) + len(tail))


def test_when_potential_longest_road_is_blocked_by_opponent_settlement(
    game: entities.Game,
) -> None:
    # GIVEN: the current player has two disconnected roads that would
    # become the longest if they were connected
    builder = game.active_player
    helpers.place_buildings(
        game,
        builder,
        edges=[(0, -1, 0), (0, -1, 1), (0, 0, 0), (0, 0, 2), (0, 0, 3)],
        vertices=[(0, 0, 0), (0, 0, 4)],
    )

    # GIVEN: an opponent in the middle of a potential longest road
    opponent = game.turn_order[1]
    helpers.place_buildings(game, opponent, edges=[(1, 0, 3)], vertices=[(0, 0, 2)])

    # WHEN: the pieces that would connect two roads if it were not blocked
    # by the opponent's settlement are added
    new = teyuna_core.canonical_edge(0, 0, 1)
    game.use_edge(builder, new)
    actions.maybe_add_to_longest_road(game, builder, edge=new)

    # THEN: the longest road should remain unassiged because of the
    # opponent's settlement.
    assert game.longest_road == (None, 0)


def test_holder_length_updates_when_road_grows(game: entities.Game) -> None:
    holder = game.active_player
    game.longest_road = (holder, 5)
    edge = helpers.place_buildings(
        game, holder, edges=[(0, 0, d) for d in range(6)], vertices=[(0, 0, 0)]
    )

    actions.maybe_add_to_longest_road(game, holder, edge=edge)

    assert game.longest_road == (holder, 6)


def test_longest_path_remains_unassigned_if_tie_is_not_broken(
    game: entities.Game,
) -> None:
    challenger = game.active_player
    game.longest_road = (None, 5)
    edge = helpers.place_buildings(
        game, challenger, edges=[(0, 0, d) for d in range(5)], vertices=[(0, 0, 0)]
    )
    actions.maybe_add_to_longest_road(game, challenger, edge=edge)

    assert game.longest_road == (None, 5)


def test_longest_path_is_assigned_after_beating_tie(
    game: entities.Game,
) -> None:
    challenger = game.active_player
    game.longest_road = (None, 5)
    edge = helpers.place_buildings(
        game, challenger, edges=[(0, 0, d) for d in range(6)], vertices=[(0, 0, 0)]
    )
    actions.maybe_add_to_longest_road(game, challenger, edge=edge)

    assert game.longest_road == (challenger, 6)
