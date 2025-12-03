import os
import importlib

# Caminho da pasta atual (__init__.py)
current_dir = os.path.dirname(__file__)

# Para cada arquivo .py na pasta, exceto __init__.py
for filename in os.listdir(current_dir):
    if filename.endswith(".py") and filename != "__init__.py":
        modulename = f"cfunctions.commands.{filename[:-3]}"  # remove .py
        importlib.import_module(modulename)
