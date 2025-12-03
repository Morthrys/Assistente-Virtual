# abrir_app.py
import os
import subprocess
import platform
from difflib import get_close_matches
from function_reg import Registry
from cfunctions import storage
from cfunctions.cache_sys import CACHE
from context_manager import CONTEXT

@Registry.command("abrir_app", aliases=["iniciar", "abrir", "executar"])
def abrir_app(nome: str):
    storage.load_data()
    apps = storage.get_data("apps")
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

    if nome in apps:
        print(f"Konto> Abrindo App {nome}")
        return abrir(apps[nome])
    
    print(f"Konto> App '{nome}' não está salvo, tentando achar no sistema")

    candidates = sorted(CACHE.executaveis, 
        key=lambda x: (not x.lower().endswith(".lnk"), x.lower()))
    match = get_close_matches(nome.lower(), [os.path.basename(e).lower() for e in candidates], n=len(candidates), cutoff=0.6)
    
    if not match:
        print(f"Konto> Nenhum aplicativo correspondente a '{nome}' foi encontrado.")
        return
    
    candidato = next((e for e in candidates if os.path.basename(e).lower() == match[0]), None)
    if not candidato or not os.path.exists(candidato):
        print("Konto> Nenhum caminho válido encontrado")
        return
    
    print(f"Konto> Abrindo App {nome}")
    abrir(candidato)
    
    def confirmar(resposta: str):
        r = resposta.strip().lower()
        if r in("s", "sim"):
            print(f"Konto> Deseja salvar {nome}? (s/n)")
            CONTEXT.set("salvar_app", salvar_app)
        else:
            print("Konto> Procurando próximo caminho possível")

    def salvar_app(resposta: str):
        r = resposta.strip().lower()
        if r in ("s", "sim"):   
            storage.set_data("apps", nome, candidato)
            print(f"Konto> App '{nome}' salvo com sucesso.")
    
    print(f"Konto> O app '{nome}' foi aberto? (s/n)")
    CONTEXT.set("confirmar_abrir_app", confirmar)