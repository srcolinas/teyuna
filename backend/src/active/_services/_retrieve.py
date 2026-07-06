import collections
import uuid
from typing import Protocol

from ... import player
from .. import _entities, _ports


class RetrieveGameRepository(Protocol):
    def retrieve(self, id: uuid.UUID) -> _entities.ActiveGame: ...


def retrieve_game(
    id: uuid.UUID, /, *, repository: RetrieveGameRepository
) -> _ports.ActiveGame:
    game = repository.retrieve(id)
    players, settlements, paths = [], [], []
    for nickname, entity_player in game.players.items():
        players.append(_to_port_player(nickname, entity_player))
        for location, type in entity_player.settlements.items():
            settlements.append(
                _ports.PlayedSettlement(
                    location=_ports.VertexCoordinate(
                        hex_coord=_ports.HexCoordinate(
                            q=location.hex_coord.q, r=location.hex_coord.r
                        ),
                        direction=location.direction,
                    ),
                    type=type,
                    owner=nickname,
                )
            )
        for path in entity_player.paths:
            paths.append(
                _ports.PlayedStonePath(
                    owner=nickname,
                    location=_ports.EdgeCoordinate(
                        hex_coord=_ports.HexCoordinate(
                            q=path.hex_coord.q, r=path.hex_coord.r
                        ),
                        direction=path.direction,
                    ),
                )
            )

    return _ports.ActiveGame(
        id=id,
        map=game.map,
        conquistator_location=_ports.HexCoordinate(
            q=game.conquistator_location.q, r=game.conquistator_location.r
        ),
        players=players,
        settlements=settlements,
        paths=paths,
        turn_order=game.turn_order,
    )


def _to_port_player(
    nickname: player.Nickname, entity_player: _entities.Player
) -> _ports.Player:
    counts = collections.Counter(entity_player.settlements.values())
    return _ports.Player(
        nickname=nickname,
        played_wisdom_cards=[
            card
            for card, count in entity_player.played_cards.items()
            for _ in range(count)
        ],
        num_hidden_wisdom_cards=sum(entity_player.cards.values()),
        num_resources=sum(entity_player.resources.values()),
        available_teraces=_entities.MAX_TERRACES
        - counts[_entities.SettlementType.TERRACE],
        available_great_teraces=_entities.MAX_GREAT_TERRACES
        - counts[_entities.SettlementType.GREAT_TERRACE],
        available_paths=_entities.MAX_PATHS - len(entity_player.paths),
    )
