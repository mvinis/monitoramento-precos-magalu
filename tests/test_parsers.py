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
    assert detectar_bundle("Kit de bateria para relógio inteligente Suunto Core Lumi t4 t3 e t1 - Marca Própria") is True
    assert detectar_bundle("Pulseira Inteligente Xiaomi Smart Band 10 Tela AMOLED com 150 modos esportivos, Recursos Premium de Monitoramento e Bateria Até 21 Dias") is False
    assert detectar_bundle("A26 5G (256GB) - Branco + Fit 3 - Grafite - Samsung") is True
    assert detectar_bundle("Smartphone Infinix Hot 11S 128GB Verde 4G 6GB RAM 6,78” Câm. Tripla + Selfie 8MP") is False

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
    assert categorizar_produto(titulo_capa.lower(), 89.10) == "Proteção"
    
    titulo_pulseira = "Pulseira Relógio Smartwatch Compatível D20 D13 Y68"
    assert categorizar_produto(titulo_pulseira.lower(), 9.21) == "Acessório"

    titulo_relogio_smartwatch = "Relógio Inteligente Para Vivo V21 - generico"
    assert categorizar_produto(titulo_relogio_smartwatch.lower(), 189) == "Smartwatch"

    titulo_celular_basico = "Celular 150 4G Dual Chip Com Câmera lançamento 4G - nokia"
    assert categorizar_produto(titulo_celular_basico.lower(), 299.0) == "Celular Básico"

    titulo_smartwatch_infantil = "Relógio SmartWatch Infantil Com Rastreador GPS Chip e Câmera - Plus Distribuidora"
    assert categorizar_produto(titulo_smartwatch_infantil.lower(), 111.06) == "Smartwatch"

    titulo_pulseira_mi_smart = "Pulseira MI Smart Band 6 Xiaomi, Display AMOLED, Função Esportiva, Preto - BAND 6"
    assert categorizar_produto(titulo_pulseira_mi_smart.lower(), 1010.52) == "Smartband"
   
    titulo_smartwatch_xiaomi = "Xiaomi Watch 5 Active Branco Alta Durabilidade"
    assert categorizar_produto(titulo_smartwatch_xiaomi.lower(), 1147) == "Smartwatch"

    titulo_pulseiro_de_monitor = "Pulseira de monitor de frequência cardíaca COROS cinza grande"
    assert categorizar_produto(titulo_pulseiro_de_monitor.lower(), 229.53) == "Acessório"

    titulo_bracelet_de_silicone = "Bracelete De Silicone Para Mi Band 3 / 4 Xiaomi, Laranja"
    assert categorizar_produto(titulo_bracelet_de_silicone.lower(), 39.99) == "Acessório"

    titulo_pulseira_silicone_para_samsung = "Pulseira de silicone para Samsung Galaxy Fit 2 R220 rosa - Lightbek Official Store"
    assert categorizar_produto(titulo_pulseira_silicone_para_samsung.lower(), 234.50) == "Acessório"

    titulo_relogio_plumzong_monitor = "Relógio Plumzong Feminino Inteligente Pulseira Monitor De Freqüência Cardíaca - ElaShopp"
    assert categorizar_produto(titulo_relogio_plumzong_monitor.lower(), 729.30) == "Smartwatch"
    
    titulo_pulseira_inteligente_xiaomi_smartband = "Pulseira Inteligente Xiaomi Smart Band 10 Preto"
    assert categorizar_produto(titulo_pulseira_inteligente_xiaomi_smartband.lower(), 600) == "Smartband"
    
    titulo_pulseira_inteligente_xiaomi_smartband = "Pulseira Inteligente Xiaomi Smart Band 10 Preto"
    assert categorizar_produto(titulo_pulseira_inteligente_xiaomi_smartband.lower(), 600) == "Smartband"
    
    titulo_pulseira_inteligente_xiomi = "Pulseira Inteligente Xiaomi Smart Band 10 Tela AMOLED com 150 modos esportivos, Recursos Premium de Monitoramento e Bateria Até 21 Dias"
    assert categorizar_produto(titulo_pulseira_inteligente_xiomi.lower(), 1100) == "Smartband"

    titulo_relogio_inteligente = "Relógio Inteligente Para Samsung Galaxy A54 - generico"
    assert categorizar_produto(titulo_relogio_inteligente.lower(), 187.97) == "Smartwatch"

    titulo_pulseira_esportiva_nsmart = "Pulseira Esportiva NSmart compatíveis com smartwatch Verge e verge Lite."
    assert categorizar_produto(titulo_pulseira_esportiva_nsmart.lower(), 1719.71) == "Acessório"

    titulo_correa = "Correa para Reloj Inteligente XIAOMI Mi Smart Watch 10 Resistente al Agua 5ATM"
    assert categorizar_produto(titulo_correa.lower(), 574.84) == "Acessório"

    titulo_carregador_para_mi_band = "Carregador para Mi Band 4 Pulseira Inteligente - KAPBOM"
    assert categorizar_produto(titulo_carregador_para_mi_band.lower(), 89.70) == "Carregador"

    titulo_smartband_mix_smartwatch = "Smartwatch Pulseira Xiaomi Smart Band 9 Active"
    assert categorizar_produto(titulo_smartband_mix_smartwatch.lower(), 248) == "Smartband"
    
    titulo_kit_bateria = "Kit de bateria para relógio inteligente Suunto Core Lumi t4 t3 e t1 - Marca Própria"
    assert categorizar_produto(titulo_kit_bateria.lower(), 391) == "Carregador"

    titulo_relogio_band = "Relógio Band Fintie Gizmo Watch 3 2 1/Gabb Watch 3 2 1 Nylon"
    assert categorizar_produto(titulo_relogio_band.lower(), 142.83) == "Smartband"

    titulo_relogio_esportivo_coros = "Relógio esportivo COROS PACE 3"
    assert categorizar_produto(titulo_relogio_esportivo_coros.lower(), 1740) == "Smartband"

    titulo_haylou_smartwatch = "Haylou RS4 Smartwatch com Tela AMOLED Bateria de até 25 dias. Monitoramento de Saúde, Modos de Treinamento"
    assert categorizar_produto(titulo_haylou_smartwatch.lower(), 440) == "Smartwatch"

    titulo_smartwatch_xiaomi_haylou = "Relógio Smartwatch XiaomiMi Haylou Watch 2 Pro Bluetooth 5.3 Tela De 1,85 HD Display Original Bateria de longa Duração Sicroniza Com Strava"    
    assert categorizar_produto(titulo_smartwatch_xiaomi_haylou.lower(), 288) == "Smartwatch"
    
    titulo_smartband_mix_smartwatch_segundo = "Relógio Smartwatch Smartband Fitness Huawei Band 9 Bateria 14 Dias 100 Treinos"    
    assert categorizar_produto(titulo_smartband_mix_smartwatch_segundo.lower(), 347) == "Smartband"

    titulo_bastao_selfie = "Bastão de selfie compacto Power Grip Vivitar para GoPro HF-PG5200"    
    assert categorizar_produto(titulo_bastao_selfie.lower(), 270) == "Suporte"
    
    titulo_pau_de_selfie = "Pau d selfie - Kapaom"    
    assert categorizar_produto(titulo_pau_de_selfie.lower(), 49.05) == "Suporte"

    titulo_vara_de_mao = "Vara de Mão Flutuante para Selfie à Prova dÁgua com Alça de Pulso Compatível com Câmeras de Ação 15m Controle Wireless - Vedo"    
    assert categorizar_produto(titulo_vara_de_mao.lower(), 138) == "Suporte"

    titulo_tripe_telefone = "Tripé de Telefone SENSYNE 67 com Selfie Stick e Controle Remoto - Prata"    
    assert categorizar_produto(titulo_tripe_telefone.lower(), 327) == "Suporte"
    
    titulo_bastao_flutuante = "Bastão Flutuante The Handler 3.0 Original GoPro - AFHGM-003"    
    assert categorizar_produto(titulo_bastao_flutuante.lower(), 441) == "Suporte"

    titulo_bastao_suporte_moto = "Bastão Suporte Moto p/ Câmera 360 Graus Efeito Invisível Insta360 Extensor Retrátil Alumínio Sport - CLICK"    
    assert categorizar_produto(titulo_bastao_suporte_moto.lower(), 269) == "Suporte"

    titulo_powerbank_portatil = "PowerBank Carregador Portátil 20000 mAh Power Bank Anatel Original A'Gold - A' gold"    
    assert categorizar_produto(titulo_powerbank_portatil.lower(), 116) == "Carregador"

    titulo_bateria_portatil = "Bateria Portátil Power Bank Magsafe Compativel Com iPhone 11 12 13 14 15 - Single"    
    assert categorizar_produto(titulo_bateria_portatil.lower(), 125) == "Carregador"

    titulo_carregador_powerbank_lightning = "Powerbank Carregador Portátil 2000mah Lightning Chaveiro - RPC"    
    assert categorizar_produto(titulo_carregador_powerbank_lightning.lower(), 56) == "Carregador"

    titulo_carregador_portatil_turbo = "2X Carregador Portátil Power Bank Turbo I2Go 20000Mah 20W Co"    
    assert categorizar_produto(titulo_carregador_portatil_turbo.lower(), 1051) == "Carregador"

    titulo_banco_potencia = "Banco de potência Anker PowerCore 10K 10.000mAh USB-C 5V/3A"    
    assert categorizar_produto(titulo_banco_potencia.lower(), 285) == "Carregador"

    titulo_carregador_anker = "Anker Carregador Portátil USB tripla S/fio 25.000 mAh Prata"    
    assert categorizar_produto(titulo_carregador_anker.lower(), 3457) == "Carregador"

    titulo_powerbank_magnetico = "Novo Powerbank Carregador Portátil Magnético 10.000 Mah Universal com 4 Saídas de Carregamento Cor Preto - Power Bank"    
    assert categorizar_produto(titulo_powerbank_magnetico.lower(), 292) == "Carregador"

    titulo_cabo_usb_turbo = "Cabo Carregador Usb Turbo Compativel Para Fone Xiaomi Red Airdots 2 Top - HREBOS"    
    assert categorizar_produto(titulo_cabo_usb_turbo.lower(), 27.90) == "Cabo"
    
    titulo_tripe_preto = "Tripé Preto Para Celular Flexivel E Camera - DUKIE"
    assert categorizar_produto(titulo_tripe_preto.lower(), 17.90) == "Suporte"

    titulo_estabilizador_soleste = "Estabilizador De Imagem Soleste Tripé de Mesa Gravação Vídeo Foto Selfie Vlog Suporte Para Celular Universal Cor Branco - Leffa Shop"
    assert categorizar_produto(titulo_estabilizador_soleste.lower(), 72) == "Suporte"

    titulo_kit_tripe_retratil = "Kit Completo: Tripé Retrátil para Celular + Nota Fiscal - Monac"
    assert categorizar_produto(titulo_kit_tripe_retratil.lower(), 72) == "Suporte"

    titulo_kit_tripe_aluminio = "Kit Tripé Alumínio Universal 1,02 M Suporte P Celular Câmera - Inboxmobile"
    assert categorizar_produto(titulo_kit_tripe_aluminio.lower(), 42) == "Suporte"

    titulo_kit_tripe_mesa = "Mini Tripé De Mesa Flexível 360 Suporte Smartphone Vermelho - Worldview"
    assert categorizar_produto(titulo_kit_tripe_mesa.lower(), 82) == "Suporte"

    titulo_registro_tripe = "Registro Profissional: Tripé Portátil para Smartphones e Câmeras - Entrega Expressa - Monac"
    assert categorizar_produto(titulo_registro_tripe.lower(), 72.80) == "Suporte"

    titulo_teleprompter_baby = "Teleprompter Baby Retrátil 11+ Tripé + Suporte Smartphone - Texano"
    assert categorizar_produto(titulo_teleprompter_baby.lower(), 726.30) == "Suporte"

    titulo_carregador_classic = "2X Carregador Samsung Galaxy Watch Classic 4 3 Active2, Cabo"
    assert categorizar_produto(titulo_carregador_classic.lower(), 184) == "Carregador"

    titulo_peliculas_hidrogel = "1,3 ou 5 Películas Hidrogel HD Para Garmin Forerunner 965 955 745 645 6265 255 620 630 225 230 235 2 - São Jorge Fábrica e Distribuidora"
    assert categorizar_produto(titulo_peliculas_hidrogel.lower(), 31) == "Proteção"

    titulo_bateria_compativel = "Bateira Compatível Galaxy M14 5g Bm146aby Nfe."
    assert categorizar_produto(titulo_bateria_compativel.lower(), 198) == "Carregador"

    titulo_smartphone_celular_xiaomi = "Smartphone Celular Xiaomi Redmi Note 14 PRO 5G 256GB 8GB NFC Câmera tripla 200MP 4K Tela AMOLED 120Hz Aparelho Premium com IA Carregador 45W Atmos"
    assert categorizar_produto(titulo_smartphone_celular_xiaomi.lower(), 2500) == "Smartphone"

    titulo_smartphone_celular_xiaomi = "Xiaomi Poco X7 Pro 512GB / 12GB RAM, Preto, Camera 50 Mpx,NFC, 5G, Carregador 90W, Tela de 6,67', Dual SIM, Lançamento 2025"
    assert categorizar_produto(titulo_smartphone_celular_xiaomi.lower(), 3387) == "Smartphone"

    titulo_smartphone_infinix = "Smartphone Infinix Hot 11S 128GB Verde 4G 6GB RAM 6,78” Câm. Tripla + Selfie 8MP"
    assert categorizar_produto(titulo_smartphone_infinix.lower(), 999.10) == "Smartphone"

    titulo_smartphone_motorola_edge_pro = "Smartphone Motorola Edge 60 Pro 5G - Azul, 256GB, RAM 24GB (12GB RAM+12GB Ram Boost), Câmera 50MP, Selfie 50MP e Tela de 6,7"
    assert categorizar_produto(titulo_smartphone_motorola_edge_pro.lower(), 3499) == "Smartphone"

    titulo_smartphone_motorola_edge_pro = "Xiaomi Poco C75 128GB Global 6GB Preto 4G Tela com Baixa Luz Azul Selfie IA RAM até 16GB"
    assert categorizar_produto(titulo_smartphone_motorola_edge_pro.lower(), 1225) == "Smartphone"

    titulo_pelicula_vidro_unidade = "3UN Película 3D De Vidro Privacidade + 1UN Capinha Capa Anti Impacto para Iphone 14 - LXL"
    assert categorizar_produto(titulo_pelicula_vidro_unidade.lower(), 34.37) == "Proteção"

    titulo_capinha_moto_g = "G15 Capinha Moto G15 Case Reforçada Silicone Transparente Flexível Anti Choque Proteção De Câmera e Pelicula Motorola G15 Vidro 3D Cobertura Total - Phonecell"
    assert categorizar_produto(titulo_capinha_moto_g.lower(), 17.19) == "Proteção"

    titulo_kit_capa_transparente = "Kit 2 em 1 Capa Transparente + Película 3D De Vidro para Samsung Galaxy M52 5G - PREMIUM"
    assert categorizar_produto(titulo_kit_capa_transparente.lower(), 19.34) == "Proteção"

    titulo_kit_para_galaxy_capa_e_pelicula = "Kit para Galaxy A56 5G Capa Silicone TPU Transparente + Película 3D Frontal Vidro - LXL"
    assert categorizar_produto(titulo_kit_para_galaxy_capa_e_pelicula.lower(), 20.62) == "Proteção"

    titulo_cinto_de_corrida = "Cinto De Corrida Para Maratona Com Suporte Para Gel, Acessórios Para Triatlo E Fitness Ao Ar Livre - hengsong"
    assert categorizar_produto(titulo_cinto_de_corrida.lower(), 14.19) == "Acessório"

    titulo_fonte_mini_ugreen = "Fonte Mini 30W Ugreen Turbo Suporta 25W 20W 25693 ( ul )"
    assert categorizar_produto(titulo_fonte_mini_ugreen.lower(), 199.55) == "Carregador"

    titulo_fonte_notebook_acer = "Fonte Compatível com Notebook Acer Aspire A3152195KF AC02 AC02F - Generic"
    assert categorizar_produto(titulo_fonte_notebook_acer.lower(), 51.51) == "Carregador"

    titulo_grip_para_celular = "Grip para Celular LOVEHANDLE PRO Premium - Silicone Preto com Alça"
    assert categorizar_produto(titulo_grip_para_celular.lower(), 324) == "Acessório"

    titulo_alto_falante = "Alto-falante de parede FDM Universal One Pair (branco)"
    assert categorizar_produto(titulo_alto_falante.lower(), 508) == "Áudio"

    titulo_porta_chaves_yubikey = "Porta-chaves Yubikey Protector Flip Case Designz3D"
    assert categorizar_produto(titulo_porta_chaves_yubikey.lower(), 178.16) == "Outros"

    titulo_fonte_carregador_nintendo = "Fonte Carregador Para Nintendo Switch Bivolt - Knup"
    assert categorizar_produto(titulo_fonte_carregador_nintendo.lower(), 299) == "Carregador"

    titulo_fonte_carregador_nintendo_switch = "Nintendo Switch Ac Adapter Carregador Fonte Bivolt - Dobe"
    assert categorizar_produto(titulo_fonte_carregador_nintendo_switch.lower(), 106) == "Carregador"

    titulo_estacion_enfriamiento = "Estación de Enfriamiento y Carga para PS5/Slim/Pro + BRHE"
    assert categorizar_produto(titulo_estacion_enfriamiento.lower(), 342) == "Acessório"

    titulo_fonte_conversor = "Fonte (conversor) 12v 2a - Dvr - Genérica"
    assert categorizar_produto(titulo_fonte_conversor.lower(), 18.20) == "Carregador"

    titulo_celular_idosos_positivo = "Celular ideal Para Idosos Positivo P26 Rede 4G mp3 Dual Chip bateria 1000mAh"
    assert categorizar_produto(titulo_celular_idosos_positivo.lower(), 250) == "Celular Básico"

    titulo_celular_simples_nokia = "Celular Simples Nokia 110 Radio FM Bateria Boa Para Pais Idoso"
    assert categorizar_produto(titulo_celular_simples_nokia.lower(), 239) == "Celular Básico"
    
