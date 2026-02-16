import logging
from transformers import pipeline

class ProductClassifier:
    def __init__(self):
        logging.info("Iniciando carregamento do modelo mDeBERTa-v3 🤖...")
        # O pipeline zero-shot-classification utiliza NLI (Natural Language Inference)
        self.classifier = pipeline("zero-shot-classification", 
                                    model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli")
        
        self.categorias_alvo = [
            "Smartphone", "Celular Básico", "Smartwatch", "Smartband",
            "Fone de Ouvido", "Carregador", "Capa e Película", "Console",
            "Tablet", "Chip", "Acessórios"
        ]
        logging.info("Modelo carregado com sucesso.")

    def classificar(self, texto_bruto, preco_produto, modo_profundo=False):
        tipo = "PROFUNDA (Título + Descrição)" if modo_profundo else "SIMPLES (Título)"
        logging.info(f"🧠 IA pensando... Modo: {tipo}")
        
        # 1. FUNIL DE CATEGORIAS (Essencial)
        categorias_analise = self.categorias_alvo
        if modo_profundo:
            categorias_analise = ["Smartwatch", "Smartband", "Acessórios"]

        # 2. PROMPT LIMPO E DIRETO
        if modo_profundo:
            texto_para_ia = f"""
            CLASSIFICAÇÃO TÉCNICA DE DISPOSITIVO VESTÍVEL:
            - SMARTWATCH: Tela inteira touch, faz ligações, tem NFC, colocar músicas, baixar aplicativos, carregamento por indução, deve possui gps, Series 9, W29, W59.
            - SMARTBAND: Toque em apenas 1 ponto, carregamento USB na haste, app FitPro, D20, Y68.
            
            PRODUTO: {texto_bruto}
            """
        else:
            texto_para_ia = texto_bruto
        
        template = "Este dispositivo é um {}"

        try:
            resultado = self.classifier(
                texto_para_ia[:1200],
                categorias_analise,
                hypothesis_template=template,
                multi_label=True 
            )

            vencedor = resultado['labels'][0]
            melhor_score = resultado['scores'][0]

            modelos_band = ["d20", "y68", "m3", "m4", "fitpro", "hryfine"]
            texto_lower = texto_bruto.lower()

            # 1️⃣ Regra de domínio forte - Valor muito baixo para ser um smartwatch, mesmo de entrada
            if any(m in texto_lower for m in modelos_band) and preco_produto <= 100:
                logging.warning("📉 Modelo típico de smartband detectado. Forçando Smartband.")
                return "Smartband"
            
            # --- 3. REATIVAÇÃO DA LÓGICA DE DESEMPATE (OBRIGATÓRIO) ---
            if len(resultado['labels']) > 1:
                segundo_vencedor = resultado['labels'][1]
                segundo_score = resultado['scores'][1]
                
                # Se a disputa for entre Watch e Band e a diferença for menor que 15% e o preço estar ainda muito abaixo de mercado
                if {vencedor, segundo_vencedor} == {"Smartwatch", "Smartband"}:
                    diferenca = abs(melhor_score - segundo_score)
                    if diferenca < 0.15 and preco_produto <= 100:
                        logging.warning(f"⚖️ Empate Técnico (dif: {diferenca:.4f}). Aplicando Veredito Técnico: Smartband.")
                        return "Smartband"

            # 4. DECISÃO FINAL
            if melhor_score > 0.40: # Threshold menor pois o funil é restrito
                logging.info(f"✅ Veredito: {vencedor} ({melhor_score:.4f})")
                return vencedor
            
            return "Outros"

        except Exception as e:
            logging.error(f"❌ Erro na IA: {e}")
            return "Outros"