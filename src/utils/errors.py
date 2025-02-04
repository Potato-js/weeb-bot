from discord.ext import commands


class WeeabooError(commands.CommandError):
    """Raised when a Bot related Errror occurs"""

    pass


class MissingParameter(WeeabooError):
    """Raised when there is a missing parameter"""

    def __init__(self, parameter_name: str, message: str = None):
        self.parameter_name = parameter_name

        if message is None:
            message = f"Missing required parameter: {parameter_name}"

        super().__init__(message)


class InvalidParameter(WeeabooError):
    """Raised when there is a missing parameter"""

    pass


class PlayerIsNotAvailable(WeeabooError):
    """Raised when the Lavalink Player is Not connected to a Voice Channel"""

    def __init__(self, message="❗ | The bot isn't connected to a VC", *args):
        super().__init__(message, *args)
