import re
import logging
from rapidfuzz import process, fuzz

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
   
    categoria_base = categorizar_produto(titulo_low, p_credito_avista)

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
        'caneta': 'Acessório', 'mouse': 'Acessório', 'teclado': 'Acessório', 'antena': 'Acessório',
        'pulseira': 'Acessório', 'carteira':'Acessório',
        'capa': 'Proteção', 'capinha': 'Proteção',
        'fone': 'Áudio', 
        'cabo': 'Cabo',
        'fonte': 'Fonte',
        'carregador':'Carregador',
        'óculos de realidade virtual': 'Óculos de Realidade Virtual',
        'smartwatch': 'Smartwatch', 'smart watch': 'Smartwatch',
        'smartband': 'Smartband',
        'garrafa': 'Acessório','garrafa térmica': 'Acessório',
        'celular básico': 'Celular Básico', 'celular rural': 'Celular Básico',
        'a26' : 'Smartphone',
        'fit 3': 'Smartband',
        'galaxy fit': 'Smartband',
        'mi band': 'Smartband',
        'smartwatch': 'Smartwatch', 'smart watch': 'Smartwatch', 'galaxy watch': 'Smartwatch', 'apple watch': 'Smartwatch',
        'smartband': 'Smartband', 'fit 3': 'Smartband', 'mi band': 'Smartband', 'galaxy fit': 'Smartband',
        'reparo de tela':'Outros',
        'pelúcia':'Outros'
    }

    # Verifica se é um hardware (para ativar a proteção da pulseira)
    is_hardware_principal = any(v in base.lower() for v in ['smartwatch', 'smartband', 'smartphone', 'tablet'])
    tem_combo_real = re.search(r'\b(com|kit|combo|e)\b|\+|&', titulo_low)

    # 🔒 TRAVA DEFINITIVA
    if not tem_combo_real:
        return base

    for termo, nome_exibicao in extras.items():
        padrao = re.escape(termo)
        if re.search(padrao, titulo_low):

            if nome_exibicao.lower() in base.lower():
                continue

            # 👇 NOVA TRAVA
            if not tem_combo_real:
                continue
                
            # Detecta se o hardware principal está só sendo mencionado
            if is_hardware_principal and "película" in titulo_low:
                # O produto é só proteção, ignora adicionar Smartwatch
                tem_combo_real = False

    for termo, nome_exibicao in extras.items():
        padrao = rf'\b{re.escape(termo)}s?\b'
        if re.search(padrao, titulo_low):

            if nome_exibicao.lower() in base.lower():
                continue

            if nome_exibicao == "Acessório" and is_hardware_principal and "pulseira" in termo:
                padrao_extra = r'(extra|reserva|kit|\d+|brinde)\s*.*pulseira|pulseira.*\s*(extra|reserva|kit|\d+|brinde)'
                match_extra = re.search(padrao_extra, titulo_low)
                match_com = re.search(r'\bcom\b.*\bpulseira', titulo_low)

                if match_extra or match_com:
                    componentes.append(nome_exibicao)
                else:
                    continue
            else:
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
    match_acessorios = re.search(r'\d+\s*(un|unid|unidades|x)?\s*(pulseiras?|fones?|pel[íi]culas?|capas?|case|tiras?)', titulo_limpo)
    # Detecta pulseira EXTRA
    match_pulseira_extra = re.search(
        r'(com\s+)?pulseira\s+(extra|metal|reserva|adicional|\d+)',
        titulo_limpo
    )

    if match_pulseira_extra:
        return True

    # 1. Palavras-chave de itens extras (Voltando para a lista segura)
    itens_adicionais = ['brinde', 'kit', 'combo', 'par de']
    tem_item_extra = any(k in titulo_limpo for k in itens_adicionais)

    # 2. DETECTOR CIRÚRGICO DE SOMA EXPLICITA (+)
    # Procura especificamente se o sinal de + está imediatamente antes de um eletrônico/acessório real.
    # Ex: Pega "... + Fit 3" e "... + Carregador", mas IGNORA "... + GaNFast" e "... + BR"
    # padrao_soma = r'\+\s*(fit|watch|buds|airpods|fone|carregador|fonte|cabo|capa|capinha|pel[íi]cula)\b'
    padrao_soma = r'\+\s*(\d+\s*(un|x|unid|unidades)?\s*)?(fit|watch|buds|airpods|fone|carregador|fonte|cabo|capa|capinha|pel[íi]cula)\b'
    match_soma_explicita = re.search(padrao_soma, titulo_limpo)

    if match_soma_explicita:
        return True

    # 3. FILTRO FINAL DE SEGURANÇA
    # Se ainda sobrou um sinal, mas o título é carregado de termos técnicos e não tem "kit/brinde"
   # 3. FILTRO FINAL DE SEGURANÇA
    if tem_sinal and not tem_item_extra and not bool(match_acessorios):
        # Lista atualizada com 'sensor', 'toque', 'tela', 'bluetooth', etc.
        termos_specs = ['br', 'nfc', 'nf', 'gb', 'mb', '5g', '4g', 'dual', 'sim', 'mah', 'bateria', 'biometria', 'nfe', 'camera', 'samsung xiaomi', 'ganfast', 'mp', 'usb', 'gps', 'sensor', 'tela', 'toque', 'led', 'lcd', 'bluetooth', 'wifi', 'wi-fi', 'medidor', 'monitor']
        if any(t in titulo_limpo for t in termos_specs):
            return False
    
    # Detecta padrão explícito de bundle com acessório
    if re.search(r'\bcom\b.*\b(pulseira|cabo|fone|capinha|capa)\b', titulo_limpo):
        return True

    return bool(match_acessorios) or bool(match_qtd_unidades) or tem_item_extra or tem_sinal

