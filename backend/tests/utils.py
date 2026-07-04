import datetime
import uuid

from src import active, proposed


def create_game_and_add_players(
    *,
    active_repository: active.InMemoryActiveGameRepository,
    max_players: int = 3,
    players_to_add: int = 3,
    usernames: list[str] | None = None,
) -> uuid.UUID:
    proposed_repository = proposed.InMemoryProposedGameRepository()
    manager = active.GameManager(active_repository)

    proposed_game_id = proposed_repository.add(
        num_players=max_players,
        expires_at=datetime.datetime.now() + datetime.timedelta(seconds=1),
    ).id

    if usernames is None:
        usernames = [f"srcolinas-{i}" for i in range(players_to_add)]

    active_game_id: uuid.UUID | None = None
    for i in range(players_to_add):
        result = proposed.add_player(
            game_id=proposed_game_id,
            username=usernames[i],
            repository=proposed_repository,
            manager=manager,
        )
        if result.game is not None:
            active_game_id = result.game

    assert active_game_id is not None
    return active_game_id
