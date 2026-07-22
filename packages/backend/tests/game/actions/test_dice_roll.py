import collections
import datetime
import random

from src.game import actions, entities


def test_raises_when_player_not_in_turn(game: entities.Game) -> None:
    other = game.turn_order[1]
    result = actions.handle_dice_roll(
        game,
        actions.PlayerAction(
            by=other,
            rng_=FixedRandom([1, 1]),
        ),
    )
    assert result.error == f"Player {other} is not in turn"
    assert result.die_1 == -1
    assert result.die_2 == -1
    assert result.to_discard == {}
    assert result.produced == {}


def test_rolls_seven_with_no_discards_moves_to_move_conquistator(
    game: entities.Game,
) -> None:
    game.player_idx = 0
    player = game.active_player

    result = actions.handle_dice_roll(
        game,
        actions.PlayerAction(by=player, rng_=FixedRandom([3, 4])),
    )

    assert result.error is None
    assert result.next_phase is entities.GamePhaseName.MOVE_CONQUISTATOR
    assert result.die_1 == 3
    assert result.die_2 == 4
    assert result.to_discard == {}
    assert result.produced == {}
    assert game.to_discard_resources == {}
    assert game.player_idx == 0
    assert game.active_player == player


def test_rolls_seven_with_players_over_seven_moves_to_discard_resources(
    game: entities.Game,
) -> None:
    game.player_idx = 0
    player = game.active_player
    over_limit = game.turn_order[1]
    under_limit = game.turn_order[2]
    game.players[over_limit].resources = collections.Counter(
        {entities.ResourceCard.WOOD: 8}
    )
    game.players[under_limit].resources = collections.Counter(
        {entities.ResourceCard.WOOD: 7}
    )

    result = actions.handle_dice_roll(
        game,
        actions.PlayerAction(by=player, rng_=FixedRandom([3, 4])),
    )

    assert result.error is None
    assert result.next_phase is entities.GamePhaseName.DISCARD_RESOURCES
    assert result.die_1 == 3
    assert result.die_2 == 4
    assert result.to_discard == {over_limit: 4}
    assert result.produced == {}
    assert game.to_discard_resources == {over_limit: 4}


def test_rolls_non_seven_moves_to_trade_and_build(
    game: entities.Game,
) -> None:
    game.player_idx = 0
    player = game.active_player

    result = actions.handle_dice_roll(
        game,
        actions.PlayerAction(by=player, rng_=FixedRandom([2, 3])),
    )

    assert result.error is None
    assert result.next_phase is entities.GamePhaseName.TRADE_AND_BUILD
    assert result.die_1 == 2
    assert result.die_2 == 3
    assert result.to_discard == {}
    assert result.produced == {}
    assert game.player_idx == 0
    assert game.active_player == player


def test_produces_one_resource_from_terrace() -> None:
    game = _mountains_game(
        settlements={
            0: _settlements(
                {entities.Coordinate(q=0, r=-1, d=2): entities.SettlementType.TERRACE}
            ),
        },
    )
    active = game.active_player
    other = game.turn_order[1]

    result = actions.handle_dice_roll(
        game,
        actions.PlayerAction(by=active, rng_=FixedRandom([3, 5])),
    )

    assert result.error is None
    assert result.next_phase is entities.GamePhaseName.TRADE_AND_BUILD
    assert result.die_1 == 3
    assert result.die_2 == 5
    assert result.to_discard == {}
    assert result.produced == {active: {entities.ResourceCard.GOLD: 1}}
    assert game.players[active].resources[entities.ResourceCard.GOLD] == 1
    assert game.players[other].resources[entities.ResourceCard.GOLD] == 0
    assert game.resource_supply[entities.ResourceCard.GOLD] == 18


def test_produces_two_resources_from_great_terrace() -> None:
    game = _mountains_game(
        settlements={
            0: _settlements(
                {
                    entities.Coordinate(
                        q=0, r=-1, d=2
                    ): entities.SettlementType.GREAT_TERRACE,
                }
            ),
        },
    )
    active = game.active_player

    result = actions.handle_dice_roll(
        game,
        actions.PlayerAction(by=active, rng_=FixedRandom([3, 5])),
    )

    assert result.error is None
    assert result.next_phase is entities.GamePhaseName.TRADE_AND_BUILD
    assert result.die_1 == 3
    assert result.die_2 == 5
    assert result.to_discard == {}
    assert result.produced == {active: {entities.ResourceCard.GOLD: 2}}
    assert game.players[active].resources[entities.ResourceCard.GOLD] == 2
    assert game.resource_supply[entities.ResourceCard.GOLD] == 17


def test_does_not_grant_when_supply_is_empty() -> None:
    game = _mountains_game(
        settlements={
            0: _settlements(
                {entities.Coordinate(q=0, r=-1, d=2): entities.SettlementType.TERRACE}
            ),
        },
        supply_gold=0,
    )
    active = game.active_player

    result = actions.handle_dice_roll(
        game,
        actions.PlayerAction(by=active, rng_=FixedRandom([3, 5])),
    )

    assert result.error is None
    assert result.next_phase is entities.GamePhaseName.TRADE_AND_BUILD
    assert result.die_1 == 3
    assert result.die_2 == 5
    assert result.to_discard == {}
    assert result.produced == {}
    assert game.players[active].resources[entities.ResourceCard.GOLD] == 0
    assert game.resource_supply[entities.ResourceCard.GOLD] == 0


