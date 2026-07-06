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
        for settlement in entity_player.settlements:
            settlements.append(
                _ports.PlayedSettlement(
                    location=settlement.location,
                    type=settlement.type,
                    owner=nickname,
                )
            )
        for location in entity_player.paths:
            paths.append(_ports.PlayedStonePath(owner=nickname, location=location))

    return _ports.ActiveGame(
        id=id,
        map=game.map,
        conquistator_location=game.conquistator_location,
        players=players,
        settlements=settlements,
        paths=paths,
        turn_order=game.turn_order,
    )


def _to_port_player(
    nickname: player.Nickname, entity_player: _entities.Player
) -> _ports.Player:
    return _ports.Player(
        nickname=nickname,
        played_wisdom_cards=[
            card
            for card, count in entity_player.played_cards.items()
            for _ in range(count)
        ],
        num_hidden_wisdom_cards=sum(entity_player.cards.values()),
        num_resources=sum(entity_player.resources.values()),
        available_settlements=list(entity_player.settlements),
        available_paths=max(0, 15 - len(entity_player.paths)),
    )
