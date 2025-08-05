from discord.ext import commands


class WeeabooError(commands.CommandError):
    """Raised when a Bot related Errror occurs"""

    pass


class PlayerIsNotAvailable(WeeabooError):
    """Raised when the Lavalink Player is Not connected to a Voice Channel"""

    def __init__(self, message="❗ | The bot isn't connected to a VC", *args):
        super().__init__(message, *args)


class EconomyError(WeeabooError):
    """Raised when an economy cog error happens"""

    pass


class InvalidFunds(EconomyError):
    """Raised when the user has invalid funds in either the bank or wallet"""

    def __init__(self, message="⚠️ | You don't have enough funds to do that!", *args):
        super().__init__(message, *args)


class AccountNotFound(EconomyError):
    """Raised when the user does not have an account in the database"""

    def __init__(
        self,
        message="⚠️ | It looks like you don't have a wallet yet! One has been created for you, please rerun the command.",
        *args
    ):
        super().__init__(message, *args)
