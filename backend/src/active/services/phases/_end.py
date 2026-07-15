from __future__ import annotations

from ... import entities
from . import _core, _errors


class EndPhase(_core.GamePhaseNode[None, None, None]):
    def run(
        self, game: entities.ActiveGame, request: _core.PlayerRequest
    ) -> _core.RunOutcome[None]:
        raise _errors.InvalidActionError(
            f"Game has ended; no actions are allowed (got {request.action})"
        )

    def on_exit(self, game: entities.ActiveGame) -> _core.ExitOutcome[None]:
        raise RuntimeError("End phase cannot be exited")

    def on_enter(self, game: entities.ActiveGame) -> _core.EnterOutcome[None]:
        return _core.EnterOutcome(value=None)
