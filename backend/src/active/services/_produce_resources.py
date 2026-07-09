import collections

from .. import entities, _map
from . import _errors

_HEX_TYPE_TO_RESOURCE: dict[entities.HexType, entities.ResourceCard] = {
    entities.HexType.MOUNTAINS: entities.ResourceCard.GOLD,
    entities.HexType.QUARRIES: entities.ResourceCard.STONE,
    entities.HexType.HIGHLANDS: entities.ResourceCard.COTTON,
    entities.HexType.VALLEYS: entities.ResourceCard.MAIZE,
    entities.HexType.JUNGLE: entities.ResourceCard.WOOD,
}


def produce_resources(game: entities.ActiveGame) -> None:
    if game.phase is not entities.GamePhase.MAIN:
        raise _errors.InvalidGamePhase

    # TODO: improve performance by using a differnet data structure
    # to represent the map and figure out which players benefit
    # from the production roll more efficiently.
    roll_1, roll_2 = game._rnd.randint(1, 6), game._rnd.randint(1, 6)
    total = roll_1 + roll_2
    for hex in game.map:
        if hex.number == total:
            if hex.type is not entities.HexType.DESERT:
                resource = _HEX_TYPE_TO_RESOURCE[hex.type]
                for p in game.turn_order:
                    settlements = game.players[p].settlements
                    for i in range(6):
                        coord = _map.canonical_vertex(hex.q, hex.r, i)
                        if coord not in settlements:
                            continue
                        if settlements[coord] is entities.SettlementType.TERRACE:
                            game.grant_resources(
                                p, resources=collections.Counter({resource: 1})
                            )
                        elif (
                            settlements[coord] is entities.SettlementType.GREAT_TERRACE
                        ):
                            game.grant_resources(
                                p, resources=collections.Counter({resource: 2})
                            )
