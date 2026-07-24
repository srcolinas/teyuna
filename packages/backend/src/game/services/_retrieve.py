import uuid
from typing import Protocol

import teyuna_core

from .. import entities


class RetrieveGameRepository(Protocol):
    def retrieve(self, id: uuid.UUID) -> entities.Game: ...


def retrieve_game(
    id: uuid.UUID, /, *, repository: RetrieveGameRepository
) -> teyuna_core.Game:
    game = repository.retrieve(id)
    victory_points = game.victory_points
    players, settlements, paths = [], [], []
    for nickname, entity_player in game.players.items():
        players.append(
            _to_port_player(nickname, entity_player, victory_points[nickname])
        )
        for location, type in entity_player.settlements.items():
            settlements.append(
                teyuna_core.PlayedSettlement(
                    location=teyuna_core.VertexCoordinate(
                        hex_coord=teyuna_core.HexCoordinate(q=location.q, r=location.r),
                        direction=location.d,
                    ),
                    type=type,
                    owner=nickname,
                )
            )
        for path in entity_player.paths:
            paths.append(
                teyuna_core.PlayedStonePath(
                    owner=nickname,
                    location=teyuna_core.EdgeCoordinate(
                        hex_coord=teyuna_core.HexCoordinate(q=path.q, r=path.r),
                        direction=path.d,
                    ),
                )
            )
    return teyuna_core.Game(
        id=id,
        turns_played=game.turns_played,
        map=tuple(
            teyuna_core.Hex(
                coordinate=teyuna_core.HexCoordinate(q=hex.q, r=hex.r),
                type=hex.type,
                number=hex.number,
            )
            for hex in game.map
        ),
        conquistator_location=teyuna_core.HexCoordinate(
            q=game.conquistator_location.q, r=game.conquistator_location.r
        ),
        harbours=teyuna_core.grouped_harbours(game.harbours),
        players=players,
        settlements=settlements,
        paths=paths,
        turn_order=_turn_order_from_active(
            game.turn_order, game.player_idx, game.phase
        ),
        phase=game.phase,
        phase_deadline=game.phase_deadline,
        available_slots=game.available_slots,
        trade_proposals=[
            teyuna_core.ActiveTradeProposal(
                id=proposal_id,
                by=proposal.by,
                offer=dict(proposal.offer),
                request=dict(proposal.request),
                to=sorted(proposal.to),
            )
            for proposal_id, proposal in game.trade_proposals.items()
        ],
        to_discard_resources=dict(game.to_discard_resources),
    )


def _turn_order_from_active(
    turn_order: tuple[str, ...],
    player_idx: int,
    phase: teyuna_core.GamePhaseName,
) -> tuple[str, ...]:
    """Return seating order starting at the active player.

    Clockwise for all phases except second placement, which is counter-clockwise.
    Empty while the game is still in the lobby.
    """
    if not turn_order:
        return ()
    if phase is teyuna_core.GamePhaseName.SECOND_PLACEMENT:
        return turn_order[player_idx::-1] + turn_order[:player_idx:-1]
    return turn_order[player_idx:] + turn_order[:player_idx]


def _to_port_player(
    nickname: str, entity_player: entities.Player, victory_points: int
) -> teyuna_core.Player:
    counts = entity_player.settlements.counts
    return teyuna_core.Player(
        victory_points=victory_points,
        nickname=nickname,
        played_wisdom_cards=[
            card
            for card, count in entity_player.played_cards.items()
            for _ in range(count)
        ],
        num_hidden_wisdom_cards=sum(entity_player.cards.values())
        + sum(entity_player.cards_bought_this_turn.values()),
        num_resources=sum(entity_player.resources.values()),
        available_terraces=teyuna_core.MAX_TERRACES
        - counts[teyuna_core.SettlementType.TERRACE],
        available_great_terraces=teyuna_core.MAX_GREAT_TERRACES
        - counts[teyuna_core.SettlementType.GREAT_TERRACE],
        available_paths=teyuna_core.MAX_PATHS - len(entity_player.paths),
    )


def retrieve_hand(
    id: uuid.UUID,
    nickname: str,
    /,
    *,
    repository: RetrieveGameRepository,
) -> teyuna_core.PlayerHand:
    game = repository.retrieve(id)
    entity_player = game.players[nickname]
    wisdom_cards = [
        card for card, count in entity_player.cards.items() for _ in range(count)
    ] + [
        card
        for card, count in entity_player.cards_bought_this_turn.items()
        for _ in range(count)
    ]
    return teyuna_core.PlayerHand(
        resources=dict(entity_player.resources),
        wisdom_cards=wisdom_cards,
    )
