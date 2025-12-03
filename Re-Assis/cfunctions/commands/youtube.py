# youtube.py
import threading
import yt_dlp
import os
import string
import sys
import contextlib
from function_reg import Registry
from cfunctions.storage import BASE_DIR

player_info = {"player": None, "tocando": False, "titulo": None, "loop": False,}

CACHE_FILE = os.path.join(BASE_DIR, ".cache_vlc_path")

playlist = []
playlist_index = -1

def localizar_vlc() -> str | None:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                caminho = f.read().strip()
                if caminho and os.path.exists(os.path.join(caminho, "libvlc.dll")):
                    return caminho
        except:
            pass

    caminhos_possiveis = [
        os.path.join("Program Files", "VideoLAN", "VLC"),
        os.path.join("Program Files (x86)", "VideoLAN", "VLC"),
        "VLC",
    ]
    unidades = [f"{letra}:\\" for letra in string.ascii_uppercase if os.path.exists(f"{letra}:\\")]

    for unidade in unidades:
        for caminho_rel in caminhos_possiveis:
            caminho = os.path.join(unidade, caminho_rel)
            if os.path.exists(os.path.join(caminho, "libvlc.dll")):
                with open(CACHE_FILE, "w", encoding="utf-8") as f:
                    f.write(caminho)
                return caminho

    for unidade in unidades:
        for root, dirs, files in os.walk(unidade):
            if "libvlc.dll" in files:
                with open(CACHE_FILE, "w", encoding="utf-8") as f:
                    f.write(root)
                return root
    return None

vlc_path = localizar_vlc()
if vlc_path:
    os.add_dll_directory(vlc_path)
else:
    print("Konto> Aviso: libvlc.dll não foi localizado, certifique-se de que o VLC está instalado.")

import vlc

class YTLogger:
    def debug(self, msg):
        pass
    def warning(self, msg):
        pass
    def error(self, msg):
        print(f"Konto> Error: {msg}", file=sys.stderr)

@Registry.command("tocar", aliases=["play", "reproduzir"])
def tocar_video(busca: str):
    global player_info
    try:
        busca = busca.strip()
        if not busca:
            print("Konto> Informe o nome do vídeo ou música para tocar.")
            return

        if player_info["player"] and player_info["tocando"]:
            player_info["player"].stop()

        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "default_search": "ytsearch1",
            "nocheckcertificate": True,
            "logger": YTLogger(),
        }
        
        devnull = open(os.devnull, "w", encoding="utf-8", errors="ignore")
        with contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
                info = ydl.extract_info(busca, download=False)
        
        devnull.close()
        entry = info["entries"][0] if "entries" in info and len(info["entries"]) > 0 else info
        url = entry.get("url")
        titulo = entry.get("title", "Desconhecido")

        if not url:
            print("Konto> Não foi possível obter o link de streaming para esta mídia.")
            return

        instance = vlc.Instance("--no-video")
        player = instance.media_player_new()  # type: ignore
        media = instance.media_new(url)  # type: ignore
        player.set_media(media)

        def play_stream():
            player.play()
            player_info.update({"player": player, "tocando": True, "titulo": titulo})

        threading.Thread(target=play_stream, daemon=True).start()
        print(f"Konto> Tocando agora: {titulo}")
        return

    except Exception as e:
        print(f"Konto> Erro ao tentar reproduzir: {e}")
        return

@Registry.command("parar_reprodução", aliases=["stop", "parar", "cancelar"], key=["reproducao", "musica", "music", "video"])
def stop_vid():
    global player_info
    try:
        if player_info["player"] and player_info["tocando"]:
            player_info["player"].stop()
            player_info.update({"player": None, "tocando": False, "titulo": None})
            print("Konto> Reprodução encerrada")
            return
        print("Konto> Nenhuma música ou vídeo tocando no momento")
        return
    except Exception as e:
        print(f"Konto> Erro ao parar reprodução: {e}")
        return

@Registry.command("pausar_reprodução", aliases=["pause", "pausar"], key=["reproducao", "musica", "music", "video"])
def pausar_vid():
    global player_info
    try:
        player = player_info["player"]

        if not player or not player_info["tocando"]:
            print("Konto> Nada está tocando no momento.")
            return
        
        if player.is_playing():
            player.pause()
            player_info["tocando"] = False
            print("Konto> Reprodução pausada.")
        else:
            print("Konto> A reprodução já está pausada.")

    except Exception as e:
        print(f"Konto> Erro: {e}")

