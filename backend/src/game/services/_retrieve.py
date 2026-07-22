import uuid
from typing import Protocol

from .. import actions, entities, player, ports


class RetrieveGameRepository(Protocol):
    def retrieve(self, id: uuid.UUID) -> entities.Game: ...


def retrieve_game(
    id: uuid.UUID, /, *, repository: RetrieveGameRepository
) -> ports.Game:
    game = repository.retrieve(id)
    players, settlements, paths = [], [], []
    for nickname, entity_player in game.players.items():
        players.append(_to_port_player(game, nickname, entity_player))
        for location, type in entity_player.settlements.items():
            settlements.append(
                ports.PlayedSettlement(
                    location=ports.VertexCoordinate(
                        hex_coord=ports.HexCoordinate(q=location.q, r=location.r),
                        direction=location.d,
                    ),
                    type=type,
                    owner=nickname,
                )
            )
        for path in entity_player.paths:
            paths.append(
                ports.PlayedStonePath(
                    owner=nickname,
                    location=ports.EdgeCoordinate(
                        hex_coord=ports.HexCoordinate(q=path.q, r=path.r),
                        direction=path.d,
                    ),
                )
            )

    return ports.Game(
        id=id,
        map=tuple(
            ports.Hex(
                coordinate=ports.HexCoordinate(q=hex.q, r=hex.r),
                type=hex.type,
                number=hex.number,
            )
            for hex in game.map
        ),
        conquistator_location=ports.HexCoordinate(
            q=game.conquistator_location.q, r=game.conquistator_location.r
        ),
        players=players,
        settlements=settlements,
        paths=paths,
        turn_order=_turn_order_from_active(
            game.turn_order, game.player_idx, game.phase
        ),
        phase=game.phase,
        phase_deadline=game.phase_deadline,
        available_slots=game.available_slots,
    )


def _turn_order_from_active(
    turn_order: tuple[player.Nickname, ...],
    player_idx: int,
    phase: entities.GamePhaseName,
) -> tuple[player.Nickname, ...]:
    """Return seating order starting at the active player.

    Clockwise for all phases except second placement, which is counter-clockwise.
    Empty while the game is still in the lobby.
    """
    if not turn_order:
        return ()
    if phase is entities.GamePhaseName.SECOND_PLACEMENT:
        return turn_order[player_idx::-1] + turn_order[:player_idx:-1]
    return turn_order[player_idx:] + turn_order[:player_idx]


def _to_port_player(
    game: entities.Game,
    nickname: player.Nickname,
    entity_player: entities.Player,
) -> ports.Player:
    counts = entity_player.settlements.counts
    return ports.Player(
        nickname=nickname,
        victory_points=actions.victory_points(game, nickname),
        played_wisdom_cards=[
            card
            for card, count in entity_player.played_cards.items()
            for _ in range(count)
        ],
        num_hidden_wisdom_cards=sum(entity_player.cards.values())
        + sum(entity_player.cards_bought_this_turn.values()),
        num_resources=sum(entity_player.resources.values()),
        available_terraces=entities.MAX_TERRACES
        - counts[entities.SettlementType.TERRACE],
        available_great_terraces=entities.MAX_GREAT_TERRACES
        - counts[entities.SettlementType.GREAT_TERRACE],
        available_paths=entities.MAX_PATHS - len(entity_player.paths),
    )
