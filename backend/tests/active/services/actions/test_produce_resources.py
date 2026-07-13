import collections

from src.active import entities
from src.active.services import actions


def test_produces_gives_1_resource_from_terrace() -> None:
    game = entities.ActiveGame(
        map=(
            entities.Hex(
                q=0,
                r=0,
                type=entities.HexType.MOUNTAINS,
                number=8,
            ),
            entities.Hex(
                q=0,
                r=1,
                type=entities.HexType.DESERT,
                number=7,
            ),
        ),
        conquistator_location=entities.Hex(
            q=0,
            r=1,
            type=entities.HexType.DESERT,
            number=7,
        ),
        turn_order=("srcolinas-1", "srcolinas-2", "srcolinas-3"),
        players={
            "srcolinas-1": entities.Player(
                resources=collections.Counter({entities.ResourceCard.GOLD: 0}),
                settlements=entities.SettlementsCollection(
                    {
                        entities.Coordinate(
                            q=0, r=-1, d=2
                        ): entities.SettlementType.TERRACE,
                    },
                ),
            ),
            "srcolinas-2": entities.Player(),
            "srcolinas-3": entities.Player(),
        },
    )
    actions.produce_resources(game, roll=8)
    assert game.players["srcolinas-1"].resources[entities.ResourceCard.GOLD] == 1
    assert game.players["srcolinas-2"].resources[entities.ResourceCard.GOLD] == 0
    assert game.players["srcolinas-3"].resources[entities.ResourceCard.GOLD] == 0


def test_produces_gives_2_resources_from_great_terrace() -> None:
    game = entities.ActiveGame(
        map=(
            entities.Hex(
                q=0,
                r=0,
                type=entities.HexType.MOUNTAINS,
                number=8,
            ),
            entities.Hex(
                q=0,
                r=1,
                type=entities.HexType.DESERT,
                number=7,
            ),
        ),
        conquistator_location=entities.Hex(
            q=0,
            r=1,
            type=entities.HexType.DESERT,
            number=7,
        ),
        turn_order=("srcolinas-1", "srcolinas-2", "srcolinas-3"),
        players={
            "srcolinas-1": entities.Player(
                resources=collections.Counter({entities.ResourceCard.GOLD: 0}),
                settlements=entities.SettlementsCollection(
                    {
                        entities.Coordinate(
                            q=0, r=-1, d=2
                        ): entities.SettlementType.GREAT_TERRACE,
                    },
                ),
            ),
            "srcolinas-2": entities.Player(),
            "srcolinas-3": entities.Player(),
        },
    )
    actions.produce_resources(game, roll=8)
    assert game.players["srcolinas-1"].resources[entities.ResourceCard.GOLD] == 2
    assert game.players["srcolinas-2"].resources[entities.ResourceCard.GOLD] == 0
    assert game.players["srcolinas-3"].resources[entities.ResourceCard.GOLD] == 0
