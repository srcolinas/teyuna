import collections
import collections.abc
import random
from typing import TypeVar

import pytest

from src.active import entities
from src.active.services import phases

_T = TypeVar("_T")


def test_raises_player_not_in_turn_error_if_not_in_turn(
    game: entities.ActiveGame,
    phase: phases.BlessingOfAlunaPhase,
) -> None:
    with pytest.raises(phases.PlayerNotInTurnError):
        phase.run(
            game,
            phases.PlayerRequest(
                by=game.turn_order[1],
                action=phases.TakeFromSupplyAction(
                    resources=collections.Counter(
                        {
                            entities.ResourceCard.GOLD: 1,
                            entities.ResourceCard.WOOD: 1,
                        }
                    )
                ),
            ),
        )


def test_raises_invalid_action_if_not_allowed(
    game: entities.ActiveGame,
    phase: phases.BlessingOfAlunaPhase,
) -> None:
    with pytest.raises(phases.InvalidActionError):
        phase.run(
            game,
            phases.PlayerRequest(
                by=game.active_player,
                action=phases.PlayWisdomCardAction(
                    card=entities.WisdomCard.BLESSING_OF_ALUNA
                ),
            ),
        )


def test_take_from_supply_returns_resources(
    game: entities.ActiveGame,
    phase: phases.BlessingOfAlunaPhase,
) -> None:
    taken = collections.Counter(
        {
            entities.ResourceCard.GOLD: 1,
            entities.ResourceCard.WOOD: 1,
        }
    )
    phase.on_enter(game)

    result = phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.TakeFromSupplyAction(resources=taken),
        ),
    )

    assert result == phases.RunOutcome(finished=True, value=taken)
    assert game.players[game.active_player].resources[entities.ResourceCard.GOLD] == 1
    assert game.players[game.active_player].resources[entities.ResourceCard.WOOD] == 1


def test_advance_phase_grants_random_resources(game: entities.ActiveGame) -> None:
    game.resource_supply = collections.Counter(
        {
            entities.ResourceCard.GOLD: 1,
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.COTTON: 0,
            entities.ResourceCard.MAIZE: 0,
            entities.ResourceCard.WOOD: 0,
        }
    )
    expected = collections.Counter(
        {
            entities.ResourceCard.GOLD: 1,
            entities.ResourceCard.STONE: 1,
        }
    )
    phase = phases.BlessingOfAlunaPhase(rnd=_FixedSampleRandom([0, 1]))
    phase.on_enter(game)

    result = phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.AdvancePhaseAction(),
        ),
    )

    assert result == phases.RunOutcome(finished=True, value=expected)
    assert game.players[game.active_player].resources == expected
    assert sum(game.resource_supply.values()) == 0


def test_on_exit_after_action_returns_to_blessing_return_phase(
    game: entities.ActiveGame,
    phase: phases.BlessingOfAlunaPhase,
) -> None:
    taken = collections.Counter(
        {
            entities.ResourceCard.GOLD: 1,
            entities.ResourceCard.WOOD: 1,
        }
    )
    game.blessing_return_phase = phases.GamePhaseName.PRE_DICE_ROLL.value
    phase.on_enter(game)
    phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.TakeFromSupplyAction(resources=taken),
        ),
    )

    outcome = phase.on_exit(game)

    assert outcome.next is phases.GamePhaseName.PRE_DICE_ROLL
    assert outcome.value == taken
    assert game.blessing_return_phase is None


def test_on_exit_returns_to_trade_and_build_when_set(
    game: entities.ActiveGame,
    phase: phases.BlessingOfAlunaPhase,
) -> None:
    taken = collections.Counter({entities.ResourceCard.STONE: 2})
    game.blessing_return_phase = phases.GamePhaseName.TRADE_AND_BUILD.value
    phase.on_enter(game)
    phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.TakeFromSupplyAction(resources=taken),
        ),
    )

    outcome = phase.on_exit(game)

    assert outcome.next is phases.GamePhaseName.TRADE_AND_BUILD
    assert game.blessing_return_phase is None


def test_on_exit_after_advance_returns_taken_resources(
    game: entities.ActiveGame,
) -> None:
    game.resource_supply = collections.Counter(
        {
            entities.ResourceCard.GOLD: 1,
            entities.ResourceCard.STONE: 1,
            entities.ResourceCard.COTTON: 0,
            entities.ResourceCard.MAIZE: 0,
            entities.ResourceCard.WOOD: 0,
        }
    )
    expected = collections.Counter(
        {
            entities.ResourceCard.GOLD: 1,
            entities.ResourceCard.STONE: 1,
        }
    )
    game.blessing_return_phase = phases.GamePhaseName.PRE_DICE_ROLL.value
    phase = phases.BlessingOfAlunaPhase(rnd=_FixedSampleRandom([0, 1]))
    phase.on_enter(game)
    phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.AdvancePhaseAction(),
        ),
    )

    outcome = phase.on_exit(game)

    assert outcome.next is phases.GamePhaseName.PRE_DICE_ROLL
    assert outcome.value == expected
    assert game.blessing_return_phase is None


@pytest.fixture
def phase() -> phases.BlessingOfAlunaPhase:
    return phases.BlessingOfAlunaPhase()


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
