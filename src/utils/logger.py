import logging


def setup_logger():
    # Create a custom logger
    logger = logging.getLogger("weeb-bot")
    logger.setLevel(logging.DEBUG)

    # Create a console handler and set the level to debug
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # Create a formatter and set it for the console handler
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)

    # Add the console handler to the logger
    if not logger.handlers:  # Avoid adding multiple handlers
        logger.addHandler(console_handler)

    return logger
