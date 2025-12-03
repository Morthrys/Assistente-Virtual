from collections import defaultdict
from typing import Callable
from inspect import signature

class CommandRegistry:
    def __init__(self):
        self._commands: dict[str, Callable] = {}
        self._intent_map: dict[str, str]  = {}
        self._aliases: dict[str, set[str]] = defaultdict(set)
        self._keys: dict[str, set[str]] = defaultdict(set)

    def register(self, name: str, func: Callable, aliases=None, key=None, intent: str | None = None):
        if not name:
            raise ValueError("Nome do comando não pode ser vazio")
        name_norm = name.strip()
        self._commands[name_norm] = func

        if aliases:
            for a in (aliases if isinstance(aliases, (list, set, tuple)) else [aliases]):
                if a:
                    self._aliases[name_norm].add(a.strip())

        if key:
            for k in (key if isinstance(key, (list, set, tuple)) else [key]):
                if k:
                    self._keys[name_norm].add(k.strip())

        if intent:
            self._intent_map[intent] = name_norm

    def command(self, name: str, aliases=None, key=None, intent: str | None = None):
        def decorator(func):
            cmd_name = name or func.__name__
            self.register(cmd_name, func, aliases=aliases, key=key, intent=intent)
            return func
        return decorator

    def executer(self, command, argumento=None, texto_original=None):
        if not command:
            raise ValueError("Konto> Comando não pode ser None")
        cmd = command.strip()
        if cmd in self._commands:
            main = cmd
        else:
            found = None
            for name, alias_set in self._aliases.items():
                if cmd in alias_set:
                    found = name
                    break
            if found:
                main = found
            else:
                main = self._intent_map.get(cmd, None) or None
        
        if main is None:
            raise ValueError(f"Konto> Comando '{command}' não reconhecido")
        
        func = self._commands.get(main)
        if func is None:
            raise ValueError(f"Konto> Comando registrado '{main}' não tem função associada")
        try:
            params = signature(func).parameters
            if len(params) == 0:
                return func()
            if len(params) == 1:
                return func(argumento)
            return func(argumento, texto_original)
        except Exception as e:
            print(f"Konto> Erro ao executar '{command}': {e}")

    def list_commands(self):
        return list(self._commands.keys())
    
    def map_intent(self, intent: str) -> str | None:
        return self._intent_map.get(intent)
    
    def register_intent_mapping(self, intent: str, command_name: str):
        if intent and command_name:
            self._intent_map[intent] = command_name

Registry = CommandRegistry()
