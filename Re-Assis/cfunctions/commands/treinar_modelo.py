# treinar_modelo.py
from intent_trainer import load_or_train_model
from function_reg import Registry

@Registry.command("treinar_modelo", aliases=["treinar", "retrain"])
def treinar_modelo(_texto=None):
    print("Konto> Iniciando retreinamento do modelo...")
    pipeline, classes = load_or_train_model(force_train=True)
    if pipeline:
        print(f"Konto> Modelo treinado com {len(classes)} classes.") # type: ignore
    else:
        print("Konto> Falha ao treinar o modelo.")
    return pipeline, classes