from typing import Optional, Callable

class ContextManager:
    def __init__(self):
        self.current_context: Optional[str] = None
        self.callback: Optional[Callable[[str], None]] = None

    def set(self, name: str, callback: Callable[[str], None]):
        self.current_context = name
        self.callback = callback
    
    def clear(self):
        self.current_context = None
        self.callback = None

    def handle_input(self, text: str) -> bool:
        if self.callback:
            cb = self.callback
            self.clear()
            cb(text)
            return True
        return False
    
CONTEXT = ContextManager()