def test_detectar_cabo_sem_bundle_extra():
    titulo = "Cabo Carregador Usb Turbo Compativel Para Fone Xiaomi Red Airdots 2 Top - HREBOS"
    titulo_low = titulo.lower()
    preco = 27.90

    cat_base = categorizar_produto(titulo_low, preco)
    assert cat_base == "Cabo"

    resultado_final = montar_string_bundle(cat_base, titulo_low)

    assert set(resultado_final.split(" + ")) == {"Cabo"}
    
    partes = resultado_final.split(" + ")
    assert set(partes) == {"Cabo"}

def test_detectar_a26_e_smartband():
    titulo = "A26 5G (256GB) - Branco + Fit 3 - Grafite - Samsung"
    titulo_low = titulo.lower()
    preco = 2998

    cat_base = categorizar_produto(titulo_low, preco)
    assert cat_base == "Smartphone"

    # 2. Aplica a lógica de Bundle
    resultado_final = montar_string_bundle(cat_base, titulo_low)

    # 3. Verifica conjunto
    assert "Smartphone" in resultado_final
    assert "Smartband" in resultado_final
    
    partes = resultado_final.split(" + ")
    assert set(partes) == {"Smartphone", "Smartband"}

def test_detectar_correa_xiaomi_e_pelicula():
    titulo = "Correa Para Xiaomi Redmi Watch 4 - Silicone + Pelicula 3D - Tech King"
    titulo_low = titulo.lower()
    preco = 65

    cat_base = categorizar_produto(titulo_low, preco)
    assert cat_base == "Acessório"

    # 2. Aplica a lógica de Bundle
    resultado_final = montar_string_bundle(cat_base, titulo_low)

    # 3. Verifica conjunto
    assert "Acessório" in resultado_final
    assert "Proteção" in resultado_final
    
    partes = resultado_final.split(" + ")
    assert set(partes) == {"Acessório", "Proteção"}

