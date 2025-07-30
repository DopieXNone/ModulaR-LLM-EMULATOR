import json
import subprocess
import os
from datetime import datetime
from colorama import Fore, Style
from files.menu import menu_loop

SETTINGS_DIR = os.path.join(os.path.dirname(__file__), "files")
SETTINGS_PATH = os.path.join(SETTINGS_DIR, "settings.json")
CHAT_DIR = os.path.join(SETTINGS_DIR, "chats")
os.makedirs(CHAT_DIR, exist_ok=True)

class Settings:
    SETTINGS_MENU_OPTIONS = [
        "Chat or Agent Mode",
        "Dialog Type",
        "Interact with Computer (coming soon)",
        "Use Emoji",
        "Select Model",
        "Save Preset",
        "Return to Main Menu"
    ]
    
    def __init__(self):
        self.default_mode = "chat"
        self.dialog_type = "general"
        self.allow_system_interaction = False
        self.use_emoji = False
        self.selected_model = None

        self.load_settings()
        self.ensure_model_selected()

    def load_settings(self):
        if os.path.exists(SETTINGS_PATH):
            try:
                with open(SETTINGS_PATH, "r") as f:
                    data = json.load(f)
                self.default_mode = data.get("default_mode", self.default_mode)
                self.dialog_type = data.get("dialog_type", self.dialog_type)
                self.allow_system_interaction = data.get("allow_system_interaction", self.allow_system_interaction)
                self.use_emoji = data.get("use_emoji", self.use_emoji)
                self.selected_model = data.get("selected_model", self.selected_model)
            except Exception as e:
                print(Fore.RED + f"Failed to load settings: {e}" + Style.RESET_ALL)

    def save_settings(self):
        data = {
            "default_mode": self.default_mode,
            "dialog_type": self.dialog_type,
            "allow_system_interaction": self.allow_system_interaction,
            "use_emoji": self.use_emoji,
            "selected_model": self.selected_model
        }
        try:
            with open(SETTINGS_PATH, "w") as f:
                json.dump(data, f, indent=2)
            print(Fore.GREEN + f"Settings saved to {SETTINGS_PATH}" + Style.RESET_ALL)
        except Exception as e:
            print(Fore.RED + f"Failed to save settings: {e}" + Style.RESET_ALL)

    def ensure_model_selected(self):
        if not self.selected_model:
            print(Fore.YELLOW + "\nNo model selected. You must select one to continue." + Style.RESET_ALL)
            self.select_model()

    def select_model(self):
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
            lines = result.stdout.strip().splitlines()[1:]
            models = [line.split()[0] for line in lines]
            if not models:
                print(Fore.RED + "No models found." + Style.RESET_ALL)
                return

            idx = menu_loop(models)
            if idx == -1:
                print(Fore.YELLOW + "Model selection cancelled." + Style.RESET_ALL)
                return

            self.selected_model = models[idx]
            print(Fore.GREEN + f"Selected model: {self.selected_model}" + Style.RESET_ALL)
            self.save_settings()

        except Exception as e:
            print(Fore.RED + f"Error listing models: {e}" + Style.RESET_ALL)

    def select_emoji(self):
        options = ["Enable Emoji", "Disable Emoji", "Back"]
        while True:
            choice = menu_loop(options)
            if choice == 0:
                self.use_emoji = True
                self.save_settings()
                print(Fore.GREEN + "Emoji enabled." + Style.RESET_ALL)
            elif choice == 1:
                self.use_emoji = False
                self.save_settings()
                print(Fore.GREEN + "Emoji disabled." + Style.RESET_ALL)
            elif choice == 2 or choice == -1:
                break
    
    def interact_with_computer(self):
        options = [
            "Feature Coming Soon!",
            "Back"
        ]
        while True:
            choice = menu_loop(options)
            if choice in (0, 1, -1):
                break

    def show_menu(self):
        while True:
            choice = menu_loop(self.SETTINGS_MENU_OPTIONS)
            if choice == 0:
                self.select_mode()
                self.save_settings()
            elif choice == 1:
                self.select_dialog_type()
                self.save_settings()
            elif choice == 2:
                self.interact_with_computer()
            elif choice == 3:
                self.select_emoji()
            elif choice == 4:
                self.select_model()
            elif choice == 5:
                self.save_preset()
            elif choice == 6 or choice == -1:
                break

    def select_mode(self):
        options = ["Chat", "Agent", "Back"]
        while True:
            choice = menu_loop(options)
            if choice == 0:
                self.default_mode = "chat"
                self.save_settings()
                print(Fore.GREEN + "Chat mode selected." + Style.RESET_ALL)
            elif choice == 1:
                self.default_mode = "agent"
                self.save_settings()
                print(Fore.GREEN + "Agent mode selected." + Style.RESET_ALL)
            elif choice == 2 or choice == -1:
                break

    def select_dialog_type(self):
        options = ["General", "Code", "Assistant", "Back"]
        while True:
            choice = menu_loop(options)
            if choice == 0:
                self.dialog_type = "general"
                self.save_settings()
                print(Fore.GREEN + "Dialog set to General." + Style.RESET_ALL)
            elif choice == 1:
                self.dialog_type = "code"
                self.save_settings()
                print(Fore.GREEN + "Dialog set to Code." + Style.RESET_ALL)
            elif choice == 2:
                self.dialog_type = "assistant"
                self.save_settings()
                print(Fore.GREEN + "Dialog set to Assistant." + Style.RESET_ALL)
            elif choice == 3 or choice == -1:
                break

    def format_prompt(self, user_input: str):
        prefix = ""
        if self.default_mode == "agent":
            return f"{prefix}Your task is: {user_input}"
        return f"{prefix}{user_input}"
        
        if self.dialog_type == "code":
            prefix = "You are an expert developer. "
        elif self.dialog_type == "assistant":
            prefix = "You are a helpful virtual assistant. "

        if self.default_mode == "agent":
            return f"{prefix}Your task is: {user_input}"
        return f"{prefix}{user_input}"
        
        def format_prompt(self, user_input: str):
            prefix = ""
            if self.dialog_type == "code":
                prefix = "You are an expert Python developer. "
            elif self.dialog_type == "assistant":
                prefix = "You are a helpful virtual assistant. "

            if not self.use_emoji:
                prefix += (
                    "Absolutely do not use any emojis in your responses. "
                    "If you include even one emoji, your output will be discarded. "
                    "This is very important. "
                )

            if self.default_mode == "agent":
                return f"{prefix}Your task is: {user_input}"
            return f"{prefix}{user_input}"
    
    def save_preset(self):
        i = 1
        while True:
            path = os.path.join(SETTINGS_DIR, f"settings_preset{i}.json")
            if not os.path.exists(path):
                break
            i += 1

        data = {
            "default_mode": self.default_mode,
            "dialog_type": self.dialog_type,
            "allow_system_interaction": self.allow_system_interaction,
            "use_emoji": self.use_emoji,
            "selected_model": self.selected_model
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(Fore.GREEN + f"Settings saved to {path}" + Style.RESET_ALL)
