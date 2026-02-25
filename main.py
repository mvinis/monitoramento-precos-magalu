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
    if not os.path.exists('data/raw') or not os.path.exists('data/raw/json') or not os.path.exists('data/raw/xlsx') or not os.path.exists('data/raw/json/exceptions') or not os.path.exists('data/raw/json/payloads'):
        os.makedirs('data/raw')
        os.makedirs('data/raw/json')
        os.makedirs('data/raw/json/exceptions')
        os.makedirs('data/raw/json/payloads')
        os.makedirs('data/raw/xlsx')
    
    timestamp_nome = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # --- SALVAMENTO EM JSON (padrão) ---
    caminho_json = f'data/raw/json/payloads/produtos_magalu_{timestamp_nome}.json'
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
    
    # CATEGORIAS DE FILTROS POSSÍVEIS DENTRO DA MAGALU:  Smartphone, Capa para Celular, Smartwatch, Película para Celular, 
    # Carregador para Celular e Tablet, Kit de Capa e Película para Celular, Suporte para Celular, Carregador Portátil, Cabo para Celular, 
    # Pulseira para Smartwatch e Smartband, Conector para Celular, Bastão de Selfie, Tripé, Capa para Smartwatch, Kit de Acessórios para Celular, 
    # Carregador para Celular, Bateria para Celular, Celular Simples, Película para Smartwatch, Tela para Celular, Fonte de Alimentação, 
    # Bolsa para Celular, Fonte de Alimentação para Carregador, Peças e Acessórios para Celulares, Estabilizador para Celular, Smartband, 
    # Lente de Câmera para Celular, Kit de Ferramentas para Reparo de Celular, Tampa para Celular, Braçadeira para Celular, Controle para Celular, 
    # Óculos de Realidade Virtual para Celular, Cabo USB, Stencil BGA, Kit de Ferramentas, Carregador para Smartwatch, 
    # Ampliador de Tela para Celular, Peças e Acessórios para Smartwatch, Alto-falante para Celular, Pingente para Celular, 
    # Microscópio para Reparo de Celular, Anel inteligente, Adaptador para Equipamento de Áudio, Câmera para Celular, Bateria para Eletrônicos, 
    # Suporte para Smartwatch, Gaveta de Chip para Celular, Rastreador de Veículo, Chip para Celular, Adesivo para Celular, Capa para Tablet, 
    # Protetor Ocular para Câmera, Kit de Peças para Reparo de Celular, Placa para Celular, Display LCD para Celular, Tela de Proteção, 
    # Lente para Celular, Suporte de Celular para Veículos, Suporte para Tablet, Adaptador para Carregador de Celular

    # categorias_alvo = ["Smartband", "Smartwatch", "Smartphone", "Celular Simples", "Carregador para Celular"] # padrão: Smartwatch, Smartband, Celular simples, Carregador Portátil
    categorias_alvo = [
        # "Adaptador para Carregador de Celular",
        # "Adaptador para Equipamento de Áudio",
        # "Adesivo para Celular",
        # "Alto-falante para Celular",
        # "Ampliador de Tela para Celular",
        # "Anel inteligente",
        # "Bastão de Selfie",
        # "Bateria para Celular",
        # "Bateria para Eletrônicos",
        # "Bolsa para Celular",
        # "Braçadeira para Celular",
        # "Cabo para Celular",
        # "Cabo USB",
        # "Câmera para Celular",
        # "Capa para Celular",
        # "Capa para Smartwatch",
        # "Capa para Tablet",
        # "Carregador para Celular",
        # "Carregador para Celular e Tablet",
        # "Carregador para Smartwatch",
        # "Carregador Portátil",
        "Celular Simples",
        # "Chip para Celular",
        # "Conector para Celular",
        # "Controle para Celular",
        # "Display LCD para Celular",
        # "Estabilizador para Celular",
        # "Fonte de Alimentação",
        # "Fonte de Alimentação para Carregador",
        # "Gaveta de Chip para Celular",
        # "Kit de Acessórios para Celular",
        # "Kit de Capa e Película para Celular",
        # "Kit de Ferramentas",
        # "Kit de Ferramentas para Reparo de Celular",
        # "Kit de Peças para Reparo de Celular",
        # "Lente de Câmera para Celular",
        # "Lente para Celular",
        # "Microscópio para Reparo de Celular",
        # "Óculos de Realidade Virtual para Celular",
        # "Peças e Acessórios para Celulares",
        # "Peças e Acessórios para Smartwatch",
        # "Película para Celular",
        # "Película para Smartwatch",
        # "Pingente para Celular",
        # "Placa para Celular",
        # "Protetor Ocular para Câmera",
        # "Pulseira para Smartwatch e Smartband",
        # "Rastreador de Veículo",
        "Smartband",
        "Smartphone",
        "Smartwatch",
        # "Stencil BGA",
        # "Suporte de Celular para Veículos",
        # "Suporte para Celular",
        # "Suporte para Smartwatch",
        # "Suporte para Tablet",
        # "Tela de Proteção",
        # "Tela para Celular",
        # "Tampa para Celular",
        # "Tripé",
    ]
    categorias_alvo = [capitalizar_categoria(item) for item in categorias_alvo]

    todas_coletas = []
    categorias_vazias = []

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
            categorias_vazias.append(categoria)

    # 4. Salva o resultado consolidado
    if todas_coletas:
        salvar_dados(todas_coletas)
    else:
        logging.error("❌  Nenhum dado foi coletado em nenhuma categoria.")
    
    # 5. Salva o relatório de categorias vazias (Auditoria)
    if categorias_vazias:
        timestamp_nome = datetime.now().strftime("%Y%m%d_%H%M%S")
        caminho_vazias = f'data/raw/json/exceptions/categorias_vazias_{timestamp_nome}.json'
        
        # Salva o array das categorias vazias em um JSON simples
        with open(caminho_vazias, 'w', encoding='utf-8') as f:
            json.dump(categorias_vazias, f, ensure_ascii=False, indent=4)
            
        logging.info(f"⚠️  Relatório de {len(categorias_vazias)} categorias sem produtos salvo em: \033[33m{caminho_vazias}\033[0m")

if __name__ == "__main__":
    executar()