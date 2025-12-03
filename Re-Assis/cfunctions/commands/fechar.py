# fechar.py
import platform
from function_reg import Registry
from difflib import get_close_matches
import psutil
from context_manager import CONTEXT

system = platform.system()
try:
    if system == "Windows":
        import win32gui
        import win32con
        import win32process
        from pywinauto import Application
    else:
        import pygetwindow as gw
except ImportError:
    pass

@Registry.command("fechar", aliases=["encerrar"]) 
def fechar(name: str):
    name = name.strip().lower()

    if not name:
        return "Konto> Nenhum nome informado para fechar"
    
    janelas = list_janelas()
    janelas_enc = []

    if janelas:
        # Lista apenas títulos legíveis
        titles = [title.lower() for _, title in janelas if title.strip()]
        corresp = _search_janelas_corresp(name, titles)
        if corresp:
            # Seleciona janelas correspondentes e filtra pelo executável
            for hwnd, title in janelas:
                if title.lower() in corresp:
                    if _verificar_exec(hwnd, name):
                        # Filtra janelas fantasmas (ex: "Deseja sair", "Salvar alterações")
                        t_lower = title.lower()
                        if any(x in t_lower for x in ["deseja", "salvar", "confirmar", "fechar", "imprimir"]):
                            continue
                        if name == "pdf" and ".pdf" not in t_lower and "acrobat" not in t_lower:
                            continue
                        janelas_enc.append((hwnd, title))

    if janelas_enc:
        # Se só 1 janela
        if len(janelas_enc) == 1:
            hwnd, title = janelas_enc[0]
            # Para Adobe PDF no Windows, tratar múltiplas abas
            if system == "Windows" and "acrobat" in title.lower():
                _fechar_pdf_com_pywinauto([hwnd], name)
            else:
                close_janela(hwnd, title)
            return
        
        # Se houver múltiplas, permite escolher um arquivo específico
        docs_map = {i+1: (hwnd, title) for i, (hwnd, title) in enumerate(janelas_enc)}
        print("Konto> Foram encontradas várias janelas/documentos: ")
        for i, (_, title) in docs_map.items():
            print(f" {i}. {title}")

        def escolher_para_fechar(choice: str):
            choice = choice.strip().lower()
            if choice == "cancelar":
                print("Konto> Operação cancelada.")
                return
            if choice in ["todas", "todos"]:
                if system == "Windows" and any("acrobat" in t.lower() for _, t in janelas_enc):
                    _fechar_pdf_com_pywinauto([hwnd for hwnd, _ in janelas_enc], name)
                else:
                    for hwnd, title in janelas_enc:
                        close_janela(hwnd, title)
                return
            try:
                # Multi-seleção
                indices = [int(x.strip()) for x in choice.split(",")]
                fechadas = set()
                hwnds_pdf = []
                for idx in indices:
                    if idx in docs_map:
                        hwnd, title = docs_map[idx]
                        if system == "Windows" and "acrobat" in title.lower():
                            hwnds_pdf.append(hwnd)
                        else:
                            close_janela(hwnd, title)
                        fechadas.add(idx)
                    else:
                        print(f"Konto> Número inválido: {idx}")
                if hwnds_pdf:
                    _fechar_pdf_com_pywinauto(hwnds_pdf, name)
                if not fechadas:
                    print("Konto> Nenhuma janela foi fechada.")
            except ValueError:
                print("Konto> Entrada inválida")

        CONTEXT.set("fechar_escolha", escolher_para_fechar)
        print("Konto> Qual deseja fechar? (números separados por vírgula, 'todas(os)' ou 'cancelar')")
        return

    # Se não encontrou janelas, tenta pelo processo
    _fechar_por_processo(name)


