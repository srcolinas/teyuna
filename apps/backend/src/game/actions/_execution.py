import dataclasses
import random


@dataclasses.dataclass(frozen=True, slots=True)
class ExecutionContext:
    by: str
    due_to_timeout: bool
    rng: random.Random