def test_detectar_celular_rural_com_cabo():
    titulo = "Kit Celular Rural 4G Pro connect com wifi + Antena + Cabo 10m - PROELETRONIC"
    titulo_low = titulo.lower()
    preco = 735

    cat_base = categorizar_produto(titulo_low, preco)
    assert cat_base == "Celular Básico"

    # 2. Aplica a lógica de Bundle
    resultado_final = montar_string_bundle(cat_base, titulo_low)

    # 3. Verifica conjunto
    assert "Celular Básico" in resultado_final
    assert "Cabo" in resultado_final
    assert "Acessório" in resultado_final
    
    partes = resultado_final.split(" + ")
    assert set(partes) == {"Celular Básico", "Cabo", "Acessório"}

    

def test_detectar_bundle_relogio_pulseira():
    titulo = "Relógio digital Smart inteligente Hw12 41mm com pulseira metal extra - Smart Bracelet"
    titulo_low = titulo.lower()
    preco = 158.64

    # 1. Primeiro descobre o item principal
    cat_base = categorizar_produto(titulo_low, preco)
    assert cat_base == "Smartwatch"  # Isso deve ser verdade

    # 2. Aplica a lógica de Bundle
    resultado_final = montar_string_bundle(cat_base, titulo_low)

    # 3. Verifica conjunto
    assert "Smartwatch" in resultado_final
    assert "Acessório" in resultado_final
    
    partes = resultado_final.split(" + ")
    assert set(partes) == {"Smartwatch", "Acessório"}

