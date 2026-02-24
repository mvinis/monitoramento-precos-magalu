import json
import os
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
import logging

# Importações internas
from src.scraper import MagaluScraper
from src.utils import configurar_logs
from src.parsers import capitalizar_categoria

# 1. Carrega as configurações do ambiente (.env)
load_dotenv()

ENV = os.getenv("ENVIRONMENT", "dev")
VERSION = os.getenv("PIPELINE_VERSION", "v1.0")

def salvar_dados(dados):
    """
    Persiste os dados em JSON e Excel.
    """
    # 1. Cria o diretório se não existir
    if not os.path.exists('data/raw') or not os.path.exists('data/raw/json') or not os.path.exists('data/raw/xlsx'):
        os.makedirs('data/raw')
        os.makedirs('data/raw/json')
        os.makedirs('data/raw/xlsx')
    
    timestamp_nome = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # --- SALVAMENTO EM JSON (Seu padrão atual) ---
    caminho_json = f'data/raw/json/produtos_magalu_{timestamp_nome}.json'
    with open(caminho_json, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)
    
    # --- SALVAMENTO EM EXCEL (Nova Auditoria) ---
    try:
        caminho_excel = f'data/raw/xlsx/produtos_magalu_{timestamp_nome}.xlsx'
        
        # O json_normalize "achata" o dicionário aninhado (preço, vendedor, etc) em colunas planas
        df = pd.json_normalize(dados)
        
        # Salva em Excel
        df.to_excel(caminho_excel, index=False)
        logging.info(f"📊 Planilha de auditoria salva em: \033[32m{caminho_excel}\033[0m")
    except Exception as e:
        logging.error(f"❌ Erro ao gerar Excel: {e}")

    logging.info(f"💾 Arquivo JSON salvo em: \033[32m{caminho_json}\033[0m")

def executar():

    """
    Orquestra o fluxo principal (workflow) da aplicação.
    
    Responsável por inicializar as configurações de log, instanciar o motor de 
    scraping com as variáveis de ambiente corretas, disparar o processo de 
    coleta e garantir a persistência dos dados finais.
    """

    configurar_logs()
    
    logging.info(f"🚀 Iniciando extração | Ambiente: {ENV} | Versão: {VERSION}")
    
    bot = MagaluScraper(ambiente=ENV, versao=VERSION)
    
    # 2. Lista de categorias
    
    # CATEGORIAS DE FILTROS POSSÍVEIS DENTRO DA MAGALU:  Smartphone, Capa para Celular, Smartwatch, Película para Celular, Carregador para Celular e Tablet, Kit de Capa e Película para Celular, Suporte para Celular, Carregador Portátil, Cabo para Celular, Pulseira para Smartwatch e Smartband, Conector para Celular, Bastão de Selfie, Tripé, Capa para Smartwatch, Kit de Acessórios para Celular, Carregador para Celular, Bateria para Celular, Celular Simples, Película para Smartwatch, Tela para Celular, Fonte de Alimentação, Bolsa para Celular, Fonte de Alimentação para Carregador, Peças e Acessórios para Celulares, Estabilizador para Celular, Smartband, Lente de Câmera para Celular, Kit de Ferramentas para Reparo de Celular, Tampa para Celular, Braçadeira para Celular, Controle para Celular, Óculos de Realidade Virtual para Celular, Cabo USB, Stencil BGA, Kit de Ferramentas, Carregador para Smartwatch, Ampliador de Tela para Celular, Peças e Acessórios para Smartwatch, Alto-falante para Celular, Pingente para Celular, Microscópio para Reparo de Celular, Anel inteligente, Adaptador para Equipamento de Áudio, Câmera para Celular, Bateria para Eletrônicos, Suporte para Smartwatch, Gaveta de Chip para Celular, Rastreador de Veículo, Chip para Celular, Adesivo para Celular, Capa para Tablet, Protetor Ocular para Câmera, Kit de Peças para Reparo de Celular, Placa para Celular, Display LCD para Celular, Tela de Proteção, Lente para Celular, Suporte de Celular para Veículos, Suporte para Tablet, Adaptador para Carregador de Celular

    categorias_alvo = ["Kit de Capa e Película para Celular"] # padrão: Smartwatch, Smartband Carregador Portátil
    categorias_alvo = [capitalizar_categoria(item) for item in categorias_alvo]

    todas_coletas = []

    if not categorias_alvo:
        logging.error("❌  Não há nenhuma categoria alvo de filtro")

    # 3. Loop para percorrer cada categoria
    for categoria in categorias_alvo:
        logging.info(f"🔍 Iniciando coleta da categoria: {categoria}")
        
        resultados_categoria = bot.coletar_produtos(categoria_alvo=categoria)
        
        if resultados_categoria:
            logging.info(f"✅ Coletados {len(resultados_categoria)} itens de {categoria}")
            todas_coletas.extend(resultados_categoria)
        else:
            logging.warning(f"⚠  Nenhuma oferta encontrada para {categoria}")

    # 4. Salva o resultado consolidado
    if todas_coletas:
        salvar_dados(todas_coletas)
    else:
        logging.error("❌  Nenhum dado foi coletado em nenhuma categoria.")

if __name__ == "__main__":
    executar()