def categorizar_produto(titulo, preco):

    categorias_map = get_categorias_multilingue()

    categorias_espanhol = {
    "Proteção": [
        "capa", "capinha", "funda", "película", "vidrio templado", "case"
    ],
    "Carregador": [
        "cargador", "fuente", "adaptador", "power bank"
    ],
    "Acessório": [
        "estación", "soporte", "dock", "hub", "base", "adaptador", "braçadeira"
    ],
    "Console": [
        "ps5", "playstation", "xbox", "nintendo switch"
    ],
    "Smartphone": [
        "smartphone", "celular", "móvil"
    ],
    "Smartwatch": [
        "smartwatch", "reloj inteligente", "galaxy watch", "apple watch"
    ],
    "Smartband": [
        "smartband", "pulsera inteligente", "mi band", "fit 3"
    ]
}

    titulo = corrigir_erros_digitacao(titulo)

    # 1. TRUNCAGEM
    partes = re.split(r'\b(compatível|compativel| p/ (?!idosos?)| para (?!idosos?)| p/(?!idosos?)| p\. (?!idosos?)| p\.(?!idosos?)| para a | para o | e )\b', titulo)
    titulo_foco = partes[0]

    padrao_aspirador = r'^(([\d,\s]+|ou\s+)+(x|un|unids?|unidades?|pcs|pe[çc]as?)?\s*|kit\s+(de\s+)?|combo\s+(de\s+)?|pacote\s+(com\s+)?|\d+\s*em\s*\d+\s*)+'
    titulo_foco_limpo = re.sub(padrao_aspirador, '', titulo_foco).strip()

    padrao_comp = r'\b(para|p/|compatível|compativel)\b.*\b(mi band|smart band|smartwatch|iphone|galaxy)\b'

    titulo_sem_kit = titulo_foco

        # 🔒 FAST TRACK ABSOLUTO PARA FONTE / CARREGADOR
    if re.search(r'^\s*(fonte|carregador)\b', titulo_foco):
        return "Carregador"
    
    # 🔒 Só força Carregador se for KIT ou BATERIA de reposição, ignora especificação de bateria
    if re.search(r'\b(kit de bateria|bateria de reposi[cç][aã]o|bateria portátil|bateria celular avulsa)\b', titulo, re.IGNORECASE):
        return "Carregador"

    if titulo_foco.startswith("kit "):
        titulo_sem_kit = re.sub(r'^kit\s+', '', titulo_foco)
    
    # PROTEÇÃO CONTRA ESPECIFICAÇÃO DE BATERIA
    if re.search(r'\bbateria\b', titulo, re.IGNORECASE):
        if re.search(r'\d+\s*mah|\d+\s*dias|de|até|duração', titulo, re.IGNORECASE):
            pass
        elif re.search(r'\b(kit de bateria|bateria de reposi[cç][aã]o|bateria portátil|bateria celular avulsa)\b', titulo, re.IGNORECASE):
            return "Carregador"
        
    if re.search(r'\bpau\b.*\bselfie\b', titulo):
        return "Suporte"
    
    for cat in ["Áudio", "Carregador", "Cabo", "Proteção"]:
        for termo in categorias_map[cat]:
            if re.search(rf'^\b{re.escape(termo)}\b', titulo_sem_kit):
                return cat
            
    # --- FAST TRACK PARA CATEGORIAS IMEDIATAS ---
    for cat in ["Áudio", "Carregador", "Cabo", "Proteção"]:
        for termo in categorias_map[cat]:
            # O 's?' no final permite que ele encontre tanto "película" quanto "películas"
            if re.search(rf'^\b{re.escape(termo)}s?\b', titulo_foco_limpo):
                return cat

    # 2. ESCUDO DE ACESSÓRIOS (Prioridade Imediata)
    prioridade_imediata = ["Proteção","Carregador", "Cabo", "Suporte", "Acessório", "Áudio", "Insumos", "Outros"]
    for cat in prioridade_imediata:
        for termo in categorias_map[cat]:
            if re.search(rf'^\s*{re.escape(termo)}\b', titulo_foco_limpo):
                
                if termo == "pulseira":
                    if re.search(r'\b(smart|mi|xiaomi|inteligente)\b', titulo_foco):
                        continue

                if cat in ["Proteção", "Cabo"]:
                    if preco < 200:
                        return cat
                    else:
                        continue
        
                    
                return cat
    
    if re.search(padrao_comp, titulo):
    # Se o título começa com "relógio inteligente" ou "smartwatch"
        if re.search(r'^(rel[oó]gio inteligente|smartwatch|rel[oó]gio smart)', titulo):
            pass
            
        # Adicionamos variações de protetor de tela na trava de segurança
        elif re.search(r'\b(capa|capinha|pel[íi]cula|case|protetor(es)? de tela)\b', titulo, re.IGNORECASE):
            return "Proteção"
            
        else:
            return "Acessório"
            
    if re.search(r'^\s*(carregador|cabo|fonte|base carregador|power bank|powerbank)\b', titulo):
        return "Carregador"
                        
    ordem_hardware = ["Óculos de Realidade Virtual", "Tablet", "Suporte", "Celular Básico", "Smartphone", "Smartband", "Smartwatch", "Carregador", "Console", "Chip"]

    categorias_detectadas = []

    for cat in ordem_hardware:
        for termo in categorias_map[cat]:
            if re.search(rf'\b{re.escape(termo)}s?\b', titulo_foco, re.IGNORECASE):

                if cat in ["Smartphone", "Tablet"] and preco < 250:
                    continue

                if cat == "Chip" and "celular" in titulo:
                    continue

                if cat not in categorias_detectadas:
                    categorias_detectadas.append(cat)

    if categorias_detectadas:
        return categorias_detectadas[0]
        
    # 4. BUSCA GLOBAL DE ACESSÓRIOS (A Rede de Segurança)
    ordem_acessorios_backup = ["Proteção", "Carregador", "Cabo", "Suporte", "Áudio", "Insumos", "Acessório"]
    
    for cat in ordem_acessorios_backup:
        for termo in categorias_map[cat]:
            if re.search(rf'\b{re.escape(termo)}s?\b', titulo, re.IGNORECASE):
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

