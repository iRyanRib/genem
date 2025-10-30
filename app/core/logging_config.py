import logging
import sys
from typing import Optional
from datetime import datetime
import os


class ColoredFormatter(logging.Formatter):
    """Formatador colorido para logs no terminal."""
    
    # Códigos de cores ANSI
    COLORS = {
        'DEBUG': '\033[36m',    # Ciano
        'INFO': '\033[32m',     # Verde
        'WARNING': '\033[33m',  # Amarelo
        'ERROR': '\033[31m',    # Vermelho
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Adiciona cor baseada no nível
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Formata o log com cor
        record.levelname = f"{color}{record.levelname}{reset}"
        
        return super().format(record)


def setup_logging(
    log_level: str = "INFO",
    log_to_file: bool = False,
    log_file_path: Optional[str] = None,
    use_colors: bool = True
) -> logging.Logger:
    """
    Configura o sistema de logging para funcionar adequadamente no Docker.
    
    Args:
        log_level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Se deve salvar logs em arquivo
        log_file_path: Caminho do arquivo de log
        use_colors: Se deve usar cores no terminal
    
    Returns:
        Logger configurado
    """
    
    # Converte string para nível
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Remove handlers existentes
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Configura o logger raiz
    root_logger.setLevel(numeric_level)
    
    # Handler para stdout (essencial para Docker)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(numeric_level)
    
    # Formato do log
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    if use_colors and sys.stdout.isatty():
        # Usa formatador colorido se estiver em terminal
        formatter = ColoredFormatter(log_format)
    else:
        # Formatador simples para Docker/produção
        formatter = logging.Formatter(log_format)
    
    stdout_handler.setFormatter(formatter)
    root_logger.addHandler(stdout_handler)
    
    # Handler para arquivo (opcional)
    if log_to_file:
        if not log_file_path:
            log_file_path = f"logs/genem_{datetime.now().strftime('%Y%m%d')}.log"
        
        # Cria diretório se não existir
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setLevel(numeric_level)
        
        # Formato mais detalhado para arquivo
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Configurações específicas para Docker
    # Força flush imediato dos logs
    for handler in root_logger.handlers:
        handler.setStream(sys.stdout)
        if hasattr(handler.stream, 'reconfigure'):
            handler.stream.reconfigure(line_buffering=True)
    
    # Desabilita buffering de output para Docker
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
    
    # Logger específico da aplicação
    app_logger = logging.getLogger("genem")
    app_logger.setLevel(numeric_level)
    
    # Configurações para bibliotecas externas
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.INFO)
    
    app_logger.info(f"Sistema de logging configurado - Nível: {log_level}")
    
    return app_logger


def get_logger(name: str) -> logging.Logger:
    """
    Obtém um logger com o nome especificado.
    
    Args:
        name: Nome do logger (geralmente __name__)
    
    Returns:
        Logger configurado
    """
    return logging.getLogger(name)


# Configuração padrão para desenvolvimento
def setup_development_logging():
    """Configuração rápida para desenvolvimento."""
    return setup_logging(
        log_level="DEBUG",
        log_to_file=True,
        use_colors=True
    )


# Configuração padrão para produção/Docker
def setup_production_logging():
    """Configuração para produção/Docker."""
    return setup_logging(
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_to_file=False,  # No Docker, logs vão para stdout
        use_colors=False     # Sem cores no Docker
    )




