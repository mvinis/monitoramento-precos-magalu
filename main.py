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

    """
    Persiste os dados coletados em formato JSON na camada local de dados brutos (raw).
    
    Cria automaticamente o diretório de destino e versiona o arquivo utilizando 
    um timestamp para evitar sobrescrita e garantir o histórico da coleta.

    Args:
        dados (list[dict]): Lista de produtos estruturados para salvar.
    """

    if not os.path.exists('data/raw'):
        os.makedirs('data/raw')
    
    timestamp_nome = datetime.now().strftime("%Y%m%d_%H%M%S")
    caminho = f'data/raw/produtos_magalu_{timestamp_nome}.json'
    
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)
    
    print(f"\n💾 Arquivo versionado salvo em: {caminho}")

def executar():

    """
    Orquestra o fluxo principal (workflow) da aplicação.
    
    Responsável por inicializar as configurações de log, instanciar o motor de 
    scraping com as variáveis de ambiente corretas, disparar o processo de 
    coleta e garantir a persistência dos dados finais.
    """

    configurar_logs()
    
    print(f"🚀 Iniciando extração | Ambiente: {ENV} | Versão: {VERSION}")
    
    # 2. É passada as variáveis para o bot (scraper) corretamente
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