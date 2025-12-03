import os
import time
import sys

class Konto:
    def __init__(self, train: bool = False):
        self.run = False
        self.train = train
        self.classes = None

    def iniciar(self):
        self.run = True
        return True
    
    def input_listen(self):
        while self.run:
            try:
                text = input().strip().lower()
                if text in ("exit", "sair", "encerrar"):
                    self.encerrar()
            except (KeyboardInterrupt, EOFError):
                self.encerrar()
                break

    def encerrar(self):
        if not self.run:
            return
        print("Konto> Encerrando o Assistente.")
        self.run = False
        os._exit(0)

    def loop(self):
        while self.run:
            try:
                self.input_listen()
                time.sleep(0.05)
            except KeyboardInterrupt:
                self.encerrar()


if __name__ == "__main__":
    konto = Konto()
    
    if not konto.iniciar():
        sys.exit(1)

    konto.loop()