def capitalizar_categoria(texto):
    palavras_minusculas = {"de", "da", "do", "das", "dos", "e", "para"}
    # 👇 Nova lista VIP de siglas e exceções
    siglas = {"LCD", "USB", "BGA", "VR", "TV", "FM", "GPS", "NFC", "SOS"}
    
    palavras = texto.split()
    resultado = []
    
    for i, palavra in enumerate(palavras):
        # 1ª Regra: Se a palavra for uma sigla, deixa tudo maiúsculo
        if palavra.upper() in siglas:
            resultado.append(palavra.upper())
            
        # 2ª Regra: Se for preposição (e não for a 1ª palavra), deixa minúsculo
        elif palavra.lower() in palavras_minusculas and i != 0:
            resultado.append(palavra.lower())
            
        # 3ª Regra: Restante das palavras em Title Case
        else:
            resultado.append(palavra.capitalize())
    
    return " ".join(resultado)

def corrigir_erros_digitacao(texto):
    """
    Uso de Fuzzy Matching para corrigir erros de digitação comuns no e-commerce.
    Avalia palavra por palavra e substitui se a similaridade for >= 85%.
    """
    # 1. "Dicionário de Ouro" (Palavras que nos importam)
    vocabulario_alvo = [
        "bateria", "película", "pelicula", "carregador", "smartwatch", "smartband", 
        "pulseira", "capinha", "fone", "bluetooth", "cabo", "fonte", "celular"
    ]
    
    palavras = re.findall(r'\b\w+\b', texto.lower())
    texto_corrigido = texto.lower()

    for palavra in palavras:

        resultado = process.extractOne(palavra, vocabulario_alvo, scorer=fuzz.ratio)

        if not resultado:
            continue

        palavra_correta, score, _ = resultado

        # 🚨 NOVA TRAVA IMPORTANTE
        # Só corrige se:
        # 1) Similaridade alta
        # 2) A diferença de tamanho for pequena (erro de digitação real)
        if 85 <= score < 100 and abs(len(palavra) - len(palavra_correta)) <= 2:
            
            logging.debug(
                f"🛠️ Fuzzy Match: Corrigindo '{palavra}' para '{palavra_correta}' (Score: {score}%)"
            )

            texto_corrigido = re.sub(
                rf'\b{palavra}\b',
                palavra_correta,
                texto_corrigido
            )
                
    return texto_corrigido

