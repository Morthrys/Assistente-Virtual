# pesquisar.py
import webbrowser
from function_reg import Registry
from cfunctions import storage
from context_manager import CONTEXT

@Registry.command("pesquisar", aliases=["buscar", "procurar"])
def pesquisar_web(query: str):
    storage.load_data()
    sites = storage.get_data("sites")

    if query.startswith(("http://", "https://", "www.")):
        if not query.startswith(("http://", "https://")):
            query = "https://" + query
        print("Konto> Abrindo link direto")
        webbrowser.open(query)
        print("Konto> Deseja salvar esse link? (s/n):")
        CONTEXT.set("pesquisar_salvar_link", lambda resp: salvar_link(resp, query))
        return

    if query in sites:
        url = sites[query]
        print(f"Konto> Abrindo site salvo: {url}")
        webbrowser.open(url)
        return

    print(f"Konto> Pesquisando '{query}' na web...")
    webbrowser.open(f"https://www.google.com/search?q={query}")
    print("Konto> Deseja salvar essa pesquisa como atalho? (s/n):")
    CONTEXT.set("pesquisar_salvar_pesquisa", lambda resp: salvar_pesquisa(resp, query))


def salvar_link(resp: str, query: str):
    resp = resp.strip().lower()
    if resp in ("s", "sim"):
        print("Konto> Digite o apelido para o link:")
        CONTEXT.set("apelido_link", lambda apelido: salvar_site_final(apelido, query))


def salvar_pesquisa(resp: str, termo: str):
    resp = resp.strip().lower()
    if resp in ("s", "sim"):
        print("Konto> Digite a URL para salvar:")
        CONTEXT.set("url_pesquisa", lambda url: salvar_site_final(termo, url))


def salvar_site_final(chave: str, valor: str):
    storage.set_data("sites", chave.strip().lower(), valor.strip())
    print(f"Konto> Atalho '{chave}' -> {valor} salvo com sucesso.")