import os
import msvcrt
from colorama import init, Fore, Style

init(autoreset=True)

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def print_menu(options, selected_index):
    clear()
    print(Fore.CYAN + "====== ModulaR LLM emulator ======\n" + Style.RESET_ALL)
    for i, option in enumerate(options):
        if i == selected_index:
            print(Fore.GREEN + f"> {option}" + Style.RESET_ALL)
        else:
            print(f"  {option}")

def menu_loop(options):
    """
    Mostra un menu interattivo per selezionare un'opzione da una lista.
    Ritorna l'indice selezionato, oppure -1 se si preme ESC.
    """
    selected = 0
    print_menu(options, selected)

    while True:
        key = msvcrt.getch()

        if key == b'\xe0':  # tasti freccia
            arrow = msvcrt.getch()
            if arrow == b'H':  # freccia su
                selected = (selected - 1) % len(options)
            elif arrow == b'P':  # freccia giù
                selected = (selected + 1) % len(options)
        elif key in (b'w', b'W'):
            selected = (selected - 1) % len(options)
        elif key in (b's', b'S'):
            selected = (selected + 1) % len(options)
        elif key == b'\r':  # Invio
            return selected
        elif key == b'\x1b':  # ESC
            return -1

        print_menu(options, selected)

# Menu principale fisso (puoi personalizzarlo)
MENU_OPTIONS = [
    "Temporary Chat",
    "Persistent Chat (with memory)",
    "Settings",
    "Load Addons",
    "Exit"
]

if __name__ == "__main__":
    choice = menu_loop(MENU_OPTIONS)
    clear()
    if choice == -1:
        print("Exited.")
    else:
        print(f"You selected: {MENU_OPTIONS[choice]}")
