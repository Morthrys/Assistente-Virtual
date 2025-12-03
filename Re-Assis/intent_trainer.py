# intent_trainer
import json
import joblib
import os
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from text_for import normalize_text

MODEL_FILE = "intent_classifier.joblib"
NEW_EXAMPLES_FILE = "new_examples.json"
AUTO_TRAIN_THRESHOLD = 1

def load_initial_data():
    return {
        "ajuda": [
            "o que posso fazer?", "ajuda", "comandos",
        ],
        "abrir_app": [
            "abrir word", "executar excel", "rodar steam",
            "iniciar outlook", "abra o navegador", "abrir aplicativo word", "abrir aplicativo steam", "rodar aplicativo excel"
        ],
        "pesquisar": [
            "pesquisar clima rio de janeiro", "buscar sinônimos de feliz",
            "procurar receita de bolo", "buscar site steam", "acessar site instagram", "procurar site do github"
        ],
        "treinar_modelo": [
            "treinar", "treinar novamente", "treine o modelo", "aprender novamente", "treinar assistente"
        ],
        "clima": [
            "clima Rj", "qual o clima de hoje", "qual a previsão da chuva de amanhã", "verificar previsão de chuva São Paulo"
        ],
        "data_hora":[
            "que horas são?", "qual a data atual", "amanhã é que dia", "que dia da semana cai 25 de dezembro"
        ],
        "fechar": [
            "fechar aplicativo", "fechar word", "fechar excel", "encerrar steam", "sair do navegador", "encerre o navegador"
        ],
        "alarme": [
            "definir alarme para as 10hrs", "definir alarme para as 10 horas", "cancelar alarme das 10hrs", 
            "cancelar alarme das 10 horas", "listar alarmes", "criar despertador para as 5 da manhã", "alarme para daqui a 2 minutos"
        ],
        "youtube": [
            "tocar set if off - why worry", "reproduzir link park numb", "play shooter lagrimas de odio", 
            "parar video em reprodução", "cancelar reprodução"
        ],
        "abrir_arquivo": [
            "abrir arquivo main_call.py", "abra arquivo data_hora.py", "executar arquivo cache_sys.py"
        ],
        "editar_entrada": [
            "editar entrada apps firefox", "excluir entrada apps firefox", "modificar entrada sites youtube",
            "mudar entrada sites steam", "mexer entrada sites", "alterar entrada apps chrome"
        ],
    }

def load_new_examples(path=NEW_EXAMPLES_FILE):
    if not os.path.exists(path) or os.stat(path).st_size == 0:
        with open(path, "w", encoding="utf-8") as f:
            f.write('{"X": [], "y": []}')
        return [], []
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("X", []), data.get("y", [])
    except (FileNotFoundError, json.JSONDecodeError):
        with open(path, "w", encoding="utf-8") as f:
            f.write('{"X": [], "y": []}')
        return [], []

def add_new_example(frase, intent, path=NEW_EXAMPLES_FILE):
    X, y = load_new_examples(path)
    X.append(frase)
    y.append(intent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"X": X, "y": y}, f, ensure_ascii=False)
    if len(X) % AUTO_TRAIN_THRESHOLD == 0:
        print(f"Konto> {len(X)} exemplos acumulados. Retreinando o modelo...")
        load_or_train_model(force_train=True)

def load_or_train_model(force_train=False):
    model_file = MODEL_FILE
    
    if not force_train and os.path.exists(model_file):
        try:
            pipeline, classes = joblib.load(model_file)
            print("Konto> Modelo carregado com sucesso!")
            return pipeline, classes
        except Exception as e:
            print(f"Konto> Erro ao carregar o modelo: {e}. O arquivo pode estar corrompido.")
            print("Konto> Tentando treinar um novo modelo...")

    if not force_train:
        print("Konto> Arquivo de modelo não encontrado. Treinando novo modelo...")
    
    raw_data = load_initial_data()
    X_init, y_init = [], []
    for intent, phrases in raw_data.items():
        X_init.extend(phrases)
        y_init.extend([intent] * len(phrases))
        
    X_new, y_new = load_new_examples()
    X_all, y_all = X_init + X_new, y_init + y_new

    if not X_all:
        print("Konto> Nenhum dado de treinamento encontrado. O modelo não pode ser treinado.")
        return None, None

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(preprocessor=normalize_text)),
        ("clf", SGDClassifier(
            loss="log_loss",
            max_iter=1000,
            tol=1e-3,
        )),
    ])

    pipeline.fit(X_all, y_all)
    classes = sorted(set(y_all))
    joblib.dump((pipeline, classes), model_file)
    print(f"Konto> Novo modelo treinado com {len(X_all)} exemplos e {len(classes)} classes.")
    return pipeline, classes

if __name__ == "__main__":
    load_or_train_model()