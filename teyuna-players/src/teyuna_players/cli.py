import argparse
import uuid

from . import builder, skipper, sleepy, loop


def main() -> None:
    parser = argparse.ArgumentParser("Creates up to 4 players to play a game of Teyuna")
    parser.add_argument(
        "--game-id",
        type=uuid.UUID | None,
        default=None,
        help="if not provided, a new game will be created. If provided, the players will join the existing game.",
    )
    parser.add_argument(
        "players",
        nargs="*",
        default=["builder"] * 3,
        help="names of the agents to play with. If not provided, a dumb player will be created.",
    )
    args = parser.parse_args()


_PLAYERS = {
    "sleepy": sleepy.SleepyPlayer,
    "skipper": skipper.SkipperPlayer,
    "builder": builder.BuilderPlayer,
}
