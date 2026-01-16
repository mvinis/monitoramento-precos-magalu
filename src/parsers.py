# Este arquivo conterá apenas as funções de tratamento. Elas são independentes do Selenium.
import re
import logging
import os

from datetime import datetime
import hashlib

def montar_objeto_produto(dados_brutos, contexto, classificador_ai=None):
    p_original = dados_brutos.get('preco_antigo', 0)
    p_pix = dados_brutos.get('preco_pix', 0)
    # No seu caso, o preco_atual (venda final) costuma ser o crédito à vista
    p_credito_avista = dados_brutos.get('preco_atual', 0) 

    # Se o classificador for enviado, usamos a IA, senão usamos "Outros"
    if classificador_ai:
        categoria = classificador_ai.classificar(dados_brutos['titulo'])
    else:
        categoria = "A classificar"
    
    # Lógica de Categoria Dinâmica
    titulo = dados_brutos['titulo'].lower()
    if any(k in titulo for k in ['fone', 'headset', 'earbud']):
        categoria = "Acessórios / Áudio"
    elif any(k in titulo for k in ['cabo', 'carregador', 'pelicula', 'capa']):
        categoria = "Acessórios / Mobile"
    elif any(k in titulo for k in ['smartphone', 'celular', 'iphone', 'motorola', 'samsung', 'xiaomi']):
        categoria = "Smartphones"
    else:
        categoria = "Outros"
    
    # 1. Definimos que é bundle APENAS se a IA identificou duas categorias distintas
    # (Ex: "Smartphone & Fone de Ouvido")
    is_bundle_pela_ia = " & " in categoria

    # 2. Criamos uma regra para o sinal de "+" que ignora especificações de RAM
    # O Regex abaixo procura um " + " que NÃO esteja perto de palavras como "RAM" ou "GB"
    titulo_para_busca = dados_brutos['titulo'].upper()
    tem_mais_separado = " + " in titulo_para_busca

    # Verificamos se o "+" não é apenas propaganda de RAM (comum em Motorola e Samsung)
    is_ram_boost = "RAM+" in titulo_para_busca or "+8GB" in titulo_para_busca

    # Lógica Final: É bundle se a IA disse que sim OU se tem um " + " que não seja RAM Boost
    is_bundle_final = is_bundle_pela_ia or (tem_mais_separado and not is_ram_boost)

    # Cálculo de Descontos
    valor_absoluto_desc = 0
    percentual_desc = 0
    if p_original > p_credito_avista and p_original > 0:
        valor_absoluto_desc = round(p_original - p_credito_avista, 2)
        percentual_desc = round((valor_absoluto_desc / p_original) * 100, 2)

    # Extração de parcelas do texto (Ex: "12x de R$ 180,46")
    import re
    parcelas_max = 1
    valor_parcela = p_credito_avista
    txt_parc = dados_brutos.get('parcelamento_original', '')
    
    match_parc = re.search(r'(\d+)x', txt_parc)
    if match_parc:
        parcelas_max = int(match_parc.group(1))
        # Se você já tem o valor_parcela vindo do scraper, use-o. 
        # Aqui vamos estimar dividindo o total pelo número de parcelas
        valor_parcela = round(p_credito_avista / parcelas_max, 2)

    return {
        "metadata": {
            "timestamp_coleta": contexto['timestamp'],
            "plataforma": "Magazine Luiza",  # Fixo, pois este parser é para Magalu
            "scraper_name": "MagaluScraper",
            "versao_pipeline": contexto['versao_pipeline'], # Dinâmico
            "ambiente": contexto['ambiente'],               # Dinâmico
            "tipo_coleta": os.getenv("COLLECTION_TYPE", "manual")
        },
        "produto": {
            "id_site": dados_brutos['id_produto'],
            "nome": dados_brutos['titulo'],
            "categoria": categoria,
            "is_bundle": is_bundle_final,
            "sku": dados_brutos['id_produto']
        },
        "preço": {
            "moeda": "BRL",
            "preco_base": p_credito_avista,
            "preco_original": p_original if p_original > 0 else None,
            "descontos": {
                "percentual": percentual_desc,
                "valor_absoluto": valor_absoluto_desc
            },
            "precos_por_metodo": {
                "pix": p_pix if p_pix > 0 else None,
                "boleto": p_pix if p_pix > 0 else None,
                "credito_avista": p_credito_avista
            },
            "parcelamento": {
                "parcelas_max": parcelas_max,
                "valor_parcela": valor_parcela,
                "sem_juros": "sem juros" in txt_parc.lower()
            }
        },
        "vendedor": {
            "nome": contexto["loja"],
            "tipo_vendedor": "VENDEDOR_TERCEIRO" if contexto["canal_venda"] else "PLATAFORMA"
        },
        "plataforma": {
                "nome": "Magazine Luiza",
                "canal_venda": contexto["canal_venda"]
        },
        "origem": {
            "url_completa": contexto['url_produto'],
            "pagina_origem": contexto['pagina']
        }
    }

def normalizar_texto(texto):
    """Remove espaços invisíveis (U+00a0) e limpa espaços em branco extras"""
    if not texto:
        return "N/A"
    # Substitui o caractere invisível \xa0 por um espaço comum e remove excessos
    return texto.replace('\xa0', ' ').strip()

def limpar_valor_simples_para_float(texto):
    if not texto or "N/A" in texto:
        return 0.0
    try:
        # Primeiro normalizamos para garantir que o \xa0 sumiu
        limpo = normalizar_texto(texto)
        limpo = limpo.replace('R$', '').replace('ou', '').replace('.', '').replace(',', '.').replace(' ', '')
        
        resultado = re.search(r"[-+]?\d*\.\d+|\d+", limpo)
        return float(resultado.group()) if resultado else 0.0
    except:
        return 0.0
    if not texto or "N/A" in texto:
        return 0.0
    try:
        # 1. Substitui o espaço invisível (U+00a0) por um espaço comum
        # 2. Em seguida, remove R$, 'ou', pontos de milhar e ajusta a vírgula
        limpo = texto.replace('\xa0', ' ') # Transforma o invisível em visível
        limpo = limpo.replace('R$', '').replace('ou', '').replace('.', '').replace(',', '.').strip()
        
        # O Regex abaixo vai ignorar qualquer espaço que sobrar e pegar só o número
        resultado = re.search(r"[-+]?\d*\.\d+|\d+", limpo)
        return float(resultado.group()) if resultado else 0.0
    except Exception as e:
        return 0.0

def calcular_preco_total_parcelado(texto_parcela):

    """Calcula total de parcelas (ex: 10x 399,78 -> 3997.8)"""
    if not texto_parcela or "N/A" in texto_parcela:
        return 0.0
    try:
        # Remove pontos para não confundir o regex
        numeros = re.findall(r'\d+', texto_parcela.replace('.', ''))
        if len(numeros) >= 3:
            parcelas = int(numeros[0])
            valor_parcela = float(f"{numeros[1]}.{numeros[2]}")
            return round(parcelas * valor_parcela, 2)
    except Exception as e:
        logging.error(f"Erro ao calcular parcelamento: {texto_parcela} -> {e}")
        return 0.0
    return 0.0
