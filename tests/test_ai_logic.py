import pytest
from src.parsers import montar_objeto_produto
from src.models.classifier import ProductClassifier

# Criamos uma "Fixture" para carregar a IA apenas uma vez para todos os testes
# O Pytest carrega a IA uma única vez quando o arquivo de teste começa, guarda ela na memória, e "empresta" o mesmo objeto para todos os testes daquele arquivo.
@pytest.fixture(scope="module")
def ia():
    return ProductClassifier()

@pytest.fixture
def contexto_padrao():
    return {
        "timestamp": "2026-01-19",
        "versao_pipeline": "1.0",
        "ambiente": "dev",
        "tipo_coleta": "teste", 
        "loja": "Teste", 
        "canal_venda": "PLATAFORMA", 
        "url_produto": "http://teste.com", 
        "pagina": 1
    }

def test_gamepad_nao_deve_ser_smartphone(ia, contexto_padrao):

    dado_mocado = {
        "id_produto": "GME_01",
        "titulo": "Controle Gamepad Joystick Celular Bluetooth Android Jogos Pc - Altomex / X3",
        "preco_atual": 85.00
    }

    resultado = montar_objeto_produto(dado_mocado, contexto_padrao, classificador_ai=ia)
    categoria = resultado['produto']['categoria']

    # O ASSERT: Eu espero que a categoria NÃO contenha "Smartphone"
    # se classificar como Smartphone, o teste FALHA aqui.
    assert "Smartphone" not in categoria, f"Erro! Gamepad foi classificado como {categoria}"

    # se foi classificado como "Console", o teste foi um sucesso
    assert "Console" in categoria, f"Sucesso! Gamepad foi classificado como {categoria}"

def test_samsung_b310e_deve_ser_celular_basico(ia):
    contexto = {"timestamp": "2026-01-19", "versao_pipeline": "1.0", "ambiente": "dev", "tipo_coleta": "teste", "loja": "Teste", "canal_venda": "PLATAFORMA", "url_produto": "http://teste.com", "pagina": 1}
    
    dado_mocado = {
        "id_produto": "CEL_01",
        "titulo": "Samsung SM-B310E 2G GSM Dual Chip aceita Memory Card",
        "preco_atual": 150.00
    }

    resultado = montar_objeto_produto(dado_mocado, contexto, classificador_ai=ia)
    
    # Valida se a inteligência (IA ou IFs) pegou que é um celular básico
    assert "Celular Básico" in resultado['produto']['categoria']

def test_insumo_reparo_nao_deve_ser_celular(ia):
    contexto = {"timestamp": "2026-01-21", "versao_pipeline": "1.0", "ambiente": "dev", "tipo_coleta": "teste", "loja": "Teste", "canal_venda": "PLATAFORMA", "url_produto": "http://teste.com", "pagina": 1}
    
    dado_mocado = {
        "id_produto": "123000",
        "titulo": "Kit 2 Cola Adesiva Branca e Preta P/ Display Celulares 15ml - OEM",
        "preco_atual": 25.00
    }

    resultado = montar_objeto_produto(dado_mocado, contexto, classificador_ai=ia)
    categoria = resultado['produto']['categoria']

    # O ASSERT: Esperamos que NÃO seja Celular Básico e nem Smartphone
    assert categoria == "Outros", f"Erro! Insumo foi classificado erroneamente como {categoria}"

def test_suporte_garra_nao_deve_ser_carregador(ia):
    contexto = {"timestamp": "2026-01-21", "versao_pipeline": "1.0", "ambiente": "dev", "tipo_coleta": "teste", "loja": "Teste", "canal_venda": "PLATAFORMA", "url_produto": "http://teste.com", "pagina": 1}
    
    dado_mocado = {
        "id_produto": "012345",
        "titulo": "Suporte Garra Celular P/ Motos Universal Com Carregador Usb - +BR",
        "preco_atual": 10.00
    }

    resultado = montar_objeto_produto(dado_mocado, contexto, classificador_ai=ia)
    categoria = resultado['produto']['categoria']

    assert categoria == "Suporte", f"Erro! Insumo foi classificado erroneamente como {categoria}"
