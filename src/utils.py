import logging
import time
import colorlog
import os

def configurar_logs():
    """
    Configura o sistema de logs:
    - Arquivo: Salva tudo em data/logs/scraping.log (sem cores, formato completo).
    - Terminal: Mostra no cmd/vscode (com cores, formato resumido).
    """
    # 1. Garante que a pasta existe
    if not os.path.exists('data/logs'):
        os.makedirs('data/logs')
    
    # 2. Pega o Logger Raiz (Root) e define o nível global
    logger = logging.getLogger()
    
    # Limpa handlers anteriores para evitar duplicação se a função for chamada 2x
    if logger.hasHandlers():
        logger.handlers.clear()
        
    logger.setLevel(logging.INFO)

    # --- HANDLER 1: ARQUIVO (Texto Puro, Completo) ---
    # Aqui não usamos cores, pois arquivos de texto não leem cores ANSI bem.
    file_handler = logging.FileHandler("data/logs/scraping.log", encoding='utf-8')
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # --- HANDLER 2: TERMINAL (Colorido e Bonito) ---
    console_handler = logging.StreamHandler()
    console_formatter = colorlog.ColoredFormatter(
        "%(cyan)s%(asctime)s%(reset)s - %(log_color)s%(levelname)-8s%(reset)s - %(message)s",
        datefmt='%H:%M:%S', # No terminal, só a hora basta (economiza espaço)
        reset=True,
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

def obter_timestamp():
    """Retorna o horário atual formatado para o JSON"""
    return time.strftime("%Y-%m-%d %H:%M:%S")