from typing import Iterable

import teyuna_core


def overwrite_map(
    *,
    source: Iterable[teyuna_core.MapHex],
    overwrites: dict[teyuna_core.HexLocation, tuple[teyuna_core.HexType, int]],
) -> tuple[teyuna_core.MapHex, ...]:
    result: list[teyuna_core.MapHex] = []
    for hex_tile in source:
        key = teyuna_core.HexLocation(q=hex_tile.q, r=hex_tile.r)
        if key in overwrites:
            hex_type, number = overwrites[key]
            result.append(
                teyuna_core.MapHex(
                    q=hex_tile.q, r=hex_tile.r, type=hex_type, number=number
                )
            )
        else:
            result.append(hex_tile)

    return tuple(result)
