from __future__ import annotations

from ... import entities
from .. import actions
from . import _core, _errors
from ._trade_and_build import GameWonResult, LongestRoadResult


class PathfinderPhase(
    _core.GamePhaseNode[LongestRoadResult | GameWonResult | None, None, None]
):
    def __init__(self) -> None:
        self._paths_placed = 0

    def run(
        self, game: entities.ActiveGame, request: _core.PlayerRequest
    ) -> _core.RunOutcome[LongestRoadResult | GameWonResult | None]:
        if game.active_player != request.by:
            raise _errors.PlayerNotInTurnError(f"Player {request.by} is not in turn")
        match request.action:
            case _core.BuyAction(item=item, coordinate=coordinate):
                if item is not _core.Buyable.PATH:
                    raise _errors.InvalidActionError(
                        f"Unknown action: {request.action}"
                    )
                if len(game.players[request.by].paths) >= entities.MAX_PATHS:
                    raise actions.InsufficientResources
                edge = entities.canonical_edge(coordinate.q, coordinate.r, coordinate.d)
                actions.add_free_path(
                    game,
                    request.by,
                    q=coordinate.q,
                    r=coordinate.r,
                    direction=coordinate.d,
                )
                self._paths_placed += 1
                awarded = actions.update_longest_road(game, request.by, edge=edge)
                if actions.declare_winner_if_eligible(game, request.by):
                    return _core.RunOutcome(
                        finished=True,
                        value=GameWonResult(winner=request.by),
                    )
                value: LongestRoadResult | None = None
                if awarded is not None:
                    owner, length = awarded
                    value = LongestRoadResult(owner=owner, length=length)
                return _core.RunOutcome(finished=self._paths_placed >= 2, value=value)
            case _core.AdvancePhaseAction():
                return _core.RunOutcome(finished=True, value=None)
            case _:
                raise _errors.InvalidActionError(f"Unknown action: {request.action}")

    def on_exit(self, game: entities.ActiveGame) -> _core.ExitOutcome[None]:
        if game.winner is not None:
            game.pathfinder_return_phase = None
            return _core.ExitOutcome(next=_core.GamePhaseName.END, value=None)
        if game.pathfinder_return_phase is None:
            raise RuntimeError("pathfinder_return_phase must be set before exiting")
        next_phase = _core.GamePhaseName(game.pathfinder_return_phase)
        game.pathfinder_return_phase = None
        return _core.ExitOutcome(next=next_phase, value=None)

    def on_enter(self, game: entities.ActiveGame) -> _core.EnterOutcome[None]:
        self._paths_placed = 0
        return _core.EnterOutcome(value=None)
