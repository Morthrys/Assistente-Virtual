import spacy
import re
from functools import lru_cache
from collections import defaultdict
from text_for import normalize_text, Dictionary, normalize_lema_text
from function_reg import Registry

nlp = spacy.load("pt_core_news_md", disable=["ner", "parser"])

class Entities:

    def __init__(self):
        self.dictionary = Dictionary
        self.memory = {}

    @lru_cache(maxsize=1024)
    def get_synonyms(self, word: str) -> set[str]:
        """
        Retorna o conjunto de sinônimos
        """
        word_norm = normalize_text(word)
        syns = self.dictionary(word_norm)
        return {word_norm, *map(normalize_text, syns)}

    def extract_entities(self, text: str, contexto: str = "default"):
        """
        Extrai entidades detectadas pelo Spacy e organiza por tipo.
        Retornando um dicionário de tipos em lista de valores.
        """
        entidades = []
        doc = nlp(text)

        for i, token in enumerate(doc):
            # Ignora a pontuação e espaços
            if token.is_punct or token.is_space:
                continue
            # Ignora artigos e etc isolados
            if token.pos_ in {"DET", "ADP", "CCONJ", "SCONJ", "PRON"}:
                # Mantém conectores se dentro de um nome composto
                if 0 < i < len(doc) - 1:
                    prev_tok = doc[i - 1]
                    next_tok = doc[i + 1]
                    if prev_tok.pos_ not in {"DET", "ADP", "CCONJ", "SCONJ", "PRON"} and next_tok.pos_ not in {"DET", "ADP", "CCONJ", "SCONJ", "PRON"}:
                        entidades.append(token.text)
                continue
            entidades.append(token.text)

        # Atualiza memória contextual
        self.last_entities = entidades
        self.memory[contexto] = entidades
        return entidades
    
    def get_last_entities(self, context: str = "default"):
        """Retorna as últimas entidades salvas para o contexto atual"""
        return self.memory.get(context, [])
    
    def resolve_missing_entities(self, text: str, context: str = "default"):
        """
        Usa o histórico para completar comandos: 'abrir novamente' -> reutiliza a última entidade detectada
        """
        entities = self.extract_entities(text, context)
        if not entities:
            return self.get_last_entities(context)
        return entities
    
    @lru_cache(maxsize=1024)
    def _lemmas_from_text(text: str) -> tuple[str, ...]: # type: ignore
        """
        Helper: retorna tupla de lemmas.
        """
        doc = nlp(text)
        lemmas = []
        for t in doc:
            if t.is_punct or t.is_space:
                continue
            lem = t.lemma_.lower()
            lemmas.append(lem)
        return tuple(lemmas)


    def detectar_comando(self, texto: str) -> tuple[str | None, str, list[str]]:
        texto_norm = normalize_text(texto)
        melhor_match = None
        melhor_match_len = 0
        pos_final = -1

        doc = nlp(texto)
        tokens = [t for t in doc if not t.is_punct and not t.is_space]
        lemmas = [t.lemma_.lower() for t in tokens]
        token_starts = [t.idx for t in tokens]
        tokens_texts = [t.text for t in tokens]

        def _match_flex(text_lemmas, syn_lemmas):
            j = 0
            for i, lemma in enumerate(text_lemmas):
                if lemma == syn_lemmas[j]:
                    j += 1
                    if j == len(syn_lemmas):
                        return True, i
            return False, -1

        for syn, cmd_name in list(Registry._lookup.items()):
            syn_doc = nlp(syn)
            syn_lemmas = [t.lemma_.lower() for t in syn_doc if not t.is_punct and not t.is_space]
            if not syn_lemmas:
                continue

            key_obj = Registry.keys.get(cmd_name)
            key_candidates = []
            if key_obj:
                if isinstance(key_obj, str):
                    key_candidates = [key_obj]
                else:
                    try:
                        for k in key_obj:
                            if isinstance(k, str):
                                key_candidates.append(k)
                    except Exception:
                        pass
            key_candidates = [normalize_text(k) for k in key_candidates if isinstance(k, str)]

            key_matched = False
            if key_candidates:
                for key_c in key_candidates:
                    key_lemmas = [t.lemma_.lower() for t in nlp(key_c) if not t.is_punct and not t.is_space]
                    matched, _ = _match_flex(lemmas, key_lemmas)
                    if (key_c in texto_norm) or matched:
                        key_matched = True
                        break
                if not key_matched:
                    continue

            matched, end_idx = _match_flex(lemmas, syn_lemmas)
            if matched:
                pos_candidate = token_starts[end_idx] + len(tokens_texts[end_idx])
                if len(syn_lemmas) > melhor_match_len:
                    melhor_match = (cmd_name, " ".join(syn_lemmas))
                    melhor_match_len = len(syn_lemmas)
                    pos_final = pos_candidate
                continue

            syn_norm = normalize_text(syn)
            syn_tokens = set(syn_norm.split())
            text_tokens = set(texto_norm.split())
            if syn_tokens and syn_tokens <= text_tokens:
                last_word = list(syn_tokens)[-1]
                pos = texto_norm.rfind(last_word)
                pos_candidate = pos + len(last_word) if pos != -1 else -1
                if len(syn_tokens) > melhor_match_len:
                    melhor_match = (cmd_name, syn_norm)
                    melhor_match_len = len(syn_tokens)
                    pos_final = pos_candidate

        if not melhor_match:
            argumento = " ".join(self.extract_entities(texto))
            return None, "", argumento # type: ignore

        cmd_name, syn_norm = melhor_match

        argumento_raw = texto[pos_final:].strip() if pos_final and pos_final > 0 else texto.strip()

        arg_doc = nlp(argumento_raw)
        arg_tokens = [t for t in arg_doc if not t.is_punct and not t.is_space]
        while arg_tokens and arg_tokens[0].pos_ in {"DET", "ADP"}:
            arg_tokens = arg_tokens[1:]
        argumento_raw = " ".join(t.text for t in arg_tokens)

        key_obj = Registry.keys.get(cmd_name)
        key_candidates = []
        if key_obj:
            if isinstance(key_obj, str):
                key_candidates = [key_obj]
            else:
                try:
                    for k in key_obj:
                        if isinstance(k, str):
                            key_candidates.append(k)
                except Exception:
                    pass
        key_candidates = [normalize_text(k) for k in key_candidates if isinstance(k, str)] # type: ignore

        if key_candidates and argumento_raw:
            arg_doc = nlp(argumento_raw)
            arg_tokens = [t for t in arg_doc if not t.is_punct and not t.is_space]
            if arg_tokens:
                first_text = arg_tokens[0].text
                first_lem = arg_tokens[0].lemma_.lower()
                removed = False
                for key_c in key_candidates:
                    key_lem = [t.lemma_.lower() for t in nlp(key_c) if not t.is_punct and not t.is_space]
                    if normalize_text(first_text) == key_c or (key_lem and first_lem == key_lem[0]):
                        arg_tokens = arg_tokens[1:]
                        removed = True
                        break
                if removed:
                    argumento_raw = " ".join(t.text for t in arg_tokens)

        entities = self.extract_entities(argumento_raw)
        self.last_entities = entities
        argumento = " ".join(entities).strip()

        return cmd_name, syn_norm, argumento # type: ignore

