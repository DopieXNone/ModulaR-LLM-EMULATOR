import requests
import os
import re
from datetime import datetime
from colorama import init, Fore, Style
from files.menu import menu_loop, MENU_OPTIONS
from files.settings import Settings, CHAT_DIR
from files import addons
from files.addons import (
        load_addons, apply_agent_modifiers,
        print_info, print_warning, print_error,
        show_addons_menu
    )


init(autoreset=True)  # colorama

def remove_emojis(text):
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"  # emoticon
        u"\U0001F300-\U0001F5FF"  # simboli
        u"\U0001F680-\U0001F6FF"  # trasporti
        u"\U0001F1E0-\U0001F1FF"  # bandiere
        u"\U00002700-\U000027BF"
        u"\U0001F900-\U0001F9FF"
        u"\U0001FA70-\U0001FAFF"
        "]+", flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)

class LlamaAgent:
    def __init__(self, persistent=False, settings=None):
        self.settings = settings or Settings()
        self.model = self.settings.selected_model or "llama3"
        self.persistent = persistent
        self.history = []

    def ask(self, user_input: str):
        prompt = self.settings.format_prompt(user_input)
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        if self.persistent:
            history_text = "\n".join(
                f"User: {h['user']}\nAssistant: {h['llm']}" for h in self.history
            )
            payload["prompt"] = f"{history_text}\nUser: {prompt}\nAssistant:"

        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()["response"].strip()

            # Rimuovi le emoji se disabilitate dalle impostazioni
            if not self.settings.use_emoji:
                result = remove_emojis(result)

            if self.persistent:
                self.history.append({"user": user_input, "llm": result})

            return result
        else:
            raise Exception(f"Request failed: {response.text}")
    
    def save_chat(self):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        path = os.path.join(CHAT_DIR, f"chat_{timestamp}.json")
        try:
            import json
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
            print(f"\nChat saved in: {path}")
        except Exception as e:
            print(f"Error saving chat: {e}")

def list_installed_models():
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            if not models:
                print(Fore.RED + "No installed models found." + Style.RESET_ALL)
                input("Premi Invio per continuare...")
                return

            model_names = [m['name'] for m in models]
            model_names.append("Return to Main Menu")

            while True:
                choice = menu_loop(model_names)
                if choice == -1 or choice == len(model_names) - 1:
                    break
                else:
                    print(Fore.GREEN + f"Hai selezionato il modello: {model_names[choice]}" + Style.RESET_ALL)
                    input("Premi Invio per tornare alla lista dei modelli...")

        else:
            print("Failed to retrieve models.")
            input("Premi Invio per continuare...")

    except Exception as e:
        print("Ollama not reachable:", e)
        input("Premi Invio per continuare...")

def chat_loop(persistent, settings):
    agent = LlamaAgent(persistent=persistent, settings=settings)

    # Carica e applica gli addon che modificano l'agente (in modo sicuro)
    addons_list = load_addons()
    for addon in addons_list:
        try:
            if hasattr(addon, "modify_agent") and callable(addon.modify_agent):
                addon.modify_agent(agent)
        except Exception as e:
            print(Fore.RED + f"[Addon] Errore nell'applicare '{addon.__name__}': {e}" + Style.RESET_ALL)

    multiline_mode = False
    buffer = []

    while True:
        user_input = input(">>> ").strip()

        if user_input == "":
            continue

        # Comandi speciali
        if user_input.startswith("/"):
            if user_input == "/exit":
                break
            elif user_input == "/bye":
                break
            elif user_input == "/clear":
                agent.history.clear()
                print(Fore.YELLOW + "Session cleared." + Style.RESET_ALL)
            elif user_input == "/show":
                list_installed_models()
            elif user_input == "/multiline":
                multiline_mode = True
                print("Multiline mode ON. End input with /multiline-stop.")
                continue
            elif user_input == "/multiline-stop":
                multiline_mode = False
                user_input = "\n".join(buffer)
                buffer = []
            elif user_input in ("/?", "/help"):
                print(Fore.MAGENTA + "Comandi disponibili:\n"
                      "/exit - Esce dalla chat\n"
                      "/clear - Pulisce la cronologia\n"
                      "/show - Mostra modelli installati\n"
                      "/multiline - Avvia modalità multilinea\n"
                      "/multiline-stop - Termina modalità multilinea\n"
                      "/help - Mostra questo messaggio" + Style.RESET_ALL)
                continue
            else:
                print(Fore.YELLOW + "Comando non implementato." + Style.RESET_ALL)
                continue

        if multiline_mode:
            buffer.append(user_input)
            continue

        try:
            response = agent.ask(user_input)
            print(Fore.GREEN + "Response:" + Style.RESET_ALL, response)
        except Exception as e:
            print(Fore.RED + f"Errore: {e}" + Style.RESET_ALL)

    if persistent:
        agent.save_chat()


def main_menu():
    settings = Settings()

    if not settings.selected_model:
        print(Fore.YELLOW + "\nNo model selected. You must select one to continue." + Style.RESET_ALL)
        settings.select_model()

    while True:
        choice = menu_loop(MENU_OPTIONS)

        if choice == 0:
            chat_loop(persistent=False, settings=settings)
        elif choice == 1:
            chat_loop(persistent=True, settings=settings)
        elif choice == 2:
            settings.show_menu()
        elif choice == 3:
            show_addons_menu(load_addons())
        elif choice == 4 or choice == -1:
            print("Exiting.")
            break
        else:
            print("Invalid option.")

if __name__ == "__main__":
    main_menu()
