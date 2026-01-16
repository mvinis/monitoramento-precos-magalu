import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Importações internas
from src.scraper import MagaluScraper
from src.utils import configurar_logs

# 1. Carrega as configurações do ambiente (.env)
load_dotenv()

ENV = os.getenv("ENVIRONMENT", "dev")
VERSION = os.getenv("PIPELINE_VERSION", "v1.0")

def salvar_dados(dados):
    if not os.path.exists('data/raw'):
        os.makedirs('data/raw')
    
    timestamp_nome = datetime.now().strftime("%Y%m%d_%H%M%S")
    caminho = f'data/raw/produtos_magalu_{timestamp_nome}.json'
    
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)
    
    print(f"\n💾 Arquivo versionado salvo em: {caminho}")

def executar():
    configurar_logs()
    
    print(f"🚀 Iniciando extração | Ambiente: {ENV} | Versão: {VERSION}")
    
    # 2. Agora passamos as variáveis para o bot corretamente
    bot = MagaluScraper(ambiente=ENV, versao=VERSION)
    
    # 3. Executa a coleta
    resultados = bot.coletar_produtos()
    
    # 4. Salva o resultado final
    if resultados:
        salvar_dados(resultados)
    else:
        print("⚠ Nenhum dado foi coletado.")

if __name__ == "__main__":
    executar()