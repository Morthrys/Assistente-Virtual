# abrir_arquivo.py
import os
import subprocess
import platform
from difflib import get_close_matches
from function_reg import Registry
from cfunctions.cache_sys import CACHE
from context_manager import CONTEXT

@Registry.command("abrir_arquivo", aliases=["iniciar_arquivo", "executar_arquivo"], key=["arquivo"])
def abrir_arquivo(name: str):
    sistema = platform.system()

    def abrir(caminho):
        try:
            if sistema == "Windows":
                subprocess.Popen(['start', "", caminho], shell=True)
            elif sistema == "Darwin":
                subprocess.Popen(["open", caminho])
            else:
                subprocess.Popen(["xdg-open", caminho])
        except Exception as e:
            print(f"Konto> Erro ao abrir {caminho}: {e}")

    candidates = sorted(CACHE.arquivos)
    match = get_close_matches(name.lower(), [os.path.basename(e).lower() for e in candidates], n=len(candidates), cutoff=0.4)

    if not match:
        print(f"Konto> Nenhum arquivo correspondente a '{name}' foi encontrado.")
        return

    for m in match:
        caminho = CACHE._resolver_arquivo(m)
        if not caminho:
            print(f"Konto> Arquivo '{caminho}' não foi encontrado no sistema.")
            continue

        print(f"Konto> Abrindo Arquivo {name}")
        abrir(caminho)
        print(f"Konto> O arquivo correto foi aberto? (s/n)")
        CONTEXT.set("confirmar_arquivo", lambda resp: confirmar_arquivo(resp, name, match, abrir))
        return

    print(f"Konto> Não foi possível abrir {name}")


def confirmar_arquivo(resp: str, name: str, match, abrir_func):
    resp = resp.strip().lower()
    if resp in ("s", "sim"):
        print("Konto> Arquivo confirmado com sucesso.")
        return
    print("Konto> Procurando próximo arquivo possível...")
    match = match[1:]
    caminho = CACHE._resolver_arquivo(match[0])
    if caminho:
        print(f"Konto> Tentando abrir {match[0]}...")
        abrir_func(caminho)
        print(f"Konto> O arquivo correto foi aberto? (s/n)")
        CONTEXT.set("confirmar_arquivo", lambda r: confirmar_arquivo(r, name, match, abrir_func))
