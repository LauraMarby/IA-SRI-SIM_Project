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

class ConsoleInterface:
    def __init__(self, coordinator):
        self.coordinator = coordinator

    def launch(self):
        print("=" * 60)
        print(BARTENDER_ASCII)
        print("=" * 60)
        print("¿En qué puedo ayudarte con tus cócteles hoy?")
        print("Escribe 'salir' para terminar.\n")

        while True:
            user_input = input("> ")
            if user_input.lower() in ['salir', 'exit', 'quit']:
                print("🍸 ¡Hasta luego, bartender amigo!")
                break
            response = self.coordinator.handle_query(user_input)
            if response:
                print(f"🍸 {response}/n")
