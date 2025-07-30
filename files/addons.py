import os
import json
import importlib.util
from typing import List, Callable, Optional, Dict, Any, Tuple

from colorama import Fore, Style
from files.menu import menu_loop

# ----------------------------------------
# Percorsi e costanti globali
# ----------------------------------------

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
ADDONS_FOLDER = os.path.join(PROJECT_ROOT, "addons")
# Allineato alla tua struttura: dati persistenti degli addon in /files/files/addons_data
ADDONS_DATA_DIR = os.path.join(os.path.dirname(__file__), "files", "addons_data")
os.makedirs(ADDONS_DATA_DIR, exist_ok=True)

# ----------------------------------------
# Colori e helper di stampa
# ----------------------------------------

INFO = Fore.CYAN
SUCCESS = Fore.GREEN
WARNING = Fore.YELLOW
ERROR = Fore.RED
RESET = Style.RESET_ALL

def print_info(msg: str) -> None: print(INFO + msg + RESET)
def print_success(msg: str) -> None: print(SUCCESS + msg + RESET)
def print_warning(msg: str) -> None: print(WARNING + msg + RESET)
def print_error(msg: str) -> None: print(ERROR + msg + RESET)

# ----------------------------------------
# Strumenti utili per addon (UI testuale)
# ----------------------------------------

def simple_menu(options: List[str], prompt: str = "Seleziona un'opzione:") -> int:
    print()
    for i, option in enumerate(options):
        print(f"{i + 1}. {option}")
    print("0. Annulla")
    while True:
        choice = input(f"{prompt} ")
        if choice.isdigit():
            idx = int(choice)
            if 0 <= idx <= len(options):
                return idx - 1
        print_warning("Scelta non valida, riprova.")

def ask_input(prompt: str = "Inserisci valore: ") -> str:
    return input(Fore.BLUE + prompt + RESET).strip()

def confirm(prompt: str = "Confermi? [y/n]: ") -> bool:
    return input(Fore.YELLOW + prompt + RESET).lower().startswith("y")

def read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print_error(f"Errore nella lettura di {path}: {e}")
        return ""

def write_file(path: str, content: str) -> None:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print_success(f"File scritto: {path}")
    except Exception as e:
        print_error(f"Errore nella scrittura di {path}: {e}")

# ----------------------------------------
# Classe base per addon (opzionale)
# ----------------------------------------

class BaseAddon:
    def __init__(self, name: str, description: str = "Nessuna descrizione"):
        self.name = name
        self.description = description

    def main(self) -> None:
        print_info(f"Esecuzione addon {self.name} - {self.description}")
        # Da sovrascrivere nelle classi figlie

# ----------------------------------------
# Registry: comandi, hook, voci menu, config persistente
# ----------------------------------------

# Struttura: [{"name": "mycmd", "handler": callable, "help": "descrizione"}]
CUSTOM_COMMANDS: List[Dict[str, Any]] = []

# Ogni hook: callable(agent, text) -> text
USER_INPUT_HOOKS: List[Callable[[Any, str], str]] = []
MODEL_OUTPUT_HOOKS: List[Callable[[Any, str], str]] = []

# Voci extra per menu (label, handler)
MAIN_MENU_ENTRIES: List[Tuple[str, Callable[[], None]]] = []
ADDONS_MENU_ENTRIES: List[Tuple[str, Callable[[], None]]] = []

def register_command(name: str, handler: Callable[[Any, str, Any], Optional[str]], help_text: str = "") -> None:
    """
    Registra un comando custom.
    - name: senza slash (es. 'mycmd')
    - handler: (agent, args: str, settings) -> Optional[str]
    - help_text: testo di aiuto opzionale
    """
    # Evita duplicati sul nome
    for c in CUSTOM_COMMANDS:
        if c["name"] == name:
            c["handler"] = handler
            c["help"] = help_text
            return
    CUSTOM_COMMANDS.append({"name": name, "handler": handler, "help": help_text})

def get_registered_commands() -> List[str]:
    return [f"/{c['name']}" for c in CUSTOM_COMMANDS]

def find_command(name: str) -> Optional[Dict[str, Any]]:
    for c in CUSTOM_COMMANDS:
        if c["name"] == name:
            return c
    return None

def handle_custom_command(agent: Any, raw_text: str, settings: Any) -> Tuple[bool, Optional[str]]:
    """
    Tenta di gestire un comando custom. Ritorna (handled, output opzionale).
    Esempio raw_text: '/mycmd argomenti...'
    """
    if not raw_text.startswith("/"):
        return False, None
    parts = raw_text[1:].split(" ", 1)
    cmd_name = parts[0].strip()
    args = parts[1].strip() if len(parts) > 1 else ""
    cmd = find_command(cmd_name)
    if not cmd:
        return False, None
    try:
        output = cmd["handler"](agent, args, settings)
        return True, output
    except Exception as e:
        print_error(f"[AddonCommand] Errore comando '/{cmd_name}': {e}")
        return True, None

def register_user_input_hook(func: Callable[[Any, str], str]) -> None:
    USER_INPUT_HOOKS.append(func)

def register_model_output_hook(func: Callable[[Any, str], str]) -> None:
    MODEL_OUTPUT_HOOKS.append(func)

def run_user_input_hooks(agent: Any, text: str) -> str:
    """
    Applica in cascata tutti gli hook di input registrati: text = hook(agent, text).
    """
    out = text
    for hook in USER_INPUT_HOOKS:
        try:
            out = hook(agent, out)
            if out is None:
                # Se un hook restituisce None, mantieni stringa corrente
                out = text
        except Exception as e:
            print_error(f"[Hook on_input] Errore: {e}")
    return out

