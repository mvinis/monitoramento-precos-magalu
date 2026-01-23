import re
import logging

def montar_objeto_produto(dados_brutos, contexto, classificador_ai=None):
    """
    Transforma dados brutos em um objeto estruturado (Schema VIP).
    Mantém a integridade das chaves originais com lógica de classificação híbrida.
    """
    # --- 1. EXTRAÇÃO E TIPAGEM ---
    p_original = dados_brutos.get('preco_antigo', 0)
    p_pix = dados_brutos.get('preco_pix', 0)
    p_credito_avista = dados_brutos.get('preco_atual', 0) 
    
    titulo_raw = dados_brutos.get('titulo', 'N/A')
    titulo_low = titulo_raw.lower()
    is_bundle_final = detectar_bundle(titulo_raw)

    logging.info(f"--- Processando: {titulo_raw[:50]}... ---")

    # --- NOVO: BLOCO 0 - FILTRO DE INSUMOS E REPARO (Ajustado) ---
    if any(k in titulo_low for k in ['cola', 'adesivo', 'resina', 'ferramenta', 'limpeza', 'reparo']):
        categoria_base = "Outros"
    
    else:
        # MUDANÇA 1: Expandimos a lista para capturar a posição de Relógios também
        termos_hardware_geral = [
            'iphone', 'smartphone', 'galaxy', 'motorola', 'redmi', 'poco', 'xiaomi',
            'relógio', 'relogio', 'watch', 'smartwatch', 'hw5', 'w28', 's10', 'fitband'
        ]
        
        pos_hw = -1
        for k in termos_hardware_geral:
            p = titulo_low.find(k)
            if p != -1 and (pos_hw == -1 or p < pos_hw):
                pos_hw = p

        # --- 2. HIERARQUIA DE CATEGORIZAÇÃO ---
        
        # 1.1 Suportes e Estabilizadores
        if any(k in titulo_low for k in ['suporte', 'tripe', 'tripé', 'bastão', 'pau de selfie', 'estabilizador', 'ring light']):
            termos_sup = ['suporte', 'tripe', 'tripé', 'bastão', 'pau de selfie', 'estabilizador', 'ring light']
            pos_acc = min([titulo_low.find(k) for k in termos_sup if titulo_low.find(k) != -1])
            
            if pos_hw == -1 or pos_acc < pos_hw:
                categoria_base = "Suporte"
            else:
                if any(w in titulo_low for w in ['watch', 'relógio', 'relogio', 'hw5', 'w28']):
                    categoria_base = "Smartwatch"
                else:
                    categoria_base = "Smartphone"

        # 1.2 Energia
        elif any(k in titulo_low for k in ['carregador', 'cabo', 'fonte', 'adaptador', 'power bank']):
            pos_acc = min([titulo_low.find(k) for k in ['carregador', 'cabo', 'fonte', 'adaptador', 'power bank'] if titulo_low.find(k) != -1])
            if pos_hw == -1 or pos_acc < pos_hw:
                categoria_base = "Carregador"
            else:
                if any(w in titulo_low for w in ['watch', 'relógio', 'relogio', 'hw5', 'w28']):
                    categoria_base = "Smartwatch"
                else:
                    categoria_base = "Smartphone"

        # 1.3 Proteção e Estética
        elif any(k in titulo_low for k in ['capa', 'capinha', 'película', 'pelicula', 'case', 'pulseira', 'smarttag', 'airtag', 'rastreador', 'localizador']):
            pos_acc = min([titulo_low.find(k) for k in ['capa', 'capinha', 'película', 'pelicula', 'case', 'pulseira', 'smarttag', 'airtag', 'rastreador', 'localizador'] if titulo_low.find(k) != -1])
            
            if pos_hw == -1 or pos_acc < pos_hw:
                categoria_base = "Acessório" if 'pulseira' in titulo_low else "Proteção"
            else:
                if any(w in titulo_low for w in ['watch', 'relógio', 'relogio', 'hw5', 'w28', 's10']):
                    categoria_base = "Smartwatch"
                else:
                    categoria_base = "Smartphone"

        # 1.4 Óculos Inteligente
        elif any(k in titulo_low for k in ['óculos', 'oculos', 'vr', 'realidade virtual', 'óculos 3d', '3d']):
            categoria_base = "Óculos Inteligente"

        # 1.5 Videogame (físico)
        elif any(k in titulo_low for k in ['gamepad', 'joystick', 'playstation', 'xbox', 'nintendo', 'pc gamer', 'ps']):
            categoria_base = "Console"
        
        # 1.5 Celular Básico (apenas funções básicas)
        elif any(k in titulo_low for k in ['celular', 'celular antigo', '2g']):
            termos_sup = ['celular', 'celular antigo', '2g']
            pos_acc = min([titulo_low.find(k) for k in termos_sup if titulo_low.find(k) != -1])
            if pos_hw == -1 or pos_acc < pos_hw:
                categoria_base = "Celular Básico"
            else:
                categoria_base = "Smartphone"
        
        # 1.6 Relógio Inteligente (contém várias funções)
        elif any(k in titulo_low for k in ['relógio', 'relogio', 'watch', 'smartwatch', 'hw5', 'w28']):
            categoria_base = "Smartwatch"

        # 1.7 Smartband (contém funções básicas. smartband != smartwatch)
        elif any(k in titulo_low for k in ['smartband', 'mi band', 'fitband', 'band', 'm3', 'm4', 'fit']):
            termos_sup = ['smartband', 'mi band', 'fitband', 'band', 'm3', 'm4', 'fit']
            pos_acc = min([titulo_low.find(k) for k in termos_sup if titulo_low.find(k) != -1])
            if pos_hw == -1 or pos_acc < pos_hw:
                categoria_base = "Smartband"
            else:
                categoria_base = "Smartphone"
        
        # 1.8 Chip
        elif any(k in titulo_low for k in ['chip', 'pre-pago', 'pré-pago', 'pre pago', 'smart card', 'microchip', 'minichip', 'nanochip', 'cartão sim']):
            termos_sup = ['chip', 'pre-pago', 'pré-pago', 'pre pago']
            pos_acc = min([titulo_low.find(k) for k in termos_sup if titulo_low.find(k) != -1])
            if pos_hw == -1 or pos_acc < pos_hw:
                categoria_base = "Chip"
            else:
                categoria_base = "Smartphone"

        # BLOCO 2: HARDWARE DIRETO
        elif pos_hw != -1 or any(k in titulo_low for k in ['smartphone', 'smarphone', 'smart phone', 'not', 'x7', 'redmi note', 'realme', 'C61', 'lg k', 'motorola', '14 pro', '15 pro', '13 pro', '12 pro']):
            if any(w in titulo_low for w in ['watch', 'relógio', 'relogio', 'hw5', 'w28']):
                categoria_base = "Smartwatch"
            else:
                categoria_base = "Smartphone"

        # BLOCO 3: IA
        else:
            if classificador_ai:
                categoria_base = classificador_ai.classificar(titulo_raw)
            else:
                categoria_base = "Outros"

    # --- 3. LÓGICA DE BUNDLE (Executada para TODOS, incluindo a Cola) ---
    if is_bundle_final:
        categoria = montar_string_bundle(categoria_base, titulo_low)
    else:
        categoria = categoria_base

    # --- 4. CÁLCULOS FINANCEIROS ---
    valor_absoluto_desc = 0
    percentual_desc = 0
    if p_original > p_credito_avista and p_original > 0:
        valor_absoluto_desc = round(p_original - p_credito_avista, 2)
        percentual_desc = round((valor_absoluto_desc / p_original) * 100, 2)

    txt_parc = dados_brutos.get('parcelamento_original', '')
    match_parc = re.search(r'(\d+)x', txt_parc)
    parcelas_max = int(match_parc.group(1)) if match_parc else 1
    valor_parcela = round(p_credito_avista / parcelas_max, 2) if parcelas_max > 0 else p_credito_avista

    # --- 5. CONSTRUÇÃO DO OBJETO FINAL (Schema VIP) ---
    return {
        "metadata": {
            "timestamp_coleta": contexto['timestamp'],
            "plataforma": "Magazine Luiza",
            "scraper_name": "MagaluScraper",
            "versao_pipeline": contexto['versao_pipeline'],
            "ambiente": contexto['ambiente'],
            "tipo_coleta": contexto['tipo_coleta']
        },
        "produto": {
            "id_site": dados_brutos['id_produto'],
            "nome": titulo_raw,
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
            "tipo_vendedor": "VENDEDOR_TERCEIRO" if contexto["canal_venda"] == "MARKETPLACE" else "PLATAFORMA"
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

# --- FUNÇÕES AUXILIARES ---

def montar_string_bundle(base, titulo_low):
    componentes = [base]
    extras = {
        'película': 'Película', 'pelicula': 'Película',
        'capa': 'Capa', 'capinha': 'Capa',
        'pulseira': 'Acessório', 'fone': 'Áudio',
        'cabo': 'Cabo', 'fonte': 'Fonte'
    }
    for termo, nome_exibicao in extras.items():
        # Evita adicionar "Capa" se a base já for "Proteção" por exemplo
        if termo in titulo_low and nome_exibicao.lower() not in base.lower():
            componentes.append(nome_exibicao)
    return " + ".join(list(dict.fromkeys(componentes)))

def detectar_bundle(titulo):
    """
    Detecta combos reais, limpando especificações de RAM, Tela (FHD+) 
    e Câmeras (+ Selfie) para evitar falsos positivos.
    """
    titulo_low = titulo.lower()

    # 1. LIMPEZA DE ESPECIFICAÇÕES TÉCNICAS (O Escudo)
    # Limpa RAM: "4+4gb", "8gb+16gb", "ram+boost", "+ 8gb ram"
    titulo_limpo = re.sub(r'\d+\s*[+&]\s*\d+\s*(gb|ram|virtual)', '', titulo_low)
    titulo_limpo = re.sub(r'ram\s*[+&]\s*boost', '', titulo_limpo)
    titulo_limpo = re.sub(r'\+\s*\d+\s*gb', '', titulo_limpo)
    
    # Limpa Tela: "fhd+", "hd+", "qhd+"
    titulo_limpo = re.sub(r'(fhd|hd|qhd|amoled|oled|ips)\s*\+', '', titulo_limpo)
    
    # Limpa Câmeras: "+ selfie", "+ frontal", "+ cam"
    titulo_limpo = re.sub(r'\+\s*(selfie|frontal|cam|câm|traseira)', '', titulo_limpo)

    # 2. VERIFICAÇÃO NO TÍTULO LIMPO
    tem_sinal = any(s in titulo_limpo for s in ['+', '&', ' c/'])
    
    # Padrões de quantidade (Ex: 2 pulseiras)
    match_acessorios = re.search(r'\d+\s*(pulseiras|fones|películas|peliculas|capas|case|tiras)', titulo_limpo)
    
    # Palavras-chave de itens extras
    itens_adicionais = ['brinde', 'kit', 'combo', 'fone bluetooth', 'cabo', 'fonte']
    tem_item_extra = any(k in titulo_limpo for k in itens_adicionais)

    # 3. FILTRO FINAL DE SEGURANÇA
    # Se ainda sobrou um sinal, mas o título é carregado de termos técnicos e não tem "kit/brinde"
    if tem_sinal and not tem_item_extra and not bool(match_acessorios):
        termos_specs = ['br', 'nfc', 'nf', 'gb', 'mb', '5g', '4g', 'dual', 'sim', 'mah', 'bateria', 'biometria', 'nfe', 'camera', 'samsung xiaomi', 'ganfast', 'mp']
        if any(t in titulo_limpo for t in termos_specs):
            # Se só sobrou o sinal de + mas não detectamos um item claro, assumimos que é spec residual
            return False

    return bool(match_acessorios) or tem_item_extra or tem_sinal

# FUNÇÕES DATA CLEANER

def normalizar_texto(texto):

    """
    Higieniza strings removendo artefatos comuns de web scraping.
    
    Substitui espaços não-quebráveis (Unicode \xa0) por espaços padrão
    e remove espaços em branco sobressalentes nas extremidades.

    Args:
        texto (str): String bruta capturada do HTML.
    Returns:
        str: Texto normalizado ou "N/A" caso a entrada seja nula/vazia.
    """

    if not texto: return "N/A"
    return texto.replace('\xa0', ' ').strip()

def limpar_valor_simples_para_float(texto):

    """
    Converte strings monetárias (R$ 1.299,50) em float (1299.5).
    
    Trata separadores de milhar, decimais brasileiros e limpa caracteres 
    invisíveis, servindo como camada de Data Quality do pipeline.
    
    Args:
        texto (str): Texto bruto do scraping.
    Returns:
        float: Valor convertido ou 0.0 em caso de erro/N/A.
    """

    if not texto or "N/A" in texto: return 0.0
    try:
        limpo = normalizar_texto(texto)
        limpo = limpo.replace('R$', '').replace('ou', '').replace('.', '').replace(',', '.').replace(' ', '')
        resultado = re.search(r"[-+]?\d*\.\d+|\d+", limpo)
        return float(resultado.group()) if resultado else 0.0
    except:
        return 0.0
    
def calcular_preco_total_parcelado(texto_parcela):

    """
    Calcula o valor total de uma venda parcelada a partir de uma string descritiva.
    
    Extrai a quantidade de parcelas e o valor unitário da parcela para projetar
    o custo final a prazo, permitindo análises de juros e encargos financeiros.

    Exemplo:
        "10x de R$ 399,78" -> 3997.8 (Calculou o total de parcelas)
        "sem juros" -> Identifica os componentes numéricos e realiza o produto.

    Args:
        texto_parcela (str): Texto bruto contendo a condição de parcelamento 
            (ex: "12x de R$ 150,00").

    Returns:
        float: Valor total projetado (parcelas * valor). Retorna 0.0 em caso de 
            falha na extração ou dados nulos.

    Raises:
        Logging Error: Registra falhas de conversão no log do sistema para 
            fins de monitoramento de qualidade dos dados.
    """

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