import logging
import time
import os

def configurar_logs():
    """Configura o sistema de logs e garante que a pasta de logs exista"""
    if not os.path.exists('data/logs'):
        os.makedirs('data/logs')
        
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("data/logs/scraping.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def obter_timestamp():
    """Retorna o horário atual formatado para o JSON"""
    return time.strftime("%Y-%m-%d %H:%M:%S")