def run_model_output_hooks(agent: Any, text: str) -> str:
    """
    Applica in cascata tutti gli hook di output registrati: text = hook(agent, text).
    """
    out = text
    for hook in MODEL_OUTPUT_HOOKS:
        try:
            out = hook(agent, out)
            if out is None:
                out = text
        except Exception as e:
            print_error(f"[Hook on_output] Errore: {e}")
    return out

def register_main_menu_entry(label: str, handler: Callable[[], None]) -> None:
    MAIN_MENU_ENTRIES.append((label, handler))

def register_addons_menu_entry(label: str, handler: Callable[[], None]) -> None:
    ADDONS_MENU_ENTRIES.append((label, handler))

# Config persistente per singolo addon
def get_addon_config(name: str, default: Optional[dict] = None) -> dict:
    path = os.path.join(ADDONS_DATA_DIR, f"{name}.json")
    if not os.path.exists(path):
        return default or {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print_error(f"Errore lettura config {name}: {e}")
        return default or {}

def save_addon_config(name: str, data: dict) -> None:
    path = os.path.join(ADDONS_DATA_DIR, f"{name}.json")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print_success(f"Configurazione salvata: {name}")
    except Exception as e:
        print_error(f"Errore salvataggio config {name}: {e}")

# ----------------------------------------
# Loader addon + applicazione modificatori agente
# ----------------------------------------

def load_addons() -> List[Any]:
    addons: List[Any] = []
    if not os.path.exists(ADDONS_FOLDER):
        os.makedirs(ADDONS_FOLDER)

    for file in os.listdir(ADDONS_FOLDER):
        if file.endswith(".py") and not file.startswith("__"):
            path = os.path.join(ADDONS_FOLDER, file)
            name = file[:-3]
            try:
                spec = importlib.util.spec_from_file_location(name, path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                addons.append(module)
                print_success(f"[Addon] Caricato: {file}")
            except Exception as e:
                print_error(f"[Addon] Errore nel caricamento di '{file}': {e}")
    return addons

def apply_agent_modifiers(agent: Any, addons: List[Any]) -> None:
    """
    Applica automaticamente modify_agent(agent) se presente.
    Inoltre, se l'addon registra hook/command/menu nel suo main() lo si può richiamare
    a discrezione dell'utente dal menu addon. Qui non chiamiamo main() automaticamente.
    """
    for addon in addons:
        try:
            if hasattr(addon, "modify_agent") and callable(addon.modify_agent):
                addon.modify_agent(agent)
                print_info(f"[Addon] modify_agent applicato da {addon.__name__}")
        except Exception as e:
            print_error(f"[Addon] Errore in modify_agent di {addon.__name__}: {e}")

# ----------------------------------------
# Menu interattivo per addons
# ----------------------------------------

def show_addons_menu(addons: List[Any]) -> None:
    """
    Mostra il menu addon con:
      - elenco degli addon caricati (se hanno main())
      - eventuali voci extra registrate dagli addon (ADDONS_MENU_ENTRIES)
    """
    if not addons and not ADDONS_MENU_ENTRIES:
        print_warning("Nessun addon disponibile.")
        input("Premi Invio per tornare al menu...")
        return

    # Costruisci voci menu: addon con main + voci extra registrate
    addon_labels = [getattr(mod, "__description__", mod.__name__) for mod in addons]
    custom_labels = [label for (label, _handler) in ADDONS_MENU_ENTRIES]
    options = addon_labels + custom_labels + ["Torna al menu principale"]

    while True:
        choice = menu_loop(options)
        if choice == -1 or choice == len(options) - 1:
            break

        # Se scelta rientra negli addon caricati
        if 0 <= choice < len(addon_labels):
            addon = addons[choice]
            if hasattr(addon, "main") and callable(addon.main):
                try:
                    print_info(f"\nEsecuzione addon: {addon.__name__}")
                    addon.main()
                except Exception as e:
                    print_error(f"Errore durante l'esecuzione di {addon.__name__}: {e}")
            else:
                print_warning(f"{addon.__name__} non ha una funzione main().")
        else:
            # Voce custom registrata
            custom_idx = choice - len(addon_labels)
            label, handler = ADDONS_MENU_ENTRIES[custom_idx]
            try:
                handler()
            except Exception as e:
                print_error(f"Errore durante l'esecuzione di '{label}': {e}")

        input("\nPremi Invio per continuare...")

# ----------------------------------------
# Variabili esportabili
# ----------------------------------------

ADDONS_DIR = ADDONS_FOLDER

__all__ = [
    # Colori e messaggi
    "INFO", "SUCCESS", "WARNING", "ERROR", "RESET",
    "print_info", "print_success", "print_warning", "print_error",

    # UI helpers
    "simple_menu", "ask_input", "confirm",
    "read_file", "write_file",

    # Classi e percorsi
    "BaseAddon", "ADDONS_DIR", "ADDONS_DATA_DIR", "PROJECT_ROOT",

    # Loader e menu
    "load_addons", "show_addons_menu", "apply_agent_modifiers",

    # Registri e API per modding
    "CUSTOM_COMMANDS", "USER_INPUT_HOOKS", "MODEL_OUTPUT_HOOKS",
    "MAIN_MENU_ENTRIES", "ADDONS_MENU_ENTRIES",
    "register_command", "get_registered_commands", "handle_custom_command",
    "register_user_input_hook", "register_model_output_hook",
    "run_user_input_hooks", "run_model_output_hooks",
    "register_main_menu_entry", "register_addons_menu_entry",
    "get_addon_config", "save_addon_config",
]
