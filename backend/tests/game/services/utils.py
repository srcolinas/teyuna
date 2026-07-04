import datetime
import uuid


from src.game import repository, services


def create_game_and_add_players(
    *,
    repository_: repository.InMemoryRepository,
    max_players: int = 3,
    players_to_add: int = 3,
    usernames: list[str] | None = None,
) -> uuid.UUID:
    game_id = repository_.add(
        num_players=max_players,
        expires_at=datetime.datetime.now() + datetime.timedelta(seconds=1),
    ).id

    if usernames is None:
        usernames = [f"srcolinas-{i}" for i in range(players_to_add)]

    for i in range(players_to_add):
        services.add_player(
            game_id=game_id, username=usernames[i], repository=repository_
        )
    return game_id
