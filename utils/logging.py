import logging

def setup_logger():
    logger = logging.getLogger("reservoir_agent")
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    

    logger.addHandler(handler)
    return logger

logger = setup_logger()
