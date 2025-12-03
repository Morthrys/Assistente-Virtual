# editar_entrada.py
import json
import threading
from cfunctions import storage
from function_reg import Registry
from difflib import get_close_matches
from text_for import normalize_text
from context_manager import CONTEXT

_edit_lock = threading.Lock()

def _fuzzy_find(name: str, options: list[str]) -> str | None:
    matches = get_close_matches(name.lower(), [o.lower() for o in options], n=1, cutoff=0.6)
    if matches:
        lower_map = {o.lower(): o for o in options}
        return lower_map.get(matches[0])
    return None

@Registry.command("editar_entrada", aliases=["excluir_entrada", "modificar_entrada", "alterar_entrada"], key="entrada")
def edit(name: str):
    try:
        parts = name.strip().split()
        if not parts:
            jsons = [f"{k}_map" for k in storage._storage.keys()]
            if not jsons:
                print("Konto> Nenhum JSON encontrado no diretório data/.")
            else:
                print("Konto> Forneça junto ao comando o nome do JSON desejado.\n- " + "\n- ".join(jsons))
            return
        
        file_base = normalize_text(parts[0])
        all_jsons = {normalize_text(k): k for k in storage._storage.keys()}
        if file_base not in all_jsons:
            sugestao = _fuzzy_find(file_base, list(all_jsons.keys()))
            if sugestao:
                real_name = all_jsons[sugestao]
                if file_base.lower() == sugestao.lower() or len(sugestao) / max(len(file_base), 1) > 0.85:
                    file_base = real_name
                else:
                    def confirmar_json(resp: str):
                        if resp in ("s", "sim"):
                            edit(f"{real_name} {' '.join(parts[1:])}")
                        else:
                            print("Konto> Ação cancelada.")
                    print(f"Konto> '{file_base}' não encontrado. Usar {sugestao}? (S/N): ")
                    CONTEXT.set("editar_entrada_confirma_json", confirmar_json)
                    return
            else:
                print(f"Konto> '{file_base}' não corresponde a nenhum JSON conhecido")
                print("Disponíveis:\n- " + "\n- ".join(all_jsons.values()))
                return
        else:
            file_base = all_jsons[file_base]
            
        data = storage.get_data(file_base)
        if data is None or not data:
            print(f"Konto> O arquivo '{file_base}_map.json' está vazio ou não existe.")
            return
        
        if isinstance(data, dict):
            chaves = list(data.keys())
        elif isinstance(data, list):
            chaves = [str(i) for i in range(len(data))]
        else:
            print("Konto> Estrutura de dados inválida (não é dict nem list).")
            return

        selection = parts[1] if len(parts) > 1 else None
        if not selection:
            lines = [f"Konto> Entradas em {file_base}_map.json:"]
            for k in chaves:
                lines.append(f"- {k}")
            print("\n".join(lines))
            print("Konto> Digite a entrada que deseja (ou Enter para cancelar): ")
            def handle_selection(resp: str):
                if not resp:
                    print("Konto> Ação cancelada pelo usuário")
                else:
                    edit(f"{file_base} {resp}")
            CONTEXT.set("editar_entrada_select", handle_selection)
            return
        
        selection_norm = normalize_text(selection)
        selected_key = None
        selected_index = None
        entry = None
        
        if isinstance(data, dict):
            norm_map = {normalize_text(k): k for k in data.keys()}
            key_match = norm_map.get(selection_norm)
            if not key_match:
                sugestao = _fuzzy_find(selection_norm, list(norm_map.keys()))
                if sugestao:
                    real_key = norm_map[sugestao]
                    def confirmar_entrada(resp: str):
                        if resp in ("s", "sim"):
                            edit(f"{file_base} {real_key}")
                        else:
                            print("Konto> Ação cancelada.")
                    print(f"Konto> Entrada '{selection}' não encontrada. Usar {real_key}? (S/N): ")
                    CONTEXT.set("editar_entrada_confirma_entrada", confirmar_entrada)
                    return
            if key_match:
                selected_key = key_match
                entry = data[selected_key]

        elif isinstance(data, list):
            if selection_norm.isdigit():
                idx = int(selection_norm)
                if 0 <= idx < len(data):
                    selected_index = idx
                    entry = data[idx]
            else:
                norm_list = [normalize_text(str(x)) for x in data] # type: ignore
                if selection_norm in norm_list:
                    selected_index = norm_list.index(selection_norm)
                    entry = data[selected_index]
                else:
                    sugestao = _fuzzy_find(selection_norm, norm_list)
                    if sugestao:
                        idx = norm_list.index(sugestao)
                        def confirmar_lista(resp: str):
                            if resp in ("s", "sim"):
                                edit(f"{file_base} {idx}")
                            else:
                                print("Konto> Ação cancelada.")
                        print(f"Konto> Entrada '{selection}' não encontrada. Usar índice {idx}? (S/N): ")
                        CONTEXT.set("editar_entrada_confirma_lista", confirmar_lista)
                        return
        
        if entry is None:
            print(f"Konto> Entrada '{selection}' não encontrada em {file_base}_map.json.")
            return
        
        print(f"Konto> Entrada selecionada ({selection}):")
        try:
            print(json.dumps(entry, indent=2, ensure_ascii=False))
        except Exception:
            print(repr(entry))
        print("Konto> Digite editar[E] / excluir[X] / cancelar[C]: ")

        def handle_action(resp: str):
            resp = resp.strip().lower()
            if resp in ("x", "excluir"):
                with _edit_lock:
                    if isinstance(data, dict) and selected_key:
                        storage.delete_data(file_base, selected_key)
                    elif isinstance(data, list) and selected_index is not None:
                        data.pop(selected_index) # type: ignore
                        storage.save_data(file_base)
                    print(f"Konto> Entrada '{selection}' excluída de {file_base}_map.json.")
                storage.load_data()
            elif resp in ("e", "editar"):
                print(f"Konto> Novo valor de {selection}: ")
                def handle_edit(new_value: str):
                    new_value = new_value.strip()
                    try:
                        parsed_value = json.loads(new_value)
                    except json.JSONDecodeError:
                        parsed_value = new_value  
                    with _edit_lock:
                        if isinstance(data, dict) and selected_key:
                            storage.set_data(file_base, selected_key, parsed_value)
                        elif isinstance(data, list) and selected_index is not None:
                            data[selected_index] = parsed_value  # type: ignore
                            storage.save_data(file_base)
                    print(f"Konto> Entrada '{selection}' atualizada em {file_base}_map.json.")
                    storage.load_data()
                CONTEXT.set("editar_entrada_valor", handle_edit)
            else:
                print("Konto> Ação cancelada.")
        CONTEXT.set("editar_entrada_acao", handle_action)
        
    except Exception as e:
        print(f"Konto> Erro ao editar entrada: {e}")
