import collections
import random

from src.active import entities, services


def test_produces_gives_1_resource_from_terrace() -> None:
    game = entities.ActiveGame(
        map=[
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
        ],
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
    game.set_game_phase(entities.GamePhase.MAIN)
    game.set_turn_phase(entities.TurnPhase.PRODUCTION)
    services.produce_resources(game, rnd=RandomGenerator(4))
    assert game.players["srcolinas-1"].resources[entities.ResourceCard.GOLD] == 1
    assert game.players["srcolinas-2"].resources[entities.ResourceCard.GOLD] == 0
    assert game.players["srcolinas-3"].resources[entities.ResourceCard.GOLD] == 0


def test_produces_gives_2_resources_from_great_terrace() -> None:
    game = entities.ActiveGame(
        map=[
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
        ],
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
    game.set_game_phase(entities.GamePhase.MAIN)
    game.set_turn_phase(entities.TurnPhase.PRODUCTION)
    services.produce_resources(game, rnd=RandomGenerator(4))
    assert game.players["srcolinas-1"].resources[entities.ResourceCard.GOLD] == 2
    assert game.players["srcolinas-2"].resources[entities.ResourceCard.GOLD] == 0
    assert game.players["srcolinas-3"].resources[entities.ResourceCard.GOLD] == 0


def test_moves_turn_phase_to_trade() -> None:
    game = entities.ActiveGame(
        map=[
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
        ],
        conquistator_location=entities.Hex(
            q=0,
            r=1,
            type=entities.HexType.DESERT,
            number=7,
        ),
        turn_order=("srcolinas-1", "srcolinas-2", "srcolinas-3"),
        players={
            "srcolinas-1": entities.Player(),
            "srcolinas-2": entities.Player(),
            "srcolinas-3": entities.Player(),
        },
    )
    game.set_game_phase(entities.GamePhase.MAIN)
    game.set_turn_phase(entities.TurnPhase.PRODUCTION)
    services.produce_resources(game, rnd=RandomGenerator(4))
    assert game.turn_phase is entities.TurnPhase.TRADE


class RandomGenerator(random.Random):
    def __init__(self, constant: int) -> None:
        super().__init__()
        self._constant = constant

    def randint(self, a: int, b: int) -> int:
        return self._constant
