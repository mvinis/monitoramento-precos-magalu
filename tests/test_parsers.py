from src.parsers import limpar_valor_simples_para_float, normalizar_texto, detectar_bundle, categorizar_produto, montar_string_bundle
import pytest

def test_limpar_valor_real_brasileiro():
    """Valida se o conversor de moeda lida com pontos, vírgulas e R$"""
    assert limpar_valor_simples_para_float("R$ 1.299,50") == 1299.50
    assert limpar_valor_simples_para_float("2.500,00") == 2500.00

def test_normalizar_texto_com_unicode():
    """Valida a remoção do espaço invisível \xa0"""
    texto_sujo = "Smartphone\xa0Samsung "
    assert normalizar_texto(texto_sujo) == "Smartphone Samsung"

def test_limpar_valor_vazio():
    """Valida se a função retorna 0.0 para entradas inválidas"""
    assert limpar_valor_simples_para_float("N/A") == 0.0
    assert limpar_valor_simples_para_float("") == 0.0

def test_falsos_positivos_memoria_ram():
    """Testa se especificações de RAM NÃO são detectadas como bundle."""
    # O sinal de '+' é técnico, não deve ser bundle
    assert detectar_bundle("Xiaomi Redmi 14C 256GB 4+4GB RAM") is False
    assert detectar_bundle("Motorola Moto G54 8GB+8GB RAM Boost") is False
    assert detectar_bundle("Smartphone 128GB + 6GB RAM") is False

@pytest.mark.parametrize("titulo", [
    "Smartphone com NFC + Bluetooth",
    "Celular Dual Sim + 4G",
    "Smartphone Samsung Galaxy A16 128GB Verde Claro 5G 4GB RAM 6,7\" FHD+ Câm Tripla até 50MP + Selfie 13MP Bateria 5000mAh",
    'Smartphone Xiaomi POCO X7 256GB 8GB RAM tela de 6.67" camera 50+8+2MP 20MP',
    "Carregador Turbo 125w USB-C Compatível com Xiaomi Samsung Motorola Quick Charger + GaNFast Moto G53 G54 Edge 30 40 50 - Tx - Original",
    "Smartphone Motorola Moto G15, 50 MP + 5 MP, 256 GB, 4G, Verde - XT2521-2",
    "Smartphone POCO C75 8+GB RAM 256GB, Preto - XIAOMI",
    "Suporte Garra Celular P/ Motos Universal Com Carregador Usb - +BR"
])
def test_falsos_positivos_tecnicos(titulo):
    assert detectar_bundle(titulo) is False


def test_bundles_reais():
    """Testa se combos verdadeiros SÃO detectados corretamente."""
    assert detectar_bundle("Smartphone Samsung Galaxy A54 + Fone Bluetooth") is True
    assert detectar_bundle("Kit 2 Pulseiras para Smartwatch") is True
    assert detectar_bundle("iPhone 15 com Brinde Capinha e Película") is True
    assert detectar_bundle("Combo Gamer: Mouse + Teclado") is True
    assert detectar_bundle("Relógio + 7 Pulseiras") is True
    assert detectar_bundle("Relógio digital Smart inteligente Hw12 41mm com pulseira metal extra - Smart Bracelet") is True

def test_match_categorias():
    """
    Valida a lógica de classificação de produtos (Hardware vs Acessórios).

    Este teste garante que a função `categorizar_produto` aplique corretamente as 
    regras de regex e travas de preço para distinguir produtos com nomes similares.

    Cenários Cobertos:
    ------------------
    1. Proteção: Garante que capas/cases não sejam confundidas com o aparelho.
    2. Acessórios: Valida se pulseiras (baratas) são separadas dos relógios.
    3. Smartwatch Genérico: Testa se um relógio barato (mas acima do corte de acessório) 
       é mantido como Hardware e não descartado.
    4. Celular Básico: Verifica a detecção de Feature Phones (Nokia, etc).
    5. Smartwatch Infantil: Garante que relógios de crianças (com GPS/Chip) sejam 
       classificados como Hardware, apesar do preço baixo.

    Raises:
        AssertionError: Se a categoria retornada for diferente da esperada.
    """
    
    titulo_capa = "Capa Protetora Anti Impacto edge 60 e edge 60 fusion - Motorola"
    assert categorizar_produto(titulo_capa.lower(), titulo_capa, 89.10) == "Proteção"
    
    titulo_pulseira = "Pulseira Relógio Smartwatch Compatível D20 D13 Y68"
    assert categorizar_produto(titulo_pulseira.lower(), titulo_pulseira, 9.21) == "Acessório"

    titulo_relogio_smartwatch = "Relógio Inteligente Para Vivo V21 - generico"
    assert categorizar_produto(titulo_relogio_smartwatch.lower(), titulo_relogio_smartwatch, 189) == "Smartwatch"

    titulo_celular_basico = "Celular 150 4G Dual Chip Com Câmera lançamento 4G - nokia"
    assert categorizar_produto(titulo_celular_basico.lower(), titulo_celular_basico, 299.0) == "Celular Básico"

    titulo_smartwatch_infantil = "Relógio SmartWatch Infantil Com Rastreador GPS Chip e Câmera - Plus Distribuidora"
    assert categorizar_produto(titulo_smartwatch_infantil.lower(), titulo_smartwatch_infantil, 111.06) == "Smartwatch"

def test_detectar_bundle_relogio_pulseira():
    titulo = "Relógio digital Smart inteligente Hw12 41mm com pulseira metal extra - Smart Bracelet"
    titulo_low = titulo.lower()
    preco = 158.64

    # 1. Primeiro descobre o item principal
    cat_base = categorizar_produto(titulo_low, titulo, preco)
    assert cat_base == "Smartwatch"  # Isso deve ser verdade

    # 2. Agora aplica a lógica de Bundle
    resultado_final = montar_string_bundle(cat_base, titulo_low)

    # 3. Verifica conjunto
    assert "Smartwatch" in resultado_final
    assert "Acessório" in resultado_final
    
    partes = resultado_final.split(" + ")
    assert set(partes) == {"Smartwatch", "Acessório"}

def test_detectar_bundle_garrafa_smartwatch_fone():
    titulo = "Kit Garrafa térmica 500ml inox sensor Led + Smartwatch Y8 + Fone Bluetooth - KIT ACADEMIA"
    titulo_low = titulo.lower()
    preco = 127

    # 1. Primeiro descobre o item principal
    cat_base = categorizar_produto(titulo_low, titulo, preco)
    assert cat_base == "Smartwatch"

    # 2. Agora aplica a lógica de Bundle (O que faltava no teste)
    resultado_final = montar_string_bundle(cat_base, titulo_low)

    # 3. Verifica conjunto
    assert "Smartwatch" in resultado_final
    assert "Acessório" in resultado_final
    assert "Áudio" in resultado_final

    partes = resultado_final.split(" + ")
    assert set(partes) == {"Smartwatch", "Acessório", "Áudio"}
    