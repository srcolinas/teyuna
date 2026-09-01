import collections
import datetime

import pytest

from src.game import entities
import teyuna_core


@pytest.fixture
def game() -> entities.Game:
    mountains = teyuna_core.MapHex(
        q=0, r=0, type=teyuna_core.HexType.MOUNTAINS, number=1
    )
    nicknames = ("player-0", "player-1", "player-2")
    started = entities.Game(
        map=(mountains,),
        conquistator_location=teyuna_core.HexLocation(q=mountains.q, r=mountains.r),
        players={
            nickname: entities.Player(
                cards=collections.Counter(),
                played_cards=collections.Counter(),
                resources=collections.Counter(),
                settlements=entities.SettlementsCollection(),
                paths=set(),
            )
            for nickname in nicknames
        },
        available_slots=0,
    )
    started.start(datetime.timedelta(seconds=60))
    return started
