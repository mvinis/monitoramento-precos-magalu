import logging
from transformers import pipeline

# Configuração básica de log para aparecer no console (Stream)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
class ProductClassifier:
    def __init__(self):
        logging.info("Iniciando carregamento do modelo mDeBERTa-v3 🤖...")
        self.classifier = pipeline("zero-shot-classification", 
                                    model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli")
        
        self.categorias_alvo = [
            "Smartphone e Celular", 
            "Fone de Ouvido e Áudio", 
            "Carregador e Cabo", 
            "Capa e Película",
            "Smartwatch e Wearable",
            "Tablet",
            "Chip",
            "Suporte",
            "Proteção",
            "Bluetooth",
            "Bateria",
            "Console"
        ]
        logging.info("Modelo carregado com sucesso.")

    def classificar(self, titulo):
        logging.info(f"--- Nova Classificação iniciada (Threshold: 0.95) ---")
        logging.info(f"Título: {titulo}")

        try:
            resultado = self.classifier(
                titulo, 
                self.categorias_alvo, 
                hypothesis_template="Este produto é um {}",
                multi_label=True 
            )

            logging.info("Scores calculados pela IA:")
            for label, score in zip(resultado['labels'], resultado['scores']):
                status = "✅" if score > 0.95 else "❌"
                logging.info(f"  {status} {label}: {score:.4f}")

            # Pegamos todos que passaram de 95%
            labels_confiáveis = [
                resultado['labels'][i] 
                for i, score in enumerate(resultado['scores']) if score > 0.95
            ]
            
            # --- NOVO BLOCO: LÓGICA DE DOMINÂNCIA ---
            if len(labels_confiáveis) > 1:
                melhor_score = resultado['scores'][0]
                segundo_melhor_score = resultado['scores'][1]
                
                # Se o primeiro lugar é esmagador (ex: 0.9997) e a diferença para o 
                # segundo é maior que 0.01 (1%), ignoramos o segundo para evitar o falso combo.
                if melhor_score > 0.999 and (melhor_score - segundo_melhor_score) > 0.01:
                    vencedor_absoluto = resultado['labels'][0]
                    logging.info(f"Dominância detectada! Mantendo apenas: {vencedor_absoluto}")
                    return vencedor_absoluto
                
                # Se não houver dominância clara, mantém o combo
                res = "Combo: " + " & ".join(labels_confiáveis)
                logging.info(f"Resultado Final: [BUNDLE ALTA CONFIANÇA] -> {res}")
                return res
            # ----------------------------------------
            
            if not labels_confiáveis:
                top_label = resultado['labels'][0]
                top_score = resultado['scores'][0]
                if top_score > 0.70:
                    logging.info(f"Aviso: Usando melhor opção disponível: {top_label}")
                    return top_label
                else:
                    return "Outros"

            final_label = labels_confiáveis[0]
            logging.info(f"Resultado Final: {final_label}")
            return final_label

        except Exception as e:
            logging.error(f"Erro crítico na classificação da IA: {e}")
            return "Outros"