def test_detectar_bundle_alca_e_carteira():
    titulo = "Alça de telefone RENUIS com bolsa com zíper e carteira tiracolo"
    titulo_low = titulo.lower()
    preco = 384.64

    # 1. Primeiro descobre o item principal
    cat_base = categorizar_produto(titulo_low, preco)
    assert cat_base == "Acessório"  # Isso deve ser verdade

    # 2. Aplica a lógica de Bundle
    resultado_final = montar_string_bundle(cat_base, titulo_low)

    # 3. Verifica conjunto
    assert "Acessório" in resultado_final
    
    partes = resultado_final.split(" + ")
    assert set(partes) == {"Acessório"}

def test_detectar_bundle_kit_fone_e_carregador():
    titulo = "KIT Fone de ouvido tipo c + Carregador 20W TURBO para Samsung M54,A54,S20 fe,20 ultra,S21 - HMT"
    titulo_low = titulo.lower()
    preco = 126

    # 1. Primeiro descobre o item principal
    cat_base = categorizar_produto(titulo_low, preco)
    assert cat_base == "Áudio"  # Isso deve ser verdade

    # 2. Aplica a lógica de Bundle
    resultado_final = montar_string_bundle(cat_base, titulo_low)

    # 3. Verifica conjunto
    assert "Áudio" in resultado_final
    assert "Carregador" in resultado_final
    
    partes = resultado_final.split(" + ")
    assert set(partes) == {"Áudio", "Carregador"}

    

