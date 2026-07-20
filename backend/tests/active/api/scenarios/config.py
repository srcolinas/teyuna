from typing import Iterable

from src.active import entities


def overwrite_map(
    *,
    source: Iterable[entities.Hex],
    overwrites: dict[entities.HexLocation, tuple[entities.HexType, int]],
) -> tuple[entities.Hex, ...]:
    result: list[entities.Hex] = []
    for hex_tile in source:
        key = entities.HexLocation(q=hex_tile.q, r=hex_tile.r)
        if key in overwrites:
            hex_type, number = overwrites[key]
            result.append(
                entities.Hex(q=hex_tile.q, r=hex_tile.r, type=hex_type, number=number)
            )
        else:
            result.append(hex_tile)

    return tuple(result)
