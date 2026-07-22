import functools
import secrets
from collections.abc import Callable

type Token = str
type Nickname = str


class PlayerAuthenticationService:
    def __init__(
        self, token_generator: Callable[[], Token] = secrets.token_hex
    ) -> None:
        self._memory: dict[Token, Nickname] = {}
        self._token_generator = token_generator

    def add(self, nickname: Nickname) -> Token:
        s = self._token_generator()
        while s in self._memory:
            s = self._token_generator()
        self._memory[s] = nickname
        return s

    def retrieve(self, token: Token) -> Nickname | None:
        return self._memory.get(token)


@functools.cache
def service() -> PlayerAuthenticationService:
    return PlayerAuthenticationService()
