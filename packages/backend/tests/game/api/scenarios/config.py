from typing import Iterable

import teyuna_shared


def overwrite_map(
    *,
    source: Iterable[teyuna_shared.MapHex],
    overwrites: dict[teyuna_shared.HexLocation, tuple[teyuna_shared.HexType, int]],
) -> tuple[teyuna_shared.MapHex, ...]:
    result: list[teyuna_shared.MapHex] = []
    for hex_tile in source:
        key = teyuna_shared.HexLocation(q=hex_tile.q, r=hex_tile.r)
        if key in overwrites:
            hex_type, number = overwrites[key]
            result.append(
                teyuna_shared.MapHex(
                    q=hex_tile.q, r=hex_tile.r, type=hex_type, number=number
                )
            )
        else:
            result.append(hex_tile)

    return tuple(result)
