import collections

from src.active import entities
from src.active.services import actions


def _mountains_game(
    *,
    settlements: dict[str, entities.SettlementsCollection],
    supply_gold: int | None = None,
) -> entities.ActiveGame:
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
                settlements=settlements.get(
                    "srcolinas-1", entities.SettlementsCollection()
                ),
            ),
            "srcolinas-2": entities.Player(
                resources=collections.Counter({entities.ResourceCard.GOLD: 0}),
                settlements=settlements.get(
                    "srcolinas-2", entities.SettlementsCollection()
                ),
            ),
            "srcolinas-3": entities.Player(
                resources=collections.Counter({entities.ResourceCard.GOLD: 0}),
                settlements=settlements.get(
                    "srcolinas-3", entities.SettlementsCollection()
                ),
            ),
        },
    )
    if supply_gold is not None:
        game.resource_supply[entities.ResourceCard.GOLD] = supply_gold
    return game


def test_produces_gives_1_resource_from_terrace() -> None:
    game = _mountains_game(
        settlements={
            "srcolinas-1": entities.SettlementsCollection(
                {
                    entities.Coordinate(
                        q=0, r=-1, d=2
                    ): entities.SettlementType.TERRACE,
                },
            ),
        },
    )
    actions.produce_resources(game, roll=8)
    assert game.players["srcolinas-1"].resources[entities.ResourceCard.GOLD] == 1
    assert game.players["srcolinas-2"].resources[entities.ResourceCard.GOLD] == 0
    assert game.players["srcolinas-3"].resources[entities.ResourceCard.GOLD] == 0
    assert game.resource_supply[entities.ResourceCard.GOLD] == 18


def test_produces_gives_2_resources_from_great_terrace() -> None:
    game = _mountains_game(
        settlements={
            "srcolinas-1": entities.SettlementsCollection(
                {
                    entities.Coordinate(
                        q=0, r=-1, d=2
                    ): entities.SettlementType.GREAT_TERRACE,
                },
            ),
        },
    )
    actions.produce_resources(game, roll=8)
    assert game.players["srcolinas-1"].resources[entities.ResourceCard.GOLD] == 2
    assert game.players["srcolinas-2"].resources[entities.ResourceCard.GOLD] == 0
    assert game.players["srcolinas-3"].resources[entities.ResourceCard.GOLD] == 0
    assert game.resource_supply[entities.ResourceCard.GOLD] == 17


def test_does_not_grant_when_supply_is_empty() -> None:
    game = _mountains_game(
        settlements={
            "srcolinas-1": entities.SettlementsCollection(
                {
                    entities.Coordinate(
                        q=0, r=-1, d=2
                    ): entities.SettlementType.TERRACE,
                },
            ),
        },
        supply_gold=0,
    )
    actions.produce_resources(game, roll=8)
    assert game.players["srcolinas-1"].resources[entities.ResourceCard.GOLD] == 0
    assert game.resource_supply[entities.ResourceCard.GOLD] == 0


def test_grants_partial_when_supply_has_less_than_requested() -> None:
    game = _mountains_game(
        settlements={
            "srcolinas-1": entities.SettlementsCollection(
                {
                    entities.Coordinate(
                        q=0, r=-1, d=2
                    ): entities.SettlementType.GREAT_TERRACE,
                },
            ),
        },
        supply_gold=1,
    )
    actions.produce_resources(game, roll=8)
    assert game.players["srcolinas-1"].resources[entities.ResourceCard.GOLD] == 1
    assert game.resource_supply[entities.ResourceCard.GOLD] == 0


def test_turn_order_gets_remaining_supply_first() -> None:
    vertex = entities.Coordinate(q=0, r=-1, d=2)
    other_vertex = entities.Coordinate(q=0, r=0, d=1)
    game = _mountains_game(
        settlements={
            "srcolinas-1": entities.SettlementsCollection(
                {vertex: entities.SettlementType.TERRACE},
            ),
            "srcolinas-2": entities.SettlementsCollection(
                {other_vertex: entities.SettlementType.TERRACE},
            ),
        },
        supply_gold=1,
    )
    actions.produce_resources(game, roll=8)
    assert game.players["srcolinas-1"].resources[entities.ResourceCard.GOLD] == 1
    assert game.players["srcolinas-2"].resources[entities.ResourceCard.GOLD] == 0
    assert game.resource_supply[entities.ResourceCard.GOLD] == 0
