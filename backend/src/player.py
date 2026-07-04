import functools
import secrets

type Token = str
type Nickname = str


class PlayerAuthenticationService:
    def __init__(self) -> None:
        self._memory: dict[Token, Nickname] = {}

    def add(self, nickname: Nickname) -> Token:
        s = secrets.token_hex()
        while s in self._memory:
            s = secrets.token_hex()
        self._memory[s] = nickname
        return s

    def retrieve(self, token: Token) -> Nickname | None:
        return self._memory.get(token)


@functools.cache
def service() -> PlayerAuthenticationService:
    return PlayerAuthenticationService()
