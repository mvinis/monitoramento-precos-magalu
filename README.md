# 🛒 Monitoramento de Preços E-commerce - Magalu

Este projeto implementa um pipeline de engenharia de dados end-to-end voltado à coleta e análise de produtos do e-commerce da Magazine Luiza. A solução realiza web scraping automatizado, aplica classificação de categorias por meio de modelos de Inteligência Artificial executados localmente e organiza os dados em um schema analítico padronizado (Schema VIP), garantindo consistência, rastreabilidade e prontidão para consumo em plataformas de Big Data como o Databricks.

## 🚀 Funcionalidades

- **Web Scraping Avançado:** Utiliza Selenium com técnicas de evasão de bot (User-Agents dinâmicos, modo incognito e exclusão de flags de automação).
- **Deep Data Extraction:** Identifica se o produto é de venda direta ou Marketplace (ex: Carrefour, Samsung) através da análise de metadados da URL.
- **Classificação com IA Local:** Utiliza o modelo `mDeBERTa-v3` (via Hugging Face Transformers) para classificar produtos em categorias sem custo de API e com alta precisão (Zero-Shot Classification).
- **Detecção de Bundles:** Lógica inteligente para identificar combos de produtos (bundles - ex: Relógio + Fone), tratando falsos positivos técnicos.
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
│   ├── classifier.py     # Lógica de IA para classificação de categorias
│   ├── parsers.py        # Tratamento de dados e montagem do Schema VIP
│   ├── scraper.py        # Motor de busca e navegação Selenium
│   └── utils.py          # Ferramentas auxiliares (logs, timestamps)
├── .env                  # Variáveis de ambiente (não versionado)
├── .gitignore            # Proteção de arquivos sensíveis
├── main.py               # Ponto de entrada da aplicação
└── requirements.txt      # Dependências do projeto
```

⚙️ Instruções de Configuração

1. Pré-requisitos

Python instalado.
Google Chrome instalado.

2. Instalação
   Clone o repositório e instale as dependências:

Bash

git clone [https://github.com/mvinis/monitoramento-precos-magalu.git](https://github.com/mvinis/monitoramento-precos-magalu.git)
cd monitoramento-precos-magalu
python -m venv venv
source venv/bin/activate # No Windows: .\venv\Scripts\activate
pip install -r requirements.txt 3. Variáveis de Ambiente
Crie um arquivo .env na raiz do projeto:

Snippet de código

PIPELINE_VERSION=v1.2
ENVIRONMENT=prod
COLLECTION_TYPE=web_scraping

4. Execução
   Para iniciar a coleta, basta rodar:

Bash

python main.py
