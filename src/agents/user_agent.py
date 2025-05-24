from ui import user_interface as ui

class UserAgent:
    def __init__(self, env):
        self.env = env

    def interact(self):
        coordinator = self.env.get_agent('coordinator')
        ui.show_welcome_message()

        while True:
            user_input = ui.get_user_input()
            if user_input.lower() in ['salir', 'exit', 'quit']:
                ui.show_exit_message()
                break

            response = coordinator.handle_query(user_input)
            if response:
                ui.show_response(response)

