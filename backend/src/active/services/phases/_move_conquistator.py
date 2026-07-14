from __future__ import annotations

import dataclasses
import random

from .... import player
from ... import entities
from .. import actions
from . import _core, _errors

_RND: random.Random = random.Random()


@dataclasses.dataclass(frozen=True, slots=True)
class MoveConquistatorResult:
    location: entities.HexLocation
    stolen_from: player.Nickname | None


class MoveConquistatorPhase(
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
        return _core.ExitOutcome(
            next=_core.GamePhaseName.TRADE_AND_BUILD,
            value=game.conquistator_location,
        )

    def on_enter(self, game: entities.ActiveGame) -> _core.EnterOutcome[None]:
        self._performed = False
        return _core.EnterOutcome(value=None)
