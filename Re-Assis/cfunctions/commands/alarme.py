# alarme.py
import datetime
import time
import re
import threading
import sys
from function_reg import Registry
from cfunctions import storage

if not hasattr(storage, "ALARMES"):
    alarme = storage.get_data("ALARMES")

alarme_tocando = {"ativo": False, "hora": None, "stop_event": None}

def safe_print(msg: str):
    sys.stdout.write("\r" + msg + "\n")
    sys.stdout.flush()

def _tocar_alarme(hora_str, alarme_time):
    tempo_restante = (alarme_time - datetime.datetime.now()).total_seconds()
    if tempo_restante > 0:
        time.sleep(tempo_restante)

    alarmes = alarme.get(hora_str)
    if not alarmes or not alarmes.get("ativo"):
        return

    stop_event = threading.Event()
    alarme_tocando["ativo"] = True
    alarme_tocando["hora"] = hora_str
    alarme_tocando["stop_event"] = stop_event

    safe_print(f"Konto> Alarme tocando! São {alarme_time.strftime('%H:%M')}")

    def bloop():
        try:
            import winsound
            while not stop_event.is_set() and alarme.get(hora_str, {}).get("ativo", False):
                winsound.Beep(1000, 400)
                time.sleep(0.3)
        except Exception:
            safe_print("Konto> (som não disponível neste sistema)")

    threading.Thread(target=bloop, daemon=True).start()

    while not stop_event.is_set():
        time.sleep(0.1)

    alarme_tocando.update({"ativo": False, "hora": None, "stop_event": None})
    alarme.pop(hora_str, None)
    safe_print("Konto> Alarme encerrado")

@Registry.command("alarme", aliases=["despertador", "tocar_alarme", "tocar_despertador"])
def alarm(name: str):
    storage.load_data()
    if not name:
        print("Konto> Especifique o horário do alarme ou comando ('listar', 'cancelar').")
        return

    text = name.lower().strip()
    now = datetime.datetime.now()

    if "cancelar todos" in text:
        for t in list(alarme.values()):
            t["ativo"] = False
        alarme.clear()
        print("Konto> Todos os alarmes foram cancelados")
        return

    if "cancelar" in text:
        match_can = re.search(r"(\d{1,2})(?::(\d{2}))?", text)
        if match_can:
            hora = int(match_can.group(1))
            minuto = int(match_can.group(2)) if match_can.group(2) else 0
            alvo = f"{hora:02d}:{minuto:02d}"
            removidos = [h for h in list(alarme.keys()) if h.startswith(alvo)]
            if removidos:
                for h in removidos:
                    alarme[h]["ativo"] = False
                    del alarme[h]
                print(f"Konto> Alarme das {alvo} cancelado com sucesso")
            else:
                print(f"Konto> Nenhum alarme encontrado para {alvo}.")
        else:
            print("Konto> Informe o horário do alarme a cancelar, ex: 'cancelar alarme das 8:30'.")
        return

    if "listar" in text or "ativos" in text:
        if not alarme:
            print("Konto> Nenhum alarme ativo no momento")
            return
        print("Konto> Alarmes ativos:")
        for k, v in alarme.items():
            hora = v["hora"].strftime("%H:%M")
            restante = int((v["hora"] - now).total_seconds())
            if restante < 0:
                restante = 0
            m, s = divmod(restante, 60)
            print(f" - {hora} (em {m} min e {s} seg)")
        return

    match_em_comp = re.search(r"\b(?:em|me acorde em|tocar em|alarme em|daqui a|daqui)\s*(\d+)\s*(?:hora|horas|h)\s*(?:e\s*(\d+)\s*(?:minuto|minutos|min|m))?", text)
    match_em_min = re.search(r"\b(?:em|me acorde em|tocar em|alarme em|daqui a|daqui)\s*(\d+)\s*(?:minuto|minutos|min|m)\b", text)
    match_abs = re.search(r"(\d{1,2})(?::(\d{2}))?", text)

    alarme_time = None

    if match_em_comp:
        horas = int(match_em_comp.group(1))
        minutos = int(match_em_comp.group(2)) if match_em_comp.group(2) else 0
        delta = datetime.timedelta(hours=horas, minutes=minutos)
        alarme_time = now + delta
    elif match_em_min:
        minutos = int(match_em_min.group(1))
        delta = datetime.timedelta(minutes=minutos)
        alarme_time = now + delta
    elif match_abs:
        hora = int(match_abs.group(1))
        minuto = int(match_abs.group(2)) if match_abs.group(2) else 0
        alarme_time = now.replace(hour=hora, minute=minuto, second=0, microsecond=0)
        if alarme_time <= now:
            alarme_time += datetime.timedelta(days=1)
    else:
        print("Konto> Não consegui entender o horário do alarme.")
        return

    tempo_restante = (alarme_time - datetime.datetime.now()).total_seconds()
    id_alarme = alarme_time.strftime("%H:%M:%S")

    alarme[id_alarme] = {
        "hora": alarme_time,
        "ativo": True,
        "thread": threading.Thread(target=_tocar_alarme, args=(id_alarme, alarme_time), daemon=True),
    }

    alarme[id_alarme]["thread"].start()
    m, s = divmod(int(tempo_restante), 60)
    print(f"Konto> Alarme definido para {alarme_time.strftime('%H:%M')} ({m} min e {s} seg restantes).")

@Registry.command("parar_alarme", aliases=["desligar_despertador", "parar_despertador", "desligar_alarme"])
def parar_alarme():
    if not alarme_tocando["ativo"]:
        print("Konto> Nenhum alarme tocando no momento.")
        return
    stop_event = alarme_tocando.get("stop_event")
    if stop_event:
        stop_event.set()
    else:
        print("Konto> Erro interno ao tentar parar o alarme")