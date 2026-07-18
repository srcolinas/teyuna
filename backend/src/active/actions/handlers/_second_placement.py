import collections

from .... import player
from ... import entities
from .. import _registry
from . import _errors, _first_placement, _placement


def handle_second_placement(
    game: entities.ActiveGame, action: _first_placement.FreePlacementAction
) -> _registry.GamePhaseName:
    if game.active_player != action.by:
        raise _errors.PlayerNotInTurnError(f"Player {action.by} is not in turn")

    can = _placement.can_add_free_terrace_at(
        free_verticies=game.free_verticies,
        restricted_verticies=game.restricted_verticies,
        target=action.terrace,
    )
    if not can:
        raise _errors.InvalidSettlementLocation(
            f"Cannot add free terrace at {action.terrace}"
        )

    can = _placement.can_add_free_path_at(
        target=action.path,
        free_edges=game.free_edges,
        existing_settlements={
            *game.players[action.by].settlements.locations(),
            action.terrace,
        },
        existing_paths=game.players[action.by].paths,
        free_vertices=game.free_verticies,
    )
    if not can:
        raise _errors.InvalidPathLocation(f"Cannot add free path at {action.path}")

    game.use_vertex(action.by, action.terrace, entities.SettlementType.TERRACE)
    game.use_edge(action.by, action.path)
    _grant_resources_for_terrace(game, by=action.by, terrace=action.terrace)

    if game.player_idx > 0:
        game.player_idx -= 1
        return _registry.GamePhaseName.SECOND_PLACEMENT
    return _registry.GamePhaseName.DICE_ROLL


def _grant_resources_for_terrace(
    game: entities.ActiveGame,
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
