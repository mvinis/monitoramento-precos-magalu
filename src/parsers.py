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
   
    categoria_base = categorizar_produto(titulo_low, titulo_raw, p_credito_avista)

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
            "id_produto": dados_brutos['id_produto'],
            "nome": titulo_raw,
            "cor": "N/A",
            "categoria": categoria,
            "is_bundle": is_bundle_final,
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

def montar_string_bundle(base, titulo_low):
    componentes = [base]
    
    extras = {
        'película': 'Proteção', 'pelicula': 'Proteção',
        'caneta': 'Acessório', 'mouse': 'Acessório', 'teclado': 'Acessório', 
        'pulseira': 'Acessório', 'capa': 'Capa', 'capinha': 'Capa',
        'fone': 'Áudio', 'cabo': 'Cabo', 'fonte': 'Fonte',
        'óculos de realidade virtual': 'Óculos de Realidade Virtual',
        'smartwatch': 'Smartwatch', 'smart watch': 'Smartwatch',
        'smartband': 'Smartband',
        'garrafa': 'Acessório','garrafa térmica': 'Acessório',
    }

    # Verifica se é um hardware (para ativar a proteção da pulseira)
    is_hardware_principal = any(v in base.lower() for v in ['smartwatch', 'smartband', 'smartphone', 'tablet'])

    for termo, nome_exibicao in extras.items():
        if termo in titulo_low:

            # 1. Evita duplicar a própria categoria
            if nome_exibicao.lower() in base.lower():
                continue

            # 2. LÓGICA ESPECIAL PARA PULSEIRAS
            if nome_exibicao == "Acessório" and is_hardware_principal and "pulseira" in termo:
                
                # Regex original do seu código (ajustada para pegar os dois lados)
                # Testando: "pulseira extra" OU "extra pulseira"
                padrao_extra = r'(extra|reserva|kit|\d+|brinde)\s*.*pulseira|pulseira.*\s*(extra|reserva|kit|\d+|brinde)'
                match_extra = re.search(padrao_extra, titulo_low)
                
                # Regex para "com pulseira"
                match_com = re.search(r'\bcom\b.*\bpulseira', titulo_low)


                if match_extra or match_com:
                     componentes.append(nome_exibicao)
                else:
                     continue 
            
            else:
                # Para outros itens, adiciona direto
                componentes.append(nome_exibicao)
    
    resultado_final = " + ".join(list(dict.fromkeys(componentes)))
    return resultado_final

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

    # Limpa opções de cores: "Preto + Azul", "Branco/Verde"
    titulo_limpo = re.sub(r'(preto|branco|azul|rosa|verde|dourado|silver|grafite)\s*[+/&]\s*(preto|branco|azul|rosa|verde|dourado|silver|grafite)', '', titulo_limpo)

    # 2. VERIFICAÇÃO NO TÍTULO LIMPO
    tem_sinal = any(s in titulo_limpo for s in ['+', '&', ' c/', 'com'])

    # Se tem quantidade. Ex: 2 relógios...
    match_qtd_unidades = re.search(r'\b(2|3|4|5|10)\s*(unidades|unid|x|vendas|relogios|smartwatch|fone|kit|par de)', titulo_limpo)
    
    # Padrões de quantidade (Ex: 2 pulseiras)
    match_acessorios = re.search(r'\d+\s*(pulseiras|fones|películas|peliculas|capas|case|tiras)', titulo_limpo)

    # Detecta pulseira EXTRA
    match_pulseira_extra = re.search(
        r'(com\s+)?pulseira\s+(extra|metal|reserva|adicional|\d+)',
        titulo_limpo
    )

    if match_pulseira_extra:
        return True
    
    # Palavras-chave de itens extras
    itens_adicionais = ['brinde', 'kit', 'combo', 'fone de ouvido', 'fone bluetooth', 'cabo', 'fonte', 'fit', 'watch']
    tem_item_extra = any(k in titulo_limpo for k in itens_adicionais)

    # 3. FILTRO FINAL DE SEGURANÇA
    # Se ainda sobrou um sinal, mas o título é carregado de termos técnicos e não tem "kit/brinde"
    if tem_sinal and not tem_item_extra and not bool(match_acessorios):
        termos_specs = ['br', 'nfc', 'nf', 'gb', 'mb', '5g', '4g', 'dual', 'sim', 'mah', 'bateria', 'biometria', 'nfe', 'camera', 'samsung xiaomi', 'ganfast', 'mp', 'usb', 'gps']
        if any(t in titulo_limpo for t in termos_specs):
            return False
    
    # Detecta padrão explícito de bundle com acessório
    if re.search(r'\bcom\b.*\b(pulseira|cabo|fone|capinha|capa)\b', titulo_limpo):
        return True

    return bool(match_acessorios) or bool(match_qtd_unidades) or tem_item_extra or tem_sinal

