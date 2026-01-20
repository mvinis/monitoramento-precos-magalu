from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re
import time
import random
import logging
import hashlib
from src.models.classifier import ProductClassifier

# Importação de ferramentas internas
from src.parsers import (
    limpar_valor_simples_para_float, 
    calcular_preco_total_parcelado, 
    normalizar_texto,
    montar_objeto_produto
)
from src.utils import obter_timestamp

ia_instanciada = ProductClassifier()

class MagaluScraper:
    def __init__(self, ambiente="dev", versao="1.0"):
        self.ambiente = ambiente
        self.versao = versao
        self.tipo_coleta = "web_scraping"

        # Configura a instância do Selenium com argumentos para evitar bloqueios.
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--incognito") # modo anônimo
        self.chrome_options.add_argument("--window-size=1920,1080")
        
        # Oculta a flag de automação para o site não detectar o bot facilmente (se não é detectado e barrado)
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option('useAutomationExtension', False)
        
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        self.chrome_options.add_argument(f'user-agent={user_agent}')
        
        self.driver = None
        self.classificador = ProductClassifier()

    def iniciar_driver(self):
        """Inicializa o Chrome via Selenium com gestão automática de drivers e opções de evasão."""
        servico = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=servico, options=self.chrome_options)

    def fechar_driver(self):
        """Encerra a instância do navegador e libera os recursos de memória do sistema."""
        if self.driver:
            self.driver.quit()

    def coletar_produtos(self, max_paginas=None):
        """
        Executa o pipeline completo de coleta, extração e estruturação de dados.
        
        Este método coordena o ciclo de vida do scraper, navegando pela paginação do 
        e-commerce, identificando cards de produtos e processando informações de 
        preço, identidade e marketplace.

        O processo segue as etapas:
        1. **Navegação**: Gerencia o loop de páginas com delays aleatórios para evitar bloqueios.
        2. **Extração (Parsing)**: Utiliza BeautifulSoup para localizar elementos DOM (títulos, preços, links).
        3. **Identificação de Marketplace**: Analisa parâmetros de URL (`seller_id`) para distinguir 
           entre 'Venda Direta' (Magazine Luiza) e vendedores terceiros.
        4. **Normalização**: Converte strings monetárias e textos Unicode em tipos primitivos (float/int).
        5. **Estruturação (Schema VIP)**: Consolida os dados no formato final para ingestão em Data Lake.

        Args:
            max_paginas (int, optional): Limite de páginas para a coleta. 
                Se for None, o scraper percorrerá todas as páginas disponíveis.

        Returns:
            list[dict]: Uma lista de dicionários, onde cada item é um objeto de produto 
                validado e estruturado conforme o Schema VIP.

        Raises:
            Exception: Captura e loga erros em nível de card ou página, garantindo que 
                uma falha isolada não interrompa todo o pipeline (resiliência).
        """
        self.iniciar_driver()
        buffer_produtos = [] # buffer
        pagina = 1
        
        try:
            while True:
                if max_paginas and pagina > max_paginas:
                    logging.info(f"🛑 Limite de {max_paginas} páginas atingido.")
                    break

                url = f"https://www.magazinevoce.com.br/magazineoficialweblu/celulares-e-smartphones/l/te/?page={pagina}"
                logging.info(f"📡 Acessando Página {pagina}...")
                
                try:
                    self.driver.get(url)
                    time.sleep(random.uniform(4, 7))
                    
                    sopa = BeautifulSoup(self.driver.page_source, 'html.parser')
                    cards = sopa.find_all(['a'], attrs={'data-testid': 'product-card-container'})

                    if not cards:
                        logging.warning(f"🏁 Fim da linha na página {pagina}. Não há mais cards.")
                        break

                    for card in cards:
                        try:
                            # 1. Busca de Elementos
                            titulo_elem = card.find('h2', attrs={'data-testid': 'product-title'})
                            if not titulo_elem: continue

                            preco_original_elem = card.find('p', attrs={'data-testid': 'price-original'})
                            texto_parcelamento_elem = card.find('p', attrs={'data-testid': 'installment'})
                            preco_pix_elem = card.find('p', attrs={'data-testid': 'price-value'})

                            # 2. Tratamento de Textos e Preços
                            txt_titulo = normalizar_texto(titulo_elem.text)
                            txt_antigo = normalizar_texto(preco_original_elem.text) if preco_original_elem else "N/A"
                            txt_pix = normalizar_texto(preco_pix_elem.text) if preco_pix_elem else "N/A"
                            info_parcela = normalizar_texto(texto_parcelamento_elem.text) if texto_parcelamento_elem else "N/A"

                            num_antigo = limpar_valor_simples_para_float(txt_antigo)
                            num_pix = limpar_valor_simples_para_float(txt_pix)

                            # 3. Lógica do Preço de Venda
                            if info_parcela != "N/A" and "x" in info_parcela.lower():
                                num_atual = calcular_preco_total_parcelado(info_parcela)
                            elif num_pix > 0:
                                num_atual = num_pix
                            else:
                                num_atual = num_antigo

                            # 4. Extração de ID, Link e VENDEDOR (Nova Lógica)
                            link_relativo = card.get('href', '')
                            
                            # --- BUSCA DO VENDEDOR NO LINK ---
                            # Tentamos encontrar 'seller_id=nome_da_loja'
                            vendedor_nome = "Magazine Luiza"
                            match_seller = re.search(r'seller_id=([^&/]+)', link_relativo)
                            
                            if match_seller:
                                raw_seller = match_seller.group(1).lower()
                                
                                # Se o seller_id for diferente de magazineluiza, é Marketplace!
                                if "magazineluiza" not in raw_seller:
                                    vendedor_nome = raw_seller.replace('oficial', '').capitalize()
                                    canal_venda = "MARKETPLACE"
                                else:
                                    # Caso tenha seller_id mas seja o do próprio Magalu
                                    vendedor_nome = "Magazine Luiza"
                                    canal_venda = "VENDA_DIRETA"
                              
                            # ---------------------------------

                            product_id = "N/A"
                            match_p = re.search(r'/p/(\d+)/', link_relativo)
                            
                            if match_p:
                                product_id = match_p.group(1)
                            else:
                                product_id = hashlib.md5(txt_titulo.encode()).hexdigest()[:10]

                            # 5. Organização dos dados para o Schema VIP
                            dados_limpos = {
                                "id_produto": product_id,
                                "titulo": txt_titulo,
                                "preco_antigo": num_antigo,
                                "preco_pix": num_pix,
                                "preco_atual": num_atual,
                                "parcelamento_original": info_parcela
                            }

                            contexto = {
                                "timestamp": obter_timestamp(),
                                "ambiente": self.ambiente,
                                "versao_pipeline": self.versao,
                                "tipo_coleta": self.tipo_coleta,
                                "url_produto": f"https://www.magazinevoce.com.br{link_relativo}",
                                "canal_venda": canal_venda,
                                "loja": vendedor_nome,
                                "pagina": pagina
                            }

                            # 6. Montagem e Buffer
                            produto_final = montar_objeto_produto(dados_limpos, contexto, classificador_ai=ia_instanciada)
                            buffer_produtos.append(produto_final)

                        except Exception as e:
                            logging.error(f"❌ Erro ao processar card na página {pagina}: {e}")
                            continue 

                    logging.info(f"✅ Página {pagina} finalizada. Total: {len(buffer_produtos)} itens.")
                    pagina += 1

                except Exception as e:
                    logging.error(f"⚠️ Erro crítico na página {pagina}: {e}")
                    pagina += 1 

        finally:
            self.fechar_driver()
            
        return buffer_produtos