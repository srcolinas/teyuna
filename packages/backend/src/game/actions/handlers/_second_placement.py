import collections

import teyuna_shared

from ... import entities
from .. import timeouts
from . import _placement


def handle_second_placement(
    game: entities.Game, action: teyuna_shared.FreePlacementAction
) -> teyuna_shared.PlacedBuildingsResult:
    previous_phase = game.phase
    if game.active_player != action.by:
        return teyuna_shared.PlacedBuildingsResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=f"Player {action.by} is not in turn",
        )

    action = timeouts.resolve_free_placement(
        game,
        action.rng_,
        by=action.by,
        terrace=action.terrace,
        path=action.path,
        due_to_timeout=action.due_to_timeout,
    )
    if action.terrace is None or action.path is None:
        return teyuna_shared.PlacedBuildingsResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error="Could not resolve a legal free placement",
        )

    can = _placement.can_add_free_terrace_at(
        free_verticies=game.free_verticies,
        restricted_verticies=game.restricted_verticies,
        target=action.terrace,
    )
    if not can:
        return teyuna_shared.PlacedBuildingsResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=_placement.format_invalid_settlement_location(
                target=action.terrace,
                player=action.by,
                free_vertices=game.free_verticies,
                restricted_vertices=game.restricted_verticies,
            ),
        )

    player_state = game.players[action.by]
    can = _placement.can_add_free_path_at(
        target=action.path,
        free_edges=game.free_edges,
        existing_settlements=player_state.settlements.locations(),
        existing_paths=player_state.paths,
        free_vertices=game.free_verticies,
        new_settlement=action.terrace,
    )
    if not can:
        return teyuna_shared.PlacedBuildingsResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=_placement.format_invalid_path_location(
                target=action.path,
                player=action.by,
                existing_settlements=player_state.settlements.locations(),
                existing_paths=player_state.paths,
                free_edges=game.free_edges,
            ),
        )

    game.use_vertex(action.by, action.terrace, teyuna_shared.SettlementType.TERRACE)
    game.use_edge(action.by, action.path)
    _grant_resources_for_terrace(game, by=action.by, terrace=action.terrace)

    if game.player_idx == 0:
        game.phase = teyuna_shared.GamePhaseName.DICE_ROLL
    else:
        game.player_idx -= 1
        game.phase = teyuna_shared.GamePhaseName.SECOND_PLACEMENT
    return teyuna_shared.PlacedBuildingsResult(
        previous_phase=previous_phase,
        next_phase=game.phase,
        action=action,
        settlement=action.terrace,
        path=action.path,
        next_player=game.active_player,
    )


def _grant_resources_for_terrace(
    game: entities.Game,
    *,
    by: str,
    terrace: teyuna_shared.Coordinate,
) -> None:
    locs = teyuna_shared.hex_locations_at_vertex(terrace.q, terrace.r, terrace.d)
    amount: collections.Counter[teyuna_shared.ResourceCard] = collections.Counter()
    for hex_tile in game.map:
        if teyuna_shared.HexLocation(q=hex_tile.q, r=hex_tile.r) not in locs:
            continue
        if hex_tile.type is teyuna_shared.HexType.DESERT:
            continue
        resource = teyuna_shared.HEX_TYPE_TO_RESOURCE[hex_tile.type]
        amount[resource] += 1
    to_grant = collections.Counter(
        {
            resource: granted
            for resource, count in amount.items()
            if (granted := min(count, game.resource_supply[resource])) > 0
        }
    )
    if to_grant:
        game.take_from_supply(to=by, amount=to_grant)