def test_detectar_bundle_carregador_e_cabo():
    titulo = "Novo Carregador Portátil Indução Com 4 Cabos 10000 Mah - Envio Imediato - Power Bank"
    titulo_low = titulo.lower()
    preco = 129

    # 1. Primeiro descobre o item principal
    cat_base = categorizar_produto(titulo_low, preco)
    assert cat_base == "Carregador"  # Isso deve ser verdade

    # 2. Aplica a lógica de Bundle
    resultado_final = montar_string_bundle(cat_base, titulo_low)

    # 3. Verifica conjunto
    assert "Carregador" in resultado_final
    assert "Cabo" in resultado_final
    
    partes = resultado_final.split(" + ")
    assert set(partes) == {"Carregador", "Cabo"}

def test_detectar_bundle_garrafa_smartwatch_fone():
    titulo = "Kit Garrafa térmica 500ml inox sensor Led + Smartwatch Y8 + Fone Bluetooth - KIT ACADEMIA"
    titulo_low = titulo.lower()
    preco = 127

    # 1. Primeiro descobre o item principal
    cat_base = categorizar_produto(titulo_low, preco)
    assert cat_base == "Smartwatch"

    # 2. Aplica a lógica de Bundle (O que faltava no teste)
    resultado_final = montar_string_bundle(cat_base, titulo_low)

    # 3. Verifica conjunto
    assert "Smartwatch" in resultado_final
    assert "Acessório" in resultado_final
    assert "Áudio" in resultado_final

    partes = resultado_final.split(" + ")
    assert set(partes) == {"Smartwatch", "Acessório", "Áudio"}

