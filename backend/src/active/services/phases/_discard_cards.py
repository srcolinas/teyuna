from __future__ import annotations

import dataclasses
import random

from .... import player
from ... import entities
from .. import actions
from . import _core, _errors

_RND: random.Random = random.Random()


@dataclasses.dataclass(frozen=True, slots=True)
class DiscardRequirement:
    by: player.Nickname
    count: int


class DiscardCardsPhase(
    _core.GamePhaseNode[None, None, tuple[DiscardRequirement, ...]]
):
    def __init__(self, rnd: random.Random = _RND) -> None:
        self._rnd = rnd
        self._must_discard: set[player.Nickname] = set()
        self._discarded: set[player.Nickname] = set()

    def run(
        self, game: entities.ActiveGame, request: _core.PlayerRequest
    ) -> _core.RunOutcome[None]:
        match request.action:
            case _core.DiscardCardsAction(resources=resources):
                if self._must_discard <= self._discarded:
                    return _core.RunOutcome(finished=True, value=None)
                if (
                    request.by not in self._must_discard
                    or request.by in self._discarded
                ):
                    raise _errors.InvalidActionError(
                        f"Player {request.by} cannot discard cards"
                    )
                actions.discard_cards(game, request.by, resources=resources)
                self._discarded.add(request.by)
                finished = self._must_discard <= self._discarded
                return _core.RunOutcome(finished=finished, value=None)
            case _:
                raise _errors.InvalidActionError(f"Unknown action: {request.action}")

    def on_exit(self, game: entities.ActiveGame) -> _core.ExitOutcome[None]:
        for nickname in self._must_discard - self._discarded:
            actions.discard_random_half(game, nickname, rnd=self._rnd)
        return _core.ExitOutcome(next=_core.GamePhaseName.MOVE_CONQUISTATOR, value=None)

    def on_enter(
        self, game: entities.ActiveGame
    ) -> _core.EnterOutcome[tuple[DiscardRequirement, ...]]:
        self._discarded = set()
        requirements: list[DiscardRequirement] = []
        for nickname in game.turn_order:
            total = sum(game.players[nickname].resources.values())
            if total > 7:
                requirements.append(DiscardRequirement(by=nickname, count=total // 2))
        self._must_discard = {requirement.by for requirement in requirements}
        return _core.EnterOutcome(value=tuple(requirements))