def _fechar_pdf_com_pywinauto(hwnd_list, name):
    """ Fecha abas PDF abertas no Adobe Reader sem fechar o processo inteiro """
    try:
        for hwnd in hwnd_list:
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                app = Application(backend="uia").connect(process=pid)
                window = app.window(handle=hwnd)

                # Lista todas as abas/documentos visíveis
                docs = []
                for w in window.descendants(control_type="Document"):
                    title = w.window_text()
                    if title and ".pdf" in title.lower():
                        docs.append((w, title))

                # Se não encontrou documentos filhos, tenta a própria janela
                if not docs and ".pdf" in window.window_text().lower():
                    docs.append((window, window.window_text()))

                if not docs:
                    continue

                # Pergunta ao usuário se houver múltiplos
                if len(docs) > 1:
                    print("Konto> Foram encontradas várias abas PDF:")
                    for i, (_, title) in enumerate(docs, 1):
                        print(f" {i}. {title}")

                    def escolher_pdf(choice: str):
                        choice = choice.strip().lower()
                        if choice == "cancelar":
                            print("Konto> Operação cancelada.")
                            return
                        if choice in ["todas", "todos"]:
                            to_close = docs
                        else:
                            try:
                                indices = [int(x.strip())-1 for x in choice.split(",")]
                                to_close = [docs[i] for i in indices if 0 <= i < len(docs)]
                            except ValueError:
                                print("Konto> Entrada inválida")
                                return
                        for doc, title in to_close:
                            try:
                                doc.type_keys("^w")
                                print(f"Konto> '{title}' foi fechado com sucesso")
                            except Exception as e:
                                print(f"Konto> Erro ao fechar '{title}': {e}")

                    CONTEXT.set("fechar_pdf", escolher_pdf)
                    print("Konto> Qual deseja fechar? (números separados por vírgula, 'todas(os)' ou 'cancelar')")
                    return
                else:
                    to_close = docs

                # Fecha apenas as abas selecionadas
                for doc, title in to_close:
                    try:
                        doc.type_keys("^w")
                        print(f"Konto> '{title}' foi fechado com sucesso")
                    except Exception as e:
                        print(f"Konto> Erro ao fechar '{title}': {e}")

            except Exception:
                continue

    except Exception as e:
        print(f"Konto> Erro ao conectar com Adobe Reader: {e}")


def list_janelas():
    if system == "Windows":
        janelas = []

        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    # Ignora diálogos sem documento (Adobe confirmações, tooltips etc)
                    t = title.lower()
                    if any(x in t for x in ["deseja", "salvar", "confirmar", "caixa de diálogo", "erro", "alerta"]):
                        return
                    janelas.append((hwnd, title))
        
        win32gui.EnumWindows(callback, None)
        return janelas
    else:
        janelas = []
        for win in gw.getAllWindows():
            if win.title and win.isVisible:
                t = win.title.lower()
                if any(x in t for x in ["deseja", "salvar", "confirmar", "caixa de diálogo", "erro", "alerta"]):
                    continue
                janelas.append((win, win.title))
        return janelas
    

def close_janela(hwnd, title):
    try:
        if system == "Windows":
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        else:
            hwnd.close()
        print(f"Konto> '{title}' foi fechado com sucesso")
    except Exception as e:
        print(f"Konto> Erro ao tentar fechar '{title}': {e}")


def _search_janelas_corresp(name, titles):
    # Substring match
    corresp = []
    for t in titles:
        if name == "pdf" and ".pdf" in t:
            corresp.append(t)
        elif name in t:
            corresp.append(t)
    if corresp:
        return corresp
    return get_close_matches(name, titles, n=5, cutoff=0.4)


def _verificar_exec(hwnd, name):
    try:
        if system == "Windows":
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            proc = psutil.Process(pid)
            exe_name = proc.name().lower()
            title = win32gui.GetWindowText(hwnd).lower()

            if name == "pdf":
                if ".pdf" in title or "acrobat" in exe_name:
                    return True

            if (name in exe_name or exe_name in get_close_matches(name, [exe_name], n=1, cutoff=0.6)) \
               or (name in title):
                return True
            return False
        else:
            pid = getattr(hwnd, "_hWnd", None)
            if pid:
                for proc in psutil.process_iter(['pid', 'name']):
                    if proc.pid == pid:
                        exe_name = proc.info['name'].lower()
                        title = getattr(hwnd, "title", "").lower()
                        if name == "pdf" and (".pdf" in title or "acrobat" in exe_name):
                            return True
                        if (name in exe_name or exe_name in get_close_matches(name, [exe_name], n=1, cutoff=0.6)) \
                           or (name in title):
                            return True
            return True
    except Exception:
        return True


def _fechar_por_processo(name):
    # Mapeamento rápido para Adobe Reader
    if name.lower() in ["pdf", "acrobat"]:
        target_names = ["Acrobat.exe"]
    else:
        target_names = [name.lower()]

    fechado = False
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] in target_names:
                proc.terminate()
                fechado = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if fechado:
        print(f"Konto> Processo(s) '{name}' encerrado(s).")
    else:
        print(f"Konto> Nenhum processo correspondente a '{name}' foi encontrado.")
