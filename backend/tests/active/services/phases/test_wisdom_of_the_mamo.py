import collections
import random
from typing import Any

import pytest

from src.active import entities
from src.active.services import phases


def test_raises_player_not_in_turn_error_if_not_in_turn(
    game: entities.ActiveGame,
    phase: phases.WisdomOfTheMamoPhase,
) -> None:
    with pytest.raises(phases.PlayerNotInTurnError):
        phase.run(
            game,
            phases.PlayerRequest(
                by=game.turn_order[1],
                action=phases.ClaimResourceAction(resource=entities.ResourceCard.GOLD),
            ),
        )


def test_raises_invalid_action_if_not_allowed(
    game: entities.ActiveGame,
    phase: phases.WisdomOfTheMamoPhase,
) -> None:
    with pytest.raises(phases.InvalidActionError):
        phase.run(
            game,
            phases.PlayerRequest(
                by=game.active_player,
                action=phases.PlayWisdomCardAction(
                    card=entities.WisdomCard.WINDOM_OF_MAMO
                ),
            ),
        )


def test_claim_resource_takes_from_opponents(
    game: entities.ActiveGame,
    phase: phases.WisdomOfTheMamoPhase,
) -> None:
    active = game.active_player
    opponent = game.turn_order[1]
    game.players[opponent].resources[entities.ResourceCard.WOOD] = 4
    phase.on_enter(game)

    result = phase.run(
        game,
        phases.PlayerRequest(
            by=active,
            action=phases.ClaimResourceAction(resource=entities.ResourceCard.WOOD),
        ),
    )

    expected = collections.Counter({entities.ResourceCard.WOOD: 4})
    assert result == phases.RunOutcome(finished=True, value=expected)
    assert game.players[active].resources[entities.ResourceCard.WOOD] == 4
    assert game.players[opponent].resources[entities.ResourceCard.WOOD] == 0


def test_advance_phase_claims_random_resource(game: entities.ActiveGame) -> None:
    active = game.active_player
    opponent = game.turn_order[1]
    game.players[opponent].resources[entities.ResourceCard.GOLD] = 2
    phase = phases.WisdomOfTheMamoPhase(
        rnd=_FixedChoiceRandom(entities.ResourceCard.GOLD)
    )
    phase.on_enter(game)

    result = phase.run(
        game,
        phases.PlayerRequest(
            by=active,
            action=phases.AdvancePhaseAction(),
        ),
    )

    expected = collections.Counter({entities.ResourceCard.GOLD: 2})
    assert result == phases.RunOutcome(finished=True, value=expected)
    assert game.players[active].resources[entities.ResourceCard.GOLD] == 2


def test_on_exit_after_action_returns_to_mamo_return_phase(
    game: entities.ActiveGame,
    phase: phases.WisdomOfTheMamoPhase,
) -> None:
    opponent = game.turn_order[1]
    game.players[opponent].resources[entities.ResourceCard.STONE] = 1
    game.mamo_return_phase = phases.GamePhaseName.PRE_DICE_ROLL.value
    phase.on_enter(game)
    phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.ClaimResourceAction(resource=entities.ResourceCard.STONE),
        ),
    )

    outcome = phase.on_exit(game)

    assert outcome.next is phases.GamePhaseName.PRE_DICE_ROLL
    assert outcome.value == collections.Counter({entities.ResourceCard.STONE: 1})
    assert game.mamo_return_phase is None


def test_on_exit_returns_to_trade_and_build_when_set(
    game: entities.ActiveGame,
    phase: phases.WisdomOfTheMamoPhase,
) -> None:
    game.mamo_return_phase = phases.GamePhaseName.TRADE_AND_BUILD.value
    phase.on_enter(game)
    phase.run(
        game,
        phases.PlayerRequest(
            by=game.active_player,
            action=phases.ClaimResourceAction(resource=entities.ResourceCard.MAIZE),
        ),
    )

    outcome = phase.on_exit(game)

    assert outcome.next is phases.GamePhaseName.TRADE_AND_BUILD
    assert game.mamo_return_phase is None


def test_on_exit_without_action_claims_randomly(game: entities.ActiveGame) -> None:
    opponent = game.turn_order[1]
    game.players[opponent].resources[entities.ResourceCard.COTTON] = 3
    game.mamo_return_phase = phases.GamePhaseName.PRE_DICE_ROLL.value
    phase = phases.WisdomOfTheMamoPhase(
        rnd=_FixedChoiceRandom(entities.ResourceCard.COTTON)
    )
    phase.on_enter(game)

    outcome = phase.on_exit(game)

    assert outcome.next is phases.GamePhaseName.PRE_DICE_ROLL
    assert outcome.value == collections.Counter({entities.ResourceCard.COTTON: 3})
    assert game.mamo_return_phase is None
    assert game.players[game.active_player].resources[entities.ResourceCard.COTTON] == 3


@pytest.fixture
def phase() -> phases.WisdomOfTheMamoPhase:
    return phases.WisdomOfTheMamoPhase()


class _FixedChoiceRandom(random.Random):
    def __init__(self, choice: entities.ResourceCard) -> None:
        super().__init__()
        self._choice = choice

    def choice(self, seq: Any) -> Any:
        del seq
        return self._choice
