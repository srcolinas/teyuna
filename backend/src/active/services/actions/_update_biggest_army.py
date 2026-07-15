from .... import player
from ... import entities

_MIN_BIGGEST_ARMY: int = 3


def update_biggest_army(
    game: entities.ActiveGame,
    by: player.Nickname,
    /,
) -> tuple[player.Nickname, int] | None:
    """Update biggest army after ``by`` plays a warrior.

    Returns ``(owner, count)`` when the biggest-army holder changes,
    otherwise ``None``. Count-only updates for the current holder are
    applied silently.
    """
    count = game.players[by].played_cards[entities.WisdomCard.WARRIOR]
    if count < _MIN_BIGGEST_ARMY:
        return None

    holder, stored = game.biggest_army
    # Strictly more than the stored record — including an unassigned tie count.
    if count > stored:
        game.biggest_army = (by, count)
        if holder != by:
            return (by, count)
    return None