def test_grants_partial_when_supply_has_less_than_requested() -> None:
    game = _mountains_game(
        settlements={
            0: _settlements(
                {
                    entities.Coordinate(
                        q=0, r=-1, d=2
                    ): entities.SettlementType.GREAT_TERRACE,
                }
            ),
        },
        supply_gold=1,
    )
    active = game.active_player

    result = actions.handle_dice_roll(
        game,
        actions.PlayerAction(by=active, rng_=FixedRandom([3, 5])),
    )

    assert result.error is None
    assert result.next_phase is entities.GamePhaseName.TRADE_AND_BUILD
    assert result.die_1 == 3
    assert result.die_2 == 5
    assert result.to_discard == {}
    assert result.produced == {active: {entities.ResourceCard.GOLD: 1}}
    assert game.players[active].resources[entities.ResourceCard.GOLD] == 1
    assert game.resource_supply[entities.ResourceCard.GOLD] == 0


def test_turn_order_gets_remaining_supply_first() -> None:
    game = _mountains_game(
        settlements={
            0: _settlements(
                {entities.Coordinate(q=0, r=-1, d=2): entities.SettlementType.TERRACE}
            ),
            1: _settlements(
                {entities.Coordinate(q=0, r=0, d=1): entities.SettlementType.TERRACE}
            ),
        },
        supply_gold=1,
    )
    active = game.active_player
    next_in_order = game.turn_order[1]

    result = actions.handle_dice_roll(
        game,
        actions.PlayerAction(by=active, rng_=FixedRandom([3, 5])),
    )

    assert result.error is None
    assert result.next_phase is entities.GamePhaseName.TRADE_AND_BUILD
    assert result.die_1 == 3
    assert result.die_2 == 5
    assert result.to_discard == {}
    assert result.produced == {active: {entities.ResourceCard.GOLD: 1}}
    assert game.players[active].resources[entities.ResourceCard.GOLD] == 1
    assert game.players[next_in_order].resources[entities.ResourceCard.GOLD] == 0
    assert game.resource_supply[entities.ResourceCard.GOLD] == 0


def test_does_not_produce_from_conquistator_hex() -> None:
    game = _mountains_game(
        settlements={
            0: _settlements(
                {entities.Coordinate(q=0, r=-1, d=2): entities.SettlementType.TERRACE}
            ),
        },
    )
    active = game.active_player
    game.conquistator_location = entities.HexLocation(q=0, r=0)

    result = actions.handle_dice_roll(
        game,
        actions.PlayerAction(by=active, rng_=FixedRandom([3, 5])),
    )

    assert result.error is None
    assert result.next_phase is entities.GamePhaseName.TRADE_AND_BUILD
    assert result.die_1 == 3
    assert result.die_2 == 5
    assert result.to_discard == {}
    assert result.produced == {}
    assert game.players[active].resources[entities.ResourceCard.GOLD] == 0
    assert game.resource_supply[entities.ResourceCard.GOLD] == 19


def test_does_not_produce_from_desert_or_non_matching_roll() -> None:
    game = entities.Game(
        map=(
            entities.Hex(q=0, r=0, type=entities.HexType.DESERT, number=5),
            entities.Hex(q=1, r=0, type=entities.HexType.MOUNTAINS, number=8),
        ),
        conquistator_location=entities.HexLocation(q=0, r=1),
        players={
            "player-0": entities.Player(),
            "player-1": entities.Player(),
            "player-2": entities.Player(),
        },
        available_slots=0,
    )
    game.start(datetime.timedelta(seconds=60))
    active = game.active_player
    game.players[active].settlements = _settlements(
        {
            entities.Coordinate(q=0, r=-1, d=2): entities.SettlementType.TERRACE,
            entities.Coordinate(q=1, r=-1, d=2): entities.SettlementType.TERRACE,
        }
    )

    result = actions.handle_dice_roll(
        game,
        actions.PlayerAction(by=active, rng_=FixedRandom([2, 3])),
    )

    assert result.error is None
    assert result.next_phase is entities.GamePhaseName.TRADE_AND_BUILD
    assert result.die_1 == 2
    assert result.die_2 == 3
    assert result.to_discard == {}
    assert result.produced == {}
    assert game.players[active].resources[entities.ResourceCard.GOLD] == 0
    assert game.resource_supply[entities.ResourceCard.GOLD] == 19


def _settlements(
    locations: dict[entities.Coordinate, entities.SettlementType],
) -> entities.SettlementsCollection:
    settlements = entities.SettlementsCollection()
    for coord, settlement_type in locations.items():
        settlements[coord] = settlement_type
    return settlements


def _mountains_game(
    *,
    settlements: dict[int, entities.SettlementsCollection],
    supply_gold: int | None = None,
) -> entities.Game:
    nicknames = ("player-0", "player-1", "player-2")
    game = entities.Game(
        map=(
            entities.Hex(q=0, r=0, type=entities.HexType.MOUNTAINS, number=8),
            entities.Hex(q=0, r=1, type=entities.HexType.DESERT, number=7),
        ),
        conquistator_location=entities.HexLocation(q=0, r=1),
        players={nickname: entities.Player() for nickname in nicknames},
        available_slots=0,
    )
    game.start(datetime.timedelta(seconds=60))
    for turn_index, settlement_collection in settlements.items():
        game.players[game.turn_order[turn_index]].settlements = settlement_collection
    if supply_gold is not None:
        game.resource_supply[entities.ResourceCard.GOLD] = supply_gold
    return game


class FixedRandom(random.Random):
    def __init__(self, values: list[int]) -> None:
        super().__init__()
        self._values = iter(values)

    def randint(self, a: int, b: int) -> int:
        value = next(self._values)
        assert a <= value <= b
        return value