def categorizar_produto(titulo, preco):

    # Dicionário das categorias
    categorias_map = {
        
        "Proteção": [
            "capa", "capinha", "case", "pelicula", "película", "vidro temperado", "anti queda"
        ],
        "Óculos de Realidade Virtual": [
            "óculos vr", "óculos inteligente", "vr", "óculos de realidade virtual", "óculos vr realidade virtual"
        ],
        "Carregador": [
            "carregador", "fonte", "adaptador tomada", "carregamento rapido", "turbo", "power bank", "bateria", "bateria celular",  "carregador portátil", "base carregador"
        ],
        "Smartwatch": [
            "smartwatch", "apple watch", "galaxy watch", "relogio inteligente", "smart watch", "microwear",
            "relógio inteligente", "hw", "hw12", "w28", "ultra 9", "series 9", "relógio smart", "gps", "relógio smartwatch", "relógio smart watch", 
            "garmin forerunner", "celular de pulso", "relógio digital smart inteligente", "xiaomi watch", "plumzong"
        ],
        "Smartband": [
            "smartband", "pulseira mi", "smart band", "mi band", "pulseira inteligente", "galaxy fit", "correa",
            "fit 3", "d20", "m6", "w69", "gl08", "y68", "fitpro", "hryfine", "m3 band", "m4 band", "xufeng", "relógio smart", "relógio de pulso", "relógio bracelet", " pulseira inteligente ", 
            "s10", "t800", "smartach", "relógio esportivo", "relógio fitness", "xiaomi smart band", "relógio digital sport", "pulseira esportiva"
        ],
        "Tablet": [
            "tablet", "ipad", "galaxy tab", "xiaomi pad", "lenovo tab"
        ],
        "Acessório": [
            "pulseira","band", "smarttag", "localizador", "mili mitag", "airtag", "cordão", "bolsa", "carteira", "controle remoto", "garrafa térmica", "moto tag", "pulseira de silicone", "monitor de frequência cardíaca", "pulseira de monitor de frequência cardíaca",
            "bracelet de silicone"
        ],
        "Suporte": [
            'suporte', 'suporta', 'tripe', 'tripé', 'bastão', 'pau de selfie', 'estabilizador', 'ring light', 'braçadeira', 'ventosa'
        ],
        "Smartphone": [
            "smartphone", "iphone", "galaxy", "motorola", "moto g", " redmi ", "a56", "redemi", "a26",
            "poco", "realme", "14 pro", "15 pro", "s24", "s23", "x7", "128gb", "256gb", "not", "lg k62", "oukitel", "m7", "xiomi celular"
        ],
        "Celular Básico": [
            "celular basico", "celular para idosos", "idoso", "celular antigo", "nokia 150", "celular 150",
            "2g", "flip", "teclado numerico", "celular do idoso", "celular blu joy", "samsung sm-b310e", "botão grande", "celular simples", "celular lg", "celular nokia", "celular positivo", "Botão SOS"
        ],
        "Console": [
            "console", "playstation", "ps5", "xbox", "nintendo switch", "gamepad", "joystick", "dualsense", "controle de videogame"
        ],

        # 3. ACESSÓRIOS (Para captar antes do hardware)
        
        "Cabo": [
            "cabo usb", "cabo tipo c", "cabo"
        ],
        
        "Áudio": [
            "fone de ouvido", "headset", "earbuds", "airpods", "galaxy buds"
        ],
        
        # 4. OUTROS / CONSUMÍVEIS
        "Chip": [r"(?<!dual\s)(?<!com\s)chip", "pre-pago", "claro", "vivo", "tim", "oi", "cartao sim", "pré-pago", "smart card", "microchip", "minichip", "nanochip"],
        "Outros": ["tela de projeção", "projetores", "adaptador", "amplificador de tela", "sumup"],
        "Insumos": ["cola", "resina", "ferramenta", "limpeza", "reparo"]
    }
    
    # 1. TRUNCAGEM
    partes = re.split(r'\b(compatível|compativel| p/ | para | p/| p\. | para a | para o | e )\b', titulo)
    titulo_foco = partes[0] 
    padrao_comp = r'\b(para|p/|compatível|compativel)\b.*\b(mi band|smart band|smartwatch|iphone|galaxy)\b'

    # 2. ESCUDO DE ACESSÓRIOS (Prioridade Imediata)
    prioridade_imediata = ["Proteção","Carregador", "Cabo", "Suporte", "Acessório", "Áudio", "Insumos"]
    for cat in prioridade_imediata:
        for termo in categorias_map[cat]:
            if re.search(rf'^\s*{re.escape(termo)}\b', titulo_foco):
                
                if termo == "pulseira":
                    if re.search(r'\b(smart|mi|xiaomi|inteligente)\b', titulo_foco):
                        continue

                if cat in ["Proteção", "Cabo", "Suporte"]:
                    if preco < 200:
                        return cat
                    else:
                        continue
                
                if re.search(padrao_comp, titulo):
                    # Só classifica como acessório genérico se não for algo mais específico
                    if not any(titulo_foco.startswith(x) for x in ["carregador", "cabo", "fonte", "base carregador"]):
                        return "Acessório"

                if cat == "Acessório":
                    return cat
                    
                return cat
    
    if re.search(padrao_comp, titulo):
    # Se o título começa com "relógio inteligente" ou "smartwatch"
        if re.search(r'^(rel[oó]gio inteligente|smartwatch|rel[oó]gio smart)', titulo):
            pass  # continua fluxo normal
        else:
            return "Acessório"
                

    # 3. PRIORIDADE HARDWARE
    ordem_hardware = ["Óculos de Realidade Virtual", "Tablet", "Smartband", "Smartwatch", "Smartphone", "Celular Básico", "Console", "Chip"]
    
    for cat in ordem_hardware:
        for termo in categorias_map[cat]:
            if re.search(rf'\b{re.escape(termo)}\b', titulo_foco):
                
                # --- TRAVA 1: SEGURANÇA CONTRA CAPAS ---
                if cat in ["Smartphone", "Tablet"] and preco < 250:
                    # Se achou termo de smartphone mas é muito barato,
                    # interrompe a busca NESTA categoria e vai para a próxima (pode ser "Outros" ou "Acessório" depois)
                    break 

                # --- TRAVA 2: SEGURANÇA CONTRA "DUAL CHIP" FALSO ---
                if cat == "Chip" and "celular" in titulo_foco:
                    continue

                # Se passou pelas travas, é isso!
                return cat
    
    # 4. BUSCA GLOBAL (Backup)
    for cat in ordem_hardware:
        for termo in categorias_map.get(cat, []):
            if re.search(rf'\b{termo}\b', titulo):
                if cat in ["Smartphone", "Tablet"] and preco < 250: continue
                if cat == "Chip" and "celular" in titulo: continue
                return cat
                
    return "Outros"

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
    
    except Exception as e:
        logging.error(f"{e}")
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
        numeros = re.findall(r'\d+', texto_parcela.replace('.', ''))
        if len(numeros) >= 3:
            parcelas = int(numeros[0])
            valor_parcela = float(f"{numeros[1]}.{numeros[2]}")
            return round(parcelas * valor_parcela, 2)
    except Exception as e:
        logging.error(f"Erro ao calcular parcelamento: {texto_parcela} -> {e}")
        return 0.0
    return 0.0

