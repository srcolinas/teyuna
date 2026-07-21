from collections.abc import Collection, Mapping

from ... import player
from ... import entities


class PlayerNotInTurnError(Exception):
    pass


def _sorted_coords(
    coords: Collection[entities.Coordinate],
) -> list[entities.Coordinate]:
    return sorted(coords)


class InvalidSettlementLocation(Exception):
    def __init__(
        self,
        *,
        target: entities.Coordinate,
        player: player.Nickname,
        free_vertices: Collection[entities.Coordinate],
        restricted_vertices: Collection[entities.Coordinate],
        existing_paths: Collection[entities.Coordinate] = (),
        existing_settlements: Mapping[entities.Coordinate, entities.SettlementType]
        | None = None,
        reason: str | None = None,
    ) -> None:
        self.target = target
        self.player = player
        self.free_vertices = free_vertices
        self.restricted_vertices = restricted_vertices
        self.existing_paths = existing_paths
        self.existing_settlements = existing_settlements
        self.reason = reason
        parts = [
            f"Player {player} cannot place settlement at {target}",
        ]
        if reason is not None:
            parts.append(reason)
        parts.append(f"free_vertices={_sorted_coords(free_vertices)}")
        parts.append(f"restricted_vertices={_sorted_coords(restricted_vertices)}")
        if existing_paths:
            parts.append(f"existing_paths={_sorted_coords(existing_paths)}")
        if existing_settlements is not None:
            settlements = {
                coord: settlement_type
                for coord, settlement_type in sorted(existing_settlements.items())
            }
            parts.append(f"existing_settlements={settlements}")
        super().__init__("; ".join(parts))


class InvalidPathLocation(Exception):
    def __init__(
        self,
        *,
        target: entities.Coordinate,
        player: player.Nickname,
        existing_settlements: Collection[entities.Coordinate],
        existing_paths: Collection[entities.Coordinate],
        free_edges: Collection[entities.Coordinate],
    ) -> None:
        self.target = target
        self.player = player
        self.existing_settlements = existing_settlements
        self.existing_paths = existing_paths
        self.free_edges = free_edges
        super().__init__(
            f"Player {player} cannot place path at {target}; "
            f"existing_settlements={_sorted_coords(existing_settlements)}; "
            f"existing_paths={_sorted_coords(existing_paths)}; "
            f"free_edges={_sorted_coords(free_edges)}"
        )


class InvalidConquistatorLocation(Exception):
    def __init__(
        self,
        *,
        target: entities.HexLocation,
        player: player.Nickname,
        current_location: entities.HexLocation,
    ) -> None:
        self.target = target
        self.player = player
        self.current_location = current_location
        super().__init__(
            f"Player {player} cannot move conquistator to {target}; "
            f"current_location={current_location}"
        )


class PlayerDoesNotHaveCardError(Exception):
    pass


class InsufficientResourceSupplyError(Exception):
    pass


class InsufficientResourcesError(Exception):
    pass


class EmptyWisdomDeckError(Exception):
    pass


class PlayerNotRequiredToDiscardError(Exception):
    pass


class InvalidDiscardCountError(Exception):
    pass


class TradeProposalNotFound(Exception):
    pass


class InvalidTradeTargets(Exception):
    pass


class TradeNotAddressedToPlayerError(Exception):
    pass
