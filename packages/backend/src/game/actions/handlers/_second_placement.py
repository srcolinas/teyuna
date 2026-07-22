import collections

from ... import player
from ... import entities
from . import _first_placement, _placement


def handle_second_placement(
    game: entities.Game, action: _first_placement.FreePlacementAction
) -> _first_placement.PlacedBuildingsResult:
    previous_phase = game.phase
    if game.active_player != action.by:
        return _first_placement.PlacedBuildingsResult(
            previous_phase=previous_phase,
            next_phase=game.phase,
            action=action,
            error=f"Player {action.by} is not in turn",
        )

    can = _placement.can_add_free_terrace_at(
        free_verticies=game.free_verticies,
        restricted_verticies=game.restricted_verticies,
        target=action.terrace,
    )
    if not can:
        return _first_placement.PlacedBuildingsResult(
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
        return _first_placement.PlacedBuildingsResult(
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

    game.use_vertex(action.by, action.terrace, entities.SettlementType.TERRACE)
    game.use_edge(action.by, action.path)
    _grant_resources_for_terrace(game, by=action.by, terrace=action.terrace)

    if game.player_idx == 0:
        game.phase = entities.GamePhaseName.DICE_ROLL
    else:
        game.player_idx -= 1
        game.phase = entities.GamePhaseName.SECOND_PLACEMENT
    return _first_placement.PlacedBuildingsResult(
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
    by: player.Nickname,
    terrace: entities.Coordinate,
) -> None:
    locs = entities.hex_locations_at_vertex(terrace.q, terrace.r, terrace.d)
    amount: entities.ResourceCount = collections.Counter()
    for hex_tile in game.map:
        if entities.HexLocation(q=hex_tile.q, r=hex_tile.r) not in locs:
            continue
        if hex_tile.type is entities.HexType.DESERT:
            continue
        resource = entities.HEX_TYPE_TO_RESOURCE[hex_tile.type]
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
