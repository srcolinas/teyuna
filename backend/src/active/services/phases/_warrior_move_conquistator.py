from __future__ import annotations

import random

from ... import entities
from .. import actions
from . import _core, _errors
from ._move_conquistator import MoveConquistatorResult

_RND: random.Random = random.Random()


class WarriorMoveConquistatorPhase(
    _core.GamePhaseNode[MoveConquistatorResult | None, entities.HexLocation, None]
):
    def __init__(self, rnd: random.Random = _RND) -> None:
        self._rnd = rnd
        self._performed = False

    def run(
        self, game: entities.ActiveGame, request: _core.PlayerRequest
    ) -> _core.RunOutcome[MoveConquistatorResult | None]:
        if game.active_player != request.by:
            raise _errors.PlayerNotInTurnError(f"Player {request.by} is not in turn")
        match request.action:
            case _core.MoveConquistatorAction(q=q, r=r, from_player=from_player):
                actions.move_conquistator(
                    game,
                    request.by,
                    q=q,
                    r=r,
                    from_player=from_player,
                    rnd=self._rnd,
                )
                self._performed = True
                return _core.RunOutcome(
                    finished=True,
                    value=MoveConquistatorResult(
                        location=game.conquistator_location,
                        stolen_from=from_player,
                    ),
                )
            case _core.AdvancePhaseAction():
                return _core.RunOutcome(finished=True, value=None)
            case _:
                raise _errors.InvalidActionError(f"Unknown action: {request.action}")

    def on_exit(
        self, game: entities.ActiveGame
    ) -> _core.ExitOutcome[entities.HexLocation]:
        if not self._performed:
            actions.move_conquistator_randomly(game, rnd=self._rnd)
        if game.warrior_return_phase is None:
            raise RuntimeError("warrior_return_phase must be set before exiting")
        next_phase = _core.GamePhaseName(game.warrior_return_phase)
        game.warrior_return_phase = None
        return _core.ExitOutcome(
            next=next_phase,
            value=game.conquistator_location,
        )

    def on_enter(self, game: entities.ActiveGame) -> _core.EnterOutcome[None]:
        self._performed = False
        return _core.EnterOutcome(value=None)
