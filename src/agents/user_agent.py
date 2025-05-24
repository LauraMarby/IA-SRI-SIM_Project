class UserAgent:
    def __init__(self, env):
        self.env = env

    def interact(self):
        coordinator = self.env.get_agent('coordinator')
        print("¿En qué puedo ayudarte con tus cócteles hoy? (Escribe 'salir' para terminar)")
        while True:
            user_input = input("> ")
            if user_input.lower() in ['salir', 'exit', 'quit']:
                print("¡Hasta luego!")
                break
            coordinator.handle_query(user_input)
