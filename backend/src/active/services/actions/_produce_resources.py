import collections

from ... import entities


def produce_resources(
    game: entities.ActiveGame,
    *,
    roll: int,
) -> None:
    for hex_tile in game.map:
        if hex_tile.number != roll:
            continue
        if hex_tile.type is entities.HexType.DESERT:
            continue
        resource = _HEX_TYPE_TO_RESOURCE[hex_tile.type]
        for nickname in game.turn_order:
            settlements = game.players[nickname].settlements
            for direction in range(6):
                coord = entities.canonical_vertex(hex_tile.q, hex_tile.r, direction)
                if coord not in settlements:
                    continue
                settlement = settlements[coord]
                if settlement is entities.SettlementType.TERRACE:
                    amount = 1
                elif settlement is entities.SettlementType.GREAT_TERRACE:
                    amount = 2
                else:
                    continue
                granted = collections.Counter({resource: amount})
                game.players[nickname].resources += granted
                game.resource_supply -= granted


_HEX_TYPE_TO_RESOURCE: dict[entities.HexType, entities.ResourceCard] = {
    entities.HexType.MOUNTAINS: entities.ResourceCard.GOLD,
    entities.HexType.QUARRIES: entities.ResourceCard.STONE,
    entities.HexType.HIGHLANDS: entities.ResourceCard.COTTON,
    entities.HexType.VALLEYS: entities.ResourceCard.MAIZE,
    entities.HexType.JUNGLE: entities.ResourceCard.WOOD,
}
