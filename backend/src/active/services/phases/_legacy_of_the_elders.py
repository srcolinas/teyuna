from __future__ import annotations

from ... import entities
from . import _core, _errors


class LegacyOfTheEldersPhase(_core.GamePhaseNode[None, None, None]):
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

    def on_exit(self, game: entities.ActiveGame) -> _core.ExitOutcome[None]:
        if game.legacy_return_phase is None:
            raise RuntimeError("legacy_return_phase must be set before exiting")
        next_phase = _core.GamePhaseName(game.legacy_return_phase)
        game.legacy_return_phase = None
        return _core.ExitOutcome(next=next_phase, value=None)

    def on_enter(self, game: entities.ActiveGame) -> _core.EnterOutcome[None]:
        return _core.EnterOutcome(value=None)
