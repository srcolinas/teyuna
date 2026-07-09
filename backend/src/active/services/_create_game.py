import collections
import random

from collections.abc import Sequence

from ... import player
from .. import entities, _map


def create_new(players: Sequence[player.Nickname]) -> entities.ActiveGame:
    map = _map.generate_map()
    deserts = [hex for hex in map if hex.type == entities.HexType.DESERT]
    players = list(players)
    random.shuffle(players)
    return entities.ActiveGame(
        map=map,
        conquistator_location=random.choice(deserts),
        turn_order=tuple(players),
        players={
            nickname: entities.Player(
                cards=collections.Counter(),
                played_cards=collections.Counter(),
                resources=collections.Counter(),
                settlements=entities.SettlementsCollection(),
                paths=set(),
            )
            for nickname in players
        },
    )
