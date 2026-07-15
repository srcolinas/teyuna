import collections
import random
from typing import Any

import pytest

from src.active import entities
from src.active.services import phases


def test_raises_player_not_in_turn_error_if_not_in_turn(
    multi_hex_game: entities.ActiveGame,
    phase: phases.WarriorMoveConquistatorPhase,
) -> None:
    target = multi_hex_game.map[1]
    with pytest.raises(phases.PlayerNotInTurnError):
        phase.run(
            multi_hex_game,
            phases.PlayerRequest(
                by=multi_hex_game.turn_order[1],
                action=phases.MoveConquistatorAction(q=target.q, r=target.r),
            ),
        )


def test_raises_invalid_action_if_not_allowed(
    multi_hex_game: entities.ActiveGame,
    phase: phases.WarriorMoveConquistatorPhase,
) -> None:
    with pytest.raises(phases.InvalidActionError):
        phase.run(
            multi_hex_game,
            phases.PlayerRequest(
                by=multi_hex_game.active_player,
                action=phases.PlayWisdomCardAction(card=entities.WisdomCard.WARRIOR),
            ),
        )


def test_move_without_steal_returns_result(
    multi_hex_game: entities.ActiveGame,
    phase: phases.WarriorMoveConquistatorPhase,
) -> None:
    target = multi_hex_game.map[1]
    expected = entities.HexLocation(q=target.q, r=target.r)
    phase.on_enter(multi_hex_game)

    result = phase.run(
        multi_hex_game,
        phases.PlayerRequest(
            by=multi_hex_game.active_player,
            action=phases.MoveConquistatorAction(q=target.q, r=target.r),
        ),
    )

    assert result == phases.RunOutcome(
        finished=True,
        value=phases.MoveConquistatorResult(location=expected, stolen_from=None),
    )
    assert multi_hex_game.conquistator_location == expected


def test_move_with_steal_reports_stolen_from(
    multi_hex_game: entities.ActiveGame,
) -> None:
    active = multi_hex_game.active_player
    victim = multi_hex_game.turn_order[1]
    target = multi_hex_game.map[1]
    expected = entities.HexLocation(q=target.q, r=target.r)
    vertex = entities.canonical_vertex(target.q, target.r, 0)
    multi_hex_game.players[victim].settlements[vertex] = entities.SettlementType.TERRACE
    multi_hex_game.players[victim].resources = collections.Counter(
        {entities.ResourceCard.WOOD: 2}
    )
    phase = phases.WarriorMoveConquistatorPhase(rnd=_FixedChoiceRandom(0))
    phase.on_enter(multi_hex_game)

    result = phase.run(
        multi_hex_game,
        phases.PlayerRequest(
            by=active,
            action=phases.MoveConquistatorAction(
                q=target.q, r=target.r, from_player=victim
            ),
        ),
    )

    assert result == phases.RunOutcome(
        finished=True,
        value=phases.MoveConquistatorResult(location=expected, stolen_from=victim),
    )
    assert multi_hex_game.players[active].resources[entities.ResourceCard.WOOD] == 1
    assert multi_hex_game.players[victim].resources[entities.ResourceCard.WOOD] == 1


def test_advance_phase_finishes_with_none(
    multi_hex_game: entities.ActiveGame,
    phase: phases.WarriorMoveConquistatorPhase,
) -> None:
    phase.on_enter(multi_hex_game)
    result = phase.run(
        multi_hex_game,
        phases.PlayerRequest(
            by=multi_hex_game.active_player,
            action=phases.AdvancePhaseAction(),
        ),
    )
    assert result == phases.RunOutcome(finished=True, value=None)


def test_on_exit_after_action_returns_to_warrior_return_phase(
    multi_hex_game: entities.ActiveGame,
    phase: phases.WarriorMoveConquistatorPhase,
) -> None:
    target = multi_hex_game.map[1]
    expected = entities.HexLocation(q=target.q, r=target.r)
    multi_hex_game.warrior_return_phase = phases.GamePhaseName.PRE_DICE_ROLL.value
    phase.on_enter(multi_hex_game)
    phase.run(
        multi_hex_game,
        phases.PlayerRequest(
            by=multi_hex_game.active_player,
            action=phases.MoveConquistatorAction(q=target.q, r=target.r),
        ),
    )

    outcome = phase.on_exit(multi_hex_game)

    assert outcome.next is phases.GamePhaseName.PRE_DICE_ROLL
    assert outcome.value == expected
    assert multi_hex_game.conquistator_location == expected
    assert multi_hex_game.warrior_return_phase is None


def test_on_exit_returns_to_trade_and_build_when_set(
    multi_hex_game: entities.ActiveGame,
    phase: phases.WarriorMoveConquistatorPhase,
) -> None:
    target = multi_hex_game.map[1]
    multi_hex_game.warrior_return_phase = phases.GamePhaseName.TRADE_AND_BUILD.value
    phase.on_enter(multi_hex_game)
    phase.run(
        multi_hex_game,
        phases.PlayerRequest(
            by=multi_hex_game.active_player,
            action=phases.MoveConquistatorAction(q=target.q, r=target.r),
        ),
    )

    outcome = phase.on_exit(multi_hex_game)

    assert outcome.next is phases.GamePhaseName.TRADE_AND_BUILD
    assert multi_hex_game.warrior_return_phase is None


def test_on_exit_without_action_relocates_randomly(
    multi_hex_game: entities.ActiveGame,
) -> None:
    original = multi_hex_game.conquistator_location
    expected = entities.HexLocation(
        q=multi_hex_game.map[1].q, r=multi_hex_game.map[1].r
    )
    multi_hex_game.warrior_return_phase = phases.GamePhaseName.PRE_DICE_ROLL.value
    phase = phases.WarriorMoveConquistatorPhase(rnd=_FixedChoiceRandom(0))
    phase.on_enter(multi_hex_game)

    outcome = phase.on_exit(multi_hex_game)

    assert outcome.next is phases.GamePhaseName.PRE_DICE_ROLL
    assert outcome.value == expected
    assert multi_hex_game.conquistator_location == expected
    assert multi_hex_game.conquistator_location != original
    assert multi_hex_game.warrior_return_phase is None
    for nickname in multi_hex_game.turn_order:
        assert sum(multi_hex_game.players[nickname].resources.values()) == 0


@pytest.fixture
def phase() -> phases.WarriorMoveConquistatorPhase:
    return phases.WarriorMoveConquistatorPhase()


@pytest.fixture
def multi_hex_game(game: entities.ActiveGame) -> entities.ActiveGame:
    jungle = entities.Hex(q=1, r=0, type=entities.HexType.JUNGLE, number=6)
    desert = entities.Hex(q=0, r=1, type=entities.HexType.DESERT, number=0)
    game.map = (game.map[0], jungle, desert)
    game.conquistator_location = entities.HexLocation(q=game.map[0].q, r=game.map[0].r)
    return game


class _FixedChoiceRandom(random.Random):
    def __init__(self, index: int) -> None:
        super().__init__()
        self._index = index

    def choice(self, seq: Any) -> Any:
        return seq[self._index]
