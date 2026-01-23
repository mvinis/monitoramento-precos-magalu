%md

# 🛒 Monitoramento de Preços E-commerce - Magalu

Este projeto implementa um pipeline de engenharia de dados end-to-end voltado à coleta e análise de produtos do e-commerce da Magazine Luiza. A solução realiza web scraping automatizado, aplica classificação de categorias por meio de modelos de Inteligência Artificial executados localmente e organiza os dados em um schema analítico padronizado (Schema VIP), garantindo consistência, rastreabilidade e prontidão para consumo em plataformas de Big Data como o Databricks.

## 📐 Arquitetura da Solução

O robô utiliza uma estrutura de **Buffer & Parsing**, garantindo que o dado seja validado e estruturado no "Schema VIP" antes mesmo de ser salvo no disco (Camada Bronze).

### Diagrama Flowchart

```mermaid
graph TD
    %% Estilos
    classDef start fill:#a5d6a7,stroke:#333,color:#000,font-weight:bold;
    classDef process fill:#90caf9,stroke:#333,color:#000,stroke-width:1px;
    classDef decision fill:#fff4dd,stroke:#d4a017,color:#000,stroke-width:2px;
    classDef error fill:#ffcdd2,stroke:#f66,color:#000,stroke-width:1px;
    classDef storage fill:#eeeeee,stroke:#333,color:#000,stroke-width:2px;
    classDef final fill:#fbb,stroke:#333,color:#000,font-weight:bold;

    Start((Início)):::start --> Config[Definir URL Inicial e<br/>Inicializar Buffer]:::process

    Config --> AccessPage[Acessar Página Atual]:::process
    AccessPage --> SuccessPage{Página<br/>Carregou?}:::decision

    SuccessPage -- Não --> LogPageErr[Log: Falha na Página]:::error
    LogPageErr --> HasNext

    SuccessPage -- Sim --> FindCards[Identificar Lista de Cards]:::process

    FindCards --> CheckCards{Existem Cards<br/>pendentes?}:::decision

    CheckCards -- Sim --> PickNext[Selecionar Próximo Card da Lista]:::process
    PickNext --> Extract[Aplicar Regras de Negócio e Schema VIP]:::process

    Extract --> ValidData{Dados<br/>Válidos?}:::decision

    ValidData -- Sim --> AddBuffer[Adicionar ao Buffer]:::process
    ValidData -- Não --> LogProdErr[Log: Pular Produto]:::error

    LogProdErr --> CheckCards
    AddBuffer --> CheckCards

    CheckCards -- Não --> HasNext{Existe Próxima<br/>Página?}:::decision

    HasNext -- Sim --> NextURL[Preparar URL da Próxima Página]:::process
    NextURL --> AccessPage

    HasNext -- Não --> Aggregation[Consolidar Buffer e Metadados]:::process
    Aggregation --> SaveJSON[Gerar Arquivo JSON Bronze]:::storage
    SaveJSON --> End((Fim do Processo)):::final
```

### Diagrama de Sequência

```mermaid
sequenceDiagram
    participant ORQ as Orquestrador (Main)
    participant DRV as WebDriver (Browser)
    participant SCR as Motor de Scraping
    participant TRF as Transformador de Dados
    participant STO as Zona de Destino (Storage)
    autonumber

    ORQ->>DRV: Solicita URL Alvo
    DRV->>DRV: Aguarda Conteúdo Dinâmico (JS)
    DRV-->>ORQ: Conteúdo Bruto (HTML/DOM)
    ORQ->>SCR: Analisar (Parse) Conteúdo Bruto
    SCR->>SCR: Identifica Componentes do Produto (Nodes)
    loop Para cada Objeto de Produto
        SCR->>TRF: Envia Strings Brutas (Preço, Nome, ID)
        TRF->>TRF: Aplica Limpeza e Regras de Negócio
        TRF->>TRF: Gera Hash Único (Fingerprint)
        TRF-->>SCR: Objeto Estruturado/Validado
    end

    SCR-->>ORQ: Dataset Normalizado
    ORQ->>STO: Persistir Dados (JSON)
```

### Diagrama de Classes

```mermaid
classDiagram
    class MagaluScraper {
        +list buffer_produtos
        +coletar_produtos()
    }

    class ProductClassifier {
        <<Service - IA Local>>
        +model mDeBERTa
        +classificar(titulo)
    }

    class ProductParsers {
        +montar_objeto_produto(dados_brutos, contexto, classificador_ai=None)
        +montar_string_bundle(base, titulo_low)
        +detectar_bundle(titulo)
    }

    class DataCleaner {
        +limpar_valor_simples_para_float(texto)
        +normalizar_texto(texto)
        +calcular_preco_total_parcelado(texto_parcela)
    }

    class DataQualityTestsParsers {
        <<UnitTests>>
        +test_limpar_valor_real_brasileiro()
        +test_normalizar_texto_com_unicode()
        +test_limpar_valor_vazio()
        +test_falsos_positivos_memoria_ram()
        +test_falsos_positivos_tecnicos()
        +test_bundles_reais()
    }

    class AILogicTests {
        <<UnitTests>>
        +test_gamepad_nao_deve_ser_smartphone(ia, contexto_padrao)
        +test_samsung_b310e_deve_ser_celular_basico(ia, contexto_padrao)
        +test_insumo_reparo_nao_deve_ser_celular(ia, contexto_padrao)
        +test_suporte_garra_nao_deve_ser_carregador(ia, contexto_padrao)
    }

    %% Relações com legendas (Estereótipos)
    MagaluScraper --> ProductParsers : 1. Envia Cards Brutos
    ProductParsers --> DataCleaner : 2. Solicita Saneamento
    ProductParsers --> ProductClassifier : 3. Fallback Classifica via IA

    DataQualityTestsParsers ..> DataCleaner : Valida Tipagem
    DataQualityTestsParsers ..> ProductParsers : Valida Regex
    AILogicTests ..> ProductClassifier : Injeta Fixture
    AILogicTests ..> ProductParsers : Valida Fluxo Híbrido
```

