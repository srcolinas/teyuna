import collections
import collections.abc
import random
from typing import TypeVar

import pytest

from src.active import entities
from src.active.services import phases

_T = TypeVar("_T")


def test_non_active_player_with_more_than_seven_can_discard(
    game: entities.ActiveGame,
    phase: phases.DiscardCardsPhase,
) -> None:
    other = game.turn_order[1]
    game.players[other].resources = collections.Counter({entities.ResourceCard.GOLD: 8})
    phase.on_enter(game)

    result = phase.run(
        game,
        phases.PlayerRequest(
            by=other,
            action=phases.DiscardCardsAction(
                resources=collections.Counter({entities.ResourceCard.GOLD: 4})
            ),
        ),
    )

    assert result == phases.RunOutcome(finished=True, value=None)
    assert sum(game.players[other].resources.values()) == 4


def test_rejects_advance_phase_action(
    game: entities.ActiveGame,
    phase: phases.DiscardCardsPhase,
) -> None:
    phase.on_enter(game)
    with pytest.raises(phases.InvalidActionError):
        phase.run(
            game,
            phases.PlayerRequest(
                by=game.active_player,
                action=phases.AdvancePhaseAction(),
            ),
        )


def test_rejects_player_who_does_not_need_to_discard(
    game: entities.ActiveGame,
    phase: phases.DiscardCardsPhase,
) -> None:
    must = game.turn_order[0]
    other = game.turn_order[1]
    game.players[must].resources = collections.Counter({entities.ResourceCard.GOLD: 8})
    game.players[other].resources = collections.Counter({entities.ResourceCard.GOLD: 3})
    phase.on_enter(game)

    with pytest.raises(phases.InvalidActionError):
        phase.run(
            game,
            phases.PlayerRequest(
                by=other,
                action=phases.DiscardCardsAction(
                    resources=collections.Counter({entities.ResourceCard.GOLD: 1})
                ),
            ),
        )


def test_rejects_already_discarded_player(
    game: entities.ActiveGame,
    phase: phases.DiscardCardsPhase,
) -> None:
    p1 = game.turn_order[0]
    p2 = game.turn_order[1]
    game.players[p1].resources = collections.Counter({entities.ResourceCard.GOLD: 8})
    game.players[p2].resources = collections.Counter({entities.ResourceCard.STONE: 8})
    phase.on_enter(game)

    phase.run(
        game,
        phases.PlayerRequest(
            by=p1,
            action=phases.DiscardCardsAction(
                resources=collections.Counter({entities.ResourceCard.GOLD: 4})
            ),
        ),
    )
    game.players[p1].resources = collections.Counter({entities.ResourceCard.GOLD: 8})

    with pytest.raises(phases.InvalidActionError):
        phase.run(
            game,
            phases.PlayerRequest(
                by=p1,
                action=phases.DiscardCardsAction(
                    resources=collections.Counter({entities.ResourceCard.GOLD: 4})
                ),
            ),
        )


def test_mid_discard_does_not_finish_until_last_required_player(
    game: entities.ActiveGame,
    phase: phases.DiscardCardsPhase,
) -> None:
    p1 = game.turn_order[0]
    p2 = game.turn_order[1]
    game.players[p1].resources = collections.Counter({entities.ResourceCard.GOLD: 8})
    game.players[p2].resources = collections.Counter({entities.ResourceCard.STONE: 8})
    phase.on_enter(game)

    mid = phase.run(
        game,
        phases.PlayerRequest(
            by=p1,
            action=phases.DiscardCardsAction(
                resources=collections.Counter({entities.ResourceCard.GOLD: 4})
            ),
        ),
    )
    assert mid == phases.RunOutcome(finished=False, value=None)

    last = phase.run(
        game,
        phases.PlayerRequest(
            by=p2,
            action=phases.DiscardCardsAction(
                resources=collections.Counter({entities.ResourceCard.STONE: 4})
            ),
        ),
    )
    assert last == phases.RunOutcome(finished=True, value=None)


def test_nobody_must_discard_finishes_without_inventory_change(
    game: entities.ActiveGame,
    phase: phases.DiscardCardsPhase,
) -> None:
    for nickname in game.turn_order:
        game.players[nickname].resources = collections.Counter(
            {entities.ResourceCard.GOLD: 5}
        )
    phase.on_enter(game)

    result = phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.DiscardCardsAction(resources=collections.Counter()),
        ),
    )

    assert result == phases.RunOutcome(finished=True, value=None)
    assert sum(game.players[game.active_player].resources.values()) == 5


def test_on_enter_returns_players_who_must_discard_and_counts(
    game: entities.ActiveGame,
    phase: phases.DiscardCardsPhase,
) -> None:
    p1 = game.turn_order[0]
    p2 = game.turn_order[1]
    game.players[p1].resources = collections.Counter({entities.ResourceCard.GOLD: 8})
    game.players[p2].resources = collections.Counter({entities.ResourceCard.GOLD: 9})
    game.players[game.turn_order[2]].resources = collections.Counter(
        {entities.ResourceCard.GOLD: 7}
    )

    outcome = phase.on_enter(game)

    assert phase._must_discard == {p1, p2}
    assert phase._discarded == set()
    assert outcome.value == (
        phases.DiscardRequirement(by=p1, count=4),
        phases.DiscardRequirement(by=p2, count=4),
    )


def test_on_exit_returns_move_conquistator_and_auto_discards_pending(
    game: entities.ActiveGame,
) -> None:
    pending = game.turn_order[1]
    game.players[pending].resources = collections.Counter(
        {
            entities.ResourceCard.GOLD: 4,
            entities.ResourceCard.STONE: 4,
        }
    )
    phase = phases.DiscardCardsPhase(rnd=_FixedSampleRandom([0, 1, 2, 3]))
    phase.on_enter(game)
    assert pending in phase._must_discard

    outcome = phase.on_exit(game)

    assert outcome.next is phases.GamePhaseName.MOVE_CONQUISTATOR
    assert sum(game.players[pending].resources.values()) == 4


@pytest.fixture
def phase() -> phases.DiscardCardsPhase:
    return phases.DiscardCardsPhase()


class _FixedSampleRandom(random.Random):
    def __init__(self, indexes: list[int]) -> None:
        super().__init__()
        self._indexes = indexes

    def sample(
        self,
        population: collections.abc.Sequence[_T],
        k: int,
        *,
        counts: collections.abc.Iterable[int] | None = None,
    ) -> list[_T]:
        del counts
        return [population[i] for i in self._indexes[:k]]
