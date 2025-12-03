# cache_sys.py
import os
import platform
import json
import time
import threading
import psutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from cfunctions.storage import BASE_DIR

CACHE_FILE = os.path.join(BASE_DIR, "cache_sys.json")
CACHE_REFRESH_INTERVAL = 60

class CacheSystem:
    def __init__(self):
        self.executaveis = set()
        self.arquivos = set()
        self.inicializado = False
        self._ultimo_uso = time.time()
        self._lock = threading.Lock()

    def inicializar(self):
        """Carrega cache do disco, se existir, ou cria um novo"""
        with self._lock:
            if self.inicializado:
                return
            
            if os.path.exists(CACHE_FILE):
                try:
                    with open(CACHE_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        self.executaveis = set(data.get("executaveis", []))
                        self.arquivos = set(data.get("arquivos", []))
                except Exception as e:
                    print(f"Konto> Erro ao carregar cache do disco: {e}")
                    self._regen_cache()
            else:
                self._regen_cache()

        self.inicializado = True
        self._iniciar_thread_monitoramento()

    def _regen_cache(self):
        new_exec = self._buscar_executaveis()
        new_arqs = self._buscar_arquivos()

        if new_exec != self.executaveis or new_arqs != self.arquivos:
            self.executaveis = new_exec
            self.arquivos = new_arqs
            self._save_in_disk()

    def _save_in_disk(self):
        try:
            data = {
                "executaveis": list(self.executaveis),
                "arquivos": list(self.arquivos),
                "timestamp": time.time()
            }
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Konto> Erro ao salvar cache em disco: {e}")

    def _iniciar_thread_monitoramento(self):
        """Inicia thread que monitora ociosidade e recarrega cache se necessário"""
        def monitorar_ociosidade():
            while True:
                time.sleep(5)
                if time.time() - self._ultimo_uso > CACHE_REFRESH_INTERVAL:
                        with self._lock:
                            self._regen_cache()
                            self._ultimo_uso = time.time()
        
        t = threading.Thread(target=monitorar_ociosidade, daemon=True)
        t.start()

    def set_use(self):
        """Atualiza o timestamp de última atividade."""
        self._ultimo_uso = time.time()

    def _buscar_executaveis(self) -> set[str]:
        executaveis = set()
        drives = listar_drives()
        sistema = platform.system()

        def escanear_diretorio(base: Path):
            encontrados = set()
            if not base.exists():
                return encontrados
            try:
                for app in base.rglob("*"):
                    if app.is_file() and app.suffix.lower() in [".exe", ".lnk"]:
                        encontrados.add(str(app))
            except (PermissionError, OSError):
                pass
            return encontrados
        
        def escanear_path_dir(path_dir: str):
            encontrados = set()
            if not path_dir or not os.path.exists(path_dir):
                return encontrados
            try:
                for file in os.listdir(path_dir):
                    caminho = os.path.join(base, file)
                    if os.path.isfile(caminho) and os.access(caminho, os.X_OK):
                        encontrados.add(file.lower())
            except PermissionError:
                pass
            return encontrados
        
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = []

            if sistema.startswith("Win"):
                for drive in drives:
                    bases = [
                        Path(drive) / "Program Files",
                        Path(drive) / "Program Files (x86)",
                        Path(drive) / "Users" / os.getlogin() / "AppData" / "Local" / "Programs",
                        Path(drive) / "Users" / os.getlogin() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs",
                        Path(drive) / "Users" / os.getlogin() / "Desktop",
                        Path(drive) / "Users" / os.getlogin() / "Downloads",
                        Path(drive) / "Users" / os.getlogin() / "Documents",
                    ]
                    for base in bases:
                        futures.append(executor.submit(escanear_diretorio, base))
            else:
                bases = [Path("/usr/bin"), Path("/usr/local/bin"), Path("/opt")]
                for base in bases:
                    futures.append(executor.submit(escanear_diretorio, base))

            for path_dir in os.environ.get("PATH", "").split(os.pathsep):
                futures.append(executor.submit(escanear_path_dir, path_dir))

            for future in as_completed(futures):
                executaveis.update(future.result())

        return executaveis
    
    def _buscar_arquivos(self) -> set[str]:
        arquivos = set()
        drives = listar_drives()
        
        def escanear_pasta(pasta: str):
            encontrados = set()
            if not os.path.exists(pasta):
                return encontrados
            for root, _, files in os.walk(pasta):
                    for file in files:
                        if not isinstance(file, str):
                            continue

                        nome = file.lower()
                        if nome.endswith(".lnk") or nome.endswith(".exe"):
                            continue
                        
                        encontrados.add(nome)
            return encontrados
        
        pastas = []
        usuario = os.getlogin()
        for drive in drives:
            pastas += [
                os.path.join(drive, "Users", usuario, "Desktop"),
                os.path.join(drive, "Users", usuario, "Documents"),
                os.path.join(drive, "Users", usuario, "Downloads"),
            ]

        with ThreadPoolExecutor(max_workers=min(8, len(pastas))) as executor:
            futures = [executor.submit(escanear_pasta, pasta) for pasta in pastas]
            for f in as_completed(futures):
                arquivos |= f.result()

        return arquivos
    
    def _resolver_arquivo(self, name: str) -> str | None:
        name = name.lower()
        drives = listar_drives()
        usuario = os.getlogin()

        pastas = []
        for drive in drives:
            pastas = [
                os.path.join(drive, "Users", usuario, "Desktop"),
                os.path.join(drive, "Users", usuario, "Documents"),
                os.path.join(drive, "Users", usuario, "Downloads"),
            ]
        for pasta in pastas:
            for root, _, files in os.walk(pasta):
                for file in files:
                    if file.lower() == name:
                        return os.path.join(root, file)
                    
        return None

def listar_drives() -> list[str]:
    drives = []
    for part in psutil.disk_partitions(all=False):
        if "cdrom" in part.opts or not os.path.exists(part.mountpoint):
            continue
        
        if part.fstype and part.fstype.lower() in ("ntfs", "fat32", "exfat", "apfs", "ext4"):
            drives.append(part.mountpoint)
    
    return drives

CACHE = CacheSystem()