## 🕸️ Funcionalidades

- **Web Scraping:** Utiliza Selenium com técnicas de evasão de bot (User-Agents dinâmicos, modo incognito e exclusão de flags de automação).
- **Deep Data Extraction:** Captura dados sobre os produtos vendidos na plataforma e identifica se o produto é de venda direta ou Marketplace (ex: Carrefour, Samsung) através da análise de metadados da URL.
- **Classificação com IA Local:** Utiliza o modelo `mDeBERTa-v3` básico (via Hugging Face Transformers) para classificar produtos em categorias sem custo de API e com alta precisão (Zero-Shot Classification).
- **Detecção de Bundles:** Lógica inteligente para identificar combos de produtos (chamados "bundles" na mesma proposta de venda do produto - ex: Relógio + Fone), tratando falsos positivos técnicos.
- **Metadata de Auditoria:** Cada registro contém informações de versão do pipeline, ambiente (dev/prod) e timestamp, garantindo linhagem de dados.
- **Schema VIP Profissional:** Estrutura de JSON aninhada que separa dados de produto, precificação detalhada (PIX, Crédito, Parcelamento) e fontes.

## 🛠️ Tecnologias Utilizadas

- **Linguagem:** Python 3.10+
- **Automação:** Selenium & BeautifulSoup4
- **IA/ML:** Hugging Face Transformers & PyTorch
- **Configuração:** Python-dotenv (Variáveis de Ambiente)
- **Data Lake: (Em progresso)** Integração com Databricks (Medallion Architecture).

## 📁 Estrutura do Projeto

```text
├── data/raw/             # Arquivos JSON brutos coletados
├── src/
│   ├── models/
│   │   └── classifier.py # Lógica de IA (NLP) para categorias
│   ├── parsers.py        # Tratamento de dados e Schema VIP
│   ├── scraper.py        # Motor de busca e navegação Selenium
│   └── utils.py          # Ferramentas auxiliares (logs, timestamps)
├── tests/                # Suíte de testes automatizados
│   ├── test_ai_logic.py  # Validação de inferência e categorias feita pela IA
│   └── test_parsers.py   # Validação de saneamento e regex
├── .env                  # Variáveis de ambiente (não versionado)
├── .gitignore            # Proteção de arquivos sensíveis
├── main.py               # Ponto de entrada da aplicação
└── requirements.txt      # Dependências do projeto
```

## ⚙️ Instruções de Configuração

**1. Pré-requisitos**

- Python instalado
- Google Chrome instalado

**2. Pré-requisitos**

Clone o repositório e instale as dependências:

- `git clone [https://github.com/mvinis/monitoramento-precos-magalu.git](https://github.com/mvinis/monitoramento-precos-magalu.git)`

- `cd monitoramento-precos-magalu`

- `python -m venv venv`

- `source venv/bin/activate`
- No Windows: `.\venv\Scripts\activate`

- `pip install -r requirements.txt`

**3. Variáveis de Ambiente**

Crie um arquivo `.env` na raiz do projeto:

**Snippet de código**

`PIPELINE_VERSION=v1.2`

`ENVIRONMENT=prod`

`COLLECTION_TYPE=web_scraping`

**4. Execução**

Para iniciar a coleta dos dados dos produtos, basta rodar:

`python main.py`

> Nota: Na primeira execução, o script realizará o download do modelo de linguagem (mDeBERTa) automaticamente. Certifique-se de ter espaço em disco (~500MB) e conexão com a internet. O mDeBERTa é um modelo de Inteligência Artificial treinado para entender o significado profundo de textos em diversos idiomas, inclusive o português. Ele é necessário para analisar os nomes dos produtos e decidir, de forma inteligente e sem regras manuais (fixadas no código), em qual categoria cada item se encaixa (ex: Smartphones, Acessórios ou Áudio).

## 🧪 Qualidade e Testes

Para garantir a integridade dos dados e a resiliência das transformações (especialmente no tratamento de valores monetários brasileiros e caracteres Unicode), o projeto possui uma suíte de testes unitários automatizados.

**1. O que é testado?**

- **Saneamento de Moeda**: Validação da conversão de strings (ex: R$ 1.299,50) para o tipo float (1299.5).

- **Normalização Unicode**: Verificação da remoção de caracteres invisíveis (\xa0) comuns em raspagens web.

- **Resiliência de Parsing**: Garantia de que entradas nulas ou inválidas não quebrem o pipeline (retorno padrão 0.0).

- **Blindagem de Bundles**: Validação de que "8GB+8GB RAM" não é detectado como combo.

- **Priorização de Hardware**: Garante que "Relógio + 7 Pulseiras" mantenha a categoria 'Smartwatch'.

- **Dupla Verificação do resultado da IA**: Por meio do `test_ai_logic.py`, é feito alguns testes se os produtos que eventualmente foram classificados pela IA, estão coerentes de fato.

**2. Como rodar os testes**

Certifique-se de que o ambiente virtual está ativo e execute:

`python -m pytest -v`

> Esse comando é necessário, pois o `pytest` executa os testes a partir da pasta `tests` e, por padrão, não reconhece a pasta `src` no `PYTHONPATH`, impedindo a importação das funções. Por isso, é necessário utilizar `python -m` no início do comando. E `-v`é para ver as funções exatas de cada arquivo.
