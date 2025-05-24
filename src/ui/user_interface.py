# src/ui/user_interface.py

BARTENDER_ASCII = r"""
      .-''''-.
     /  O  O  \
     \  \__/  /
     /'------'\
    |          |
    \.--.  .--./
    (____\/____)
     \\\\\/////    

   Virtual Bartender
"""

def show_welcome_message():
    print("=" * 60)
    print(BARTENDER_ASCII)
    print("=" * 60)
    print("¿En qué puedo ayudarte con tus cócteles hoy?")
    print("Escribe 'salir' para terminar.\n")

def get_user_input():
    return input("> ")

def show_response(response):
    print(f"🍸 {response}\n")

def show_exit_message():
    print("🍸 ¡Hasta luego, bartender amigo!")
