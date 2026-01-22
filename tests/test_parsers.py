from src.parsers import limpar_valor_simples_para_float, normalizar_texto, detectar_bundle

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
    # O sinal de '+' aqui é técnico, não deve ser bundle
    assert detectar_bundle("Xiaomi Redmi 14C 256GB 4+4GB RAM") is False
    assert detectar_bundle("Motorola Moto G54 8GB+8GB RAM Boost") is False
    assert detectar_bundle("Smartphone 128GB + 6GB RAM") is False

def test_falsos_positivos_tecnicos():
    """Testa se termos técnicos com sinais NÃO são detectadas como bundle."""
    assert detectar_bundle("Smartphone com NFC + Bluetooth") is False
    assert detectar_bundle("Celular Dual Sim + 4G") is False
    assert detectar_bundle("Smartphone Samsung Galaxy A16 128GB Verde Claro 5G 4GB RAM 6,7\" FHD+ Câm Tripla até 50MP + Selfie 13MP Bateria 5000mAh") is False
    assert detectar_bundle("Relógio Inteligente Smartwatch Redondo Masculino H-1 Serie 9 Original Compativel C/ Samsung Xiaomi - Laves") is False
    assert detectar_bundle('Smartphone Xiaomi POCO X7 256GB 8GB RAM tela de 6.67" camera 50+8+2MP 20MP') is False
    assert detectar_bundle("Carregador Turbo 125w USB-C Compatível com Xiaomi Samsung Motorola Quick Charger + GaNFast Moto G53 G54 Edge 30 40 50 - Tx - Original") is False
    assert detectar_bundle("Smartphone Motorola Moto G15, 50 MP + 5 MP, 256 GB, 4G, Verde - XT2521-2") is False
    assert detectar_bundle("Smartphone POCO C75 8+GB RAM 256GB, Preto - XIAOMI") is False

def test_bundles_reais():
    """Testa se combos verdadeiros SÃO detectados corretamente."""
    assert detectar_bundle("Smartphone Samsung Galaxy A54 + Fone Bluetooth") is True
    assert detectar_bundle("Kit 2 Pulseiras para Smartwatch") is True
    assert detectar_bundle("iPhone 15 com Brinde Capinha e Película") is True
    assert detectar_bundle("Combo Gamer: Mouse + Teclado") is True
    assert detectar_bundle("Relógio + 7 Pulseiras") is True
    