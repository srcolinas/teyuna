from __future__ import annotations

import dataclasses
import random

from ... import entities
from . import _core, _errors

_RND: random.Random = random.Random()


@dataclasses.dataclass(frozen=True, slots=True)
class DiceRollResult:
    first: int
    second: int


class DiceRollPhase(_core.GamePhaseNode[None, DiceRollResult, None]):
    def __init__(self, rnd: random.Random = _RND) -> None:
        self._rnd = rnd

    def run(
        self, game: entities.ActiveGame, request: _core.PlayerRequest
    ) -> _core.RunOutcome[None]:
        if game.active_player != request.by:
            raise _errors.PlayerNotInTurnError(f"Player {request.by} is not in turn")
        match request.action:
            case _core.AdvancePhaseAction():
                return _core.RunOutcome(finished=True, value=None)
            case _:
                raise _errors.InvalidActionError(f"Unknown action: {request.action}")
        return _core.RunOutcome(finished=True, value=None)

    def on_exit(self, game: entities.ActiveGame) -> _core.ExitOutcome[DiceRollResult]:
        first = self._rnd.randint(1, 6)
        second = self._rnd.randint(1, 6)
        next_phase = (
            _core.GamePhaseName.CONQUEST
            if first + second == 7
            else _core.GamePhaseName.PRODUCTION
        )
        return _core.ExitOutcome(
            next=next_phase,
            value=DiceRollResult(first=first, second=second),
        )

    def on_enter(self, game: entities.ActiveGame) -> _core.EnterOutcome[None]:
        return _core.EnterOutcome(value=None)
