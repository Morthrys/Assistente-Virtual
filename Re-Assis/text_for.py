# text_for.py
import unicodedata
import spacy
from functools import lru_cache
from typing import Optional, List
from nltk.corpus import wordnet as wn
import re

nlp = spacy.load("pt_core_news_md" , disable=["ner", "parser"])

@lru_cache(maxsize=512)
def Dictionary(base: str, extras: Optional[List[str]] = None) -> List[str]:
    termos = [base]
    if extras:
        termos.extend(extras)
    try:
        synsets = wn.synsets(base, lang="por")
        for syn in synsets:
            for lemma in syn.lemmas(lang="por"):  # type: ignore
                if lemma.name() not in termos:
                    termos.append(lemma.name())
    except Exception as e:
        print(f"Aviso: não foi possível carregar sinônimos do WordNet para '{base}'. Erro: {e}")
    return list(set(termos))  # remove duplicados

@lru_cache(maxsize=512)
def normalize_lema_text(text: str) -> str:
    """Normaliza texto: lematiza, remove acentos, padroniza minúsculas e espaços."""
    doc = nlp(text)
    text_lema = " ".join(token.lemma_ for token in doc if not token.is_punct)
    nfkd = unicodedata.normalize("NFKD", text_lema)
    text_no_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    # normaliza espaços e minúsculas no final
    return re.sub(r'\s+', ' ', text_no_accents).strip().lower()

@lru_cache(maxsize=512)
def normalize_text(text: str) -> str:
    """Normaliza texto: removendo acentos, caracteres especiais e espaços extras."""
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"[^a-z0-9\s']", " ", text)
    return re.sub(r"\s+", " ", text).strip()