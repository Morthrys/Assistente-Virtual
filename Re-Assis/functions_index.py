# functions_index.py
from function_reg import Registry
from text_for import normalize_text
from intent_trainer import add_new_example
from entities import Entities
from context_manager import CONTEXT
import cfunctions.commands

entities = Entities()

def detectar_comando(texto: str):
    return entities.detectar_comando(texto)

def processar_entrada(texto: str, model, threshold: float = 0.6):
    texto_norm = normalize_text(texto)

    if CONTEXT.current_context:
        if CONTEXT.handle_input(texto_norm):
            return

    comando, text_comando, argumento_norm = detectar_comando(texto_norm)
    
    if comando:
        if isinstance(comando, (set, list, tuple)):
            comando = next(iter(comando))

        comando = normalize_text(str(comando))

        idx = texto.lower().find(text_comando.lower())
        if idx != -1:
            argumento_original = texto[idx + len(text_comando):].strip()
        else:
            argumento_original = argumento_norm

        try:
            return Registry.executer(comando, argumento_original, texto)
        except Exception as e:
            print(f"Konto> Erro ao executar comando '{comando}': {e}")
        return

    # Obtém probabilidades se disponível
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba([texto_norm])[0]
        classes = model.classes_
        max_idx = proba.argmax()
        pred = classes[max_idx]
        conf = proba[max_idx]
    else:
        pred = model.predict([texto_norm])[0]
        conf = 1.0

    def confian(resposta: str):
        intent = resposta.strip().lower()
        if not intent:
            print("Konto> Entrada ignorada.")
            CONTEXT.clear()
            return True

        if conf < threshold:
            if intent in Registry.list_commands():
                add_new_example(texto, intent)
                print("Konto> Exemplo adicionado ao dataset.")
            else:
                print("Konto> Entrada ignorada.")
        else:
            print("Konto> Sem comando explícito identificado.")

        CONTEXT.clear()
        return True

    if conf < threshold:
        print(f"Konto> Confiança baixa ({conf:.2f}) para a intenção '{pred}'. Qual seria a intenção correta? ")
        CONTEXT.set("confiança_baixa", confian) # type: ignore
        return

    return Registry.executer(pred, "", texto)