@Registry.command("retomar_reprodução", aliases=["resume", "retomar", "continuar"], key=["reproducao", "musica", "music", "video"])
def retomar_vid():
    global player_info
    try:
        player = player_info["player"]

        if not player:
            print("Konto> Nenhuma mídia carregada para retomar.")
            return
        
        state = player.get_state()

        if state in (vlc.State.Paused, vlc.State.Stopped): # type: ignore
            player.play()
            player_info["tocando"] = True
            print("Konto> Reprodução retomada.")
        else:
            print("Konto> A mídia já está tocando.")

    except Exception as e:
        print(f"Konto> Erro ao retomar reprodução: {e}")

"""@Registry.command("pausar_reprodução", aliases=["pause", "pausar"], key=["reproducao", "musica", "music", "video"])
def pausar_vid():
    player = player_info["player"]
    if not player or not player_info["tocando"]:
        print("Konto> Nada está tocando.")
        return
    if player.is_playing():
        player.pause()
        player_info["tocando"] = False
        print("Konto> Pausado.")
    else:
        print("Konto> Já está pausado.")

@Registry.command("retomar_reprodução", aliases=["resume", "retomar"], key=["reproducao", "musica", "music", "video"])
def retomar_vid():
    player = player_info["player"]
    if not player:
        print("Konto> Nada carregado.")
        return
    state = player.get_state()
    if state in (vlc.State.Paused, vlc.State.Stopped): # type: ignore
        player.play()
        player_info["tocando"] = True
        print("Konto> Retomado.")
    else:
        print("Konto> Já está tocando.")"""

@Registry.command("adiantar", aliases=["pular_para_frente", "passar_para_frente"], key=["reproducao", "musica", "music", "video"])
def avancar_vid():
    player = player_info["player"]
    if not player:
        print("Konto> Nada tocando.")
        return
    pos = player.get_time()
    dur = player.get_length()
    if dur <= 0:
        print("Konto> Duração indisponível.")
        return
    player.set_time(min(pos + 10000, dur - 500))
    print("Konto> +10 segundos.")

@Registry.command("retroceder", aliases=["voltar", "pular_para_tras"], key=["reproducao", "musica", "music", "video"])
def retroceder_vid():
    player = player_info["player"]
    if not player:
        print("Konto> Nada tocando.")
        return
    pos = player.get_time()
    player.set_time(max(pos - 10000, 0))
    print("Konto> -10 segundos.")

@Registry.command("velocidade", aliases=["rate"], key=["reproducao", "musica", "music", "video"])
def ajustar_vel(valor=None):
    player = player_info["player"]
    if not player:
        print("Konto> Nada tocando.")
        return
    if not valor:
        print(f"Konto> Velocidade atual: {player.get_rate()}x")
        return
    try:
        valor = float(valor)
        player.set_rate(valor)
        print(f"Konto> Velocidade {valor}x")
    except:
        print("Konto> Use valor numérico.")

@Registry.command("ir_para", aliases=["pular_para", "tempo"], key=["reproducao", "musica", "music", "video"])
def ir_vid(minuto=None, segundo=None):
    player = player_info["player"]
    if not player:
        print("Konto> Nada tocando.")
        return
    if minuto is None:
        print("Konto> Exemplo: ir para 1 30")
        return
    minuto = int(minuto)
    segundo = int(segundo) if segundo else 0
    novo = (minuto * 60 + segundo) * 1000
    dur = player.get_length()
    if dur <= 0:
        print("Konto> Duração indisponível.")
        return
    if novo > dur:
        novo = max(0, dur - 500)
    player.set_time(novo)
    print(f"Konto> Indo para {minuto}:{segundo:02d}")

@Registry.command("loop", aliases="repetir", key="playlist")
def loop_vid():
    player = player_info["player"]
    if not player:
        print("Konto> Nada tocando.")
        return
    current = player.get_media().get_meta(0)
    if "loop" not in player_info:
        player_info["loop"] = False
    player_info["loop"] = not player_info["loop"]
    print("Konto> Loop ativado." if player_info["loop"] else "Konto> Loop desativado.")

@Registry.command("proximo", aliases="next", key="playlist") 
def playlist_next():
    global playlist_index
    if not playlist:
        print("Konto> Playlist vazia.")
        return
    playlist_index = (playlist_index + 1) % len(playlist)
    tocar_video(playlist[playlist_index])

@Registry.command("anterior", aliases="prev", key="playlist")
def playlist_prev():
    global playlist_index
    if not playlist:
        print("Konto> Playlist vazia.")
        return
    playlist_index = (playlist_index - 1) % len(playlist)
    tocar_video(playlist[playlist_index])

@Registry.command("progresso", aliases="status", key="playlist")
def progresso_vid():
    player = player_info["player"]
    if not player:
        print("Konto> Nada tocando.")
        return
    pos = max(0, player.get_time())
    dur = max(1, player.get_length())
    mp = pos // 60000
    sp = (pos % 60000) // 1000
    md = dur // 60000
    sd = (dur % 60000) // 1000
    print(f"Konto> {mp}:{sp:02d} / {md}:{sd:02d}")