def test_detectar_bundle_powerbank_miisso():
    titulo = "Power Bank miisso 6000mAh x 2 com cabos embutidos para telefones"
    titulo_low = titulo.lower()
    preco = 575

    # 1. Primeiro descobre o item principal
    cat_base = categorizar_produto(titulo_low, preco)
    assert cat_base == "Carregador"

    # 2. Aplica a lógica de Bundle (O que faltava no teste)
    resultado_final = montar_string_bundle(cat_base, titulo_low)

    # 3. Verifica conjunto
    assert "Carregador" in resultado_final
    assert "Cabo" in resultado_final

    partes = resultado_final.split(" + ")
    assert set(partes) == {"Carregador", "Cabo"}

def test_detectar_bundle_relogio_sport_e_pulseiras():
    titulo = "Relógio Digital Sport Led Ultra max com pulseira 3 padrão - Blulory"
    titulo_low = titulo.lower()
    preco = 4575.50

    # 1. Primeiro descobre o item principal
    cat_base = categorizar_produto(titulo_low, preco)
    assert cat_base == "Smartband"

    # 2. Aplica a lógica de Bundle (O que faltava no teste)
    resultado_final = montar_string_bundle(cat_base, titulo_low)

    # 3. Verifica conjunto
    assert "Smartband" in resultado_final
    assert "Acessório" in resultado_final

    partes = resultado_final.split(" + ")
    assert set(partes) == {"Smartband", "Acessório"}
    