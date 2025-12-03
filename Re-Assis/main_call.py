# main_call.py
# Noita, Pixel Logic(document), shift-o in aseprite
import threading
import queue
import time
import sys
import argparse
import os
from functions_index import processar_entrada
from intent_trainer import load_or_train_model
from cfunctions import storage
from cfunctions.cache_sys import CACHE
from function_reg import Registry
from context_manager import CONTEXT

class KontoAssistant:
    def __init__(self, force_train: bool = False):
        self.entrada_queue = queue.Queue()
        self.pipeline = None
        self.classes = None
        self.force_train = force_train
        self._running = False

    def iniciar(self):
        storage.load_data()
        CACHE.inicializar()

        self.pipeline, self.classes = load_or_train_model(force_train=self.force_train)
        if not self.pipeline:
            print("Konto> Falha ao carregar ou treinar modelo de intenções.")
            return False

        print("Konto> Assistente inicializado com sucesso!")
        self._running = True
        return True
    
    def _input_listener(self):
        while self._running:
            try:
                texto = input().strip()
                if texto:
                    self.entrada_queue.put(("texto", texto))
            except (EOFError, KeyboardInterrupt):
                self.encerrar()
                break
    
    def _processar_texto(self, texto: str):
        if not texto:
            return
        
        if texto.lower() in ["sair", "exit", "quit", "encerrar"]:
            self.encerrar()
            return
        
        if texto.lower().startswith("konto "):
            texto = texto[len("konto "):].strip()

        try:
            CACHE.set_use()
            if CONTEXT.current_context:
                CONTEXT.handle_input(texto)
            else:
                processar_entrada(texto, self.pipeline)
        except Exception as e:
            print(f"Konto> Erro ao processar entrada: {e}")

    def loop(self):
        while self._running:
            try:
                if not self.entrada_queue.empty():
                    tipo, dado = self.entrada_queue.get()
                    if tipo == "texto":
                        self._processar_texto(dado)
                time.sleep(0.05)
            except KeyboardInterrupt:
                self.encerrar()

    def encerrar(self):
        if not self._running:
            return
        self._running = False
        print("Konto> Encerrando assistente.")
        os._exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", action="store_true", help="Forçar treinamento ou retrainamento")
    args = parser.parse_args()

    konto = KontoAssistant(force_train=args.train)
    if not konto.iniciar():
        sys.exit(1)
    
    t_input = threading.Thread(target=konto._input_listener, daemon=True)
    t_input.start()

    konto.loop()