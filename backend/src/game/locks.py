import threading
import uuid


class GameLockManager:
    def __init__(self) -> None:
        self._locks: dict[uuid.UUID, threading.Lock] = {}
        self._meta = threading.Lock()

    def lock_for(self, game_id: uuid.UUID) -> threading.Lock:
        with self._meta:
            lock = self._locks.get(game_id)
            if lock is None:
                lock = threading.Lock()
                self._locks[game_id] = lock
            return lock