def get_categorias_multilingue():

    """
    Retorna um dicionário de categorias de produtos com termos associados em múltiplos idiomas.

    A função combina categorias principais em português com extensões em espanhol, permitindo
    a classificação ou detecção de produtos com base em palavras-chave. Cada categoria é
    mapeada para uma lista de termos que podem aparecer em títulos de produtos ou descrições.
    
    Retorno:
        dict: Dicionário onde cada chave é uma categoria e o valor é uma lista de termos
              em português e espanhol associados àquela categoria.
    """

    categorias_pt = {
        
            "Proteção": [
                "capa", "capinha", "case", "pelicula", "película", "vidro temperado", "anti queda", "vidro temperado", "protetor de tela", "protetores de tela"
            ],
            "Óculos de Realidade Virtual": [
                "óculos vr", "óculos inteligente", "vr", "óculos de realidade virtual", "óculos vr realidade virtual"
            ],
            "Carregador": [
                "carregador", "fonte", "adaptador tomada", "carregamento rapido", "turbo", "power bank", "powerbank", "bateria", "bateria celular", 
                "bateria portátil", "carregador portátil", "base carregador", "banco de potência"
            ],
            "Smartwatch": [
                "smartwatch", "apple watch", "galaxy watch", "relogio inteligente", "smart watch", "microwear",
                "relógio inteligente", "hw", "hw12", "w28", "ultra 9", "series 9", "relógio smart", "gps", "relógio smartwatch", "relógio smart watch", 
                "garmin forerunner", "celular de pulso", "relógio digital", "relógio digital smart inteligente", "xiaomi watch", "plumzong", "smart digital"
            ],
            "Smartband": [
                "smartband", "pulseira mi", "smart band", "mi band", "pulseira inteligente", "galaxy fit", "relógio band",
                "fit 3", "d20", "m6", "w69", "gl08", "y68", "fitpro", "hryfine", "m3 band", "m4 band", "xufeng", "relógio smart", 
                "relógio de pulso", "relógio bracelet", " pulseira inteligente ", "s10", "t800", "smartach", "relógio esportivo", 
                "relógio fitness", "xiaomi smart band", "relógio digital sport", "pulseira esportiva", "amazfit band"
            ],
            "Tablet": [
                "tablet", "ipad", "galaxy tab", "xiaomi pad", "lenovo tab"
            ],
            "Acessório": [
                "pulseira","band", "smarttag", "localizador", "mili mitag", "airtag", "cordão", "bolsa", "carteira", "controle remoto", "garrafa térmica", "moto tag", "pulseira de silicone", "monitor de frequência cardíaca", "pulseira de monitor de frequência cardíaca",
                "bracelet de silicone", "antena", "correa", "alça de telefone", "cinto de corrida", "grip"
            ],
            "Suporte": [
                'suporte', 'tripe', 'tripé', 'bastão', 'pau de selfie', 'estabilizador', 'ring light', 'braçadeira', 'ventosa', 'vara de mão', 'bastão suporte'
            ],
            "Smartphone": [
                "smartphone", "iphone", "galaxy", "motorola", "moto g", " redmi ", "a56", "redemi", "a26",
                "poco", "realme", "14 pro", "15 pro", "s24", "s23", "x7", "128gb", "256gb", "not", "lg k62", "oukitel", "m7", "xiomi celular", 'xiaomi 14t'
            ],
            "Celular Básico": [
                "celular basico", "celular para idoso", "celular para idosos", "idoso", "idosos", "celular antigo", "nokia 150", "celular 150", "celular rural",
                "2g", "teclado numerico", "celular do idoso", "celular blu joy", "samsung sm-b310e", "botão grande", "celular simples", "celular lg", "celular nokia", "celular positivo", "Botão SOS",
                "multilaser up", "up play", "p9134", "tela 1.8", "tela 2.4", "feature phone", "celular p/ idoso", 
                "positivo p2", "positivo p26", "celular fácil", "celular de tecla"
            ],
            "Console": [
                "console", "playstation", "ps5", "xbox", "nintendo switch", "gamepad", "joystick", "dualsense", "controle de videogame"
            ],

            # 3. ACESSÓRIOS (Para captar antes do hardware)
            
            "Cabo": [
                "cabo usb", "cabo tipo c", "cabo", "cabo lightning", "cabo micro usb", "cabo de dados", "cabo de carregamento", "cabo de carga", "cabo de energia", "cabo de sincronização"
            ],
            
            "Áudio": [
                "fone de ouvido", "headset", "earbuds", "airpods", "galaxy buds", "alto-falante", "fone bluetooth", "fones sem fio", "fone sem fio", "fone bluetooth", "caixa de som", "caixa de som bluetooth", "caixa de som portátil"
            ],
            
            # 4. OUTROS / CONSUMÍVEIS
            "Chip": [r"(?<!dual\s)(?<!com\s)chip", "pre-pago", "claro", "vivo", "tim", "oi", "cartao sim", "pré-pago", "smart card", "microchip", "minichip", "nanochip"],
            "Outros": ["tela de projeção", "projetores", "adaptador", "amplificador de tela", "sumup", "porta-chaves", "placa dock de carga", "flex power", "flex volume",
                "dock de carga", "placa flex", "reparo de tela", "botão", "botões", "gatilho", "mola", "analógico", "escova principal", "aspirador", "robo de limpeza", "pelúcia"],
            "Insumos": ["cola", "resina", "ferramenta", "limpeza", "espatulas", "pá"]
    }
    
    categorias_es = {
        "Proteção": ["capa", "capinha", "funda", "película", "vidrio templado", "case"],
        "Carregador": ["cargador", "fuente", "adaptador", "power bank"],
        "Acessório": ["estación", "soporte", "hub", "base", "adaptador", "braçadeira"],
        "Console": ["ps5", "playstation", "xbox", "nintendo switch"],
        "Smartphone": ["smartphone", "celular", "móvil"],
        "Smartwatch": ["smartwatch", "reloj inteligente", "galaxy watch", "apple watch"],
        "Smartband": ["smartband", "pulsera inteligente", "mi band", "fit 3"]
    }

    for cat, termos in categorias_es.items():
        if cat in categorias_pt:
            categorias_pt[cat].extend(termos)
        else:
            categorias_pt[cat] = termos

    return categorias_pt
