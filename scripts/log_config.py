import logging
import sys


def setup_logging(
    level=logging.INFO,
    format_string="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
):
    """Configura o logging básico para a aplicação."""
    logging.basicConfig(level=level, format=format_string, stream=sys.stdout)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
