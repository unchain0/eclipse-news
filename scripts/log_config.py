import logging
import sys


def setup_logging(
    level=logging.INFO,
    format_string="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
):
    """Configura o logging básico para a aplicação."""
    # Usar sys.stdout para garantir que a saída vá para o console padrão
    # Isso pode ser útil em ambientes onde a saída padrão é redirecionada
    logging.basicConfig(level=level, format=format_string, stream=sys.stdout)
    # Silenciar logs de bibliotecas de terceiros, se necessário
    # logging.getLogger("requests").setLevel(logging.WARNING)
    # logging.getLogger("urllib3").setLevel(logging.WARNING)
