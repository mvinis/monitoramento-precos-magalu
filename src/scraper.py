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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

# Importação de ferramentas internas
from src.parsers import (
    limpar_valor_simples_para_float, 
    calcular_preco_total_parcelado, 
    normalizar_texto,
    montar_objeto_produto
)
from src.utils import obter_timestamp
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
    
    def extrair_descricao_detalhada(self, url_produto, txt_produto):
        """Abre o produto em uma nova aba, extrai a descrição e fecha a aba."""
        logging.info(f"📡 Extraindo descrição do produto {txt_produto}")
        try:
            # Abre uma nova aba vazia
            self.driver.execute_script("window.open('');")
            # Alterna o foco para a nova aba (a última da lista)
            self.driver.switch_to.window(self.driver.window_handles[-1])
            
            self.driver.get(url_produto)

            # Espera um pouco mais para o JavaScript "preencher" a div
            time.sleep(4)
            
            sopa_detalhe = BeautifulSoup(self.driver.page_source, 'html.parser')
            # Localizador padrão da descrição na Magalu
            desc_elem = sopa_detalhe.find('div', attrs={'data-testid': 'rich-content-container'})
            
            texto_desc = normalizar_texto(desc_elem.text) if desc_elem else "N/A"
            
            # Fecha a aba e volta para a aba principal (índice 0)
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
    
            return texto_desc
        except Exception as e:
            logging.error(f"⚠️ Falha no Drill-down: {e}")
            # Garante que volta para a aba principal mesmo em erro
            if len(self.driver.window_handles) > 1:
                self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            return "N/A"
 
    def coletar_produtos(self, categoria_alvo, max_paginas=None):
        """
        Pipeline de coleta blindado: filtragem dinâmica, detecção de fim e IA.
        """
        self.iniciar_driver()
        buffer_produtos = []
        pagina = 1
        filtro_aplicado = False
        
        # URL BASE - Ponto de partida
        url_base = "https://www.magazinevoce.com.br/magazineoficialweblu/celulares-e-smartphones/l/te/"
        
        try:
            while True:

                # 1. CONSTRUÇÃO DA URL DINÂMICA
                # pasta_filtro = f"entity---{categoria_alvo.lower()}/" if filtro_aplicado else ""
                # url_final = f"{url_base}{pasta_filtro}?page={pagina}"

                if pagina == 1:
                    self.driver.get(url_base)
                else:
                    # Usa a URL atual já com filtro aplicado
                    url_atual = self.driver.current_url
                    if "page=" in url_atual:
                        url_atual = re.sub(r'page=\d+', f'page={pagina}', url_atual)
                    else:
                        url_atual += f"?page={pagina}"
                    self.driver.get(url_atual)
                
                logging.info(f"--- 📡 Acessando {categoria_alvo} | Página {pagina} ---")
                # self.driver.get(url_final)
                # Remove qualquer overlay fixo (ex: pop-up no rodapé)
                self.driver.execute_script("""
                    document.querySelectorAll('div').forEach(el => {
                        let style = window.getComputedStyle(el);
                        if (style.position === 'fixed' && style.zIndex > 1000) {
                            el.remove();
                        }
                    });
                """)

                time.sleep(random.uniform(4, 6))

                sopa = BeautifulSoup(self.driver.page_source, 'html.parser')

                # 2. APLICAÇÃO DO FILTRO (Apenas na Página 1)
                if pagina == 1 and not filtro_aplicado:
                    try:
                        # Clicar primeiro em ver todas as opções de filtros
                        xpath_btn_cat_filtro = f"//div[@data-testid='accordion-multiple-filters' and .//p[text()='Tipo de produto']]//button[@data-testid='filter-action' and text()='Ver todos']"
                        xpath_filtro = f"//li[@data-testid='filter-checkbox'][.//p[text()='{categoria_alvo}']]"
                
                        # 1. Espera até 10 segundos para o botão existir e ser clicável
                        botao = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, xpath_btn_cat_filtro))
                        )
                        
                        # 3. Tenta o clique normal
                        botao.click()
                        logging.info("✅ Botão 'Ver todos' clicado com sucesso.")

                        filtro_pai = WebDriverWait(self.driver, 12).until(
                            EC.element_to_be_clickable((By.XPATH, xpath_filtro))
                        )
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", filtro_pai)
                        time.sleep(1)
                        
                        checkbox = filtro_pai.find_element(By.CSS_SELECTOR, "input[data-testid='checkbox-item']")
                        logging.info(f"🖱️  Marcando o filtro {categoria_alvo} pela primeira vez...")
                        checkbox.click()
                        
                        filtro_aplicado = True
                        time.sleep(5) # Espera o Ajax recarregar
                        sopa = BeautifulSoup(self.driver.page_source, 'html.parser')

                        # --- DETECÇÃO DO LIMITE DE PÁGINAS ---
                        sopa_paginacao = BeautifulSoup(self.driver.page_source, 'html.parser')
                        nav = sopa_paginacao.find('nav', attrs={'aria-label': 'pagination navigation'})
                        if nav and max_paginas is None:
                            links = nav.find_all('a', attrs={'data-testid': 'pagination-item'})
                            nums = [int(l.text) for l in links if l.text.isdigit()]
                            if nums:
                                max_paginas = max(nums)
                                logging.info(f"🎯 Limite dinâmico: {max_paginas} páginas.")
                        
                    except Exception as e:
                        logging.error(f"⚠️  Falha ao aplicar filtro: {e}")
                        break

                # 3. VALIDAÇÃO (KILL SWITCH)
                chip = sopa.find('label', attrs={'data-testid': 'chip-label'})
                texto_chip = chip.find('p').get_text().strip() if chip else ""
                
                # Comparação da categoria_alvo
                if filtro_aplicado and texto_chip != categoria_alvo:
                    logging.warning(f"🚨 Filtro de {categoria_alvo} caiu! Encerrando na pág {pagina}.")
                    break

                # 4. PROCESSAMENTO DOS CARDS
                cards = sopa.find_all(['a'], attrs={'data-testid': 'product-card-container'})
                if not cards:
                    break

                for card in cards:
                    try:
                        # --- EXTRAÇÃO DE DADOS DO CARD ---
                        titulo_elem = card.find('h2', attrs={'data-testid': 'product-title'})
                        if not titulo_elem: continue
                        
                        preco_orig_elem = card.find('p', attrs={'data-testid': 'price-original'})
                        parcela_elem = card.find('p', attrs={'data-testid': 'installment'})
                        pix_elem = card.find('p', attrs={'data-testid': 'price-value'})

                        txt_titulo = normalizar_texto(titulo_elem.text)
                        txt_antigo = normalizar_texto(preco_orig_elem.text) if preco_orig_elem else "N/A"
                        txt_pix = normalizar_texto(pix_elem.text) if pix_elem else "N/A"
                        info_parcela = normalizar_texto(parcela_elem.text) if parcela_elem else "N/A"

                        num_antigo = limpar_valor_simples_para_float(txt_antigo)
                        num_pix = limpar_valor_simples_para_float(txt_pix)

                        # Cálculo de Preço Atual
                        if info_parcela != "N/A" and "x" in info_parcela.lower():
                            num_atual = calcular_preco_total_parcelado(info_parcela)
                        elif num_pix > 0:
                            num_atual = num_pix
                        else:
                            num_atual = num_antigo

                        # Vendedor e Link
                        link_relativo = card.get('href', '')
                        url_produto = f"https://www.magazinevoce.com.br{link_relativo}"
                        
                        vendedor_nome = "Magazine Luiza"
                        canal_venda = "VENDA_DIRETA"
                        match_s = re.search(r'seller_id=([^&/]+)', link_relativo)
                        if match_s:
                            raw_s = match_s.group(1).lower()
                            if "magazineluiza" not in raw_s:
                                vendedor_nome = raw_s.replace('oficial', '').capitalize()
                                canal_venda = "MARKETPLACE"

                        product_id = "N/A"
                        
                        match_p = re.search(r'/p/([^/]+)/', link_relativo)

                        if match_p:
                            product_id = match_p.group(1)
                            logging.info(f"✅ ID extraído da URL: {product_id}")
                        else:
                            product_id = hashlib.md5(txt_titulo.encode()).hexdigest()[:10]
                            logging.warning(f"⚠️ ID não encontrado, usando Hash: {product_id}")

                        # 5. MONTAGEM DO OBJETO
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
                            "url_produto": url_produto,
                            "canal_venda": canal_venda,
                            "loja": vendedor_nome,
                            "pagina": pagina
                        }

                        produto_final = montar_objeto_produto(dados_limpos, contexto, classificador_ai=self.classificador)

                        # --- 6. GATILHO DE REVISÃO IA ---
                        cat_atual = produto_final['produto']['categoria']
                        cat_principal = cat_atual.split(' + ')[0] if ' + ' in cat_atual else cat_atual

                        if cat_principal == "Smartwatch" and num_atual <= 199:
                            desc = self.extrair_descricao_detalhada(url_produto, txt_titulo)
                            if desc != "N/A":
                                prompt = f"Produto: {txt_titulo} | Preço: R$ {num_atual} | Descrição: {desc[:1500]}"
                                veredito = self.classificador.classificar(prompt, preco_produto=num_atual, modo_profundo=True)
                                
                                if produto_final['produto']['is_bundle'] and ' + ' in cat_atual:
                                    extras = cat_atual.split(' + ')[1:]
                                    produto_final['produto']['categoria'] = " + ".join([veredito] + extras)
                                else:
                                    produto_final['produto']['categoria'] = veredito
                                logging.info(f"🤖 IA reclassificou: {cat_atual} -> {produto_final['produto']['categoria']}")

                        buffer_produtos.append(produto_final)

                    except Exception as e:
                        logging.error(f"❌ Erro no card: {e}")

                # 7. INCREMENTO
                if max_paginas and pagina >= max_paginas:
                    break
                pagina += 1

        except Exception as e:
            logging.error(f"❌  Erro crítico: {e}")
        finally:
            self.fechar_driver()
            
        return buffer_produtos