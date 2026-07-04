import uuid
from typing import Protocol

from .. import entities, ports


class RetrieveGameRepository(Protocol):
    def retrieve(self, id: uuid.UUID) -> entities.ActiveGame | None: ...


def retrieve_game(
    id: uuid.UUID, /, *, repository: RetrieveGameRepository
) -> ports.ActiveGame | None:
    game = repository.retrieve(id)
    if game is None:
        return None

    players, settlements, paths = [], [], []
    for username, player in game.players.items():
        players.append(_to_port_player(username, player))
        for settlement in player.settlements:
            settlements.append(
                ports.PlayedSettlement(
                    location=settlement.location,
                    type=settlement.type,
                    owner=username,
                )
            )
        for location in player.paths:
            paths.append(ports.PlayedStonePath(owner=username, location=location))

    return ports.ActiveGame(
        id=id,
        map=game.map,
        conquistator_location=game.conquistator_location,
        players=players,
        settlements=settlements,
        paths=paths,
    )


def _to_port_player(username: str, player: entities.Player) -> ports.Player:
    return ports.Player(
        username=username,
        played_wisdom_cards=[
            card for card, count in player.played_cards.items() for _ in range(count)
        ],
        num_hidden_wisdom_cards=sum(player.cards.values()),
        num_resources=sum(player.resources.values()),
        available_settlements=list(player.settlements),
        available_paths=max(0, 15 - len(player.paths)),
    )
