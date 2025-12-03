# voz.py
import struct
import pvporcupine
import pyaudio
import sys
import json
import queue
from vosk import Model, KaldiRecognizer

def iniciar_escuta(entrada_queue: queue.Queue, WAKE_WORD="konto"):
    try:
        porcupine = pvporcupine.create(keywords=["konto"], acess_key="SUA_CHAVE_PICOVOICE_AQUI") # type: ignore
        pa = pyaudio.PyAudio()
        stream = pa.open(rate=porcupine.sample_rate, channels=1, format=pyaudio.paInt16, input=True, frames_per_buffer=porcupine.frame_length)
        model = Model("model_pt")
        rec = KaldiRecognizer(model, porcupine.sample_rate)

        print("Konto> Sistema de voz local iniciado")

        while True:
            pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm_unpacked = struct.unpack_from("h" * porcupine.frame_length, pcm)
            keyword_index = porcupine.process(pcm_unpacked)
            if keyword_index >= 0:
                comando = escutar_comando_vosk(pa, model)
                if comando:
                    entrada_queue.put(comando)

    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"Konto> Erro no sistema de voz: {e}")
    finally:
        try:
            stream.stop_stream()
            stream.close()
            pa.terminate()
        except Exception:
            pass


def escutar_comando_vosk(pa, model, tempo_max=8):
    rec = KaldiRecognizer(model, 16000)
    stream = pa.open(rate=16000, channels=1, format=pyaudio.paInt16, input=True, frames_per_buffer=4000)
    frames_silencio = 0
    comando_final = ""

    while True:
        data = stream.read(4000, exception_on_overflow=False)
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            comando_final = result.get("text", "")
            break
        else:
            frames_silencio += 1
            if frames_silencio > (tempo_max *5):
                break
    
    stream.stop_stream()
    stream.close()
    return comando_final.strip() if comando_final else None