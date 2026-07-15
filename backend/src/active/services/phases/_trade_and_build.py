from __future__ import annotations

import dataclasses

from .... import player
from ... import entities
from .. import actions
from . import _core, _errors


@dataclasses.dataclass(frozen=True, slots=True)
class LongestRoadResult:
    owner: player.Nickname | None
    length: int


class TradeAndBuildPhase(
    _core.GamePhaseNode[
        entities.TradeProposal | LongestRoadResult | entities.WisdomCard | None,
        None,
        None,
    ]
):
    def run(
        self, game: entities.ActiveGame, request: _core.PlayerRequest
    ) -> _core.RunOutcome[
        entities.TradeProposal | LongestRoadResult | entities.WisdomCard | None
    ]:
        match request.action:
            case _core.ProposeTradeAction(offer=offer, request=trade_request, to=to):
                if request.by != game.active_player and to != (game.active_player,):
                    raise _errors.InvalidActionError(
                        f"Player {request.by} can only propose trades to the active player"
                    )
                actions.propose_trade(
                    game, by=request.by, offer=offer, request=trade_request, to=to
                )
                return _core.RunOutcome(finished=False, value=None)
            case _core.TradeWithSupplyAction(offers=offers, requests=requests):
                _require_active_player(game, request.by)
                actions.trade(game, by=request.by, offers=offers, requests=requests)
                return _core.RunOutcome(finished=False, value=None)
            case _core.AcceptTradeProposalAction(id=proposal_id):
                proposal = game.trade_proposals.get(proposal_id)
                if proposal is not None and request.by not in proposal.to:
                    raise _errors.InvalidActionError(
                        f"Player {request.by} cannot accept this trade proposal"
                    )
                actions.accept_trade(game, by=request.by, id=proposal_id)
                return _core.RunOutcome(finished=False, value=proposal)
            case _core.BuyAction(item=item, coordinate=coordinate):
                _require_active_player(game, request.by)
                match item:
                    case _core.Buyable.TERRACE:
                        actions.build_terrace(
                            game,
                            request.by,
                            q=coordinate.q,
                            r=coordinate.r,
                            direction=coordinate.d,
                        )
                        if game.longest_road[0] is not None:
                            vertex = entities.canonical_vertex(
                                coordinate.q, coordinate.r, coordinate.d
                            )
                            updated = actions.recompute_longest_road(
                                game, request.by, vertex=vertex
                            )
                            if updated is not None:
                                owner, length = updated
                                return _core.RunOutcome(
                                    finished=False,
                                    value=LongestRoadResult(owner=owner, length=length),
                                )
                    case _core.Buyable.GREAT_TERRACE:
                        actions.build_great_terrace(
                            game,
                            request.by,
                            q=coordinate.q,
                            r=coordinate.r,
                            direction=coordinate.d,
                        )
                    case _core.Buyable.PATH:
                        edge = entities.canonical_edge(
                            coordinate.q, coordinate.r, coordinate.d
                        )
                        actions.build_path(
                            game,
                            request.by,
                            q=coordinate.q,
                            r=coordinate.r,
                            direction=coordinate.d,
                        )
                        awarded = actions.update_longest_road(
                            game, request.by, edge=edge
                        )
                        if awarded is not None:
                            owner, length = awarded
                            return _core.RunOutcome(
                                finished=False,
                                value=LongestRoadResult(owner=owner, length=length),
                            )
                return _core.RunOutcome(finished=False, value=None)
            case _core.BuyWisdomCardAction():
                _require_active_player(game, request.by)
                actions.buy_wisdom_card(game, request.by)
                return _core.RunOutcome(finished=False, value=None)
            case _core.PlayWisdomCardAction(card=card):
                _require_active_player(game, request.by)
                actions.play_wisdom_card(game, request.by, card=card)
                if card is entities.WisdomCard.WARRIOR:
                    game.warrior_return_phase = (
                        _core.GamePhaseName.TRADE_AND_BUILD.value
                    )
                    return _core.RunOutcome(finished=True, value=card)
                if card is entities.WisdomCard.BLESSING_OF_ALUNA:
                    game.blessing_return_phase = (
                        _core.GamePhaseName.TRADE_AND_BUILD.value
                    )
                    return _core.RunOutcome(finished=True, value=card)
                return _core.RunOutcome(finished=False, value=card)
            case _core.AdvancePhaseAction():
                _require_active_player(game, request.by)
                return _core.RunOutcome(finished=True, value=None)
            case _:
                raise _errors.InvalidActionError(f"Unknown action: {request.action}")

    def on_exit(self, game: entities.ActiveGame) -> _core.ExitOutcome[None]:
        if game.warrior_return_phase is not None:
            return _core.ExitOutcome(
                next=_core.GamePhaseName.WARRIOR_MOVE_CONQUISTATOR, value=None
            )
        if game.blessing_return_phase is not None:
            return _core.ExitOutcome(
                next=_core.GamePhaseName.BLESSING_OF_ALUNA, value=None
            )
        game.trade_proposals.clear()
        game.player_idx = (game.player_idx + 1) % len(game.turn_order)
        return _core.ExitOutcome(next=_core.GamePhaseName.PRE_DICE_ROLL, value=None)

    def on_enter(self, game: entities.ActiveGame) -> _core.EnterOutcome[None]:
        game.trade_proposals.clear()
        return _core.EnterOutcome(value=None)


def _require_active_player(game: entities.ActiveGame, by: player.Nickname) -> None:
    if game.active_player != by:
        raise _errors.PlayerNotInTurnError(f"Player {by} is not in turn")
