# data_hora.py
import re
import locale
import dateparser
from function_reg import Registry
from datetime import datetime, timedelta

try:
    locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
except Exception:
    pass

@Registry.command("data_atual", aliases=["hora", "agora", "data"])
def inform_day(argumento: str = "", texto_original: str = ""):
    texto = (texto_original or argumento).lower().strip()
    now = datetime.now()

    if texto in ["hora", "horas"]:
        print(f"Konto> Agora são {now.strftime('%H:%M:%S')}.")
        return

    # Extrai uma frase temporal simples
    def extract_time_phrase(text):
        patterns = [
            r"\b(há|ha|atrás|antes|daqui a|daqui|em)\b[^.?,;]{0,40}\b(\d+|um|uma|dois|duas|três|tres|quatro|cinco|seis|sete|oito|nove|dez)\b[^.?,;]{0,20}\b(minuto|minutos|hora|horas|dia|dias|semana|semanas|m[eê]s|mes|meses|ano|anos)\b",
            r"\b(\d{1,2})\s*(de)?\s*([a-zçãéíóú]+)\s*(de\s*\d{4})?\b",
            r"\b(\d{1,2})[\/\-](\d{1,2})([\/\-]\d{2,4})?\b",
            r"\b(amanh[ãa]|ontem|anteontem|depois de amanhã|depois de amanha|hoje)\b",
            r"\bàs?\s*\d{1,2}(:\d{2})?\b",
            r"\b\d{1,2}:\d{2}\b", 
        ]
        for p in patterns:
            m = re.search(p, text, flags=re.IGNORECASE)
            if m:
                return m.group(0)
        return None
    
    phrase = extract_time_phrase(texto)
    to_parse = phrase if phrase else texto

    if any(p in texto for p in ["há", "ha", "atrás", "antes"]):
        prefer_dir = "past"
    elif any(p in texto for p in ["daqui", "depois", "próximo", "proximo", "seguinte", "futuro", "em "]):
        prefer_dir = "future"
    else:
        prefer_dir = "current_period"

    rel_match = re.search(r"(há|ha|atrás|antes|daqui a|daqui|em)\s*(\d+|um|uma|dois|duas|três|tres|quatro|cinco|seis|sete|oito|nove|dez)\s*(minuto|minutos|hora|horas|dia|dias|semana|semanas|m[eê]s|mes|meses|ano|anos)", texto, flags=re.IGNORECASE)

    parsed = None
    if rel_match:
        dir_word, num_word, unid = rel_match.groups()
        map_num = {
            "um": 1, "uma": 1, "dois": 2, "duas": 2, "três": 3, "tres": 3,
            "quatro": 4, "cinco": 5, "seis": 6, "sete": 7, "oito": 8, "nove": 9, "dez": 10,
        }
        value = int(map_num.get(num_word, num_word))
        mult = -1 if dir_word in ["há", "ha", "atrás", "atras", "antes"] else 1
        if "minuto" in unid:
            parsed = now + timedelta(minutes=value * mult)
        elif "hora" in unid:
            parsed = now + timedelta(hours=value * mult)
        elif "semana" in unid:
            parsed = now + timedelta(weeks=value * mult)
        elif "m" in unid:
            parsed = now + timedelta(days=30 * value * mult)
        elif "ano" in unid:
            parsed = now + timedelta(days=365 * value * mult)
        elif "dia" in unid:
            parsed = now + timedelta(days=value * mult)
            
    if not parsed:
        # Tenta interpretar a data/hora
        parsed = dateparser.parse(
            to_parse,
            languages=["pt"],
            settings={
                "RELATIVE_BASE": now,
                "PREFER_DATES_FROM": prefer_dir,
                "RETURN_AS_TIMEZONE_AWARE": False,
            },
        )

    # Se não conseguiu parse, tenta reconhecer datas explícitas tipo "25 de dezembro"
    if not parsed:
        match = re.search(r"(\d{1,2})\s+de\s+([a-zç]+)", texto)
        if match:
            day, month_name = match.groups()
            meses = {
                "janeiro": 1, "fevereiro": 2, "março": 3, "marco": 3, "abril": 4,
                "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
                "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
            }
            m = meses.get(month_name, now.month)
            year = now.year
            # se o mês já passou neste ano → assume próximo ano
            if m < now.month:
                year += 1
            parsed = datetime(year, m, int(day))
        else:
            parsed = now

    diff = (parsed - now).total_seconds()
    abs_diff = abs(diff)
    date_fmt = parsed.strftime("%d/%m/%Y")
    hour_fmt = parsed.strftime("%H:%M:%S")
    week_day = parsed.strftime("%A").capitalize()

    wants_time = bool(re.search(r"\b(hora|horas|minuto|minutos|às|as)\b", texto))
    wants_date = bool(re.search(r"\b(dia|data|semana|m[eê]s|mes|ano|quando|cai)\b", texto)) or bool(re.search(r"\d{1,2}\s*de\s*[a-zçãé]+", texto)) or bool(re.search(r"\d{1,2}[\/\-]\d{1,2}", texto))

    if wants_time and not wants_date:
        if abs_diff < 60:
            print(f"Konto> Agora são {now.strftime('%H:%M:%S')}.")
            return
        elif diff < 0:
            mins = int(abs_diff // 60)
            hrs = int(abs_diff // 3600)
            if hrs >= 1:
                print(f"Konto> Há {hrs} hora(s) eram {hour_fmt}.")
            else:
                print(f"Konto> Há {mins} minuto(s) eram {hour_fmt}.")
        else:
            mins = int(abs_diff // 60)
            hrs = int(abs_diff // 3600)
            if hrs >= 1:
                print(f"Konto> Daqui a {hrs} hora(s) será {hour_fmt}.")
            else:
                print(f"Konto> Daqui a {mins} minuto(s) será {hour_fmt}.")
        return

    # Resposta para datas explícitas
    if re.search(r"\d{1,2}\s*de\s*[a-zçãé]+|\d{1,2}[\/\-]\d{1,2}", texto, flags=re.IGNORECASE):
        print(f"Konto> {date_fmt} cairá em uma {week_day}.")
        return

    if wants_date:
        if diff < -1:
            print(f"Konto> A data foi {date_fmt} ({week_day}).")
        elif diff > 1:
            print(f"Konto> A data será {date_fmt} ({week_day}).")
        else:
            print(f"Konto> Hoje é {date_fmt} ({week_day}).")
        return

    print(f"Konto> Hoje é {now.strftime('%d/%m/%Y')} ({now.strftime('%A').capitalize()}), e são {now.strftime('%H:%M:%S')}.")