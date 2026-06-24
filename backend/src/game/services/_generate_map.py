import random

from .. import entities


def generate_map() -> entities.Map:
    types = (
        [entities.HexType.MOUNTAINS] * 3
        + [entities.HexType.QUARRIES] * 3
        + [entities.HexType.HIGHLANDS] * 4
        + [entities.HexType.VALLEYS] * 4
        + [entities.HexType.JUNGLE] * 4
        + [entities.HexType.DESERT]
    )
    random.shuffle(types)

    numbers = [2, 12] + [3, 4, 5, 6, 8, 9, 10, 11] * 2
    random.shuffle(numbers)

    map = []
    for q in range(-2, 3):
        for r in range(-2, 3):
            try:
                coord = entities.HexCoordinate(q=q, r=r)
            except ValueError:
                continue
            type = types.pop()
            number = 7 if type is entities.HexType.DESERT else numbers.pop()
            map.append(
                entities.Hex(
                    coordinate=coord,
                    type=type,
                    number=number,
                )
            )

    return map
