import logging
import sys
import platform

# Color constants
RESET_COLOR = '\033[0m'
WHITE_COLOR = '\033[37m'  # Default white color

# Color mapping dictionary
LOG_COLORS = {
    'SCHEDULER': '\033[94m',  # blue
    'DID_FIND_BURST': '\033[95m',  # magenta
}

# Logger color detection
def get_logger_color(title: str):
    """
    Get color code for logger title.
    Returns white color if title is not in LOG_COLORS dictionary.
    """
    return LOG_COLORS.get(title, WHITE_COLOR)


def set_logger(title: str):
    if platform.system() == "Windows":
        use_windows_logging = False
    else:
        use_windows_logging = False

    logger = logging.getLogger(title)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        # handler = logging.StreamHandler()
        # Only log to stdout since tee will handle writing to file
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(f'%(asctime)s - {get_logger_color(title)}%(name)15s - %(levelname)s - %(message)s{RESET_COLOR}')
        handler.setFormatter(formatter)
        # Prevent propagation to avoid duplicate logging(specially for linux)
        logger.propagate = use_windows_logging
        logger.addHandler(handler)

    return logger