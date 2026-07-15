from __future__ import annotations

import collections
import random

from ... import entities
from .. import actions
from . import _core, _errors

_RND: random.Random = random.Random()


class BlessingOfAlunaPhase(
    _core.GamePhaseNode[entities.ResourceCount, entities.ResourceCount, None]
):
    def __init__(self, rnd: random.Random = _RND) -> None:
        self._rnd = rnd
        self._performed = False
        self._taken: entities.ResourceCount = collections.Counter()

    def run(
        self, game: entities.ActiveGame, request: _core.PlayerRequest
    ) -> _core.RunOutcome[entities.ResourceCount]:
        if game.active_player != request.by:
            raise _errors.PlayerNotInTurnError(f"Player {request.by} is not in turn")
        match request.action:
            case _core.TakeFromSupplyAction(resources=resources):
                taken = actions.take_from_supply(game, request.by, resources=resources)
                self._performed = True
                self._taken = taken
                return _core.RunOutcome(finished=True, value=taken)
            case _core.AdvancePhaseAction():
                taken = actions.take_from_supply_randomly(
                    game, request.by, rnd=self._rnd
                )
                self._performed = True
                self._taken = taken
                return _core.RunOutcome(finished=True, value=taken)
            case _:
                raise _errors.InvalidActionError(f"Unknown action: {request.action}")

    def on_exit(
        self, game: entities.ActiveGame
    ) -> _core.ExitOutcome[entities.ResourceCount]:
        if not self._performed:
            self._taken = actions.take_from_supply_randomly(
                game, game.active_player, rnd=self._rnd
            )
        if game.blessing_return_phase is None:
            raise RuntimeError("blessing_return_phase must be set before exiting")
        next_phase = _core.GamePhaseName(game.blessing_return_phase)
        game.blessing_return_phase = None
        return _core.ExitOutcome(next=next_phase, value=self._taken)

    def on_enter(self, game: entities.ActiveGame) -> _core.EnterOutcome[None]:
        self._performed = False
        self._taken = collections.Counter()
        return _core.EnterOutcome(value=None)
