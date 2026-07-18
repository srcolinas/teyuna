class PlayerNotInTurnError(Exception):
    pass


class InvalidSettlementLocation(Exception):
    pass


class InvalidPathLocation(Exception):
    pass


class InvalidConquistatorLocation(Exception):
    pass


class PlayerDoesNotHaveCardError(Exception):
    pass


class InsufficientResourceSupplyError(Exception):
    pass


class InsufficientResourcesError(Exception):
    pass


class EmptyWisdomDeckError(Exception):
    pass


class PlayerNotRequiredToDiscardError(Exception):
    pass


class InvalidDiscardCountError(Exception):
    pass


class TradeProposalNotFound(Exception):
    pass


class InvalidTradeTargets(Exception):
    pass


class TradeNotAddressedToPlayerError(Exception):
    pass
